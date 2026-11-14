# Flamefall Analytics

**What microgravity combustion experiments actually measured, for people designing crewed
spacecraft, stations, surface habitats and pressurised rovers.**

Space Apps Challenge 2026 · *Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity
Combustion Data* · team Flamefall Analytics.

| | |
|---|---|
| **Live dashboard** | https://zogwork.github.io/flamefall-analytics/ (runs in your browser; the first visit can take up to a minute to load) |
| **7-slide summary** | https://zogwork.github.io/flamefall-analytics/deck/ |
| **Use of SI tools** | [docs/SI_DISCLOSURE.md](docs/SI_DISCLOSURE.md) |
| **Corrections found by checking sources** | [DECISIONS.md](DECISIONS.md) |

The dashboard summarises, ranks and interprets combustion investigations from NASA's Physical
Sciences Informatics (PSI) repository. Three rules hold on every page:

1. **Every number carries its source**: report, table, page and test number.
2. **"No data" is an answer.** Where nobody has run the test (partial gravity, for example) the
   dashboard says so and shows the nearest real tests. It never fills a gap by guessing.
3. **No verdicts.** Outputs are measurements and estimates with stated uncertainty. Nothing here
   rates a material, atmosphere or design as acceptable for flight.

## The six pages

| Page | Question it answers |
|---|---|
| Overview | What are the headline numbers, and why does the combination of more oxygen, less pressure and low gravity matter? |
| FLEX Explorer | What happened in each of the 276 droplet burns? Filter by fuel, oxygen, pressure, diluent and outcome |
| Investigation Catalogue | Which experiments matter for my vehicle? Search the evidence, filter, or rank by a stated rule |
| Scenario Lab | What is the nearest real test to my scenario, what does a validated model estimate, and where is there no data? |
| Model Lab | How were the models validated, what do they get wrong, and where do they stop being usable? |
| What We Don't Know | Where does the data stop, and what kinds of burning can a crew or a sensor miss? |

## What "SI-powered" means here

- **Retrieval and extraction.** A question returns the matching measured statements themselves,
  each with its source. No text is generated, so no number can be invented.
- **Ranking by a stated rule.** The formula and its weights are on screen and adjustable, and the
  page says when the order depends on the weights.
- **Small validated models.** Logistic regression, tested on groups of tests the model never saw.
  Droplet extinction: AUC 0.88 on unseen atmospheres, 0.74 on an unseen fuel (the headline).
  Solid materials: 0.48, so the model is reported as failing and is not used.
- **Distance to data on every estimate.** Outside the tested range an output is labelled DEMO.

Droplet, gas-flame, solid-material and smoke evidence are never pooled in one model or one chart.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Tests, in the same activated environment:

```bash
python -m pip install pytest
python -m pytest
```

The live link runs the same files in the browser through stlite (Streamlit compiled to
WebAssembly). `python scripts/build_web.py` regenerates `index.html`, which mounts `app.py`,
`flamefall/`, `views/` and `data/` by URL. The app also runs unchanged on any Streamlit host.

## What is in the repository

| Path | What it is |
|---|---|
| `app.py`, `views/` | The Streamlit app, one file per page |
| `flamefall/` | Data loading, schema rules, catalogue and search, ranking formula, models, charts, shared UI |
| `data/flex-table-ix.csv` | 276 FLEX droplet-burn tests from NASA/TP-2015-216046, Table IX |
| `data/flex_caption_annotations.csv` | Per-test cool-flame, support and extinction wording from the same report's figure captions |
| `data/flex_droplets.csv` | The same tests in the normalised 24-column research schema |
| `data/psi/` | Snapshot of the PSI records for "combustion" and all 25 per-test experimental tables |
| `data/bass2/` | BASS-II test tables transcribed from NASA/TM-20210011385 (126 tests, 290 labelled points) |
| `data/solid_test_points.csv` | 313 solid-fuel test points from BASS-II, Saffire and SoFIE-GEL |
| `data/evidence.json` | 66 sourced statements with read level and quote |
| `data/investigations.csv` | The 33-row catalogue |
| `data/models/`, `data/cv_splits.json` | Trained model cards and the fold membership of every row |
| `data/PROVENANCE.md` | Where each file came from, cleaning rules, how to re-check it |
| `scripts/` | Extraction, verification, build and training scripts |
| `tests/` | Totals recomputed from the data, schema rules, models, every page, wording rules |
| `deck/` | The 7-slide summary (one HTML file) |
| `docs/` | SI disclosure, human spot-check list, submission text |
| `DECISIONS.md` | Assumptions, and corrections found by checking primary sources |
| `QUESTIONS.md` | Open items that need a human |

## Data sources

- **PSI Data Repository, combustion science** (the challenge's data source):
  https://psi.nasa.gov/physci/repo/search?q=combustion
- **FLEX**: Dietrich et al., *Detailed Results From the Flame Extinguishment Experiment (FLEX) March
  2009 to December 2011*, NASA/TP-2015-216046, Nov 2015. https://ntrs.nasa.gov/citations/20150023456
- **BASS-II**: Olson et al., *Burning and Suppression of Solids-II (BASS-II) Summary Report*,
  NASA/TM-20210011385, Oct 2021. https://ntrs.nasa.gov/citations/20210011385
- Papers and reports cited per statement in `data/evidence.json`.

The FLEX report and the BASS-II memo are primary sources found by the builder; they are not links
on the challenge's Resources tab. Full details are in `data/PROVENANCE.md`.

## Re-check the data yourself

```bash
curl -L -o flex.pdf https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf
curl -L -o bass2.pdf https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf
python -m pip install pymupdf pdfplumber
python scripts/verify_flex_table_ix.py flex.pdf        # all 3,864 cells of the core dataset
bash scripts/bass2/run_all.sh bass2.pdf                # rebuilds every BASS-II CSV and checks each row
python scripts/fetch_psi.py                            # re-pulls the PSI snapshot
python scripts/train_models.py                         # reproduces the model cards (seed 42)
```

## Licence and branding

MIT licence (see `LICENSE`). The project uses publicly released NASA data. It is not affiliated
with or endorsed by NASA and uses no NASA logos, insignia or mission marks.
