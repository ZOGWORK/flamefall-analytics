"""Plotly figures for the FLEX (droplet) evidence. Droplet data only: never mixed with solids."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import flex, theme

AXIS_LABEL = {
    "o2_pct": "Ambient O2, mol %",
    "co2_pct": "Ambient CO2, mol %",
    "he_pct": "Ambient He, mol %",
    "pressure_atm": "Ambient pressure, atm",
    "d0_mm": "Initial droplet diameter D0, mm",
    "o2_partial_kpa": "O2 partial pressure, kPa",
}

HOVER = ("<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
         "O2 %{customdata[2]:.0f}% · CO2 %{customdata[3]:.0f}% · He %{customdata[4]:.0f}%<br>"
         "P %{customdata[5]} · D0 %{customdata[6]} mm<br>"
         "K %{customdata[7]} mm²/s · outcome %{customdata[8]}<extra></extra>")


def _custom(df: pd.DataFrame) -> np.ndarray:
    def s(col, digits):
        return df[col].map(lambda v: "n/a" if pd.isna(v) else f"{v:.{digits}f}")
    return np.column_stack([
        df["test_id"], df["fuel"], df["o2_pct"], df["co2_pct"], df["he_pct"],
        s("pressure_atm", 2) + " atm", s("d0_mm", 2), s("burning_rate_mm2_s", 2), df["outcome"]])


def logistic_trend(x: np.ndarray, y: np.ndarray, grid: np.ndarray) -> np.ndarray | None:
    """One-variable logistic fit (Newton iterations). Returns None when it cannot be fitted."""
    if len(x) < 8 or len(set(y)) < 2 or np.ptp(x) == 0:
        return None
    mu, sd = x.mean(), x.std()
    X = np.column_stack([np.ones_like(x, dtype=float), (x - mu) / sd])
    beta = np.zeros(2)
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ beta))
        w = np.clip(p * (1 - p), 1e-6, None)
        hess = X.T @ (X * w[:, None]) + 1e-3 * np.eye(2)   # tiny ridge keeps separable data finite
        step = np.linalg.solve(hess, X.T @ (y - p) - 1e-3 * beta)
        beta += step
        if np.abs(step).max() < 1e-8:
            break
    G = np.column_stack([np.ones_like(grid, dtype=float), (grid - mu) / sd])
    return 1 / (1 + np.exp(-G @ beta))


def share_by_level(df: pd.DataFrame, xcol: str) -> pd.DataFrame:
    """Extinction share at each tested level of xcol, per fuel, with Wilson 95% intervals."""
    rows = []
    for (fuel, level), g in df.groupby(["fuel", xcol]):
        n, k = len(g), int(g["extinguished"].sum())
        lo, hi = flex.wilson_interval(k, n)
        rows.append(dict(fuel=fuel, level=level, n=n, k=k, share=k / n, lo=lo, hi=hi,
                         disruption=int((g["outcome"] == "Disruption").sum()),
                         completion=int((g["outcome"] == "Completion").sum())))
    return pd.DataFrame(rows)


def extinction_share_figure(df: pd.DataFrame, xcol: str = "o2_pct") -> go.Figure:
    fig = go.Figure()
    agg = share_by_level(df, xcol)
    for fuel, color in theme.FUEL_COLORS.items():
        a = agg[agg["fuel"] == fuel]
        if a.empty:
            continue
        fig.add_trace(go.Scatter(
            x=a["level"], y=a["share"] * 100, mode="markers", name=f"{fuel} (share per level)",
            marker=dict(color=color, size=6 + 3.2 * np.sqrt(a["n"]), opacity=0.85,
                        line=dict(color=theme.BG, width=1)),
            error_y=dict(type="data", symmetric=False, array=(a["hi"] - a["share"]) * 100,
                         arrayminus=(a["share"] - a["lo"]) * 100, color=color, thickness=1, width=0),
            customdata=np.column_stack([a["k"], a["n"], a["disruption"], a["completion"],
                                        a["lo"] * 100, a["hi"] * 100]),
            hovertemplate=(f"<b>{fuel}</b> at %{{x:.0f}}%<br>Extinction %{{customdata[0]}} of %{{customdata[1]}} "
                           "tests = %{y:.0f}%<br>95% interval %{customdata[4]:.0f}–%{customdata[5]:.0f}%<br>"
                           "Disruption %{customdata[2]} · Completion %{customdata[3]}<extra></extra>")))
        sub = df[df["fuel"] == fuel]
        grid = np.linspace(sub[xcol].min(), sub[xcol].max(), 60) if len(sub) else np.array([])
        trend = logistic_trend(sub[xcol].to_numpy(float), sub["extinguished"].to_numpy(float), grid)
        if trend is not None:
            fig.add_trace(go.Scatter(x=grid, y=trend * 100, mode="lines", name=f"{fuel} trend",
                                     line=dict(color=color, width=2, dash="dot"), hoverinfo="skip"))
    fig.update_layout(
        xaxis_title=AXIS_LABEL[xcol], yaxis_title="Tests ending in Extinction, %",
        yaxis=dict(range=[-4, 104], ticksuffix="%"), height=420)
    return fig


def outcome_mix_figure(df: pd.DataFrame, xcol: str = "o2_pct") -> go.Figure:
    """Stacked counts of the three outcomes at each tested level: the three stay separate."""
    tab = df.groupby([xcol, "outcome"]).size().unstack(fill_value=0)
    fig = go.Figure()
    for outcome in flex.OUTCOMES:
        if outcome in tab:
            fig.add_trace(go.Bar(x=tab.index, y=tab[outcome], name=outcome,
                                 marker_color=theme.OUTCOME_COLORS[outcome],
                                 hovertemplate=f"{outcome}: %{{y}} tests at %{{x:.0f}}%<extra></extra>"))
    fig.update_layout(barmode="stack", xaxis_title=AXIS_LABEL[xcol], yaxis_title="Number of tests",
                      height=420, bargap=0.25)
    return fig


def outcome_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["outcome"].value_counts().reindex(flex.OUTCOMES).fillna(0).astype(int)
    fig = go.Figure(go.Pie(
        labels=counts.index, values=counts.values, hole=0.62, sort=False, direction="clockwise",
        marker=dict(colors=[theme.OUTCOME_COLORS[o] for o in counts.index], line=dict(color=theme.BG, width=2)),
        textinfo="value", textposition="inside", insidetextorientation="horizontal",
        textfont=dict(family=theme.MONO, size=13, color=theme.BG),
        hovertemplate="%{label}: %{value} tests (%{percent})<extra></extra>"))
    fig.update_layout(
        showlegend=True, height=340, margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(orientation="h", yanchor="top", y=-0.02, xanchor="center", x=0.5),
        annotations=[dict(text=f"<b>{int(counts.sum())}</b><br>tests", x=0.5, y=0.5, showarrow=False,
                          font=dict(size=18, family=theme.MONO, color=theme.TEXT))])
    return fig


def burning_rate_figure(df: pd.DataFrame, xcol: str = "d0_mm") -> go.Figure:
    """Average burning-rate constant K against a chosen condition. Rows without K or x are not drawn."""
    d = df.dropna(subset=["burning_rate_mm2_s", xcol])
    symbols = {"Extinction": "circle", "Disruption": "x", "Completion": "diamond"}
    fig = go.Figure()
    for fuel, color in theme.FUEL_COLORS.items():
        for outcome, symbol in symbols.items():
            g = d[(d["fuel"] == fuel) & (d["outcome"] == outcome)]
            if g.empty:
                continue
            fig.add_trace(go.Scatter(
                x=g[xcol], y=g["burning_rate_mm2_s"], mode="markers", name=f"{fuel} · {outcome}",
                marker=dict(color=color, symbol=symbol, size=8, opacity=0.8,
                            line=dict(color=theme.BG, width=0.5)),
                customdata=_custom(g), hovertemplate=HOVER))
    fig.update_layout(xaxis_title=AXIS_LABEL[xcol], yaxis_title="Average burning rate K, mm²/s", height=440)
    return fig


def d2_reconstruction(row: pd.Series) -> go.Figure | None:
    """d²-law line rebuilt from Table IX (D0, average K, burn time). Not the measured trace."""
    d0, k, t_end = row["d0_mm"], row["burning_rate_mm2_s"], row["burn_time_s"]
    if pd.isna(d0) or pd.isna(k) or pd.isna(t_end):
        return None
    t = np.linspace(0, t_end, 50)
    d2 = d0 ** 2 - k * t
    color = theme.FUEL_COLORS[row["fuel"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=d2, mode="lines", name="d²-law line: D0² − K·t",
                             line=dict(color=color, width=3),
                             hovertemplate="t = %{x:.1f} s<br>D² = %{y:.2f} mm²<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0], y=[d0 ** 2], mode="markers", name="Initial diameter² (Table IX)",
                             marker=dict(color=theme.TEXT, size=10, symbol="circle-open", line=dict(width=2)),
                             hovertemplate="D0 = %{customdata:.2f} mm<extra></extra>", customdata=[d0]))
    dext = row["extinction_diameter_mm"]
    if not pd.isna(dext):
        fig.add_trace(go.Scatter(
            x=[t_end], y=[dext ** 2], mode="markers", name="Reported visible-flame extinction diameter²",
            marker=dict(color=theme.RED, size=12, symbol="x"),
            hovertemplate="Extinction diameter = %{customdata:.2f} mm at %{x:.1f} s<extra></extra>",
            customdata=[dext]))
    fig.add_hline(y=0, line=dict(color=theme.BORDER, width=1))
    fig.update_layout(xaxis_title="Time from ignition, s", yaxis_title="Droplet diameter², mm²", height=380,
                      yaxis=dict(rangemode="tozero"))
    return fig
