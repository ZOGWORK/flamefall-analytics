"""Catalogue, evidence table, retrieval and the solid-fuel test points."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from flamefall import catalogue as cat
from flamefall import schema

SCHEMA_COLUMNS = [
    "investigation_id", "full_name", "programme", "platform", "facility", "status", "date_start", "date_end", "pi",
    "objective", "materials", "sample_geometry", "o2_min_pct", "o2_max_pct", "pressure_min_kPa", "pressure_max_kPa",
    "flow_min_cm_s", "flow_max_cm_s", "flow_regime", "gravity_g", "n_tests", "key_result", "key_result_value",
    "key_result_unit", "psi_url", "primary_source_url", "primary_source_ref", "verification"]


@pytest.fixture(scope="module")
def inv() -> pd.DataFrame:
    return cat.load_investigations()


@pytest.fixture(scope="module")
def ev() -> pd.DataFrame:
    return cat.load_evidence()


def test_catalogue_has_the_research_schema(inv):
    for col in SCHEMA_COLUMNS:
        assert col in inv.columns, col
    assert inv["investigation_id"].is_unique
    assert (inv["objective"].str.len() <= 280).all()
    assert set(inv["status"]) <= {"complete", "operating", "planned", "flown_analysis_pending"}
    assert set(inv["verification"]) <= schema.ALLOWED_VERIFICATION


def test_catalogue_covers_the_required_investigations_with_ids_and_links(inv):
    by_id = inv.set_index("investigation_id")
    expect = {"FLEX": "PSI-69", "BASS-II": "PSI-25", "SAME": "PSI-102", "SAME-R": "PSI-101", "Saffire-I": "PSI-98",
              "Saffire-II": "PSI-99", "Saffire-III": "PSI-100", "ACME-BRE": "PSI-20", "ACME-CFI-G": "PSI-159",
              "ACME-FlameDesign": "PSI-10", "ACME-CLD": "PSI-21", "ACME-EFIELD": "PSI-22", "ACME-sFlame": "PSI-23"}
    for investigation, psi_id in expect.items():
        row = by_id.loc[investigation]
        assert row["psi_id"] == psi_id
        assert row["psi_url"] == f"https://psi.nasa.gov/physci/repo/data/investigations/{psi_id}"
        assert row["doi"].startswith("10.")
    assert int(inv["in_psi_search"].sum()) == 26
    assert int((inv["in_psi_search"] & inv["is_combustion"]).sum()) == 24


def test_every_row_has_a_source_link(inv):
    assert (inv["primary_source_url"].str.startswith("http") | inv["psi_url"].str.startswith("http")).all()


def test_planned_and_pending_statuses(inv):
    by_id = inv.set_index("investigation_id")
    assert by_id.loc["FM2", "status"] == "planned"
    assert by_id.loc["LUCI", "status"] == "flown_analysis_pending"
    assert by_id.loc["FM2", "n_tests"] == ""                  # nothing flown, so no test count
    # a planned test matrix is a note, never a tested range that ranking or tagging could read
    for col in ("o2_min_pct", "o2_max_pct", "pressure_min_kPa", "pressure_max_kPa"):
        assert by_id.loc["FM2", col] == "", col
    assert "Planned, not flown" in by_id.loc["FM2", "note"] and "37, 33, 29 and 25% O2" in by_id.loc["FM2", "note"]
    assert by_id.loc["FM2", "environments"] == ["Lunar"]      # tagged by its gravity alone
    ranked = cat.rank_investigations(34, 56.5, 5, "solid", 0.16).set_index("investigation_id")
    assert ranked.loc["FM2", "rel_oxygen"] == 0.0 and ranked.loc["FM2", "rel_pressure"] == 0.0


def test_nothing_is_imputed_where_psi_is_silent(inv):
    """Rows whose PSI table has no oxygen or pressure column keep those cells empty."""
    by_id = inv.set_index("investigation_id")
    for investigation in ["BASS", "SPICE", "SLICE", "ACME-CLD", "ACME-EFIELD", "PSI-117", "FLARE"]:
        assert by_id.loc[investigation, "o2_min_pct"] == "" and by_id.loc[investigation, "pressure_min_kPa"] == ""
    assert by_id.loc["BASS-II", "pressure_min_kPa"] == ""      # the PSI table has no pressure column
    assert by_id.loc["BASS-II", "pi"] == ""                    # the PSI record lists no principal investigator


def test_inverse_flame_oxygen_never_enters_an_ambient_range(inv, ev):
    by_id = inv.set_index("investigation_id")
    for investigation in ["ACME-CFI-G", "ACME-FlameDesign"]:
        assert float(by_id.loc[investigation, "o2_max_pct"]) <= 40.0
    assert pd.to_numeric(inv["o2_max_pct"], errors="coerce").max() <= 40.0
    burner = ev[~ev["o2_is_ambient"].astype(bool)]
    assert list(burner["id"]) == ["inverse-flame-85"]
    assert "burner feed" in burner.iloc[0]["statement"] and "not a cabin-like ambient" in burner.iloc[0]["statement"]
    # rule (d): the burner-feed row can never reach an ambient-oxygen axis
    assert "inverse-flame-85" not in set(cat.ambient_evidence()["id"])
    assert cat.ambient_evidence()["o2_is_ambient"].astype(bool).all()


def test_evidence_rows_are_complete(ev):
    assert ev["id"].is_unique and len(ev) >= 60
    for col in ["statement", "source_ref", "source_url", "verification", "read_level", "evidence_class"]:
        assert (ev[col].astype(str).str.len() > 0).all(), col
    assert ev["source_url"].str.startswith("http").all()
    assert set(ev["verification"]) <= schema.ALLOWED_VERIFICATION
    unverified = ev[ev["verification"] == "unverified"]
    assert unverified["read_level"].str.contains("not re-read").all()


def test_saffire_heat_release_labels(ev):
    by_id = ev.set_index("id")
    assert "Average heat release by fuel-consumption" in by_id.loc["saffire-hrr-fuelcal", "statement"]
    assert "averages, not peaks" in by_id.loc["saffire-hrr-fuelcal", "statement"]
    assert "Peak heat release by oxygen-consumption" in by_id.loc["saffire-hrr-o2cal", "statement"]


def test_smoke_tables_are_kept_apart(ev):
    by_id = ev.set_index("id")
    assert "80 nm" in by_id.loc["same1-table1", "statement"] and "42" not in by_id.loc["same1-table1", "statement"]
    assert "42 to 89" in by_id.loc["samer-table1", "statement"]
    assert by_id.loc["same1-table1", "investigation_id"] != by_id.loc["samer-table1", "investigation_id"]


def test_curated_key_results_point_at_evidence():
    curated = json.loads((cat.DATA / "investigations_curated.json").read_text(encoding="utf-8"))["investigations"]
    ids = set(cat.load_evidence()["id"])
    for c in curated:
        key = c.get("key_evidence", "")
        assert key in ("", "computed:flex") or key in ids, (c["investigation_id"], key)


def test_key_evidence_filed_under_another_flight_is_a_table_that_names_this_one():
    """Two multi-flight tables are filed under their first flight; each names the flight that cites it."""
    curated = json.loads((cat.DATA / "investigations_curated.json").read_text(encoding="utf-8"))["investigations"]
    ev = cat.load_evidence().set_index("id")
    elsewhere = {(c["investigation_id"], c["key_evidence"]) for c in curated
                 if c.get("key_evidence") in ev.index and ev.loc[c["key_evidence"], "investigation_id"] != c["investigation_id"]}
    assert elsewhere == {("Saffire-III", "saffire-spread-table"), ("Saffire-V", "saffire-hrr-fuelcal")}
    assert "Saffire III" in ev.loc["saffire-spread-table", "statement"]
    assert "V-2" in ev.loc["saffire-hrr-fuelcal", "statement"]


def test_a_plan_and_a_context_statement_carry_no_tested_range(ev):
    """FM2 has not flown and the brief's expected atmosphere is not a test: neither can match an oxygen filter."""
    by_id = ev.set_index("id")
    for entry in ("fm2-plan", "brief-atmospheres"):
        assert pd.isna(by_id.loc[entry, "o2_min_pct"]) and pd.isna(by_id.loc[entry, "o2_max_pct"]), entry
        assert pd.isna(by_id.loc[entry, "pressure_kpa"]), entry
    assert not ev.loc[ev["evidence_class"] == "context", "o2_max_pct"].notna().any()
    assert not {"fm2-plan", "brief-atmospheres"} & set(cat.ambient_evidence()["id"])
    for question in ("solid materials above 30% oxygen", "tests above 80% oxygen", "fabric at least 25% oxygen"):
        res = cat.answer(question)
        assert not {"fm2-plan", "brief-atmospheres"} & {s["doc_id"] for s in res["statements"]}, question
        assert "FM2" not in res["investigations"], question


