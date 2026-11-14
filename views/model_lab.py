"""Model Lab: how each model was validated, what it learned, and where it stops being usable."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from flamefall import model, theme, ui

LABELS = {
    "droplet_extinction": "Droplets: does the visible flame go out?",
    "droplet_cool_flame": "Droplets: cool-flame evidence after extinction (exploratory)",
    "solid_sustained": "Solid materials: is the flame sustained? (failed validation)",
}
NICE = {
    "o2_pct": "Oxygen, %", "pressure_kpa": "Pressure (log)", "o2_partial_kpa": "O2 partial pressure",
    "co2_pct": "CO2, %", "he_pct": "Helium, %", "d0_mm": "Droplet diameter (log)", "fuel_heptane": "Fuel is n-heptane",
    "flow_cm_s": "Flow (log)", "thickness_mm": "Thickness (log)", "is_quiescent": "Still gas",
    "o2_pct x flow_cm_s": "Oxygen × flow", "(intercept)": "(intercept)",
}
UNITS = {"o2_pct": "%", "pressure_kpa": "kPa", "o2_partial_kpa": "kPa", "co2_pct": "%", "he_pct": "%", "d0_mm": "mm",
         "flow_cm_s": "cm/s", "thickness_mm": "mm"}


@st.cache_resource(show_spinner=False)
def fitted(name: str) -> model.Fitted:
    return model.Fitted(name)


def f2(v, digits=2) -> str:
    return "n/a" if v is None or v != v else f"{v:.{digits}f}"


ui.kicker("Validation · grouped cross-validation, seed 42")
st.title("Model Lab")
st.markdown(
    '<p class="ff-lede">Three small logistic models, each trained on one kind of evidence and tested on groups of '
    "tests it never saw. Droplet data and solid-material data are never pooled. One of the three fails, and is shown failing.</p>",
    unsafe_allow_html=True)

name = st.radio("Model", list(LABELS), format_func=LABELS.get, horizontal=False, label_visibility="collapsed")
with st.spinner("Loading the model card…"):
    fm = fitted(name)
r, m = fm.r, fm.r["metrics"]
lomo = r["leave_one_material_out"]
cy, c5 = m["confusion_at_youden"], m["confusion_at_0.5"]
failed = r["headline_auc"] is not None and r["headline_auc"] < 0.6
stress = "leave-one-fuel-out" if name.startswith("droplet") else "leave-one-material-out"

if failed:
    ui.callout(
        "This model failed validation and is not used anywhere in the dashboard",
        f"On test series it had not seen, it ranks a sustained flame above an extinguished one only {m['roc_auc']:.0%} "
        "of the time: no better than a coin. The Scenario Lab therefore shows the nearest real tests for solid "
        "materials and no probability.",
        "danger",
        "Why: each test series has its own oxygen limit (13.5% for a rod in concurrent flow, about 17% for fabric, "
        "17.5% for a rod in opposed flow), extinction happens at both low and high flow, and most recorded extinctions "
        "are given as fan settings with no velocity. A single straight boundary cannot carry over from one series to another.")

ui.stat_cards([
    dict(value=f2(r["headline_auc"]), label=f"headline AUC ({r['headline_is']})",
         source=f"the worse of grouped CV {f2(m['roc_auc'])} and {stress} {f2(lomo['pooled_auc'])}",
         tone="red" if failed else "amber"),
    dict(value=f2(m["roc_auc"]), label="grouped-CV ROC-AUC",
         source=f"95% interval {f2(m['roc_auc_ci'][0])} to {f2(m['roc_auc_ci'][1])} · cluster bootstrap over {r['n_split_groups']} groups",
         tone="cyan"),
    dict(value=f"{cy['false_positive_rate']:.0%}" if cy["false_positive_rate"] is not None else "n/a",
         label="false-positive rate at the working threshold",
         source=f"{cy['fp']} of {cy['fp'] + cy['tn']} negatives called positive at threshold {cy['threshold']:.2f} (Youden's J)",
         tone="red"),
    dict(value=r["n_rows"], label="rows after exclusions",
         source=f"{r['n_positive']} positive ({r['positive_share']:.0%}) · {r['n_groups']} groups · class weights "
                f"{'balanced' if r['class_weight_balanced'] else 'not needed'}", tone="green"),
])
st.caption(f"Positive class: {r['target_label']}.")
ui.source("scripts/train_models.py → data/models/" + name + ".json; fold membership in data/cv_splits.json")

# ------------------------------------------------------------------ metrics
ui.rule()
left, right = st.columns(2, gap="large")
with left:
    ui.section("Can it tell the two outcomes apart?", "ROC curve from out-of-fold predictions only: every point was scored by a model that never saw its group.", level=3)
    roc = m["roc"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[p[0] for p in roc], y=[p[1] for p in roc], mode="lines", name="Model",
                             line=dict(color=theme.RED if failed else theme.CYAN, width=3, shape="hv"),
                             hovertemplate="False-positive rate %{x:.2f}<br>Sensitivity %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Coin flip",
                             line=dict(color=theme.GREY, dash="dot"), hoverinfo="skip"))
    if cy["false_positive_rate"] is not None and cy["sensitivity"] is not None:
        fig.add_trace(go.Scatter(x=[cy["false_positive_rate"]], y=[cy["sensitivity"]], mode="markers",
                                 name="Working threshold", marker=dict(color=theme.AMBER, size=12, symbol="diamond")))
    fig.update_layout(xaxis_title="False-positive rate", yaxis_title="Sensitivity", height=380,
                      xaxis=dict(range=[-0.02, 1.02]), yaxis=dict(range=[-0.02, 1.02]))
    ui.plotly(fig, key="roc")
    sens90 = m["burning_sensitivity_at_90_specificity"]
    burning = r["burning_label"]
    st.markdown(
        '<div class="ff-kv">'
        f'<div class="k">PR-AUC</div><div class="ff-mono">{f2(m["pr_auc"])}</div>'
        f'<div class="k">Brier score</div><div class="ff-mono">{f2(m["brier"], 3)}</div>'
        f'<div class="k">Majority-class accuracy</div><div class="ff-mono">{m["baseline_majority_accuracy"]:.0%} (the bar to beat)</div>'
        f'<div class="k">Sensitivity for “{burning}” at 90% specificity</div><div class="ff-mono">'
        f'{"n/a" if sens90["sensitivity"] is None else format(sens90["sensitivity"], ".0%")}</div>'
        f'<div class="k">Row-wise CV AUC</div><div class="ff-mono">{f2(m["rowwise_cv_auc_for_comparison_only"])} '
        "(leaky; shown only for contrast)</div></div>", unsafe_allow_html=True)
with right:
    ui.section("What does it get wrong?", "Confusion matrices at the default 0.5 and at the Youden threshold the dashboard uses.", level=3)

    def matrix(c: dict, title: str) -> go.Figure:
        z = [[c["tn"], c["fp"]], [c["fn"], c["tp"]]]
        fig = go.Figure(go.Heatmap(z=z, x=["Predicted 0", "Predicted 1"], y=["Actual 0", "Actual 1"], showscale=False,
                                   colorscale=[[0, theme.PANEL], [1, "#7C4A12"]], text=z, texttemplate="%{text}",
                                   textfont=dict(size=22, family=theme.MONO, color=theme.TEXT), hoverinfo="skip"))
        fig.update_layout(height=230, margin=dict(l=70, r=10, t=44, b=30), title=title, yaxis=dict(autorange="reversed"))
        return fig

    ui.plotly(matrix(c5, "Threshold 0.50"), key="cm5")
    ui.plotly(matrix(cy, f"Threshold {cy['threshold']:.2f} (Youden's J, used by the dashboard)"), key="cmy")
    if name == "droplet_extinction":
        st.caption(f"The costly error is top right: {cy['fp']} tests where the flame did not go out but the model "
                   "said it would. A model like this must not be relied on by itself for a fire-protection decision.")
ui.source("Pooled out-of-fold predictions, outer GroupKFold with 5 folds; inner GroupKFold with 3 folds chooses C from "
          f"{r['C_grid']} (chosen for the final fit: {r['C_final']})")

# ------------------------------------------------------------------ calibration + groups
ui.rule()
left, right = st.columns(2, gap="large")
with left:
    ui.section("Are the probabilities honest?", "Predicted probability against what happened, in ten bins. On the dotted line means well calibrated.", level=3)
    bins = pd.DataFrame(m["calibration"]["bins"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=theme.GREY, dash="dot"), name="Perfect", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=bins["mean_predicted"], y=bins["observed_share"], mode="lines+markers", name="Model",
                             marker=dict(size=6 + 2.5 * bins["n"] ** 0.5, color=theme.CYAN), line=dict(color=theme.CYAN),
                             customdata=bins["n"], hovertemplate="Predicted %{x:.2f}<br>Observed %{y:.2f}<br>%{customdata} tests<extra></extra>"))
    fig.update_layout(xaxis_title="Mean predicted probability", yaxis_title="Observed share", height=360,
                      xaxis=dict(range=[-0.02, 1.02]), yaxis=dict(range=[-0.02, 1.02]))
    ui.plotly(fig, key="cal")
    st.caption(f"Calibration slope {f2(m['calibration']['slope'])} (1 is ideal; below 1 means over-confident), "
               f"intercept {f2(m['calibration']['intercept'])}. Bin sizes are small; read the shape, not single points.")
with right:
    ui.section("Does it hold up group by group?", "One line per group. A blank AUC means the group has only one outcome, so AUC is undefined.", level=3)
    pg = pd.DataFrame(m["per_group"]).sort_values("n", ascending=False)
    st.dataframe(pg, hide_index=True, width="stretch", height=360,
                 column_config={"group": st.column_config.TextColumn("Group", width="large"), "n": "Rows",
                                "positives": "Positive", "auc": st.column_config.NumberColumn("AUC", format="%.2f"),
                                "mean_predicted": st.column_config.NumberColumn("Mean predicted", format="%.2f"),
                                "observed_share": st.column_config.NumberColumn("Observed share", format="%.2f")})
    lm = pd.DataFrame(lomo["per_material"])
    st.markdown(f"**Stress test: {stress}** (train on the others, test on the one left out)")
    st.dataframe(lm[[c for c in ["material", "n", "positives", "auc", "brier", "note"] if c in lm]], hide_index=True, width="stretch",
                 column_config={"auc": st.column_config.NumberColumn("AUC", format="%.2f"),
                                "brier": st.column_config.NumberColumn("Brier", format="%.3f")})
ui.source("Out-of-fold predictions per group; the stress test is reported separately and never averaged into the grouped-CV figure")

# ------------------------------------------------------------------ coefficients
ui.rule()
ui.section("What moved the prediction?", "Each bar is a change in log-odds for a one-standard-deviation increase, with a 95% bootstrap interval.")
ct = pd.DataFrame(r["coef_table"])
ct = ct[ct["feature"] != "(intercept)"].copy()
ct["label"] = ct["feature"].map(lambda s: NICE.get(s, s.replace("=", ": ").replace("_", " ")))
ct = ct.iloc[::-1]
fig = go.Figure(go.Bar(
    x=ct["log_odds"], y=ct["label"], orientation="h",
    marker_color=[theme.RED if v > 0 else theme.CYAN for v in ct["log_odds"]],
    error_x=dict(type="data", symmetric=False, array=ct["ci_high"] - ct["log_odds"], arrayminus=ct["log_odds"] - ct["ci_low"],
                 color=theme.MUTED, thickness=1.2),
    customdata=ct[["odds_ratio", "ci_low", "ci_high"]].to_numpy(),
    hovertemplate="%{y}<br>log-odds %{x:.2f} [%{customdata[1]:.2f}, %{customdata[2]:.2f}]<br>odds ratio %{customdata[0]:.2f}<extra></extra>"))
fig.add_vline(x=0, line=dict(color=theme.BORDER))
fig.update_layout(height=120 + 30 * len(ct), xaxis_title=f"Change in log-odds of “{r['target_label'].split(' (')[0]}”", margin=dict(l=170))
ui.plotly(fig, key="coef")
caveats = ["These are associations in the tests that were run, not causes.",
           "Gas fractions sum to one, and oxygen fraction, pressure and oxygen partial pressure are tied together, so their effects cannot be separated cleanly."]
if name.startswith("droplet"):
    caveats.append("Helium appears in only 51 tests, run at their own oxygen levels and pressures: its bar is not evidence that helium suppresses or sustains a flame.")
ui.callout("How to read this chart", " ".join(caveats), "info")
with st.expander("Coefficient table"):
    st.dataframe(pd.DataFrame(r["coef_table"]), hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.3f") for c in ["log_odds", "odds_ratio", "ci_low", "ci_high"]})
ui.source(f"Final model refitted on all {r['n_rows']} rows; intervals from {r['bootstrap']['n']} cluster-bootstrap refits")

# ------------------------------------------------------------------ envelope + try a query
ui.rule()
ui.section("Where does the model stop?", "The ranges it was trained on, and a live check of how far any query sits from that data.")
env = pd.DataFrame([dict(Input=NICE.get(k, k).replace(" (log)", ""), Minimum=v[0], Maximum=v[1], Unit=UNITS.get(k, ""))
                    for k, v in r["envelope"].items()])
a, b = st.columns([2, 3], gap="large")
with a:
    st.markdown("**Training-data envelope**")
    st.dataframe(env, hide_index=True, width="stretch",
                 column_config={"Minimum": st.column_config.NumberColumn(format="%.2f"), "Maximum": st.column_config.NumberColumn(format="%.2f")})
    st.caption(f"Nearest-neighbour distance between training rows: median {r['distance']['train_nn_median']:.2f}, "
               f"95th percentile {r['distance']['train_nn_p95']:.2f} (standardised units).")
with b:
    st.markdown("**Try a query** (starts outside the envelope on purpose)")
    defaults = {"o2_pct": 45.0, "pressure_kpa": 56.5, "co2_pct": 0.0, "he_pct": 0.0, "d0_mm": 3.0, "flow_cm_s": 10.0, "thickness_mm": 3.0}
    q = {}
    qcols = st.columns(3)
    inputs = [c for c in r["continuous"] if c != "o2_partial_kpa"]
    for i, col in enumerate(inputs):
        q[col] = qcols[i % 3].number_input(f"{NICE.get(col, col).replace(' (log)', '')}{', ' + UNITS[col] if col in UNITS else ''}",
                                           value=defaults.get(col, 1.0), min_value=0.01 if col in r["log_features"] else 0.0,
                                           key=f"q-{name}-{col}")
    q["o2_partial_kpa"] = q["o2_pct"] / 100 * q["pressure_kpa"]
    for col in r["binary"]:
        q[col] = 1.0 if qcols[len(inputs) % 3].checkbox(NICE.get(col, col), value=True, key=f"q-{name}-{col}") else 0.0
    for col, cats in r["categorical"].items():
        q[col] = st.selectbox(col.replace("_", " ").capitalize(), [c for c in cats if c != "rare"], key=f"q-{name}-{col}")
    out = fm.predict(q)
    if out["extrapolating"]:
        why = [f"{NICE.get(o['feature'], o['feature']).replace(' (log)', '')} {o['value']:g} is outside the tested "
               f"{o['tested_min']:.3g} to {o['tested_max']:.3g}" for o in out["outside_envelope"]]
        if out["far_from_data"]:
            why.append(f"distance to the nearest training row is {out['nn_distance']:.2f}, beyond the {out['train_nn_p95']:.2f} that covers 95% of training rows")
        ui.callout("Distance-to-data warning: this query is an extrapolation",
                   "; ".join(why).capitalize() + ". Any output is a DEMO value, not an estimate to act on.", "danger")
    else:
        ui.callout("Inside the training envelope",
                   f"Distance to the nearest training row is {out['nn_distance']:.2f} (95% of training rows are within {out['train_nn_p95']:.2f} of another).", "info")
    if failed:
        st.caption("No probability is shown for this model because it failed validation.")
    else:
        st.markdown(f"Model output: **{out['p']:.0%}** (95% interval {out['lo']:.0%} to {out['hi']:.0%})"
                    + (" · **DEMO**" if out["extrapolating"] else ""))
    st.caption("Nearest training rows: " + ", ".join(f"{n_['row_id']} ({n_['distance']:.2f})" for n_ in out["nearest"][:4]))

# ------------------------------------------------------------------ protocol
ui.rule()
ui.section("How it was built", "The protocol, the features left out, and the features added with their written reason.", level=3)
st.markdown(
    f"- **Model.** L2-penalised logistic regression (lbfgs, up to 5,000 iterations); C chosen from {r['C_grid']} by inner grouped CV.\n"
    f"- **Validation.** Outer grouped 5-fold: a group ({'a tested atmosphere' if name.startswith('droplet') else 'an investigation or test series'}) "
    "is never split between training and test. Folds are fixed by seed 42 and saved.\n"
    "- **No leakage.** Burning rate, burn time, extinction diameter, heat release and spread rate are outcomes and are never inputs. "
    "Medians, means and standard deviations are learned on the training fold only.\n"
    f"- **Headline.** The worse of grouped-CV AUC and the {stress} stress test.")
for n_ in r["notes"]:
    st.markdown(f"- {n_}")
x, y = st.columns(2, gap="large")
with x:
    st.markdown("**Specified features not used, and why**")
    for k, v in r["dropped_features"].items():
        st.markdown(f"- `{k}`: {v}")
with y:
    st.markdown("**Features added to the specified list, with the reason**")
    if r["added_features"]:
        for k, v in r["added_features"].items():
            st.markdown(f"- `{k}`: {v}")
    else:
        st.markdown("- None.")
if name == "droplet_extinction":
    s = r["sensitivity_without_disruption"]
    ui.callout("Sensitivity check: leave the disrupted tests out",
               f"Refitted on Extinction against Completion only ({s['n_rows']} rows), grouped-CV AUC is {s['roc_auc']:.2f} "
               f"(95% interval {s['roc_auc_ci'][0]:.2f} to {s['roc_auc_ci'][1]:.2f}). Disruption is never counted as "
               "extinction in either version; the main model simply keeps those rows as “did not extinguish”.", "info")
ui.source("Research specification §7.3, adapted where the data forced it; every adaptation is listed in DECISIONS.md")
