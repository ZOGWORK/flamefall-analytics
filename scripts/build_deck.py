"""Build the seven-slide presentation as a PowerPoint file.

    python scripts/build_deck.py            # writes docs/Flamefall-Analytics-deck.pptx

Every number on every slide is read from the project's data files through the `flamefall`
package at build time. Nothing is typed in: change the data and the deck changes with it, and
`tests/test_deck.py` fails if the committed file no longer says what a fresh build says.

Design rules (docs/SUBMISSION.md and the deck guidelines): exactly seven slides; one idea per
slide; the biggest type is a number; at most three short lines of text besides the source line;
a source line on every slide; flat colour on a dark background; amber accent, cyan for data, red
for extinction, green for completion, violet for disruption; no logos, images or gradients.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flamefall import aggregates, flex  # noqa: E402
from flamefall import catalogue as cat  # noqa: E402

OUT = ROOT / "docs" / "Flamefall-Analytics-deck.pptx"
SITE = "flamefall-analytics.onrender.com"
SITE_URL = f"https://{SITE}"

HEAD, BODY, MONO = "Space Grotesk", "IBM Plex Sans", "JetBrains Mono"
BG, SURFACE, LINE = "0B0F14", "141B24", "263241"
TEXT, MUTED, DIM = "E6EDF3", "9AA7B5", "64717F"
AMBER, CYAN, RED, GREEN, VIOLET = "F59E0B", "22D3EE", "EF4444", "22C55E", "A78BFA"
OUTCOME_COLOR = {"Extinction": RED, "Disruption": VIOLET, "Completion": GREEN}
W, H = 13.333, 7.5
LEFT = 0.7


def rgb(hex_: str) -> RGBColor:
    return RGBColor.from_string(hex_)


# =============================================================================== the numbers

def numbers() -> dict:
    """Everything the slides print, computed from the data files."""
    s, c = flex.summary(), cat.counts()
    f = flex.load_flex()
    inv = cat.load_investigations()
    psi = inv[inv["in_psi_search"]]
    burned_label = {"gas": "Gas flames", "solid": "Solid materials", "model": "Modelling studies", "droplet": "Liquid droplets",
                    "smoke": "Smoke and aerosols", "not combustion": "Not combustion"}
    burned = psi["fuel_type"].value_counts()
    assert set(burned.index) <= set(burned_label), set(burned.index) - set(burned_label)
    ev = cat.load_evidence().set_index("id")
    cards = {n: json.loads((ROOT / "data" / "models" / f"{n}.json").read_text(encoding="utf-8"))
             for n in ("droplet_extinction", "droplet_cool_flame", "solid_sustained")}
    card = cards["droplet_extinction"]
    # the tests the model could not use, and why: checked here, so the slide's note cannot be wrong
    used = {row["row_id"] for row in card["training_rows"]}
    left_out = f[~f["test_id"].isin(used)]
    assert len(used) == card["n_rows"] and left_out["pressure_kpa"].isna().all(), left_out[["test_id", "pressure_kpa"]]
    assert left_out["notes"].str.contains("pressure printed as 0 mmHg in source; treated as missing", regex=False).all(), list(left_out["notes"])
    cy = card["metrics"]["confusion_at_youden"]
    solid = cat.load_solid_points()
    decided = solid[solid["outcome"] != "ambiguous"]
    top = decided.loc[decided["o2_at_outcome_pct"].idxmax()]
    gravity = [cat._num(g) for g in psi.loc[psi["status"] != "planned", "gravity_g"]]
    scenario = dict(material="PMMA", o2=21.0, pressure=101.3, flow=10.0)
    near = cat.nearest_solid(scenario["material"], scenario["o2"], scenario["pressure"], scenario["flow"], k=3)
    panels = json.loads((ROOT / "data" / "panels.json").read_text(encoding="utf-8"))
    cool_temp = ev.loc["cfig-press", "statement"]
    assert "600 to 1000 K" in cool_temp, cool_temp
    solid_limit = float(ev.loc["sofie-gel-envelope", "o2_max_pct"])
    assert solid_limit == float(ev.loc[ev["evidence_class"] == "solid", "o2_max_pct"].max()), "the widest solid range is no longer SoFIE-GEL's"
    assert top["outcome"] == "no_ignition" and float(top["o2_at_outcome_pct"]) < solid_limit, top
    return {
        "n": s["n"], "outcomes": s["outcomes"], "first": s["first_test"], "last": s["last_test"], "report": flex.REPORT,
        "extinction_share": s["extinction_share"], "by_fuel": s["by_fuel"],
        "order": list(f.sort_values("test_no")["outcome"]),
        "share_by_o2": {fuel: [(float(r["level"]), float(r["share"])) for r in
                               aggregates.share_by_level(f[f["fuel"] == fuel], "o2_pct").to_dict("records")]
                        for fuel in ("Methanol", "Heptane")},
        "cool": s["cool_flame"], "heptane_extinctions": s["heptane_extinctions"],
        "cool_temp": "600 to 1000 K", "cool_temp_source": ev.loc["cfig-press", "source_ref"],
        "co2_and_he": s["co2_and_he"],
        "search_hits": c["search_hits"], "combustion_science": c["combustion_science"], "retrieved": c["retrieved"][:10],
        "burned": [(burned_label[k], int(v)) for k, v in burned.items()],
        "auc_cv": card["metrics"]["roc_auc"], "auc_headline": card["headline_auc"], "headline_is": card["headline_is"],
        "fp": cy["fp"], "tn": cy["tn"], "tp": cy["tp"], "fn": cy["fn"], "fpr": cy["false_positive_rate"],
        "model_rows": card["n_rows"], "model_left_out": list(left_out["test_id"]),
        "n_models": len(cards), "failed_models": sum(1 for m in cards.values() if m["headline_auc"] < 0.6),
        "partial_g": sum(1 for g in gravity if g is not None and 0.05 < g < 0.5),
        "solid_top_o2": float(top["o2_at_outcome_pct"]), "solid_top_source": top["source_ref"].split(" (")[0],
        "solid_limit": solid_limit, "outside_search": c["outside_psi_search"],
        "scenario": scenario,
        "near": [dict(test=f"{r['investigation_id']} {r['test_no']}", o2=float(r["o2_at_outcome_pct"]), flow=float(r["flow_cm_s"]),
                      direction=r["flow_direction"], outcome=r["outcome"], distance=float(r["distance"])) for _, r in near.iterrows()],
        "near_source": sorted({r["source_ref"].split(" (")[0] for _, r in near.iterrows()}),
        "near_pressure_assumed": bool((~near["pressure_stated"]).any()),
        "smoke_nm": panels["smoke"]["threshold_nm"], "sub500": ev.loc["same1-sub500", "statement"],
        "blue_flame": panels["blue_flame_quote"]["quote"],
    }


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


# =============================================================================== drawing helpers

def text(slide, x, y, w, h, content, *, size=16, font=BODY, color=TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=None, name=None, link=None):
    """A text box. `content` is a string or a list of (string, {overrides}) runs; "\\n" starts a new paragraph."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    runs = [(content, {})] if isinstance(content, str) else content
    para = tf.paragraphs[0]
    first = True
    for chunk, over in runs:
        for i, part in enumerate(chunk.split("\n")):
            if i > 0:
                para = tf.add_paragraph()
                first = True
            if first:
                para.alignment = align
                if spacing:
                    para.line_spacing = spacing
                first = False
            if not part:
                continue
            run = para.add_run()
            run.text = part
            run.font.name = over.get("font", font)
            run.font.size = Pt(over.get("size", size))
            run.font.bold = over.get("bold", bold)
            run.font.color.rgb = rgb(over.get("color", color))
    if link:
        box.click_action.hyperlink.address = link
    return box


