"""Visual language for the dashboard: one palette, one Plotly template, one stylesheet.

Rule: a colour means the same thing on every page.
  red    = the visible flame went out (Extinction) / danger band
  green  = burned to completion
  violet = disruption (NOT an extinction; kept visually separate)
  cyan   = methanol / neutral data
  flame  = n-heptane / primary accent
  grey   = unverified or no data
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

BG = "#0B0F14"
PANEL = "#111821"
PANEL_2 = "#16202B"
BORDER = "#243140"
TEXT = "#E6EDF3"
MUTED = "#9AA7B6"
AMBER = "#F59E0B"
FLAME = "#FF8C1A"
CYAN = "#22D3EE"
RED = "#F87171"
GREEN = "#34D399"
VIOLET = "#A78BFA"
GREY = "#6B7785"

OUTCOME_COLORS = {"Extinction": RED, "Disruption": VIOLET, "Completion": GREEN}
FUEL_COLORS = {"Methanol": CYAN, "Heptane": FLAME}
COOL_COLORS = {"indicated": AMBER, "not_indicated": CYAN, "unclear": GREY, "": "#3A4756"}
VERIFICATION_COLORS = {"verified_live": GREEN, "index": AMBER, "unverified": GREY}

MONO = "'JetBrains Mono', 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SANS = "'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def register_plotly_template() -> None:
    """Register and activate the dark 'flamefall' Plotly template."""
    axis = dict(
        gridcolor="#1C2733", zerolinecolor="#2A3847", linecolor=BORDER, tickcolor=BORDER,
        title_font=dict(size=13, color=MUTED), tickfont=dict(size=12, color=MUTED, family=MONO),
    )
    pio.templates["flamefall"] = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=SANS, color=TEXT, size=13),
            colorway=[CYAN, FLAME, VIOLET, GREEN, RED, AMBER, GREY],
            xaxis=axis,
            yaxis=axis,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=12),
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=56, r=16, t=40, b=48),
            hoverlabel=dict(bgcolor=PANEL_2, bordercolor=BORDER, font=dict(family=MONO, color=TEXT, size=12)),
            title=dict(font=dict(size=14, color=TEXT), x=0, xanchor="left"),
        )
    )
    pio.templates.default = "flamefall"


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp {{ font-family: {SANS}; }}
.stApp {{ background: radial-gradient(1200px 500px at 85% -10%, rgba(255,140,26,0.07), transparent 60%), {BG}; }}
section[data-testid="stSidebar"] {{ background: #0D131A; border-right: 1px solid {BORDER}; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1280px; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
h1 {{ font-weight: 700; }}
h2 {{ font-weight: 650; margin-top: 0.4rem; }}
code, pre, .ff-mono {{ font-family: {MONO}; }}

/* --- hero ------------------------------------------------------------ */
.ff-kicker {{ font-family: {MONO}; font-size: 0.74rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: {AMBER}; margin-bottom: 0.35rem; }}
.ff-hero {{ font-size: clamp(1.7rem, 4.2vw, 2.9rem); line-height: 1.1; font-weight: 700; margin: 0 0 0.6rem 0;
  color: {TEXT}; text-wrap: balance; }}
.ff-hero em {{ font-style: normal; color: {FLAME}; }}
.ff-lede {{ color: {MUTED}; font-size: 1.05rem; max-width: 62ch; margin-bottom: 0.4rem; }}

/* --- stat cards ------------------------------------------------------ */
.ff-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 0.6rem 0 0.2rem; }}
.ff-card {{ background: linear-gradient(180deg, {PANEL} 0%, #0E151D 100%); border: 1px solid {BORDER};
  border-radius: 10px; padding: 14px 16px 12px; min-width: 0; }}
.ff-card .v {{ font-family: {MONO}; font-size: 1.9rem; font-weight: 700; color: {TEXT}; line-height: 1.1;
  font-variant-numeric: tabular-nums; }}
.ff-card .v small {{ font-size: 0.95rem; color: {MUTED}; font-weight: 500; }}
.ff-card .l {{ color: {TEXT}; font-size: 0.92rem; margin-top: 4px; }}
.ff-card .s {{ color: {MUTED}; font-size: 0.74rem; margin-top: 8px; font-family: {MONO}; line-height: 1.35; }}
.ff-card.amber {{ border-top: 2px solid {AMBER}; }}
.ff-card.cyan {{ border-top: 2px solid {CYAN}; }}
.ff-card.red {{ border-top: 2px solid {RED}; }}
.ff-card.green {{ border-top: 2px solid {GREEN}; }}
.ff-card.violet {{ border-top: 2px solid {VIOLET}; }}
.ff-card.grey {{ border-top: 2px solid {GREY}; opacity: 0.78; }}

/* --- provenance, badges, callouts ----------------------------------- */
.ff-src {{ font-family: {MONO}; font-size: 0.74rem; color: {MUTED}; border-left: 2px solid {BORDER};
  padding: 2px 0 2px 10px; margin: 0.15rem 0 1.2rem; line-height: 1.5; overflow-wrap: anywhere; }}
.ff-src a {{ color: {CYAN}; text-decoration: none; }}
.ff-src a:hover {{ text-decoration: underline; }}
.ff-explain {{ color: {MUTED}; margin: -0.35rem 0 0.7rem; max-width: 78ch; }}
.ff-badge {{ display: inline-block; font-family: {MONO}; font-size: 0.68rem; letter-spacing: 0.06em;
  text-transform: uppercase; padding: 2px 8px; border-radius: 999px; border: 1px solid; margin-right: 6px;
  white-space: nowrap; }}
.ff-badge.ok {{ color: {GREEN}; border-color: rgba(52,211,153,0.5); background: rgba(52,211,153,0.08); }}
.ff-badge.warn {{ color: {AMBER}; border-color: rgba(245,158,11,0.5); background: rgba(245,158,11,0.08); }}
.ff-badge.bad {{ color: {RED}; border-color: rgba(248,113,113,0.5); background: rgba(248,113,113,0.08); }}
.ff-badge.info {{ color: {CYAN}; border-color: rgba(34,211,238,0.45); background: rgba(34,211,238,0.07); }}
.ff-badge.violet {{ color: {VIOLET}; border-color: rgba(167,139,250,0.5); background: rgba(167,139,250,0.08); }}
.ff-badge.mute {{ color: {MUTED}; border-color: {BORDER}; background: rgba(255,255,255,0.03); }}
.ff-call {{ border: 1px solid {BORDER}; border-left: 3px solid {AMBER}; background: {PANEL}; border-radius: 8px;
  padding: 12px 16px; margin: 0.5rem 0 1rem; }}
.ff-call.nodata {{ border-left-color: {GREY}; background: repeating-linear-gradient(135deg, {PANEL} 0 14px, #131C26 14px 28px); }}
.ff-call.danger {{ border-left-color: {RED}; }}
.ff-call.info {{ border-left-color: {CYAN}; }}
.ff-call h4 {{ margin: 0 0 4px 0; font-size: 0.98rem; }}
.ff-call p {{ margin: 0.25rem 0; color: {TEXT}; }}
.ff-call .m {{ color: {MUTED}; font-size: 0.88rem; }}
.ff-nodata-tag {{ font-family: {MONO}; font-weight: 700; letter-spacing: 0.14em; color: {TEXT};
  background: #2A3644; border-radius: 4px; padding: 2px 8px; margin-right: 8px; font-size: 0.8rem; }}
.ff-unverified {{ opacity: 0.55; filter: grayscale(0.6); }}
.ff-kv {{ display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; font-size: 0.9rem; }}
.ff-kv .k {{ color: {MUTED}; font-family: {MONO}; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.06em; padding-top: 2px; }}
.ff-rule {{ height: 1px; background: {BORDER}; margin: 1.6rem 0 1.2rem; border: 0; }}

/* --- widgets --------------------------------------------------------- */
div[data-testid="stMetricValue"] {{ font-family: {MONO}; }}
div[data-testid="stExpander"] {{ border: 1px solid {BORDER}; border-radius: 8px; background: {PANEL}; }}
div[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 8px; }}
a[data-testid="stPageLink-NavLink"] {{ border: 1px solid {BORDER}; border-radius: 8px; background: {PANEL}; }}
button:focus-visible, a:focus-visible, input:focus-visible {{ outline: 2px solid {AMBER} !important; outline-offset: 2px; }}

@media (max-width: 640px) {{
  .block-container {{ padding-left: 0.9rem; padding-right: 0.9rem; padding-top: 3.2rem; }}
  .ff-grid {{ grid-template-columns: 1fr 1fr; gap: 8px; }}
  .ff-card {{ padding: 10px 12px; }}
  .ff-card .v {{ font-size: 1.35rem; }}
  .ff-kv {{ grid-template-columns: 1fr; }}
}}
</style>
"""
