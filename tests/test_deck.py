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


A_COLOUR = "{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr"


def signature(path: Path) -> list[list[tuple]]:
    """The look of the deck: for every shape its kind, name, place, size, every colour its XML names
    (fill, outline, text, and for a chart each series and point), and how every run of text is set."""
    out = []
    for slide in pptx.Presentation(str(path)).slides:
        shapes = []
        for shape in slide.shapes:
            colours = tuple(el.get("val") for el in shape._element.iter(A_COLOUR))
            if getattr(shape, "has_chart", False) and shape.has_chart:
                colours += tuple(el.get("val") for el in shape.chart._chartSpace.iter(A_COLOUR))
            runs = ()
            if shape.has_text_frame:
                runs = tuple((r.text, r.font.name, r.font.size, r.font.bold) for para in shape.text_frame.paragraphs for r in para.runs)
            shapes.append((str(shape.shape_type), shape.name, shape.left, shape.top, shape.width, shape.height, colours, runs))
        out.append(shapes)
    return out


def scatter_points(chart) -> dict[str, list[tuple[float, float]]]:
    """Each series of a scatter chart as its own list of (x, y) points, in the order they are stored."""
    out = {}
    for series in chart.plots[0].series:
        xs = [float(v.text) for v in series._element.findall(".//c:xVal//c:v", C_NS)]
        out[series.name] = list(zip(xs, [float(v) for v in series.values]))
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
    """Text, chart data and speaker notes, and for every shape its kind, place, size, colours and type setting."""
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
    for path in (a, DECK):                                                         # the file describes itself, not a template
        app = zipfile.ZipFile(path).read("docProps/app.xml").decode("utf-8")
        assert app == build_deck.APP_PROPERTIES
        assert "<Slides>7</Slides><Notes>7</Notes>" in app and "Widescreen" in app
        assert not any(left in app for left in ("Macintosh", "4:3", "Office Theme", "<Words>", "AppVersion"))
    with zipfile.ZipFile(a) as z:
        assert {(i.date_time, i.create_system, i.external_attr) for i in z.infolist()} == {
            (build_deck.FIXED_DATE, build_deck.ZIP_SYSTEM, build_deck.ZIP_ATTR)}
        books = [name for name in z.namelist() if name.startswith("ppt/embeddings/") and name.endswith(".xlsx")]
        assert books                                                               # each chart's workbook carries the fixed date too
        for name in books:
            import io

            with zipfile.ZipFile(io.BytesIO(z.read(name))) as book:
                assert {i.date_time for i in book.infolist()} == {build_deck.FIXED_DATE}, name
                assert "2026-11-14T00:00:00Z" in book.read("docProps/core.xml").decode("utf-8"), name


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
        7: [f"{n['solid_top_o2']:.1f}%", f"{n['co2_and_he']} of {n['n']}", f"above {n['solid_top_o2']:.1f}% oxygen", f"below {n['smoke_nm']} nm"],
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
    # the scatter plots, per fuel, exactly the share at each oxygen level that fuel was tested at
    chart = next(s.chart for s in pptx.Presentation(str(DECK)).slides[3].shapes if getattr(s, "has_chart", False) and s.has_chart)
    points = scatter_points(chart)
    assert set(points) == {"Methanol", "n-Heptane"}
    for label, fuel in (("Methanol", "Methanol"), ("n-Heptane", "Heptane")):
        assert len(points[label]) == len(n["share_by_o2"][fuel]), fuel
        for (x, y), (level, share) in zip(points[label], n["share_by_o2"][fuel]):
            assert (x, y) == pytest.approx((level, share)), (fuel, level)
        assert len(points[label]) == len({x for x, _ in points[label]}) >= 10, fuel          # one point per level, no repeats
    # the scenario example lists real tests, nearest first, and gives no probability for a solid
    for row in n["near"]:
        assert row["test"] in flat[5]
    assert [r["distance"] for r in n["near"]] == sorted(r["distance"] for r in n["near"])
    notes = pptx.Presentation(str(DECK)).slides[5].notes_slide.notes_text_frame.text
    assert "the nearest real tests and no probability" in notes
    table = " ".join(t for t in deck[5] if "sustained" in t or "BASS" in t)
    assert table and not re.search(r"\d+(\.\d+)?%", table)                       # no chance is printed for the solid


