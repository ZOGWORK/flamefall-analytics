"""The triage formula: the worked example from the research specification, and its properties."""
from __future__ import annotations

import pytest

from flamefall import ranking
from flamefall.ranking import Scenario

BASE = Scenario("worked example", "PMMA", 21.0, 101.0, 20.0, 0.0)


def test_weights_sum_to_one():
    assert sum(ranking.WEIGHTS.values()) == pytest.approx(1.0)
    assert ranking.WEIGHTS == {"M_O2": 0.30, "M_flow": 0.20, "H": 0.15, "D": 0.15, "G": 0.10, "C": 0.10}


def test_worked_example_terms():
    v = ranking.terms(BASE)["values"]
    assert v["M_O2"] == pytest.approx(1.0)
    assert v["M_flow"] == pytest.approx(1.0)
    assert v["H"] == pytest.approx(0.28, abs=0.005)        # log10(5) / log10(320)
    assert v["D"] == pytest.approx(0.3)
    assert v["G"] == pytest.approx(0.5)
    assert v["C"] == 0.0


def test_worked_example_scores():
    """PMMA rod, concurrent flow, 21% O2 at 101 kPa, 20 cm/s."""
    assert round(ranking.hazard(BASE), 3) == 0.637                                    # microgravity
    lunar = Scenario("lunar", "PMMA", 21.0, 101.0, 20.0, 0.16)
    assert round(ranking.hazard(lunar), 3) == 0.687
    at_limit = Scenario("limit", "PMMA", 13.6, 101.0, 20.0, 0.0)
    assert ranking.terms(at_limit)["values"]["M_O2"] == pytest.approx(0.0)
    assert round(ranking.hazard(at_limit), 3) == 0.337                                # non-zero at the limit


def test_terms_stay_in_unit_interval():
    for o2 in (5, 13.6, 21, 40, 100):
        for flow in (0, 0.5, 1, 30, 42, 55, 90):
            for g in (0, 0.16, 0.38, 1):
                s = Scenario("x", "PMMA", o2, 70.0, flow, g, "large sample (vehicle scale)", 20.0)
                for value in ranking.terms(s)["values"].values():
                    assert 0.0 <= value <= 1.0
                assert 0.0 <= ranking.hazard(s) <= 1.0


def test_still_gas_is_not_scored_zero():
    still = Scenario("still", "PMMA", 30.0, 70.0, 0.0, 0.0)
    assert ranking.terms(still)["values"]["M_flow"] == pytest.approx(0.4)


def test_flow_term_shape():
    f = lambda v: ranking.m_flow(Scenario("x", "PMMA", 21, 101, v, 0))[0]   # noqa: E731
    assert f(1) == f(15) == f(30) == 1.0
    assert f(55) == 0.0 and f(80) == 0.0
    assert f(42.5) == pytest.approx(0.5)
    assert 0.4 < f(0.5) < 1.0


def test_partial_pressure_not_fraction_drives_oxygen_term():
    """31% O2 at 54.1 kPa (16.8 kPa O2) scores lower on oxygen than 22% at 100 kPa (22 kPa O2)."""
    low_p = Scenario("a", "PMMA", 31.0, 54.1, 20, 0)
    high_p = Scenario("b", "PMMA", 22.0, 100.0, 20, 0)
    assert ranking.terms(low_p)["values"]["M_O2"] < ranking.terms(high_p)["values"]["M_O2"]


def test_unknown_material_is_flagged():
    t = ranking.terms(Scenario("x", "polycarbonate", 25, 101, 10, 0))
    assert t["flags"] and "floor" in t["flags"][0]
    assert not ranking.terms(BASE)["flags"]


def test_detection_term():
    kapton = Scenario("k", "Kapton", 21, 101, 10, 0)
    assert ranking.terms(kapton)["values"]["D"] == pytest.approx(0.9)
    big = Scenario("k", "Kapton", 21, 101, 10, 0, free_volume_m3=17)
    assert ranking.terms(big)["values"]["D"] == pytest.approx(1.0)


def test_cool_flame_term_only_for_large_n_alkane_droplets():
    drop = Scenario("d", "n-heptane droplet", 21, 101, 0, 0, is_droplet=True, droplet_d0_mm=3.0, n_alkane=True)
    small = Scenario("d", "n-heptane droplet", 21, 101, 0, 0, is_droplet=True, droplet_d0_mm=1.5, n_alkane=True)
    methanol = Scenario("d", "methanol droplet", 21, 101, 0, 0, is_droplet=True, droplet_d0_mm=3.0, n_alkane=False)
    assert ranking.terms(drop)["values"]["C"] == 1.0
    assert ranking.terms(small)["values"]["C"] == 0.0 and ranking.terms(methanol)["values"]["C"] == 0.0


def test_perturbed_weights_are_renormalised():
    variants = ranking.perturbed_weights()
    assert len(variants) == 12
    for _, w in variants:
        assert sum(w.values()) == pytest.approx(1.0) and min(w.values()) >= 0


def test_sensitivity_reports_order_changes():
    out = ranking.sensitivity(ranking.PRESETS)
    assert out["base_top"] == [n for n, _ in ranking.rank(ranking.PRESETS)[:3]]
    assert out["weight_sensitive"] == bool(out["changes"])
    for change in out["changes"]:
        assert change["top"] != out["base_top"]