def rect(slide, x, y, w, h, fill, *, line=None, dash=False, name=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        shape.name = name
    shape.shadow.inherit = False
    if fill is None:
        shape.fill.background()
    else:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1)
        if dash:
            from pptx.enum.dml import MSO_LINE
            shape.line.dash_style = MSO_LINE.DASH
    return shape


def new_slide(prs, number: int, kicker: str, source: str, notes: str):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(BG)
    text(slide, LEFT, 0.42, 9.0, 0.3, kicker.upper(), size=11, font=MONO, color=AMBER, name="Kicker")
    text(slide, W - LEFT - 1.5, 0.42, 1.5, 0.3, f"{number} / 7", size=11, font=MONO, color=DIM, align=PP_ALIGN.RIGHT, name="Slide number")
    text(slide, LEFT, H - 0.72, W - 2 * LEFT, 0.42, [("Source: ", {"color": DIM}), (source, {})], size=10.5, color=MUTED,
         anchor=MSO_ANCHOR.BOTTOM, name="Source")
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def hero(slide, x, y, w, value: str, caption: str, *, size=120, color=AMBER, caption_w=None, name="Hero number"):
    height = size / 72 * 1.08
    text(slide, x, y, w, height, value, size=size, font=MONO, color=color, bold=True, name=name)
    text(slide, x, y + height + 0.05, caption_w or w, 0.9, caption, size=15, color=TEXT, name=f"{name} caption")
    return y + height + 0.05


