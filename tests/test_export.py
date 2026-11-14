"""The JSON the web app reads: current, complete, and faithful to the data files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_web  # noqa: E402

from flamefall import flex, ranking  # noqa: E402
from flamefall import catalogue as cat  # noqa: E402

DATA = ROOT / "web" / "src" / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built() -> dict:
    return export_web.build()


def test_committed_export_is_current(built):
    """Every committed file equals a fresh export, and no stray file sits beside them."""
    stale = [str(p.relative_to(ROOT)) for p, text in built.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    assert stale == [], f"run `python scripts/export_web.py`: {stale}"
    extra = [p.name for d in (export_web.DATA_OUT, export_web.PSI_OUT) for p in d.glob("*.json") if p not in built]
    assert extra == []
    assert export_web.main(["--check"]) == 0


def test_export_is_strict_json_with_missing_values_as_null(built):
    for path, text in built.items():
        assert "NaN" not in text and "Infinity" not in text, path.name
        json.loads(text)                                           # parses without the NaN extension
    rows = {r["test_id"]: r for r in load("flex.json")["rows"]}
    assert len(rows) == 276
    assert rows["FLEX-114"]["pressure_mmhg"] is None and rows["FLEX-114"]["pressure_kpa"] is None   # never 0
    assert rows["FLEX-212"]["d0_mm"] is None and rows["FLEX-212"]["burning_rate_mm2_s"] is None
    assert rows["FLEX-039"]["extinction_diameter_mm"] == 0         # printed as zero, so kept as zero


def test_flex_export_matches_the_table():
    f = flex.load_flex()
    data = load("flex.json")
    assert data["summary"]["outcomes"] == {"Extinction": 186, "Disruption": 62, "Completion": 28}
    assert [r["test_id"] for r in data["rows"]] == f["test_id"].tolist()
    assert sum(r["extinguished"] for r in data["rows"]) == 186
    for row, (_, src) in zip(data["rows"], f.iterrows()):
        assert row["outcome"] == src["outcome"] and row["o2"] == pytest.approx(src["o2"])
        assert (row["end_diameter_label"] == "Ext. diameter") == (src["outcome"] == "Extinction")
    assert data["printed_end_diameter"] == {"Completion": 15, "Disruption": 24, "Extinction": 159}


def test_catalogue_and_evidence_exports_match_their_sources():
    c = load("catalogue.json")
    inv = cat.load_investigations()
    assert [r["investigation_id"] for r in c["investigations"]] == inv["investigation_id"].tolist()
    assert c["counts"]["search_hits"] == 26 and c["counts"]["combustion_science"] == 24
    by_id = {r["investigation_id"]: r for r in c["investigations"]}
    for col in ("o2_min_pct", "o2_max_pct", "pressure_min_kPa", "pressure_max_kPa"):
        assert by_id["FM2"][col] == "", col                        # planned: no tested range reaches the app
    assert by_id["FM2"]["environments"] == ["Lunar"]
    ev = load("evidence.json")
    assert len(ev) == len(cat.load_evidence()) == c["counts"]["evidence"]
    burner = [e for e in ev if not e["o2_is_ambient"]]
    assert burner and all("burner" in e["statement"].lower() for e in burner)


def test_search_index_never_offers_a_burner_feed_as_ambient():
    s = load("search.json")
    docs = {d["doc_id"]: d for d in s["docs"]}
    assert docs["inverse-flame-85"]["o2_is_ambient"] is False
    assert len(s["docs"]) == len(s["vectors"]) == len(cat.corpus())
    assert len(s["vocab"]) == len(s["idf"])
    assert s["min_score"] == 0.04 and "co2" in s["synonyms"]


def test_solid_export_keeps_every_point_and_its_source():
    s = load("solid.json")
    points = cat.load_solid_points()
    assert len(s["points"]) == len(points) == s["n_total"]
    assert s["n_decided"] == int((points["outcome"] != "ambiguous").sum())
    assert all(p["source_ref"] for p in s["points"])
    assert s["envelope_all"]["o2"][1] < 34                         # nothing above 34% O2: the app's NO DATA band
    for material, env in s["envelopes"].items():
        if env["n"]:
            assert env["flow"][0] > 0, material                    # no solid test in still gas


def test_ranking_export_and_worked_example():
    r = load("ranking.json")
    assert r["weights"] == ranking.WEIGHTS and sum(r["weights"].values()) == pytest.approx(1.0)
    assert [p["name"] for p in r["presets"]] == [p.name for p in ranking.PRESETS]
    golden = json.loads(export_web.GOLDEN_OUT.read_text(encoding="utf-8"))
    assert golden["worked_example"] == {"base": 0.637, "lunar": 0.687, "limit": 0.337}


def test_model_cards_reach_the_app_without_per_row_predictions():
    for name in ("droplet_extinction", "droplet_cool_flame", "solid_sustained"):
        card = load(f"model_{name}.json")
        assert "oof" not in card and card["bootstrap"]["n"] == len(card["bootstrap"]["coef"])
        assert card["training_rows"] and card["envelope"] and card["distance"]["train_nn_p95"] > 0
    assert load("model_solid_sustained.json")["headline_auc"] < 0.6            # the failed model is exported as failed


def test_panel_numbers_are_in_the_source_each_panel_cites():
    panels = json.loads((ROOT / "data" / "panels.json").read_text(encoding="utf-8"))
    evidence = {e["id"]: e for e in json.loads((ROOT / "data" / "evidence.json").read_text(encoding="utf-8"))}
    for flight in panels["smoke"]["flights"]:
        statement = evidence[flight["evidence_id"]]["statement"]
        for row in flight["rows"]:
            for value in (row["fresh"], row["aged"]):
                assert str(value) in statement, f"{flight['id']} {row['material']} {value}"
    for row in panels["luci"]["rows"]:
        for value in (row["lunar"], row["earth"]):
            as_printed = {f"{value:g}".lstrip("0"), f"{value:.1f}".lstrip("0"), f"{value / 10:.2f}".lstrip("0")}
            assert any(v in row["quote"] for v in as_printed), f"{row['label']} {value}"
    assert "non-monotonic" in panels["partial_gravity_wording"] and "FM2" in panels["partial_gravity_wording"]
    assert load("panels.json") == panels
