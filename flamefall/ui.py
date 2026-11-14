"""Small HTML building blocks shared by every page.

Every section follows the same order: heading, one-line plain-English explainer,
the visual, then the source footnote. `section()` and `source()` enforce that order.
"""
from __future__ import annotations

import html

import streamlit as st

from . import theme


def setup_page() -> None:
    """Call once per page: inject the stylesheet and activate the Plotly template."""
    theme.register_plotly_template()
    st.markdown(theme.CSS, unsafe_allow_html=True)


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def kicker(text: str) -> None:
    st.markdown(f'<div class="ff-kicker">{esc(text)}</div>', unsafe_allow_html=True)


def section(title: str, explainer: str, level: int = 2) -> None:
    """Heading + one-line explainer."""
    st.markdown(f"{'#' * level} {title}")
    st.markdown(f'<p class="ff-explain">{explainer}</p>', unsafe_allow_html=True)


def source(text: str, url: str | None = None, extra: str = "") -> None:
    """Provenance footnote. No number goes on screen without one of these under it."""
    link = f' · <a href="{esc(url)}" target="_blank" rel="noopener">open source</a>' if url else ""
    tail = f" · {extra}" if extra else ""
    st.markdown(f'<div class="ff-src">Source: {text}{link}{tail}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "mute") -> str:
    return f'<span class="ff-badge {kind}">{esc(text)}</span>'


VERIFICATION_BADGE = {
    "verified_live": ("verified against primary source", "ok"),
    "index": ("index-level: abstract or summary only", "warn"),
    "unverified": ("not verified", "mute"),
}


def verification_badge(level: str) -> str:
    text, kind = VERIFICATION_BADGE.get(level, (level or "not verified", "mute"))
    return badge(text, kind)


def stat_cards(cards: list[dict]) -> None:
    """cards: [{value, unit?, label, source, tone?}] rendered as a responsive grid of real text."""
    parts = ['<div class="ff-grid">']
    for c in cards:
        unit = f" <small>{esc(c['unit'])}</small>" if c.get("unit") else ""
        parts.append(
            f'<div class="ff-card {esc(c.get("tone", "amber"))}">'
            f'<div class="v">{esc(c["value"])}{unit}</div>'
            f'<div class="l">{c["label"]}</div>'
            f'<div class="s">{c["source"]}</div></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def callout(title: str, body: str, kind: str = "", muted: str = "") -> None:
    m = f'<p class="m">{muted}</p>' if muted else ""
    st.markdown(f'<div class="ff-call {kind}"><h4>{title}</h4><p>{body}</p>{m}</div>', unsafe_allow_html=True)


def no_data(title: str, body: str, muted: str = "") -> None:
    """The explicit NO DATA panel. 'No data' is an answer, not an error."""
    callout(f'<span class="ff-nodata-tag">NO DATA</span>{title}', body, "nodata", muted)


def rule() -> None:
    st.markdown('<hr class="ff-rule">', unsafe_allow_html=True)


def plotly(fig, key: str | None = None, height: int | None = None) -> None:
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", key=key,
                    config={"displaylogo": False, "responsive": True,
                            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]})


def fmt(value, digits: int = 2, unit: str = "", missing: str = "—") -> str:
    """Format a number; a missing value prints as a dash, never as 0."""
    try:
        if value is None or value != value:  # NaN check
            return missing
    except TypeError:
        return missing
    text = f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return f"{text} {unit}".strip()


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"
