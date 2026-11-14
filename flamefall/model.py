"""Small, honestly validated logistic models. Droplet rows and solid rows never share a model.

Three models, one protocol:
  droplet_extinction  P(visible flame goes out)      FLEX Table IX, 275 rows
  droplet_cool_flame  P(cool-flame evidence)         FLEX n-heptane extinctions with a caption statement
  solid_sustained     P(flame is sustained)          BASS-II, Saffire, SoFIE-GEL test points

Protocol (research specification section 7.3):
  * features are initial conditions only: nothing measured after ignition is a feature;
  * L2 logistic regression, C chosen from {0.01, 0.1, 1, 10} by inner grouped CV;
  * outer GroupKFold(5), inner GroupKFold(3): a group is never split between train and test;
  * a separate leave-one-material-out stress test; the headline is the WORSE of the two AUCs;
  * every preprocessing statistic (median, mean, SD) is learned on the training fold only.

Training lives here and is run by scripts/train_models.py, which writes plain JSON. The
dashboard reads that JSON and predicts with numpy alone (see `Fitted`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import flex, schema

DATA = Path(__file__).resolve().parents[1] / "data"
MODEL_DIR = DATA / "models"
SEED = 42
C_GRID = [0.01, 0.1, 1.0, 10.0]
N_BOOT = 1000
MIN_GROUP_ROWS = 5
RARE_CLASS_ROWS = 5


# =============================================================================== specifications

@dataclass
class Spec:
    name: str
    title: str
    target_label: str               # what y = 1 means
    burning_is_y1: bool             # True: y = 1 is "still burning"; False: y = 0 is "still burning"
    continuous: list[str]           # standardised; missing values median-imputed in-fold
    log_features: list[str]         # subset of `continuous` that is log-transformed first
    log1p_features: list[str]
    binary: list[str]
    categorical: dict[str, list[str]] = field(default_factory=dict)   # column -> fixed category order
    interactions: list[tuple[str, str]] = field(default_factory=list)
    group_col: str = "group"
    report_group_col: str = "group"
    material_col: str = "material"
    merge_small_groups: bool = False                                  # only meaningful when groups are investigations
    squares: list[str] = field(default_factory=list)                 # standardised features that also enter squared
    dropped: dict[str, str] = field(default_factory=dict)             # feature -> why it is not used
    added: dict[str, str] = field(default_factory=dict)               # feature -> written justification
    notes: list[str] = field(default_factory=list)


NOMINAL_ATM = np.array([0.7, 1.0, 2.0, 3.0])


def atmosphere_group(row: pd.Series) -> str:
    """One group per tested atmosphere: gas composition plus nominal pressure."""
    nominal = NOMINAL_ATM[np.abs(NOMINAL_ATM - row["pressure_atm"]).argmin()]
    return f"O2 {row['o2']:.2f} / CO2 {row['co2']:.2f} / He {row['he']:.2f} @ {nominal:g} atm"


def droplet_frame() -> pd.DataFrame:
    f = flex.load_flex().copy()
    f["verification"] = "verified_live"
    f = schema.model_rows_only(f)
    f = f[f["pressure_kpa"].notna()].copy()             # rule (i): drop rows missing O2 / pressure / pO2
    f["group"] = f.apply(atmosphere_group, axis=1)
    f["material"] = f["fuel"]
    f["fuel_heptane"] = (f["fuel"] == "Heptane").astype(float)
    f["row_id"] = f["test_id"]
    return f


DROPLET_DROPPED = {
    "flow_cm_s": "every FLEX droplet burned in still gas: the feature is constant",
    "is_quiescent": "constant (always 1)",
    "flow_direction": "not applicable to a droplet in still gas",
    "gravity_g": "the data span one gravity level (microgravity); the specification says to drop it",
    "o2_x_flow": "needs flow, which is constant",
    "o2_partial_x_gravity": "needs gravity, which is constant",
}
DROPLET_ADDED = {
    "co2_pct": "CO2 dilution is the suppression variable FLEX was flown to test; leaving it out would hide the "
               "experiment's main factor",
    "he_pct": "helium dilution is FLEX's second suppression variable (51 tests)",
}

SPECS = {
    "droplet_extinction": Spec(
        name="droplet_extinction", title="Droplet model: did the visible flame go out?",
        target_label="test ended in Extinction (visible flame went out before the fuel was gone)",
        burning_is_y1=False,
        continuous=["o2_pct", "pressure_kpa", "o2_partial_kpa", "co2_pct", "he_pct", "d0_mm"],
        log_features=["pressure_kpa", "d0_mm"], log1p_features=[], binary=["fuel_heptane"],
        dropped=DROPLET_DROPPED, added=DROPLET_ADDED,
        notes=["y = 0 groups Disruption and Completion. A disrupted droplet is not an extinguished flame; "
               "see the sensitivity run that leaves Disruption rows out.",
               "Grouping is by tested atmosphere because FLEX is a single investigation: a model is always "
               "scored on atmospheres it never saw."]),
    "droplet_cool_flame": Spec(
        name="droplet_cool_flame", title="Droplet model: cool-flame evidence after visible extinction",
        target_label="report caption states evidence of cool-flame burning after the visible flame went out",
        burning_is_y1=True,
        continuous=["o2_pct", "pressure_kpa", "o2_partial_kpa", "co2_pct", "he_pct", "d0_mm"],
        log_features=["pressure_kpa", "d0_mm"], log1p_features=[], binary=[],
        dropped={**DROPLET_DROPPED, "material_class": "every labelled row is n-heptane: the feature is constant"},
        added=DROPLET_ADDED,
        notes=["Labels come from the FLEX report's figure captions (authors' inference from vaporisation and "
               "vapour cloud), and exist for n-heptane only.",
               "Rows: n-heptane tests that ended in Extinction and whose caption says 'evidence' or "
               "'no evidence'. Unclear and silent captions are left out, not counted as negatives.",
               "Very small and unbalanced. Exploratory only."]),
    "solid_sustained": Spec(
        name="solid_sustained", title="Solid-fuel model: is the flame sustained?",
        target_label="source states the flame burned or spread at this condition",
        burning_is_y1=True,
        continuous=["o2_pct", "pressure_kpa", "o2_partial_kpa", "flow_cm_s", "thickness_mm"],
        log_features=["pressure_kpa", "thickness_mm"], log1p_features=["flow_cm_s"], binary=["is_quiescent"],
        categorical={"flow_direction": ["opposed", "concurrent", "stagnation"],
                     "material_class": ["PMMA", "SIBAL-cotton", "Nomex", "silicone", "rare"]},
        interactions=[("o2_pct", "flow_cm_s")], merge_small_groups=True,
        dropped={"gravity_g": "every verified solid test point is microgravity: one gravity level, so dropped",
                 "o2_partial_x_gravity": "needs gravity, which is constant"},
        notes=["Groups are investigations; BASS-II is split into its six investigator test series, which used "
               "different sample geometries. Groups with fewer than 5 rows are merged for splitting only.",
               "BASS-II pressure is taken as 1 atm (stated for the fabric tests; same glovebox for the rest).",
               "Most extinction points in the BASS-II appendix are given as fan settings with no cm/s value "
               "and cannot be used, so sustained points are over-represented."]),
}


def solid_frame() -> pd.DataFrame:
    s = pd.read_csv(DATA / "solid_test_points.csv")
    s = schema.model_rows_only(s)
    s = s[s["usable_for_model"].astype(str).str.lower() == "true"].copy()
    s["y"] = s["sustained"].astype(int)
    s["o2_initial_pct"] = s["o2_pct"]
    s["o2_pct"] = s["o2_at_outcome_pct"]              # extinctions are placed at the oxygen they happened at
    s["o2_partial_kpa"] = s["o2_pct"] / 100 * s["pressure_kPa"]
    s["pressure_kpa"] = s["pressure_kPa"]
    s["is_quiescent"] = (s["flow_cm_s"] == 0).astype(float)
    counts = s["material_class"].value_counts()
    s["material_class"] = s["material_class"].where(s["material_class"].map(counts) >= RARE_CLASS_ROWS, "rare")
    s["material"] = s["material_class"]
    s["group"] = s["group_id"]
    s["row_id"] = s["point_id"]
    return s


def frame_for(name: str) -> pd.DataFrame:
    if name == "droplet_extinction":
        f = droplet_frame()
        f["y"] = f["extinguished"].astype(int)
        return f
    if name == "droplet_cool_flame":
        f = droplet_frame()
        f = f[(f["fuel"] == "Heptane") & (f["outcome"] == "Extinction")
              & f["cool_flame_label"].isin(["indicated", "not_indicated"])].copy()
        f["y"] = (f["cool_flame_label"] == "indicated").astype(int)
        return f
    if name == "solid_sustained":
        return solid_frame()
    raise KeyError(name)


# =============================================================================== preprocessing

def fit_prep(df: pd.DataFrame, spec: Spec) -> dict:
    """Learn medians, means and SDs on a training frame only."""
    prep = {"median": {}, "mean": {}, "sd": {}}
    for col in spec.continuous:
        x = df[col].astype(float)
        x = np.log(x) if col in spec.log_features else (np.log1p(x) if col in spec.log1p_features else x)
        med = float(np.nanmedian(x)) if np.isfinite(x).any() else 0.0
        x = x.fillna(med)
        prep["median"][col], prep["mean"][col] = med, float(x.mean())
        sd = float(x.std(ddof=0))
        prep["sd"][col] = sd if sd > 1e-9 else 1.0
    return prep


def feature_names(spec: Spec) -> list[str]:
    names = list(spec.continuous) + list(spec.binary)
    for col, cats in spec.categorical.items():
        names += [f"{col}={c}" for c in cats]
    names += [f"{a} x {b}" for a, b in spec.interactions]
    names += [f"{c} squared" for c in spec.squares]
    return names


def transform(df: pd.DataFrame, spec: Spec, prep: dict) -> np.ndarray:
    cols, z = [], {}
    for col in spec.continuous:
        x = df[col].astype(float)
        x = np.log(x) if col in spec.log_features else (np.log1p(x) if col in spec.log1p_features else x)
        x = x.fillna(prep["median"][col])
        z[col] = ((x - prep["mean"][col]) / prep["sd"][col]).to_numpy()
        cols.append(z[col])
    for col in spec.binary:
        cols.append(df[col].astype(float).to_numpy())
    for col, cats in spec.categorical.items():
        values = df[col].where(df[col].isin(cats), "rare" if "rare" in cats else None)
        for c in cats:
            cols.append((values == c).astype(float).to_numpy())
    for a, b in spec.interactions:
        cols.append(z[a] * z[b])
    for c in spec.squares:
        cols.append(z[c] ** 2)
    return np.column_stack(cols)


# =============================================================================== fitting and CV

def _fit(X, y, C, balanced):
    from sklearn.linear_model import LogisticRegression

    m = LogisticRegression(C=C, solver="lbfgs", max_iter=5000, class_weight="balanced" if balanced else None)
    m.fit(X, y)
    return m


def _splits(groups: np.ndarray, k: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Seeded grouped folds: groups are shuffled once with SEED, then dealt to folds by size."""
    rng = np.random.default_rng(SEED)
    uniq, counts = np.unique(groups, return_counts=True)
    order = rng.permutation(len(uniq))
    uniq, counts = uniq[order], counts[order]
    by_size = np.argsort(-counts, kind="stable")
    fold_of, load = {}, np.zeros(k)
    for i in by_size:
        j = int(load.argmin())
        fold_of[uniq[i]] = j
        load[j] += counts[i]
    fold = np.array([fold_of[g] for g in groups])
    return [(np.where(fold != j)[0], np.where(fold == j)[0]) for j in range(k) if (fold == j).any()]