def test_a_planned_investigation_earns_no_relevance(inv):
    ranked = cat.rank_investigations(34, 56.5, 0, "solid", 0.16).set_index("investigation_id")
    fm2 = ranked.loc["FM2"]
    assert fm2["relevance"] == 0.0 and fm2["rel_gravity"] == 0.0 and fm2["rel_fuel type"] == 0.0
    assert fm2["why_gravity"] == "planned, not tested"
    assert ranked.loc["LUCI", "rel_gravity"] == 1.0                 # flown in simulated lunar gravity
    assert "Lunar" in inv.set_index("investigation_id").loc["FM2", "environments"]   # tagged by its plan, never ranked
    assert "planned for" in cat.ENV_RULES["Lunar"]


def test_still_gas_relevance_fades_with_flow_instead_of_switching_off(inv):
    row = inv.set_index("investigation_id").loc["FLEX"]
    at = lambda flow: cat.relevance(row, 21, 101.3, flow, "droplet", 0)       # noqa: E731
    assert at(0)["terms"]["flow"] == 1.0 and at(0)["why"]["flow"] == "still gas, as tested"
    assert at(0.1)["terms"]["flow"] == pytest.approx(0.995)
    assert at(10)["terms"]["flow"] == pytest.approx(0.5) and "still gas only" in at(10)["why"]["flow"]
    assert at(20)["terms"]["flow"] == 0.0 and at(60)["terms"]["flow"] == 0.0


