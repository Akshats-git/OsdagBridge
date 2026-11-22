"""Vector charts for the design report (matplotlib object-oriented API only).

The desktop app draws live plots with matplotlib in the same process, so this
module never imports ``pyplot`` and never changes global state: every figure is
a standalone ``Figure`` styled through ``rc_context(theme.mpl_rc())``.  A test
enforces the no-pyplot rule.  Colours, sizes and fonts come from ``theme.py``.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Sequence

from matplotlib import rc_context
from matplotlib.figure import Figure

from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.report_data import URRow

logger = logging.getLogger(__name__)

UR_FIG_HEIGHT_IN = 4.6
LABEL_ROTATION = 40


def _plain(label: str) -> str:
    """Report labels hold LaTeX dashes; charts use plain text."""
    return label.replace(" --- ", " \u2013 ").replace("---", "\u2013")


def _bars(ax, items, ylabel: str, fmt: str = "{:.2f}", color: str = T.CHART_BAR_COLOR,
          na_text: str = "n/a", rotation: int = LABEL_ROTATION, colors=None) -> float:
    """Vertical bars with a value label on top; ``None`` values get an ``na_text`` marker.

    ``colors`` optionally gives one colour per bar.  Returns the upper y limit.
    """
    top = max([v for _, v in items if v is not None] + [1e-9]) * 1.18
    small = T.CHART_FONT_SIZE - 1
    for x, (_, v) in enumerate(items):
        if v is None:
            ax.text(x, 0.015 * top, na_text, va="bottom", ha="center", fontsize=small,
                    color=T.hex_color(T.CHART_NA_COLOR), style="italic")
            continue
        bar_color = colors[x] if colors else color
        ax.bar(x, v, width=0.62, color=T.hex_color(bar_color), zorder=3)
        ax.text(x, v + 0.01 * top, fmt.format(v), va="bottom", ha="center", fontsize=small)
    ax.set_xticks(range(len(items)))
    ax.set_xticklabels([label for label, _ in items], rotation=rotation,
                       ha="right" if rotation else "center", rotation_mode="anchor")
    ax.set_xlim(-0.6, len(items) - 0.4)
    ax.set_ylim(0, top)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)
    return top


def ur_figure(rows: Sequence[URRow]) -> Figure:
    """Bar chart of every utilisation ratio with a red dashed line at the limit.

    The y-axis is the utilisation ratio.  A bar turns the fail colour when its UR
    exceeds ``theme.UR_LIMIT``; checks without a numeric result get an "n/a" marker
    instead of a bar (they are not drawn as zero, which would read as a pass).
    """
    with rc_context(T.mpl_rc()):
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, UR_FIG_HEIGHT_IN))
        ax = fig.add_subplot(111)
        items = [(_plain(r.label), r.ur) for r in rows]
        colors = [T.CHART_BAR_COLOR if r.ur is None or T.ur_passes(r.ur) else T.CHART_BAR_FAIL_COLOR
                  for r in rows]
        top = _bars(ax, items, "Utilisation ratio (demand / capacity)", colors=colors)
        top = max(top, T.UR_LIMIT * 1.15)
        ax.set_ylim(0, top)
        ax.axhline(T.UR_LIMIT, color=T.hex_color(T.CHART_LIMIT_COLOR), linestyle="--", linewidth=1.0, zorder=4)
        ax.text(len(items) - 0.45, T.UR_LIMIT + 0.01 * top, f"limit = {T.UR_LIMIT:g}",
                color=T.hex_color(T.CHART_LIMIT_COLOR), ha="right", va="bottom", fontsize=T.CHART_FONT_SIZE - 1)
        fig.subplots_adjust(left=0.1, right=0.99, top=0.98, bottom=0.36)
        return fig


def save_pdf(fig: Figure, path: str) -> str:
    """Write ``fig`` as a vector PDF (fonts embedded, see ``mpl_rc``)."""
    with rc_context(T.mpl_rc()):
        fig.savefig(path, format="pdf")
    return path


def ur_chart(rows: Sequence[URRow], path: str) -> Optional[str]:
    """Render the UR chart to ``path``; ``None`` (with a log entry) on failure."""
    try:
        return save_pdf(ur_figure(rows), path)
    except Exception as exc:       # a chart must never break the report
        logger.warning("UR chart not drawn: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Material quantity charts (chapter 7)
# ---------------------------------------------------------------------------

STEEL_ITEMS = (
    ("Girders", "steel_girders"), ("Bracing: top chord", "bracing_top"),
    ("Bracing: bottom chord", "bracing_bot"), ("Bracing: diagonals", "bracing_diag"),
    ("End diaphragms", "end_diaphragm"), ("Shear studs", "shear_studs"),
)
CONCRETE_ITEMS = (("Deck slab", "concrete_deck"), ("Crash barrier", "crash_barrier"))


def _items(q: dict, spec, suffix: str):
    return [(label, q.get(f"{key}_{suffix}_num")) for label, key in spec]


def steel_tonnage_figure(q: dict) -> Figure:
    """Structural steel weight (MT) per member group; missing items read N.A., not zero."""
    items = _items(q, STEEL_ITEMS, "wt_total")
    with rc_context(T.mpl_rc()):
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, T.CHART_FIG_HEIGHT_IN))
        _bars(fig.add_subplot(111), items, "Weight (MT)", na_text="N.A.")
        fig.subplots_adjust(left=0.1, right=0.99, top=0.97, bottom=0.33)
        return fig


def concrete_rebar_figure(q: dict) -> Figure:
    """Concrete volume (m3) and reinforcement weight (MT) side by side (different units)."""
    conc = _items(q, CONCRETE_ITEMS, "vol_total")
    rebar = [("Deck reinforcement", q.get("rebar_deck_wt_total_num"))]
    with rc_context(T.mpl_rc()):
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, T.CHART_FIG_HEIGHT_IN))
        a1, a2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [2, 1]})
        _bars(a1, conc, "Concrete volume (m\u00b3)", na_text="N.A.", rotation=0)
        _bars(a2, rebar, "Reinforcement weight (MT)", color=T.PRIMARY, na_text="N.A.", rotation=0)
        fig.subplots_adjust(left=0.09, right=0.99, top=0.97, bottom=0.14, wspace=0.3)
        return fig


def quantity_charts(q: dict, out_dir: str) -> dict:
    """Write both quantity charts into ``out_dir``; returns {name: filename} for those drawn."""
    made = {}
    for name, make in (("steel_chart", steel_tonnage_figure), ("concrete_chart", concrete_rebar_figure)):
        try:
            save_pdf(make(q), os.path.join(out_dir, name + ".pdf"))
            made[name] = name + ".pdf"
        except Exception as exc:
            logger.warning("%s not drawn: %s", name, exc)
    return made
