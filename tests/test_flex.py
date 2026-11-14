"""The FLEX dataset: totals are recomputed from the CSV, never copied from a document."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from flamefall import flex, schema


@pytest.fixture(scope="module")
def f() -> pd.DataFrame:
    return flex.load_flex()


@pytest.fixture(scope="module")
def raw() -> pd.DataFrame:
    return flex.load_table_ix()


def test_row_and_column_count(raw):
    assert len(raw) == 276
    assert list(raw.columns) == [
        "test_no", "cir_id", "date", "gmt", "fuel", "pressure_mmhg", "o2", "n2", "co2", "he", "d0_mm",
        "extinction_diameter_mm", "burning_rate_mm2_s", "burn_time_s", "outcome", "notes"]


def test_test_numbers(raw):
    assert raw["test_no"].is_unique
    assert raw["test_no"].min() == 1 and raw["test_no"].max() == 280
    assert sorted(set(range(1, 281)) - set(raw["test_no"])) == [156, 205, 213, 228]


def test_outcome_totals(raw):
    counts = raw["outcome"].value_counts().to_dict()
    assert counts == {"Extinction": 186, "Disruption": 62, "Completion": 28}


def test_outcomes_by_fuel(raw):
    tab = raw.groupby(["fuel", "outcome"]).size().unstack(fill_value=0)
    assert tab.loc["Methanol"].to_dict() == {"Completion": 8, "Disruption": 23, "Extinction": 126}
    assert tab.loc["Heptane"].to_dict() == {"Completion": 20, "Disruption": 39, "Extinction": 60}
    share = {fuel: round(tab.loc[fuel, "Extinction"] / tab.loc[fuel].sum() * 100, 1) for fuel in tab.index}
    assert share == {"Heptane": 50.4, "Methanol": 80.3}       # both sides come from the data


def test_ranges_and_missing(raw):
    expect = {  # column: (min, max, missing)
        "pressure_mmhg": (526.3, 2319.9, 1), "o2": (0.12, 0.34, 0), "n2": (0.09, 0.88, 0),
        "co2": (0.0, 0.70, 0), "he": (0.0, 0.45, 0), "d0_mm": (1.10, 4.67, 12),
        "extinction_diameter_mm": (0.0, 4.60, 78), "burning_rate_mm2_s": (0.05, 1.06, 16),
        "burn_time_s": (0.30, 39.2, 6)}
    for col, (lo, hi, miss) in expect.items():
        assert raw[col].min() == pytest.approx(lo), col
        assert raw[col].max() == pytest.approx(hi), col
        assert int(raw[col].isna().sum()) == miss, col
    assert int(raw["gmt"].isna().sum()) == 1


def test_cleaning_flags_present(raw):
    notes = raw.set_index("test_no")["notes"]
    assert set(notes[notes != ""].index) == {70, 73, 114, 227, 229}
    row = raw.set_index("test_no")
    assert pd.isna(row.loc[114, "pressure_mmhg"])            # printed 0 mmHg -> missing
    assert row.loc[227, "burn_time_s"] == 6 and "approx" in notes[227].lower()
    assert row.loc[229, "burn_time_s"] == 9 and "approx" in notes[229].lower()
    assert row.loc[70, "cir_id"] == row.loc[73, "cir_id"] == "193F001"
    numeric = ["d0_mm", "extinction_diameter_mm", "burning_rate_mm2_s", "burn_time_s"]
    assert row.loc[212, numeric].isna().all() and row.loc[212, "outcome"] == "Extinction"
    zero = sorted(row.index[row["extinction_diameter_mm"] == 0])
    assert zero == [39, 43, 51, 52, 63, 69, 93, 135]           # printed 0, kept as 0


def test_diluent_sanity(f):
    assert int((f["he"] > 0).sum()) == 51
    assert int((f["co2"] > 0).sum()) == 123
    assert int(((f["co2"] > 0) & (f["he"] > 0)).sum()) == 0     # CO2 and He were never combined


def test_gas_fraction_sums(f):
    """The printed fractions are two-decimal values; 29 rows do not sum to exactly 1.00."""
    sums = f["gas_sum"].value_counts().to_dict()
    assert sums == {1.0: 247, 0.99: 22, 0.98: 6, 1.01: 1}
    assert f.loc[f["gas_sum"] == 0.98, "test_no"].tolist() == [69, 75, 76, 79, 80, 81]


def test_derived_columns(f):
    r = f.set_index("test_no").loc[1]
    assert r["test_id"] == "FLEX-001" and r["date_iso"] == "2009-03-05"
    assert r["pressure_atm"] == pytest.approx(757.7 / 760)
    assert r["pressure_kpa"] == pytest.approx(101.018, abs=0.01)
    assert r["o2_partial_kpa"] == pytest.approx(0.21 * 101.018, abs=0.01)
    # First and last test number printed on each PDF page of Table IX, read from the PDF itself
    # (scripts/verify_flex_table_ix.py, rows_from_pdf). Not derived from ROWS_PER_PDF_PAGE.
    printed = {26: (1, 31), 27: (32, 65), 28: (66, 100), 29: (101, 135), 30: (136, 171),
               31: (172, 206), 32: (207, 241), 33: (242, 275), 34: (276, 280)}
    by_page = f.groupby("pdf_page")["test_no"].agg(["min", "max"])
    assert {int(p): (int(lo), int(hi)) for p, (lo, hi) in by_page.iterrows()} == printed
    assert f["source"].iloc[0].endswith("PDF p. 26, row FLEX-001") and f["source"].iloc[-1].endswith("PDF p. 34, row FLEX-280")


def test_summary_matches_recount(f):
    s = flex.summary()
    assert s["n"] == 276 and s["outcomes"] == {"Extinction": 186, "Disruption": 62, "Completion": 28}
    assert s["extinction_share"] == pytest.approx(186 / 276)
    assert s["by_fuel"]["Methanol"]["extinction_share"] == pytest.approx(126 / 157)
    assert s["by_fuel"]["Heptane"]["extinction_share"] == pytest.approx(60 / 119)


def test_caption_annotations(f):
    """Cool-flame labels exist only where the report's caption makes a statement."""
    s = flex.summary()
    assert s["captions"] == 274
    labelled = f[f["cool_flame_label"] != ""]
    assert set(labelled["fuel"]) == {"Heptane"}                 # no methanol cool-flame statement
    assert (labelled["cool_flame_quote"].str.contains("cool flame", case=False)).all()
    assert s["heptane_extinctions"] == 60
    assert s["cool_flame"] == {"indicated": 39, "not_indicated": 8, "unclear": 6, "": 7}