def style_chart(chart, *, size=11):
    chart.font.name = BODY
    chart.font.size = Pt(size)
    chart.font.color.rgb = rgb(MUTED)
    chart.has_title = False


def quiet_axis(axis, *, gridlines=False, labels=True):
    axis.format.line.color.rgb = rgb(LINE)
    axis.has_major_gridlines = gridlines
    if gridlines:
        axis.major_gridlines.format.line.color.rgb = rgb(LINE)
        axis.major_gridlines.format.line.width = Pt(0.5)
    axis.tick_labels.font.size = Pt(11)
    axis.tick_labels.font.color.rgb = rgb(MUTED)
    if not labels:
        axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE


def bar_chart(slide, x, y, w, h, categories, values, colors, *, name, label_color=TEXT):
    """Horizontal bars, one colour per bar, the value printed at the end of each."""
    data = CategoryChartData()
    data.categories = categories
    data.add_series("Count", values)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    frame.name = name
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 55
    plot.vary_by_categories = False
    series = plot.series[0]
    for i, color in enumerate(colors):
        point = series.points[i]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(color)
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(13)
    labels.font.name = MONO
    labels.font.bold = True
    labels.font.color.rgb = rgb(label_color)
    labels.number_format = "0"
    labels.number_format_is_linked = False
    chart.category_axis.reverse_order = True          # first category at the top
    quiet_axis(chart.category_axis)
    chart.category_axis.tick_labels.font.size = Pt(13)
    chart.category_axis.tick_labels.font.color.rgb = rgb(TEXT)
    quiet_axis(chart.value_axis, labels=False)
    chart.value_axis.format.line.fill.background()
    chart.value_axis.minimum_scale = 0
    chart.value_axis.maximum_scale = max(values) * 1.18
    return chart


def outcome_bar(slide, x, y, w, h, counts: dict, *, label_size=13):
    """One flat bar split by outcome, with the three counts in one line under it."""
    total = sum(counts.values())
    cursor = x
    runs = []
    for outcome in ("Extinction", "Disruption", "Completion"):
        width = w * counts[outcome] / total
        rect(slide, cursor, y, width, h, OUTCOME_COLOR[outcome], name=f"{outcome} share")
        cursor += width
        runs += [("■ ", {"color": OUTCOME_COLOR[outcome]}), (f"{outcome} ", {"color": MUTED}),
                 (f"{counts[outcome]}     ", {"font": MONO, "bold": True, "color": TEXT})]
    text(slide, x, y + h + 0.1, w, 0.3, runs, size=label_size, name="Outcome counts")


# =============================================================================== the seven slides

def slide_title(prs, n):
    s = new_slide(
        prs, 1, "Space Apps 2026 · Flame in Freefall",
        f"{n['report']}, Table IX ({n['first']} to {n['last']}). Totals recomputed from the table.",
        f"Flamefall Analytics is an interactive console over NASA's microgravity combustion data. Its core is {n['n']} droplet burns "
        f"from the FLEX experiment on the space station: {n['outcomes']['Extinction']} ended in extinction of the visible flame, "
        f"{n['outcomes']['Disruption']} in disruption and {n['outcomes']['Completion']} burned to completion. Live at {SITE_URL}.")
    text(s, LEFT, 1.25, 6.3, 1.0, "Flamefall Analytics", size=50, font=HEAD, bold=True, name="Title")
    text(s, LEFT, 2.45, 5.9, 1.2, "Flame in Freefall: what microgravity combustion experiments actually measured, for spacecraft fire safety.",
         size=19, color=MUTED, spacing=1.1, name="Subtitle")
    text(s, LEFT, 3.95, 5.9, 0.5, "An interactive console over NASA's microgravity combustion data.", size=16, name="One line")
    text(s, LEFT, 5.55, 5.9, 0.4, [("Team Flamefall Analytics  ·  ", {"color": MUTED}), (SITE, {"font": MONO, "color": AMBER})],
         size=13, link=SITE_URL, name="Team and link")
    text(s, 7.3, 0.95, 5.4, 2.9, str(n["n"]), size=190, font=MONO, color=AMBER, bold=True, name="Hero number")
    text(s, 7.4, 3.9, 5.2, 0.4, "droplet burns on the space station, one row each", size=15, name="Hero number caption")
    outcome_bar(s, 7.4, 4.65, 5.2, 0.5, n["outcomes"])
    return s


