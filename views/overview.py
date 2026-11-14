"""Overview: the headline numbers, the dangerous combination, and where to go next."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from flamefall import flex, ui

ROOT = Path(__file__).resolve().parents[1]
s = flex.summary()
meth, hept = s["by_fuel"]["Methanol"], s["by_fuel"]["Heptane"]
cool = s["cool_flame"]

ui.kicker("Space Apps 2026 · Flame in Freefall")
st.markdown(
    '<h1 class="ff-hero">Fire behaves differently in space. '
    "<em>This dashboard shows what was actually measured.</em></h1>"
    '<p class="ff-lede">Decades of microgravity combustion experiments, reduced to what they recorded, '
    "ranked for the crewed vehicle or habitat you care about, with every number traceable to its table "
    "and an explicit “no data” wherever nobody has run the test.</p>",
    unsafe_allow_html=True,
)

src_ix = f"{flex.REPORT}, Table IX · recomputed from the CSV"
ui.stat_cards([
    dict(value=s["n"], label="FLEX droplet-burn tests in Table IX",
         source=f"{src_ix} · {s['first_test']} to {s['last_test']}, {len(s['absent_numbers'])} numbers absent",
         tone="amber"),
    dict(value=ui.pct(s["extinction_share"]), label="ended with the visible flame going out",
         source=f"{src_ix} · {s['outcomes']['Extinction']} of {s['n']}; Disruption "
                f"{s['outcomes']['Disruption']} and Completion {s['outcomes']['Completion']} counted separately",
         tone="red"),
    dict(value=f"{ui.pct(meth['extinction_share'])} vs {ui.pct(hept['extinction_share'])}",
         label="extinction share, methanol vs n-heptane",
         source=f"{src_ix} · {meth['Extinction']}/{meth['n']} vs {hept['Extinction']}/{hept['n']}",
         tone="cyan"),
    dict(value=f"{cool['indicated']} of {s['heptane_extinctions']}",
         label="“extinguished” heptane droplets with cool-flame evidence afterwards",
         source=f"{flex.REPORT}, Appendix B figure captions · {cool['not_indicated']} no evidence, "
                f"{cool['unclear']} unclear, {cool['']} caption silent",
         tone="violet"),
])

ui.rule()
ui.section(
    "The dangerous combination",
    "Four conditions that future crewed vehicles push towards at the same time, and what the experiments say about each.",
)
c1, c2 = st.columns(2)
with c1:
    ui.callout(
        "More oxygen, less pressure",
        "Spacesuits run on 100% O2 at 4.3 psi, so Moon-base and rover cabins are expected to sit in between: "
        "30% O2 or more at 10.2 psi or less. Flammability depends strongly on oxygen.",
        muted="Official challenge brief, Flame in Freefall (Space Apps 2026).",
    )
    ui.callout(
        "Fuel chemistry matters as much as atmosphere",
        f"In the same apparatus, methanol went out in {ui.pct(meth['extinction_share'])} of tests and "
        f"n-heptane in {ui.pct(hept['extinction_share'])}. There is no single flammability number.",
        muted=f"{src_ix}.",
        kind="info",
    )
with c2:
    ui.callout(
        "“No visible flame” is not “fire out”",
        f"The FLEX report describes evidence of cool-flame burning after the visible flame vanished in "
        f"{cool['indicated']} of the {s['heptane_extinctions']} n-heptane tests logged as Extinction: the droplet "
        "kept vaporising with nothing to see.",
        muted=f"{flex.REPORT}, Appendix B figure captions (authors' reading of vaporisation rate and vapour cloud).",
        kind="danger",
    )
    ui.no_data(
        "Partial gravity",
        "The repository holds no combustion test run in lunar or Martian gravity. Every partial-gravity answer "
        "in this dashboard says so and shows the nearest real tests instead.",
        muted="Official challenge brief: no partial-gravity combustion data currently in PSI.",
    )

ui.rule()
ui.section("Where to look", "Each page answers one question.")
links = [
    ("views/flex_explorer.py", "FLEX Explorer", "What happened in each of the 276 droplet burns?"),
    ("views/catalogue.py", "Investigation Catalogue", "Which experiments matter for my vehicle?"),
    ("views/scenario_lab.py", "Scenario Lab", "What is the nearest real test to my scenario?"),
    ("views/model_lab.py", "Model Lab", "How far can a model be trusted here?"),
    ("views/unknowns.py", "What We Don't Know", "Where does the data stop?"),
]
cols = st.columns(3)
for i, (path, title, question) in enumerate(p for p in links if (ROOT / p[0]).exists()):
    with cols[i % 3]:
        st.page_link(path, label=f"**{title}**  \n{question}", icon=":material/arrow_forward:")

ui.rule()
ui.source(
    f"FLEX data: {flex.REPORT_TITLE} ({flex.REPORT}), PSI record {flex.PSI_ID}. A builder-discovered primary "
    "source, not a link supplied on the challenge page.",
    flex.RECORD_URL,
)
