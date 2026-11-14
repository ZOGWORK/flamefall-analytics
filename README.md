# Flamefall Analytics

**What microgravity combustion experiments actually measured, for people designing crewed
spacecraft, stations, surface habitats and pressurised rovers.**

Space Apps Challenge 2026 · *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity
Combustion Data* · team Flamefall Analytics.

- **Live console:** https://flamefall-analytics.onrender.com
- **Slide deck (7 slides):** https://flamefall-analytics.onrender.com/deck/

The project summarises, ranks and interprets combustion investigations from NASA's Physical
Sciences Informatics (PSI) repository. Three rules hold throughout:

1. **Every number carries its source**: report, table, page and test number.
2. **"No data" is an answer.** Where nobody has run the test (partial gravity, for example) that is
   stated, with the nearest real tests. A gap is never filled by guessing.
3. **No verdicts.** Outputs are measurements and estimates with stated uncertainty. Nothing here
   rates a material, atmosphere or design as acceptable for flight.

## How it is put together

| Layer | Where | What it does |
|---|---|---|
| Data and models | `flamefall/`, `scripts/`, `data/` (Python) | Loads and checks the source tables, builds the catalogue, fits and validates the models |
| Export | `scripts/export_web.py` | Writes everything the web app reads as JSON, plus reference answers for its tests |
| Web app | `web/` (Next.js App Router, shadcn/ui, Recharts, Framer Motion) | Six pages and the slide deck, exported as a static site and hosted on Render |

Python runs at build time only. The web app never opens a CSV and never fits a model. Moving
between pages, or changing a filter, happens in the browser with no page reload.

## Run the web app

```bash
cd web
npm ci
npm run dev
```

Tests, lint and the production build, from the same folder:

```bash
npm run test
npm run lint
npm run build
```

## Rebuild and check the data

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts/build_flex_droplets.py
python scripts/export_web.py
```

Tests, in the same activated environment:

```bash
python -m pip install pytest
python -m pytest
```

## What is in the repository

| Path | What it is |
|---|---|
| `web/` | The web app: pages in `src/app/`, components in `src/components/`, calculations in `src/lib/` |
| `web/src/data/`, `web/public/psi/` | The exported JSON the app reads (written by `scripts/export_web.py`) |
| `flamefall/` | Data loading, schema rules, aggregates, catalogue, triage formula and models |
| `data/flex-table-ix.csv` | 276 FLEX droplet-burn tests from NASA/TP-2015-216046, Table IX |
| `data/flex_caption_annotations.csv` | Per-test cool-flame, support and extinction wording from the same report's figure captions |
| `data/flex_droplets.csv` | The same tests in the normalised 24-column research schema |
| `data/psi/`, `data/bass2/` | The PSI repository snapshot and the BASS-II tables |
| `data/evidence.json`, `data/panels.json` | Sourced statements and small curated tables |
| `data/models/` | Stored model cards |
| `data/PROVENANCE.md` | Where each file came from, cleaning rules, how to re-check it |
| `scripts/` | Extraction, verification, build, training and export scripts |
| `tests/` | Totals recomputed from the data; schema rules (a) to (e); export checks; wording rules |
| `docs/` | SI disclosure, human spot-check list, submission text |
| `DECISIONS.md` | Assumptions, and corrections found by checking primary sources |
| `QUESTIONS.md` | Open items that need a human |
| `render.yaml` | How the site is built and published on Render |

## Data sources

- **FLEX**: Dietrich et al., *Detailed Results From the Flame Extinguishment Experiment (FLEX) March
  2009 to December 2011*, NASA/TP-2015-216046, Nov 2015. https://ntrs.nasa.gov/citations/20150023456
  (PSI record PSI-69).
- **PSI Data Repository, combustion science**: https://psi.nasa.gov/physci/repo/search?q=combustion

The FLEX report is a primary source found by the builder; it is not one of the links on the
challenge's Resources tab. Full details are in `data/PROVENANCE.md`.

## Re-check the core dataset yourself

```bash
curl -L -o flex.pdf https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf
pip install pymupdf
python scripts/verify_flex_table_ix.py flex.pdf
```

The script rebuilds Table IX from the PDF with a different library than the one used for the
original extraction and compares every cell with the CSV.

## Licence and branding

MIT licence (see `LICENSE`). The project uses publicly released NASA data. It is not affiliated
with or endorsed by NASA and uses no NASA logos, insignia or mission marks.
