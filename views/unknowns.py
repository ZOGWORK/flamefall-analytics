"""What We Don't Know: the gaps in the data, and the fires a crew cannot see."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from flamefall import catalogue as cat
from flamefall import flex, psi, theme, ui

ev = cat.load_evidence().set_index("id")
f = flex.load_flex()
s = flex.summary()
solid = cat.load_solid_points()
decided = solid[solid["outcome"] != "ambiguous"]


def cite(eid: str) -> None:
    e = ev.loc[eid]
    ui.source(f"{e['source_ref']} · read: {e['read_level']}", e["source_url"], verification=e["verification"])


def statement(eid: str) -> None:
    e = ev.loc[eid]
    grey = ' class="ff-unverified"' if e["verification"] == "unverified" else ""
    st.markdown(f'<p{grey} style="margin:0.4rem 0 0.2rem">{ui.esc(e["statement"])}</p>', unsafe_allow_html=True)
    cite(eid)


ui.kicker("Honest limits")
st.title("What We Don't Know")
st.markdown(
    '<p class="ff-lede">A dashboard that only shows what was measured hides the most useful fact: where the '
    "measurements stop. This page lists the gaps, then the kinds of burning a crew or a sensor can miss.</p>",
    unsafe_allow_html=True)

# =========================================================================== gaps
ui.section("The gaps", "Three places where the question is asked and no test exists to answer it.")

# ---- 1. partial gravity
st.markdown("### 1 · Partial gravity")
ui.no_data("No lunar- or Martian-gravity combustion dataset is in the repository",
           "Every flight investigation in the catalogue ran in microgravity. Fire on the Moon or Mars has to be "
           "bracketed from microgravity and normal-gravity results, plus the few short tests below.",
           "Official challenge brief, Flame in Freefall.")
pg = pd.DataFrame([
    dict(what="LUCI: SIBAL fabric, downward", lunar=0.92, earth=1.5, unit="mm/s (flame base)"),
    dict(what="LUCI: SIBAL fabric, flame tip", lunar=1.1, earth=2.8, unit="mm/s"),
    dict(what="LUCI: 4-mm PMMA rod, upward tip", lunar=1.5, earth=4.0, unit="mm/s"),
])
fig = go.Figure()
fig.add_trace(go.Bar(y=pg["what"], x=pg["lunar"], name="Simulated lunar gravity", orientation="h", marker_color=theme.VIOLET,
                     hovertemplate="%{y}<br>%{x} mm/s in simulated lunar gravity<extra></extra>"))
fig.add_trace(go.Bar(y=pg["what"], x=pg["earth"], name="Normal gravity, same hardware", orientation="h", marker_color=theme.GREY,
                     hovertemplate="%{y}<br>%{x} mm/s in normal gravity<extra></extra>"))
fig.update_layout(barmode="group", height=280, xaxis_title="Flame spread rate, mm/s", margin=dict(l=230))
a, b = st.columns([3, 2], gap="large")
with a:
    st.markdown("**The nearest real tests: one suborbital flight, preliminary slides**")
    ui.plotly(fig, key="luci")
    ui.source("Ferkul et al., ASGSR 2025 presentation, slides 19, 21, 33, 36 (NTRS 20250010653). "
              "A conference presentation, not peer reviewed, not a repository dataset",
              "https://ntrs.nasa.gov/citations/20250010653", verification="verified_live")
with b:
    ui.callout("Read these three bars with care",
               "Lunar gravity was created by spinning the capsule at 11 RPM, so Coriolis force bends the flames. It is one "
               "flight, about two and a half minutes, in air at normal pressure, with two samples sharing one chamber. "
               "Both samples spread more slowly than in normal gravity, yet the fabric kept burning about 45 s longer.",
               "info")
    statement("lunar-g-centrifuge-delta")
st.markdown(
    "> Spread rate vs gravity is non-monotonic in the models and in low-conductivity-core wire tests, with a maximum "
    "and a minimum flammability O2 near lunar gravity; thin-cellulose KC-135 data at 0.2–0.4 atm are monotonic in g "
    "over 0.1–1 g. The peak location is material-, geometry- and pressure-dependent and is not yet fixed by a "
    "lunar-surface measurement — that is what FM2 is for.")
x, y = st.columns(2, gap="large")
with x:
    statement("partial-g-kc135")
    statement("partial-g-wires")
    statement("buoyant-velocity-unknown")
with y:
    statement("fm2-plan")
    statement("luci-method")
    statement("buoyant-velocity-ices2019")

# ---- 2. oxygen above the tested range for solids
ui.rule()
st.markdown("### 2 · Solid materials above the tested oxygen range")
env = cat.solid_envelope()
top = decided.sort_values("o2_at_outcome_pct", ascending=False).head(6)
fig = go.Figure()
for outcome, color in [("sustained", theme.FLAME), ("quenched", theme.CYAN), ("blowoff", theme.VIOLET), ("no_ignition", theme.GREY)]:
    d = decided[decided["outcome"] == outcome]
    fig.add_trace(go.Scatter(
        x=d["o2_at_outcome_pct"], y=d["pressure_kPa"], mode="markers", name=outcome.replace("_", " "),
        marker=dict(color=color, size=9, opacity=0.75, line=dict(color=theme.BG, width=0.5)),
        customdata=d[["investigation_id", "test_no", "material_class", "flow_cm_s"]].astype(object).fillna("n/a").to_numpy(),
        hovertemplate="%{customdata[0]} %{customdata[1]} · %{customdata[2]}<br>O2 %{x:.1f}% at %{y:.1f} kPa · flow %{customdata[3]} cm/s<extra></extra>"))
fig.add_vrect(x0=34, x1=42, fillcolor="#2A3644", opacity=0.55, line_width=0)
fig.add_annotation(x=38, y=85, text="NO DATA<br>above 34% O2", showarrow=False, font=dict(color=theme.TEXT, family=theme.MONO, size=13))
fig.add_shape(type="rect", x0=30, x1=42, y0=40, y1=70.3, line=dict(color=theme.AMBER, dash="dot"), fillcolor="rgba(245,158,11,0.06)")
fig.add_annotation(x=36, y=46, text="expected Moon-base and rover atmospheres:<br>30% O2 or more, 70.3 kPa or less", showarrow=False,
                   font=dict(color=theme.AMBER, size=11))
fig.update_layout(xaxis_title="Ambient O2 at the outcome, % by volume", yaxis_title="Pressure, kPa", height=430,
                  xaxis=dict(range=[12, 42]), yaxis=dict(range=[40, 115]))
ui.plotly(fig, key="solid-envelope")
ui.source(f"{len(decided)} solid-fuel test points with a stated outcome: NASA/TM-20210011385 (BASS-II), PSI-98 and PSI-99 tables, "
          "ICES-2024-365, ICES-2025-156, NTRS 20240007628. Solid fuels only; droplet and gas tests are not on this chart",
          "https://ntrs.nasa.gov/citations/20210011385")
ui.no_data(
    "No solid-material test point above 34% oxygen, and only a handful inside the exploration box",
    f"The highest oxygen level with a recorded outcome is {env['o2'][1]:.1f}% (a Nomex sample that did not ignite); the "
    f"highest with a sustained flame is {env['sustained_o2_max']:.1f}%. Only the Saffire V and VI samples sit at reduced "
    "pressure. One later experiment reports a tested range up to 34% O2 and down to 0.15 atm, but its individual points "
    "above 21% are not published in a table.",
    "Spacesuits use 100% oxygen at 4.3 psi; nothing in this data set speaks to that condition.")
statement("sofie-gel-envelope")
statement("saffire-vi-partial-pressure")

# ---- 3. CO2 + He
ui.rule()
st.markdown("### 3 · Carbon dioxide and helium together")
both = int(((f["co2"] > 0) & (f["he"] > 0)).sum())
fig = go.Figure()
for fuel, color in theme.FUEL_COLORS.items():
    d = f[f["fuel"] == fuel]
    fig.add_trace(go.Scatter(x=d["co2_pct"], y=d["he_pct"], mode="markers", name=fuel if fuel != "Heptane" else "n-Heptane",
                             marker=dict(color=color, size=9, opacity=0.55),
                             customdata=d[["test_id", "o2_pct"]].to_numpy(),
                             hovertemplate="%{customdata[0]} · O2 %{customdata[1]:.0f}%<br>CO2 %{x:.0f}% · He %{y:.0f}%<extra></extra>"))
fig.add_shape(type="rect", x0=2.5, x1=72, y0=2.5, y1=47, fillcolor="#2A3644", opacity=0.5, line_width=0)
fig.add_annotation(x=37, y=25, text=f"NO DATA<br>{both} of {len(f)} tests contain both gases", showarrow=False,
                   font=dict(color=theme.TEXT, family=theme.MONO, size=13))
fig.update_layout(xaxis_title="CO2 in the atmosphere, mol %", yaxis_title="Helium in the atmosphere, mol %", height=380)
ui.plotly(fig, key="co2he")
ui.source(f"{flex.REPORT}, Table IX: CO2 present in {s['co2_tests']} tests, helium in {s['he_tests']}, both in {both}", flex.PDF_URL)
st.markdown("Every FLEX test lies on one of the two axes. Whether the two diluents help, hinder or ignore each other was never tested, "
            "and helium's own effect on extinction is unclear with only "
            f"{s['he_tests']} tests.")

# ---- smaller gaps
ui.rule()
st.markdown("### Other gaps found while checking sources")
gaps = pd.DataFrame([
    dict(Gap="A smoke-detection delay in microgravity compared with normal gravity, in seconds",
         Status="No published number. The SAME report says lags are longer and gives none; Saffire gives absolute microgravity times only.",
         Source="SAME Final Report abstract; ICES-2024-365; ICES-2026-577"),
    dict(Gap="Cool-flame burning rates for n-heptane",
         Status="No open table. Hot and cool rates are published for n-decane and n-octane only; Table IX gives hot-flame rates.",
         Source="NTRS 20140006750; NASA/TP-2015-216046"),
    dict(Gap="One-step cool-flame kinetic parameters fitted to FLEX (2012)",
         Status="Not openly available. A later six-step model is open and is cited instead.",
         Source="Williams and Nayagam 2019 (open copy)"),
    dict(Gap="Numeric extinction or dilution limits for coflow and spherical gas flames",
         Status="Qualitative statements only in every open source read.",
         Source="ACME overview, JASMAC-33 (NTRS 20210022542)"),
    dict(Gap="BASS-II extinction velocities for most rod and film tests",
         Status="Recorded as fan settings; the memo prints no conversion to cm/s, so 100 of 290 test points have no velocity.",
         Source="NASA/TM-20210011385, Appendix A"),
    dict(Gap="Numbers that appear only in the 2019 BASS-II conference paper",
         Status="Not re-read: the repository blocks automated access. Shown greyed wherever they appear.",
         Source="ICES-2019-101"),
])
st.dataframe(gaps, hide_index=True, width="stretch",
             column_config={c: st.column_config.TextColumn(width="large") for c in ["Gap", "Status"]})

# =========================================================================== what you can't see
ui.rule()
ui.section("What you can't see", "Three ways a fire can be burning with nothing obvious to look at.")

st.markdown("### Cool flames after the visible flame is gone")
c = s["cool_flame"]
labels = ["Cool-flame evidence", "No evidence", "Unclear", "Caption silent"]
values = [c["indicated"], c["not_indicated"], c["unclear"], c[""]]
fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=[theme.AMBER, theme.CYAN, theme.GREY, "#3A4756"],
                       text=values, textposition="outside", textfont=dict(family=theme.MONO),
                       hovertemplate="%{y}: %{x} tests<extra></extra>"))
fig.update_layout(height=250, xaxis_title=f"n-Heptane tests logged as Extinction (n = {s['heptane_extinctions']})",
                  yaxis=dict(autorange="reversed"), margin=dict(l=150))
a, b = st.columns([3, 2], gap="large")
with a:
    ui.plotly(fig, key="cool")
    ui.source(f"{flex.REPORT}, Appendix B figure captions: the authors' reading of continued vaporisation and a vapour "
              "cloud after the visible flame vanished. No methanol caption mentions a cool flame", flex.PDF_URL)
with b:
    ui.callout("“Extinction” in the table means the visible flame",
               f"In {c['indicated']} of {s['heptane_extinctions']} n-heptane tests the droplet kept vaporising after the "
               "flame disappeared. A sensor or a rule that equates “no visible flame” with “fire out” is wrong for these.",
               "danger")
    statement("cfig-cool-flames-psi")
statement("flex-k-hot-cool")

ui.rule()
st.markdown("### Dim blue flames at low flow")
ui.callout("Near its limit a flame shrinks, turns blue and can sit on the fuel for minutes",
           "In the solid-fuel tests, quenching at very low flow is described as the flame shrinking to a hemispherical "
           "blue flame that oscillates before going out. In still gas at raised oxygen, small burner flames emulating "
           "solid materials burned for minutes.",
           "", "Sources below.")
x, y = st.columns(2, gap="large")
with x:
    st.markdown("> the flame shrinks to a hemispherical blue flame and oscillates with increasing amplitude just before going out")
    ui.source("NASA/TM-20210011385 §6.1.1 (report p. 64)", "https://ntrs.nasa.gov/citations/20210011385",
              verification="verified_live")
with y:
    statement("bre-21pct-out")
    statement("bre-25pct")

ui.rule()
st.markdown("### Smoke too fine for the detector")
t1 = pd.DataFrame({
    "Material": ["Kapton", "Teflon", "Lamp wick (cellulose)", "Silicone rubber"],
    "Unaged": [80, 170, 186, 189], "Aged 720 s": [155, 228, 258, 352]})
t2 = pd.DataFrame({
    "Material": ["Kapton", "Teflon", "Lamp wick (cellulose)", "Silicone rubber", "Pyrell"],
    "Unaged": [42, 81, 90, 128, 149], "Aged 720 s": [89, 70, 229, 269, 293]})


def smoke_fig(t: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=t["Material"], y=t["Unaged"], name="Fresh smoke", marker_color=theme.CYAN,
                         hovertemplate="%{x}: %{y} nm fresh<extra></extra>"))
    fig.add_trace(go.Bar(x=t["Material"], y=t["Aged 720 s"], name="After 720 s", marker_color=theme.FLAME,
                         hovertemplate="%{x}: %{y} nm after 720 s<extra></extra>"))
    fig.add_hline(y=500, line=dict(color=theme.RED, dash="dot"), annotation_text="500 nm", annotation_font_color=theme.RED)
    fig.update_layout(barmode="group", height=340, yaxis_title="Geometric mean diameter, nm", yaxis=dict(range=[0, 560]))
    return fig


tab1, tab2 = st.tabs(["First flight (SAME)", "Reflight (SAME-R)"])
with tab1:
    ui.plotly(smoke_fig(t1), key="same1")
    cite("same1-table1")
with tab2:
    ui.plotly(smoke_fig(t2), key="same2")
    cite("samer-table1")
st.caption("The two flights used different hardware and diagnostics and their values differ by about a factor of two. "
           "They are shown on separate tabs and are never averaged.")
x, y = st.columns(2, gap="large")
with x:
    statement("same-detector-misses")
    statement("same1-lag-qualitative")
with y:
    statement("saffire-alarm-981")
    statement("saffire-2026-alarm")

ui.rule()
st.markdown("### An oxygen figure that is not a cabin atmosphere")
statement("inverse-flame-85")
st.caption("This is why every oxygen value in the data carries an ambient-or-burner flag, and why burner-feed values are "
           "kept off every ambient-oxygen axis in this dashboard.")
ui.source("PSI inverse-flame tables for PSI-159 and PSI-10", psi.record_url("PSI-159"))