def merge_small_groups(groups: pd.Series, merge: bool = True) -> np.ndarray:
    if not merge:
        return groups.to_numpy()
    counts = groups.value_counts()
    return groups.where(groups.map(counts) >= MIN_GROUP_ROWS, "other (groups under 5 rows)").to_numpy()


def choose_C(df: pd.DataFrame, spec: Spec, split_groups: np.ndarray, balanced: bool) -> float:
    """Inner grouped CV: pooled out-of-fold log-loss, which stays defined when a fold has one class."""
    y = df["y"].to_numpy()
    k = min(3, len(np.unique(split_groups)))
    if k < 2 or len(np.unique(y)) < 2:
        return 1.0
    best, best_loss = 1.0, np.inf
    for C in C_GRID:
        p = np.full(len(df), np.nan)
        for tr, te in _splits(split_groups, k):
            if len(np.unique(y[tr])) < 2:
                p[te] = y[tr].mean()
                continue
            prep = fit_prep(df.iloc[tr], spec)
            p[te] = _fit(transform(df.iloc[tr], spec, prep), y[tr], C, balanced).predict_proba(
                transform(df.iloc[te], spec, prep))[:, 1]
        p = np.clip(p, 1e-6, 1 - 1e-6)
        loss = float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
        if loss < best_loss - 1e-12:
            best, best_loss = C, loss
    return best