def test_extinction_wording_takes_the_stated_mode(f):
    by_no = f.set_index("test_no")
    assert f["extinction_wording"].value_counts().to_dict() == {"": 189, "radiative": 44, "diffusive": 39,
                                                                "both_mentioned": 4}
    # stated diffusive, with radiative loss named only as a contribution
    assert by_no.loc[225, "extinction_wording"] == "diffusive"
    # captions that say they cannot tell which
    assert set(by_no.loc[[247, 251, 255, 264], "extinction_wording"]) == {"both_mentioned"}
    # "either radiative or outside the flammability boundary" states no mode: left empty, nothing imputed
    assert set(by_no.loc[[140, 141], "extinction_wording"]) == {""}
    sch = flex.build_schema_frame().set_index("flex_no")
    assert sch.loc[225, "extinction_mode"] == "diffusive_only"
    assert sch.loc[225, "D_diff_ext_mm"] == by_no.loc[225, "extinction_diameter_mm"]
    assert pd.isna(sch.loc[247, "D_diff_ext_mm"]) and pd.isna(sch.loc[247, "D_rad_ext_mm"])
    for n in (140, 141):
        assert sch.loc[n, "extinction_mode"] == "visible_extinction_mode_not_stated"
        assert pd.isna(sch.loc[n, "D_rad_ext_mm"]) and sch.loc[n, "visible_ext_diameter_mm"] > 0


