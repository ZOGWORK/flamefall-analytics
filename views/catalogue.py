"""Investigation Catalogue: every combustion investigation, searchable, filterable and ranked by a stated rule."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from flamefall import catalogue as cat
from flamefall import psi, ranking, ui

inv = cat.load_investigations()
ev = cat.load_evidence()
n = cat.counts()

ui.kicker("PSI Data Repository · combustion science")
st.title("Investigation Catalogue")
st.markdown(
    '<p class="ff-lede">What each experiment set out to do, what it burned, under which conditions, and the one '
    "result that matters most for fire protection. Fields the repository does not state are left blank.</p>",
    unsafe_allow_html=True)

ui.stat_cards([
    dict(value=n["search_hits"], label="records returned by a PSI search for “combustion”",
         source=f"PSI repository search, retrieved {n['retrieved'][:10]}", tone="amber"),
    dict(value=n["combustion_science"], label="of those are Combustion Science",
         source="The other two are a solder study (PSI-181) and a fluid-physics experiment (PSI-108)", tone="cyan"),
    dict(value=n["tables"], label="per-test experimental tables attached to those records",
         source=f"{n['with_experimental_table']} of {n['search_hits']} records attach at least one; all copied into this repository",
         tone="green"),
    dict(value=n["outside_psi_search"], label="related investigations that the search does not return",
         source="Saffire IV to VI, SoFIE-GEL, FLARE, LUCI, FM2: added from their own papers and marked as such",
         tone="violet"),
])
ui.source("PSI Data Repository search “combustion” and each record's own metadata (CC0-1.0)", psi.SEARCH_URL)

# ------------------------------------------------------------------ ask
ui.rule()
ui.section(
    "Ask the evidence",
    "Type a question. The answer is the matching measured statements themselves, each with its source: "
    "retrieval and extraction only, so it cannot make up a number.")
examples = ["Which experiments tested solid materials above 25% oxygen?", "Did the smoke detector miss anything?",
            "What do we know about fire in lunar gravity?", "Does turning off ventilation put a flame out?"]
query = st.text_input("Question", value="", placeholder=examples[0], label_visibility="collapsed")
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    if col.button(ex, width="stretch"):
        query = ex
if query:
    res = cat.answer(query)
    if res["filters"]:
        f = res["filters"]
        parts = ([f"ambient O2 of {f['o2_at_least']:g}% or more"] if "o2_at_least" in f else []) \
            + ([f"ambient O2 of {f['o2_at_most']:g}% or less"] if "o2_at_most" in f else []) \
            + ([f"{cat.EVIDENCE_CLASS_LABEL[f['evidence_class']].lower()} only"] if "evidence_class" in f else [])
        if "o2_at_least" in f or "o2_at_most" in f:
            st.caption("Filter read from your question: " + "; ".join(parts) + ". Burner-feed oxygen values are never matched.")
    if not res["statements"] and res["hits"].empty:
        ui.no_data("Nothing in the catalogue matches that question",
                   "No sourced statement or investigation record contains those terms. Try a material, a hardware "
                   "name, or a condition such as oxygen, pressure, flow or gravity.")
    else:
        st.markdown(f"**{len(res['statements'])} sourced statements** from {len(res['investigations'])} investigations:")
        for s in res["statements"]:
            grey = ' class="ff-unverified"' if s["verification"] == "unverified" else ""
            st.markdown(
                f'<div{grey}><p style="margin:0.5rem 0 0.1rem"><b>{ui.esc(s["investigation_id"])}</b> · {ui.esc(s["text"])}</p>'
                f'<div class="ff-src" style="margin-bottom:0.4rem">{ui.verification_badge(s["verification"])} '
                f'{ui.esc(s["source_ref"])} · <a href="{ui.esc(s["source_url"])}" target="_blank" rel="noopener">open source</a>'
                f"</div></div>", unsafe_allow_html=True)
        other = [i for i in res["investigations"] if i in set(inv["investigation_id"])]
        if other:
            st.caption("Investigations to open below: " + ", ".join(other[:8]))

# ------------------------------------------------------------------ filters + ranking
ui.rule()
ui.section("Browse and rank", "Filter by hardware, fuel and environment, or rank every investigation against a scenario.")
c1, c2, c3 = st.columns(3)
hardware = c1.multiselect("Hardware", sorted(inv.loc[inv["is_combustion"], "facility_group"].unique()),
                          help="CIR = Combustion Integrated Rack; MDCA = droplet apparatus; MSG = glovebox.")
fuel = c2.multiselect("Fuel type", ["droplet", "gas", "solid", "smoke", "model"],
                      format_func=lambda k: cat.FUEL_TYPE_LABEL[k])
env = c3.multiselect("Environment", list(cat.ENV_RULES),
                     help=" · ".join(f"{k}: {v}" for k, v in cat.ENV_RULES.items()))

preset_names = ["No ranking (catalogue order)"] + [p.name for p in ranking.PRESETS]
choice = st.selectbox("Rank by closeness to a scenario", preset_names)
if choice != preset_names[0]:
    p = next(p for p in ranking.PRESETS if p.name == choice)
    cls = "solid"
    shown = cat.rank_investigations(p.o2_pct, p.pressure_kpa, p.flow_cm_s, cls, p.gravity_g)
    w = cat.RELEVANCE_WEIGHTS
    st.markdown(
        f'<div class="ff-call info"><h4>Ranking rule (a design choice, shown in full)</h4>'
        f'<p class="ff-mono">closeness = {" + ".join(f"{v:.2f} × {k}" for k, v in w.items())}</p>'
        f'<p class="m">Scenario: {p.o2_pct:g}% O2 at {p.pressure_kpa:g} kPa, {p.flow_cm_s:g} cm/s, '
        f'{ranking.GRAVITY_NAME[p.gravity_g]}, solid material. Each term is 1 when the scenario lies inside the '
        "investigation's tested range, fades with distance outside it, and is 0 when the repository does not state "
        "the range. It measures how close the test conditions are. It says nothing about how dangerous the scenario is.</p></div>",
        unsafe_allow_html=True)
else:
    shown = inv[inv["is_combustion"]].copy()

if hardware:
    shown = shown[shown["facility_group"].isin(hardware)]
if fuel:
    shown = shown[shown["fuel_type"].isin(fuel)]
if env:
    shown = shown[shown["environments"].map(lambda tags: any(e in tags for e in env))]

if shown.empty:
    ui.no_data("No investigation matches these filters",
               "Remove a filter to see the rest. The full catalogue has "
               f"{int(inv['is_combustion'].sum())} combustion investigations.")

if "relevance" in shown and not shown.empty:
    table = shown[["investigation_id", "relevance"] + [f"rel_{k}" for k in cat.RELEVANCE_WEIGHTS]].head(12)
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={"investigation_id": "Investigation",
                       "relevance": st.column_config.ProgressColumn("Closeness", min_value=0, max_value=1, format="%.2f"),
                       **{f"rel_{k}": st.column_config.NumberColumn(k.capitalize(), format="%.2f")
                          for k in cat.RELEVANCE_WEIGHTS}})
    st.caption("Top 12 by closeness. Open an investigation below for the reason behind each term.")


def fmt_range(lo, hi, unit: str) -> str:
    if lo == "" or hi == "":
        return "not stated"
    lo, hi = float(lo), float(hi)
    return f"{lo:g} {unit}" if lo == hi else f"{lo:g} to {hi:g} {unit}"


st.markdown(f"**{len(shown)} investigations**")
for _, r in shown.iterrows():
    tag = r["psi_id"] if r["psi_id"] else "not in the PSI search"
    score = f" · closeness {r['relevance']:.2f}" if "relevance" in r else ""
    with st.expander(f"{r['investigation_id']} — {r['full_name']}  ·  {tag}{score}"):
        badges = ui.verification_badge(r["verification"]) + ui.badge(cat.FUEL_TYPE_LABEL.get(r["fuel_type"], r["fuel_type"]), "info")
        badges += "".join(ui.badge(e, "mute") for e in r["environments"])
        if r["status"] != "complete":
            badges += ui.badge(r["status"].replace("_", " "), "warn")
        st.markdown(badges, unsafe_allow_html=True)
        if r["key_result"]:
            st.markdown(f"**Key finding.** {r['key_result']}")
            ui.source(ui.esc(r["primary_source_ref"]), r["primary_source_url"])
        else:
            st.markdown("**Key finding.** *None recorded: no quantitative result for this investigation was checked "
                        "against a primary source during the build.*")
        st.markdown(
            '<div class="ff-kv">'
            f'<div class="k">Objective</div><div>{ui.esc(r["objective"]) or "not stated"}</div>'
            f'<div class="k">Fuels / materials</div><div>{ui.esc(r["materials"]) or "not stated"}</div>'
            f'<div class="k">Samples</div><div>{ui.esc(r["sample_geometry"]) or "not stated"}</div>'
            f'<div class="k">Ambient O2</div><div class="ff-mono">{fmt_range(r["o2_min_pct"], r["o2_max_pct"], "%")}</div>'
            f'<div class="k">Pressure</div><div class="ff-mono">{fmt_range(r["pressure_min_kPa"], r["pressure_max_kPa"], "kPa")}</div>'
            f'<div class="k">Flow</div><div class="ff-mono">{fmt_range(r["flow_min_cm_s"], r["flow_max_cm_s"], "cm/s")}'
            f'{" · " + r["flow_regime"] if r["flow_regime"] else ""}</div>'
            f'<div class="k">Tests</div><div class="ff-mono">{r["n_tests"] if r["n_tests"] != "" else "not stated"}'
            f'{" (" + ui.esc(r["n_tests_source"]) + ")" if r["n_tests_source"] else ""}</div>'
            f'<div class="k">Hardware</div><div>{ui.esc(r["facility"]) or ui.esc(r["facility_group"])} · {ui.esc(r["platform"])}</div>'
            f'<div class="k">Lead</div><div>{ui.esc(r["pi"]) or "not stated in the record"}</div>'
            f'<div class="k">Record dates</div><div class="ff-mono">{r["date_start"] or "?"} to {r["date_end"] or "?"}</div>'
            "</div>", unsafe_allow_html=True)
        if r["range_source"]:
            st.caption(f"Where the ranges come from: {r['range_source']}.")
        if r["note"]:
            st.caption(r["note"])
        if "relevance" in r:
            st.caption("Closeness terms: " + " · ".join(
                f"{k} {r[f'rel_{k}']:.2f} ({r[f'why_{k}']})" for k in cat.RELEVANCE_WEIGHTS))
        links = []
        if r["psi_id"]:
            links.append(f'<a href="{r["psi_url"]}" target="_blank" rel="noopener">PSI record {r["psi_id"]}</a>')
        if r["doi"]:
            links.append(f'<a href="https://doi.org/{r["doi"]}" target="_blank" rel="noopener">DOI {r["doi"]}</a>')
        if r["primary_source_url"] and r["primary_source_url"] != r["psi_url"]:
            links.append(f'<a href="{r["primary_source_url"]}" target="_blank" rel="noopener">primary source</a>')
        st.markdown('<div class="ff-src">' + " · ".join(links) + "</div>", unsafe_allow_html=True)

        more = ev[ev["investigation_id"] == r["investigation_id"]]
        if len(more):
            st.markdown(f"**All sourced statements for this investigation ({len(more)})**")
            for _, e in more.iterrows():
                grey = ' class="ff-unverified"' if e["verification"] == "unverified" else ""
                flag = "" if e["o2_is_ambient"] else ui.badge("burner feed, not ambient", "bad")
                st.markdown(
                    f'<div{grey}><p style="margin:0.4rem 0 0.1rem">{flag}{ui.esc(e["statement"])}</p>'
                    f'<div class="ff-src" style="margin-bottom:0.3rem">{ui.verification_badge(e["verification"])}'
                    f'{ui.esc(e["source_ref"])} · read: {ui.esc(e["read_level"])} · '
                    f'<a href="{ui.esc(e["source_url"])}" target="_blank" rel="noopener">open source</a></div></div>',
                    unsafe_allow_html=True)
        tables = [t for t in r["psi_tables"].split("; ") if t]
        if tables:
            pick = st.selectbox("PSI experimental table", tables, key=f"tbl-{r['investigation_id']}")
            if st.toggle("Show this table", key=f"show-{r['investigation_id']}"):
                t = psi.read_table(pick)
                st.dataframe(t, hide_index=True, width="stretch", height=280)
                st.caption(f"{len(t)} rows, exactly as PSI publishes them ({pick}).")

others = inv[~inv["is_combustion"]]
if len(others) and not (hardware or fuel or env):
    ui.rule()
    ui.section("Returned by the search, but not combustion", "Listed for completeness and left out of every ranking.", level=3)
    st.dataframe(others[["psi_id", "full_name", "psi_research_area", "psi_url"]], hide_index=True, width="stretch",
                 column_config={"psi_id": "PSI ID", "full_name": "Title", "psi_research_area": "PSI research area",
                                "psi_url": st.column_config.LinkColumn("Record")})
    ui.source("PSI Data Repository search “combustion”", psi.SEARCH_URL)
