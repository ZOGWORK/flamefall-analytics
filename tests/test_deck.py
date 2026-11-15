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
C_NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}


def chart_text(chart) -> str:
    """Categories, series names and every plotted value. For a scatter, the x values too."""
    plot = chart.plots[0]
    parts = [str(c) for c in plot.categories] + [s.name for s in plot.series]
    for series in plot.series:
        xs = [v.text for v in series._element.findall(".//c:xVal//c:v", C_NS)]
        parts += xs + [str(v) for v in series.values]
    return "chart: " + " | ".join(parts)


def slide_texts(path: Path) -> list[list[str]]:
    """The text of every shape on every slide, in order, with each chart's data."""
    out = []
    for slide in pptx.Presentation(str(path)).slides:
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                texts.append(shape.text_frame.text)
            if getattr(shape, "has_chart", False) and shape.has_chart:
                texts.append(chart_text(shape.chart))
        out.append(texts)
    return out


def signature(path: Path) -> list[list[tuple]]:
    """Where every shape sits, what colour it is, and how every run of text is set: the look of the deck."""
    out = []
    for slide in pptx.Presentation(str(path)).slides:
        shapes = []
        for shape in slide.shapes:
            fill = ""
            if getattr(shape, "fill", None) is not None and shape.fill.type == 1:          # solid
                fill = str(shape.fill.fore_color.rgb)
            runs = ()
            if shape.has_text_frame:
                runs = tuple((r.text, r.font.name, r.font.size, r.font.bold, str(r.font.color.rgb) if r.font.color.type else "")
                             for para in shape.text_frame.paragraphs for r in para.runs)
            shapes.append((shape.name, shape.left, shape.top, shape.width, shape.height, fill, runs))
        out.append(shapes)
    return out


@pytest.fixture(scope="module")
def n() -> dict:
    return build_deck.numbers()


@pytest.fixture(scope="module")
def deck() -> list[list[str]]:
    assert DECK.exists(), "run `python scripts/build_deck.py`"
    return slide_texts(DECK)


def by_name(slide) -> dict:
    return {shape.name: shape for shape in slide.shapes}


def test_the_committed_deck_is_what_a_fresh_build_says(tmp_path, deck):
    """Text, chart data, speaker notes, and the position, colour and type of every shape."""
    fresh = build_deck.build(tmp_path / "deck.pptx")
    hint = "run `python scripts/build_deck.py` and commit the file"
    assert slide_texts(fresh) == deck, hint
    assert signature(fresh) == signature(DECK), hint
    notes = lambda path: [s.notes_slide.notes_text_frame.text for s in pptx.Presentation(str(path)).slides]   # noqa: E731
    assert notes(fresh) == notes(DECK), hint


def test_two_builds_from_the_same_data_are_the_same_file(tmp_path):
    a, b = build_deck.build(tmp_path / "a.pptx"), build_deck.build(tmp_path / "b.pptx")
    assert a.read_bytes() == b.read_bytes()
    core = zipfile.ZipFile(a).read("docProps/core.xml").decode("utf-8")
    assert "Team Flamefall Analytics" in core and "Steve Canny" not in core and "python-pptx" not in core


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
        2: [str(n["search_hits"]), f"{n['combustion_science']} of the {n['search_hits']} records are combustion science",
            f"adds {n['outside_search']} related investigations"],
        3: [str(n["n"]), f"Extinction {o['Extinction']}", f"{n['first']} to {n['last']}"],
        4: [pct(n["extinction_share"]), pct(m["extinction_share"]), f"{m['Extinction']} of {m['n']}", pct(h["extinction_share"]),
            f"{h['Extinction']} of {h['n']}", f"Extinction {m['Extinction']}", f"Extinction {h['Extinction']}"],
        5: [f"{c['indicated']} of {n['heptane_extinctions']}", n["cool_temp"], "as reported for gas cool flames"],
        6: [f"{n['auc_headline']:.2f}", f"({n['auc_cv']:.2f})", f"{pct(n['fpr'], 0)} false-positive rate",
            f"{n['fp']} of {n['fp'] + n['tn']} negatives", f"{n['model_rows']} OF {n['n']} TESTS"],
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
    # the scatter plots each fuel's share at each oxygen level it was tested at: x and y both
    scatter = next(t for t in deck[3] if t.startswith("chart: "))
    for fuel in ("Methanol", "Heptane"):
        for level, share in n["share_by_o2"][fuel]:
            assert f"{level:g}" in scatter.replace(".0 ", " ").split(" | ") or f"{level}" in scatter.split(" | "), (fuel, level)
            assert str(share) in scatter.split(" | "), (fuel, share)
    # the scenario example lists real tests, nearest first, and gives no probability for a solid
    for row in n["near"]:
        assert row["test"] in flat[5]
    assert [r["distance"] for r in n["near"]] == sorted(r["distance"] for r in n["near"])
    assert "NO PROBABILITY FOR A SOLID" in flat[5]


