"""Build-time export: everything the React app reads, written as JSON.

    python scripts/export_web.py            # rewrite the files
    python scripts/export_web.py --check    # exit 1 if any committed file differs from a fresh export

Python owns the data. The front end imports these files and never opens a CSV, never re-fits a
model and never re-derives a source value. Where the front end must compute something at once
(a filter, a slider), it repeats a calculation that lives here in Python, and `golden.json` holds
this layer's answers so the front end's tests can compare.

Outputs
  web/src/data/*.json                    bundled with the app
  web/public/psi/*.json                  PSI experimental tables, fetched only when a reader opens one
  web/src/lib/__fixtures__/golden.json   reference answers for the front end's tests
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flamefall import aggregates, flex, model, psi, ranking  # noqa: E402
from flamefall import catalogue as cat  # noqa: E402

WEB = ROOT / "web"
DATA_OUT = WEB / "src" / "data"
PSI_OUT = WEB / "public" / "psi"
GOLDEN_OUT = WEB / "src" / "lib" / "__fixtures__" / "golden.json"

FLEX_COLUMNS = [
    "test_no", "test_id", "cir_id", "date_iso", "fuel", "pressure_mmhg", "pressure_atm", "pressure_kpa",
    "o2", "n2", "co2", "he", "o2_pct", "co2_pct", "he_pct", "o2_partial_kpa", "d0_mm", "extinction_diameter_mm",
    "burning_rate_mm2_s", "burn_time_s", "outcome", "extinguished", "atmosphere", "cool_flame_label",
    "cool_flame_quote", "caption_figure", "support", "notes", "source", "caption_atmosphere",
    "caption_atmosphere_differs",
]
SOLID_COLUMNS = [
    "point_id", "investigation_id", "test_no", "material_class", "material_verbatim", "geometry", "flow_direction",
    "flow_cm_s", "o2_at_outcome_pct", "pressure_kPa", "outcome", "outcome_quote", "source_ref", "source_url",
    "verification", "usable_for_model",
]
MODEL_DROP = ("oof",)      # per-row out-of-fold predictions stay in data/models; the app shows the curves built from them


def clean(value):
    """Plain JSON: NaN and pd.NA become null, numpy scalars become Python numbers."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        v = float(value)
        return None if math.isnan(v) or math.isinf(v) else round(v, 10)
    if value is pd.NA or value is None:
        return None
    return value