def slide_problem(prs, n):
    others = n["search_hits"] - n["combustion_science"]
    s = new_slide(
        prs, 2, "The problem",
        f"PSI Data Repository, search “combustion”, retrieved {n['retrieved']}. {n['combustion_science']} of the {n['search_hits']} records are "
        f"combustion science; {others} are other research areas. The console adds {n['outside_search']} related investigations the search does not return.",
        f"Fire behaves differently in space, and the rules for stopping it were written for gravity. A fire in a crewed cabin has nowhere to go. "
        f"A search of NASA's Physical Sciences Informatics repository for combustion returns {n['search_hits']} records; "
        f"{n['combustion_science']} are combustion science. The chart groups them by what each one burned.")
    text(s, LEFT, 1.15, 11.6, 1.1, "Fire behaves differently in space, and the rules for stopping it were written for gravity.",
         size=28, font=HEAD, bold=True, spacing=1.05, name="Title")
    text(s, LEFT, 2.5, 11.6, 0.5, "A fire in a crewed cabin or habitat has nowhere to go, and the crew cannot step outside.", size=17, color=MUTED,
         name="Stakes")
    hero(s, LEFT, 3.35, 4.2, str(n["search_hits"]), "records returned by a search of NASA's PSI repository for “combustion”: the starting point of this console's catalogue",
         size=130, caption_w=4.3)
    text(s, 5.75, 3.4, 6.8, 0.3, f"THE {n['search_hits']} RECORDS, BY KIND", size=11, font=MONO, color=DIM, name="Chart label")
    labels = [k for k, _ in n["burned"]]
    values = [v for _, v in n["burned"]]
    bar_chart(s, 5.6, 3.65, 7.0, 2.95, labels, values, [DIM if k == "Not combustion" else CYAN for k in labels], name="Records by what they burned")
    return s