def test_a_question_naming_two_classes_is_not_filtered_to_one():
    question = "Which materials did the smoke detector miss?"
    assert cat.parse_filters(question) == {}
    res = cat.answer(question)
    assert "same-detector-misses" in {s["doc_id"] for s in res["statements"]}
    assert cat.parse_filters("solid fabric materials") == {"evidence_class": "solid"}


def test_an_oxygen_limit_filters_the_listed_investigations_too(inv):
    res = cat.answer("Which experiments ran above 80% oxygen?")
    assert res["filters"] == {"o2_at_least": 80.0}
    top = pd.to_numeric(inv.set_index("investigation_id")["o2_max_pct"], errors="coerce")
    for investigation in res["hits"].loc[res["hits"]["kind"] == "investigation", "investigation_id"]:
        assert top[investigation] >= 80, investigation
    kept = set(res["hits"].loc[res["hits"]["kind"] == "evidence", "doc_id"])
    assert kept <= {s["doc_id"] for s in cat.answer("Which experiments ran above 80% oxygen?", k=50)["statements"]}
    assert "inverse-flame-85" not in kept


# ------------------------------------------------------------------ solid test points

def test_solid_points_never_contain_droplet_or_gas_rows():
    s = cat.load_solid_points()
    assert set(s["investigation_id"]) <= {"BASS", "BASS-II", "Saffire-I", "Saffire-II", "Saffire-III", "Saffire-IV",
                                           "Saffire-V", "Saffire-VI", "SoFIE-GEL"}
    assert not s["material_class"].str.contains("heptane|methanol|droplet", case=False).any()
    assert s["point_id"].is_unique and len(s) == 313


def test_solid_point_labels():
    s = cat.load_solid_points()
    assert set(s["outcome"]) == {"sustained", "quenched", "blowoff", "no_ignition", "ambiguous"}
    assert s.loc[s["outcome"] == "ambiguous", "sustained"].isna().all()
    assert not s.loc[s["outcome"] == "ambiguous", "usable_for_model"].any()
    usable = s[s["usable_for_model"]]
    assert len(usable) == 179 and int(usable["sustained"].sum()) == 135
    assert usable[["o2_pct", "pressure_kPa", "flow_cm_s"]].notna().all().all()
    assert (s["outcome_quote"].str.len() > 0).all() and s["source_url"].str.startswith("http").all()
    assert (s["gravity_g"] == 0).all()                         # no partial-gravity point exists


def test_extinctions_use_the_end_of_test_oxygen():
    s = cat.load_solid_points()
    out = s[s["outcome"].isin(["quenched", "blowoff"]) & s["o2_final_pct"].notna()]
    assert (out["o2_at_outcome_pct"] == out["o2_final_pct"]).all()
    kept = s[s["outcome"].isin(["sustained", "no_ignition"])]
    assert (kept["o2_at_outcome_pct"] == kept["o2_pct"]).all()