def is_balanced_needed(y: np.ndarray) -> bool:
    share = y.mean()
    return bool(min(share, 1 - share) < 0.30)


def nested_cv(df: pd.DataFrame, spec: Spec) -> dict:
    y = df["y"].to_numpy()
    split_groups = merge_small_groups(df[spec.group_col], spec.merge_small_groups)
    balanced = is_balanced_needed(y)
    k = min(5, len(np.unique(split_groups)))
    oof, fold_id, chosen, folds = np.full(len(df), np.nan), np.full(len(df), -1), [], []
    for j, (tr, te) in enumerate(_splits(split_groups, k)):
        if len(np.unique(y[tr])) < 2:
            oof[te], C = y[tr].mean(), None
        else:
            C = choose_C(df.iloc[tr], spec, split_groups[tr], balanced)
            prep = fit_prep(df.iloc[tr], spec)
            oof[te] = _fit(transform(df.iloc[tr], spec, prep), y[tr], C, balanced).predict_proba(
                transform(df.iloc[te], spec, prep))[:, 1]
        fold_id[te] = j
        chosen.append(C)
        folds.append({"fold": j, "C": C, "test_groups": sorted(set(split_groups[te])),
                      "train_rows": df["row_id"].iloc[tr].tolist(), "test_rows": df["row_id"].iloc[te].tolist()})
    return {"oof": oof, "fold": fold_id, "C_per_fold": chosen, "folds": folds, "balanced": balanced,
            "split_groups": split_groups, "k": k}


