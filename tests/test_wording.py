"""Wording rules that the science depends on, checked across every file whose text reaches a reader."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER_FACING = (
    sorted((ROOT / "flamefall").glob("*.py"))
    + [ROOT / "data" / "evidence.json", ROOT / "data" / "investigations_curated.json", ROOT / "README.md"]
    + sorted((ROOT / "data" / "models").glob("*.json"))
    + [ROOT / "data" / "panels.json"]
    + sorted((ROOT / "web" / "src" / "data").glob("*.json"))          # what the web app reads
    + sorted(p for ext in ("*.ts", "*.tsx") for p in (ROOT / "web" / "src").rglob(ext))
    + sorted((ROOT / "docs").glob("*.md"))
)
VERDICT = re.compile(r"\b(safe|unsafe|certified|certification|certify)\b", re.I)
EIGHTY_FIVE = re.compile(r"\b85\s?%|\b0\.85\b|\b85 percent")
OXYGEN = re.compile(r"oxygen|\bO2\b|XO2", re.I)
QUALIFIER = re.compile(r"burner|inverse", re.I)
MIXTURE = re.compile(r"^(\d(?:\.\d+)?(?:/\d(?:\.\d+)?)+) ([A-Za-z0-9]+(?:/[A-Za-z0-9]+)+)$")


def says_85_percent_oxygen(text: str) -> bool:
    """True when a text gives 85% as an oxygen value.

    A gas mixture written as "0.15/0.85 O2/N2" pairs values with gases by position, so there the
    oxygen value is read from its own position and a nitrogen fraction of 0.85 is not a match.
    """
    mixture = MIXTURE.match(text.strip())
    if mixture:
        fractions = dict(zip(mixture.group(2).split("/"), mixture.group(1).split("/")))
        return float(fractions.get("O2", 0)) == 0.85
    return bool(EIGHTY_FIVE.search(text) and OXYGEN.search(text))


def strings(node):
    """Every text value inside a parsed JSON document."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


def lines(path: Path):
    """The units a rule is applied to: lines of a text file, or each text value of a JSON file.

    A JSON file may be written on a single line, so its lines mean nothing; its values do.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        for number, value in enumerate(strings(json.loads(text)), 1):
            yield number, value
    else:
        for number, line in enumerate(text.splitlines(), 1):
            yield number, line


def test_no_verdict_wording_anywhere():
    """Nothing may be called safe or certified. ('Safety' as a field of study is fine.)"""
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:120]}" for p in READER_FACING for n, line in lines(p)
            if VERDICT.search(line)]
    assert not hits, "\n".join(hits)


def test_every_85_percent_oxygen_value_is_labelled_as_a_burner_feed():
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:140]}" for p in READER_FACING for n, line in lines(p)
            if says_85_percent_oxygen(line) and not QUALIFIER.search(line)]
    assert not hits, "\n".join(hits)


def test_the_85_percent_rule_reads_gas_mixture_notation_by_position():
    assert says_85_percent_oxygen("tested at 85% O2")
    assert says_85_percent_oxygen("burner oxygen mole fraction of 0.85")
    assert not says_85_percent_oxygen("0.15/0.85 O2/N2")              # 0.85 is the nitrogen fraction
    assert says_85_percent_oxygen("0.85/0.15 O2/N2")
    assert not says_85_percent_oxygen("85% of tests")


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
    """No logo, insignia or mission-patch image is referenced anywhere."""
    for p in READER_FACING:
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"<img[^>]+(nasa|meatball|insignia|patch)", text, re.I), p.name
        assert not re.search(r"\.(png|jpg|jpeg|svg|gif)[\"')]", text, re.I), p.name