def test_the_confusion_matrix_has_each_count_in_its_own_cell(n):
    shapes = by_name(pptx.Presentation(str(DECK)).slides[5])
    cell = lambda name: shapes[name].text_frame.text                                       # noqa: E731
    assert shapes["Row 1"].text_frame.text == "flame went out" and shapes["Row 2"].text_frame.text == "flame did not go out"
    assert "goes out" in shapes["Column 1"].text_frame.text and "keeps burning" in shapes["Column 2"].text_frame.text
    assert (cell("Matrix cell 1.1"), cell("Matrix cell 1.2")) == (str(n["tp"]), str(n["fn"]))      # went out: called so, missed
    assert (cell("Matrix cell 2.1"), cell("Matrix cell 2.2")) == (str(n["fp"]), str(n["tn"]))      # did not: false alarm, right
    assert n["tp"] + n["fn"] + n["fp"] + n["tn"] == n["model_rows"] == n["n"] - len(n["model_left_out"])
    red = [name for name in ("Matrix cell 1.1", "Matrix cell 1.2", "Matrix cell 2.1", "Matrix cell 2.2")
           if str(shapes[name].fill.fore_color.rgb) == build_deck.RED]
    assert red == ["Matrix cell 2.1"]                                                      # only the false positives are red
    source = shapes["Source"].text_frame.text
    assert all(test in source for test in n["model_left_out"]) and n["model_left_out"] == ["FLEX-114"]


def test_the_last_slide_claims_only_what_the_data_supports(n):
    shapes = by_name(pptx.Presentation(str(DECK)).slides[6])
    source = shapes["Source"].text_frame.text
    assert n["solid_top_source"] in source and "ICES-2025-156" in source       # where the 31.9% test point is printed
    for needed in ("PSI Data Repository", "challenge brief", "SAME Final Report", "T'ien et al."):
        assert needed in source, needed
    panel = shapes["Panel label 2"].text_frame.text + "\n" + shapes["Not in the data"].text_frame.text
    assert "NEVER TESTED" not in panel.upper()         # LUCI has flown in simulated lunar gravity; its data is not in the repository
    assert "WHAT THE DATA DOES NOT HOLD" in panel and "lunar or Martian gravity" in panel


def test_the_waffle_has_one_cell_per_test_in_test_order(n):
    slide = pptx.Presentation(str(DECK)).slides[2]
    cells = [s for s in slide.shapes if s.name.startswith("Test ")]
    assert len(cells) == n["n"]
    assert [s.name for s in cells] == [f"Test {i + 1}: {outcome}" for i, outcome in enumerate(n["order"])]
    assert {s.name.split(": ")[1]: str(s.fill.fore_color.rgb) for s in cells} == {
        "Extinction": "EF4444", "Disruption": "A78BFA", "Completion": "22C55E"}     # red, violet, green: the same on every slide
    assert all(str(s.fill.fore_color.rgb) == build_deck.OUTCOME_COLOR[s.name.split(": ")[1]] for s in cells)
    assert len({(s.left, s.top) for s in cells}) == n["n"]                          # no two cells in the same place


def test_no_verdict_wording_no_images_and_only_the_deck_fonts(deck):
    prs = pptx.Presentation(str(DECK))
    notes = [s.notes_slide.notes_text_frame.text for s in prs.slides]
    for i, texts in enumerate(deck, start=1):
        for t in texts + [notes[i - 1]]:
            assert not VERDICT.search(t), f"slide {i}: {t[:80]}"
            assert "NET late 2026" not in t and "CFI-G up to 85" not in t
    with zipfile.ZipFile(DECK) as z:
        assert not [name for name in z.namelist() if name.startswith("ppt/media/")], "the deck holds no image or logo"
        assert not any(b"<p:transition" in z.read(name) or b"<p:timing" in z.read(name)
                       for name in z.namelist() if name.startswith("ppt/slides/slide"))       # no transitions or animations
    fonts = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            assert shape.shape_type != pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    fonts |= {run.font.name for run in para.runs}
    assert fonts == {build_deck.HEAD, build_deck.BODY, build_deck.MONO} == {"Space Grotesk", "IBM Plex Sans", "JetBrains Mono"}
    assert str(prs.slides[0].background.fill.fore_color.rgb) == build_deck.BG == "0B0F14"


def test_the_biggest_type_on_every_slide_is_a_number():
    for i, slide in enumerate(pptx.Presentation(str(DECK)).slides, start=1):
        runs = [(r.font.size, r.text) for s in slide.shapes if s.has_text_frame for para in s.text_frame.paragraphs for r in para.runs]
        size, biggest = max(runs, key=lambda x: x[0])
        assert re.fullmatch(r"[\d.,%]+( of \d+)?", biggest.strip()), f"slide {i}: {biggest!r} at {size.pt} pt"


def test_no_slide_is_a_wall_of_text(deck):
    """A word budget over everything a reader has to read: all text except the source line, the
    small upper-case labels, the slide number and bare numbers. Counted from the file, whatever a
    shape is called, so adding a paragraph to a slide fails here."""
    budget, longest = 95, 28
    for i, texts in enumerate(deck, start=1):
        read = [t for t in texts if not t.startswith(("Source: ", "chart: ")) and not re.fullmatch(r"\d / 7", t)
                and t != t.upper() and re.search(r"[A-Za-z]{3}", t)]
        words = [len(t.split()) for t in read]
        assert sum(words) <= budget, f"slide {i}: {sum(words)} words"
        assert max(words) <= longest, f"slide {i}: {max(read, key=lambda t: len(t.split()))}"
        sentences = [t for t in read if len(t.split()) >= 9]
        assert len(sentences) <= 5, f"slide {i}: {len(sentences)} full lines of text"
