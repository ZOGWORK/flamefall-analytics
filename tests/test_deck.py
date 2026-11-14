"""The slide deck and the in-browser page: their numbers must be the data's numbers."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from flamefall import catalogue as cat
from flamefall import flex, model

ROOT = Path(__file__).resolve().parents[1]
DECK = (ROOT / "deck" / "index.html").read_text(encoding="utf-8")
TEXT = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", DECK))


def card(name: str) -> dict:
    return json.loads((model.MODEL_DIR / f"{name}.json").read_text(encoding="utf-8"))


def test_deck_has_exactly_seven_slides():
    assert len(re.findall(r'<section class="slide', DECK)) == 7
    assert "Slide 7 of 7" in DECK and "Slide 8" not in DECK


def test_deck_flex_numbers_match_the_csv():
    s = flex.summary()
    m, h, c = s["by_fuel"]["Methanol"], s["by_fuel"]["Heptane"], s["cool_flame"]
    for needle in [
        f"Extinction {s['outcomes']['Extinction']}", f"Disruption {s['outcomes']['Disruption']}",
        f"Completion {s['outcomes']['Completion']}",
        f"{m['Extinction']} of {m['n']} extinguished · {m['extinction_share']:.1%}",
        f"{h['Extinction']} of {h['n']} extinguished · {h['extinction_share']:.1%}",
        f"{c['indicated']} kept burning as a cool flame", f"{c['not_indicated']} no evidence",
        f"{c['unclear']} unclear", f"{c['']} caption silent",
        f"{s['heptane_extinctions']} n-heptane tests logged as",
        f"{s['co2_and_he']} of {s['n']}", f"CO2 in {s['co2_tests']} tests, helium in {s['he_tests']}",
        f"{s['ranges']['extinction_diameter_mm'][3]} tests print no extinction diameter",
    ]:
        assert needle in TEXT, needle
    # the dot grid is drawn from the same four counts
    assert f"[['cool',{c['indicated']}],['none',{c['not_indicated']}],['unclear',{c['unclear']}],['silent',{c['']}]]" in DECK
    widths = re.findall(r"--w:([\d.]+)%;background:var\(--(red|violet|green)\)", DECK)[:3]
    assert [float(w) for w, _ in widths] == [round(100 * s["outcomes"][o] / s["n"], 1)
                                             for o in ("Extinction", "Disruption", "Completion")]


def test_deck_model_numbers_match_the_model_cards():
    d, s = card("droplet_extinction"), card("solid_sustained")
    dm, sm = d["metrics"], s["metrics"]
    cy = dm["confusion_at_youden"]
    for needle in [
        f"AUC {dm['roc_auc']:.2f}", f"AUC {d['headline_auc']:.2f}", f"AUC {sm['roc_auc']:.2f}",
        f"{d['n_rows']} tests, {d['n_groups']} atmospheres",
        f"95% interval {dm['roc_auc_ci'][0]:.2f} to {dm['roc_auc_ci'][1]:.2f}",
        f"{cy['fp']} of {cy['fp'] + cy['tn']} non-extinctions are called extinctions ({cy['false_positive_rate']:.0%})",
        f"{s['n_rows']} verified test points, 95% interval {sm['roc_auc_ci'][0]:.2f} to {sm['roc_auc_ci'][1]:.2f}",
        f"{dm['rowwise_cv_auc_for_comparison_only']:.2f} and {sm['rowwise_cv_auc_for_comparison_only']:.2f}",
    ]:
        assert needle in TEXT, needle
    assert d["headline_is"] == "leave-one-material-out"          # "unseen fuel (the headline)"


def test_deck_catalogue_numbers_match_the_data():
    n = cat.counts()
    decided = cat.solid_envelope()["n"]
    ev = cat.load_evidence().set_index("id")
    for needle in [
        f"{n['search_hits']} records come back", f"{n['combustion_science']} are combustion science",
        f"{n['tables']} per-test tables", f"{n['evidence_verified']} of {n['evidence']}",
        f"{decided} solid-fuel test points with a stated outcome",
        "3,864 cells", "274 rows", "981 s", "13.5%", "15.4%", "0.92 mm/s against 1.5 mm/s",
    ]:
        assert needle in TEXT, needle
    assert ev.loc["saffire-alarm-981", "value"] == 981
    assert ev.loc["luci-sibal", "value"] == 0.92
    assert "3,217, 3,080 and 1,507 W" in TEXT and "3,150 W was an average, not a peak" in TEXT


def test_every_slide_carries_a_source():
    slides = re.split(r'<section class="slide', DECK)[1:]
    for i, slide in enumerate(slides, 1):
        assert 'class="src"' in slide, f"slide {i} has no source line"


def test_deck_is_self_contained_and_unbranded():
    assert not re.search(r"<img\b", DECK)                         # charts are inline SVG and CSS only
    scripts = re.findall(r'<script[^>]*src="([^"]+)"', DECK)
    assert scripts == []                                         # no external script
    assert "prefers-reduced-motion" in DECK                      # animations can be turned off
    assert "not affiliated with or endorsed by NASA" in TEXT


# ------------------------------------------------------------------ the in-browser page

def test_web_page_mounts_every_file_the_app_needs():
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_web

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    listed = json.loads(re.search(r"const paths = (\[.*?\]);", page, re.S).group(1))
    assert listed == build_web.collect()                         # index.html is current
    for needed in ["app.py", "flamefall/model.py", "views/overview.py", "views/flex_explorer.py",
                   "views/catalogue.py", "views/scenario_lab.py", "views/model_lab.py", "views/unknowns.py",
                   "data/flex-table-ix.csv", "data/evidence.json", "data/investigations.csv",
                   "data/solid_test_points.csv", "data/models/droplet_extinction.json",
                   "data/psi/search_combustion.json", "data/psi/SNAPSHOT.json"]:
        assert needed in listed, needed
    assert all((ROOT / p).exists() for p in listed)
    assert f"@stlite/browser@{build_web.STLITE}/" in page and "@latest" not in page
    assert (ROOT / ".nojekyll").exists()


def test_web_page_root_fills_the_viewport():
    """stlite positions the app absolutely inside #root. With no height the app loads but is invisible."""
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    rule = re.search(r"#root\s*\{([^}]*)\}", page).group(1)
    assert "position: fixed" in rule and "inset: 0" in rule


