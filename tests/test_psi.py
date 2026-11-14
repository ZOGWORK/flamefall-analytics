"""The PSI snapshot: what the official repository returns, and how it cross-checks our data."""
from __future__ import annotations

import pandas as pd
import pytest

from flamefall import flex, psi


def test_search_returns_26_hits_24_combustion_science():
    s = psi.summary()
    assert s["search_hits"] == 26
    assert s["combustion_science"] == 24
    assert sorted(r["psi_id"] for r in s["other_areas"]) == ["PSI-108", "PSI-181"]


def test_core_investigations_present_with_ids():
    ids = dict(zip(psi.load_search()["acronym"], psi.load_search()["psi_id"]))
    expect = {"FLEX": "PSI-69", "FLEX-2": "PSI-68", "BASS": "PSI-26", "BASS-II": "PSI-25", "SAME": "PSI-102",
              "SAME-R": "PSI-101", "SAFFIRE-I": "PSI-98", "SAFFIRE-II": "PSI-99", "SAFFIRE-III": "PSI-100",
              "SPICE": "PSI-107", "SLICE": "PSI-106", "ACME CFI-G": "PSI-159", "ACME/Flame Design": "PSI-10",
              "ACME CLD Flame": "PSI-21", "ACME BRE": "PSI-20", "ACME E-FIELD Flames": "PSI-22",
              "ACME s-Flame": "PSI-23", "CFI": "PSI-39"}
    for acronym, psi_id in expect.items():
        assert ids.get(acronym) == psi_id, acronym


def test_every_record_and_table_is_on_disk():
    for psi_id in psi.load_search()["psi_id"]:
        rec = psi.load_record(psi_id)
        assert rec["accession"] == psi_id
        assert psi.load_files(psi_id)["psi_id"] == psi_id
    assert len(psi.table_names()) == 25


def test_snapshot_carries_no_contact_details():
    for path in (psi.PSI_DIR / "records").glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert '"email"' not in text and '"phone"' not in text, path.name


def test_fix_text_repairs_replacement_characters():
    assert psi.fix_text("BASS�II tests") == "BASS-II tests"
    assert psi.fix_text("If you�re far from Earth") == "If you're far from Earth"
    assert psi.fix_text("real-time �lab partner� operations") == 'real-time "lab partner" operations'
    assert "�" not in psi.fix_text("a � b")


def test_psi_flex_table_matches_table_ix_value_for_value():
    """Third independent check of the core dataset: PSI's own FLEX experimental table.

    PSI numbers its rows 1..274 in sequence instead of using the FLEX test numbers, so rows are
    aligned on the CIR identifier and time, not on the number.
    """
    p = psi.read_table("PSI-69_Experimental table_FLEX.csv")
    p.columns = ["n", "cir", "date", "gmt", "fuel", "p", "o2", "n2", "co2", "he", "d0", "dext", "k", "bt", "end"]
    mine = flex.load_table_ix()
    assert len(p) == 274 and p["n"].astype(int).tolist() == list(range(1, 275))

    def num(v) -> float | None:
        v = str(v).strip().lstrip("~")
        return None if v in ("", "-", "–", "\x96", "nan") else float(v)

    pool: dict[tuple, list] = {}
    for _, r in mine.iterrows():
        pool.setdefault((r["cir_id"], "" if pd.isna(r["gmt"]) else r["gmt"]), []).append(r)
    used, diffs = set(), []
    pairs = [("pressure_mmhg", "p"), ("o2", "o2"), ("n2", "n2"), ("co2", "co2"), ("he", "he"), ("d0_mm", "d0"),
             ("extinction_diameter_mm", "dext"), ("burning_rate_mm2_s", "k"), ("burn_time_s", "bt")]
    for _, r in p.iterrows():
        cands = [c for c in pool.get((r["cir"].strip(), r["gmt"].strip()), []) if c["test_no"] not in used]
        assert cands, f"PSI row {r['n']} has no Table IX partner"
        c = cands[0]
        used.add(c["test_no"])
        assert c["fuel"] == r["fuel"] and c["outcome"] == r["end"]
        for mine_col, psi_col in pairs:
            a = None if pd.isna(c[mine_col]) else float(c[mine_col])
            if a != num(r[psi_col]):
                diffs.append((int(c["test_no"]), mine_col, a, r[psi_col]))
    # the single difference is the documented cleaning of FLEX-114 (0 mmHg -> missing)
    assert diffs == [(114, "pressure_mmhg", None, "0")]
    assert sorted(set(mine["test_no"]) - used) == [216, 230]      # in Table IX, absent from PSI's table


def test_inverse_flame_oxygen_is_a_burner_feed_not_an_ambient():
    """85 % O2 exists only as the burner stream of inverse flames; chamber ambients stop at 40 %."""
    fd_inv = psi.numeric(psi.read_table("PSI-10_Experimental table_Flame Design_Inverse Flame.csv")["XO2"])
    fd_norm = psi.numeric(psi.read_table("PSI-10_Experimental table_Flame Design_Normal Flame.csv")["XO2 (init)"])
    cfi_inv = psi.numeric(psi.read_table("PSI-159_Experimental table_CFI-G_Inverse Flames.csv")["XO2"])
    cfi_norm = psi.numeric(psi.read_table("PSI-159_Experimental table_CFI-G_Normal Flames.csv")["XO2 before test"])
    assert fd_inv.max() == pytest.approx(0.85, abs=1e-3) and cfi_inv.max() == pytest.approx(0.85, abs=1e-3)
    assert fd_norm.max() == pytest.approx(0.40, abs=1e-3) and cfi_norm.max() == pytest.approx(0.40, abs=1e-3)


def test_cfig_cool_flame_rows():
    t = psi.read_table("PSI-159_Experimental table_CFI-G_Normal Flames.csv")
    marked = t[t["Cool flame?"] != ""]
    yes = marked[marked["Cool flame?"].str.startswith("yes")]
    assert len(t) == 179 and len(marked) == 8 and len(yes) == 7
    assert set(yes["Fuel"]) == {"30% butane"}
    assert psi.numeric(yes["XO2 before test"]).between(0.389, 0.400).all()
    assert (psi.numeric(yes["approx p (bar)"]) == 2.0266).all()


def test_bass2_psi_table_oxygen_range():
    t = psi.read_table("PSI-25_Experimental table_BASS-II.csv")
    o2 = psi.numeric(t["Calibrated  initial O2 % by vol"])
    assert len(t) == 129 and o2.min() == 13.6 and o2.max() == 22.2
