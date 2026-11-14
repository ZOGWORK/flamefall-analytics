"""Flamefall Analytics: entry point. Run with `streamlit run app.py`."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from flamefall import ui

ROOT = Path(__file__).parent

st.set_page_config(
    page_title="Flamefall Analytics",
    page_icon=":material/local_fire_department:",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.setup_page()

# One level of navigation, in reading order. A page appears only once its file exists,
# so a partial deploy never shows a dead link.
PAGES = [
    ("views/overview.py", "Overview", ":material/home:", "overview"),
    ("views/flex_explorer.py", "FLEX Explorer", ":material/scatter_plot:", "flex"),
    ("views/catalogue.py", "Investigation Catalogue", ":material/menu_book:", "catalogue"),
    ("views/scenario_lab.py", "Scenario Lab", ":material/tune:", "scenario"),
    ("views/model_lab.py", "Model Lab", ":material/monitoring:", "model"),
    ("views/unknowns.py", "What We Don't Know", ":material/visibility_off:", "unknowns"),
]
pages = [
    st.Page(path, title=title, icon=icon, url_path=slug, default=(slug == "overview"))
    for path, title, icon, slug in PAGES
    if (ROOT / path).exists()
]

with st.sidebar:
    st.markdown(
        '<div class="ff-kicker" style="margin:0.2rem 0 0">Flamefall Analytics</div>'
        '<div style="color:#9AA7B6;font-size:0.82rem;margin-bottom:0.6rem">'
        "Fire safety evidence from microgravity combustion experiments</div>",
        unsafe_allow_html=True,
    )

st.navigation(pages, position="sidebar").run()

with st.sidebar:
    st.markdown(
        '<div class="ff-src" style="margin-top:1.4rem">Estimates only. This dashboard reports what '
        "experiments measured and where no data exists. It never rates a material, atmosphere or "
        "design as acceptable for flight.</div>",
        unsafe_allow_html=True,
    )