# ------------------------------------------------------------------ relevance and retrieval

def test_relevance_rule_is_bounded_and_stated():
    assert sum(cat.RELEVANCE_WEIGHTS.values()) == pytest.approx(1.0)
    ranked = cat.rank_investigations(34, 56.5, 5, "solid", 0.16)
    assert ranked["relevance"].between(0, 1).all()
    assert ranked["relevance"].is_monotonic_decreasing
    assert "STDCE-1" not in set(ranked["investigation_id"])     # non-combustion hits are never ranked
    top = ranked.iloc[0]
    assert top["evidence_class"] in ("solid", "partial_g")
    flex_row = ranked.set_index("investigation_id").loc["FLEX"]
    assert flex_row["rel_fuel type"] == 0.0                     # droplets do not score as a solid-fuel match
    assert "not stated" in ranked.set_index("investigation_id").loc["BASS", "why_oxygen"]


def test_search_returns_sourced_statements():
    res = cat.answer("Did the smoke detector miss anything?")
    assert res["statements"] and res["statements"][0]["doc_id"] == "same-detector-misses"
    for s in res["statements"]:
        assert s["source_ref"] and s["source_url"].startswith("http")


def test_search_applies_a_stated_oxygen_filter():
    res = cat.answer("Which experiments tested solid materials above 25% oxygen?")
    assert res["filters"] == {"o2_at_least": 25.0, "evidence_class": "solid"}
    ids = {s["doc_id"] for s in res["statements"]}
    assert ids and "inverse-flame-85" not in ids               # a burner feed is not an ambient above 25%
    ev = cat.load_evidence().set_index("id")
    for i in ids:
        assert ev.loc[i, "o2_max_pct"] >= 25 and ev.loc[i, "evidence_class"] in ("solid", "partial_g")


def test_search_applies_a_fuel_class_named_without_an_oxygen_limit():
    """A question that names a class but no oxygen limit is still answered from that class only."""
    res = cat.answer("Did the smoke detector miss anything?")
    assert res["filters"] == {"evidence_class": "smoke"}
    ev = cat.load_evidence().set_index("id")
    assert res["statements"]
    assert all(ev.loc[s["doc_id"], "evidence_class"] == "smoke" for s in res["statements"])
    droplet = cat.answer("what happened to the droplet flames")
    assert droplet["filters"] == {"evidence_class": "droplet"} and droplet["statements"]
    classes = {"droplet"}
    for s in droplet["statements"]:
        cls = "droplet" if s["doc_id"].startswith("flex-") and s["doc_id"] not in ev.index else ev.loc[s["doc_id"], "evidence_class"]
        assert cls in classes, s["doc_id"]


def test_key_values_belong_to_their_own_investigation(inv):
    by_id = inv.set_index("investigation_id")
    assert (float(by_id.loc["Saffire-I", "key_result_value"]), by_id.loc["Saffire-I", "key_result_unit"]) == (0.18, "cm/s (Saffire I)")
    assert (float(by_id.loc["Saffire-III", "key_result_value"]), by_id.loc["Saffire-III", "key_result_unit"]) == (0.23, "cm/s (Saffire III)")
    assert (float(by_id.loc["Saffire-IV", "key_result_value"]), by_id.loc["Saffire-IV", "key_result_unit"]) == (3150.0, "W (average, IV-1)")
    assert (float(by_id.loc["Saffire-V", "key_result_value"]), by_id.loc["Saffire-V", "key_result_unit"]) == (2800.0, "W (average, V-2)")
    for investigation, value in [("Saffire-III", "0.23 cm/s"), ("Saffire-V", "2,800 W")]:
        assert value in by_id.loc[investigation, "key_result"]          # the number is in the statement shown


def test_counts_are_of_tests_only(inv):
    by_id = inv.set_index("investigation_id")
    assert int(by_id.loc["BASS", "n_tests"]) == 121              # 122 rows, one of them "SOOT Cleaning"
    assert "89 test points" in by_id.loc["BASS", "n_tests_source"]
    assert by_id.loc["SLICE", "n_tests"] == ""                   # PSI lists test days, not tests
    assert "test days" in by_id.loc["SLICE", "range_source"]