def leave_one_material_out(df: pd.DataFrame, spec: Spec) -> dict:
    """Train on all other materials, test on the one left out. Reported separately, never averaged in."""
    y = df["y"].to_numpy()
    materials = df[spec.material_col].to_numpy()
    balanced = is_balanced_needed(y)
    oof, rows = np.full(len(df), np.nan), []
    for m in sorted(set(materials)):
        te, tr = np.where(materials == m)[0], np.where(materials != m)[0]
        if len(tr) == 0 or len(np.unique(y[tr])) < 2:
            rows.append({"material": m, "n": int(len(te)), "auc": None, "note": "cannot train without this material"})
            continue
        # the left-out material's own indicator column carries no signal in training; that is the point
        C = choose_C(df.iloc[tr], spec, merge_small_groups(df[spec.group_col].iloc[tr], spec.merge_small_groups),
                     balanced)
        prep = fit_prep(df.iloc[tr], spec)
        oof[te] = _fit(transform(df.iloc[tr], spec, prep), y[tr], C, balanced).predict_proba(
            transform(df.iloc[te], spec, prep))[:, 1]
        rows.append({"material": m, "n": int(len(te)), "positives": int(y[te].sum()),
                     "auc": auc(y[te], oof[te]), "brier": float(np.mean((oof[te] - y[te]) ** 2)), "C": C})
    ok = ~np.isnan(oof)
    return {"per_material": rows, "pooled_auc": auc(y[ok], oof[ok]) if ok.any() else None, "n_scored": int(ok.sum())}


# =============================================================================== metrics

