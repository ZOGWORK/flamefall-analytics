"""Transcribe Tables 2.1, 4.1, 4.2, 5.1, 7.1 and D.2 verbatim into CSV.
Cells are read from the PDF (pdfplumber ruling lines + pymupdf text); nothing is typed by hand
except the CSV column names.  usage: build_body_tables.py <pdf> <out_dir>
"""
import sys, os, io, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pymupdf
from bass_common import grid_tables

pdf, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
doc = pymupdf.open(pdf)

def cell(c):
    return " ".join(c["lines"])

def table_on(page, caption_start):
    txt = doc[page - 1].get_text()
    assert caption_start in txt, (page, caption_start)
    t = grid_tables(pdf, page)[0]
    assert not t["leftover"], t["leftover"]
    return [[c for c in r] for r in t["rows"]]

def write(name, header, rows):
    with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    print(name, "rows:", len(rows))

# ---- Table 2.1 (p36)
r = table_on(36, "TABLE 2.1.")
assert cell(r[0][0]) == "Vg,cr, mm/s"
assert [cell(c) for c in r[1]] == ["O2, percent", "Experiment", "Computation", "Theory, Equation (2.5)"]
write("table_2_1.csv",
      ["o2_percent", "vgcr_mm_s_experiment", "vgcr_mm_s_computation", "vgcr_mm_s_theory_equation_2_5", "source_table", "pdf_page"],
      [[cell(c) for c in row] + ["Table 2.1", 36] for row in r[2:]])

# ---- Table 4.1 (p55)
r = table_on(55, "TABLE 4.1.")
hdr = [cell(c) for c in r[0]]
assert hdr == ["Size, m", "0.00635", "0.009525", "0.0127", "Total"], hdr
rows, group = [], ""
for row in r[1:]:
    vals = [cell(c) for c in row]
    if len(vals) == 1:
        group = vals[0]; continue
    rows.append([group] + vals + ["Table 4.1", 55])
write("table_4_1.csv",
      ["pmma_group", "row_label", "size_0.00635_m", "size_0.009525_m", "size_0.0127_m", "total", "source_table", "pdf_page"], rows)

# ---- Table 4.2 (p56)
r = table_on(56, "TABLE 4.2.")
hdr = [cell(c) for c in r[0]]
assert hdr == ["Sample diameter, m", "0.00635", "0.009525", "0.0127"], hdr
write("table_4_2.csv",
      ["row_label", "sample_diameter_0.00635_m", "sample_diameter_0.009525_m", "sample_diameter_0.0127_m", "source_table", "pdf_page"],
      [[cell(c) for c in row] + ["Table 4.2", 56] for row in r[1:]])

# ---- Table D.2 (p136)
r = table_on(136, "TABLE D.2.")
assert [cell(c) for c in r[0]] == ["Test", "Start", "End", "Total"]
write("table_d_2.csv", ["test", "start", "end", "total", "source_table", "pdf_page"],
      [[cell(c) for c in row] + ["Table D.2", 136] for row in r[1:]])

# ---- Table 5.1 (p65)
r = table_on(65, "TABLE 5.1.")
hdr = [cell(c) for c in r[0]]
assert hdr == ["Test no.", "Thickness, mm", "Width, cm", "One or two sides burning", "Velocity, cm/s",
               "Spread rate, mm/s", "Burn time, min", "Initial O2, vol%", "Final O2, vol%"], hdr
rows = []
for row in r[1:]:
    assert len(row) == 9 and not any(c["sup"] for c in row)
    rows.append([cell(c) for c in row] + ["", "Table 5.1", 65])
write("table_5_1.csv",
      ["test_no", "thickness_mm", "width_cm", "one_or_two_sides_burning", "velocity_cm_s", "spread_rate_mm_s",
       "burn_time_min", "initial_o2_vol_pct", "final_o2_vol_pct", "footnote", "source_table", "pdf_page"], rows)

# ---- Table 7.1 (p104)
txt = doc[103].get_text()
fn = {}
for m in re.finditer(r"^([ab])(Solid Inflammability Boundary at Low Speeds\.|O2 reading in these two tests might be inaccurate\.)\s*$", txt, re.M):
    fn[m.group(1)] = m.group(2)
assert set(fn) == {"a", "b"}, fn
r = table_on(104, "TABLE 7.1.")
hdr = [cell(c) for c in r[0]]
assert hdr == ["Test number", "Sample width, cm", "Flow, cm/s", "O2, vol%", "Comments"], hdr
rows = []
for row in r[1:]:
    assert len(row) == 5
    marks = [s for c in row for s in c["sup"]]
    rows.append([cell(c) for c in row] + ["; ".join(f"{m}: {fn[m]}" for m in marks), "Table 7.1", 104])
write("table_7_1.csv",
      ["test_number", "sample_width_cm", "flow_cm_s", "o2_vol_pct", "comments", "footnote", "source_table", "pdf_page"], rows)
print("Table 7.1 footnotes:", fn)