def test_caption_atmosphere_is_recorded_but_never_used(f):
    """45 captions word the atmosphere differently from Table IX; the table's values are the data."""
    conflicts = flex.caption_atmosphere_conflicts()
    assert len(conflicts) == 45 and int((f["caption_atmosphere"] != "").sum()) == 268
    by_id = conflicts.set_index("test_id")
    assert by_id.loc["FLEX-185", "caption_atmosphere"] == "0.70/0.52/0.25 O2/N2/CO2"      # sums to 1.47
    assert by_id.loc["FLEX-185", "table_ix"] == "0.23/0.52/0.25 O2/N2/CO2"
    assert by_id.loc["FLEX-280", "caption_atmosphere"] == "0.21/0.15/0.64 O2/N2/He"       # N2 and He swapped
    assert by_id.loc["FLEX-280", "table_ix"] == "0.21/0.64/0.15 O2/N2/He"
    row = f.set_index("test_id").loc["FLEX-185"]
    assert (row["o2"], row["n2"], row["co2"]) == (0.23, 0.52, 0.25)                        # Table IX wins
    # the support quote is only the opening words, with no atmosphere in it
    quotes = set(f.loc[f["support"] != "", "support_quote"])
    assert quotes == {"Free-floating methanol droplet", "Free-floating heptane droplet",
                      "Fiber-supported methanol droplet", "Fiber-supported heptane droplet",
                      "Fiber-supported methanol"}       # FLEX-127 reads "methanol with no translation"
    assert not any(ch.isdigit() for q in quotes for ch in q)


def test_disruption_is_never_extinction(f):
    sch = flex.build_schema_frame()
    dis = sch[sch["outcome"] == "Disruption"]
    assert set(dis["extinction_mode"]) == {"disruption"}
    assert dis["D_rad_ext_mm"].isna().all() and dis["D_diff_ext_mm"].isna().all()


def test_extinction_column_is_only_called_extinction_for_extinction_outcomes(f):
    """Table IX prints a value in the extinction-diameter column for 39 tests that did not extinguish."""
    from flamefall import aggregates

    printed = f[f["extinction_diameter_mm"].notna()].groupby("outcome").size().to_dict()
    assert printed == {"Completion": 15, "Disruption": 24, "Extinction": 159}
    assert set(f.loc[f["extinction_diameter_mm"] == 0, "outcome"]) == {"Disruption", "Completion"}
    by_id = f.set_index("test_id")
    for test_id, outcome in [("FLEX-001", "Disruption"), ("FLEX-051", "Completion"), ("FLEX-002", "Extinction")]:
        row = by_id.loc[test_id]
        assert row["outcome"] == outcome
        line = aggregates.d2_line(row)
        name = line["marker"]["name"]
        assert (name == aggregates.END_MARKER_EXTINCTION) == (outcome == "Extinction"), test_id
        assert (name == aggregates.END_MARKER_OTHER.format(outcome=outcome)) == (outcome != "Extinction"), test_id
        assert line["d2_start"] == pytest.approx(row["d0_mm"] ** 2)
        assert line["d2_end"] == pytest.approx(row["d0_mm"] ** 2 - row["burning_rate_mm2_s"] * row["burn_time_s"])
    assert aggregates.d2_line(by_id.loc["FLEX-212"]) is None     # no diameters printed: no line, never a guess
    assert aggregates.end_diameter_label("Extinction") == "Ext. diameter"
    assert aggregates.end_diameter_label("Disruption") == aggregates.end_diameter_label("Completion") \
        == "Diameter at test end"


def test_aggregates_accept_an_empty_selection(f):
    from flamefall import aggregates

    empty = f.iloc[0:0]
    assert list(aggregates.share_by_level(empty, "o2_pct").columns) == aggregates.SHARE_COLUMNS
    assert len(aggregates.nearest_tests(empty, 21, 1.0)) == 0


def test_share_by_level_recounts_the_table(f):
    from flamefall import aggregates

    agg = aggregates.share_by_level(f, "o2_pct")
    assert int(agg["n"].sum()) == 276 and int(agg["k"].sum()) == 186
    assert int(agg["disruption"].sum()) == 62 and int(agg["completion"].sum()) == 28
    assert ((agg["lo"] <= agg["share"] + 1e-12) & (agg["share"] <= agg["hi"] + 1e-12)).all()


def test_nearest_tests_never_use_an_imputed_pressure(f):
    from flamefall import aggregates

    assert f.set_index("test_id").loc["FLEX-114", ["pressure_atm"]].isna().all()
    near = aggregates.nearest_tests(f, f.set_index("test_id").loc["FLEX-114", "o2_pct"], 1.0, n=276)
    assert len(near) == 275 and "FLEX-114" not in set(near["test_id"]) and near["pressure_atm"].notna().all()
    assert near["distance"].is_monotonic_increasing


