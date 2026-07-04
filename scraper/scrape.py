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

import requests
from bs4 import BeautifulSoup

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

STAGE_ID_RE = re.compile(r"^stage(\d+)$")


def login(session: requests.Session) -> None:
    username = os.environ["WCS_USERNAME"]
    password = os.environ["WCS_PASSWORD"]

    session.get(LOGIN_URL, headers=HEADERS, timeout=30)

    payload = {
        "user_name": username,
        "user_pass": password,
        "user_login": "Log in",
        "user_remember": "1",
    }
    resp = session.post(LOGIN_URL, data=payload, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    check = session.get(LEAGUE_URL, headers=HEADERS, timeout=30)
    if 'id="general"' not in check.text:
        raise RuntimeError(
            "Login lijkt niet gelukt: classificatietabellen niet gevonden. "
            "Controleer WCS_USERNAME/WCS_PASSWORD."
        )


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


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
    session = requests.Session()
    login(session)

    league_soup = get_soup(session, LEAGUE_URL)
    classifications = parse_classifications(league_soup)

    stage_soup = get_soup(session, STAGE_RESULTS_URL)
    stage_results = parse_stage_results(stage_soup)

    most_picked_soup = get_soup(session, MOST_PICKED_URL)
    most_picked = parse_rider_table(most_picked_soup, tab_id="riders")

    most_points_soup = get_soup(session, MOST_POINTS_URL)
    most_points = parse_rider_table(most_points_soup, tab_id="general")

    history_soup = get_soup(session, HISTORY_URL)
    history = parse_history_table(history_soup)

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

