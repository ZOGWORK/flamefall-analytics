"""The FLEX dataset: totals are recomputed from the CSV, never copied from a document."""
from __future__ import annotations

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
    assert round(126 / 157 * 100, 1) == 80.3 and round(60 / 119 * 100, 1) == 50.4


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
    assert r["pdf_page"] == 26 and f.set_index("test_no").loc[280, "pdf_page"] == 34
    assert f["pdf_page"].value_counts().sort_index().to_dict() == flex.ROWS_PER_PDF_PAGE


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


def test_disruption_is_never_extinction(f):
    assert f.loc[f["outcome"] == "Disruption", "extinguished"].sum() == 0
    sch = flex.build_schema_frame()
    dis = sch[sch["outcome"] == "Disruption"]
    assert set(dis["extinction_mode"]) == {"disruption"}
    assert dis["D_rad_ext_mm"].isna().all() and dis["D_diff_ext_mm"].isna().all()


# ------------------------------------------------------------- schema rules (a)-(e)

@pytest.fixture(scope="module")
def sch() -> pd.DataFrame:
    return flex.load_schema()


def test_schema_file_is_current(sch):
    built = flex.build_schema_frame()
    assert list(sch.columns) == flex.SCHEMA_COLUMNS + flex.EXTRA_COLUMNS
    assert len(sch) == 276 and sch["test_id"].tolist() == built["test_id"].tolist()
    assert len(flex.SCHEMA_COLUMNS) == 24
    pd.testing.assert_series_equal(sch["K_hot_mm2_s"], built["K_hot_mm2_s"], check_names=False)
    assert sch["extinction_mode"].tolist() == built["extinction_mode"].tolist()


def test_vocabulary(sch):
    assert schema.check_vocabulary(sch) == []
    assert sch["o2_is_ambient"].all()                           # every FLEX O2 value is chamber ambient


def test_rule_a(sch):
    assert schema.rule_a_no_ignition_has_no_K(sch) == []
    gaps = schema.rule_a_missing_K_but_ignited(sch)
    assert len(gaps) == 16                                      # dashes in the source, not imputed


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


def test_rule_e_unverified_rows_excluded_from_models(sch):
    probe = sch.head(3).copy()
    probe.loc[probe.index[0], "verification"] = "unverified"
    assert len(schema.model_rows_only(probe)) == 2