def test_flex_212_keeps_its_printed_atmosphere(raw):
    r = raw.set_index("test_no").loc[212]
    assert r["pressure_mmhg"] == 759.8 and (r["o2"], r["n2"], r["co2"], r["he"]) == (0.16, 0.84, 0.0, 0.0)


# ------------------------------------------------------------- schema rules (a)-(e)

@pytest.fixture(scope="module")
def sch() -> pd.DataFrame:
    return flex.load_schema()


def test_schema_file_is_current(sch):
    built = flex.build_schema_frame()
    assert list(sch.columns) == flex.SCHEMA_COLUMNS + flex.EXTRA_COLUMNS
    assert len(sch) == 276 and sch["test_id"].tolist() == built["test_id"].tolist()
    assert len(flex.SCHEMA_COLUMNS) == 24
    # every column of the committed file must equal a fresh build, not just a few of them
    fresh = built.copy()
    for col in ("support", "notes", "cool_flame_label", "cool_flame_quote", "extinction_wording"):
        fresh[col] = fresh[col].fillna("")
    for col in sch.columns:
        a, b = sch[col], fresh[col]
        if pd.api.types.is_numeric_dtype(b) and not pd.api.types.is_bool_dtype(b):
            pd.testing.assert_series_equal(a.astype(float), b.astype(float), check_names=False, rtol=1e-9, obj=col)
        else:
            assert a.astype("string").fillna("").tolist() == b.astype("string").fillna("").tolist(), col


def test_build_script_refuses_to_write_an_invalid_file(tmp_path, monkeypatch):
    import sys

    sys.path.insert(0, str(Path(flex.__file__).resolve().parents[1] / "scripts"))
    import build_flex_droplets as build

    good = flex.build_schema_frame()
    assert build.problems(good) == []                          # documented source gaps are not problems
    bad = good.copy()
    bad.loc[bad.index[0], "extinction_mode"] = "made_up_mode"
    bad.loc[bad.index[1], "test_id"] = bad.loc[bad.index[2], "test_id"]
    bad.loc[bad.index[3], "D_rad_ext_mm"] = bad.loc[bad.index[3], "D0_mm"] + 1.0
    found = build.problems(bad)
    assert any("made_up_mode" in p for p in found) and any("duplicate" in p for p in found)
    assert any("rule (c)" in p for p in found)
    monkeypatch.setattr(flex, "DATA", tmp_path)
    monkeypatch.setattr(flex, "build_schema_frame", lambda: bad)
    assert build.main() == 1 and not (tmp_path / "flex_droplets.csv").exists()
    monkeypatch.setattr(flex, "build_schema_frame", lambda: good)
    assert build.main() == 0 and (tmp_path / "flex_droplets.csv").exists()


def test_vocabulary(sch):
    assert schema.check_vocabulary(sch) == []
    assert sch["o2_is_ambient"].all()                           # every FLEX O2 value is chamber ambient


def test_rule_a(sch):
    assert schema.rule_a_no_ignition_has_no_K(sch) == []
    gaps = schema.rule_a_missing_K_but_ignited(sch)
    assert len(gaps) == 16                                      # dashes in the source, not imputed


def test_rule_a_catches_a_burning_rate_on_a_test_that_did_not_ignite(sch):
    """Table IX has no test that failed to ignite, so the rule is exercised with a planted row."""
    assert "no_ignition" not in set(sch["extinction_mode"])
    probe = sch.head(3).copy()
    probe.loc[probe.index[0], "extinction_mode"] = "no_ignition"          # keeps its burning rate: a violation
    probe.loc[probe.index[1], ["extinction_mode", "K_hot_mm2_s"]] = ["no_ignition", float("nan")]   # consistent
    assert probe.loc[probe.index[0], "K_hot_mm2_s"] == probe.loc[probe.index[0], "K_hot_mm2_s"]     # not NaN
    assert schema.rule_a_no_ignition_has_no_K(probe) == [probe.loc[probe.index[0], "test_id"]]


