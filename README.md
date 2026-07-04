# Tour de France Fantasy League — automatische scraper & Excel-dashboard

Dit project scrapet elke dag automatisch de standen van jullie league op
worldcyclingstats.com en bouwt er een Excel-dashboard van met lijngrafieken
(algemene stand, klassementen, stijgers/dalers).

Alles draait **gratis in de cloud via GitHub Actions** — je pc hoeft niet
aan te staan.

---

## Stap 1 — GitHub-account aanmaken (eenmalig, 2 minuten)

1. Ga naar https://github.com/signup
2. Vul een e-mailadres, wachtwoord en gebruikersnaam in en volg de stappen.
3. Bevestig je e-mailadres via de link die GitHub je stuurt.

Klaar — je hebt nu een (gratis) GitHub-account.

## Stap 2 — Een nieuwe, privé repository aanmaken

Een "repository" (repo) is simpelweg een projectmap in de cloud.

1. Log in op https://github.com
2. Klik rechtsboven op de **+** en kies **"New repository"**.
3. Geef 'm een naam, bijvoorbeeld `tdf-fantasy-league-2026`.
4. Zet de zichtbaarheid op **Private** (zodat alleen jij en wie je uitnodigt
   het kunnen zien — belangrijk, want straks staan hier je inloggegevens
   *versleuteld* in, en willen we geen publieke Excel-data delen zonder dat
   je dat zelf beslist).
5. Klik op **"Create repository"**.

## Stap 3 — De projectbestanden uploaden

Ik heb alle bestanden al voor je klaargezet (zie de bijlagen in dit
gesprek: `scraper/scrape.py`, `scraper/build_excel.py`,
`.github/workflows/daily-scrape.yml`, `requirements.txt`).

Makkelijkste manier zonder command line:

1. Open je nieuwe repository op GitHub.
2. Klik op **"uploading an existing file"** (staat op de lege-repo-pagina),
   of klik op **Add file → Upload files**.
3. Sleep de hele projectmap (met behoud van de submap-structuur
   `scraper/` en `.github/workflows/`) erin. Let op: GitHub's
   upload-scherm behoudt mapstructuur als je de mappen zelf meesleept
   (niet alleen losse bestanden).
4. Klik onderaan op **"Commit changes"**.

*(Ken je iemand die met Git/command line werkt? Dan kan het ook via
`git clone`, bestanden erin zetten, `git push` — maar dat is niet nodig.)*

## Stap 4 — Je inloggegevens veilig opslaan als "Secrets"

Secrets zijn versleutelde variabelen die alleen de automatische workflow
kan lezen — jij, andere bezoekers, en zelfs GitHub-medewerkers kunnen ze
niet terugzien nadat je ze hebt opgeslagen.

1. Ga in je repository naar **Settings** (tab boven in de repo).
2. In het linkermenu: **Secrets and variables → Actions**.
3. Klik op **"New repository secret"**.
4. Naam: `WCS_USERNAME` — Waarde: jouw gebruikersnaam op worldcyclingstats.com.
   Klik **Add secret**.
5. Herhaal voor **`WCS_PASSWORD`** met je wachtwoord.

## Stap 5 — De automatisering activeren

1. Ga naar de tab **Actions** boven in je repository.
2. GitHub vraagt mogelijk om workflows te bevestigen — klik op
   **"I understand my workflows, go ahead and enable them"**.
3. Je ziet nu **"Dagelijkse Tour de France Fantasy scrape"** in de lijst.
   Deze draait vanaf nu automatisch elke dag om 20:30 (Nederlandse tijd)
   tijdens de Tour.

### Meteen even testen

Je hoeft niet te wachten tot vanavond:

1. Klik op **Actions → Dagelijkse Tour de France Fantasy scrape**.
2. Klik rechts op **"Run workflow" → Run workflow**.
3. Wacht ~30 seconden en klik erop om te zien of hij groen (geslaagd) of
   rood (mislukt) wordt. Bij rood: klik erop, lees de foutmelding, en
   stuur die aan mij door — meestal is het een verkeerde gebruikersnaam/
   wachtwoord of een kleine wijziging in de site-structuur die ik dan snel
   kan fixen.

## Stap 6 — GitHub Pages aanzetten (voor de interactieve pagina)

Dit is de stap die je een **link** geeft naar de interactieve pagina met
de animatie en aan/uit-knoppen (in plaats van alleen een Excel-download).

1. Ga naar **Settings → Pages** in je repository.
2. Bij **"Build and deployment"** → **Source**: kies **"Deploy from a branch"**.
3. Bij **Branch**: kies **`main`** en map **`/ (root)`**. Klik **Save**.
4. Wacht ~1 minuut. GitHub toont dan boven in dit scherm een link zoals:
   `https://<jouw-gebruikersnaam>.github.io/tdf-fantasy-league-2026/`

Dat is de link die je met je collega's kunt delen — die pagina wordt
automatisch elke dag bijgewerkt zodra de scraper gedraaid heeft.

> Let op: bij een **private** repository is GitHub Pages ook privé-achtig
> (alleen mensen met toegang tot de repo kunnen 'm zien, of je moet de repo
> op Public zetten voor Pages). Wil je 'm makkelijk met collega's delen
> zonder dat ze een GitHub-account nodig hebben, zet de repo dan op
> **Public** — er staan alleen league-standen in, geen wachtwoorden (die
> blijven altijd als versleutelde secret, nooit in de zichtbare bestanden).

## Stap 7 — Het dashboard bekijken

- **Interactieve pagina (met animatie + aan/uit-knoppen):** de link uit
  Stap 6, bijvoorbeeld `https://<gebruikersnaam>.github.io/<repo-naam>/`.
- **Excel-bonusbestand:** `data/dashboard.xlsx` in de repository
  (Download raw file). Zelfde cijfers, statische grafieken, geen
  animatie/toggles (dat kan Excel niet).
- **Ruwe data:** `data/latest.json` — alles wat gescraped is, voor eigen
  analyses.


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

