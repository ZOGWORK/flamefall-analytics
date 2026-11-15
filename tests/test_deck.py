"""The PowerPoint deck: seven slides, every number from the data, a source on every slide."""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pytest

pptx = pytest.importorskip("pptx")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_deck  # noqa: E402

DECK = ROOT / "docs" / "Flamefall-Analytics-deck.pptx"
VERDICT = re.compile(r"\b(safe|unsafe|certified|certification|certify)\b", re.I)


def slide_texts(path: Path) -> list[list[str]]:
    """The text of every shape on every slide, in order; chart categories and series names included."""
    out = []
    for slide in pptx.Presentation(str(path)).slides:
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                texts.append(shape.text_frame.text)
            if getattr(shape, "has_chart", False) and shape.has_chart:
                plot = shape.chart.plots[0]
                texts.append("chart: " + " | ".join([str(c) for c in plot.categories] + [s.name for s in plot.series]
                                                    + [str(v) for s in plot.series for v in s.values]))
        out.append(texts)
    return out


@pytest.fixture(scope="module")
def n() -> dict:
    return build_deck.numbers()


@pytest.fixture(scope="module")
def deck() -> list[list[str]]:
    assert DECK.exists(), "run `python scripts/build_deck.py`"
    return slide_texts(DECK)


def test_the_committed_deck_is_what_a_fresh_build_says(tmp_path, deck):
    fresh = build_deck.build(tmp_path / "deck.pptx")
    assert slide_texts(fresh) == deck, "run `python scripts/build_deck.py` and commit the file"
    notes = lambda path: [s.notes_slide.notes_text_frame.text for s in pptx.Presentation(str(path)).slides]   # noqa: E731
    assert notes(fresh) == notes(DECK)


def test_exactly_seven_slides_each_with_a_source_line_and_speaker_notes(deck):
    assert len(deck) == 7
    prs = pptx.Presentation(str(DECK))
    for i, (slide, texts) in enumerate(zip(prs.slides, deck), start=1):
        sources = [t for t in texts if t.startswith("Source: ")]
        assert len(sources) == 1 and len(sources[0]) > 25, f"slide {i}"
        assert f"{i} / 7" in texts, f"slide {i}"
        assert len(slide.notes_slide.notes_text_frame.text) > 80, f"slide {i} has no speaker notes"


def test_every_number_on_the_slides_is_the_one_in_the_data(n, deck):
    flat = ["\n".join(texts) for texts in deck]
    o, m, h, c = n["outcomes"], n["by_fuel"]["Methanol"], n["by_fuel"]["Heptane"], n["cool"]
    pct = build_deck.pct
    assert (n["n"], o["Extinction"], o["Disruption"], o["Completion"]) == (276, 186, 62, 28)       # the table itself
    expected = {
        1: [str(n["n"]), f"Extinction {o['Extinction']}", f"Disruption {o['Disruption']}", f"Completion {o['Completion']}"],
        2: [str(n["search_hits"]), f"{n['combustion_science']} of the {n['search_hits']} records are combustion science"],
        3: [str(n["n"]), f"Extinction {o['Extinction']}", f"{n['first']} to {n['last']}"],
        4: [pct(n["extinction_share"]), pct(m["extinction_share"]), f"{m['Extinction']} of {m['n']}", pct(h["extinction_share"]),
            f"{h['Extinction']} of {h['n']}", f"Extinction {m['Extinction']}", f"Extinction {h['Extinction']}"],
        5: [f"{c['indicated']} of {n['heptane_extinctions']}", n["cool_temp"]],
        6: [f"{n['auc_headline']:.2f}", f"({n['auc_cv']:.2f})", f"{pct(n['fpr'], 0)} false-positive rate",
            f"{n['fp']} of {n['fp'] + n['tn']} negatives", str(n["tp"]), str(n["fn"]), str(n["tn"])],
        7: [f"{n['solid_top_o2']:.1f}%", f"{n['co2_and_he']} of {n['n']}", f"above {n['solid_limit']:g}% oxygen", f"below {n['smoke_nm']} nm"],
    }
    for number, strings in expected.items():
        for s in strings:
            assert s in flat[number - 1], f"slide {number}: {s!r}"
    # the values the guidelines name, as the data has them
    assert pct(n["extinction_share"]) == "67.4%" and pct(m["extinction_share"]) == "80.3%" and pct(h["extinction_share"]) == "50.4%"
    assert (c["indicated"], c["not_indicated"], c["unclear"], c[""]) == (39, 8, 6, 7)
    assert f"{n['auc_headline']:.2f}" == "0.74" and f"{n['auc_cv']:.2f}" == "0.88" and (n["fp"], n["fp"] + n["tn"]) == (16, 90)
    assert n["partial_g"] == 0 and n["co2_and_he"] == 0 and f"{n['solid_top_o2']:.1f}" == "31.9"
    # charts carry the same counts
    assert "chart: " + " | ".join([k for k, _ in n["burned"]]) in flat[1]
    assert sum(v for _, v in n["burned"]) == n["search_hits"]
    assert f"| {c['indicated']}.0 | {c['not_indicated']}.0 | {c['unclear']}.0 | {c['']}.0" in flat[4]
    # the scenario example lists real tests, nearest first, and gives no probability for a solid
    for row in n["near"]:
        assert row["test"] in flat[5]
    assert [r["distance"] for r in n["near"]] == sorted(r["distance"] for r in n["near"])
    assert "no probability" in flat[5]