def test_extinction_mode_says_what_the_caption_says(sch):
    """A caption that reports no cool-flame evidence is not labelled "not stated"."""
    f = flex.load_flex()
    radiative = f["extinction_wording"] == "radiative"
    mode = dict(zip(f["test_no"], sch["extinction_mode"]))
    stated_none = sorted(f.loc[radiative & (f["cool_flame_label"] == "not_indicated") & (f["outcome"] == "Extinction"), "test_no"])
    assert stated_none == [130, 266, 267]
    assert {mode[n] for n in stated_none} == {"radiative_no_cool_flame_evidence"}
    silent = f.loc[radiative & (f["cool_flame_label"] == "") & (f["outcome"] == "Extinction"), "test_no"]
    assert {mode[n] for n in silent} <= {"radiative_cool_flame_not_stated"}
    assert not sch.loc[sch["extinction_mode"] == "radiative_no_cool_flame_evidence", "cool_flame_observed"].astype(bool).any()


def test_d2_line_never_goes_below_zero(f):
    from flamefall import aggregates

    lines = {r["test_id"]: aggregates.d2_line(r) for _, r in f.iterrows()}
    drawn = {t: line for t, line in lines.items() if line is not None}
    assert all(line["d2_end"] >= 0 for line in drawn.values())
    stopped = {t: line for t, line in drawn.items() if line["t_zero"] is not None}
    assert len(stopped) == 31                                    # printed K and burn time overshoot D0 squared
    for t, line in stopped.items():
        assert line["d2_end"] == 0.0 and 0 < line["t_zero"] < line["t_end"] and line["t_line_end"] == line["t_zero"], t
    whole = drawn["FLEX-002"]
    assert whole["t_zero"] is None and whole["t_line_end"] == whole["t_end"]


def test_rule_b(sch):
    assert schema.rule_b_cool_flame_needs_radiative_diameter(sch) == list(schema.KNOWN_SOURCE_GAPS["b"])


def test_rule_c(sch):
    assert schema.rule_c_diameters_ordered(sch) == []
    # exactly one row exceeds D0 by the table's 0.01 mm rounding step
    assert schema.rule_c_diameters_ordered(sch, tol=0.0) == ["FLEX-n-heptane-129"]


def test_rule_d_burner_flow_never_on_ambient_axis(sch):
    probe = sch.head(2).copy()
    probe.loc[probe.index[0], ["o2_mol_pct", "o2_is_ambient"]] = [85.0, False]   # inverse-flame burner feed
    kept = schema.ambient_o2_only(probe)
    assert len(kept) == 1 and kept["o2_mol_pct"].max() < 85
    with pytest.raises(ValueError):
        schema.ambient_o2_only(probe.drop(columns=["o2_is_ambient"]))


def test_rule_d_reads_the_flag_whatever_its_type(sch):
    probe = sch.head(6).copy()
    probe["o2_is_ambient"] = [1.0, 0.0, float("nan"), 1.0, 1.0, 0.0]     # a 1/0 column that gained a blank
    assert len(schema.ambient_o2_only(probe)) == 3
    probe["o2_is_ambient"] = probe["o2_is_ambient"].astype(object)
    probe["o2_is_ambient"] = ["1.0", "true", "yes", " TRUE ", "0", "maybe"]
    assert len(schema.ambient_o2_only(probe)) == 4
    for yes in (True, 1, 1.0, "1", "1.0", "True", "yes"):
        assert schema.is_ambient_flag(yes), yes
    for no in (False, 0, 0.0, None, float("nan"), pd.NA, "", "0", "no", "false", "85"):
        assert not schema.is_ambient_flag(no), no


def test_vocabulary_reports_blanks_and_unknowns_together(sch):
    probe = sch.head(4).copy()
    probe.loc[probe.index[0], "extinction_mode"] = None
    probe.loc[probe.index[1], "extinction_mode"] = "made_up_mode"
    probe.loc[probe.index[2], "verification"] = float("nan")
    probe.loc[probe.index[3], "verification"] = "trust me"
    found = schema.check_vocabulary(probe)                       # must list problems, not raise
    assert "extinction_mode is blank in 1 row(s)" in found and "verification is blank in 1 row(s)" in found
    assert any("made_up_mode" in p for p in found) and any("trust me" in p for p in found)


def test_rule_e_unverified_rows_excluded_from_models(sch):
    probe = sch.head(5).copy()
    probe.loc[probe.index[0], "verification"] = "unverified"
    probe.loc[probe.index[1], "verification"] = None          # a blank cell
    probe.loc[probe.index[2], "verification"] = "something else"
    kept = schema.model_rows_only(probe)
    assert len(kept) == 2 and set(kept["verification"]) == {"verified_live"}     # fails closed


