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


def test_search_with_no_match_returns_nothing_rather_than_a_guess():
    res = cat.answer("zebra accounting spreadsheet")
    assert res["n_hits"] == 0 and res["statements"] == []


def test_nearest_tests():
    near = cat.nearest_flex("Heptane", 21, 101.3, 0, 0, 3.0)
    assert len(near) == 8 and set(near["fuel"]) == {"Heptane"} and near["distance"].is_monotonic_increasing
    solid = cat.nearest_solid("PMMA", 30, 55, 20)
    assert solid.iloc[0]["investigation_id"] == "Saffire-VI" and "ambiguous" not in set(solid["outcome"])
    assert cat.solid_envelope()["o2"][1] < 34                   # nothing above 34% O2 for solids