def records(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    return [clean({c: row[c] for c in columns}) for _, row in df.iterrows()]


# =============================================================================== data files

def flex_export() -> dict:
    f = flex.load_flex().copy()
    rows = records(f, FLEX_COLUMNS)
    for row, (_, src) in zip(rows, f.iterrows()):
        row["table_atmosphere"] = flex.table_atmosphere(src)
        row["end_diameter_label"] = aggregates.end_diameter_label(src["outcome"])
    return {
        "meta": {"report": flex.REPORT, "report_title": flex.REPORT_TITLE, "record_url": flex.RECORD_URL,
                 "pdf_url": flex.PDF_URL, "psi_id": flex.PSI_ID,
                 "table_source": f"{flex.REPORT}, Table IX (PDF pp. 26–34)",
                 "end_marker_extinction": aggregates.END_MARKER_EXTINCTION,
                 "end_marker_other": aggregates.END_MARKER_OTHER},
        "summary": clean(flex.summary()),
        "outcomes": flex.OUTCOMES,
        "families": sorted(f["atmosphere"].unique()),
        "caption_conflicts": int(f["caption_atmosphere_differs"].sum()),
        "printed_end_diameter": clean(f[f["extinction_diameter_mm"].notna()].groupby("outcome").size().to_dict()),
        "rows": rows,
    }


def catalogue_export() -> dict:
    inv = cat.load_investigations()
    cols = [c for c in inv.columns]
    rows = []
    for _, r in inv.iterrows():
        row = clean({c: r[c] for c in cols})
        row["psi_tables"] = [t for t in str(r["psi_tables"]).split("; ") if t]
        rows.append(row)
    return {
        "counts": clean(cat.counts()), "search_url": psi.SEARCH_URL, "env_rules": cat.ENV_RULES,
        "fuel_type_label": cat.FUEL_TYPE_LABEL, "evidence_class_label": cat.EVIDENCE_CLASS_LABEL,
        "relevance_weights": cat.RELEVANCE_WEIGHTS, "investigations": rows,
    }


def evidence_export() -> list[dict]:
    e = cat.load_evidence()
    return records(e, list(e.columns))


def solid_export() -> dict:
    s = cat.load_solid_points()
    materials = sorted(s["material_class"].unique())
    return {
        "points": records(s, SOLID_COLUMNS),
        "envelope_all": clean(cat.solid_envelope()),
        "envelopes": {m: clean(cat.solid_envelope(m)) for m in materials},
        "n_decided": int((s["outcome"] != "ambiguous").sum()),
        "n_total": int(len(s)),
    }


def search_export() -> dict:
    """The TF-IDF index as plain numbers, so the browser scores a question exactly as Python does."""
    vec, matrix = cat._index()
    docs = cat.corpus().merge(cat._evidence_facets(), on="doc_id", how="left")
    vocab = sorted(vec.vocabulary_, key=vec.vocabulary_.get)
    m = matrix.tocsr()
    vectors = []
    for i in range(m.shape[0]):
        row = m.getrow(i)
        vectors.append([[int(j), round(float(v), 6)] for j, v in zip(row.indices, row.data)])
    doc_cols = ["doc_id", "kind", "investigation_id", "title", "text", "source_ref", "source_url", "verification",
                "evidence_class", "o2_min_pct", "o2_max_pct", "o2_is_ambient"]
    inv = cat.load_investigations()
    return {
        "docs": records(docs, doc_cols),
        "vocab": vocab, "idf": [round(float(v), 6) for v in vec.idf_],
        "vectors": vectors, "stop_words": sorted(vec.get_stop_words()), "synonyms": cat.SYNONYMS,
        "class_words": cat.CLASS_WORDS, "min_score": 0.04,
        "investigation_class": dict(zip(inv["investigation_id"], inv["evidence_class"])),
    }


def ranking_export() -> dict:
    return {
        "weights": ranking.WEIGHTS, "term_label": ranking.TERM_LABEL, "p_o2_ref_kpa": ranking.P_O2_REF_KPA,
        "p_o2_min_kpa": {k: {"value": v[0], "why": v[1]} for k, v in ranking.P_O2_MIN_KPA.items()},
        "p_o2_floor_kpa": ranking.P_O2_FLOOR_KPA, "flow_band": list(ranking.FLOW_BAND),
        "flow_zero_at": ranking.FLOW_ZERO_AT, "quiescent_score": ranking.QUIESCENT_SCORE,
        "hrr_scale_w": {k: {"watts": v[0], "why": v[1]} for k, v in ranking.HRR_SCALE_W.items()},
        "detection": {k: {"score": v[0], "why": v[1]} for k, v in ranking.DETECTION.items()},
        "detection_default": {"score": ranking.DETECTION_DEFAULT[0], "why": ranking.DETECTION_DEFAULT[1]},
        "large_volume_m3": ranking.LARGE_VOLUME_M3,
        "gravity_score": [{"g": g, "score": s, "name": ranking.GRAVITY_NAME[g]} for g, s in ranking.GRAVITY_SCORE.items()],
        "presets": [asdict(p) for p in ranking.PRESETS],
    }


def model_export(name: str) -> dict:
    card = json.loads((model.MODEL_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return {k: v for k, v in card.items() if k not in MODEL_DROP}


def panels_export() -> dict:
    return json.loads((ROOT / "data" / "panels.json").read_text(encoding="utf-8"))


def psi_tables() -> dict[str, dict]:
    out = {}
    for name in psi.table_names():
        t = psi.read_table(name)
        out[name.replace(".csv", ".json").replace(" ", "_")] = {
            "name": name, "columns": [psi.fix_text(c) for c in t.columns],
            "rows": [[psi.fix_text(v) for v in row] for row in t.itertuples(index=False, name=None)]}
    return out


# =============================================================================== reference answers

def golden() -> dict:
    f = flex.load_flex()
    g: dict = {}
    g["wilson"] = [{"k": k, "n": n, "lo": lo, "hi": hi}
                   for k, n in [(0, 5), (5, 5), (3, 30), (126, 157), (60, 119), (1, 1), (17, 40)]
                   for lo, hi in [flex.wilson_interval(k, n)]]
    g["share_by_level"] = {}
    for label, frame in [("all", f), ("methanol", f[f["fuel"] == "Methanol"]),
                         ("air_1atm", f[(f["atmosphere"].str.startswith("Air")) & (f["pressure_atm"].between(0.9, 1.1))])]:
        for xcol in ("o2_pct", "co2_pct", "he_pct"):
            g["share_by_level"][f"{label}:{xcol}"] = aggregates.share_by_level(frame, xcol).to_dict("records")
    g["logistic_trend"] = []
    for fuel in ("Methanol", "Heptane"):
        for xcol in ("o2_pct", "co2_pct"):
            sub = f[f["fuel"] == fuel]
            grid = np.linspace(sub[xcol].min(), sub[xcol].max(), 7)
            trend = aggregates.logistic_trend(sub[xcol].to_numpy(float), sub["extinguished"].to_numpy(float), grid)
            g["logistic_trend"].append({"fuel": fuel, "xcol": xcol, "grid": grid.tolist(), "p": trend.tolist()})
    g["nearest_tests"] = [
        {"fuels": fuels, "o2_pct": o2, "pressure_atm": p,
         "ids": aggregates.nearest_tests(f[f["fuel"].isin(fuels)], o2, p)["test_id"].tolist()}
        for fuels, o2, p in [(["Methanol", "Heptane"], 23.0, 1.875), (["Heptane"], 40.0, 0.5), (["Methanol"], 21.0, 1.0)]]
    g["d2_line"] = [{"test_id": t, "line": aggregates.d2_line(f.set_index("test_id").loc[t])}
                    for t in ("FLEX-001", "FLEX-002", "FLEX-051", "FLEX-212")]

    # ---- catalogue: relevance, retrieval
    g["rank_investigations"] = []
    for p in ranking.PRESETS:
        r = cat.rank_investigations(p.o2_pct, p.pressure_kpa, p.flow_cm_s, "solid", p.gravity_g)
        g["rank_investigations"].append({
            "scenario": asdict(p),
            "top": [{"id": row["investigation_id"], "relevance": row["relevance"],
                     "terms": {k: row[f"rel_{k}"] for k in cat.RELEVANCE_WEIGHTS},
                     "why": {k: row[f"why_{k}"] for k in cat.RELEVANCE_WEIGHTS}} for _, row in r.head(12).iterrows()]})
    questions = [
        "Which experiments tested solid materials above 25% oxygen?", "Did the smoke detector miss anything?",
        "What do we know about fire in lunar gravity?", "Does turning off ventilation put a flame out?",
        "which droplets burned in CO2 above 30%?", "cool flames after extinction", "oxygen below 15 percent for solids",
        "zxqv nonsense words", "", "helium dilution", "Kapton wire smoke particle size", "tests with o2 above 30%",
    ]
    g["answer"] = []
    for q in questions:
        a = cat.answer(q)
        g["answer"].append({
            "query": q, "expanded": cat.expand(q), "filters": a["filters"], "n_hits": a["n_hits"],
            "statements": [{"doc_id": s["doc_id"], "score": s["score"]} for s in a["statements"]],
            "hits": [{"doc_id": d, "score": s} for d, s in zip(a["hits"]["doc_id"], a["hits"]["score"])],
            "investigations": a["investigations"]})

    # ---- nearest real tests
    g["nearest_flex"] = []
    for fuel, o2, p, co2, he, d0 in [("Heptane", 21.0, 101.3, 0.0, 0.0, 3.0), ("Methanol", 30.0, 70.3, 0.0, 0.0, None),
                                     ("Heptane", 18.0, 101.3, 20.0, 0.0, 2.5), ("Methanol", 45.0, 56.5, 0.0, 30.0, 4.0)]:
        n = cat.nearest_flex(fuel, o2, p, co2, he, d0)
        g["nearest_flex"].append({"args": [fuel, o2, p, co2, he, d0], "ids": n["test_id"].tolist(),
                                  "distance": n["distance"].tolist()})
    g["nearest_solid"] = []
    for mat, o2, p, flow in [("PMMA", 21.0, 101.3, 10.0), ("SIBAL-cotton", 34.0, 56.5, 5.0), ("Nomex", 30.0, 70.3, 20.0),
                             ("silicone", 21.0, 101.3, 0.0), ("PMMA", 16.0, 101.3, 0.0)]:
        n = cat.nearest_solid(mat, o2, p, flow)
        g["nearest_solid"].append({"args": [mat, o2, p, flow], "ids": n["point_id"].tolist(),
                                   "distance": n["distance"].tolist(), "same_material": n["same_material"].tolist()})

    # ---- triage score
    S = ranking.Scenario
    scenarios = [S("base", "PMMA", 21.0, 101.0, 20.0, 0.0), S("lunar", "PMMA", 21.0, 101.0, 20.0, 0.16),
                 S("limit", "PMMA", 13.6, 101.0, 20.0, 0.0),
                 S("droplet", "Heptane droplet", 21.0, 101.3, 0.0, 0.0, is_droplet=True, droplet_d0_mm=3.0, n_alkane=True),
                 S("fast", "Nomex", 30.0, 70.3, 42.0, 0.38, "large sample (vehicle scale)", 20.0),
                 S("slow", "Kapton", 21.0, 101.3, 0.5, 1.0, "small sample (glovebox scale)", 100.0),
                 *ranking.PRESETS]
    g["hazard"] = [{"scenario": asdict(s), "terms": ranking.terms(s), "hazard": ranking.hazard(s)} for s in scenarios]
    g["worked_example"] = {"base": round(ranking.hazard(scenarios[0]), 3), "lunar": round(ranking.hazard(scenarios[1]), 3),
                           "limit": round(ranking.hazard(scenarios[2]), 3)}
    odd = {"M_O2": 0.10, "M_flow": 0.10, "H": 0.40, "D": 0.20, "G": 0.10, "C": 0.10}
    g["rank"] = [{"weights": w, "order": [[n, s] for n, s in ranking.rank(ranking.PRESETS, w)],
                  "sensitivity": ranking.sensitivity(ranking.PRESETS, w)} for w in (ranking.WEIGHTS, odd)]

    # ---- model estimates
    g["predict"] = []
    cases = {
        "droplet_extinction": [
            dict(o2_pct=21.0, pressure_kpa=101.3, co2_pct=0.0, he_pct=0.0, d0_mm=3.0, fuel_heptane=1.0),
            dict(o2_pct=18.0, pressure_kpa=101.3, co2_pct=20.0, he_pct=0.0, d0_mm=2.5, fuel_heptane=0.0),
            dict(o2_pct=45.0, pressure_kpa=56.5, co2_pct=0.0, he_pct=0.0, d0_mm=3.0, fuel_heptane=1.0),
            dict(o2_pct=30.0, pressure_kpa=202.6, co2_pct=0.0, he_pct=30.0, d0_mm=None, fuel_heptane=0.0),
        ],
        "droplet_cool_flame": [
            dict(o2_pct=21.0, pressure_kpa=101.3, co2_pct=0.0, he_pct=0.0, d0_mm=3.0),
            dict(o2_pct=45.0, pressure_kpa=56.5, co2_pct=10.0, he_pct=0.0, d0_mm=6.0),
        ],
    }
    for name, xs in cases.items():
        fitted = model.Fitted(name)
        for x in xs:
            x = {**x, "o2_partial_kpa": x["o2_pct"] / 100 * x["pressure_kpa"]}
            g["predict"].append({"model": name, "x": x, "out": fitted.predict(x)})
    return clean(g)


# =============================================================================== write / check

def build() -> dict[Path, str]:
    files: dict[Path, object] = {
        DATA_OUT / "flex.json": flex_export(),
        DATA_OUT / "catalogue.json": catalogue_export(),
        DATA_OUT / "evidence.json": evidence_export(),
        DATA_OUT / "solid.json": solid_export(),
        DATA_OUT / "search.json": search_export(),
        DATA_OUT / "ranking.json": ranking_export(),
        DATA_OUT / "panels.json": panels_export(),
        GOLDEN_OUT: golden(),
    }
    for name in model.SPECS:
        files[DATA_OUT / f"model_{name}.json"] = model_export(name)
    for filename, table in psi_tables().items():
        files[PSI_OUT / filename] = table
    return {path: json.dumps(clean(obj), ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"
            for path, obj in files.items()}


def main(argv: list[str]) -> int:
    built = build()
    if "--check" in argv:
        stale = [str(p.relative_to(ROOT)) for p, text in built.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        extra = [str(p.relative_to(ROOT)) for d in (DATA_OUT, PSI_OUT) if d.exists()
                 for p in d.glob("*.json") if p not in built]
        for name in stale:
            print("stale:", name)
        for name in extra:
            print("not produced by the export:", name)
        return 1 if stale or extra else 0
    for path, text in built.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    size = sum(len(t.encode("utf-8")) for t in built.values())
    print(f"wrote {len(built)} files, {size / 1024:.0f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
