# Valašský PG index

GitHub-ready projekt pro ranní paraglidingový report pro Valašsko.

Umí:

- stáhnout předpověď z Open-Meteo,
- vygenerovat PG index pro dnes, zítra a pozítří,
- uložit JSON a Markdown reporty,
- vygenerovat webová data pro GitHub Pages,
- další den validovat, jestli základní meteorologické veličiny seděly.

## Lokální spuštění

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
python scripts/run_daily_forecast.py --config config/locations.json --days 3
python scripts/build_web.py --config config/locations.json --days 3
```

Pak otevři:

```text
docs/index.html
```

## GitHub Actions

V GitHubu otevři:

```text
Actions → Daily PG forecast → Run workflow
```

Workflow vygeneruje:

```text
data/forecasts/*.json
data/forecasts/*.md
docs/data/latest.json
```

## GitHub Pages

Nastav:

```text
Settings → Pages → Build and deployment
Source: Deploy from a branch
Branch: main
Folder: /docs
Save
```

Výsledná adresa bude přibližně:

```text
https://TVUJ-UCET.github.io/TVUJ-REPOZITAR/
```

## Omezení

Toto není bezpečnostní autorita. Je to lokální index pro třídění dnů. Bouřky nejsou automatický stop; jsou samostatná riziková poznámka.
