"""Validation rules (a)-(e) for the normalised droplet schema, as machine-checkable functions.

Each rule returns the list of offending test_ids. The tests assert that the only
offenders are the documented source gaps in KNOWN_SOURCE_GAPS: places where the
printed NASA table itself is incomplete. We report those; we do not paper over them.
"""
from __future__ import annotations

import pandas as pd

ALLOWED_EXTINCTION_MODES = {
    # from the research schema
    "radiative_then_diffusive", "diffusive_only", "no_extinction_burnout", "no_ignition",
    # added so that Table IX outcomes are never forced into a category the source does not state
    "disruption", "radiative_cool_flame_not_stated", "visible_extinction_mode_not_stated",
}
ALLOWED_VERIFICATION = {"verified_live", "index", "unverified"}
ALLOWED_SUPPORT = {"tethered_fibre", "free_floated", "deployment_fibre"}

# Rounding resolution of the printed table (two decimals) plus measurement scatter:
# an extinction diameter may read 0.01-0.02 mm above D0 when the flame went out at once.
DIAMETER_TOLERANCE_MM = 0.02

KNOWN_SOURCE_GAPS = {
    "a_missing_K": "Table IX prints '-' for the burning rate of 16 ignited tests; kept empty, never imputed.",
    "b": {"FLEX-n-heptane-212": "Caption reports probable cool-flame burning, but Table IX prints '-' for "
                                "every diameter of FLEX-212, so no radiative-extinction diameter exists."},
}


def rule_a_no_ignition_has_no_K(df: pd.DataFrame) -> list[str]:
    """(a) A test that never ignited cannot have a hot-flame burning rate."""
    bad = df[(df["extinction_mode"] == "no_ignition") & df["K_hot_mm2_s"].notna()]
    return bad["test_id"].tolist()


def rule_a_missing_K_but_ignited(df: pd.DataFrame) -> list[str]:
    """Converse of (a): ignited tests whose burning rate is missing in the source (a data gap, listed)."""
    bad = df[(df["extinction_mode"] != "no_ignition") & df["K_hot_mm2_s"].isna()]
    return bad["test_id"].tolist()


def rule_b_cool_flame_needs_radiative_diameter(df: pd.DataFrame) -> list[str]:
    """(b) cool_flame_observed => D_rad_ext present, and D_diff_ext < D_rad_ext when both exist."""
    cool = df[df["cool_flame_observed"].fillna(False).astype(bool)]
    missing = cool[cool["D_rad_ext_mm"].isna()]
    both = cool.dropna(subset=["D_rad_ext_mm", "D_diff_ext_mm"])
    order = both[both["D_diff_ext_mm"] >= both["D_rad_ext_mm"]]
    return missing["test_id"].tolist() + order["test_id"].tolist()


def rule_c_diameters_ordered(df: pd.DataFrame, tol: float = DIAMETER_TOLERANCE_MM) -> list[str]:
    """(c) D0 >= D_rad_ext >= D_diff_ext whenever present (within the table's rounding tolerance)."""
    bad = []
    for col in ("D_rad_ext_mm", "D_diff_ext_mm", "visible_ext_diameter_mm"):
        if col in df:
            sub = df.dropna(subset=["D0_mm", col])
            bad += sub.loc[sub[col] > sub["D0_mm"] + tol, "test_id"].tolist()
    both = df.dropna(subset=["D_rad_ext_mm", "D_diff_ext_mm"])
    bad += both.loc[both["D_diff_ext_mm"] > both["D_rad_ext_mm"] + tol, "test_id"].tolist()
    return sorted(set(bad))


def ambient_o2_only(df: pd.DataFrame, o2_col: str = "o2_mol_pct") -> pd.DataFrame:
    """(d) The only way to get O2 values for an ambient-O2 axis.

    Rows whose oxygen value is a burner feed (o2_is_ambient = False), e.g. the
    85 % inverse-flame burner flow, are dropped here and can never share an axis
    with chamber-ambient values.
    """
    if "o2_is_ambient" not in df:
        raise ValueError("o2_is_ambient column is mandatory for any frame plotted against ambient O2")
    flag = df["o2_is_ambient"].map(lambda v: str(v).strip().lower() in ("true", "1", "yes"))
    return df[flag & df[o2_col].notna()]


MODEL_VERIFICATION = {"verified_live", "index"}


def model_rows_only(df: pd.DataFrame) -> pd.DataFrame:
    """(e) Only rows with a stated, acceptable verification level reach a model.

    Fails closed: `unverified`, a blank cell and any unknown value are all kept out.
    """
    return df[df["verification"].isin(MODEL_VERIFICATION)]


def check_vocabulary(df: pd.DataFrame) -> list[str]:
    problems = []
    bad = set(df["extinction_mode"]) - ALLOWED_EXTINCTION_MODES
    if bad:
        problems.append(f"extinction_mode not allowed: {sorted(bad)}")
    bad = set(df["verification"]) - ALLOWED_VERIFICATION
    if bad:
        problems.append(f"verification not allowed: {sorted(bad)}")
    bad = set(df["support"].dropna()) - ALLOWED_SUPPORT - {""}
    if bad:
        problems.append(f"support not allowed: {sorted(bad)}")
    if df["test_id"].duplicated().any():
        problems.append("duplicate test_id")
    return problems
