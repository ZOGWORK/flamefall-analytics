"""Wording rules that the science depends on, checked across every file a reader can see."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER_FACING = (
    sorted((ROOT / "views").glob("*.py")) + sorted((ROOT / "flamefall").glob("*.py"))
    + [ROOT / "app.py", ROOT / "data" / "evidence.json", ROOT / "data" / "investigations_curated.json",
       ROOT / "README.md"]
    + sorted((ROOT / "deck").glob("*.html")) + sorted((ROOT / "docs").glob("*.md"))
)
VERDICT = re.compile(r"\b(safe|unsafe|certified|certification|certify)\b", re.I)
EIGHTY_FIVE = re.compile(r"\b85\s?%|\b0\.85\b|\b85 percent")
OXYGEN = re.compile(r"oxygen|\bO2\b|XO2", re.I)
QUALIFIER = re.compile(r"burner|inverse", re.I)


def lines(path: Path):
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        yield number, line


def test_no_verdict_wording_anywhere():
    """Nothing may be called safe or certified. ('Safety' as a field of study is fine.)"""
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:120]}" for p in READER_FACING for n, line in lines(p)
            if VERDICT.search(line)]
    assert not hits, "\n".join(hits)


def test_every_85_percent_oxygen_value_is_labelled_as_a_burner_feed():
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:140]}" for p in READER_FACING for n, line in lines(p)
            if EIGHTY_FIVE.search(line) and OXYGEN.search(line) and not QUALIFIER.search(line)]
    assert not hits, "\n".join(hits)


def test_the_disconfirmed_phrase_is_absent():
    for p in READER_FACING:
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"CFI-G up to 85", text, re.I), p.name
        assert not re.search(r"NET late 2026", text, re.I), p.name      # stale launch date for the lunar experiment


def test_no_single_burning_rate_is_quoted_for_n_heptane():
    """0.39 mm2/s is n-decane and 0.378-0.398 is n-dodecane: neither may be attached to heptane."""
    for p in READER_FACING:
        for _, line in lines(p):
            if re.search(r"heptane", line, re.I):
                assert not re.search(r"\b0\.39\b|0\.378|0\.398", line), f"{p.name}: {line.strip()[:120]}"


def test_no_agency_marks_are_referenced():
    """No logo, insignia or mission-patch image is used anywhere in the app or the deck."""
    for p in READER_FACING:
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"<img[^>]+(nasa|meatball|insignia|patch)", text, re.I), p.name
        assert not re.search(r"\.(png|jpg|jpeg|svg|gif)[\"')]", text, re.I) or p.suffix == ".html", p.name
