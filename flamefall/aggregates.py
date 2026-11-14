"""Aggregates of the FLEX (droplet) evidence. Droplet data only: never mixed with solids.

These are the reference calculations: anything that presents these numbers must agree with them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import flex


def logistic_trend(x: np.ndarray, y: np.ndarray, grid: np.ndarray) -> np.ndarray | None:
    """One-variable logistic fit (Newton iterations). Returns None when it cannot be fitted."""
    if len(x) < 8 or len(set(y)) < 2 or np.ptp(x) == 0:
        return None
    mu, sd = x.mean(), x.std()
    X = np.column_stack([np.ones_like(x, dtype=float), (x - mu) / sd])
    beta = np.zeros(2)
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ beta))
        w = np.clip(p * (1 - p), 1e-6, None)
        hess = X.T @ (X * w[:, None]) + 1e-3 * np.eye(2)   # tiny ridge keeps separable data finite
        step = np.linalg.solve(hess, X.T @ (y - p) - 1e-3 * beta)
        beta += step
        if np.abs(step).max() < 1e-8:
            break
    G = np.column_stack([np.ones_like(grid, dtype=float), (grid - mu) / sd])
    return 1 / (1 + np.exp(-G @ beta))


SHARE_COLUMNS = ["fuel", "level", "n", "k", "share", "lo", "hi", "disruption", "completion"]


def share_by_level(df: pd.DataFrame, xcol: str) -> pd.DataFrame:
    """Extinction share at each tested level of xcol, per fuel, with Wilson 95% intervals."""
    rows = []
    for (fuel, level), g in df.groupby(["fuel", xcol]):
        n, k = len(g), int(g["extinguished"].sum())
        lo, hi = flex.wilson_interval(k, n)
        rows.append(dict(fuel=fuel, level=level, n=n, k=k, share=k / n, lo=lo, hi=hi,
                         disruption=int((g["outcome"] == "Disruption").sum()),
                         completion=int((g["outcome"] == "Completion").sum())))
    # the columns are fixed so that an empty selection gives an empty table, not a table with no columns
    return pd.DataFrame(rows, columns=SHARE_COLUMNS)


def nearest_tests(pool: pd.DataFrame, o2_pct: float, pressure_atm: float, n: int = 8) -> pd.DataFrame:
    """The n tests closest to a target oxygen level and pressure.

    A test with no printed pressure (FLEX-114) is not ranked: a missing value is never replaced.
    """
    pool = pool[pool["pressure_atm"].notna()]
    dist = ((pool["o2_pct"] - o2_pct) / 22) ** 2 + ((pool["pressure_atm"] - pressure_atm) / 2.4) ** 2
    return pool.assign(distance=dist).nsmallest(n, "distance")


def end_diameter_label(outcome: str) -> str:
    """What to call the value from Table IX's extinction-diameter column for a given outcome."""
    return "Ext. diameter" if outcome == "Extinction" else "Diameter at test end"


END_MARKER_EXTINCTION = "Reported visible-flame extinction diameter²"
END_MARKER_OTHER = "Diameter² printed at test end ({outcome}, not an extinction)"


def d2_line(row: pd.Series) -> dict | None:
    """d²-law line rebuilt from Table IX (D0, average K, burn time). Not the measured trace.

    Returns the two ends of the line and, when Table IX prints an end diameter, the marker with the
    name it must carry. None when any of the three inputs is missing.

    A diameter squared cannot be negative. For some tests the printed average K and burn time take
    the straight line below zero before the burn ends: the three printed numbers do not fit one
    line over the whole burn. The line is then drawn down to zero and no further; `t_zero` is the
    time it gets there and `t_line_end` is where the line stops. `t_end` is always the printed
    burn time.
    """
    d0, k, t_end = row["d0_mm"], row["burning_rate_mm2_s"], row["burn_time_s"]
    if pd.isna(d0) or pd.isna(k) or pd.isna(t_end):
        return None
    d2_start, d2_end = float(d0 ** 2), float(d0 ** 2 - k * t_end)
    t_zero = float(d0 ** 2 / k) if d2_end < 0 else None
    line = dict(t_end=float(t_end), d2_start=d2_start, d2_end=max(d2_end, 0.0), t_zero=t_zero,
                t_line_end=float(t_end) if t_zero is None else t_zero, marker=None)
    dext = row["extinction_diameter_mm"]
    if not pd.isna(dext):
        # Table IX prints a value in this column for some Disruption and Completion tests too.
        # Only an Extinction outcome makes it an extinction diameter.
        name = (END_MARKER_EXTINCTION if row["outcome"] == "Extinction"
                else END_MARKER_OTHER.format(outcome=row["outcome"]))
        line["marker"] = dict(name=name, t=float(t_end), d2=float(dext ** 2), diameter_mm=float(dext))
    return line