def test_web_page_versions_every_mounted_file():
    """Each file URL carries a hash of the build, so a cached old file can never be mixed with a new page."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_web

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    version = re.search(r'const version = "([0-9a-f]{12})";', page).group(1)
    assert version == build_web.content_version(build_web.collect())      # rebuild index.html after any change
    assert 'p + "?v=" + version' in page


def test_deep_links_are_sent_home_on_a_static_host():
    not_found = (ROOT / "404.html").read_text(encoding="utf-8")
    assert 'location.replace("/flamefall-analytics/")' in not_found and "http-equiv=\"refresh\"" in not_found


def test_sidebar_collapses_on_a_phone():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'initial_sidebar_state="auto"' in app and 'initial_sidebar_state="expanded"' not in app


@pytest.mark.parametrize("module", ["flamefall/flex.py", "flamefall/catalogue.py", "flamefall/psi.py",
                                    "flamefall/ranking.py", "flamefall/ui.py", "flamefall/charts.py"])
def test_app_modules_import_nothing_outside_the_browser_requirements(module):
    """The in-browser build installs pandas, numpy, plotly and scikit-learn only."""
    allowed = {"__future__", "json", "re", "math", "html", "functools", "pathlib", "dataclasses", "numpy", "pandas",
               "plotly", "streamlit", "sklearn", "scipy"}
    src = (ROOT / module).read_text(encoding="utf-8")
    tops = {m.split(".")[0] for m in re.findall(r"^\s*(?:from|import)\s+([\w.]+)", src, re.M)}
    tops.discard("")                                             # relative imports ("from . import x")
    assert tops - allowed - {"flamefall"} == set(), tops - allowed
