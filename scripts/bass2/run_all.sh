#!/usr/bin/env bash
# Rebuild every file in data/bass2/ from the BASS-II summary memo (NASA/TM-20210011385).
#
#   curl -L -o TM-20210011385.pdf https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf
#   pip install pdfplumber pymupdf
#   bash scripts/bass2/run_all.sh TM-20210011385.pdf [output-dir]
#
# Run from the repo root. The second argument defaults to data/bass2.
set -euo pipefail
PDF="${1:?path to TM-20210011385.pdf}"
OUT="${2:-data/bass2}"
PY="${PYTHON:-python}"
WORK="build/bass2"
HERE="scripts/bass2"
mkdir -p "$OUT" "$WORK"
"$PY" "$HERE/build_body_tables.py" "$PDF" "$OUT"                                   # Tables 2.1, 4.1, 4.2, 5.1, 7.1, D.2
"$PY" "$HERE/appx_cells.py" "$PDF" "$WORK/appx_cells.json"                         # Appendix A, stage 1: words -> grid cells
"$PY" "$HERE/appx_logical.py" "$WORK/appx_cells.json" "$WORK/appx_logical.json"    # stage 2: grid -> the 35 printed columns
"$PY" "$HERE/build_appendix_a.py" "$WORK/appx_logical.json" "$OUT" "$WORK"         # stage 3: one row per test
"$PY" "$HERE/build_test_points.py" "$PDF" "$OUT" "$WORK" > "$WORK/points_stats.txt" # derived, labelled test points
"$PY" "$HERE/verify_against_text.py" "$PDF" "$OUT" "$WORK"                         # every row checked against the page text
"$PY" "$HERE/check_quotes.py" "$PDF"                                               # every quoted sentence checked against its page