def test_the_waffle_has_one_cell_per_test_in_test_order(n):
    slide = pptx.Presentation(str(DECK)).slides[2]
    cells = [s.name for s in slide.shapes if s.name.startswith("Test ")]
    assert len(cells) == n["n"]
    assert cells == [f"Test {i + 1}: {outcome}" for i, outcome in enumerate(n["order"])]
    colour = {s.name.split(": ")[1]: str(s.fill.fore_color.rgb) for s in slide.shapes if s.name.startswith("Test ")}
    assert colour == build_deck.OUTCOME_COLOR                       # red extinction, violet disruption, green completion


def test_no_verdict_wording_no_images_and_only_the_deck_fonts(deck):
    prs = pptx.Presentation(str(DECK))
    notes = [s.notes_slide.notes_text_frame.text for s in prs.slides]
    for i, texts in enumerate(deck, start=1):
        for t in texts + [notes[i - 1]]:
            assert not VERDICT.search(t), f"slide {i}: {t[:80]}"
            assert "NET late 2026" not in t and "CFI-G up to 85" not in t
    with zipfile.ZipFile(DECK) as z:
        assert not [name for name in z.namelist() if name.startswith("ppt/media/")], "the deck holds no image or logo"
    fonts = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            assert shape.shape_type != pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    fonts |= {run.font.name for run in para.runs}
    assert fonts == {build_deck.HEAD, build_deck.BODY, build_deck.MONO}
    assert str(prs.slides[0].background.fill.fore_color.rgb) == build_deck.BG == "0B0F14"


def test_no_slide_is_a_wall_of_text(deck):
    """Outside the source line, labels and numbers, a slide carries at most three short lines."""
    prs = pptx.Presentation(str(DECK))
    prose_names = {"Title", "Subtitle", "One line", "Stakes", "What it is", "Method", "Why it matters", "What the model is",
                   "The honest line", "Last line", "Live link", "Team and link"}
    for i, slide in enumerate(prs.slides, start=1):
        prose = [s.text_frame.text for s in slide.shapes if s.has_text_frame and s.name in prose_names]
        assert 1 <= len(prose) <= 4, f"slide {i}: {len(prose)} lines of prose"
        assert all(len(t) <= 130 for t in prose), f"slide {i}: {max(prose, key=len)}"
        assert sum(len(t) for t in prose) <= 330, f"slide {i}"
