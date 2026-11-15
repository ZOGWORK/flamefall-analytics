# Scripts

Everything here runs at build time, from the repository root, in the activated Python environment
described in the main [README](../README.md). The web app never runs any of it: it reads the JSON
that `export_web.py` writes.

Each script's own docstring gives its inputs, outputs and usage. This page says what each one is
for and what it writes.

## Data

| Script | What it does | Writes |
|---|---|---|
| `build_flex_droplets.py` | Puts FLEX Table IX into the normalised 24-column research schema | `data/flex_droplets.csv` |
| `extract_flex_captions.py` | Extracts per-test cool-flame, support and extinction wording from the FLEX report's Appendix B figure captions | `data/flex_caption_annotations.csv` |
| `verify_flex_table_ix.py` | Re-reads Table IX from the report PDF with a second library and compares every cell with the CSV | Nothing. It prints what matches and what does not |
| `fetch_psi.py` | Snapshots the PSI Data Repository records returned by a search for "combustion", with contact details removed. Needs network access | `data/psi/` |
| `build_investigations.py` | Builds the investigation catalogue, one row per investigation | `data/investigations.csv` |
| `build_solid_points.py` | Gathers every solid-fuel test point, with its outcome and whether its pressure is stated or assumed | `data/solid_test_points.csv` |
| `bass2/` | Transcribes the BASS-II summary memo's tables from its PDF and checks every row against the page text. See `data/bass2/README.md` | `data/bass2/` |

## Models

| Script | What it does | Writes |
|---|---|---|
| `train_models.py` | Fits the three logistic models with grouped cross-validation (seed 42) and records every metric | `data/models/*.json`, `data/cv_splits.json` |

## Export

| Script | What it does | Writes |
|---|---|---|
| `export_web.py` | Writes everything the web app reads, and reference answers for its tests. `deck.json` is the words and numbers of the PowerPoint slides, read from `build_deck.py` | `web/src/data/*.json`, `web/public/psi/*.json`, `web/src/lib/__fixtures__/golden.json` |

## Presentation

| Script | What it does | Writes |
|---|---|---|
| `build_deck.py` | Builds the seven-slide PowerPoint deck. Every number on it is read from the data files at build time. The page at `/deck/` shows the same slides: it reads their words from this script through the export | `docs/Flamefall-Analytics-deck.pptx` |

`python scripts/export_web.py --check` writes nothing and exits with an error if any committed
file differs from a fresh export. The tests run the same check, so a change to the data that is
not exported fails `python -m pytest`.

## Order, when something upstream changes

1. Change the source data or the code in `flamefall/`.
2. Re-run the build script for the file that changed.
3. If the change touches what a model is trained on, run `python scripts/train_models.py`.
4. Run `python scripts/export_web.py` and `python scripts/build_deck.py`.
5. Run `python -m pytest`, then the web checks in `web/`.
