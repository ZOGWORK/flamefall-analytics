"""FLEX Explorer: the 276 droplet burns of Table IX, filterable, with provenance on every panel."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from flamefall import charts, flex, ui

f = flex.load_flex()
SRC = f"{flex.REPORT}, Table IX (PDF pp. 26–34)"

ui.kicker("Droplet combustion · quantitative core")
st.title("FLEX Explorer")
st.markdown(
    '<p class="ff-lede">Single droplets of methanol or n-heptane burned in a sealed chamber on the space '
    "station while the atmosphere was varied. One row per burn, exactly as the report prints it.</p>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ sidebar filters
with st.sidebar:
    st.markdown("#### Filter the tests")
    fuels = st.multiselect("Fuel", ["Methanol", "Heptane"], default=["Methanol", "Heptane"],
                           format_func=lambda x: "n-Heptane" if x == "Heptane" else x)
    o2_lo, o2_hi = int(f["o2_pct"].min()), int(f["o2_pct"].max())
    o2 = st.slider("Ambient O2, mol %", o2_lo, o2_hi, (o2_lo, o2_hi), step=1)
    p_lo, p_hi = 0.65, 3.10
    pressure = st.slider("Ambient pressure, atm", p_lo, p_hi, (p_lo, p_hi), step=0.05,
                         help="FLEX-114 has no pressure in the source and is kept only at the full range.")
    families = sorted(f["atmosphere"].unique())
    atmos = st.multiselect("Diluent", families, default=families)
    outcomes = st.multiselect("Outcome", flex.OUTCOMES, default=flex.OUTCOMES)

full_pressure = pressure == (p_lo, p_hi)
mask = (
    f["fuel"].isin(fuels)
    & f["o2_pct"].between(o2[0], o2[1])
    & (f["pressure_atm"].between(pressure[0], pressure[1]) | (f["pressure_atm"].isna() & full_pressure))
    & f["atmosphere"].isin(atmos)
    & f["outcome"].isin(outcomes)
)
d = f[mask]

# ------------------------------------------------------------------ empty state
if d.empty:
    ui.no_data(
        "No FLEX test matches these filters",
        "Nothing in Table IX was run at this combination. The closest tests by oxygen and pressure are listed "
        "below so you can see what was actually tried.",
    )
    pool = f[f["fuel"].isin(fuels)] if fuels else f
    pool = pool[pool["pressure_atm"].notna()]       # FLEX-114 has no pressure in the source: it is not ranked
    target_o2, target_p = sum(o2) / 2, sum(pressure) / 2
    dist = ((pool["o2_pct"] - target_o2) / 22) ** 2 + ((pool["pressure_atm"] - target_p) / 2.4) ** 2
    near = pool.assign(_d=dist).nsmallest(8, "_d")
    st.dataframe(near[["test_id", "fuel", "o2_pct", "co2_pct", "he_pct", "pressure_atm", "d0_mm", "outcome", "source"]],
                 hide_index=True, width="stretch")
    ui.source(SRC, flex.PDF_URL)
    st.stop()

n = len(d)
k = int(d["extinguished"].sum())
lo, hi = flex.wilson_interval(k, n)
ui.stat_cards([
    dict(value=n, unit=f"of {len(f)}", label="tests match the filters", source=SRC, tone="amber"),
    dict(value=ui.pct(k / n), label="ended in Extinction",
         source=f"{k} of {n} · 95% interval {ui.pct(lo, 0)}–{ui.pct(hi, 0)} (Wilson)", tone="red"),
    dict(value=int((d["outcome"] == "Disruption").sum()), label="ended in Disruption (not an extinction)",
         source=f"{flex.REPORT} §5.2: may reflect needle contamination", tone="violet"),
    dict(value=int((d["outcome"] == "Completion").sum()), label="burned to Completion", source=SRC, tone="green"),
])

# ------------------------------------------------------------------ extinction vs gas
ui.rule()
ui.section(
    "Did the flame go out?",
    "Share of tests that ended in Extinction at each tested gas level. Bigger dots mean more tests; bars are 95% intervals.",
)
xcol = st.radio("Compare against", ["o2_pct", "co2_pct", "he_pct"], horizontal=True,
                format_func=lambda c: {"o2_pct": "Oxygen", "co2_pct": "Carbon dioxide", "he_pct": "Helium"}[c],
                label_visibility="collapsed")
tab_share, tab_mix = st.tabs(["Extinction share + trend", "All three outcomes, counted"])
with tab_share:
    ui.plotly(charts.extinction_share_figure(d, xcol), key="share")
with tab_mix:
    ui.plotly(charts.outcome_mix_figure(d, xcol), key="mix")
if xcol == "he_pct":
    he_n = int((d["he"] > 0).sum())
    ui.callout(
        "Helium: effect unclear",
        f"Only {he_n} of the filtered tests contain helium ({flex.summary()['he_tests']} in the whole table), "
        "and they were run at different oxygen levels and pressures than the CO2 series. Treat the helium "
        "trend as uncertain, not as evidence that helium suppresses or sustains a flame.",
        kind="info")
elif xcol == "co2_pct":
    ui.callout(
        "CO2 and helium were never combined",
        "No FLEX test contains both diluents, so nothing here says what a CO2 + He mixture would do.",
        kind="info")
ui.source(
    f"{SRC}. The dotted trend is a one-variable logistic fit per fuel; pressure, droplet size and the other "
    "gases also vary between tests, so it describes these tests and is not a causal effect", flex.PDF_URL)

# ------------------------------------------------------------------ burning rate + donut
ui.rule()
left, right = st.columns([3, 2], gap="large")
with left:
    ui.section(
        "How fast did the droplet burn?",
        "Average burning-rate constant K for each test. There is no single K for a fuel: it moves with "
        "droplet size, oxygen and diluent.", level=3)
    kx = st.selectbox("Plot K against", ["d0_mm", "o2_pct", "co2_pct", "he_pct", "pressure_atm"],
                      format_func=lambda c: charts.AXIS_LABEL[c])
    ui.plotly(charts.burning_rate_figure(d, kx), key="k")
    drawn = int(d.dropna(subset=["burning_rate_mm2_s", kx]).shape[0])
    ui.source(
        f"{SRC}. K is the report's linear fit of D² against time from shortly after ignition to extinction. "
        f"{drawn} of {n} filtered tests drawn; the rest have no K or no x value in the source and are left out, "
        "not set to zero", flex.PDF_URL)
with right:
    ui.section("How did the tests end?", "The three outcomes are never merged.", level=3)
    ui.plotly(charts.outcome_donut(d), key="donut")
    ui.source(f"{SRC}. Disruption is not Extinction: {flex.REPORT} §5.2 links minor disruptions to needle "
              "coating contamination", flex.PDF_URL)

# ------------------------------------------------------------------ single test
ui.rule()
ui.section(
    "One test, start to finish",
    "Pick a test to see its droplet shrink. The line is rebuilt from three printed numbers; it is not the measured trace.",
)
pick = st.selectbox("Test", d["test_id"].tolist(), index=0, help="Type a test number to search.")
row = d.set_index("test_id").loc[pick]
a, b = st.columns([3, 2], gap="large")
with a:
    fig = charts.d2_reconstruction(row)
    if fig is None:
        missing = [lab for col, lab in [("d0_mm", "initial diameter"), ("burning_rate_mm2_s", "burning rate"),
                                        ("burn_time_s", "burn time")] if pd.isna(row[col])]
        ui.no_data(f"{pick} cannot be drawn",
                   f"Table IX prints no {', '.join(missing)} for this test, and a missing value is not filled in.")
    else:
        ui.plotly(fig, key="d2")
with b:
    cool = {"indicated": ("cool-flame evidence reported", "warn"), "not_indicated": ("no cool-flame evidence", "info"),
            "unclear": ("cool flame unclear", "mute")}.get(row["cool_flame_label"])
    badges = ui.badge(row["outcome"], ui.OUTCOME_BADGE[row["outcome"]])
    if cool:
        badges += ui.badge(*cool)
    if row["support"]:
        badges += ui.badge(row["support"], "mute")
    st.markdown(badges, unsafe_allow_html=True)
    st.markdown(
        '<div class="ff-kv">'
        f'<div class="k">Fuel</div><div>{"n-Heptane" if row["fuel"] == "Heptane" else "Methanol"}</div>'
        f'<div class="k">Date</div><div class="ff-mono">{row["date_iso"]}</div>'
        f'<div class="k">Atmosphere</div><div class="ff-mono">O2 {row["o2"]:.2f} · N2 {row["n2"]:.2f} · '
        f'CO2 {row["co2"]:.2f} · He {row["he"]:.2f}</div>'
        f'<div class="k">Pressure</div><div class="ff-mono">{ui.fmt(row["pressure_mmhg"], 1, "mmHg")} '
        f'({ui.fmt(row["pressure_atm"], 2, "atm")})</div>'
        f'<div class="k">D0</div><div class="ff-mono">{ui.fmt(row["d0_mm"], 2, "mm")}</div>'
        f'<div class="k">{charts.end_diameter_label(row["outcome"])}</div>'
        f'<div class="ff-mono">{ui.fmt(row["extinction_diameter_mm"], 2, "mm")}</div>'
        f'<div class="k">K</div><div class="ff-mono">{ui.fmt(row["burning_rate_mm2_s"], 2, "mm²/s")}</div>'
        f'<div class="k">Burn time</div><div class="ff-mono">{ui.fmt(row["burn_time_s"], 1, "s")}</div>'
        "</div>", unsafe_allow_html=True)
    if row["cool_flame_quote"]:
        st.markdown(f"> {ui.esc(row['cool_flame_quote'])}")
        st.caption(f"{flex.REPORT}, Appendix B, Figure {int(row['caption_figure'])} caption.")
    if row["notes"]:
        st.caption(f"Cleaning note: {row['notes']}")
    if row["caption_atmosphere_differs"]:
        st.caption(f"The report's figure caption words this atmosphere as {row['caption_atmosphere']}; "
                   f"Table IX prints {flex.table_atmosphere(row)}. Table IX is used.")
fig_ref = f"; measured trace: Appendix B, Figure {int(row['caption_figure'])}" if pd.notna(row["caption_figure"]) else ""
ui.source(f"{row['source']}{fig_ref}. Line = D0² − K·t over the printed burn time (d²-law reconstruction)", flex.PDF_URL)

# ------------------------------------------------------------------ table
ui.rule()
ui.section("Every matching test", "Sortable. Empty cells are empty in the source and stay empty here.")
table = d[["test_no", "test_id", "cir_id", "date_iso", "fuel", "pressure_mmhg", "o2", "n2", "co2", "he", "d0_mm",
           "extinction_diameter_mm", "burning_rate_mm2_s", "burn_time_s", "outcome", "cool_flame_label",
           "support", "notes", "source"]]
st.dataframe(
    table, hide_index=True, width="stretch", height=420,
    column_config={
        "test_no": st.column_config.NumberColumn("No.", width="small"),
        "test_id": st.column_config.TextColumn("Test", pinned=True),
        "cir_id": "CIR identifier",
        "date_iso": "Date",
        "fuel": "Fuel",
        "pressure_mmhg": st.column_config.NumberColumn("Pressure, mmHg", format="%.1f"),
        "o2": st.column_config.NumberColumn("O2", format="%.2f"),
        "n2": st.column_config.NumberColumn("N2", format="%.2f"),
        "co2": st.column_config.NumberColumn("CO2", format="%.2f"),
        "he": st.column_config.NumberColumn("He", format="%.2f"),
        "d0_mm": st.column_config.NumberColumn("D0, mm", format="%.2f"),
        "extinction_diameter_mm": st.column_config.NumberColumn(
            "End diameter, mm", format="%.2f",
            help="The value Table IX prints in its extinction-diameter column. It is an extinction diameter "
                 "only when the outcome is Extinction; 24 Disruption and 15 Completion rows also print one."),
        "burning_rate_mm2_s": st.column_config.NumberColumn("K, mm²/s", format="%.2f"),
        "burn_time_s": st.column_config.NumberColumn("Burn time, s", format="%.1f"),
        "outcome": "Outcome",
        "cool_flame_label": st.column_config.TextColumn("Cool flame (caption)",
                                                        help="From the Appendix B caption; blank = caption silent."),
        "support": "Support",
        "notes": st.column_config.TextColumn("Cleaning note", width="medium"),
        "source": st.column_config.TextColumn("Source", width="large"),
    })
st.download_button("Download these rows (CSV)", table.to_csv(index=False).encode("utf-8"),
                   file_name="flex_table_ix_filtered.csv", mime="text/csv")
ui.source(
    f"{flex.REPORT_TITLE}. Gas columns are mole fractions as printed; "
    f"{len(flex.summary()['gas_sum_not_1'])} rows do not sum to exactly 1.00 because the source prints two decimals",
    flex.RECORD_URL)
