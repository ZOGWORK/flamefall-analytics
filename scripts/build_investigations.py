"""Build data/investigations.csv: one row per investigation, every cell traceable.

Three kinds of cell, kept apart:
  * PSI-stated  - copied from data/psi/records/<id>.json (title, PI, dates, hardware, objective, DOI).
  * computed    - a range worked out here from a PSI experimental table; the column
                  `range_source` names the table and column used.
  * curated     - from data/investigations_curated.json; the key result points at an entry in
                  data/evidence.json, which carries the source, read level and quote.

Anything PSI does not state, and that no cited source states, stays empty. Nothing is imputed.

Run from the repo root:  python scripts/build_investigations.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flamefall import flex, psi  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
KPA_PER_ATM, KPA_PER_BAR, KPA_PER_MMHG = 101.325, 100.0, 101.325 / 760

COLUMNS = [
    "investigation_id", "full_name", "programme", "platform", "facility", "facility_group", "status",
    "date_start", "date_end", "pi", "objective", "materials", "sample_geometry", "o2_min_pct", "o2_max_pct",
    "pressure_min_kPa", "pressure_max_kPa", "flow_min_cm_s", "flow_max_cm_s", "flow_regime", "gravity_g",
    "n_tests", "key_result", "key_result_value", "key_result_unit", "psi_url", "primary_source_url",
    "primary_source_ref", "verification",
    # ---- extras beyond the research schema ----
    "psi_id", "doi", "in_psi_search", "psi_research_area", "fuel_type", "evidence_class", "range_source",
    "n_tests_source", "psi_tables", "psi_file_count", "objective_full", "note",
]


def rng(series: pd.Series, scale: float = 1.0) -> tuple[float | None, float | None]:
    v = psi.numeric(series).dropna()
    if v.empty:
        return None, None
    return round(float(v.min()) * scale, 2), round(float(v.max()) * scale, 2)


def numbers(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]


def iso_month(psi_date: str) -> str:
    """PSI prints MM-DD-YYYY; the catalogue uses YYYY-MM."""
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", (psi_date or "").strip())
    return f"{m.group(3)}-{m.group(1)}" if m else ""


def computed(inv_id: str) -> dict:
    """Ranges that can be read straight off a PSI experimental table (or Table IX for FLEX)."""
    t = psi.read_table
    if inv_id == "FLEX":
        f = flex.load_flex()
        return dict(o2=(f["o2_pct"].min(), f["o2_pct"].max()),
                    p=(round(f["pressure_kpa"].min(), 1), round(f["pressure_kpa"].max(), 1)),
                    n=len(f), n_src="rows of NASA/TP-2015-216046 Table IX (PSI's own table lists 274 of them)",
                    src="O2 and pressure from NASA/TP-2015-216046 Table IX (mmHg converted to kPa)")
    if inv_id == "FLEX-2":
        d = t("PSI-68_Experimental table_Flex2.csv")
        o2 = [x * 100 for row in d["Oxygen Mole Fraction"] for x in numbers(row)]
        p = [x * KPA_PER_ATM for row in d["Ambient Pressure (atm)"] for x in numbers(row)]
        fl = [x for row in d["Flow Velocity (cm/s)"] for x in numbers(row)]
        return dict(o2=(min(o2), max(o2)), p=(round(min(p), 1), round(max(p), 1)), flow=(min(fl), max(fl)),
                    src="PSI-68 experimental table (a test matrix by fuel: oxygen mole fraction, pressure in atm, "
                        "flow velocity). Planned values, not a per-test log")
    if inv_id == "CFI":
        d = t("PSI-39_Experimental table_CFI.csv")
        p = [x * KPA_PER_ATM for row in d["Pressure"] for x in numbers(row)]
        return dict(o2=rng(d["Oxygen"], 100), p=(round(min(p), 1), round(max(p), 1)), n=len(d),
                    n_src="rows of the PSI-39 experimental table",
                    src="PSI-39 experimental table, columns Oxygen and Pressure (atm converted to kPa)")
    if inv_id == "BASS":
        d = t("PSI-26_Experimental table_BASS.csv")
        return dict(n=len(d), n_src="rows of the PSI-26 experimental table",
                    src="PSI-26 experimental table lists samples only; it has no oxygen, pressure or flow column")
    if inv_id == "BASS-II":
        d = t("PSI-25_Experimental table_BASS-II.csv")
        return dict(o2=rng(d["Calibrated  initial O2 % by vol"]), flow=(0.0, 55.0), n=len(d),
                    n_src="rows of the PSI-25 experimental table",
                    src="O2: PSI-25 experimental table, calibrated initial O2. Flow: NASA/TM-20210011385 §6.1.1 "
                        "(0 to 55 cm/s). Pressure is not a column of the PSI table")
    if inv_id == "SPICE":
        d = t("PSI-107_Experimental table_Spice.csv")
        lo, hi = rng(d["Air Rate (cm/s)"])
        return dict(flow=(max(lo, 0.0), hi), n=len(d), n_src="rows of the PSI-107 experimental table",
                    src="PSI-107 experimental table, column 'Air Rate (cm/s)' (coflow air; negative entries "
                        "in the table are not shown as a minimum)")
    if inv_id == "SLICE":
        d = t("PSI-106_Experimental table_Slice.csv")
        return dict(n=len(d), n_src="test days in the PSI-106 experimental table",
                    src="PSI-106 experimental table lists test dates and fuel only")
    if inv_id == "SAME":
        d = t("PSI-102_Experimental table_SAME.csv")
        return dict(flow=rng(d["Air Flow (cm/s)"]), src="PSI-102 experimental table, column 'Air Flow (cm/s)'")
    if inv_id == "SAME-R":
        d = t("PSI-101_Experimental table_SAME-R.csv")
        return dict(flow=rng(d["Inlet velocity (cm/s)"]), n=len(d), n_src="rows of the PSI-101 experimental table",
                    src="PSI-101 experimental table, column 'Inlet velocity (cm/s)'")
    if inv_id == "DAFT":
        d = t("PSI-47_Experimental table_DAFT.csv")
        return dict(n=len(d), n_src="sessions in the PSI-47 experimental table", src="")
    if inv_id == "Saffire-I":
        d = t("PSI-98_Experimental table_SAFFIRE-1.csv")
        d = d[d["Material"].str.contains("SIBAL")]
        o2 = [x for row in d["Percent O2"] for x in numbers(row)]
        return dict(o2=(min(o2), max(o2)), flow=rng(d["Air Flow (cm/s)"]), n=len(d),
                    n_src="samples in the PSI-98 experimental table",
                    src="PSI-98 experimental table, columns 'Percent O2' and 'Air Flow (cm/s)'")
    if inv_id == "Saffire-II":
        d = t("PSI-99_Experimental table_SAFFIRE-2.csv")
        d = d[d["Air Flow (cm/s)"].str.contains("cm/s")]
        o2 = [x for row in d["Percent O2 (Note 1)"] for x in numbers(row)]
        fl = [x for row in d["Air Flow (cm/s)"] for x in numbers(row)]
        return dict(o2=(min(o2), max(o2)), flow=(min(fl), max(fl)), n=len(d),
                    n_src="samples in the PSI-99 experimental table",
                    src="PSI-99 experimental table, columns 'Percent O2 (Note 1)' (approximate values) and 'Air Flow'")
    if inv_id == "Saffire-III":
        d = t("PSI-100_Experimental table_SAFFIRE-3.csv")
        fl = [x for row in d["Air Flow"] for x in numbers(row)]
        return dict(flow=(min(fl), max(fl)), n=len(d), n_src="samples in the PSI-100 experimental table",
                    src="PSI-100 experimental table, column 'Air Flow' (30 cm/s). A 2023 journal table gives "
                        "25 cm/s for the same flight; both are shown, neither is preferred. The PSI table has "
                        "no oxygen column")
    if inv_id == "ACME-BRE":
        d = t("PSI-20_Experimental table_ACME BRE.csv")
        o2 = []
        for row in d["Oxygen Conc (percent)"]:
            # two cells read '3400%' and '2100%': a spreadsheet percent-format artefact for 34 and 21
            o2 += [x / 100 if x > 100 else x for x in numbers(row)]
        return dict(o2=(min(o2), max(o2)), n=int(psi.numeric(d["Flames Ignited"]).sum()),
                    n_src="sum of 'Flames Ignited' over the test days in the PSI-20 experimental table",
                    src="PSI-20 experimental table, column 'Oxygen Conc (percent)' (nominal). The table states "
                        "that chamber pressure was varied but does not list it")
    if inv_id == "ACME-CLD":
        d = t("PSI-21_Experimental table_CLD Flame.csv")
        return dict(n=int(psi.numeric(d["Flames ignited"]).sum()),
                    n_src="sum of 'Flames ignited' in the PSI-21 experimental table", src="")
    if inv_id == "ACME-EFIELD":
        d = t("PSI-22_Experimental table_ACME E-FIELD Flames.csv")
        return dict(n=int(psi.numeric(d["Flames Ignited"]).sum()),
                    n_src="sum of 'Flames Ignited' in the PSI-22 experimental table (rows with a count)", src="")
    if inv_id == "ACME-sFlame":
        d = t("PSI-23_Experimental table_ACME s-Flame.csv")
        o2 = [x for row in d["Atmosphere*"] for x in numbers(row.split("O2")[0])]
        return dict(o2=(min(o2), max(o2)), p=(101.3, 101.3), n=int(psi.numeric(d["Flames Ignited*"]).sum()),
                    n_src="sum of 'Flames Ignited' in the PSI-23 experimental table",
                    src="PSI-23 experimental table, column 'Atmosphere' (nominal ~21% and ~30% O2; the table "
                        "notes about 1 atm, with pressure rising and oxygen falling as the chamber vitiates)")
    if inv_id == "ACME-FlameDesign":
        d = t("PSI-10_Experimental table_Flame Design_Normal Flame.csv")
        inv = t("PSI-10_Experimental table_Flame Design_Inverse Flame.csv")
        return dict(o2=rng(d["XO2 (init)"], 100), p=rng(d["pmean (atm)"], KPA_PER_ATM), n=len(d) + len(inv),
                    n_src=f"rows of the two PSI-10 experimental tables ({len(d)} normal, {len(inv)} inverse)",
                    src="Normal flames only: PSI-10 table, chamber 'XO2 (init)' and 'pmean (atm)'. Inverse-flame "
                        "oxygen (up to 0.85) is a burner feed and is deliberately not part of this range")
    if inv_id == "ACME-CFI-G":
        d = t("PSI-159_Experimental table_CFI-G_Normal Flames.csv")
        inv = t("PSI-159_Experimental table_CFI-G_Inverse Flames.csv")
        return dict(o2=rng(d["XO2 before test"], 100), p=rng(d["approx p (bar)"], KPA_PER_BAR), n=len(d) + len(inv),
                    n_src=f"rows of the two PSI-159 experimental tables ({len(d)} normal, {len(inv)} inverse)",
                    src="Normal flames only: PSI-159 table, chamber 'XO2 before test' and 'approx p (bar)'. "
                        "Inverse-flame oxygen (up to 0.85) is a burner feed and is deliberately not part of this range")
    return {}


def flex_key_result() -> tuple[str, float, str, str, str]:
    s = flex.summary()
    c = s["cool_flame"]
    text = (f"{s['outcomes']['Extinction']} of {s['n']} droplet burns ended in visible-flame extinction; "
            f"{c['indicated']} of {s['heptane_extinctions']} n-heptane extinctions show cool-flame evidence afterwards.")
    return text, float(s["outcomes"]["Extinction"]), f"tests ending in Extinction (of {s['n']})", flex.RECORD_URL, \
        f"{flex.REPORT}, Table IX and Appendix B captions"


def main() -> int:
    curated = json.loads((DATA / "investigations_curated.json").read_text(encoding="utf-8"))["investigations"]
    evidence = {e["id"]: e for e in json.loads((DATA / "evidence.json").read_text(encoding="utf-8"))}
    search = psi.load_search().set_index("psi_id")
    rows = []
    for c in curated:
        inv_id, psi_id = c["investigation_id"], c.get("psi_id", "")
        row = {k: "" for k in COLUMNS}
        row.update({k: ("" if c[k] is None else c[k]) for k in c if k in COLUMNS})
        row["in_psi_search"] = bool(psi_id)
        if psi_id:
            rec = psi.load_record(psi_id)
            people = [f"{p.get('firstName', '')} {p.get('lastName', '')}".strip() for p in rec.get("contacts", [])
                      if "principal" in json.dumps(p.get("roles", "")).lower()]
            objective = psi.fix_text(rec.get("objective"))
            first = re.split(r"(?<=[.!?])\s+", " ".join(objective.split()))[0] if objective else ""
            row.update({
                "full_name": psi.fix_text(rec.get("title")),
                "facility": psi.fix_text(rec.get("experimentHardware")),
                "date_start": iso_month(rec.get("investigationStartDate", "")),
                "date_end": iso_month(rec.get("investigationEndDate", "")),
                "pi": "; ".join(dict.fromkeys(people)),
                "objective": first if len(first) <= 280 else first[:277].rstrip() + "...",
                "objective_full": objective,
                "psi_url": psi.record_url(psi_id),
                "doi": rec.get("doi") or "",
                "psi_research_area": search.loc[psi_id, "research_area"],
                "psi_tables": "; ".join(psi.table_names(psi_id)),
                "psi_file_count": psi.load_files(psi_id)["file_count"],
                "verification": "verified_live",
            })
            if c.get("platform") in ("", None):
                row["platform"] = psi.fix_text(rec.get("flightProgram"))
        comp = computed(inv_id)
        for key, lo, hi in (("o2", "o2_min_pct", "o2_max_pct"), ("p", "pressure_min_kPa", "pressure_max_kPa"),
                            ("flow", "flow_min_cm_s", "flow_max_cm_s")):
            if comp.get(key) and comp[key][0] is not None:
                row[lo], row[hi] = comp[key]
        if "n" in comp:
            row["n_tests"], row["n_tests_source"] = comp["n"], comp["n_src"]
        if comp.get("src"):
            row["range_source"] = comp["src"]
        key = c.get("key_evidence", "")
        if key == "computed:flex":
            (row["key_result"], row["key_result_value"], row["key_result_unit"], row["primary_source_url"],
             row["primary_source_ref"]) = flex_key_result()
        elif key:
            e = evidence[key]
            row.update({"key_result": e["statement"], "key_result_value": "" if e["value"] is None else e["value"],
                        "key_result_unit": e["unit"], "primary_source_url": e["source_url"],
                        "primary_source_ref": e["source_ref"]})
            if not psi_id:
                row["verification"] = e["verification"] if c.get("verification") != "index" else "index"
        if not row["primary_source_url"]:
            row["primary_source_url"] = row["psi_url"]
        if not row["primary_source_ref"] and psi_id:
            row["primary_source_ref"] = f"PSI record {psi_id}"
        rows.append(row)

    df = pd.DataFrame(rows, columns=COLUMNS)
    assert df["investigation_id"].is_unique
    missing = set(search.index) - set(df["psi_id"])
    assert not missing, f"PSI search hits without a catalogue row: {missing}"
    df.to_csv(DATA / "investigations.csv", index=False, lineterminator="\n")
    print(f"wrote investigations.csv: {len(df)} rows ({int(df['in_psi_search'].sum())} from the PSI search)")
    show = df[["investigation_id", "psi_id", "o2_min_pct", "o2_max_pct", "pressure_min_kPa", "pressure_max_kPa",
               "flow_min_cm_s", "flow_max_cm_s", "n_tests", "date_start", "pi"]]
    print(show.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