def test_the_confusion_matrix_has_each_count_in_its_own_cell(n):
    slide = pptx.Presentation(str(DECK)).slides[5]
    shapes = by_name(slide)
    cell = lambda name: shapes[name].text_frame.text                                       # noqa: E731
    # the rows are named by outcome: the model's second class holds Disruption and Completion, and the slide says so
    assert shapes["Row 1"].text_frame.text == "Extinction" and shapes["Row 2"].text_frame.text == "Disruption or Completion"
    assert shapes["Column 1"].text_frame.text == "called “Extinction”" and shapes["Column 2"].text_frame.text == "called “not Extinction”"
    outcomes = build_deck.flex.load_flex()["outcome"].value_counts()
    assert n["fp"] + n["tn"] == outcomes["Disruption"] + outcomes["Completion"]            # FLEX-114, left out, is an Extinction
    assert n["tp"] + n["fn"] == outcomes["Extinction"] - len(n["model_left_out"])
    assert "Disruption and Completion" in slide.notes_slide.notes_text_frame.text
    assert (cell("Matrix cell 1.1"), cell("Matrix cell 1.2")) == (str(n["tp"]), str(n["fn"]))      # went out: called so, missed
    assert (cell("Matrix cell 2.1"), cell("Matrix cell 2.2")) == (str(n["fp"]), str(n["tn"]))      # did not: false alarm, right
    assert n["tp"] + n["fn"] + n["fp"] + n["tn"] == n["model_rows"] == n["n"] - len(n["model_left_out"])
    red = [name for name in ("Matrix cell 1.1", "Matrix cell 1.2", "Matrix cell 2.1", "Matrix cell 2.2")
           if str(shapes[name].fill.fore_color.rgb) == build_deck.RED]
    assert red == ["Matrix cell 2.1"]                                                      # only the false positives are red
    source = shapes["Source"].text_frame.text
    assert all(test in source for test in n["model_left_out"]) and n["model_left_out"] == ["FLEX-114"]
    assert "printed as 0 mmHg and treated as missing" in source                 # what the source shows, not "no pressure"
    assert f"{n['report']}, Table IX" in source                                 # the table the 275 of 276 tests come from
    slide_text = "\n".join(s.text_frame.text for s in slide.shapes if s.has_text_frame)   # the cells of one row share a name
    for row in n["near"]:                                                       # each nearest test shows its flow direction,
        assert f"{row['flow']:g} cm/s {row['direction']}" in slide_text         # which the distance does not compare
    assert "BY OXYGEN, PRESSURE AND FLOW SPEED" in slide_text


def test_the_last_slide_claims_only_what_the_data_supports(n):
    shapes = by_name(pptx.Presentation(str(DECK)).slides[6])
    source = shapes["Source"].text_frame.text
    assert n["solid_top_source"] in source and "ICES-2025-156" in source       # where the 31.9% test point is printed
    for needed in ("PSI Data Repository", "challenge brief", "SAME Final Report", "T'ien et al."):
        assert needed in source, needed
    assert "Appendix B" in source                                               # where the cool-flame evidence is
    panel = shapes["Panel label 2"].text_frame.text + "\n" + shapes["Where it stops"].text_frame.text
    # Partial-gravity combustion has been tested: drop towers, parabolic flights and one suborbital
    # flight, all in the project's own evidence. What is true is that the repository holds none.
    from flamefall import catalogue as cat

    assert (cat.load_evidence()["evidence_class"] == "partial_g").sum() >= 5
    assert "NEVER TESTED" not in panel.upper() and "THE DATA DOES NOT HOLD" not in panel.upper()
    # the label scopes the lines to this console's data; the first names the PSI repository, the last the FLEX tests
    assert "WHERE THIS CONSOLE'S DATA STOPS" in panel
    assert "lunar or Martian gravity: no data in the PSI repository" in panel and n["partial_g"] == 0
    solid = cat.load_solid_points()
    assert f"solid materials: no test point above {n['solid_top_o2']:.1f}% oxygen" in panel       # the same number as the hero
    assert solid["o2_at_outcome_pct"].max() == solid["o2_pct"].max() == n["solid_top_o2"]
    assert "CO2 with helium: never in one FLEX test" in panel and n["co2_and_he"] == 0
    assert f"{n['solid_limit']:g}% oxygen" not in panel                                           # one study's range is not a ceiling
    assert "in the PSI repository" in shapes["Hero number 1 caption"].text_frame.text


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
    """A word budget over everything on the slide a reader has to read: every text box and shape
    except the source line, the slide number and bare numbers (the words inside a chart, its category
    names and legend, are not counted). Labels count, whatever their letter case, and so does
    anything added later, whatever its shape is called. The limits are round ceilings, not
    the deck's own figures: a slide may carry at most 120 words, no single piece of text more than
    22, and at most five pieces of nine words or more (a headline, the hero captions and one line).
    A piece is one line as written: three lines in one box are three pieces."""
    for i, texts in enumerate(deck, start=1):
        read = [line for t in texts if not t.startswith(("Source: ", "chart: ")) and not re.fullmatch(r"\d / 7", t)
                for line in t.split("\n") if re.search(r"[A-Za-z]{3}", line)]
        words = [len(re.findall(r"\S*[A-Za-z0-9]\S*", t)) for t in read]              # a separator dot is not a word
        assert sum(words) <= 120, f"slide {i}: {sum(words)} words"
        assert max(words) <= 22, f"slide {i}: {read[words.index(max(words))]}"
        assert sum(1 for w in words if w >= 9) <= 5, f"slide {i}: too many full lines of text"
