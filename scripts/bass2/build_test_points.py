"""Build bass2_test_points.csv (derived, model-ready) from the verbatim CSVs.

Inputs : table_5_1.csv, table_7_1.csv, appendix_a_tests.csv (already written to <out_dir>)
         points_spec.py (hand-made labels for Appendix A tests, every quote machine-checked here)
         the PDF (only to check quotes that cite body text, "page:<n>")
usage  : build_test_points.py <pdf> <out_dir> <work_dir>
"""
import sys, os, io, csv, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pymupdf
import points_spec as S

pdf, out_dir, work_dir = sys.argv[1:4]
doc = pymupdf.open(pdf)
def page_text(n):
    return re.sub(r"\s+", " ", doc[n - 1].get_text())

def read(name):
    with open(os.path.join(out_dir, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

t51 = read("table_5_1.csv")
t71 = read("table_7_1.csv")
appx = {r["test_no"]: r for r in read("appendix_a_tests.csv")}
t51_by = {r["test_no"]: r for r in t51}

COLS = ["point_id", "test_no", "pi", "source_table", "pdf_page", "material_verbatim", "material_class", "geometry",
        "thickness_or_diameter_mm", "width_cm", "sides_burning", "flow_direction", "o2_pct", "o2_basis",
        "flow_cm_s", "flow_basis", "outcome", "outcome_quote", "derivation", "notes",
        "o2_final_pct", "o2_final_basis", "flow_value_kind"]
OUTCOMES = {"sustained", "quenched", "blowoff", "no_ignition", "ambiguous"}
points, problems = [], []
num_re = lambda v: re.fullmatch(r"\d+(\.\d+)?", v or "") is not None

def has_number(text, num):
    return re.search(r"(?<![\d.])" + re.escape(num) + r"(?!\d|\.\d)", text) is not None

def split_list(s):
    """'10, 6, 5, and 3' -> ['10','6','5','3'] ; '20 and 15' -> ['20','15'] ; '9' -> ['9']"""
    parts = [p.strip() for p in re.split(r",\s*and\s+|\s+and\s+|,\s*", s) if p.strip()]
    return parts

# --------------------------------------------------------------------------- material / geometry helpers
PMMA_BASIS = {
    "A.1": "PMMA per Table A.1 'Material' header footnote b: 'Polymethylmethacrylate (PMMA).'",
    "A.3": "PMMA per PDF p55: 'The tests for the present task were conducted with rods of cast PMMA'",
    "A.4": "PMMA per Table A.4 'Material' header footnote b: 'Polymethylmethacrylate (PMMA).'",
    "A.5": "PMMA per Table A.5 'Material' header footnote b: 'Polymethylmethacrylate (PMMA).'",
}
for n, frag in ((55, "The tests for the present task were conducted with rods of cast PMMA"),
                (13, "or a section of a 4-cm-diameter sphere")):
    assert frag in page_text(n), (n, frag)

def appx_material(row):
    """-> (material_class, geometry, thickness_or_diameter_mm, width_cm, sides, extra_note)"""
    m, tab = row["material"], row["table"]
    note = []
    if tab == "A.1":
        mm = re.search(r"(\d+(?:\.\d+)?)-mm", m)
        um = re.search(r"(\d+)[- ]µm", m)
        thick = mm.group(1) if mm else ""
        if not mm and um:
            note.append(f"thickness is stated in µm in the source ('{um.group(0)}'); not converted, so the mm column is empty")
        w = re.search(r"(\d)[- ]cm", m)
        if "PMMA" not in m:
            note.append(PMMA_BASIS[tab])
        return "PMMA", "film", thick, (w.group(1) if w else ""), "", note
    if tab == "A.2":
        if m.startswith("Nomex"):
            return "Nomex", "other", "", "", "", ["sample form (fabric/sheet) is not stated in the report, so geometry is 'other'"]
        assert m == "Japan Wax candle", m
        return "other: Japan Wax candle", "candle", "", "", "", []
    if tab in ("A.3", "A.5"):
        d = re.match(r"(\d+(?:\.\d+)?)-mm", m)
        assert d and "rod" in m, m
        if "PMMA" not in m.upper():
            note.append(PMMA_BASIS[tab])
        return "PMMA", "rod", d.group(1), "", "", note
    if tab == "A.4":
        t = t51_by[row["test_no"]]
        note.append("thickness, width and sides are taken from Table 5.1 (PDF p65) for the same test number")
        return "PMMA", "slab", t["thickness_mm"], t["width_cm"], t["one_or_two_sides_burning"], note
    if tab == "A.6":
        assert m == "4 cm spherical section", m
        return ("PMMA", "sphere", "", "", "",
                ["material not named in Table A.6; PMMA per PDF p13: 'cast polymethylmethacrylate (PMMA) samples were shaped as "
                 "rods ..., or a section of a 4-cm-diameter sphere'",
                 "diameter is stated in cm ('4 cm'); not converted, so the mm column is empty"])
    raise AssertionError(tab)

def add(**kw):
    assert kw["outcome"] in OUTCOMES, kw
    points.append(kw)

# --------------------------------------------------------------------------- Table 5.1 (Miller)
for r in t51:
    vel, spr = split_list(r["velocity_cm_s"]), split_list(r["spread_rate_mm_s"])
    a = appx[r["test_no"]]
    o2note = ""
    if float(r["initial_o2_vol_pct"]) != float(a["o2_initial_cal_pct"]):
        o2note = f"Table 5.1 initial O2 {r['initial_o2_vol_pct']} differs from Table A.4 calibrated initial O2 {a['o2_initial_cal_pct']}"
        problems.append(("5.1 vs A.4 O2", r["test_no"], o2note))
    tracked = r["spread_rate_mm_s"] != "Not tracked"
    if tracked:
        assert len(vel) == len(spr), r
    for i, v in enumerate(vel):
        assert num_re(v), r
        base = dict(test_no=r["test_no"], pi="Miller", source_table="Table 5.1", pdf_page=65,
                    material_verbatim=a["material"], material_class="PMMA", geometry="slab",
                    thickness_or_diameter_mm=r["thickness_mm"], width_cm=r["width_cm"],
                    sides_burning=r["one_or_two_sides_burning"], flow_direction="opposed",
                    o2_pct=r["initial_o2_vol_pct"],
                    o2_basis="Table 5.1 'Initial O2, vol%' (equals Table A.4 'Calibrated initial O2, vol%' for this test)",
                    flow_cm_s=v, flow_basis=f"Table 5.1 'Velocity, cm/s': '{r['velocity_cm_s']}' (item {i+1} of {len(vel)})",
                    o2_final_pct=r["final_o2_vol_pct"], o2_final_basis="Table 5.1 'Final O2, vol%'",
                    flow_value_kind="body_table")
        nts = ["material text is from Table A.4 (Table 5.1 has no material column; PMMA and opposed flow per PDF p63-64: "
               "'The airflow was always opposed.')",
               "O2 was not held constant: it fell from the initial to the final value during the burn"]
        if o2note: nts.append(o2note)
        if tracked:
            add(**base, outcome="sustained",
                outcome_quote=f"Spread rate, mm/s: '{r['spread_rate_mm_s']}' at Velocity, cm/s: '{r['velocity_cm_s']}'",
                derivation=(f"direct: a spread rate ({spr[i]} mm/s) is reported at this velocity"
                            + (" (velocity and spread-rate lists paired by position)" if len(vel) > 1 else "")),
                notes="; ".join(nts))
        else:
            nts.append(f"Table A.4 for this test: air display '{a['air_display']}', fan display '{a['fan_display']}'")
            add(**base, outcome="ambiguous",
                outcome_quote=f"Spread rate, mm/s: 'Not tracked' at Velocity, cm/s: '{r['velocity_cm_s']}'",
                derivation="ambiguous: no spread rate is reported for this velocity ('Not tracked')",
                notes="; ".join(nts))
assert "The airflow was always opposed." in page_text(64)
assert "Quenching extinction data was also obtained at finite flow rates for most of the tests." in page_text(66)

# --------------------------------------------------------------------------- Table 7.1 (T'ien)
assert "FLAT SIBAL" in page_text(104) and "FABRICS IN CONCURRENT FLOW" in page_text(104)
WIDTH_MAP = {"2": "2.2", "1": "1.2"}
disp_vs_table = []
used_cross = set()
for r in t71:
    label = r["test_number"]
    is_bass1 = r["comments"] == "BASS"
    tno = label.split("-")[1] if not is_bass1 else "BASS " + label
    a = appx.get(tno) if not is_bass1 else None
    if not is_bass1:
        assert a is not None, label
    flows = [p.strip() for p in r["flow_cm_s"].split(" to ")]
    assert 1 <= len(flows) <= 2 and all(num_re(f) for f in flows), r
    positions = ["single"] if len(flows) == 1 else ["start", "end"]
    c = r["comments"]
    dashes = set(c) == {"-"}
    nts = []
    if a:
        nts.append(f"Table 7.1 test number '{label}' = Table A.6 test {tno} ({a['date']})")
        if float(a["o2_initial_cal_pct"]) != float(r["o2_vol_pct"]):
            msg = f"Table 7.1 O2 {r['o2_vol_pct']} differs from Table A.6 calibrated initial O2 {a['o2_initial_cal_pct']}"
            nts.append(msg); problems.append(("7.1 vs A.6 O2", tno, msg))
        wd = re.search(r"(\d) cm", a["material"])
        if wd and WIDTH_MAP[wd.group(1)] != r["sample_width_cm"]:
            msg = f"Table 7.1 width {r['sample_width_cm']} cm but Table A.6 material is '{a['material']}'"
            nts.append(msg); problems.append(("7.1 vs A.6 width", tno, msg))
        nts.append(f"Table A.6 air display '{a['air_display']}'; notes: '{a['test_notes']}'")
    else:
        nts.append("BASS (not BASS-II) test listed at the bottom of Table 7.1; it has no Appendix A row; "
                   "PDF p103: 'These four tests are all 21 percent O2 cases at a fixed flow velocity during each test.'")
    mat = "FLAT SIBAL FABRICS (Table 7.1 title)" + (f"; Table A.6 material: '{a['material']}'" if a else "")
    for pos, f in zip(positions, flows):
        src, quote, deriv, outcome = "Table 7.1", f"Comments: '{c}'", None, None
        if r["footnote"]:
            outcome = "ambiguous"
            deriv = "ambiguous: comment is dashes and the O2 value carries footnote b ('O2 reading in these two tests might be inaccurate.')"
        elif dashes:
            x = S.CROSS_7_1.get(tno, {}).get(pos)
            if x:
                outcome, q = x
                assert q in a["test_notes"], (tno, q)
                used_cross.add((tno, pos))
                src = "Table 7.1 + Table A.6"
                quote = f"Table A.6 notes: '{q}' (Table 7.1 Comments: dashes)"
                deriv = ("cross-table: Table 7.1 gives the flow but its comment is dashes; outcome taken from the Table A.6 notes of the same test"
                         + ("" if pos != "start" else "; start flow of a step test whose end condition burned"))
            else:
                outcome = "ambiguous"
                deriv = "ambiguous: Table 7.1 comment is dashes (no outcome stated)"
                extra = S.AMBIG_7_1_EXTRA.get(tno)
                if extra:
                    assert extra in a["test_notes"], (tno, extra)
                    deriv += f"; Table A.6 notes describe a flamelet: '{extra}'"
        elif is_bass1:
            outcome, deriv = "ambiguous", "ambiguous: the comment only says 'BASS' (no outcome stated for this row)"
        elif c.startswith("Reused"):
            outcome = "ambiguous"
            deriv = ("ambiguous: reused, partially burned sample (PDF p103: 'These reused samples in general had a short unburned "
                     "length and provided less quantitative data, thus will not be discussed in this report.')")
        elif c == "No ignition":
            assert pos == "single"
            outcome, deriv = "no_ignition", "direct"
        elif c == "Quenched":
            assert len(flows) == 2
            outcome = "sustained" if pos == "start" else "quenched"
            deriv = ("step test: sustained at start flow, quenched at end flow (this row: start flow)" if pos == "start"
                     else "step test: sustained at start flow, quenched at end flow (this row: end flow)")
        elif c == "No blowoff":
            assert len(flows) == 2
            outcome = "sustained"
            deriv = "step test: flow raised from start to end flow without blowoff; sustained at both (this row: %s flow)" % pos
        elif c == "Blow-off":
            assert len(flows) == 2
            outcome = "sustained" if pos == "start" else "blowoff"
            deriv = ("step test: sustained at start flow, blowoff at end flow (this row: %s flow)" % pos)
        else:
            raise AssertionError(c)
        add(test_no=tno, pi="T'ien", source_table=src, pdf_page="104" if src == "Table 7.1" else "104; %s" % a["pdf_page"],
            material_verbatim=mat, material_class="SIBAL-cotton", geometry="fabric",
            thickness_or_diameter_mm="", width_cm=r["sample_width_cm"], sides_burning="",
            flow_direction="concurrent", o2_pct=r["o2_vol_pct"], o2_basis="Table 7.1 'O2, vol%' (single O2 column)",
            flow_cm_s=f, flow_basis=f"Table 7.1 'Flow, cm/s': '{r['flow_cm_s']}'" + ("" if pos == "single" else f" ({pos} value)"),
            outcome=outcome, outcome_quote=quote, derivation=deriv, notes="; ".join(nts),
            o2_final_pct="", o2_final_basis="", flow_value_kind="body_table")
    if a:
        disp_vs_table.append((tno, r["flow_cm_s"], a["air_display"], a["fan_display"], a["flow_restrictor"]))
assert "cotton-fiberglass" in page_text(109)
for k, v in S.CROSS_7_1.items():
    for pos in v:
        assert (k, pos) in used_cross, ("unused cross entry", k, pos)
assert "These reused samples in general had a short unburned length and provided less quantitative data, thus will not be discussed in this report." in page_text(103)

# --------------------------------------------------------------------------- Appendix A (hand-made spec)
COLMAP = {"notes": "test_notes", "air": "air_display", "fan": "fan_display"}
LOW_NOTE = ("raw air-display reading at the bottom of the transducer's range: in the T'ien tests the display read 1 or <1 "
            "where Table 7.1 gives 2.2 to 2.6 cm/s (T4, T13, T6), so treat this cm/s value as approximate")
in_71 = {p["test_no"] for p in points if p["source_table"].startswith("Table 7.1")}
for e in S.SPEC:
    a = appx[e["test"]]
    assert e["test"] not in in_71, e
    btxt = a[COLMAP[e["bcol"]]]
    if e["btext"] not in btxt:
        problems.append(("basis not verbatim", e["test"], e["btext"])); continue
    if e["qcol"].startswith("page:"):
        pg = int(e["qcol"][5:]); qsrc = page_text(pg); qwhere = f"PDF p{pg} text"
    else:
        qsrc = a[COLMAP[e["qcol"]]]; qwhere = {"notes": "notes", "air": "air display", "fan": "fan display"}[e["qcol"]]
    if e["quote"] not in qsrc:
        problems.append(("quote not verbatim", e["test"], e["quote"])); continue
    if e["flow"]:
        if not has_number(e["btext"], e["flow"]):
            problems.append(("flow number not in basis", e["test"], e["flow"], e["btext"])); continue
    allcells = " | ".join(a[c] for c in COLMAP.values())
    for tok in re.findall(r"\d+\.\d+|\.\d+|\d+", e["cond"]):
        if not has_number(allcells, tok):
            problems.append(("cond number not in row", e["test"], tok, e["cond"]))
    mclass, geom, thick, width, sides, mnotes = appx_material(a)
    bwhere = {"notes": "notes", "air": "air display", "fan": "fan display"}[e["bcol"]]
    cond = e["cond"] or (f"{e['flow']} cm/s" if e["flow"] else "")
    if e["flow"] and e["bcol"] == "air":
        cond += " (air display = air velocity transducer reading in cm/s, PDF p13)"
    flow_basis = f"{cond}; Table {a['table']} {bwhere}: '{e['btext']}'"
    outcome, deriv = e["outcome"], e["deriv"]
    nts = [e["notes"]] if e["notes"] else []
    if e["test"] in S.O2_FLAGGED and outcome != "ambiguous":
        nts.append(f"label without the O2 problem would be '{outcome}' ({deriv})")
        outcome, deriv = "ambiguous", "ambiguous: " + S.O2_FLAGGED[e["test"]]
    fdir = a["flow_direction"].lower()
    if not fdir:
        nts.append(f"flow direction is not stated: the column holds '{a['sample_distance_col_verbatim']}'")
    nts.extend(mnotes)
    o2f, o2fb = "", ""
    if num_re(a["o2_final_pct"]) and num_re(a["o2_final_cal_pct"]) and num_re(a["o2_initial_pct"]):
        o2f, o2fb = a["o2_final_cal_pct"], f"Table {a['table']} 'Calibrated final O2, vol%'"
    else:
        nts.append(f"no usable final O2: raw 'Initial O2' / 'Final O2' cells are '{a['o2_initial_pct']}' / '{a['o2_final_pct']}' "
                   f"(the calibrated-final cell prints '{a['o2_final_cal_pct']}', which is not a reading)")
    if outcome in ("quenched", "blowoff") and o2f and o2f != a["o2_initial_cal_pct"]:
        nts.append("extinction came after the burn had lowered the O2: the calibrated final O2 is the closer reading for this point")
    assert num_re(a["o2_initial_cal_pct"]), a
    kind = ""
    if e["flow"]:
        kind = {"air": "air_display", "notes": "ops_notes", "fan": "fan_display_cell"}[e["bcol"]]
        if kind == "air_display" and float(e["flow"]) <= 2:
            nts.append(LOW_NOTE)
    if e["test"] == "F4":
        assert "The wax candle test successfully ignited in an opposed flow (akin to holding a candle upside down)" in page_text(54)
        nts.append("Table A.2 lists the direction as 'Stagnation'; PDF p54 text says the candle 'ignited in an opposed flow "
                   "(akin to holding a candle upside down)'")
    add(test_no=e["test"], pi=a["pi"], source_table="Table " + a["table"] + (" + text p54" if e["qcol"] == "page:54" else ""),
        pdf_page=a["pdf_page"] if not e["qcol"].startswith("page:") else f"{a['pdf_page']}; {e['qcol'][5:]}",
        material_verbatim=a["material"], material_class=mclass, geometry=geom, thickness_or_diameter_mm=thick,
        width_cm=width, sides_burning=sides, flow_direction=fdir, o2_pct=a["o2_initial_cal_pct"],
        o2_basis=f"Table {a['table']} 'Calibrated initial O2, vol%'", flow_cm_s=e["flow"], flow_basis=flow_basis,
        outcome=outcome, outcome_quote=f"{qwhere}: '{e['quote']}'", derivation=deriv, notes="; ".join(nts),
        o2_final_pct=o2f, o2_final_basis=o2fb, flow_value_kind=kind)

# --------------------------------------------------------------------------- ids, checks, output
cnt = collections.Counter()
for p in points:
    src = {"Table 5.1": "T5.1", "Table 7.1": "T7.1", "Table 7.1 + Table A.6": "T7.1"}.get(p["source_table"], p["source_table"].split(" +")[0].replace("Table ", ""))
    key = (src, p["test_no"])
    cnt[key] += 1
    p["point_id"] = f"{src}-{p['test_no'].replace(' ', '_')}-{cnt[key]:02d}"
assert len({p["point_id"] for p in points}) == len(points)
covered = {p["test_no"] for p in points}
missing = sorted(set(appx) - covered)
if missing:
    problems.append(("appendix tests with no point", missing))
for p in points:
    if p["flow_cm_s"]:
        assert num_re(p["flow_cm_s"]), p
    assert num_re(p["o2_pct"]), p

with open(os.path.join(out_dir, "bass2_test_points.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
    for p in points:
        w.writerow({k: p[k] for k in COLS})

def table(counter, rows_key, title):
    keys = sorted({k[0] for k in counter})
    print(title)
    print("| %s | sustained | quenched | blowoff | no_ignition | ambiguous | total |" % rows_key)
    print("|---|---|---|---|---|---|---|")
    tot = collections.Counter()
    for k in keys:
        vals = [counter[(k, o)] for o in ("sustained", "quenched", "blowoff", "no_ignition", "ambiguous")]
        for o, v in zip(("sustained", "quenched", "blowoff", "no_ignition", "ambiguous"), vals): tot[o] += v
        print("| %s | %s | %d |" % (k, " | ".join(map(str, vals)), sum(vals)))
    vals = [tot[o] for o in ("sustained", "quenched", "blowoff", "no_ignition", "ambiguous")]
    print("| all | %s | %d |" % (" | ".join(map(str, vals)), sum(vals)))

print("points:", len(points), " with flow_cm_s:", sum(1 for p in points if p["flow_cm_s"]))
table(collections.Counter((p["pi"], p["outcome"]) for p in points), "PI", "\nBy PI (all rows)")
table(collections.Counter((p["material_class"], p["outcome"]) for p in points), "material_class", "\nBy material_class (all rows)")
table(collections.Counter((p["material_class"], p["outcome"]) for p in points if p["flow_cm_s"]), "material_class", "\nBy material_class (rows with flow_cm_s only)")
table(collections.Counter((p["source_table"], p["outcome"]) for p in points), "source_table", "\nBy source table")
print("\nderivation classes:")
for k, v in collections.Counter(re.split(r"[:(;]", p["derivation"])[0].strip() for p in points).most_common(): print("  ", v, k)
print("\nTable 7.1 flow vs Table A.6 displays (same test):")
print("| test | Table 7.1 flow, cm/s | A.6 air display | A.6 fan display | flow restrictor |")
print("|---|---|---|---|---|")
for row in disp_vs_table: print("| " + " | ".join(x if x else "(empty)" for x in row) + " |")
print("\nflow_value_kind:", dict(collections.Counter(p["flow_value_kind"] or "(no cm/s)" for p in points)))
print("\nPROBLEMS (%d):" % len(problems))
for pr in problems: print("  ", pr)
json.dump(problems, open(os.path.join(work_dir, "points_problems.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
