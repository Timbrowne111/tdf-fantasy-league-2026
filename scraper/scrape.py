"""
Scraper voor World Cycling Stats - Tour de France Fantasy League.

Logt in met een sessie, haalt de classificatie-tabbladen (General / Points /
Mountain / Youth) op van de league-pagina, en slaat elke dag een "snapshot"
op in data/history.json zodat we later per-dag/per-etappe verlopen kunnen
tekenen (lijngrafieken).

Gebruik:
    python scrape.py

Vereiste environment variables (worden door GitHub Actions als secrets
aangeleverd, of lokaal via een .env-bestand dat NIET in git komt):
    WCS_USERNAME
    WCS_PASSWORD
    WCS_LEAGUE_URL   (optioneel, heeft een default hieronder)
"""

"""
Scraper voor World Cycling Stats - Tour de France Fantasy League.

Logt in met een sessie en haalt alle relevante pagina's op:
  - Classificaties (General / Points / Mountain / Youth) - huidige stand
  - Stage results - PER ETAPPE de stand van elke deelnemer (dit is de
    bron voor de animatie: elke etappe die al verreden is heeft hier al
    een complete rij, dus we hoeven niet zelf dag-voor-dag te "onthouden"
    - een gemiste scrape-dag herstelt zichzelf automatisch de volgende run)
  - Most picked / Most points (rider-niveau, "bijzaak")
  - History (eerdere jaren van deze league, "bijzaak")

Slaat alles op in data/latest.json (wordt elke run overschreven; de
"geschiedenis" zit al in de stage_results-structuur zelf).

Gebruik:
    python scrape.py

Vereiste environment variables:
    WCS_USERNAME
    WCS_PASSWORD
    WCS_LEAGUE_URL   (optioneel, heeft een default hieronder)
"""

import os
import re
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.worldcyclingstats.com"
LOGIN_URL = f"{BASE_URL}/en/"
LEAGUE_URL = os.environ.get(
    "WCS_LEAGUE_URL",
    f"{BASE_URL}/en/game/tour-de-france/2026/league/ahf-fantasy-cycling-league-2026",
)
STAGE_RESULTS_URL = LEAGUE_URL + "/stage-results"
MOST_PICKED_URL = LEAGUE_URL + "/most-picked"
MOST_POINTS_URL = LEAGUE_URL + "/most-points"
HISTORY_URL = LEAGUE_URL + "/history"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "latest.json"

