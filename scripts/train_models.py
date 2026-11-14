"""Train the three logistic models and write their results as JSON.

Outputs:
  data/models/<name>.json   coefficients, preprocessing, every metric, out-of-fold predictions
  data/cv_splits.json       the exact outer-fold membership of every row (seed 42)

Run from the repo root:  python scripts/train_models.py
Needs scikit-learn and scipy; the dashboard itself only reads the JSON.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flamefall import model  # noqa: E402


def sensitivity_without_disruption() -> dict:
    """Droplet extinction model refitted on Extinction vs Completion only (Disruption rows left out)."""
    df = model.frame_for("droplet_extinction")
    df = df[df["outcome"] != "Disruption"].reset_index(drop=True)
    spec = model.SPECS["droplet_extinction"]
    cv = model.nested_cv(df, spec)
    y = df["y"].to_numpy()
    lo, hi = model.cluster_bootstrap_auc(y, cv["oof"], cv["split_groups"])
    thr = model.youden_threshold(y, cv["oof"])
    return {"n_rows": int(len(df)), "n_positive": int(y.sum()), "roc_auc": model.auc(y, cv["oof"]),
            "roc_auc_ci": [lo, hi], "pr_auc": model.average_precision(y, cv["oof"]),
            "confusion_at_youden": model.confusion(y, cv["oof"], thr),
            "note": "Disruption rows removed; y = 1 Extinction, y = 0 Completion."}


def strict(obj):
    """Replace NaN and infinity with None, recursively, so the output is valid RFC 8259 JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: strict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [strict(v) for v in obj]
    return obj


def write_json(path: Path, obj) -> None:
    # allow_nan=False makes the writer fail loudly if a non-finite value ever slips through
    path.write_text(json.dumps(strict(obj), indent=1, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    model.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    splits = {}
    for name in model.SPECS:
        out = model.train(name)
        r = out["result"]
        if name == "droplet_extinction":
            r["sensitivity_without_disruption"] = sensitivity_without_disruption()
        write_json(model.MODEL_DIR / f"{name}.json", r)
        splits[name] = out["splits"]
        m = r["metrics"]
        ci = m["roc_auc_ci"]
        print(f"{name}: n={r['n_rows']} positives={r['n_positive']} groups={r['n_groups']} "
              f"C={r['C_final']} balanced={r['class_weight_balanced']}")
        print(f"   grouped-CV AUC {m['roc_auc']:.3f} [{ci[0]}, {ci[1]}]  PR-AUC {m['pr_auc']:.3f}  "
              f"Brier {m['brier']:.3f}  LOMO AUC {r['leave_one_material_out']['pooled_auc']}  "
              f"headline {r['headline_auc']} ({r['headline_is']})")
        print("   Youden", m["confusion_at_youden"])
    write_json(model.DATA / "cv_splits.json", splits)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
