"""The exported JSON: current, complete, and faithful to the data files."""
from __future__ import annotations

import json
import re
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
        assert by_id["FM2"][col] == "", col                        # planned: no tested range is exported
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
    assert s["envelope_all"]["o2"][1] < 34                         # nothing above 34% O2 for solids
    for material, env in s["envelopes"].items():
        if env["n"]:
            assert env["flow"][0] > 0, material                    # no solid test in still gas


def test_ranking_export_and_worked_example():
    r = load("ranking.json")
    assert r["weights"] == ranking.WEIGHTS and sum(r["weights"].values()) == pytest.approx(1.0)
    assert [p["name"] for p in r["presets"]] == [p.name for p in ranking.PRESETS]
    golden = json.loads(export_web.GOLDEN_OUT.read_text(encoding="utf-8"))
    assert golden["worked_example"] == {"base": 0.637, "lunar": 0.687, "limit": 0.337}
    # the numbers inside the formula travel with the export, so nothing downstream retypes them
    assert r["hrr_log_range_w"] == list(ranking.HRR_LOG_RANGE_W) == [10.0, 3200.0]
    assert r["large_volume_bonus"] == ranking.LARGE_VOLUME_BONUS == 0.1
    assert r["cool_flame_min_d0_mm"] == ranking.COOL_FLAME_MIN_D0_MM == 2.0


def test_solid_export_says_which_pressures_are_assumed():
    s = load("solid.json")
    stated = [p["pressure_stated"] for p in s["points"]]
    assert all(isinstance(v, bool) for v in stated)
    assert sum(stated) == s["n_pressure_stated"] == int(cat.load_solid_points()["pressure_stated"].sum()) == 70
    assert "assumed" in s["pressure_note"] and "1 atm" in s["pressure_note"]


def test_reference_answers_cover_the_cases_review_found():
    g = json.loads(export_web.GOLDEN_OUT.read_text(encoding="utf-8"))
    stopped = [c for c in g["d2_line"] if c["line"] and c["line"]["t_zero"] is not None]
    assert stopped and all(c["line"]["d2_end"] == 0 for c in stopped)
    assert any(c["not_compared"][-1] == "pressure" for c in g["nearest_flex"])           # FLEX-114, ranked last
    assert any("initial diameter" in c["not_compared"] for c in g["nearest_flex"])
    assert all(c["not_compared"] == [""] * len(c["ids"]) for c in g["nearest_flex"] if c["k"] == 8)
    assert any("flow" in c["not_compared"] for c in g["nearest_solid"])
    fm2 = [row for case in g["rank_investigations"] for row in case["top"] if row["id"] == "FM2"]
    assert len(fm2) == len(g["rank_investigations"])
    assert all(row["relevance"] == 0 and set(row["why"].values()) == {"planned, not tested"} for row in fm2)
    still = [row for case in g["rank_investigations"] for row in case["top"] if "still gas only" in row["why"]["flow"]]
    assert still and all(0 <= row["terms"]["flow"] < 1 for row in still)
    filters = {a["query"]: a["filters"] for a in g["answer"]}
    assert filters["Which materials did the smoke detector miss?"] == {}
    assert filters["Which experiments ran above 80% oxygen?"] == {"o2_at_least": 80.0}


def test_model_cards_reach_the_app_without_per_row_predictions():
    for name in ("droplet_extinction", "droplet_cool_flame", "solid_sustained"):
        card = load(f"model_{name}.json")
        assert "oof" not in card and card["bootstrap"]["n"] == len(card["bootstrap"]["coef"])
        assert card["training_rows"] and card["envelope"] and card["distance"]["train_nn_p95"] > 0
    assert load("model_solid_sustained.json")["headline_auc"] < 0.6            # the failed model is exported as failed


def test_panel_numbers_are_in_the_source_each_panel_cites():
    panels = json.loads((ROOT / "data" / "panels.json").read_text(encoding="utf-8"))
    evidence = {e["id"]: e for e in json.loads((ROOT / "data" / "evidence.json").read_text(encoding="utf-8"))}
    # Smoke: each material's own fresh and aged value, read out of the statement the flight cites.
    # A value in the wrong row or the wrong column fails.
    def short(material: str) -> str:
        return material.split(" (")[0].lower().replace(" rubber", "")

    first, reflight = (evidence[flight["evidence_id"]]["statement"] for flight in panels["smoke"]["flights"])
    unaged, aged = first.split("unaged:")[1].split("After 720 s of ageing:")
    fresh = [(short(m), int(v)) for m, v in re.findall(r"([A-Za-z][A-Za-z ]*?) (\d+) nm", unaged)]
    stated = [{m: (v, int(a)) for (m, v), a in zip(fresh, re.findall(r"\d+", aged))},
              {short(m): (int(a), int(b)) for m, a, b in
               re.findall(r"([A-Za-z][A-Za-z ]*?) (\d+) to (\d+)", reflight.split("720 s:")[1])}]
    assert [len(s) for s in stated] == [4, 5]
    for flight, source in zip(panels["smoke"]["flights"], stated):
        assert {short(row["material"]) for row in flight["rows"]} == set(source), flight["id"]
        for row in flight["rows"]:
            assert (row["fresh"], row["aged"]) == source[short(row["material"])], f"{flight['id']} {row['material']}"

    # LUCI: the quoted table row prints lunar, normal gravity, then their ratio, in that order.
    for row in panels["luci"]["rows"]:
        printed = [float(v) for v in re.findall(r"(?<![\w.])\d*\.\d+", row["quote"].split("|")[-1])]
        assert len(printed) == 3, row["label"]
        to_mm = 10 if "cm/s" in row["quote"] else 1                    # the rod's row is printed in cm/s
        lunar, earth, ratio = printed
        assert earth * to_mm == pytest.approx(row["earth"]), row["label"]
        assert lunar * to_mm == pytest.approx(row["lunar"], abs=0.05 * to_mm), row["label"]   # the table rounds .92 to .9
        assert row["lunar"] / row["earth"] == pytest.approx(ratio, abs=0.02), row["label"]
        if exact := re.search(r"= ?(\d*\.\d+) mm/s", row["quote"]):
            assert float(exact.group(1)) == row["lunar"], row["label"]
    assert "non-monotonic" in panels["partial_gravity_wording"] and "FM2" in panels["partial_gravity_wording"]
    assert load("panels.json") == panels