def slide_flex(prs, n):
    s = new_slide(
        prs, 3, "The evidence base · FLEX",
        f"{n['report']}, Table IX, {n['first']} to {n['last']}.",
        f"FLEX burned single droplets of methanol or n-heptane on the space station while the atmosphere was varied. Table IX of the report has "
        f"one row per burn: {n['n']} rows. Each cell here is one test, in test order, coloured by how it ended. Every total was recomputed from "
        f"the table, not copied from the report's text.")
    hero(s, LEFT, 1.0, 5.0, str(n["n"]), f"droplet burns, one row each in Table IX of {n['report']}", size=150, caption_w=4.6)
    text(s, LEFT, 4.5, 4.6, 1.0, "Single droplets of methanol or n-heptane burned on the space station while the atmosphere was varied.",
         size=15, color=MUTED, spacing=1.1, name="What it is")
    text(s, LEFT, 5.6, 4.6, 0.8, "Every total here was recomputed from the table, not copied from the report's text.", size=15, color=MUTED,
         spacing=1.1, name="Method")
    cols, size, gap = 23, 0.255, 0.05
    assert len(n["order"]) == n["n"] and n["n"] % cols == 0
    x0, y0 = 5.75, 1.15
    text(s, x0, y0 - 0.33, 7.0, 0.3, "EVERY TEST, IN TEST ORDER · ONE CELL EACH", size=11, font=MONO, color=DIM, name="Chart label")
    for i, outcome in enumerate(n["order"]):
        rect(s, x0 + (i % cols) * (size + gap), y0 + (i // cols) * (size + gap), size, size, OUTCOME_COLOR[outcome], name=f"Test {i + 1}: {outcome}")
    rows = n["n"] // cols
    outcome_bar(s, x0, y0 + rows * (size + gap) + 0.3, cols * (size + gap) - gap, 0.34, n["outcomes"])
    return s


def slide_fuel(prs, n):
    m, h = n["by_fuel"]["Methanol"], n["by_fuel"]["Heptane"]
    s = new_slide(
        prs, 4, "The quantitative core",
        f"{n['report']}, Table IX, recomputed from the data. Scatter: share of tests ending in Extinction at each tested oxygen level.",
        f"{pct(n['extinction_share'])} of all {n['n']} tests ended with the visible flame going out. For methanol it was {pct(m['extinction_share'])} "
        f"({m['Extinction']} of {m['n']}); for n-heptane {pct(h['extinction_share'])} ({h['Extinction']} of {h['n']}). Same apparatus, overlapping "
        f"atmospheres, different fuel. The scatter shows the share ending in extinction at each oxygen level tested; no trend line is fitted.")
    text(s, LEFT, 1.05, 6.0, 0.6, "Fuel matters as much as atmosphere", size=28, font=HEAD, bold=True, name="Title")
    hero(s, LEFT, 1.9, 5.2, pct(n["extinction_share"]), f"of all {n['n']} tests ended with the visible flame going out", size=96, color=RED,
         caption_w=4.6)
    hero(s, LEFT, 4.1, 2.5, pct(m["extinction_share"]), f"methanol\n{m['Extinction']} of {m['n']}", size=40, color=CYAN, name="Methanol share")
    hero(s, LEFT + 2.6, 4.1, 2.5, pct(h["extinction_share"]), f"n-heptane\n{h['Extinction']} of {h['n']}", size=40, color=AMBER, name="n-Heptane share")
    text(s, LEFT, 5.9, 4.9, 0.6, "Same apparatus, overlapping atmospheres, different fuel, very different outcome.", size=15, color=MUTED, name="One line")

    x0 = 6.15
    text(s, x0, 1.95, 6.5, 0.3, "HOW EACH FUEL'S TESTS ENDED", size=11, font=MONO, color=DIM, name="Chart label 1")
    for row, (label, fuel, color) in enumerate([("Methanol", m, CYAN), ("n-Heptane", h, AMBER)]):
        y = 2.3 + row * 0.85
        text(s, x0, y, 1.3, 0.3, label, size=13, color=color, bold=True, name=f"{label} label")
        outcome_bar(s, x0 + 1.35, y - 0.02, 5.1, 0.3, {k: fuel[k] for k in ("Extinction", "Disruption", "Completion")}, label_size=11)

    text(s, x0, 4.05, 6.5, 0.3, "SHARE ENDING IN EXTINCTION, BY OXYGEN LEVEL TESTED", size=11, font=MONO, color=DIM, name="Chart label 2")
    data = XyChartData()
    for fuel, label in (("Methanol", "Methanol"), ("Heptane", "n-Heptane")):
        series = data.add_series(label)
        for level, share in n["share_by_o2"][fuel]:
            series.add_data_point(level, share)
    frame = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(x0 - 0.1), Inches(4.25), Inches(6.7), Inches(2.45), data)
    frame.name = "Extinction share by oxygen level"
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = True
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(11)
    chart.legend.font.color.rgb = rgb(MUTED)
    from pptx.enum.chart import XL_LEGEND_POSITION
    chart.legend.position = XL_LEGEND_POSITION.TOP
    for series, color in zip(chart.plots[0].series, (CYAN, AMBER)):
        series.format.line.fill.background()
        series.marker.style = XL_MARKER_STYLE.CIRCLE
        series.marker.size = 8
        series.marker.format.fill.solid()
        series.marker.format.fill.fore_color.rgb = rgb(color)
        series.marker.format.line.fill.background()
    quiet_axis(chart.value_axis, gridlines=True)
    chart.value_axis.minimum_scale, chart.value_axis.maximum_scale, chart.value_axis.major_unit = 0, 1, 0.25
    chart.value_axis.tick_labels.number_format = "0%"
    chart.value_axis.tick_labels.number_format_is_linked = False
    quiet_axis(chart.category_axis)
    chart.category_axis.minimum_scale, chart.category_axis.maximum_scale, chart.category_axis.major_unit = 10, 36, 4
    chart.category_axis.tick_labels.number_format = '0"% O2"'
    chart.category_axis.tick_labels.number_format_is_linked = False
    return s


def slide_cool(prs, n):
    c, total = n["cool"], n["heptane_extinctions"]
    parts = [("Cool-flame evidence", c["indicated"], AMBER), ("No evidence", c["not_indicated"], CYAN), ("Unclear", c["unclear"], DIM),
             ("Caption silent", c[""], DIM)]
    assert sum(v for _, v, _ in parts) == total
    s = new_slide(
        prs, 5, "What “extinction” hides",
        f"{n['report']}, Appendix B figure captions. Cool-flame temperature, as reported for gas cool flames: {n['cool_temp_source']}.",
        f"In Table IX, Extinction means the visible flame went out. Of the {total} n-heptane tests logged as Extinction, the report's captions "
        f"give evidence of cool-flame burning afterwards in {c['indicated']}, no evidence in {c['not_indicated']}, are unclear in {c['unclear']} "
        f"and say nothing in {c['']}. Cool flames burn at {n['cool_temp']} (a figure reported for gas cool flames): a detector that watches for "
        f"visible flame does not see one.")
    text(s, LEFT, 1.05, 11.0, 0.6, "“Extinction” only means the visible flame went out", size=28, font=HEAD, bold=True, name="Title")
    hero(s, LEFT, 1.9, 6.0, f"{c['indicated']} of {total}", "n-heptane “extinctions” show evidence that the droplet kept burning as a cool flame",
         size=110, color=RED, caption_w=5.2)
    text(s, LEFT, 5.25, 5.3, 1.1,
         f"A sensor that watches for visible flame will miss a cool flame. Gas cool flames burn at {n['cool_temp']}.", size=15, color=MUTED,
         spacing=1.1, name="Why it matters")
    text(s, 6.75, 2.0, 5.8, 0.3, f"THE {total} N-HEPTANE TESTS LOGGED AS EXTINCTION", size=11, font=MONO, color=DIM, name="Chart label")
    bar_chart(s, 6.55, 2.3, 6.1, 3.6, [p[0] for p in parts], [p[1] for p in parts], [p[2] for p in parts], name="Cool-flame evidence in the captions")
    return s


def slide_model(prs, n):
    assert n["headline_is"] == "leave-one-material-out" and n["failed_models"] == 1 and n["n_models"] == 3
    negatives = n["fp"] + n["tn"]
    sc = n["scenario"]
    assumed = " Pressure taken as 1 atm." if n["near_pressure_assumed"] else ""
    s = new_slide(
        prs, 6, "The model and the Scenario Lab",
        f"Model: scripts/train_models.py and data/models in the project's code (grouped cross-validation, seed 42), on {n['report']}, Table IX; "
        f"{', '.join(n['model_left_out'])} is left out: its pressure is printed as 0 mmHg and treated as missing. "
        f"Nearest tests: {'; '.join(n['near_source'])}.{assumed}",
        f"Three small logistic models, each trained on one kind of evidence and scored on groups of tests it never saw. The droplet-extinction "
        f"model scores {n['auc_cv']:.2f} in grouped cross-validation and {n['auc_headline']:.2f} when a whole fuel is left out; the lower number "
        f"is the headline. Its second class holds both Disruption and Completion: a disrupted droplet is not an extinguished flame. "
        f"At the working threshold it calls {n['fp']} of {negatives} negatives positive. The solid-fuel model does no better than "
        f"chance and the console shows it failing, so for a solid the Scenario Lab gives the nearest real tests and no probability. The model uses "
        f"{n['model_rows']} of the {n['n']} tests: the source prints the pressure of {', '.join(n['model_left_out'])} as 0 mmHg, which is treated "
        f"as missing. The nearest tests are the closest in oxygen, pressure and flow speed; flow direction is shown but not compared.")
    hero(s, LEFT, 1.0, 4.6, f"{n['auc_headline']:.2f}",
         f"headline AUC: the worse of grouped cross-validation ({n['auc_cv']:.2f}) and leave-one-fuel-out ({n['auc_headline']:.2f}). "
         "0.5 is a coin flip, 1 is perfect.", size=130, caption_w=4.7)
    text(s, LEFT, 4.45, 4.7, 0.9, "Three small logistic models, each trained on one kind of evidence and tested on unseen groups.",
         size=15, color=MUTED, spacing=1.1, name="What the model is")
    text(s, LEFT, 5.6, 4.7, 0.9,
         [(f"{pct(n['fpr'], 0)} false-positive rate", {"color": RED, "bold": True}),
          (f" at the working threshold: {n['fp']} of {negatives} negatives called positive. One of three models fails; the console shows it.", {})],
         size=15, color=MUTED, spacing=1.1, name="The honest line")

    x0 = 6.1
    text(s, x0, 1.12, 6.5, 0.3, f"DROPLET EXTINCTION MODEL · {n['model_rows']} OF {n['n']} TESTS", size=11, font=MONO, color=DIM, name="Chart label 1")
    cw, ch, lx = 1.75, 0.78, x0 + 2.35
    text(s, lx, 1.5, cw, 0.3, "called “Extinction”", size=12, color=MUTED, align=PP_ALIGN.CENTER, name="Column 1")
    text(s, lx + cw + 0.08, 1.5, cw, 0.3, "called “not Extinction”", size=12, color=MUTED, align=PP_ALIGN.CENTER, name="Column 2")
    cells = [("Extinction", n["tp"], n["fn"], SURFACE, SURFACE), ("Disruption or Completion", n["fp"], n["tn"], RED, SURFACE)]
    for r, (label, a, b, fa, fb) in enumerate(cells):
        y = 1.85 + r * (ch + 0.08)
        text(s, x0, y, 2.25, ch, label, size=13, color=TEXT, anchor=MSO_ANCHOR.MIDDLE, name=f"Row {r + 1}")
        for k, (value, fill) in enumerate(((a, fa), (b, fb))):
            box = rect(s, lx + k * (cw + 0.08), y, cw, ch, fill, line=LINE, name=f"Matrix cell {r + 1}.{k + 1}")
            box.text_frame.margin_left = box.text_frame.margin_right = 0
            p = box.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            run = p.add_run()
            run.text = str(value)
            run.font.name, run.font.size, run.font.bold = MONO, Pt(26), True
            run.font.color.rgb = rgb(BG if fill == RED else TEXT)

    y1 = 3.95
    text(s, x0, y1, 6.5, 0.3, "NEAREST REAL TESTS BY OXYGEN, PRESSURE AND FLOW SPEED", size=11, font=MONO, color=DIM, name="Chart label 2")
    text(s, x0, y1 + 0.33, 6.5, 0.35,
         f"{sc['material']} · {sc['o2']:g}% O2 · {sc['pressure']:g} kPa · 0 g · {sc['flow']:g} cm/s", size=14, font=MONO, color=AMBER, name="Scenario")
    heads = ["Test", "O2", "Flow", "Outcome", "Distance"]
    widths = [1.75, 0.9, 1.75, 1.25, 0.95]
    xs = [x0 + sum(widths[:i]) for i in range(len(widths))]
    for xh, head, wd in zip(xs, heads, widths):
        text(s, xh, y1 + 0.82, wd, 0.28, head.upper(), size=10, font=MONO, color=DIM, name=f"Head {head}")
    for r, row in enumerate(n["near"]):
        y = y1 + 1.12 + r * 0.38
        values = [(row["test"], MONO, TEXT), (f"{row['o2']:.1f}%", MONO, TEXT), (f"{row['flow']:g} cm/s {row['direction']}", MONO, TEXT),
                  (row["outcome"].replace("_", " "), BODY, AMBER if row["outcome"] == "sustained" else RED), (f"{row['distance']:.2f}", MONO, TEXT)]
        for xv, (value, font, color), wd in zip(xs, values, widths):
            text(s, xv, y, wd, 0.3, value, size=12.5, font=font, color=color, name=f"Nearest {r + 1}")
    return s


def slide_unknown(prs, n):
    s = new_slide(
        prs, 7, "What we don't know, and where to look",
        f"PSI Data Repository and the official challenge brief; {n['report']}, Table IX and Appendix B; {n['solid_top_source']}; NASA/TM-20210011385; "
        "SAME Final Report; T'ien et al., Combust. Flame 277 (2025).",
        f"The most useful thing the console shows is where the measurements stop. There are {n['partial_g']} combustion tests in lunar or Martian "
        f"gravity in the repository; what exists elsewhere is short drop-tower and parabolic-flight tests and one suborbital flight. The highest oxygen level of any solid-fuel test point in the console's data is "
        f"{n['solid_top_o2']:.1f}% (a test that did not ignite), and the widest range mapped for a solid in its evidence ends at {n['solid_limit']:g}% "
        f"(PMMA spheres, T'ien et al. 2025). {n['co2_and_he']} of {n['n']} droplet tests contain both carbon dioxide and helium. "
        f"Every number in this deck is in the console, with its source: {SITE_URL}.")
    text(s, LEFT, 1.05, 11.9, 1.0,
         "A console that shows only what was measured would hide the most useful fact: where the measurements stop.", size=26, font=HEAD,
         bold=True, spacing=1.05, name="Title")
    heroes = [(str(n["partial_g"]), "partial-gravity combustion tests in the PSI repository"),
              (f"{n['solid_top_o2']:.1f}%", "highest oxygen of any solid-fuel test point with a stated outcome"),
              (f"{n['co2_and_he']} of {n['n']}", "droplet tests that contain both CO2 and helium")]
    for i, (value, caption) in enumerate(heroes):
        hero(s, LEFT + i * 2.35, 2.45, 2.2, value, caption, size=44, color=AMBER if i == 1 else TEXT, caption_w=2.1, name=f"Hero number {i + 1}")

    px, py, pw, ph = 7.95, 2.4, 4.7, 4.1          # tall enough for two of the last three lines to wrap
    rect(s, px, py, pw, ph, None, line=DIM, dash=True, name="No data panel")
    tag = rect(s, px + 0.25, py + 0.25, 1.05, 0.3, TEXT, name="No data tag")
    tag.text_frame.margin_left = tag.text_frame.margin_right = tag.text_frame.margin_top = tag.text_frame.margin_bottom = 0
    tag.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tag.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "NO DATA"
    run.font.name, run.font.size, run.font.bold = MONO, Pt(11), True
    run.font.color.rgb = rgb(BG)
    text(s, px + 0.25, py + 0.72, pw - 0.5, 0.3, "WHAT YOU CANNOT SEE", size=11, font=MONO, color=DIM, name="Panel label 1")
    text(s, px + 0.25, py + 1.0, pw - 0.5, 1.0,
         f"cool flames after the visible flame goes out\npale-blue flames near the limit\nsmoke particles below {n['smoke_nm']} nm", size=13.5,
         color=TEXT, spacing=1.12, name="Cannot see")
    text(s, px + 0.25, py + 2.12, pw - 0.5, 0.3, "WHERE THE MEASUREMENTS STOP", size=11, font=MONO, color=DIM, name="Panel label 2")
    text(s, px + 0.25, py + 2.4, pw - 0.5, 1.0,
         f"lunar or Martian gravity: no data in the PSI repository\nsolids in the console: no test point above {n['solid_top_o2']:.1f}% oxygen\n"
         "CO2 with helium: in no FLEX test", size=13.5, color=TEXT, spacing=1.12, name="Where it stops")

    text(s, LEFT, 4.75, 7.0, 0.7, SITE, size=30, font=MONO, color=AMBER, bold=True, link=SITE_URL, name="Live link")
    text(s, LEFT, 5.5, 7.0, 0.4, "Every number in this deck is in the console, with its source.", size=16, name="Last line")
    return s


def build(path: Path = OUT) -> Path:
    n = numbers()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    prs.core_properties.title = "Flamefall Analytics"
    prs.core_properties.subject = "Flame in Freefall: what microgravity combustion experiments actually measured"
    prs.core_properties.author = prs.core_properties.last_modified_by = "Team Flamefall Analytics"
    prs.core_properties.comments = ""
    for make in (slide_title, slide_problem, slide_flex, slide_fuel, slide_cool, slide_model, slide_unknown):
        make(prs, n)
    assert len(prs.slides) == 7
    import datetime as dt

    prs.core_properties.created = prs.core_properties.modified = dt.datetime(2026, 11, 14)
    path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(path))
    set_theme_fonts(path)
    return path


