"""Independent check of every CSV row against pymupdf page.get_text().

page.get_text() lists table cells in reading order (row by row, cell by cell), independently of
the pdfplumber cell grid used for extraction.  For each CSV row we concatenate its cells in
printed column order, delete all whitespace, and require that string to occur in the
whitespace-free page text.  A row that passes has the right values in the right order on the
stated page.  usage: verify_against_text.py <pdf> <out_dir> <work_dir>
"""
import sys, os, io, csv, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pymupdf
pdf, out_dir, work_dir = sys.argv[1:4]
doc = pymupdf.open(pdf)
_cache = {}
def ptxt(n):
    if n not in _cache:
        _cache[n] = re.sub(r"\s+", "", doc[n - 1].get_text())
    return _cache[n]
def read(name):
    with open(os.path.join(out_dir, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
def squash(parts):
    return re.sub(r"\s+", "", "".join(parts))

report = {}
def check(name, rows, cells_of, label_of):
    res = []
    for r in rows:
        s = squash(cells_of(r))
        ok = s in ptxt(int(r["pdf_page"]))
        res.append({"row": label_of(r), "page": int(r["pdf_page"]), "ok": ok, "chars_compared": len(s)})
    report[name] = res
    bad = [x["row"] for x in res if not x["ok"]]
    print(f"{name}: {len(res)} rows checked, {len(res)-len(bad)} match, mismatches: {bad}")

check("table_2_1.csv", read("table_2_1.csv"),
      lambda r: [r["o2_percent"], r["vgcr_mm_s_experiment"], r["vgcr_mm_s_computation"], r["vgcr_mm_s_theory_equation_2_5"]],
      lambda r: "O2 " + r["o2_percent"])
check("table_4_1.csv", read("table_4_1.csv"),
      lambda r: [r["row_label"], r["size_0.00635_m"], r["size_0.009525_m"], r["size_0.0127_m"], r["total"]],
      lambda r: r["pmma_group"] + " / " + r["row_label"])
check("table_4_2.csv", read("table_4_2.csv"),
      lambda r: [r["row_label"], r["sample_diameter_0.00635_m"], r["sample_diameter_0.009525_m"], r["sample_diameter_0.0127_m"]],
      lambda r: r["row_label"])
check("table_d_2.csv", read("table_d_2.csv"), lambda r: [r["test"], r["start"], r["end"], r["total"]], lambda r: "test " + r["test"])
check("table_5_1.csv", read("table_5_1.csv"),
      lambda r: [r[k] for k in ("test_no", "thickness_mm", "width_cm", "one_or_two_sides_burning", "velocity_cm_s",
                                "spread_rate_mm_s", "burn_time_min", "initial_o2_vol_pct", "final_o2_vol_pct")],
      lambda r: r["test_no"])
check("table_7_1.csv", read("table_7_1.csv"),
      lambda r: [r["test_number"], r["sample_width_cm"], r["flow_cm_s"], r["o2_vol_pct"] + (r["footnote"][:1] if r["footnote"] else ""), r["comments"]],
      lambda r: r["test_number"])
# Table 4.1 group rows: the group label must sit between the right rows
t41 = ptxt(55)
assert squash(["Total", "Black PMMA", "Test conditions", "23"]) in t41 and squash(["17", "Clear PMMA", "Test conditions", "4"]) in t41

A_ORDER = ["date", "start_end_time", "as_run_test_no", "test_no", "sample_no", "material", "igniter", "flow_restrictor",
           "sample_distance_col_verbatim", "fan_display", "air_display", "radiometer_gain", "radiometer_display", "gn2_pot",
           "gn2_display", "filter_yn", "release_mode", "exposure_mode", "exposure_compensation", "bracket_frames",
           "shutter_speed_s", "f_stop", "iso", "shutter_hold", "sd_card_sn", "total_frames_shot", "o2_initial_cal_pct",
           "o2_final_cal_pct", "o2_initial_pct", "o2_final_pct", "co2_initial_pct", "co2_final_pct", "co_initial_ppm",
           "co_final_ppm", "test_notes"]
appx = read("appendix_a_tests.csv")
for tab in ("A.1", "A.2", "A.3", "A.4", "A.5", "A.6"):
    check("appendix_a_tests.csv " + tab, [r for r in appx if r["table"] == tab], lambda r: [r[k] for k in A_ORDER], lambda r: r["test_no"])
json.dump(report, open(os.path.join(work_dir, "verify_report.json"), "w", encoding="utf-8"), indent=1)
