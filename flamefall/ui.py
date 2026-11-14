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


DISCLAIMER = ("Estimates only. This dashboard reports what experiments measured and where no data exists. "
              "It never rates a material, atmosphere or design as acceptable for flight.")


class Html(str):
    """Markup written in this codebase and meant to be rendered as HTML.

    Every helper below escapes plain strings. Pass `Html(...)` only for markup built here from
    escaped parts (a badge, a link). Text that comes from a data file is never wrapped in Html.
    """


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def _t(text: object) -> str:
    """Escape unless the caller marked the value as trusted markup."""
    return str(text) if isinstance(text, Html) else esc(text)


def kicker(text: str) -> None:
    st.markdown(f'<div class="ff-kicker">{esc(text)}</div>', unsafe_allow_html=True)


def section(title: str, explainer: str, level: int = 2) -> None:
    """Heading + one-line explainer."""
    st.markdown(f"{'#' * level} {title}")
    st.markdown(f'<p class="ff-explain">{_t(explainer)}</p>', unsafe_allow_html=True)


def source(text: str, url: str | None = None, extra: str = "") -> None:
    """Provenance footnote. No number goes on screen without one of these under it."""
    link = f' · <a href="{esc(url)}" target="_blank" rel="noopener">open source</a>' if url else ""
    tail = f" · {_t(extra)}" if extra else ""
    st.markdown(f'<div class="ff-src">Source: {_t(text)}{link}{tail}</div>', unsafe_allow_html=True)


def badge(text: str, kind: str = "mute") -> Html:
    return Html(f'<span class="ff-badge {esc(kind)}">{esc(text)}</span>')


# Badge style per outcome: the same colours as the charts. Disruption is violet, never the grey
# used for "not verified" or "no data".
OUTCOME_BADGE = {"Extinction": "bad", "Disruption": "violet", "Completion": "ok"}

VERIFICATION_BADGE = {
    "verified_live": ("verified against primary source", "ok"),
    "index": ("index-level: abstract or summary only", "warn"),
    "unverified": ("not verified", "mute"),
}


def verification_badge(level: object) -> Html:
    """Badge for a verification level. Anything missing or unknown reads as "not verified"."""
    try:
        missing = level is None or bool(level != level)     # None, or NaN (NaN != NaN)
    except TypeError:                                         # pd.NA: its comparison has no truth value
        missing = True
    key = "" if missing else str(level).strip()
    text, kind = VERIFICATION_BADGE.get(key, ("not verified", "mute"))
    return badge(text, kind)


def stat_cards_html(cards: list[dict]) -> str:
    """Markup for a responsive grid of stat cards. Every field is escaped unless passed as Html."""
    parts = ['<div class="ff-grid">']
    for c in cards:
        unit = f" <small>{esc(c['unit'])}</small>" if c.get("unit") else ""
        parts.append(
            f'<div class="ff-card {esc(c.get("tone", "amber"))}">'
            f'<div class="v">{esc(c["value"])}{unit}</div>'
            f'<div class="l">{_t(c["label"])}</div>'
            f'<div class="s">{_t(c["source"])}</div></div>')
    parts.append("</div>")
    return "".join(parts)


def stat_cards(cards: list[dict]) -> None:
    """cards: [{value, unit?, label, source, tone?}] rendered as real text, not an image."""
    st.markdown(stat_cards_html(cards), unsafe_allow_html=True)


def callout_html(title: str, body: str, kind: str = "", muted: str = "") -> str:
    m = f'<p class="m">{_t(muted)}</p>' if muted else ""
    return f'<div class="ff-call {esc(kind)}"><h4>{_t(title)}</h4><p>{_t(body)}</p>{m}</div>'


def callout(title: str, body: str, kind: str = "", muted: str = "") -> None:
    st.markdown(callout_html(title, body, kind, muted), unsafe_allow_html=True)


def no_data(title: str, body: str, muted: str = "") -> None:
    """The explicit NO DATA panel. 'No data' is an answer, not an error."""
    tagged = Html(f'<span class="ff-nodata-tag">NO DATA</span>{_t(title)}')   # the one deliberate markup path
    callout(tagged, body, "nodata", muted)


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
