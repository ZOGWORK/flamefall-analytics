"""Independent cross-check of data/flex-table-ix.csv against the source PDF.

The CSV was extracted with pdfplumber (table mode). This script re-reads
Table IX of NASA/TP-2015-216046 with a different library and method
(PyMuPDF word positions, PDF pages 26-34), rebuilds every row, applies the
same documented cleaning rules, and compares all 276 x 15 cells.

Usage:
    python scripts/verify_flex_table_ix.py path/to/20150023456.pdf

Source PDF: https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf
Requires: pymupdf (not needed by the dashboard itself).
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "flex-table-ix.csv"
TABLE_PAGES = range(26, 35)  # 1-based PDF pages 26..34
DASHES = {"-", "\u2013", "\u2014", "\u2212", "\ufffd"}
NUMERIC = ["pressure_mmhg", "o2", "n2", "co2", "he", "d0_mm",
           "extinction_diameter_mm", "burning_rate_mm2_s", "burn_time_s"]


def rows_from_pdf(pdf_path: str) -> dict[int, dict]:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    out: dict[int, dict] = {}
    for pno in TABLE_PAGES:
        page = doc[pno - 1]
        lines: dict[int, list] = {}
        for x0, y0, _x1, _y1, word, *_ in page.get_text("words"):
            lines.setdefault(round(y0 / 3), []).append((x0, word))
        for key in sorted(lines):
            toks = [w for _, w in sorted(lines[key])]
            m = re.fullmatch(r"FLEX.(\d{3})", toks[0]) if toks else None
            if not m:
                continue
            if len(toks) != 15:
                raise SystemExit(f"page {pno}: row {toks[0]} has {len(toks)} tokens: {toks}")
            (_, cir, date, gmt, fuel, p, o2, n2, co2, he, d0, dext, k, bt, outcome) = toks
            out[int(m.group(1))] = dict(
                cir_id=cir, date=date, gmt=gmt, fuel=fuel, pressure_mmhg=p, o2=o2, n2=n2,
                co2=co2, he=he, d0_mm=d0, extinction_diameter_mm=dext,
                burning_rate_mm2_s=k, burn_time_s=bt, outcome=outcome, _page=pno)
    return out


def clean(field: str, raw: str, test_no: int) -> str:
    """Apply the cleaning rules documented in data/PROVENANCE.md."""
    if raw in DASHES:
        return ""
    if field in NUMERIC:
        raw = raw.lstrip("~")
        if field == "pressure_mmhg" and test_no == 114 and float(raw) == 0:
            return ""  # printed as 0 mmHg: physically impossible, treated as missing
        return repr(float(raw))
    return raw


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pdf_rows = rows_from_pdf(sys.argv[1])
    csv_rows = {int(r["test_no"]): r for r in csv.DictReader(CSV_PATH.open(encoding="utf-8"))}
    print(f"PDF rows: {len(pdf_rows)}   CSV rows: {len(csv_rows)}")
    problems = []
    if set(pdf_rows) != set(csv_rows):
        problems.append(f"test-number sets differ: only PDF {sorted(set(pdf_rows) - set(csv_rows))}, "
                        f"only CSV {sorted(set(csv_rows) - set(pdf_rows))}")
    cells = 0
    for t in sorted(set(pdf_rows) & set(csv_rows)):
        for field, raw in pdf_rows[t].items():
            if field.startswith("_"):
                continue
            want = clean(field, raw, t)
            got = csv_rows[t][field].strip()
            if field in NUMERIC and got != "":
                got = repr(float(got))
            cells += 1
            if want != got:
                problems.append(f"FLEX-{t:03d} {field}: PDF {raw!r} -> {want!r}, CSV {got!r} (page {pdf_rows[t]['_page']})")
    per_page: dict[int, int] = {}
    for r in pdf_rows.values():
        per_page[r["_page"]] = per_page.get(r["_page"], 0) + 1
    print("rows per PDF page:", dict(sorted(per_page.items())))
    print(f"cells compared: {cells}")
    if problems:
        print(f"MISMATCHES: {len(problems)}")
        for p in problems:
            print("  ", p)
        return 1
    print("OK: every cell of the CSV matches an independent PyMuPDF read of Table IX.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
