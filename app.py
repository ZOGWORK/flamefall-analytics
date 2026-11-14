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
    initial_sidebar_state="auto",      # open on a desktop, collapsed on a phone so it never covers the page
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

nav = st.navigation(pages, position="sidebar")

# Rendered BEFORE the page runs: a page may call st.stop() (the Explorer does on an empty filter),
# and this note has to be on screen in every state of every page.
with st.sidebar:
    st.markdown(f'<div class="ff-src" style="margin-top:0.4rem">{ui.esc(ui.DISCLAIMER)}</div>',
                unsafe_allow_html=True)

nav.run()
