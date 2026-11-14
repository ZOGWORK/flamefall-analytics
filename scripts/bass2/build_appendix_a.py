"""Stage 3 of Appendix A extraction: merge wrapped grid rows into one record per test and
write appendix_a_tests.csv.  Verbatim cell text; wrapped lines joined with one space
(no space when the line ends in a hyphen / en dash, i.e. the source broke a hyphenated token).
usage: build_appendix_a.py <appx_logical.json> <out_dir> <work_dir>
"""
import sys, json, csv, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
lj, out_dir, work_dir = sys.argv[1:4]
d = json.load(open(lj, encoding="utf-8"))

PAGE_TABLE = {111: ("A.1", "Bhattacharjee"), 112: ("A.1", "Bhattacharjee"), 113: ("A.2", "Ferkul"),
              114: ("A.3", "Fernandez-Pello"), 115: ("A.3", "Fernandez-Pello"), 116: ("A.4", "Miller"),
              117: ("A.4", "Miller"), 118: ("A.5", "Olson"), 119: ("A.5", "Olson"),
              120: ("A.6", "T'ien"), 121: ("A.6", "T'ien")}

# logical column index -> (csv name, start of the header text that must be present on every page)
COLS = [
 ("date", "Actual date"), ("start_end_time", "Approximate start time and end time"),
 ("as_run_test_no", "As-run test number"), ("test_no", "Test number"), ("sample_no", "Sample number"),
 ("material", "Material"), ("igniter", "Igniter"), ("flow_restrictor", "Flow restrictor"),
 ("sample_distance_col_verbatim", "Sample distance"), ("fan_display", "Fan display"),
 ("air_display", "Air display"), ("radiometer_gain", "Radiometer gain"),
 ("radiometer_display", "Radiometer display"), ("gn2_pot", "Gaseous nitrogen (GN2)"),
 ("gn2_display", "GN2 display"), ("filter_yn", "Filter (Y/N)"), ("release_mode", "Release mode"),
 ("exposure_mode", "Exposure"), ("exposure_compensation", "Exposure compensation"),
 ("bracket_frames", "Bracket frames"), ("shutter_speed_s", "Shutter speed"), ("f_stop", "F stop"),
 ("iso", "ISO"), ("shutter_hold", "Shutter hold"), ("sd_card_sn", "Secure digital"),
 ("total_frames_shot", "Total frames shot"), ("o2_initial_cal_pct", "Calibrated initial O2"),
 ("o2_final_cal_pct", "Calibrated final O2"), ("o2_initial_pct", "Initial O2"),
 ("o2_final_pct", "Final O2"), ("co2_initial_pct", "Initial CO2"), ("co2_final_pct", "Final CO2"),
 ("co_initial_ppm", "Initial CO,"), ("co_final_ppm", "Final CO,"), ("test_notes", "Test observations"),
]
OUT_ORDER = ["table", "pi", "pdf_page", "date", "as_run_test_no", "test_no", "sample_no", "material",
             "igniter", "flow_restrictor", "flow_direction", "fan_display", "air_display",
             "o2_initial_cal_pct", "o2_final_cal_pct", "o2_initial_pct", "o2_final_pct",
             "co2_initial_pct", "co2_final_pct", "co_initial_ppm", "co_final_ppm", "test_notes",
             # extra verbatim columns (everything else printed in the matrix)
             "start_end_time", "sample_distance_col_verbatim", "radiometer_gain", "radiometer_display",
             "gn2_pot", "gn2_display", "filter_yn", "release_mode", "exposure_mode",
             "exposure_compensation", "bracket_frames", "shutter_speed_s", "f_stop", "iso",
             "shutter_hold", "sd_card_sn", "total_frames_shot", "merged_grid_rows"]

joins = []
def join_lines(lines, ctx):
    out = ""
    for ln in lines:
        if not out:
            out = ln
        elif out[-1] in "-\u2013" and len(out) > 1 and out.strip("-\u2013 ") != "":
            joins.append((ctx, out[-25:], ln[:25]))
            out += ln
        else:
            out += " " + ln
    return out

records, header_log = [], {}
for p in sorted(d, key=int):
    hdr = d[p]["header"]
    assert len(hdr) == len(COLS), (p, len(hdr))
    for (name, start), h in zip(COLS, hdr):
        assert h.startswith(start), (p, name, h)
    header_log[p] = hdr
    table, pi = PAGE_TABLE[int(p)]
    cur = None
    for gi, r in enumerate(d[p]["body"], 1):
        cells = r["cells"]
        if not cells:
            continue
        if "3" in cells:          # a non-empty "Test number" cell starts a new test
            cur = {"table": table, "pi": pi, "pdf_page": int(p), "_lines": {}, "_grid": []}
            records.append(cur)
        assert cur is not None, (p, gi, cells)
        cur["_grid"].append(gi)
        for k, lines in cells.items():
            cur["_lines"].setdefault(int(k), []).extend(lines)

rows = []
for rec in records:
    row = {"table": rec["table"], "pi": rec["pi"], "pdf_page": rec["pdf_page"]}
    tn = " ".join(rec["_lines"][3])
    for i, (name, _) in enumerate(COLS):
        row[name] = join_lines(rec["_lines"].get(i, []), f"{tn}/{name}")
    v = row["sample_distance_col_verbatim"]
    row["flow_direction"] = v if v in ("Opposed", "Concurrent", "Stagnation") else ""
    row["merged_grid_rows"] = len(rec["_grid"])
    rows.append(row)

os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "appendix_a_tests.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=OUT_ORDER)
    w.writeheader()
    for row in rows:
        w.writerow({k: row[k] for k in OUT_ORDER})
json.dump({"headers": header_log, "hyphen_joins": joins}, open(os.path.join(work_dir, "appx_build_log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

import collections
print("rows:", len(rows), dict(collections.Counter(r["table"] for r in rows)))
dup = [t for t, n in collections.Counter(r["test_no"] for r in rows).items() if n > 1]
print("duplicate test numbers:", dup)
print("non-direction values in 'Sample distance' column:", [(r["test_no"], r["sample_distance_col_verbatim"]) for r in rows if not r["flow_direction"]])
print("tests with merged continuation rows:", [(r["test_no"], r["merged_grid_rows"]) for r in rows if r["merged_grid_rows"] > 1])
print("hyphen joins (%d):" % len(joins))
for j in joins: print("  ", j)
print("empty cells per requested column:")
for k in OUT_ORDER[3:22]:
    e = [r["test_no"] for r in rows if r[k] == ""]
    if e: print("  ", k, e)