STAGE_ID_RE = re.compile(r"^stage(\d+)$")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def login_and_get_pages(urls: list[str]) -> dict:
    """Start een echte (headless) Chromium-browser via Playwright, logt in
    op worldcyclingstats.com, en haalt daarna de opgegeven URL's op.

    We gebruiken een echte browser (i.p.v. de 'requests'-library) omdat de
    site bot-detectie heeft die kale HTTP-requests met een 403 blokkeert.
    Een paar extra instellingen maken de browser minder herkenbaar als
    geautomatiseerd (headless)."""
    username = os.environ["WCS_USERNAME"]
    password = os.environ["WCS_PASSWORD"]

    pages_html = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        # Verbergt de 'navigator.webdriver' vlag die bot-detectiescripts
        # vaak gebruiken om een geautomatiseerde browser te herkennen.
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()

        try:
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)  # cookiebanner/scripts even laten laden

            page.fill('#modal-login input[name="user_name"]', username, force=True, timeout=15000)
            page.fill('#modal-login input[name="user_pass"]', password, force=True, timeout=15000)
            with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                page.click('#modal-login button[name="user_login"]', force=True, timeout=15000)
            page.wait_for_timeout(1000)

            page.goto(LEAGUE_URL, wait_until="networkidle", timeout=60000)
            if 'id="general"' not in page.content():
                raise RuntimeError(
                    "Login lijkt niet gelukt: classificatietabellen niet gevonden. "
                    "Controleer WCS_USERNAME/WCS_PASSWORD."
                )
            pages_html[LEAGUE_URL] = page.content()

            for url in urls:
                if url == LEAGUE_URL:
                    continue
                page.goto(url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(500)
                pages_html[url] = page.content()

        except Exception:
            # Bewaar een screenshot + de HTML van het moment van falen,
            # zodat we in de GitHub Actions "artifacts" precies kunnen
            # zien wat de browser te zien kreeg.
            debug_dir = Path(__file__).resolve().parent.parent / "debug"
            debug_dir.mkdir(exist_ok=True)
            try:
                page.screenshot(path=str(debug_dir / "failure.png"), full_page=True)
                (debug_dir / "failure.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass  # als zelfs dit mislukt, gooien we alsnog de oorspronkelijke fout
            raise
        finally:
            browser.close()
    return pages_html


def soup_from_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def parse_participant_table(table) -> list[dict]:
    """Parseert een tabel met deelnemers (classificatie- of stage-tabel)."""
    if table is None:
        return []
    rows = table.find_all("tr")
    if not rows:
        return []
    header_cells = [c.get_text(strip=True) for c in rows[0].find_all("td")]

    results = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) != len(header_cells):
            continue
        record = {}
        for header, cell in zip(header_cells, cells):
            if header in ("", "#"):
                continue
            text = cell.get_text(strip=True)
            record[header] = text
            if header == "Participant":
                link = cell.find("a")
                if link and "/user/" in link.get("href", ""):
                    slug = link["href"].split("/user/")[-1].strip("/").split("/")[0]
                    record["participant_slug"] = slug
        results.append(record)
    return results


def parse_classifications(soup: BeautifulSoup) -> dict:
    data = {}
    for tab_id in ["general", "points", "mountain", "youth"]:
        pane = soup.find("div", id=tab_id)
        table = pane.find("table") if pane else None
        data[tab_id] = parse_participant_table(table)
    return data


def parse_stage_results(soup: BeautifulSoup) -> dict:
    """Geeft {'Stage 1': [...], 'Stage 2': [...], ...} terug, alleen voor
    etappes die al minstens 1 niet-lege waarde hebben (nog niet verreden
    etappes bevatten alleen '-')."""
    stages = {}
    panes = soup.find_all("div", id=STAGE_ID_RE)
    panes.sort(key=lambda p: int(STAGE_ID_RE.match(p["id"]).group(1)))
    for pane in panes:
        stage_num = int(STAGE_ID_RE.match(pane["id"]).group(1))
        table = pane.find("table")
        rows = parse_participant_table(table)
        has_data = any(
            any(v not in ("-", "") for k, v in r.items() if k != "Participant" and k != "participant_slug")
            for r in rows
        )
        stages[f"Stage {stage_num}"] = rows if has_data else []
    return stages


def parse_rider_table(soup: BeautifulSoup, tab_id: str = "riders") -> list[dict]:
    """Parseert de hoofd-tabel met renners (most-picked / most-points).

    Sommige headerkolommen gebruiken colspan (bv. "Team" beslaat 2 losse
    datakolommen: vlag + afkorting). We "vouwen" de headerkolommen daarom
    open naar hetzelfde aantal kolommen als de datarijen, zodat elke
    datakolom de juiste veldnaam krijgt, ongeacht de exacte volgorde op
    de pagina."""
    pane = soup.find("div", id=tab_id)
    if pane is None:
        pane = soup.find("div", id="general")
    if pane is None:
        return []
    table = pane.find("table")
    if table is None:
        return []
    rows = table.find_all("tr")
    if not rows:
        return []

    expanded_headers = []
    for c in rows[0].find_all("td"):
        label = c.get_text(strip=True)
        colspan = int(c.get("colspan", 1))
        expanded_headers.extend([label] * colspan)

    label_map = {"×": "times_picked", "%": "percentage", "Pts": "Pts", "Team": "Team"}

    results = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) != len(expanded_headers):
            continue
        record = {}
        for label, cell in zip(expanded_headers, cells):
            if not label:
                continue
            text = cell.get_text(strip=True)
            key = label_map.get(label, label)
            record[key] = text
            if label == "Rider":
                link = cell.find("a")
                if link:
                    record["rider_url"] = link.get("href", "")
        if record:
            results.append(record)
    return results


def parse_history_table(soup: BeautifulSoup) -> list[dict]:
    table = soup.find("table", class_="large")
    if table is None:
        return []
    rows = table.find_all("tr")
    results = []
    for row in rows[1:]:
        cells = row.find_all("td")
        texts = [c.get_text(strip=True) for c in cells]
        if len(texts) < 13:
            continue
        results.append(
            {
                "year": texts[0],
                "general_winner": texts[3],
                "points_winner": texts[6],
                "mountain_winner": texts[9],
                "youth_winner": texts[12],
            }
        )
    return results


def main() -> None:
    urls = [LEAGUE_URL, STAGE_RESULTS_URL, MOST_PICKED_URL, MOST_POINTS_URL, HISTORY_URL]
    pages_html = login_and_get_pages(urls)

    classifications = parse_classifications(soup_from_html(pages_html[LEAGUE_URL]))
    stage_results = parse_stage_results(soup_from_html(pages_html[STAGE_RESULTS_URL]))
    most_picked = parse_rider_table(soup_from_html(pages_html[MOST_PICKED_URL]), tab_id="riders")
    most_points = parse_rider_table(soup_from_html(pages_html[MOST_POINTS_URL]), tab_id="general")
    history = parse_history_table(soup_from_html(pages_html[HISTORY_URL]))

    snapshot = {
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
        "classifications": classifications,
        "stage_results": stage_results,
        "most_picked": most_picked,
        "most_points": most_points,
        "history": history,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    n_stages_done = sum(1 for v in stage_results.values() if v)
    print(
        f"Snapshot opgeslagen: {len(classifications.get('general', []))} deelnemers, "
        f"{n_stages_done} etappes met data."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"FOUT tijdens scrapen: {exc}", file=sys.stderr)
        sys.exit(1)

