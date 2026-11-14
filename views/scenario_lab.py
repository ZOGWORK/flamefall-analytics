"""Scenario Lab: dial a scenario, see the nearest real tests, and see exactly where the data stops."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from flamefall import catalogue as cat
from flamefall import flex, model, ranking, ui

KPA_PER_PSI = 6.894757
MATERIALS = {
    "PMMA (acrylic)": ("solid", "PMMA"),
    "Cotton / fibreglass fabric (SIBAL)": ("solid", "SIBAL-cotton"),
    "Nomex fabric": ("solid", "Nomex"),
    "Silicone sheet": ("solid", "silicone"),
    "n-Heptane droplet": ("droplet", "Heptane"),
    "Methanol droplet": ("droplet", "Methanol"),
}
GRAVITY = {"0 g (orbit)": 0.0, "Lunar, 0.16 g": 0.16, "Mars, 0.38 g": 0.38, "Earth, 1 g": 1.0}
FEATURED = {
    "Lunar-base cabin": dict(material="Cotton / fibreglass fabric (SIBAL)", o2=34.0, p=56.5, flow=5.0, g="Lunar, 0.16 g",
                             note="30% O2 or more at 10.2 psi or less, low ventilation, a fabric."),
    "Pressurised rover": dict(material="PMMA (acrylic)", o2=30.0, p=70.3, flow=20.0, g="Lunar, 0.16 g",
                              note="Elevated oxygen at 10.2 psi with the cabin fan running, an acrylic panel."),
    "Large fire in a vehicle": dict(material="Cotton / fibreglass fabric (SIBAL)", o2=31.0, p=54.1, flow=20.0, g="0 g (orbit)",
                                    note="The Saffire VI atmosphere: a 50 cm fabric sheet in a 16.7 m3 cargo vehicle."),
    "Station cabin": dict(material="PMMA (acrylic)", o2=21.0, p=101.3, flow=10.0, g="0 g (orbit)",
                          note="Sea-level air in orbit, for comparison."),
}


@st.cache_resource(show_spinner=False)
def fitted(name: str) -> model.Fitted:
    return model.Fitted(name)


ui.kicker("Interactive · estimates, never verdicts")
st.title("Scenario Lab")
st.markdown(
    '<p class="ff-lede">Set an atmosphere, a material, a ventilation flow and a gravity level. The lab answers with '
    "the nearest tests that were actually run, an estimate where a validated model exists, and a plain "
    "“no data” where nothing was measured.</p>", unsafe_allow_html=True)

# ------------------------------------------------------------------ inputs
st.markdown("#### Start from a featured scenario")
cols = st.columns(len(FEATURED))
for col, (name, preset) in zip(cols, FEATURED.items()):
    if col.button(name, width="stretch", help=preset["note"]):
        st.session_state.update(sl_material=preset["material"], sl_o2=preset["o2"], sl_p=preset["p"],
                                sl_flow=preset["flow"], sl_g=preset["g"])
for key, default in dict(sl_material="PMMA (acrylic)", sl_o2=21.0, sl_p=101.3, sl_flow=10.0, sl_g="0 g (orbit)").items():
    st.session_state.setdefault(key, default)

a, b = st.columns(2, gap="large")
with a:
    material_label = st.selectbox("Fuel or material", list(MATERIALS), key="sl_material")
    o2 = st.slider("Oxygen, % by volume", 10.0, 60.0, step=0.5, key="sl_o2")
    pressure = st.slider("Pressure, kPa", 20.0, 310.0, step=0.1, key="sl_p",
                         help="101.3 kPa = 14.7 psi (sea level). 70.3 kPa = 10.2 psi. 56.5 kPa = 8.2 psi.")
with b:
    flow = st.slider("Ventilation flow, cm/s", 0.0, 80.0, step=0.5, key="sl_flow")
    g_label = st.radio("Gravity", list(GRAVITY), horizontal=True, key="sl_g")
    kind, mat = MATERIALS[material_label]
    co2 = he = 0.0
    d0 = None
    if kind == "droplet":
        d1, d2, d3 = st.columns(3)
        co2 = d1.number_input("CO2, %", 0.0, 80.0, 0.0, step=5.0)
        he = d2.number_input("Helium, %", 0.0, 80.0, 0.0, step=5.0)
        d0 = d3.number_input("Droplet diameter, mm", 0.5, 8.0, 3.0, step=0.1)
g = GRAVITY[g_label]
po2 = o2 / 100 * pressure

ui.stat_cards([
    dict(value=f"{po2:.1f}", unit="kPa", label="oxygen partial pressure",
         source=f"{o2:g}% × {pressure:g} kPa · sea-level air is 21.2 kPa", tone="amber"),
    dict(value=f"{pressure / KPA_PER_PSI:.1f}", unit="psi", label="total pressure",
         source=f"{pressure:g} kPa = {pressure / 101.325:.2f} atm", tone="cyan"),
    dict(value=f"{flow:g}", unit="cm/s", label="ventilation flow",
         source="still gas" if flow == 0 else "forced flow past the fuel", tone="cyan"),
    dict(value=f"{g:g} g", label="gravity", source=g_label, tone="violet" if g not in (0.0,) else "green"),
])

# ------------------------------------------------------------------ gravity gate
gaps: list[str] = []
if g in (0.16, 0.38):
    ui.rule()
    ui.no_data(
        f"No combustion test at {g_label.split(',')[0]} gravity exists in the PSI repository",
        "Everything below is from microgravity. Nothing here is scaled, interpolated or adjusted for gravity. "
        "The closest real evidence for partial gravity is listed next; none of it is a repository dataset.",
        "Official challenge brief: “there is currently no partial-gravity combustion data available in PSI.”")
    pg = cat.load_evidence()
    pg = pg[(pg["evidence_class"] == "partial_g") & pg["investigation_id"].isin(
        ["LUCI", "Lunar-g drop-tower centrifuge", "KC-135 partial-gravity flights", "Parabolic-flight wire tests", "FM2"])]
    for _, e in pg.iterrows():
        st.markdown(
            f'<p style="margin:0.5rem 0 0.1rem"><b>{ui.esc(e["investigation_id"])}</b> · {ui.esc(e["statement"])}</p>'
            f'<div class="ff-src" style="margin-bottom:0.3rem">{ui.verification_badge(e["verification"])}'
            f'{ui.esc(e["source_ref"])} · read: {ui.esc(e["read_level"])} · '
            f'<a href="{ui.esc(e["source_url"])}" target="_blank" rel="noopener">open source</a></div>',
            unsafe_allow_html=True)
    st.markdown(
        "> Spread rate vs gravity is non-monotonic in the models and in low-conductivity-core wire tests, with a "
        "maximum and a minimum flammability O2 near lunar gravity; thin-cellulose KC-135 data at 0.2–0.4 atm are "
        "monotonic in g over 0.1–1 g. The peak location is material-, geometry- and pressure-dependent and is not "
        "yet fixed by a lunar-surface measurement — that is what FM2 is for.")
    gaps.append(f"gravity: no repository test at {g:g} g")
elif g == 1.0:
    ui.rule()
    ui.no_data("Normal-gravity tests are not part of this dataset",
               "The data here are microgravity experiments. Normal-gravity values appear only where a source quotes "
               "one for comparison, so the nearest tests below are microgravity tests.")
    gaps.append("gravity: the data are microgravity tests")

# ------------------------------------------------------------------ nearest real tests + envelope
ui.rule()
if kind == "droplet":
    ui.section("Nearest real tests", f"The eight FLEX {material_label.lower()} burns closest to this atmosphere and droplet size.")
    near = cat.nearest_flex(mat, o2, pressure, co2, he, d0)
    st.dataframe(
        near[["test_id", "o2_pct", "co2_pct", "he_pct", "pressure_kpa", "d0_mm", "burning_rate_mm2_s", "outcome",
              "cool_flame_label", "distance", "source"]],
        hide_index=True, width="stretch",
        column_config={"test_id": "Test", "o2_pct": st.column_config.NumberColumn("O2, %", format="%.0f"),
                       "co2_pct": st.column_config.NumberColumn("CO2, %", format="%.0f"),
                       "he_pct": st.column_config.NumberColumn("He, %", format="%.0f"),
                       "pressure_kpa": st.column_config.NumberColumn("Pressure, kPa", format="%.1f"),
                       "d0_mm": st.column_config.NumberColumn("D0, mm", format="%.2f"),
                       "burning_rate_mm2_s": st.column_config.NumberColumn("K, mm²/s", format="%.2f"),
                       "outcome": "Outcome", "cool_flame_label": "Cool flame (caption)",
                       "distance": st.column_config.NumberColumn("Distance", format="%.2f",
                                                                 help="0 = identical conditions. Scaled: 5 points of O2, 50 kPa, 15 points of CO2, 10 of helium, 0.8 mm each count as 1."),
                       "source": st.column_config.TextColumn("Source", width="large")})
    ui.source(f"{flex.REPORT}, Table IX; cool-flame column from Appendix B captions", flex.PDF_URL)
    f = flex.load_flex()
    f = f[f["fuel"] == mat]
    if not (f["o2_pct"].min() <= o2 <= f["o2_pct"].max()):
        gaps.append(f"oxygen: FLEX {mat.lower()} tests cover {f['o2_pct'].min():.0f} to {f['o2_pct'].max():.0f}%")
    if not (f["pressure_kpa"].min() <= pressure <= f["pressure_kpa"].max()):
        gaps.append(f"pressure: FLEX {mat.lower()} tests cover {f['pressure_kpa'].min():.0f} to {f['pressure_kpa'].max():.0f} kPa")
    if co2 > 0 and he > 0:
        gaps.append("CO2 and helium together: never combined in any FLEX test")
    if co2 > f["co2_pct"].max():
        gaps.append(f"CO2: tested up to {f['co2_pct'].max():.0f}%")
    if he > f["he_pct"].max():
        gaps.append(f"helium: tested up to {f['he_pct'].max():.0f}%")
    if flow > 0:
        gaps.append("ventilation flow: every FLEX droplet burned in still gas")
    if d0 is not None and not (f["d0_mm"].min() <= d0 <= f["d0_mm"].max()):
        gaps.append(f"droplet size: tested from {f['d0_mm'].min():.2f} to {f['d0_mm'].max():.2f} mm")
else:
    ui.section("Nearest real tests",
               "The eight solid-fuel test points closest to this oxygen level, pressure and flow, same material first.")
    near = cat.nearest_solid(mat, o2, pressure, flow)
    if not near["same_material"].all():
        st.caption(f"Fewer than three {material_label} test points have a stated outcome, so other materials are included and marked.")
    st.dataframe(
        near[["investigation_id", "test_no", "material_verbatim", "o2_at_outcome_pct", "pressure_kPa", "flow_cm_s",
              "flow_direction", "outcome", "distance", "same_material", "outcome_quote", "source_ref"]],
        hide_index=True, width="stretch",
        column_config={"investigation_id": "Investigation", "test_no": "Test", "material_verbatim": "Material (as printed)",
                       "o2_at_outcome_pct": st.column_config.NumberColumn("O2, %", format="%.1f"),
                       "pressure_kPa": st.column_config.NumberColumn("Pressure, kPa", format="%.1f"),
                       "flow_cm_s": st.column_config.NumberColumn("Flow, cm/s", format="%.1f"),
                       "flow_direction": "Flow direction", "outcome": "Outcome",
                       "distance": st.column_config.NumberColumn("Distance", format="%.2f",
                                                                 help="0 = identical conditions. Scaled: 2 points of O2, 30 kPa, and a factor of e in flow each count as 1."),
                       "same_material": st.column_config.CheckboxColumn("Same material"),
                       "outcome_quote": st.column_config.TextColumn("What the source says", width="large"),
                       "source_ref": st.column_config.TextColumn("Source", width="large")})
    ui.source("BASS-II summary memo NASA/TM-20210011385 (Tables 5.1, 7.1, A.1 to A.6); PSI Saffire tables; "
              "ICES-2024-365; NTRS 20240007628", "https://ntrs.nasa.gov/citations/20210011385")
    env_m, env_all = cat.solid_envelope(mat), cat.solid_envelope()
    if env_m["n"] == 0:
        gaps.append(f"material: no {material_label} test point with a stated outcome")
    else:
        if not (env_m["o2"][0] <= o2 <= env_m["o2"][1]):
            gaps.append(f"oxygen: {material_label} was tested from {env_m['o2'][0]:.1f} to {env_m['o2'][1]:.1f}%")
        if not (env_m["pressure"][0] - 1 <= pressure <= env_m["pressure"][1] + 1):
            gaps.append(f"pressure: {material_label} was tested from {env_m['pressure'][0]:.0f} to {env_m['pressure'][1]:.0f} kPa")
        if flow > env_m["flow"][1]:
            gaps.append(f"flow: {material_label} was tested up to {env_m['flow'][1]:.0f} cm/s")
    if o2 > 34:
        gaps.append("oxygen above 34%: no solid-material test point exists at any pressure "
                    f"(highest with a stated outcome: {env_all['o2'][1]:.1f}%)")

# ------------------------------------------------------------------ model estimate
ui.rule()
ui.section("Model estimate", "A probability from a small logistic model, shown only where that model passed validation.")
if g != 0.0:
    ui.no_data("No estimate at this gravity", "Both models were trained on microgravity tests only. They are not applied to other gravity levels.")
elif kind == "droplet":
    with st.spinner("Scoring the scenario against 1,000 bootstrap models…"):
        fm = fitted("droplet_extinction")
        x = dict(o2_pct=o2, pressure_kpa=pressure, o2_partial_kpa=po2, co2_pct=co2, he_pct=he, d0_mm=d0,
                 fuel_heptane=1.0 if mat == "Heptane" else 0.0)
        out = fm.predict(x)
    m = fm.r["metrics"]
    thr = m["youden_threshold"]
    demo = out["extrapolating"] or bool(gaps)
    ui.stat_cards([
        dict(value=f"{out['p']:.0%}", label="estimated chance the visible flame goes out",
             source=f"95% interval {out['lo']:.0%} to {out['hi']:.0%} (cluster bootstrap)" + (" · DEMO: extrapolated" if demo else ""),
             tone="grey" if demo else "red"),
        dict(value="above" if out["p"] >= thr else "below",
             label=f"the decision threshold of {thr:.2f}",
             source="Youden's J threshold on out-of-fold predictions; this dashboard uses it and says so", tone="cyan"),
        dict(value=f"{out['nn_distance']:.2f}", label="distance to the nearest training test",
             source=f"typical {out['train_nn_median']:.2f}; 95% of training tests are within {out['train_nn_p95']:.2f} of another",
             tone="grey" if out["far_from_data"] else "green"),
        dict(value=f"{fm.r['headline_auc']:.2f}", label="headline AUC of this model",
             source=f"worse of grouped CV ({m['roc_auc']:.2f}) and leave-one-fuel-out; false-positive rate {m['confusion_at_youden']['false_positive_rate']:.0%}",
             tone="amber"),
    ])
    if demo:
        why = [f"{o['feature']} = {o['value']:g} is outside the tested {o['tested_min']:.3g} to {o['tested_max']:.3g}"
               for o in out["outside_envelope"]]
        if out["far_from_data"]:
            why.append("the scenario is farther from every training test than 95% of training tests are from each other")
        ui.callout("DEMO estimate: this scenario is outside what the model has seen",
                   "Treat the number above as an illustration of the model's shape, not as a prediction. "
                   + ("Reasons: " + "; ".join(why + gaps) + "." if (why or gaps) else ""), "danger")
    st.caption("“Flame goes out” means the visible flame. It includes radiative extinctions after which a cool flame "
               "can keep burning, and it does not include disruptions.")
    if mat == "Heptane":
        fc = fitted("droplet_cool_flame")
        oc = fc.predict(dict(o2_pct=o2, pressure_kpa=pressure, o2_partial_kpa=po2, co2_pct=co2, he_pct=he, d0_mm=d0))
        s = flex.summary()
        ui.callout(
            "If the visible flame goes out, is the fire out?",
            f"Not necessarily. In {s['cool_flame']['indicated']} of the {s['heptane_extinctions']} n-heptane tests logged "
            "as Extinction, the report describes evidence of cool-flame burning afterwards. An exploratory model on the "
            f"{fc.r['n_rows']} labelled tests puts the chance of cool-flame evidence for this scenario at {oc['p']:.0%} "
            f"(95% interval {oc['lo']:.0%} to {oc['hi']:.0%}; grouped-CV AUC {fc.r['metrics']['roc_auc']:.2f} with an "
            f"interval of {fc.r['metrics']['roc_auc_ci'][0]:.2f} to {fc.r['metrics']['roc_auc_ci'][1]:.2f}, so treat it as a sketch).",
            "danger", f"{flex.REPORT}, Appendix B captions; model card in the Model Lab.")
    ui.source("Logistic model trained on FLEX Table IX initial conditions only; full metrics in the Model Lab", flex.PDF_URL)
else:
    fs = fitted("solid_sustained")
    ms = fs.r["metrics"]
    ui.no_data(
        "No model estimate for solid materials",
        f"A logistic model was trained on the {fs.r['n_rows']} verified solid-fuel test points exactly as specified, "
        f"and it failed validation: on test series it had not seen, its AUC is {ms['roc_auc']:.2f} "
        f"(95% interval {ms['roc_auc_ci'][0]:.2f} to {ms['roc_auc_ci'][1]:.2f}), no better than a coin. "
        "Showing its probabilities would be inventing confidence, so none is shown.",
        "Why it fails, and every metric, are in the Model Lab. The nearest real tests above are the answer.")
    decided = near[near["outcome"].isin(["sustained", "quenched", "blowoff", "no_ignition"])]
    tally = decided["outcome"].value_counts()
    st.markdown("**What the nearest tests did:** " + " · ".join(f"{v} {k.replace('_', ' ')}" for k, v in tally.items())
                + f". Their distance from your scenario ranges from {near['distance'].min():.2f} to {near['distance'].max():.2f}; "
                "a distance above about 2 means a different regime, not a comparable test.")

# ------------------------------------------------------------------ explicit gaps
if gaps:
    ui.rule()
    ui.no_data("This scenario is outside the tested envelope",
               "No experiment in the data was run at these conditions. " + " · ".join(g_[0].upper() + g_[1:] for g_ in gaps) + ".",
               "The nearest real tests are listed above. Nothing has been filled in by interpolation.")

# ------------------------------------------------------------------ triage score
ui.rule()
ui.section("Triage score", "A stated formula for ordering scenarios by how much attention they deserve. It is not a risk rating.")
with st.expander("Adjust the weights (they are a design choice)"):
    wcols = st.columns(len(ranking.WEIGHTS))
    raw = {k: c.number_input(ranking.TERM_LABEL[k], 0.0, 1.0, v, step=0.05, key=f"w-{k}")
           for c, (k, v) in zip(wcols, ranking.WEIGHTS.items())}
    total = sum(raw.values()) or 1.0
    weights = {k: v / total for k, v in raw.items()}
    st.caption("Weights are renormalised to sum to 1. Defaults: " + ", ".join(f"{ranking.TERM_LABEL[k]} {v:.2f}" for k, v in ranking.WEIGHTS.items()) + ".")
hrr = st.radio("Size of the burning item", list(ranking.HRR_SCALE_W), horizontal=True)
volume = st.number_input("Free volume of the cabin, m³", 1.0, 1000.0, 16.7 if "vehicle" in hrr else 50.0, step=1.0)
mine = ranking.Scenario("Your scenario", mat if kind == "solid" else f"{mat} droplet", o2, pressure, flow, g, hrr, volume,
                        is_droplet=kind == "droplet", droplet_d0_mm=d0 or 0.0, n_alkane=mat == "Heptane")
t = ranking.terms(mine)
score = sum(weights[k] * t["values"][k] for k in weights)
rows = [dict(Term=ranking.TERM_LABEL[k], Weight=weights[k], Value=t["values"][k], Contribution=weights[k] * t["values"][k],
             Why=t["why"][k]) for k in ranking.WEIGHTS]
left, right = st.columns([2, 3], gap="large")
with left:
    ui.stat_cards([dict(value=f"{score:.3f}", label="triage score for your scenario (0 to 1)",
                        source="Hazard = Σ weight × term. A design choice, for ordering only.", tone="amber")])
    for flag in t["flags"]:
        st.caption(f"Flag: {flag}.")
    if kind == "solid" and t["values"]["M_O2"] == 0 and (near["outcome"] == "sustained").any() and near["distance"].min() < 1:
        ui.callout("The formula and the data disagree here",
                   "The oxygen term scores this scenario 0 because its oxygen partial pressure is below the minimum "
                   "measured at 1 atm, yet a real test close to it sustained a flame. A limit measured at one pressure "
                   "does not transfer to another by partial pressure alone. This is why the score is for triage only.",
                   "danger")
with right:
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={"Weight": st.column_config.NumberColumn(format="%.2f"),
                                "Value": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                                "Contribution": st.column_config.NumberColumn(format="%.3f"),
                                "Why": st.column_config.TextColumn(width="large")})
allsc = [mine] + ranking.PRESETS
order = ranking.rank(allsc, weights)
sens = ranking.sensitivity(allsc, weights)
st.markdown("**Order of scenarios under these weights**")
st.dataframe(pd.DataFrame([dict(Rank=i + 1, Scenario=n, Score=s) for i, (n, s) in enumerate(order)]), hide_index=True,
             width="stretch", column_config={"Score": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.3f")})
if sens["weight_sensitive"]:
    ui.callout("Ranking is weight-sensitive",
               "Moving a single weight by 0.10 changes the top three: "
               + "; ".join(f"{c['change']} → {', '.join(c['top'])}" for c in sens["changes"][:4]) + ".", "danger",
               "Do not read the order as settled. It depends on a choice of weights that no experiment fixes.")
else:
    ui.callout("Top three is stable", "Moving any single weight by ±0.10 (then renormalising) leaves the top three in the same order.", "info")
ui.source("Formula, lookup values and their sources: flamefall/ranking.py. Weights are a design choice, not a measurement")

# ------------------------------------------------------------------ wrap-up
ui.rule()
ui.section("What the data says, and what is unknown", "The two lists a reader should leave with.")
says, unknown = st.columns(2, gap="large")
with says:
    st.markdown("##### What the data says")
    if kind == "droplet":
        k_ext, k_n = int(near["extinguished"].sum()), len(near)
        st.markdown(f"- Of the {k_n} nearest FLEX tests, {k_ext} ended in visible-flame extinction, "
                    f"{int((near['outcome'] == 'Disruption').sum())} in disruption and "
                    f"{int((near['outcome'] == 'Completion').sum())} burned to completion.")
        if mat == "Heptane":
            st.markdown(f"- {int((near['cool_flame_label'] == 'indicated').sum())} of those carry cool-flame evidence after the visible flame went out.")
    else:
        st.markdown("- " + "; ".join(f"{v} of the {len(near)} nearest test points: {k.replace('_', ' ')}" for k, v in near["outcome"].value_counts().items()) + ".")
        st.markdown(f"- Oxygen partial pressure here is {po2:.1f} kPa. Saffire VI burned fabric and acrylic at about 16.8 kPa (31% O2, 54 kPa).")
    st.markdown("- Smoke from overheated wire insulation can be too fine for a light-scattering detector: see What We Don't Know.")
with unknown:
    st.markdown("##### What is unknown")
    for item in gaps or ["Nothing flagged for these inputs: the scenario sits inside the tested ranges"]:
        st.markdown(f"- {item[0].upper() + item[1:]}.")
    st.markdown("- How any of this changes in partial gravity: no repository dataset exists yet.")
