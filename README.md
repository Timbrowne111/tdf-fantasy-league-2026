# Tour de France Fantasy League — automatische scraper & interactief dashboard

Dit project scrapet elke dag automatisch de standen van jullie league op
worldcyclingstats.com en bouwt er een interactieve webpagina + Excel-
dashboard van (lijngrafieken met animatie, aan/uit-knoppen per deelnemer).

**Belangrijk:** de site blokkeert geautomatiseerde bezoekers vanaf
cloud-servers (zoals GitHub Actions) met een Cloudflare-beveiligings-
controle. Daarom draait de scraper **lokaal op jouw eigen pc** (via
Windows Taskplanner, 's avonds automatisch) — vanaf je eigen internet-
verbinding triggert die controle namelijk niet. De pc pusht de resultaten
naar GitHub, en de interactieve pagina (gratis gehost via GitHub Pages)
wordt daarna automatisch bijgewerkt, ongeacht vanaf waar er gepusht is.

---

## Stap 1 — GitHub-account & repository (eenmalig)

1. Log in op https://github.com (heb je al).
2. Rechtsboven **+ → "New repository"**.
3. Naam: bijvoorbeeld `tdf-fantasy-league-2026`. Zichtbaarheid: **Private**.
4. **Create repository**.

## Stap 2 — Projectbestanden uploaden

1. Pak deze zip uit op je pc.
2. Open je nieuwe (lege) repository → **"uploading an existing file"**.
3. Sleep de **hele inhoud** van de uitgepakte map erin (inclusief de
   verborgen map `.github/` — check na het uploaden of die goed is
   meegekomen; zo niet, zie de opmerking in Stap 5 van eerdere hulp).
4. **Commit changes**.

## Stap 3 — Python op je eigen pc installeren (eenmalig)

Je pc moet zelf Python hebben om het script te draaien.

1. Ga naar https://www.python.org/downloads/ → download en installeer de
   nieuwste versie. **Belangrijk:** vink tijdens installatie de optie
   **"Add python.exe to PATH"** aan.
2. Open een **opdrachtprompt** (Windows-toets → typ `cmd` → Enter) en
   typ `python --version` — je zou een versienummer moeten zien.

## Stap 4 — Git installeren (eenmalig, om te kunnen pushen)

1. Download en installeer https://git-scm.com/download/win (standaard-
   instellingen aanhouden tijdens installatie is prima).
2. Kloon je repository naar je pc. Open een opdrachtprompt in de map
   waar je het project wilt hebben en typ (vervang de URL door die van
   jouw eigen repository, te vinden via de groene **"Code"**-knop op
   GitHub):
   ```
   git clone https://github.com/Timbrowne111/tdf-fantasy-league-2026.git
   cd tdf-fantasy-league-2026
   ```
3. Bij de eerste keer pushen vraagt Windows je waarschijnlijk in te
   loggen via een browserpop-up — log in met je GitHub-account. Daarna
   onthoudt Windows dit.

## Stap 5 — Je inloggegevens lokaal opslaan

