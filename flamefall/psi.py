"""Read-only access to the PSI Data Repository snapshot in data/psi/ (see scripts/fetch_psi.py).

The snapshot is the official catalogue: what the PSI search for "combustion" returns,
each record's own metadata, and every per-test "Experimental table" CSV PSI attaches.
PSI releases these records under CC0-1.0.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

PSI_DIR = Path(__file__).resolve().parents[1] / "data" / "psi"
TABLES = PSI_DIR / "experimental_tables"
SEARCH_URL = "https://psi.nasa.gov/physci/repo/search?q=combustion"
COMBUSTION_AREA = "Combustion Science"


def record_url(psi_id: str) -> str:
    return f"https://psi.nasa.gov/physci/repo/data/investigations/{psi_id}"


def fix_text(text: object) -> str:
    """Repair U+FFFD characters that PSI's API returns in place of dashes, quotes and apostrophes.

    Display only: the files in data/psi/ keep PSI's bytes unchanged.
    """
    if text is None:
        return ""
    s = str(text)
    if "�" not in s:
        return s.strip()
    s = re.sub(r"(?<=\w)�(?=(s|re|t|ll|ve|d|m)\b)", "'", s)      # you're, PI's
    s = re.sub(r"(?<=\w)�(?=\w)", "-", s)                          # BASS-II
    s = re.sub(r"(?<=\s)�(?=\w)|^�(?=\w)", '"', s)            # opening quote
    s = re.sub(r"(?<=[\w.,!?])�(?=[\s.,;:)]|$)", '"', s)           # closing quote
    return s.replace("�", "-").strip()


@lru_cache(maxsize=1)
def snapshot() -> dict:
    return json.loads((PSI_DIR / "SNAPSHOT.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_search() -> pd.DataFrame:
    """The search hits for "combustion", in PSI's relevance order."""
    hits = json.loads((PSI_DIR / "search_combustion.json").read_text(encoding="utf-8"))
    rows = []
    for h in hits:
        rows.append({
            "rank": h["rank"],
            "psi_id": h["Accession"],
            "acronym": fix_text(h.get("Acronym")),
            "title": fix_text(h.get("Title")),
            "research_area": fix_text(h.get("Research Area")),
            "sub_research_area": fix_text(h.get("SubResearch Area")),
            "project_type": fix_text(h.get("Project Type")),
            "flight_platform": fix_text(h.get("Flight Platform")),
            "hardware": fix_text(h.get("Experiment Hardware")),
            "keywords": fix_text(h.get("Keywords")),
        })
    df = pd.DataFrame(rows)
    df["is_combustion_science"] = df["research_area"].str.lower() == COMBUSTION_AREA.lower()
    return df


@lru_cache(maxsize=64)
def load_record(psi_id: str) -> dict:
    return json.loads((PSI_DIR / "records" / f"{psi_id}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=64)
def load_files(psi_id: str) -> dict:
    return json.loads((PSI_DIR / "files" / f"{psi_id}.json").read_text(encoding="utf-8"))


def table_names(psi_id: str | None = None) -> list[str]:
    names = sorted(p.name for p in TABLES.glob("*.csv"))
    return [n for n in names if psi_id is None or n.startswith(f"{psi_id}_")]


@lru_cache(maxsize=64)
def read_table(filename: str) -> pd.DataFrame:
    """An experimental table exactly as PSI publishes it: every cell a string, blanks as ''."""
    path = TABLES / filename
    for enc in ("utf-8-sig", "cp1252"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=enc, keep_default_na=False)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"cannot decode {filename}")
    df.columns = [c.strip() for c in df.columns]
    # Some PSI files carry hundreds of comma-only padding rows after the last test (861 of the 1,015
    # lines in the CFI-G inverse-flame table). They are not tests and are dropped on read.
    blank = (df.apply(lambda col: col.str.strip()) == "").all(axis=1)
    return df[~blank].reset_index(drop=True)


def distinct_rows(table: pd.DataFrame) -> pd.DataFrame:
    """The table without exact repeats of an earlier row.

    A few PSI files repeat a block of rows (8 in the CFI table, 34 in SPICE, 8 in E-FIELD Flames).
    Counting or summing over the raw rows would count those tests twice.
    """
    return table.drop_duplicates().reset_index(drop=True)


def duplicate_count(table: pd.DataFrame) -> int:
    return int(table.duplicated().sum())


def numeric(series: pd.Series) -> pd.Series:
    """Parse a PSI table column as numbers; anything that is not a plain number becomes NaN."""
    return pd.to_numeric(series.astype(str).str.strip(), errors="coerce")


def summary() -> dict:
    s = load_search()
    return {
        "search_hits": int(len(s)),
        "combustion_science": int(s["is_combustion_science"].sum()),
        "other_areas": s.loc[~s["is_combustion_science"], ["psi_id", "title", "research_area"]].to_dict("records"),
        "with_experimental_table": int(sum(1 for i in s["psi_id"] if table_names(i))),
        "tables": len(table_names()),
        "retrieved": snapshot()["retrieved_utc"],
    }
