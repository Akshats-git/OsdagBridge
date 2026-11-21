"""Vector charts for the design report (matplotlib object-oriented API only).

The desktop app draws live plots with matplotlib in the same process, so this
module never imports ``pyplot`` and never changes global state: every figure is
a standalone ``Figure`` styled through ``rc_context(theme.mpl_rc())``.  A test
enforces the no-pyplot rule.  Colours, sizes and fonts come from ``theme.py``.
"""
from __future__ import annotations

import logging
from typing import Optional, Sequence

from matplotlib import rc_context
from matplotlib.figure import Figure

from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.report_data import URRow

logger = logging.getLogger(__name__)

ROW_HEIGHT_IN = 0.24


def _plain(label: str) -> str:
    """Report labels hold LaTeX dashes; charts use plain text."""
    return label.replace(" --- ", " – ").replace("---", "–")


def ur_figure(rows: Sequence[URRow]) -> Figure:
    """Horizontal bar chart of every utilisation ratio, with the limit line.

    A bar turns the fail colour when its UR exceeds ``theme.UR_LIMIT``; checks
    without a numeric result get an "n/a" marker instead of a bar (they are not
    drawn as zero, which would read as a pass).
    """
    with rc_context(T.mpl_rc()):
        n = max(len(rows), 1)
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, ROW_HEIGHT_IN * n + 0.9))
        ax = fig.add_subplot(111)
        ys = list(range(n))
        urs = [r.ur for r in rows]
        top = max([u for u in urs if u is not None] + [T.UR_LIMIT]) * 1.15
        for y, r in zip(ys, rows):
            if r.ur is None:
                ax.text(0.01 * top, y, "n/a", va="center", ha="left", fontsize=T.CHART_FONT_SIZE - 1,
                        color=T.hex_color(T.CHART_NA_COLOR), style="italic")
                continue
            color = T.CHART_BAR_COLOR if T.ur_passes(r.ur) else T.CHART_BAR_FAIL_COLOR
            ax.barh(y, r.ur, height=0.62, color=T.hex_color(color), zorder=3)
            ax.text(r.ur + 0.01 * top, y, f"{r.ur:.2f}", va="center", ha="left",
                    fontsize=T.CHART_FONT_SIZE - 1)
        ax.axvline(T.UR_LIMIT, color=T.hex_color(T.CHART_LIMIT_COLOR), linestyle="--", linewidth=1.0, zorder=4)
        ax.text(T.UR_LIMIT, -0.9, f"limit = {T.UR_LIMIT:g}", color=T.hex_color(T.CHART_LIMIT_COLOR),
                ha="center", va="bottom", fontsize=T.CHART_FONT_SIZE - 1)
        ax.set_yticks(ys)
        ax.set_yticklabels([_plain(r.label) for r in rows])
        ax.set_ylim(n - 0.4, -1.0)          # first row on top, room for the limit label
        ax.set_xlim(0, top)
        ax.set_xlabel("Utilisation ratio (demand / capacity)")
        ax.grid(axis="y", visible=False)
        fig.subplots_adjust(left=0.36, right=0.97, top=0.98, bottom=0.8 / (ROW_HEIGHT_IN * n + 0.9))
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


def _hbar(ax, items, unit: str, fmt: str = "{:.2f}", color: str = T.CHART_BAR_COLOR) -> None:
    top = max([v for _, v in items if v is not None] + [1e-9]) * 1.18
    ys = list(range(len(items)))
    for y, (_, v) in zip(ys, items):
        if v is None:
            ax.text(0.01 * top, y, "N.A.", va="center", ha="left", fontsize=T.CHART_FONT_SIZE - 1,
                    color=T.hex_color(T.CHART_NA_COLOR), style="italic")
        else:
            ax.barh(y, v, height=0.6, color=T.hex_color(color), zorder=3)
            ax.text(v + 0.01 * top, y, fmt.format(v), va="center", ha="left", fontsize=T.CHART_FONT_SIZE - 1)
    ax.set_yticks(ys)
    ax.set_yticklabels([lbl for lbl, _ in items])
    ax.set_ylim(len(items) - 0.4, -0.6)
    ax.set_xlim(0, top)
    ax.set_xlabel(unit)
    ax.grid(axis="y", visible=False)


def steel_tonnage_figure(q: dict) -> Figure:
    """Structural steel weight (MT) per member group; missing items read N.A., not zero."""
    items = _items(q, STEEL_ITEMS, "wt_total")
    with rc_context(T.mpl_rc()):
        h = ROW_HEIGHT_IN * len(items) + 0.9
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, h))
        _hbar(fig.add_subplot(111), items, "Weight (MT)")
        fig.subplots_adjust(left=0.27, right=0.96, top=0.97, bottom=0.8 / h)
        return fig


def concrete_rebar_figure(q: dict) -> Figure:
    """Concrete volume (m3) and reinforcement weight (MT) side by side (different units)."""
    conc = _items(q, CONCRETE_ITEMS, "vol_total")
    rebar = [("Deck reinforcement", q.get("rebar_deck_wt_total_num"))]
    with rc_context(T.mpl_rc()):
        h = ROW_HEIGHT_IN * 2 + 1.1
        fig = Figure(figsize=(T.CHART_FIG_WIDTH_IN, h))
        a1, a2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [3, 2]})
        _hbar(a1, conc, "Concrete volume (m³)")
        _hbar(a2, rebar, "Reinforcement weight (MT)", color=T.PRIMARY)
        fig.subplots_adjust(left=0.17, right=0.97, top=0.96, bottom=0.8 / h * 1.15, wspace=0.75)
        return fig


def quantity_charts(q: dict, out_dir: str) -> dict:
    """Write both quantity charts into ``out_dir``; returns {name: filename} for those drawn."""
    import os
    made = {}
    for name, make in (("steel_chart", steel_tonnage_figure), ("concrete_chart", concrete_rebar_figure)):
        try:
            save_pdf(make(q), os.path.join(out_dir, name + ".pdf"))
            made[name] = name + ".pdf"
        except Exception as exc:
            logger.warning("%s not drawn: %s", name, exc)
    return made
