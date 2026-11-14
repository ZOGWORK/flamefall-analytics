"""The running app: every page renders, and the acceptance behaviours hold end to end."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["views/overview.py", "views/flex_explorer.py", "views/catalogue.py", "views/scenario_lab.py",
         "views/model_lab.py", "views/unknowns.py"]


def open_page(page: str) -> AppTest:
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180)
    at.run()
    if page != PAGES[0]:
        at.switch_page(page)
        at.run()
    return at


def text_of(at: AppTest) -> str:
    """All markdown, caption and heading text on the page, tags stripped."""
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [t.value for t in at.title]
    return re.sub(r"<[^>]+>", " ", " ".join(parts))


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = open_page(page)
    assert not at.exception, [str(e.value) for e in at.exception]
    assert len(text_of(at)) > 400                               # never a blank page


def test_all_six_pages_exist():
    for page in PAGES:
        assert (ROOT / page).exists(), page


def test_overview_headline_cards():
    text = text_of(open_page("views/overview.py"))
    assert "Fire behaves differently in space" in text
    for needle in ["276", "67.4%", "80.3% vs 50.4%", "26", "24 of them combustion science"]:
        assert needle in text, needle


def test_explorer_empty_filter_gives_no_data_with_nearest_tests():
    at = open_page("views/flex_explorer.py")
    at.multiselect[0].set_value([])                             # no fuel selected
    at.run()
    assert not at.exception
    assert "No FLEX test matches these filters" in text_of(at)
    assert len(at.dataframe) >= 1                               # nearest tests are still listed


def test_partial_gravity_scenario_returns_no_data_with_nearest_real_tests():
    at = open_page("views/scenario_lab.py")
    at.radio(key="sl_g").set_value("Lunar, 0.16 g")
    at.run()
    assert not at.exception
    text = text_of(at)
    assert "NO DATA" in text and "No combustion test at Lunar gravity exists in the PSI repository" in text
    assert "No estimate at this gravity" in text                # the microgravity model is not applied
    assert "LUCI" in text and "FM2" in text                     # nearest real evidence is shown
    assert len(at.dataframe) >= 1                               # and the nearest real tests table
    assert not re.search(r"estimated chance", text)             # no fabricated number


def test_scenario_outside_the_envelope_is_flagged():
    at = open_page("views/scenario_lab.py")
    at.selectbox(key="sl_material").set_value("n-Heptane droplet")
    at.slider(key="sl_o2").set_value(50.0)
    at.run()
    assert not at.exception
    text = text_of(at)
    assert "outside the tested envelope" in text and "DEMO" in text
    assert "Oxygen: FLEX heptane tests cover 13 to 34%" in text


def test_cool_flame_estimate_is_flagged_outside_its_own_envelope():
    """30% O2 is inside the extinction model's range but outside the cool-flame model's (13 to 24%)."""
    at = open_page("views/scenario_lab.py")
    at.selectbox(key="sl_material").set_value("n-Heptane droplet")
    at.slider(key="sl_o2").set_value(30.0)
    at.slider(key="sl_flow").set_value(0.0)
    at.run()
    assert not at.exception
    text = text_of(at)
    assert "outside what the exploratory cool-flame model has seen" in text and "is a DEMO value" in text


def test_model_lab_names_the_right_class_for_the_cool_flame_model():
    at = open_page("views/model_lab.py")
    at.radio[0].set_value("droplet_cool_flame")
    at.run()
    assert not at.exception
    text = text_of(at)
    assert "cool-flame evidence after the visible flame went out" in text and "flame present" not in text


def test_solid_scenario_shows_no_model_probability():
    text = text_of(open_page("views/scenario_lab.py"))          # default: PMMA, a solid
    assert "No model estimate for solid materials" in text and "failed validation" in text
    assert "What the nearest tests did" in text


def test_oxygen_above_34_percent_for_solids_is_no_data():
    at = open_page("views/scenario_lab.py")
    at.slider(key="sl_o2").set_value(40.0)
    at.run()
    assert "Oxygen above 34%: no solid-material test point exists" in text_of(at)


def test_model_lab_shows_grouped_cv_confusion_matrix_and_distance_warning():
    at = open_page("views/model_lab.py")
    text = text_of(at)
    assert "grouped-CV ROC-AUC" in text and "false-positive rate" in text
    assert "Youden" in text and "Distance-to-data warning" in text      # default query is out of envelope
    assert "DEMO" in text


def test_unknowns_page_names_the_three_gaps_and_the_three_invisibles():
    text = text_of(open_page("views/unknowns.py"))
    for needle in ["Partial gravity", "Solid materials above the tested oxygen range",
                   "Carbon dioxide and helium together", "Cool flames after the visible flame is gone",
                   "Dim blue flames at low flow", "Smoke too fine for the detector"]:
        assert needle in text, needle
