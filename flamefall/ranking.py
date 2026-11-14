"""Scenario triage score. A stated, auditable rule; never a verdict.

    Hazard = 0.30 M_O2 + 0.20 M_flow + 0.15 H + 0.15 D + 0.10 G + 0.10 C

Every term is in [0, 1] (1 = more hazardous). Every weight and every lookup value below is a
DESIGN CHOICE, stated as one, and tested for whether the ordering of scenarios survives changing
it. The score orders scenarios for attention. It does not say that
any scenario is acceptable.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

WEIGHTS = {"M_O2": 0.30, "M_flow": 0.20, "H": 0.15, "D": 0.15, "G": 0.10, "C": 0.10}
TERM_LABEL = {
    "M_O2": "Oxygen margin", "M_flow": "Flow margin", "H": "Heat-release scale",
    "D": "Detection difficulty", "G": "Gravity", "C": "Invisible burning",
}

P_O2_REF_KPA = 21.2            # sea-level air
# Lowest oxygen at which a flame was sustained, by material, as an O2 partial pressure.
# PMMA: 13.6 % at 101 kPa (BASS-II concurrent rod). SIBAL: 16.9 % at 101.3 kPa (BASS-II Table 7.1).
P_O2_MIN_KPA = {
    "PMMA": (13.6 / 100 * 101.0, "BASS-II concurrent PMMA rod, 13.6% O2 at 101 kPa (NASA/TM-20210011385 §6.1; "
                                  "ASGSR 2014 poster)"),
    "SIBAL-cotton": (16.9 / 100 * 101.3, "BASS-II SIBAL fabric, lowest oxygen with a flame, 16.9% at 1 atm "
                                         "(NASA/TM-20210011385 Table 7.1)"),
}
P_O2_FLOOR_KPA = 13.6 / 100 * 101.0   # cross-material floor, used (and flagged) when a material has no measured minimum

FLOW_BAND = (1.0, 30.0)        # cm/s: typical ventilation band
FLOW_ZERO_AT = 55.0            # cm/s: blowoff side
QUIESCENT_SCORE = 0.4          # still gas is not scored zero: flames burned for minutes in still gas above ~25% O2

HRR_SCALE_W = {
    "small sample (glovebox scale)": (50.0, "about 50 W, the figure given for BASS-II-scale flames in ICES-2019-101 "
                                            "(not re-verified; the summary memo says most tests were well below 100 W)"),
    "large sample (vehicle scale)": (3217.0, "3,217 W peak, Saffire VI SIBAL by oxygen-consumption calorimetry "
                                             "(ICES-2024-365 Table 2)"),
}
DETECTION = {   # material -> (score, reason)
    "Kapton": (0.9, "station-type detector missed half of Kapton smoke tests"),
    "Teflon": (0.9, "station-type detector missed two-thirds of Teflon smoke tests"),
    "cellulose": (0.5, "larger particles, visible to light-scattering detectors"),
    "silicone": (0.5, "larger particles, visible to light-scattering detectors"),
}
DETECTION_DEFAULT = (0.3, "no detector-miss evidence for this material")
LARGE_VOLUME_M3 = 15.0
GRAVITY_SCORE = {0.16: 1.0, 0.38: 0.7, 0.0: 0.5, 1.0: 0.2}
GRAVITY_NAME = {0.0: "0 g (microgravity)", 0.16: "Lunar (0.16 g)", 0.38: "Mars (0.38 g)", 1.0: "Earth (1 g)"}


@dataclass(frozen=True)
class Scenario:
    name: str
    material: str                  # "PMMA", "SIBAL-cotton", "Kapton", "n-heptane droplet", ...
    o2_pct: float
    pressure_kpa: float
    flow_cm_s: float
    gravity_g: float               # 0, 0.16, 0.38 or 1
    hrr_scale: str = "small sample (glovebox scale)"
    free_volume_m3: float = 1.0
    is_droplet: bool = False
    droplet_d0_mm: float = 0.0
    n_alkane: bool = False


def m_o2(s: Scenario) -> tuple[float, str, bool]:
    p = s.o2_pct / 100 * s.pressure_kpa
    if s.material in P_O2_MIN_KPA:
        p_min, why = P_O2_MIN_KPA[s.material]
        flagged = False
    else:
        p_min, why, flagged = P_O2_FLOOR_KPA, "no measured minimum for this material: cross-material floor used", True
    value = min(1.0, max(0.0, (p - p_min) / (P_O2_REF_KPA - p_min)))
    return value, f"O2 partial pressure {p:.1f} kPa against a minimum of {p_min:.1f} kPa ({why})", flagged


def m_flow(s: Scenario) -> tuple[float, str]:
    v = s.flow_cm_s
    lo, hi = FLOW_BAND
    if v <= 0:
        return QUIESCENT_SCORE, "still gas: scored 0.4, not 0, because flames have burned in still gas at raised oxygen"
    if v < lo:
        return QUIESCENT_SCORE + (1 - QUIESCENT_SCORE) * v / lo, f"{v:g} cm/s, below the {lo:g}-{hi:g} cm/s band"
    if v <= hi:
        return 1.0, f"{v:g} cm/s, inside the {lo:g}-{hi:g} cm/s ventilation band"
    if v < FLOW_ZERO_AT:
        return (FLOW_ZERO_AT - v) / (FLOW_ZERO_AT - hi), f"{v:g} cm/s, towards the blowoff side"
    return 0.0, f"{v:g} cm/s, at or beyond {FLOW_ZERO_AT:g} cm/s"


def h_term(s: Scenario) -> tuple[float, str]:
    watts, why = HRR_SCALE_W[s.hrr_scale]
    value = min(1.0, max(0.0, math.log10(watts / 10) / math.log10(3200 / 10)))
    return value, why


def d_term(s: Scenario) -> tuple[float, str]:
    score, why = DETECTION.get(s.material, DETECTION_DEFAULT)
    if s.free_volume_m3 > LARGE_VOLUME_M3:
        score, why = min(1.0, score + 0.1), why + "; +0.1 for a free volume above 15 m3 (far-field alarm took 981 s in Saffire VI)"
    return score, why


def g_term(s: Scenario) -> tuple[float, str]:
    g = min(GRAVITY_SCORE, key=lambda k: abs(k - s.gravity_g))
    note = "" if g in (0.0, 1.0) else " No combustion test in this gravity exists in PSI."
    return GRAVITY_SCORE[g], f"{GRAVITY_NAME[g]}.{note}"


def c_term(s: Scenario) -> tuple[float, str]:
    if s.is_droplet and s.n_alkane and s.droplet_d0_mm >= 2.0:
        return 1.0, "large n-alkane droplet: can keep burning as a cool flame after the visible flame goes out"
    return 0.0, "solid fuel, or a droplet outside the cool-flame regime"


def terms(s: Scenario) -> dict:
    mo2, why_o2, flagged = m_o2(s)
    out = {"M_O2": (mo2, why_o2), "M_flow": m_flow(s), "H": h_term(s), "D": d_term(s), "G": g_term(s), "C": c_term(s)}
    return {"values": {k: v[0] for k, v in out.items()}, "why": {k: v[1] for k, v in out.items()},
            "flags": ["oxygen minimum is a cross-material floor, not measured for this material"] if flagged else []}


def hazard(s: Scenario, weights: dict | None = None) -> float:
    w = weights or WEIGHTS
    values = terms(s)["values"]
    return sum(w[k] * values[k] for k in WEIGHTS)


def perturbed_weights(step: float = 0.10) -> list[tuple[str, dict]]:
    """Each weight moved up and down by `step`, then all renormalised to sum to 1."""
    out = []
    for key in WEIGHTS:
        for sign in (+1, -1):
            w = dict(WEIGHTS)
            w[key] = max(0.0, w[key] + sign * step)
            total = sum(w.values())
            out.append((f"{key} {'+' if sign > 0 else '-'}{step:.2f}", {k: v / total for k, v in w.items()}))
    return out


def rank(scenarios: list[Scenario], weights: dict | None = None) -> list[tuple[str, float]]:
    scored = [(s.name, hazard(s, weights)) for s in scenarios]
    return sorted(scored, key=lambda t: (-t[1], t[0]))


def sensitivity(scenarios: list[Scenario], weights: dict | None = None, top: int = 3, step: float = 0.10) -> dict:
    """Does the top-`top` order survive moving each weight by +/- `step`?"""
    base_w = weights or WEIGHTS
    base = [n for n, _ in rank(scenarios, base_w)[:top]]
    changes = []
    for key in WEIGHTS:
        for sign in (+1, -1):
            w = dict(base_w)
            w[key] = max(0.0, w[key] + sign * step)
            total = sum(w.values())
            w = {k: v / total for k, v in w.items()}
            order = [n for n, _ in rank(scenarios, w)[:top]]
            if order != base:
                changes.append({"change": f"{TERM_LABEL[key]} weight {'+' if sign > 0 else '-'}{step:.2f}", "top": order})
    return {"base_top": base, "weight_sensitive": bool(changes), "changes": changes}


PRESETS = [
    Scenario("Lunar-base cabin, thin fabric, low ventilation", "SIBAL-cotton", 34.0, 56.5, 5.0, 0.16,
             "small sample (glovebox scale)", 50.0),
    Scenario("Pressurised rover, acrylic panel, cabin fan on", "PMMA", 30.0, 70.3, 20.0, 0.16,
             "small sample (glovebox scale)", 10.0),
    Scenario("Large fabric fire in a cargo-vehicle volume", "SIBAL-cotton", 31.0, 54.1, 20.0, 0.0,
             "large sample (vehicle scale)", 16.7),
    Scenario("Station cabin baseline, acrylic rod", "PMMA", 21.0, 101.3, 10.0, 0.0,
             "small sample (glovebox scale)", 100.0),
    Scenario("Overheated wire insulation, station cabin", "Kapton", 21.0, 101.3, 10.0, 0.0,
             "small sample (glovebox scale)", 100.0),
]


def as_dict(s: Scenario) -> dict:
    return asdict(s)