def auc(y: np.ndarray, p: np.ndarray) -> float | None:
    """ROC-AUC by the rank-sum formula; None when one class is absent."""
    y = np.asarray(y)
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    from scipy.stats import rankdata

    r = rankdata(np.concatenate([pos, neg]))
    return float((r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def average_precision(y: np.ndarray, p: np.ndarray) -> float | None:
    if y.sum() == 0:
        return None
    order = np.argsort(-p, kind="stable")
    hits = y[order]
    precision = np.cumsum(hits) / (np.arange(len(hits)) + 1)
    return float((precision * hits).sum() / hits.sum())


def confusion(y: np.ndarray, p: np.ndarray, thr: float) -> dict:
    pred = (p >= thr).astype(int)
    tp, fp = int(((pred == 1) & (y == 1)).sum()), int(((pred == 1) & (y == 0)).sum())
    fn, tn = int(((pred == 0) & (y == 1)).sum()), int(((pred == 0) & (y == 0)).sum())
    return {"threshold": float(thr), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "sensitivity": tp / (tp + fn) if tp + fn else None, "specificity": tn / (tn + fp) if tn + fp else None,
            "false_positive_rate": fp / (fp + tn) if fp + tn else None,
            "accuracy": (tp + tn) / len(y)}


def youden_threshold(y: np.ndarray, p: np.ndarray) -> float:
    best_t, best_j = 0.5, -np.inf
    for t in np.unique(np.round(p, 6)):
        c = confusion(y, p, t)
        if c["sensitivity"] is None or c["specificity"] is None:
            continue
        j = c["sensitivity"] + c["specificity"] - 1
        if j > best_j + 1e-12:
            best_t, best_j = float(t), j
    return best_t


def sensitivity_at_specificity(burning: np.ndarray, score: np.ndarray, target: float = 0.90) -> dict:
    """Share of still-burning cases caught when at least `target` of the not-burning cases are called correctly."""
    best = {"threshold": None, "sensitivity": 0.0, "specificity": None}
    for t in np.unique(np.round(score, 6)):
        c = confusion(burning, score, t)
        if c["specificity"] is not None and c["specificity"] >= target and (c["sensitivity"] or 0) >= best["sensitivity"]:
            best = {"threshold": float(t), "sensitivity": c["sensitivity"], "specificity": c["specificity"]}
    return best


def calibration(y: np.ndarray, p: np.ndarray, bins: int = 10) -> dict:
    from sklearn.linear_model import LogisticRegression

    q = np.clip(p, 1e-6, 1 - 1e-6)
    logit = np.log(q / (1 - q)).reshape(-1, 1)
    slope = intercept = None
    if len(np.unique(y)) == 2 and np.ptp(logit) > 0:
        m = LogisticRegression(C=1e6, solver="lbfgs", max_iter=5000).fit(logit, y)
        slope, intercept = float(m.coef_[0, 0]), float(m.intercept_[0])
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    table = [{"bin": f"{edges[b]:.1f}-{edges[b + 1]:.1f}", "n": int((idx == b).sum()),
              "mean_predicted": float(p[idx == b].mean()), "observed_share": float(y[idx == b].mean())}
             for b in range(bins) if (idx == b).any()]
    return {"slope": slope, "intercept": intercept, "bins": table}


def cluster_bootstrap_auc(y, p, groups, n_boot: int = N_BOOT) -> tuple[float | None, float | None]:
    rng = np.random.default_rng(SEED)
    uniq = np.unique(groups)
    index = {g: np.where(groups == g)[0] for g in uniq}
    vals = []
    for _ in range(n_boot):
        take = np.concatenate([index[g] for g in rng.choice(uniq, len(uniq), replace=True)])
        a = auc(y[take], p[take])
        if a is not None:
            vals.append(a)
    if len(vals) < n_boot * 0.5:
        return None, None
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def roc_points(y: np.ndarray, p: np.ndarray) -> list[list[float]]:
    pts = [[0.0, 0.0]]
    for t in sorted(np.unique(np.round(p, 6)), reverse=True):
        c = confusion(y, p, t)
        if c["sensitivity"] is not None and c["false_positive_rate"] is not None:
            pts.append([round(c["false_positive_rate"], 4), round(c["sensitivity"], 4)])
    pts.append([1.0, 1.0])
    return pts


# =============================================================================== full run

def rowwise_auc(df: pd.DataFrame, spec: Spec, C: float, balanced: bool) -> float | None:
    """AUC from ordinary row-wise 5-fold CV. Reported ONLY to show how much it flatters the model:
    rows from one atmosphere or one test series land on both sides of the split."""
    from sklearn.model_selection import StratifiedKFold

    y = df["y"].to_numpy()
    if min(y.sum(), len(y) - y.sum()) < 5:
        return None
    oof = np.zeros(len(df))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(df, y):
        prep = fit_prep(df.iloc[tr], spec)
        oof[te] = _fit(transform(df.iloc[tr], spec, prep), y[tr], C, balanced).predict_proba(
            transform(df.iloc[te], spec, prep))[:, 1]
    return auc(y, oof)


def nn_distances(X: np.ndarray) -> np.ndarray:
    """Leave-one-out nearest-neighbour distance of every training row (standardised feature space)."""
    d = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return d.min(axis=1)


def distance_columns(spec: Spec) -> list[str]:
    """Continuous inputs used for distance-to-data (interactions and indicators are not distances)."""
    return list(spec.continuous)


def train(name: str, n_boot: int = N_BOOT) -> dict:
    spec = SPECS[name]
    df = frame_for(name).reset_index(drop=True)
    y = df["y"].to_numpy()
    cv = nested_cv(df, spec)
    oof = cv["oof"]
    groups = cv["split_groups"]
    balanced = cv["balanced"]

    # ---- final model on all rows, C by grouped CV over the whole set
    C_final = choose_C(df, spec, groups, balanced)
    prep = fit_prep(df, spec)
    X = transform(df, spec, prep)
    final = _fit(X, y, C_final, balanced)
    names = feature_names(spec)
    coef = np.concatenate([final.intercept_, final.coef_[0]])

    # ---- cluster bootstrap of the final model: coefficient intervals and prediction intervals
    rng = np.random.default_rng(SEED)
    uniq = np.unique(groups)
    index = {g: np.where(groups == g)[0] for g in uniq}
    boots = []
    for _ in range(n_boot):
        take = np.concatenate([index[g] for g in rng.choice(uniq, len(uniq), replace=True)])
        if len(np.unique(y[take])) < 2:
            continue
        # every bootstrap model uses the final model's standardisation, so coefficients are comparable
        mb = _fit(X[take], y[take], C_final, balanced)
        boots.append(np.concatenate([mb.intercept_, mb.coef_[0]]).round(6).tolist())
    boot_coef = np.array(boots)
    lo, hi = np.percentile(boot_coef, [2.5, 97.5], axis=0)

    # ---- metrics on pooled out-of-fold predictions
    a = auc(y, oof)
    a_lo, a_hi = cluster_bootstrap_auc(y, oof, groups, n_boot)
    thr_j = youden_threshold(y, oof)
    burning = y if spec.burning_is_y1 else 1 - y
    burn_score = oof if spec.burning_is_y1 else 1 - oof
    per_group = []
    for g in sorted(set(df[spec.report_group_col])):
        m = (df[spec.report_group_col] == g).to_numpy()
        per_group.append({"group": g, "n": int(m.sum()), "positives": int(y[m].sum()), "auc": auc(y[m], oof[m]),
                          "mean_predicted": float(oof[m].mean()), "observed_share": float(y[m].mean())})
    lomo = leave_one_material_out(df, spec)
    candidates = [v for v in (a, lomo["pooled_auc"]) if v is not None]
    dist_cols = distance_columns(spec)
    Xd = X[:, : len(spec.continuous)]
    nn = nn_distances(Xd)

    result = {
        "name": name, "title": spec.title, "target_label": spec.target_label, "burning_is_y1": spec.burning_is_y1,
        "seed": SEED, "n_rows": int(len(df)), "n_positive": int(y.sum()), "positive_share": float(y.mean()),
        "class_weight_balanced": balanced, "C_grid": C_GRID, "C_final": C_final,
        "outer_folds": cv["k"], "C_per_outer_fold": cv["C_per_fold"],
        "n_groups": int(len(set(df[spec.group_col]))), "n_split_groups": int(len(uniq)),
        "features": names, "continuous": spec.continuous, "log_features": spec.log_features,
        "log1p_features": spec.log1p_features, "binary": spec.binary, "categorical": spec.categorical,
        "interactions": [list(t) for t in spec.interactions], "squares": spec.squares,
        "dropped_features": spec.dropped, "added_features": spec.added, "notes": spec.notes,
        "prep": prep, "coef": coef.round(6).tolist(),
        "coef_table": [{"feature": n, "log_odds": float(c), "odds_ratio": float(np.exp(c)),
                        "ci_low": float(l), "ci_high": float(h)}
                       for n, c, l, h in zip(["(intercept)"] + names, coef, lo, hi)],
        "bootstrap": {"n": len(boots), "coef": boots},
        "metrics": {
            "roc_auc": a, "roc_auc_ci": [a_lo, a_hi], "pr_auc": average_precision(y, oof),
            "brier": float(np.mean((oof - y) ** 2)), "calibration": calibration(y, oof),
            "confusion_at_0.5": confusion(y, oof, 0.5), "youden_threshold": thr_j,
            "confusion_at_youden": confusion(y, oof, thr_j),
            "burning_sensitivity_at_90_specificity": sensitivity_at_specificity(burning, burn_score),
            "per_group": per_group, "roc": roc_points(y, oof),
            "baseline_majority_accuracy": float(max(y.mean(), 1 - y.mean())),
            "rowwise_cv_auc_for_comparison_only": rowwise_auc(df, spec, C_final, balanced),
        },
        "leave_one_material_out": lomo,
        "headline_auc": min(candidates) if candidates else None,
        "headline_is": ("leave-one-material-out" if candidates and lomo["pooled_auc"] is not None
                        and lomo["pooled_auc"] <= (a if a is not None else 2) else "grouped cross-validation"),
        "envelope": {c: [float(df[c].min()), float(df[c].max())] for c in dist_cols},
        "distance": {"columns": dist_cols, "train_nn_median": float(np.median(nn)),
                     "train_nn_p95": float(np.percentile(nn, 95)), "train_nn_max": float(nn.max())},
        "oof": [{"row_id": r, "group": g, "y": int(t), "p": round(float(p), 5), "fold": int(f)}
                for r, g, t, p, f in zip(df["row_id"], df[spec.report_group_col], y, oof, cv["fold"])],
        "training_rows": df[["row_id"] + dist_cols + [c for c in spec.binary + list(spec.categorical) if c in df]
                            ].assign(y=y).round(4).to_dict("records"),
    }
    return {"result": result, "splits": {"outer": cv["folds"], "k": cv["k"], "seed": SEED,
                                         "group_column": spec.group_col,
                                         "groups": dict(zip(df["row_id"], map(str, groups)))}}


# =============================================================================== prediction (numpy only)

class Fitted:
    """A trained model loaded from JSON. Predicts with numpy only."""

    def __init__(self, name: str):
        self.r = json.loads((MODEL_DIR / f"{name}.json").read_text(encoding="utf-8"))
        self.name = name

    def _row(self, x: dict, prep: dict) -> np.ndarray:
        r = self.r
        vals, z = [1.0], {}
        for col in r["continuous"]:
            v = x.get(col)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                t = prep["median"][col]
            elif col in r["log_features"]:
                t = float(np.log(v))
            elif col in r["log1p_features"]:
                t = float(np.log1p(v))
            else:
                t = float(v)
            z[col] = (t - prep["mean"][col]) / prep["sd"][col]
            vals.append(z[col])
        for col in r["binary"]:
            vals.append(float(x.get(col, 0.0)))
        for col, cats in r["categorical"].items():
            v = x.get(col)
            v = v if v in cats else ("rare" if "rare" in cats else None)
            vals += [1.0 if v == c else 0.0 for c in cats]
        for a, b in r["interactions"]:
            vals.append(z[a] * z[b])
        for c in r.get("squares", []):
            vals.append(z[c] ** 2)
        return np.array(vals)

    def predict(self, x: dict) -> dict:
        """Probability with a 95% cluster-bootstrap interval, plus distance to the training data."""
        r = self.r
        row = self._row(x, r["prep"])
        p = float(1 / (1 + np.exp(-row @ np.array(r["coef"]))))
        ps = 1 / (1 + np.exp(-np.array(r["bootstrap"]["coef"]) @ row))
        lo, hi = (float(v) for v in np.percentile(ps, [2.5, 97.5])) if len(ps) else (None, None)
        return {"p": p, "lo": lo, "hi": hi, **self.distance(x)}

    def distance(self, x: dict) -> dict:
        """How far a query sits from the rows the model was trained on."""
        r = self.r
        cols, prep = r["distance"]["columns"], r["prep"]

        def zrow(src: dict) -> np.ndarray:
            return self._row(src, prep)[1: 1 + len(r["continuous"])]

        q = zrow(x)
        train = np.array([zrow(t) for t in r["training_rows"]])
        d = np.sqrt(((train - q) ** 2).sum(axis=1))
        order = np.argsort(d)[:5]
        outside = []
        for c in cols:
            v, (lo, hi) = x.get(c), r["envelope"][c]
            if v is not None and not (isinstance(v, float) and np.isnan(v)) and not (lo - 1e-9 <= v <= hi + 1e-9):
                outside.append({"feature": c, "value": float(v), "tested_min": lo, "tested_max": hi})
        nn, p95 = float(d.min()), r["distance"]["train_nn_p95"]
        return {"nn_distance": nn, "train_nn_p95": p95, "train_nn_median": r["distance"]["train_nn_median"],
                "outside_envelope": outside, "far_from_data": bool(nn > p95),
                "extrapolating": bool(outside or nn > p95),
                "nearest": [{"row_id": r["training_rows"][i]["row_id"], "distance": float(d[i]),
                             "y": r["training_rows"][i]["y"]} for i in order]}