FIXED_DATE = (2026, 11, 14, 0, 0, 0)
ZIP_SYSTEM, ZIP_ATTR = 0, 0o600 << 16      # what every entry of the file records, whatever machine built it
# What the file says about itself. Written whole, in place of the library template's values.
APP_PROPERTIES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    "<Application>scripts/build_deck.py</Application><PresentationFormat>Widescreen</PresentationFormat>"
    "<Slides>7</Slides><Notes>7</Notes><HiddenSlides>0</HiddenSlides></Properties>"
)


def fixed_workbook(data: bytes) -> bytes:
    """A chart's embedded workbook with its creation time and zip dates fixed, so a rebuild changes nothing."""
    import io
    import re
    import zipfile

    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            inner = src.read(item.filename)
            if item.filename == "docProps/core.xml":
                inner = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)", rb"\g<1>2026-11-14T00:00:00Z\g<2>", inner)
            info = zipfile.ZipInfo(item.filename, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system, info.external_attr = ZIP_SYSTEM, ZIP_ATTR
            dst.writestr(info, inner)
    return out.getvalue()


def set_theme_fonts(path: Path) -> None:
    """Write the heading and body fonts into the file's theme, and fix every date inside the file.

    Text with no font of its own then uses the deck's fonts too. Two builds from the same data on
    the same machine are the same file, byte for byte; across machines the compressed bytes can
    still differ with the version of zlib, which is why the test compares content, not bytes, with
    the committed file.
    """
    import re
    import shutil
    import zipfile

    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename.startswith("ppt/theme/") and item.filename.endswith(".xml"):
                xml = data.decode("utf-8")
                for block, font in (("majorFont", HEAD), ("minorFont", BODY)):
                    xml, n = re.subn(rf'(<a:{block}>\s*<a:latin typeface=")[^"]*(")', rf"\g<1>{font}\g<2>", xml)
                    assert n == 1, (item.filename, block, n)
                data = xml.encode("utf-8")
            if item.filename.startswith("ppt/embeddings/") and item.filename.endswith(".xlsx"):
                data = fixed_workbook(data)
            if item.filename == "docProps/app.xml":
                data = APP_PROPERTIES.encode("utf-8")
            info = zipfile.ZipInfo(item.filename, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system, info.external_attr = ZIP_SYSTEM, ZIP_ATTR          # the same on every operating system
            dst.writestr(info, data)
    shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    out = build(Path(sys.argv[1]) if len(sys.argv) > 1 else OUT)
    print(f"wrote {out}")
