"""FLEX droplet data: loading, derived quantities, and the normalised research schema.

Everything here is computed from data/flex-table-ix.csv (Table IX of
NASA/TP-2015-216046) and data/flex_caption_annotations.csv (Appendix B figure
captions of the same report). Nothing is imputed: an empty source cell stays NaN.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"

REPORT = "NASA/TP-2015-216046"
REPORT_TITLE = ("Detailed Results From the Flame Extinguishment Experiment (FLEX) "
                "March 2009 to December 2011, Dietrich et al., Nov 2015")
RECORD_URL = "https://ntrs.nasa.gov/citations/20150023456"
PDF_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf"
TEXT_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.txt"
PSI_ID = "PSI-69"

MMHG_PER_ATM = 760.0
KPA_PER_MMHG = 101.325 / 760.0

# Rows of Table IX printed on each PDF page (26..34); checked by scripts/verify_flex_table_ix.py.
ROWS_PER_PDF_PAGE = {26: 31, 27: 34, 28: 35, 29: 35, 30: 35, 31: 34, 32: 33, 33: 34, 34: 5}

OUTCOMES = ["Extinction", "Disruption", "Completion"]
FUEL_FORMULA = {"Methanol": "CH3OH", "Heptane": "C7H16"}
FUEL_SCHEMA_NAME = {"Methanol": "methanol", "Heptane": "n-heptane"}

SCHEMA_COLUMNS = [
    "test_id", "psi_investigation", "fuel", "fuel_formula", "D0_mm", "pressure_atm", "o2_mol_pct",
    "diluent", "o2_is_ambient", "support", "K_hot_mm2_s", "K_cool_mm2_s", "D_rad_ext_mm",
    "D_diff_ext_mm", "extinction_mode", "cool_flame_observed", "flame_temp_hot_K", "flame_temp_cool_K",
    "FSR", "peak_SVF_ppm", "burn_duration_s", "source_table", "source_url", "verification",
]
EXTRA_COLUMNS = [
    "flex_no", "outcome", "visible_ext_diameter_mm", "co2_mol_pct", "he_mol_pct", "n2_mol_pct",
    "cool_flame_label", "cool_flame_quote", "extinction_wording", "caption_figure", "pdf_page", "notes",
]


def diluent_label(row: pd.Series) -> str:
    if row["co2"] > 0:
        return "N2/CO2" if row["n2"] > 0 else "CO2"
    if row["he"] > 0:
        return "N2/He" if row["n2"] > 0 else "He"
    return "N2"


def atmosphere_family(row: pd.Series) -> str:
    """The four filter families used in the Explorer."""
    if row["co2"] > 0:
        return "CO2-diluted"
    if row["he"] > 0:
        return "He-diluted"
    if abs(row["o2"] - 0.21) < 1e-9 and abs(row["n2"] - 0.79) < 1e-9:
        return "Air (0.21 O2 / 0.79 N2)"
    return "N2-diluted (not air)"


@lru_cache(maxsize=1)
def load_table_ix() -> pd.DataFrame:
    """Table IX exactly as extracted: 276 rows, 16 columns, empty cells as NaN."""
    df = pd.read_csv(DATA / "flex-table-ix.csv", dtype={"cir_id": str, "date": str, "gmt": str, "notes": str})
    df["notes"] = df["notes"].fillna("")
    return df


@lru_cache(maxsize=1)
def load_captions() -> pd.DataFrame:
    df = pd.read_csv(DATA / "flex_caption_annotations.csv", dtype=str).fillna("")
    df["test_no"] = df["test_no"].astype(int)
    df["figure_no"] = df["figure_no"].astype(int)
    return df


@lru_cache(maxsize=1)
def load_flex() -> pd.DataFrame:
    """Table IX plus derived columns and caption annotations. One row per test."""
    df = load_table_ix().copy()
    df["test_id"] = df["test_no"].map(lambda n: f"FLEX-{n:03d}")
    df["date_iso"] = pd.to_datetime(df["date"], format="%m/%d/%y").dt.strftime("%Y-%m-%d")
    df["pressure_atm"] = df["pressure_mmhg"] / MMHG_PER_ATM
    df["pressure_kpa"] = df["pressure_mmhg"] * KPA_PER_MMHG
    for gas in ("o2", "n2", "co2", "he"):
        df[f"{gas}_pct"] = (df[gas] * 100).round(6)
    df["o2_partial_kpa"] = df["o2"] * df["pressure_kpa"]
    df["gas_sum"] = (df["o2"] + df["n2"] + df["co2"] + df["he"]).round(4)
    df["diluent"] = df.apply(diluent_label, axis=1)
    df["atmosphere"] = df.apply(atmosphere_family, axis=1)
    df["extinguished"] = (df["outcome"] == "Extinction").astype(int)
    # Which PDF page the row is printed on (rows are in test-number order).
    pages = np.repeat(list(ROWS_PER_PDF_PAGE), list(ROWS_PER_PDF_PAGE.values()))
    df["pdf_page"] = pages[: len(df)]
    caps = load_captions().rename(columns={"cool_flame": "cool_flame_label", "figure_no": "caption_figure"})
    df = df.merge(caps[["test_no", "caption_figure", "support", "cool_flame_label", "cool_flame_quote",
                        "extinction_wording", "extinction_quote"]], on="test_no", how="left")
    for col in ("support", "cool_flame_label", "cool_flame_quote", "extinction_wording", "extinction_quote"):
        df[col] = df[col].fillna("")
    df["source"] = df.apply(
        lambda r: f"{REPORT}, Table IX, PDF p. {r['pdf_page']}, row {r['test_id']}", axis=1)
    return df


def extinction_mode(row: pd.Series) -> str:
    """Schema value for extinction_mode, using only what the report states.

    Disruption is kept as its own value: a disrupted droplet is not an extinguished flame.
    """
    if row["outcome"] == "Completion":
        return "no_extinction_burnout"
    if row["outcome"] == "Disruption":
        return "disruption"
    wording, cool = row["extinction_wording"], row["cool_flame_label"]
    if cool == "indicated":
        return "radiative_then_diffusive"
    if wording == "radiative":
        return "radiative_cool_flame_not_stated"
    if wording == "diffusive":
        return "diffusive_only"
    return "visible_extinction_mode_not_stated"


def build_schema_frame() -> pd.DataFrame:
    """Normalise FLEX into the 24-column research schema (plus clearly separated extras).

    Columns the source does not give (cool-flame burning rate, second-stage extinction
    diameter, flame temperatures, standoff ratio, soot volume fraction) are left empty.
    """
    f = load_flex()
    mode = f.apply(extinction_mode, axis=1)
    radiative = mode.isin(["radiative_then_diffusive", "radiative_cool_flame_not_stated"])
    cool = f["cool_flame_label"].map({"indicated": True, "not_indicated": False})
    out = pd.DataFrame({
        "test_id": [f"FLEX-{FUEL_SCHEMA_NAME[fu]}-{n:03d}" for fu, n in zip(f["fuel"], f["test_no"])],
        "psi_investigation": "FLEX",
        "fuel": f["fuel"].map(FUEL_SCHEMA_NAME),
        "fuel_formula": f["fuel"].map(FUEL_FORMULA),
        "D0_mm": f["d0_mm"],
        "pressure_atm": f["pressure_atm"].round(4),
        "o2_mol_pct": f["o2_pct"],
        "diluent": f["diluent"],
        "o2_is_ambient": True,
        "support": f["support"].map({"free-floating": "free_floated", "fiber-supported": "tethered_fibre"}),
        "K_hot_mm2_s": f["burning_rate_mm2_s"],
        "K_cool_mm2_s": np.nan,
        "D_rad_ext_mm": f["extinction_diameter_mm"].where(radiative),
        "D_diff_ext_mm": f["extinction_diameter_mm"].where(mode == "diffusive_only"),
        "extinction_mode": mode,
        "cool_flame_observed": cool,
        "flame_temp_hot_K": np.nan,
        "flame_temp_cool_K": np.nan,
        "FSR": np.nan,
        "peak_SVF_ppm": np.nan,
        "burn_duration_s": f["burn_time_s"],
        "source_table": [
            f"{REPORT} Table IX (PDF p. {p})" + (f"; Appendix B Fig. {int(c)} caption" if pd.notna(c) else "")
            for p, c in zip(f["pdf_page"], f["caption_figure"])],
        "source_url": PDF_URL,
        "verification": "verified_live",
        # ---- extras, outside the 24-column schema ----
        "flex_no": f["test_no"],
        "outcome": f["outcome"],
        "visible_ext_diameter_mm": f["extinction_diameter_mm"],
        "co2_mol_pct": f["co2_pct"],
        "he_mol_pct": f["he_pct"],
        "n2_mol_pct": f["n2_pct"],
        "cool_flame_label": f["cool_flame_label"],
        "cool_flame_quote": f["cool_flame_quote"],
        "extinction_wording": f["extinction_wording"],
        "caption_figure": f["caption_figure"],
        "pdf_page": f["pdf_page"],
        "notes": f["notes"],
    })
    return out[SCHEMA_COLUMNS + EXTRA_COLUMNS]


@lru_cache(maxsize=1)
def load_schema() -> pd.DataFrame:
    df = pd.read_csv(DATA / "flex_droplets.csv", dtype={"cool_flame_observed": "boolean"})
    for col in ("support", "notes", "cool_flame_label", "cool_flame_quote", "extinction_wording"):
        df[col] = df[col].fillna("")
    return df


# --------------------------------------------------------------------------- summaries

def summary() -> dict:
    """Headline numbers, recomputed from the CSV on every call (never hard-coded)."""
    f = load_flex()
    by_fuel = f.groupby("fuel")["outcome"].value_counts().unstack(fill_value=0)
    hept_ext = f[(f["fuel"] == "Heptane") & (f["outcome"] == "Extinction")]
    out = {
        "n": int(len(f)),
        "first_test": f["test_id"].iloc[0],
        "last_test": f["test_id"].iloc[-1],
        "absent_numbers": sorted(set(range(1, int(f["test_no"].max()) + 1)) - set(f["test_no"])),
        "outcomes": {o: int((f["outcome"] == o).sum()) for o in OUTCOMES},
        "extinction_share": float((f["outcome"] == "Extinction").mean()),
        "by_fuel": {
            fuel: {"n": int(by_fuel.loc[fuel].sum()),
                   **{o: int(by_fuel.loc[fuel].get(o, 0)) for o in OUTCOMES},
                   "extinction_share": float(by_fuel.loc[fuel].get("Extinction", 0) / by_fuel.loc[fuel].sum())}
            for fuel in by_fuel.index},
        "ranges": {c: (float(f[c].min()), float(f[c].max()), int(f[c].notna().sum()), int(f[c].isna().sum()))
                   for c in ["pressure_mmhg", "o2", "n2", "co2", "he", "d0_mm", "extinction_diameter_mm",
                             "burning_rate_mm2_s", "burn_time_s"]},
        "he_tests": int((f["he"] > 0).sum()),
        "co2_tests": int((f["co2"] > 0).sum()),
        "co2_and_he": int(((f["co2"] > 0) & (f["he"] > 0)).sum()),
        "gas_sum_not_1": f.loc[(f["gas_sum"] - 1).abs() > 0.005, "test_id"].tolist(),
        "noted_rows": f.loc[f["notes"] != "", "test_id"].tolist(),
        "missing_gmt": int(f["gmt"].isna().sum()),
        "heptane_extinctions": int(len(hept_ext)),
        "cool_flame": {k: int((hept_ext["cool_flame_label"] == k).sum())
                       for k in ["indicated", "not_indicated", "unclear", ""]},
        "captions": int((f["caption_figure"].notna()).sum()),
    }
    return out


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial share (used for every share shown with n)."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