def test_co2_in_a_question_is_not_read_as_an_oxygen_limit():
    assert cat.parse_filters("which droplets burned in CO2 above 30%?") == {"evidence_class": "droplet"}
    assert cat.parse_filters("tests with o2 above 30%") == {"o2_at_least": 30.0}
    assert cat.parse_filters("oxygen below 15 percent for solids") == {"o2_at_most": 15.0, "evidence_class": "solid"}


def test_catalogue_counts_use_distinct_tests(inv):
    by_id = inv.set_index("investigation_id")
    assert int(by_id.loc["ACME-CFI-G", "n_tests"]) == 179 + 154          # not the 1,015 lines of the padded file
    assert int(by_id.loc["CFI", "n_tests"]) == 79
    assert int(by_id.loc["ACME-EFIELD", "n_tests"]) == 219
    assert int(by_id.loc["SPICE", "n_tests"]) == 435
    for investigation in ("CFI", "ACME-EFIELD", "SPICE"):
        assert "exact repeats" in by_id.loc[investigation, "n_tests_source"]
    assert "padding rows" in by_id.loc["ACME-CFI-G", "n_tests_source"]


def test_search_with_no_match_returns_nothing_rather_than_a_guess():
    res = cat.answer("zebra accounting spreadsheet")
    assert res["n_hits"] == 0 and res["statements"] == []


def test_nearest_tests():
    near = cat.nearest_flex("Heptane", 21, 101.3, 0, 0, 3.0)
    assert len(near) == 8 and set(near["fuel"]) == {"Heptane"} and near["distance"].is_monotonic_increasing
    solid = cat.nearest_solid("PMMA", 30, 55, 20)
    assert solid.iloc[0]["investigation_id"] == "Saffire-VI" and "ambiguous" not in set(solid["outcome"])
    assert cat.solid_envelope()["o2"][1] < 34                   # nothing above 34% O2 for solids


def test_a_missing_value_is_never_a_perfect_match():
    f = cat.flex.load_flex()
    no_pressure = f.loc[f["pressure_kpa"].isna(), "test_id"]
    assert list(no_pressure) == ["FLEX-114"]
    fuel, o2, co2, he = f.loc[f["test_id"] == "FLEX-114", ["fuel", "o2_pct", "co2_pct", "he_pct"]].iloc[0]
    n = int((f["fuel"] == fuel).sum())
    near = cat.nearest_flex(fuel, o2, 101.3, co2, he, None, k=n)
    assert near.iloc[-1]["test_id"] == "FLEX-114" and near.iloc[-1]["not_compared"] == "pressure"   # last, not first
    assert (near.iloc[:-1]["not_compared"] == "").all() and near.iloc[:-1]["distance"].is_monotonic_increasing
    with_d0 = cat.nearest_flex(fuel, o2, 101.3, co2, he, 3.0, k=n)
    partial = with_d0[with_d0["not_compared"] != ""]
    assert set(partial["not_compared"]) <= {"pressure", "initial diameter", "pressure, initial diameter"}
    assert len(partial) == int((f.loc[f["fuel"] == fuel, "d0_mm"].isna() | f.loc[f["fuel"] == fuel, "pressure_kpa"].isna()).sum())
    assert (with_d0.tail(len(partial))["not_compared"] != "").all()

    s = cat.load_solid_points()
    pool = s[(s["outcome"] != "ambiguous") & (s["material_class"] == "PMMA")]
    solid = cat.nearest_solid("PMMA", 17, 101.3, 10, k=len(pool))
    stated = solid[solid["not_compared"] == ""]
    assert len(stated) == int(pool["flow_cm_s"].notna().sum()) and stated["flow_cm_s"].notna().all()
    assert (solid.head(len(stated))["not_compared"] == "").all()
    assert set(solid.tail(len(solid) - len(stated))["not_compared"]) == {"flow"}


def test_solid_points_say_whether_their_pressure_is_stated():
    s = cat.load_solid_points()
    assert s["pressure_stated"].dtype == bool
    assert int(s["pressure_stated"].sum()) == 70 and int((~s["pressure_stated"]).sum()) == 243
    bass2 = s[s["investigation_id"].isin(["BASS", "BASS-II"])]
    assert bass2.loc[bass2["pressure_stated"], "source_ref"].str.contains("Table 7.1").all()
    assert not bass2.loc[~bass2["pressure_stated"], "source_ref"].str.contains("Table 7.1").any()
    assert list(s.loc[~s["pressure_stated"] & ~s["investigation_id"].isin(["BASS", "BASS-II"]), "point_id"]) == ["SAF6-1"]
