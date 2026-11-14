"""Build data/solid_test_points.csv: every solid-fuel test point with a stated outcome.

Sources, all read in full:
  * BASS-II  - data/bass2/bass2_test_points.csv, transcribed from NASA/TM-20210011385
               (Tables 5.1, 7.1, A.1-A.6). See data/bass2/README.md for the labelling rules.
  * Saffire  - PSI experimental tables (PSI-98, PSI-99), Olson et al. 2023 Table 1,
               ICES-2024-365 Table 1, ICES-2025-156 Table 1.
  * SoFIE-GEL - Li et al., NTRS 20240007628, Table 1.

Solid fuels only. Droplet and gas-flame tests never enter this file.

`sustained` is 1 when the source says the flame burned or spread at that condition, 0 when it
says it quenched, blew off or did not ignite, and empty when the source is unclear ("ambiguous").
`usable_for_model` additionally requires oxygen, pressure and a flow velocity in cm/s.

Run from the repo root:  python scripts/build_solid_points.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
TM_URL = "https://ntrs.nasa.gov/citations/20210011385"
ICES2024 = ("Urban et al., ICES-2024-365, Table 1", "https://ntrs.nasa.gov/citations/20240002981")
OLSON2023 = ("Olson et al., Combust. Flame 248 (2023) 112559, Table 1 (accepted manuscript)",
             "https://discovery.ucl.ac.uk/id/eprint/10164340/")
GEL = ("Li, T'ien, Ferkul, Olson, 40th Int. Symp. Combust., Table 1 (NTRS 20240007628)",
       "https://ntrs.nasa.gov/citations/20240007628")
PSI99 = ("PSI-99 experimental table (Saffire-II)", "https://psi.nasa.gov/physci/repo/data/investigations/PSI-99")

BASS2_PRESSURE_BASIS = ("NASA/TM-20210011385 §7 (report p. 95): 'Ambient pressure was 1 atm', stated for the fabric "
                        "tests; the other BASS-II tests ran in the same glovebox working volume")
KPA_PER_ATM = 101.325

COLUMNS = ["point_id", "investigation_id", "group_id", "test_no", "material_class", "material_verbatim", "geometry",
           "thickness_mm", "flow_direction", "flow_cm_s", "flow_value_kind", "o2_pct", "o2_final_pct", "o2_at_outcome_pct",
           "o2_at_outcome_basis", "o2_is_ambient",
           "pressure_kPa", "pressure_basis", "gravity_g", "outcome", "sustained", "outcome_quote", "source_ref",
           "source_url", "verification", "usable_for_model", "notes"]

# (point_id, investigation, test, material_class, material, geometry, thickness_mm, direction, flow, o2, kPa,
#  outcome, quote, (source_ref, url), notes)
EXTRA = [
    ("SAF1-S1", "Saffire-I", "sample 1", "SIBAL-cotton", "SIBAL fabric 94 x 40.6 cm", "fabric", None, "concurrent",
     20, 21.7, 102, "sustained", "Vf 0.18 cm/s", OLSON2023, ""),
    ("SAF2-5", "Saffire-II", "2-5", "SIBAL-cotton", "Cotton-Fiberglass (SIBAL) 29 x 5 cm", "fabric", 0.37,
     "concurrent", 20, 22.1, 103, "sustained", "µ-g burn length 29 cm; µ-g spread 2.1 mm/s", PSI99,
     "Oxygen printed as '~ 22.1'; pressure 103 kPa from Olson et al. 2023 Table 1. Thickness printed '037 mm'."),
    ("SAF2-6", "Saffire-II", "2-6", "SIBAL-cotton", "Cotton-Fiberglass (SIBAL) 29 x 5 cm", "fabric", 0.37,
     "concurrent", 20, 22.1, 103, "sustained", "µ-g burn length 29 cm; µ-g spread 2.6 mm/s", PSI99,
     "PSI prints 20 cm/s for this sample; Olson et al. 2023 Table 1 gives 25 cm/s. The PSI value is used."),
    ("SAF2-1", "Saffire-II", "2-1", "silicone", "Silicone 0.27 mm, 29 x 5 cm", "sheet", 0.27, "concurrent",
     20, 21.5, 103, "no_ignition", "Burn time: Insignificant; µ-g burn length ~ 0", PSI99,
     "The same PSI row records that this sample burned completely in normal gravity."),
    ("SAF2-2", "Saffire-II", "2-2", "silicone", "Silicone 0.61 mm, 29 x 5 cm", "sheet", 0.61, "concurrent",
     20, 22.1, 103, "no_ignition", "Burn time: Insignificant; µ-g burn length ~ 0", PSI99,
     "Normal-gravity burn length in the same row: 7.6 cm."),
    ("SAF2-3", "Saffire-II", "2-3", "silicone", "Silicone 1.03 mm, 29 x 5 cm", "sheet", 1.03, "concurrent",
     20, 22.1, 103, "no_ignition", "Burn time: Insignificant; µ-g burn length ~ 0", PSI99, ""),
    ("SAF2-4", "Saffire-II", "2-4", "silicone", "Silicone, 29 x 5 cm", "sheet", 0.37, "opposed",
     20, 22.1, 103, "no_ignition", "Burn time: Insignificant; µ-g burn length ~ 0", PSI99,
     "Thickness printed '037 mm'. The same row records a complete burn in normal gravity."),
    ("SAF2-7a", "Saffire-II", "2-7 (PMMA part)", "PMMA", "PMMA 0.85 mm, 5 cm long", "sheet", 0.85, "concurrent",
     20, 22.1, 103, "sustained", "The PMMA portion was completely consumed", PSI99, "Sample 2-7 is PMMA followed by Nomex."),
    ("SAF2-7b", "Saffire-II", "2-7 (Nomex part)", "Nomex", "Nomex 0.37 mm, 24 cm long", "fabric", 0.37, "concurrent",
     20, 22.1, 103, "no_ignition", "the Nomex was not ignited", PSI99, "Sample 2-7 is PMMA followed by Nomex."),
    ("SAF2-8", "Saffire-II", "2-8", "PMMA", "PMMA, 29 x 5 cm (structured, see source figure)", "slab", None,
     "concurrent", 20, 22.1, 103, "sustained", "Burn time 600 s; flames remain anchored at the base of the sample",
     PSI99, "Oxygen printed '22.1 to 22.0'."),
    ("SAF2-9", "Saffire-II", "2-9", "PMMA", "PMMA 1 cm thick, 29 x 5 cm", "slab", 10.0, "concurrent",
     20, 22.0, 103, "sustained", "Burn time 900 s; flames remain anchored at the base of the sample", PSI99,
     "Oxygen printed '22.0 to 21.9'."),
    ("SAF3-S1", "Saffire-III", "sample 1", "SIBAL-cotton", "SIBAL fabric 94 x 40.6 cm", "fabric", None, "concurrent",
     25, 21.2, 99, "sustained", "Vf 0.23 cm/s", OLSON2023,
     "PSI's own table prints 30 cm/s for this flight; the journal table's 25 cm/s is used here."),
    ("SAF4-1", "Saffire-IV", "IV-1", "SIBAL-cotton", "SIBAL cloth 50 cm long", "fabric", None, "concurrent",
     20, 22.0, 100.0, "sustained", "Burn duration 130 s; flame spread over the sample", ICES2024,
     "Olson et al. 2023 Table 1 lists this flight at 23.1% O2 and 99 kPa; ICES-2024-365 values are used."),
    ("SAF5-2", "Saffire-V", "V-2", "SIBAL-cotton", "Cotton jersey 50 cm long", "fabric", None, "concurrent",
     20, 26.2, 70.7, "sustained", "Burn duration 200 s; flame spread over the sample", ICES2024,
     "Olson et al. 2023 Table 1 lists this flight at 26.9% O2 and 76 kPa; ICES-2024-365 values are used."),
    ("SAF6-1", "Saffire-VI", "VI-1", "Nomex", "Nomex fabric 7 cm long", "fabric", None, "concurrent",
     20, 31.9, 54.1, "no_ignition", "Nomex Burn: 31.9% O2. Did not Ignite",
     ("Niehaus et al., ICES-2025-156, Table 1 (NTRS 20250002675)", "https://ntrs.nasa.gov/citations/20250002675"),
     "Pressure is the campaign's initial 54.1 kPa (same paper, p. 3)."),
    ("SAF6-2", "Saffire-VI", "VI-2", "SIBAL-cotton", "SIBAL cloth 50 cm long", "fabric", None, "concurrent",
     20, 31.0, 54.1, "sustained", "Burn duration 112 s", ICES2024, ""),
    ("SAF6-3", "Saffire-VI", "VI-3", "PMMA", "Two-sided PMMA 18 cm long, 1 cm thick", "slab", 10.0, "concurrent",
     20, 30.3, 54.6, "sustained", "Burn duration 780 s", ICES2024, ""),
    ("SAF6-4", "Saffire-VI", "VI-4", "PMMA", "One-sided PMMA 18 cm long, 0.5 cm thick", "slab", 5.0, "concurrent",
     20, 28.8, 55.2, "sustained", "Burn duration 1200 s", ICES2024, ""),
    ("GEL-1", "SoFIE-GEL", "case 1 (1409B)", "PMMA", "PMMA sphere 4 cm", "sphere", 40.0, "concurrent",
     4.83, 14.21, round(1.04 * KPA_PER_ATM, 1), "quenched", "Extinction mode: quenching", GEL, ""),
    ("GEL-2", "SoFIE-GEL", "case 2 (1408A)", "PMMA", "PMMA sphere 4 cm", "sphere", 40.0, "concurrent",
     34.28, 14.99, round(1.06 * KPA_PER_ATM, 1), "blowoff", "Extinction mode: blowoff", GEL, ""),
    ("GEL-3", "SoFIE-GEL", "case 3 (1402C)", "PMMA", "PMMA sphere 4 cm", "sphere", 40.0, "concurrent",
     11.50, 13.54, round(1.07 * KPA_PER_ATM, 1), "quenched", "Extinction mode: intermediate", GEL,
     "The source calls this extinction 'intermediate' (between quenching and blowoff); stored as quenched."),
    ("GEL-4", "SoFIE-GEL", "case 4 (1409C)", "PMMA", "PMMA sphere 4 cm", "sphere", 40.0, "concurrent",
     0.44, 20.77, round(1.03 * KPA_PER_ATM, 1), "quenched", "Extinction mode: quenching", GEL, ""),
    ("GEL-5", "SoFIE-GEL", "case 5 (1410C)", "PMMA", "PMMA sphere 4 cm", "sphere", 40.0, "concurrent",
     49.68, 14.37, round(1.07 * KPA_PER_ATM, 1), "blowoff", "Extinction mode: blowoff", GEL, ""),
]


def bass2_rows() -> pd.DataFrame:
    b = pd.read_csv(DATA / "bass2" / "bass2_test_points.csv", dtype=str, keep_default_na=False)
    is_bass = b["test_no"].str.startswith("BASS ")          # four BASS (not BASS-II) rows of Table 7.1
    material = b["material_class"].where(~b["material_class"].str.startswith("other"), "other")
    out = pd.DataFrame({
        "point_id": "B2-" + b["point_id"],
        "investigation_id": is_bass.map({True: "BASS", False: "BASS-II"}),
        "group_id": [("BASS" if bb else f"BASS-II / {pi}") for bb, pi in zip(is_bass, b["pi"])],
        "test_no": b["test_no"],
        "material_class": material,
        "material_verbatim": b["material_verbatim"],
        "geometry": b["geometry"],
        "thickness_mm": pd.to_numeric(b["thickness_or_diameter_mm"], errors="coerce"),
        "flow_direction": b["flow_direction"],
        "flow_cm_s": pd.to_numeric(b["flow_cm_s"], errors="coerce"),
        "flow_value_kind": b["flow_value_kind"],
        "o2_pct": pd.to_numeric(b["o2_pct"], errors="coerce"),
        "o2_final_pct": pd.to_numeric(b["o2_final_pct"], errors="coerce"),
        "o2_is_ambient": True,
        "pressure_kPa": 101.3,
        "pressure_basis": BASS2_PRESSURE_BASIS,
        "gravity_g": 0.0,
        "outcome": b["outcome"],
        "outcome_quote": b["outcome_quote"],
        "source_ref": "NASA/TM-20210011385, " + b["source_table"] + " (PDF p. " + b["pdf_page"] + ")",
        "source_url": TM_URL,
        "verification": "verified_live",
        "notes": b["notes"],
    })
    return out


def extra_rows() -> pd.DataFrame:
    rows = []
    for (pid, inv, test, mclass, mat, geom, thick, direction, flow, o2, kpa, outcome, quote, src, notes) in EXTRA:
        rows.append(dict(point_id=pid, investigation_id=inv, group_id=inv, test_no=test, material_class=mclass,
                         material_verbatim=mat, geometry=geom, thickness_mm=thick, flow_direction=direction,
                         flow_cm_s=flow, flow_value_kind="source_table", o2_pct=o2, o2_is_ambient=True,
                         pressure_kPa=kpa, pressure_basis=src[0], gravity_g=0.0, outcome=outcome,
                         outcome_quote=quote, source_ref=src[0], source_url=src[1], verification="verified_live",
                         notes=notes))
    return pd.DataFrame(rows)


def main() -> int:
    df = pd.concat([bass2_rows(), extra_rows()], ignore_index=True)
    df["sustained"] = df["outcome"].map({"sustained": 1, "quenched": 0, "blowoff": 0, "no_ignition": 0})
    # Oxygen falls during a long burn in a sealed glovebox. A flame that quenched or blew off did so
    # at the end-of-test oxygen, which is also what the memo plots on its flammability boundary
    # (Fig. 6.9: "Final O2 concentration"). Sustained and no-ignition points keep the initial value.
    went_out = df["outcome"].isin(["quenched", "blowoff"]) & df["o2_final_pct"].notna()
    df["o2_at_outcome_pct"] = df["o2_final_pct"].where(went_out, df["o2_pct"])
    df["o2_at_outcome_basis"] = went_out.map({True: "final O2 reading of the test", False: "initial O2 of the test"})
    df["usable_for_model"] = (df["sustained"].notna() & df["o2_pct"].notna() & df["pressure_kPa"].notna()
                              & df["flow_cm_s"].notna() & (df["verification"] != "unverified"))
    df["sustained"] = df["sustained"].astype("Int64")
    assert df["point_id"].is_unique
    df[COLUMNS].to_csv(DATA / "solid_test_points.csv", index=False, lineterminator="\n")
    u = df[df["usable_for_model"]]
    print(f"wrote solid_test_points.csv: {len(df)} points, {len(u)} usable for the model")
    print(pd.crosstab(u["group_id"], u["outcome"]))
    print(pd.crosstab(u["material_class"], u["sustained"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
