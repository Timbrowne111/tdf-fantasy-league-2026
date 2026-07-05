"""
Draait de volledige pipeline LOKAAL (op jouw eigen pc):
  1. scrapen (scrape.py)
  2. Excel-dashboard bouwen (build_excel.py)
  3. wijzigingen automatisch committen en pushen naar GitHub

Waarom lokaal en niet in de cloud (GitHub Actions)?
worldcyclingstats.com gebruikt Cloudflare-beveiliging die bekende
datacenter-IP-adressen (zoals die van GitHub's cloud-servers) blokkeert
met een "Verify you are human"-controle. Vanaf jouw eigen internet-
verbinding gebeurt dat normaal niet, omdat dat gewoon lijkt op een
gewone, ingelogde bezoeker.

Gebruik:
    python run_local.py

Vereist een bestand "secrets.env" in de hoofdmap van dit project (zelfde
map als dit script) met daarin (zonder aanhalingstekens):

    WCS_USERNAME=jouw_gebruikersnaam
    WCS_PASSWORD=jouw_wachtwoord

Dat bestand staat in .gitignore en wordt dus NOOIT meegecommit naar
GitHub - je inloggegevens blijven alleen lokaal op jouw pc.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SECRETS_FILE = ROOT / "secrets.env"


def load_secrets() -> None:
    if not SECRETS_FILE.exists():
        print(
            f"FOUT: {SECRETS_FILE} niet gevonden.\n"
            "Maak dit bestand aan met daarin:\n"
            "  WCS_USERNAME=jouw_gebruikersnaam\n"
            "  WCS_PASSWORD=jouw_wachtwoord\n",
            file=sys.stderr,
        )
        sys.exit(1)

    for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"FOUT: commando gaf foutcode {result.returncode}, stoppen.", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    load_secrets()

    run([sys.executable, "scraper/scrape.py"])
    run([sys.executable, "scraper/build_excel.py"])

    # Alleen committen/pushen als er daadwerkelijk iets gewijzigd is.
    subprocess.run(["git", "add", "data/latest.json", "data/dashboard.xlsx"], cwd=ROOT)
    diff = subprocess.run(
        ["git", "diff", "--staged", "--quiet"], cwd=ROOT
    )
    if diff.returncode == 0:
        print("\nGeen wijzigingen in de data, niets om te committen.")
        return

    run(["git", "commit", "-m", "Handmatige/lokale scrape"])
    run(["git", "push"])
    print("\nKlaar! De GitHub Pages-pagina wordt over ~1 minuut automatisch bijgewerkt.")


if __name__ == "__main__":
    main()
