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
