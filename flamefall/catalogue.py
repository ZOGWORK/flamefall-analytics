"""Investigation catalogue, evidence table, retrieval and the stated relevance rule.

The "SI layer" here is deliberately not a chatbot. It does three auditable things:
  * retrieval  - TF-IDF search over catalogue rows and sourced evidence statements;
  * summary    - extractive: the answer is the retrieved statements themselves, each with its source;
  * ranking    - a stated rule with visible weights (`relevance`), never a hidden score.
Nothing in this module can produce a number that is not already in a data file.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import flex, psi, schema

DATA = Path(__file__).resolve().parents[1] / "data"

EVIDENCE_CLASS_LABEL = {
    "droplet": "Liquid droplets", "gas": "Gas flames", "solid": "Solid materials", "smoke": "Smoke and detection",
    "partial_g": "Partial gravity", "context": "Context", "n/a": "Not combustion",
}
FUEL_TYPE_LABEL = {"droplet": "Droplet", "gas": "Gas", "solid": "Solid", "smoke": "Smoke / aerosol",
                   "model": "Modelling study", "not combustion": "Not combustion"}

# ---- environment tags: a stated rule applied to each row's own ranges (never hand-assigned)
EXPLORATION_O2_PCT = 30.0          # challenge brief: Moon atmosphere likely 30% O2 or more
EXPLORATION_P_KPA = 70.3           # ... at 10.2 psi (70.3 kPa) or less
ENV_RULES = {
    "Station": "tested at about 21% O2 (range includes 20.5 to 21.5%)",
    "Spacecraft": "vehicle-scale burn in a cargo spacecraft, or smoke detection",
    "Lunar": f"tested in, or planned for, partial gravity, or tested at O2 of {EXPLORATION_O2_PCT:g}% or more, or at {EXPLORATION_P_KPA:g} kPa or less",
    "Rover": f"tested at O2 of {EXPLORATION_O2_PCT:g}% or more, or at {EXPLORATION_P_KPA:g} kPa (10.2 psi) or less",
}


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) else f


def environment_tags(row: pd.Series) -> list[str]:
    o2_lo, o2_hi = _num(row["o2_min_pct"]), _num(row["o2_max_pct"])
    p_lo, g = _num(row["pressure_min_kPa"]), _num(row["gravity_g"])
    tags = []
    if o2_lo is not None and o2_lo <= 21.5 and o2_hi >= 20.5:
        tags.append("Station")
    if row["facility_group"] == "Cygnus" or row["fuel_type"] == "smoke":
        tags.append("Spacecraft")
    exploration = (o2_hi is not None and o2_hi >= EXPLORATION_O2_PCT) or (p_lo is not None and p_lo <= EXPLORATION_P_KPA)
    if exploration or (g is not None and 0.05 < g < 0.5):
        tags.append("Lunar")
    if exploration:
        tags.append("Rover")
    return tags


@lru_cache(maxsize=1)
def load_investigations() -> pd.DataFrame:
    df = pd.read_csv(DATA / "investigations.csv", keep_default_na=False)
    df["in_psi_search"] = df["in_psi_search"].astype(str).str.lower() == "true"
    df["environments"] = df.apply(environment_tags, axis=1)
    df["is_combustion"] = df["evidence_class"] != "n/a"
    return df


@lru_cache(maxsize=1)
def load_evidence() -> pd.DataFrame:
    df = pd.DataFrame(json.loads((DATA / "evidence.json").read_text(encoding="utf-8")))
    for col in ("o2_min_pct", "o2_max_pct", "pressure_kpa", "flow_cm_s", "gravity_g", "value"):
        if col not in df:
            df[col] = np.nan
    return df


def ambient_evidence() -> pd.DataFrame:
    """Evidence usable on an ambient-oxygen axis: burner-feed values (o2_is_ambient = False) are removed."""
    e = load_evidence()
    return schema.ambient_o2_only(e[e["o2_max_pct"].notna()], "o2_max_pct")


@lru_cache(maxsize=1)
def load_solid_points() -> pd.DataFrame:
    df = pd.read_csv(DATA / "solid_test_points.csv")
    df["usable_for_model"] = df["usable_for_model"].astype(str).str.lower() == "true"
    df["pressure_stated"] = df["pressure_stated"].astype(str).str.lower() == "true"
    for col in ("notes", "outcome_quote", "flow_direction", "geometry"):
        df[col] = df[col].fillna("")
    return df


def counts() -> dict:
    inv, s = load_investigations(), psi.summary()
    ev = load_evidence()
    return {**s, "catalogue_rows": int(len(inv)), "outside_psi_search": int((~inv["in_psi_search"]).sum()),
            "evidence": int(len(ev)), "evidence_verified": int((ev["verification"] == "verified_live").sum()),
            "evidence_unverified": int((ev["verification"] == "unverified").sum()),
            "evidence_index": int((ev["verification"] == "index").sum())}


# =============================================================================== relevance rule

RELEVANCE_WEIGHTS = {"oxygen": 0.35, "pressure": 0.20, "fuel type": 0.20, "flow": 0.15, "gravity": 0.10}


def _range_match(value: float, lo, hi, fade: float) -> tuple[float, str]:
    lo, hi = _num(lo), _num(hi)
    if lo is None or hi is None:
        return 0.0, "not stated for this investigation"
    if lo <= value <= hi:
        return 1.0, f"inside the tested range {lo:g} to {hi:g}"
    gap = lo - value if value < lo else value - hi
    return max(0.0, 1 - gap / fade), f"{gap:.1f} outside the tested range {lo:g} to {hi:g}"


def _flow_match(row: pd.Series, flow_cm_s: float) -> tuple[float, str]:
    if row["flow_regime"] != "quiescent":
        return _range_match(flow_cm_s, row["flow_min_cm_s"], row["flow_max_cm_s"], fade=20.0)
    # tested in still gas only: a full match there, fading over 20 cm/s like any other range
    if flow_cm_s == 0:
        return 1.0, "still gas, as tested"
    return max(0.0, 1 - flow_cm_s / 20.0), f"tested in still gas only; the scenario has {flow_cm_s:g} cm/s of flow"


PLANNED = "planned, not tested"


def relevance(row: pd.Series, o2_pct: float, pressure_kpa: float, flow_cm_s: float, evidence_class: str,
              gravity_g: float, weights: dict | None = None) -> dict:
    """How closely one investigation's tested conditions match a scenario. Terms are in [0, 1].

    A planned investigation has tested nothing, so it matches nothing: every term is zero.
    """
    w = weights or RELEVANCE_WEIGHTS
    if row["status"] == "planned":
        return {"score": 0.0, "terms": {k: 0.0 for k in RELEVANCE_WEIGHTS}, "why": {k: PLANNED for k in RELEVANCE_WEIGHTS}}
    t = {
        "oxygen": _range_match(o2_pct, row["o2_min_pct"], row["o2_max_pct"], fade=10.0),
        "pressure": _range_match(pressure_kpa, row["pressure_min_kPa"], row["pressure_max_kPa"], fade=40.0),
        "flow": _flow_match(row, flow_cm_s),
    }
    cls = row["evidence_class"]
    if cls == evidence_class or (cls == "partial_g" and evidence_class == "solid"):
        t["fuel type"] = (1.0, "same kind of fuel")
    elif cls == "smoke":
        t["fuel type"] = (0.5, "smoke and detection evidence applies to any burning or overheating material")
    else:
        t["fuel type"] = (0.0, "different kind of fuel: physics does not transfer")
    g = _num(row["gravity_g"])
    if g is None:
        t["gravity"] = (0.0, "not a flight test")
    elif abs(g - gravity_g) < 0.02:
        t["gravity"] = (1.0, "same gravity level")
    else:
        t["gravity"] = (0.0, f"tested at {g:g} g, scenario is {gravity_g:g} g")
    score = sum(w[k] * t[k][0] for k in w)
    return {"score": score, "terms": {k: v[0] for k, v in t.items()}, "why": {k: v[1] for k, v in t.items()}}


def rank_investigations(o2_pct, pressure_kpa, flow_cm_s, evidence_class, gravity_g, weights=None) -> pd.DataFrame:
    inv = load_investigations()
    inv = inv[inv["is_combustion"]].copy()
    rel = inv.apply(lambda r: relevance(r, o2_pct, pressure_kpa, flow_cm_s, evidence_class, gravity_g, weights), axis=1)
    inv["relevance"] = [r["score"] for r in rel]
    for k in RELEVANCE_WEIGHTS:
        inv[f"rel_{k}"] = [r["terms"][k] for r in rel]
        inv[f"why_{k}"] = [r["why"][k] for r in rel]
    return inv.sort_values(["relevance", "investigation_id"], ascending=[False, True]).reset_index(drop=True)


# =============================================================================== retrieval

SYNONYMS = {
    "fire": "flame burning combustion", "burn": "burning flame sustained spread", "smoke": "aerosol particle detector",
    "detector": "detection alarm smoke", "detection": "detector alarm smoke", "moon": "lunar partial gravity",
    "lunar": "moon partial gravity", "mars": "martian partial gravity", "plastic": "pmma acrylic",
    "acrylic": "pmma", "fabric": "sibal cotton nomex cloth", "cloth": "sibal cotton fabric", "cotton": "sibal fabric",
    "oxygen": "o2", "co2": "carbon dioxide dilution", "helium": "he dilution", "suppression": "extinction quench dilution",
    "extinguish": "extinction quench blowoff", "invisible": "cool flame", "airflow": "flow ventilation",
    "ventilation": "flow airflow fan", "rover": "exploration atmosphere reduced pressure",
    "habitat": "exploration atmosphere reduced pressure lunar", "wire": "kapton teflon insulation",
    "soot": "smoke particle", "droplet": "liquid fuel heptane methanol", "liquid": "droplet",
    "solid": "pmma sibal fabric rod slab material", "limit": "minimum flammability boundary",
}


def flex_documents() -> list[dict]:
    """Statements computed from the FLEX data on the spot, so search can cite them like any other evidence."""
    s = flex.summary()
    f = flex.load_flex()
    m, h, c = s["by_fuel"]["Methanol"], s["by_fuel"]["Heptane"], s["cool_flame"]
    src = f"{flex.REPORT}, Table IX (computed from the CSV)"
    docs = [
        ("flex-outcomes", f"FLEX droplet burns: {s['outcomes']['Extinction']} of {s['n']} tests ended in visible-flame "
         f"extinction, {s['outcomes']['Disruption']} in disruption and {s['outcomes']['Completion']} burned to completion.", src),
        ("flex-fuels", f"Methanol droplets extinguished in {m['Extinction']} of {m['n']} tests ({m['extinction_share']:.1%}); "
         f"n-heptane droplets in {h['Extinction']} of {h['n']} ({h['extinction_share']:.1%}). Fuel chemistry matters as much "
         "as atmosphere.", src),
        ("flex-cool", f"Cool flames, invisible burning: of {s['heptane_extinctions']} n-heptane tests logged as Extinction, "
         f"{c['indicated']} show evidence of cool-flame burning after the visible flame went out, {c['not_indicated']} "
         f"show none, {c['unclear']} are unclear.", f"{flex.REPORT}, Appendix B figure captions"),
        ("flex-dilution", f"Dilution of the atmosphere: carbon dioxide was present in {s['co2_tests']} FLEX tests (up to "
         f"{s['ranges']['co2'][1]:.2f} mole fraction) and helium in {s['he_tests']} (up to {s['ranges']['he'][1]:.2f}). "
         "CO2 and helium were never combined in one test.", src),
        ("flex-envelope", f"FLEX tested ambient oxygen from {s['ranges']['o2'][0]:.0%} to {s['ranges']['o2'][1]:.0%} and "
         f"pressure from {s['ranges']['pressure_mmhg'][0] / 760:.2f} to {s['ranges']['pressure_mmhg'][1] / 760:.2f} atm, "
         "all in still gas and microgravity.", src),
    ]
    for fuel in ("Methanol", "Heptane"):
        g = f[(f["fuel"] == fuel) & (f["co2"] > 0)]
        a = f[(f["fuel"] == fuel) & (f["co2"] == 0) & (f["he"] == 0)]
        docs.append((f"flex-co2-{fuel.lower()}",
                     f"{fuel} with CO2 in the atmosphere: {int(g['extinguished'].sum())} of {len(g)} tests ended in "
                     f"extinction ({g['extinguished'].mean():.0%}); with nitrogen only: {int(a['extinguished'].sum())} of "
                     f"{len(a)} ({a['extinguished'].mean():.0%}). Other conditions differ between the groups.", src))
    return [dict(doc_id=i, kind="evidence", investigation_id="FLEX", title="FLEX (computed)", text=t, source_ref=r,
                 source_url=flex.RECORD_URL, verification="verified_live") for i, t, r in docs]


@lru_cache(maxsize=1)
def corpus() -> pd.DataFrame:
    docs = flex_documents()
    for _, e in load_evidence().iterrows():
        docs.append(dict(doc_id=e["id"], kind="evidence", investigation_id=e["investigation_id"],
                         title=e["investigation_id"], text=e["statement"], source_ref=e["source_ref"],
                         source_url=e["source_url"], verification=e["verification"]))
    for _, r in load_investigations().iterrows():
        if not r["is_combustion"]:
            continue
        text = " ".join(str(x) for x in [r["full_name"], r["objective_full"] or r["objective"], r["materials"],
                                         r["sample_geometry"], r["facility"]] if x)
        docs.append(dict(doc_id=f"inv:{r['investigation_id']}", kind="investigation",
                         investigation_id=r["investigation_id"], title=r["investigation_id"], text=text,
                         source_ref=r["primary_source_ref"] or (f"PSI record {r['psi_id']}" if r["psi_id"] else ""),
                         source_url=r["psi_url"] or r["primary_source_url"], verification=r["verification"]))
    return pd.DataFrame(docs)


def expand(query: str) -> str:
    words = re.findall(r"[a-z0-9]+", query.lower())
    extra = [SYNONYMS[w] for w in words if w in SYNONYMS]
    return " ".join(words + extra)


@lru_cache(maxsize=1)
def _index():
    from sklearn.feature_extraction.text import TfidfVectorizer

    docs = corpus()
    vec = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    return vec, vec.fit_transform(docs["title"] + " " + docs["text"])


def search(query: str, k: int = 8, min_score: float = 0.04) -> pd.DataFrame:
    """Rank catalogue rows and evidence statements against a question. Empty frame when nothing matches."""
    if not query or not query.strip():
        return corpus().iloc[0:0].assign(score=[])
    vec, matrix = _index()
    q = vec.transform([expand(query)])
    scores = (matrix @ q.T).toarray().ravel()
    out = corpus().assign(score=scores)
    out = out[out["score"] >= min_score].sort_values("score", ascending=False).head(k)
    return out.reset_index(drop=True)


ABOVE = re.compile(r"(above|over|greater than|more than|at least|exceed\w*|>=?)\s*(\d+(?:\.\d+)?)\s*(%|percent)", re.I)
BELOW = re.compile(r"(below|under|less than|at most|<=?)\s*(\d+(?:\.\d+)?)\s*(%|percent)", re.I)
CLASS_WORDS = {"solid": "solid", "material": "solid", "fabric": "solid", "plastic": "solid", "droplet": "droplet",
               "liquid": "droplet", "gas": "gas", "smoke": "smoke", "detector": "smoke", "detection": "smoke"}


def parse_filters(query: str) -> dict:
    """Numeric oxygen limits and a fuel class, if the question states them in words."""
    q = query.lower()
    out = {}
    if "oxygen" in q or re.search(r"\bo2\b", q):          # "co2" must not be read as "o2"
        if m := ABOVE.search(q):
            out["o2_at_least"] = float(m.group(2))
        if m := BELOW.search(q):
            out["o2_at_most"] = float(m.group(2))
    classes = {cls for word, cls in CLASS_WORDS.items() if re.search(rf"\b{word}s?\b", q)}
    if len(classes) == 1:          # words of two classes ("materials ... smoke detector") name no single class
        out["evidence_class"] = classes.pop()
    return out


def answer(query: str, k: int = 6) -> dict:
    """Extractive answer: the retrieved, sourced statements. No generated text, so no invented numbers.

    If the question states an oxygen limit ("above 25% oxygen") the evidence is first filtered on its
    recorded ambient-oxygen range, and the filter is reported back so the user can see what was applied.
    The same limit is applied to the investigations listed with the answer, on their tested ranges.
    """
    filters = parse_filters(query)
    hits = search(query, k=k)
    statements = hits[hits["kind"] == "evidence"]
    has_o2 = "o2_at_least" in filters or "o2_at_most" in filters
    if filters:
        vec, matrix = _index()
        scores = (matrix @ vec.transform([expand(query)]).T).toarray().ravel()
        docs = corpus().assign(score=scores)
        docs = docs[docs["kind"] == "evidence"].merge(_evidence_facets(), on="doc_id", how="left")
        if has_o2:
            docs = docs[docs["o2_is_ambient"] & docs["o2_max_pct"].notna()]      # a burner feed is never matched
            if "o2_at_least" in filters:
                docs = docs[docs["o2_max_pct"] >= filters["o2_at_least"]]
            if "o2_at_most" in filters:
                docs = docs[docs["o2_min_pct"] <= filters["o2_at_most"]]
        else:
            docs = docs[docs["score"] >= 0.04]                                    # class only: still a text match
        if "evidence_class" in filters:
            wanted = {filters["evidence_class"]} | ({"partial_g"} if filters["evidence_class"] == "solid" else set())
            docs = docs[docs["evidence_class"].isin(wanted)]
        statements = docs.sort_values("score", ascending=False).head(k)[
            ["doc_id", "kind", "investigation_id", "title", "text", "source_ref", "source_url", "verification", "score"]]
        if has_o2:
            inv = load_investigations()
            lo, hi = pd.to_numeric(inv["o2_min_pct"], errors="coerce"), pd.to_numeric(inv["o2_max_pct"], errors="coerce")
            tested = hi.notna()                                                   # no tested range: cannot match a limit
            if "o2_at_least" in filters:
                tested &= hi >= filters["o2_at_least"]
            if "o2_at_most" in filters:
                tested &= lo <= filters["o2_at_most"]
            in_range = set(inv.loc[tested, "investigation_id"])
            is_statement = hits["kind"] == "evidence"
            hits = hits[(is_statement & hits["doc_id"].isin(docs["doc_id"]))
                        | (~is_statement & hits["investigation_id"].isin(in_range))]
        if "evidence_class" in filters:
            keep = set(statements["investigation_id"]) | set(
                load_investigations().loc[load_investigations()["evidence_class"].isin(wanted), "investigation_id"])
            hits = hits[hits["investigation_id"].isin(keep)]
    investigations = list(dict.fromkeys(list(statements["investigation_id"]) + list(hits["investigation_id"])))
    return {"query": query, "filters": filters, "n_hits": int(len(statements) + (hits["kind"] != "evidence").sum()),
            "statements": statements.to_dict("records"), "investigations": investigations, "hits": hits}


@lru_cache(maxsize=1)
def _evidence_facets() -> pd.DataFrame:
    """Fuel class and recorded ambient-oxygen range of every evidence document, for filtering."""
    e = load_evidence()
    facets = pd.DataFrame({"doc_id": e["id"], "evidence_class": e["evidence_class"], "o2_min_pct": e["o2_min_pct"],
                           "o2_max_pct": e["o2_max_pct"], "o2_is_ambient": e["o2_is_ambient"].astype(bool)})
    f = flex.load_flex()
    computed = pd.DataFrame({"doc_id": [d["doc_id"] for d in flex_documents()], "evidence_class": "droplet",
                             "o2_min_pct": float(f["o2_pct"].min()), "o2_max_pct": float(f["o2_pct"].max()),
                             "o2_is_ambient": True})
    return pd.concat([computed, facets], ignore_index=True)


# =============================================================================== nearest real tests

def nearest_flex(fuel: str, o2_pct: float, pressure_kpa: float, co2_pct: float, he_pct: float, d0_mm: float | None,
                 k: int = 8) -> pd.DataFrame:
    """Nearest FLEX tests to a droplet scenario, by distance over the stated initial conditions.

    A test that does not state its pressure or initial diameter is compared on what it does state.
    That is not a match on the missing quantity, so such a test is ranked after every test that
    states them all, and `not_compared` names what was left out.
    """
    f = flex.load_flex()
    f = f[f["fuel"] == fuel].copy()
    scale = {"o2_pct": 5.0, "pressure_kpa": 50.0, "co2_pct": 15.0, "he_pct": 10.0, "d0_mm": 0.8}
    d2 = ((f["o2_pct"] - o2_pct) / scale["o2_pct"]) ** 2 + ((f["co2_pct"] - co2_pct) / scale["co2_pct"]) ** 2 \
        + ((f["he_pct"] - he_pct) / scale["he_pct"]) ** 2
    d2 = d2 + (((f["pressure_kpa"] - pressure_kpa) / scale["pressure_kpa"]) ** 2).fillna(0.0)
    left_out = pd.Series(np.where(f["pressure_kpa"].isna(), "pressure", ""), index=f.index)
    if d0_mm is not None:
        d2 = d2 + (((f["d0_mm"] - d0_mm) / scale["d0_mm"]) ** 2).fillna(0.0)
        no_d0 = f["d0_mm"].isna()
        left_out = left_out.where(~no_d0, left_out.map(lambda s: f"{s}, initial diameter" if s else "initial diameter"))
    return _stated_first(f.assign(distance=np.sqrt(d2), not_compared=left_out), k)


def _stated_first(frame: pd.DataFrame, k: int) -> pd.DataFrame:
    """The k nearest rows: those that state every compared quantity first, then by distance."""
    order = frame.assign(_partial=frame["not_compared"] != "").sort_values(["_partial", "distance"], kind="stable")
    return order.drop(columns="_partial").head(k)


def nearest_solid(material_class: str, o2_pct: float, pressure_kpa: float, flow_cm_s: float, k: int = 8) -> pd.DataFrame:
    """Nearest solid-fuel test points. Same material first; other materials only if there are too few.

    A point with no flow speed (the source gives a fan setting, not cm/s) is compared on oxygen and
    pressure only, is ranked after every point that states its flow, and says so in `not_compared`.
    """
    s = load_solid_points()
    s = s[s["outcome"] != "ambiguous"].copy()
    same = s[s["material_class"] == material_class]
    pool = same if len(same) >= 3 else s
    pool = pool.copy()
    flow = pool["flow_cm_s"]
    d2 = ((pool["o2_at_outcome_pct"] - o2_pct) / 2.0) ** 2 + ((pool["pressure_kPa"] - pressure_kpa) / 30.0) ** 2
    d2 = d2 + (((np.log1p(flow) - np.log1p(flow_cm_s)) / 1.0) ** 2).fillna(0.0)
    out = pool.assign(distance=np.sqrt(d2), same_material=pool["material_class"] == material_class,
                      not_compared=np.where(flow.isna(), "flow", ""))
    return _stated_first(out, k)


def solid_envelope(material_class: str | None = None) -> dict:
    """Tested ranges of the solid-fuel points with a stated outcome (optionally for one material)."""
    s = load_solid_points()
    s = s[s["outcome"] != "ambiguous"]
    if material_class:
        s = s[s["material_class"] == material_class]
    if s.empty:
        return {"n": 0}
    return {"n": int(len(s)), "o2": (float(s["o2_at_outcome_pct"].min()), float(s["o2_at_outcome_pct"].max())),
            "pressure": (float(s["pressure_kPa"].min()), float(s["pressure_kPa"].max())),
            "flow": (float(s["flow_cm_s"].min()), float(s["flow_cm_s"].max())),
            "sustained_o2_max": float(s.loc[s["outcome"] == "sustained", "o2_at_outcome_pct"].max())
            if (s["outcome"] == "sustained").any() else None}