1. Maak in de projectmap (dezelfde map als `run_local.py`) een nieuw
   tekstbestand aan met de naam **`secrets.env`** (let op: geen `.txt`
   erachter — bij het opslaan in Kladblok kies je bij "Opslaan als
   type" voor "Alle bestanden").
2. Zet daarin (met jouw eigen gegevens):
   ```
   WCS_USERNAME=jouw_gebruikersnaam
   WCS_PASSWORD=jouw_wachtwoord
   ```
3. Dit bestand staat al in `.gitignore` en wordt dus nooit meegecommit
   naar GitHub — het blijft alleen op jouw eigen pc.

## Stap 6 — Eenmalig testen

Dubbelklik op **`run_daily.bat`** in de projectmap.

Er verschijnt een zwart venster dat:
1. de benodigde Python-pakketten installeert (kan de eerste keer een
   paar minuten duren, vooral het downloaden van de Chromium-browser),
2. inlogt op worldcyclingstats.com en de standen scrapet,
3. het Excel-bestand bouwt,
4. de wijzigingen naar GitHub pusht.

Zie je een foutmelding? Kopieer de tekst en stuur die naar mij door.
Zie je **"Klaar!"** onderaan? Dan werkt alles.

## Stap 7 — Automatisch elke dag laten draaien (Windows Taskplanner)

1. Windows-toets → typ **"Taakplanner"** (Task Scheduler) → openen.
2. Rechts: **"Basistaak maken..."**.
3. Naam: `TdF Fantasy scrape`. **Volgende**.
4. Trigger: **Dagelijks**. **Volgende** → begindatum vandaag, tijdstip
   bijvoorbeeld **20:30** (na de finish, met wat buffer). **Volgende**.
5. Actie: **"Een programma starten"**. **Volgende**.
6. Bij **"Programma/script"**: klik **Bladeren** en selecteer
   `run_daily.bat` in je projectmap. **Volgende** → **Voltooien**.

Vanaf nu draait de scrape elke avond automatisch — **wel moet je pc dan
aan staan** (hij mag in slaapstand net wel/niet werken afhankelijk van je
energie-instellingen; als je pc vaak uit staat op dat tijdstip, kies een
ander tijdstip waarop hij wél aan staat, bijvoorbeeld 's ochtends).

## Stap 8 — GitHub Pages aanzetten (voor de interactieve link)

1. **Settings → Pages** in je repository.
2. **Source**: "Deploy from a branch". **Branch**: `main`, map `/ (root)`.
   **Save**.
3. Na ~1 minuut toont GitHub de link, bijvoorbeeld:
   `https://timbrowne111.github.io/tdf-fantasy-league-2026/`

Die link kun je met collega's delen — wordt automatisch bijgewerkt zodra
jouw pc de dagelijkse scrape heeft gedraaid.

---

## Bestandsoverzicht

- `run_local.py` — de eigenlijke pipeline (scrapen → Excel bouwen → committen/pushen).
- `run_daily.bat` — dubbelklikbaar Windows-script dat `run_local.py` aanroept (dit stel je in bij Taskplanner).
- `secrets.env` — **jouw eigen** inloggegevens (maak je zelf aan, staat niet in de zip, komt nooit op GitHub).
- `scraper/scrape.py` / `scraper/build_excel.py` — ongewijzigd, worden door `run_local.py` aangeroepen.
- `.github/workflows/daily-scrape.yml` — nu alleen nog een handmatige noodoptie; de automatische cloud-planning staat uit.



---

## Wat dit dashboard bevat

**Hoofdsectie (centraal, groot) — Algemeen klassement:**
- Animatie: klik **"▶ Afspelen"** en de lijnen van alle deelnemers bouwen
  zich etappe voor etappe op, als een video van het verloop van de league.
- Een schuifbalk om zelf heen en weer te scrubben door de etappes.
- Klik op een naam in de legenda om die deelnemer aan/uit te zetten (of
  gebruik "Alles aan" / "Alles uit" om snel te focussen op 1 persoon).
- Elke deelnemer heeft overal dezelfde vaste kleur.

**Secundaire secties (kleiner, bijzaak), met dezelfde animatie/toggle-functie:**
- Puntenklassement, Bergklassement, Jongerenklassement.
- Stage results per etappe (tabel, met tabblad per etappe).
- Most picked / Most points op rennersniveau.
- History: winnaars van eerdere jaren van deze league.

**Waarom "Stage results" de brondata is voor de animatie:** die pagina
bevat van zichzelf al een complete rij per etappe die al verreden is. Dat
betekent dat zelfs als de dagelijkse scrape een keer misgaat of een dag
gemist wordt, de eerstvolgende run alsnog de complete, juiste geschiedenis
binnenhaalt — er gaat dus geen data verloren.

## Mogelijke verdere uitbreidingen (optioneel, niet nu al gebouwd)

- Losse categorie-onderverdeling binnen "Most picked" (bijvoorbeeld per
  wegtype: vlak/heuvel/berg/tijdrit) — de basisdata staat er al, dit is
  een kwestie van de tabel verder uitsplitsen als je dat ooit wilt.
- Automatische melding (bijv. e-mail) als de scrape een dag mislukt.
- Publiceren van het dashboard naar een eigen domein in plaats van
  `github.io`.

