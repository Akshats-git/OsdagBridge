"""Single source of truth for the look of the OsdagBridge design report.

Every visual or layout constant used by the report lives here: page geometry,
colours, fonts, table style, header/footer, spacing thresholds, number formats,
the utilisation-ratio pass rule and the matplotlib chart style.

``preamble.py``, ``latex_kit.py`` and ``charts.py`` read these values; chapter
modules must not hard-code colours, lengths or table padding (a unit test lints
this).  To restyle the whole report, edit this file only.

This module is pure data: it imports nothing from Qt, matplotlib or PyLaTeX so
it can be imported anywhere (including tests without a TeX installation).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAPER = "a4paper"
BASE_FONT_PT = 12
MARGIN = "1in"
HEADHEIGHT = "16pt"          # fancyhdr needs >= the header line height + rule
HEADSEP = "14pt"
FOOTSKIP = "36pt"            # room for the footer rule, note line and text
EMERGENCY_STRETCH = "3em"   # lets TeX stretch a line instead of overflowing it
LINE_STRETCH = 1.15          # \setstretch
CHAPTER_BEFORE_PT = -30.0    # \titlespacing before a chapter title

# ---------------------------------------------------------------------------
# Palette (HTML hex without '#')
# ---------------------------------------------------------------------------
PRIMARY = "91B014"           # Osdag green: rules, header/footer rules
PASS_COLOR = "1B7F3B"
FAIL_COLOR = "C0392B"
WARN_COLOR = "B7791F"
NA_COLOR = "6B7280"
TEXT_COLOR = "000000"
TABLE_HEAD_FILL = None       # e.g. "EEF4D6" for a tinted header row (None = no fill)
TABLE_ZEBRA_FILL = None      # e.g. "F7F9EC" for alternating rows (None = off)

# LaTeX colour names registered by the preamble (name -> hex)
LATEX_COLORS = {
    "osdagGreen": PRIMARY,
    "urPass": PASS_COLOR,
    "urFail": FAIL_COLOR,
    "urWarn": WARN_COLOR,
    "urNA": NA_COLOR,
}

# ---------------------------------------------------------------------------
# Table style
# ---------------------------------------------------------------------------
TABCOLSEP_PT = 6.0
ARRAYSTRETCH = 1.12
ARRAYRULE_PT = 0.5
EXTRAROWHEIGHT_PT = 0.6
COMPACT_TABCOLSEP_PT = 3.0   # for dense numeric tables (compact=True in the kit)
COMPACT_SIZE = r"\footnotesize"
LT_PRE_PT = 6.0              # \LTpre
LT_POST_PT = 8.0             # \LTpost
CAPTION_SKIP_PT = 4.0        # \abovecaptionskip / \belowcaptionskip
HEADER_BOLD = True
HEADER_SIZE = r"\small"      # header row font size (keeps narrow columns from overflowing)
CONTINUED_TEXT = "(continued)"
CONTINUES_TEXT = "Continued on next page"

# Default table width as a fraction of \linewidth
TABLE_WIDTH_FRACTION = 1.0

# ---------------------------------------------------------------------------
# Spacing and pagination thresholds
# ---------------------------------------------------------------------------
NEEDSPACE_HEADING_LINES = 6      # keep a heading with at least this many lines
NEEDSPACE_TABLE_LINES = 6        # start a table only if this many lines fit
FIGURE_MAX_HEIGHT = r"0.42\textheight"
FIGURE_FULL_WIDTH = r"\linewidth"
FIGURE_ROW_WIDTH = 0.31          # share of \linewidth for each of three side-by-side figures
SECTION_GAP_PT = 6.0

# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------
RULE_THICKNESS_PT = 1.0
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_RIGHT = r"Page \thepage\ of \pageref{LastPage}"
SD_NOTE = "* Software default value"

# ---------------------------------------------------------------------------
# Utilisation ratio rule: one rule for the table, the chart and the summary
# ---------------------------------------------------------------------------
UR_LIMIT = 1.0


def ur_passes(ur: float) -> bool:
    """A check passes when UR <= UR_LIMIT (IRC 24 / IS 800 convention)."""
    return float(ur) <= UR_LIMIT


# ---------------------------------------------------------------------------
# Number formats
# ---------------------------------------------------------------------------
DECIMALS_FORCE = 2
DECIMALS_RATIO = 3
DECIMALS_LENGTH = 2
MISSING = "---"             # rendered for None / unavailable values


def fmt(value, decimals: int = 2, missing: str = MISSING) -> str:
    """Format a number; ``None`` / non-numeric -> ``missing`` (never ``0.00``)."""
    try:
        if value is None or value == "":
            return missing
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return missing


# ---------------------------------------------------------------------------
# Unicode characters the preamble teaches pdflatex about
# (codepoint, LaTeX replacement)
# ---------------------------------------------------------------------------
UNICODE_MAP = (
    (0x2264, r"\ensuremath{\leq}"),
    (0x2265, r"\ensuremath{\geq}"),
    (0x00D7, r"\ensuremath{\times}"),
    (0x03BC, r"\ensuremath{\mu}"),
    (0x00B5, r"\ensuremath{\mu}"),
    (0x03C6, r"\ensuremath{\phi}"),
    (0x03C4, r"\ensuremath{\tau}"),
    (0x03B3, r"\ensuremath{\gamma}"),
    (0x03C3, r"\ensuremath{\sigma}"),
    (0x2212, r"\ensuremath{-}"),
    (0x2013, r"--"),
    (0x2014, r"---"),
    (0x00B2, r"\ensuremath{^{2}}"),
    (0x00B3, r"\ensuremath{^{3}}"),
    (0x2192, r"\ensuremath{\rightarrow}"),
    (0x2248, r"\ensuremath{\approx}"),
    (0x00B1, r"\ensuremath{\pm}"),
    (0x2020, r"\textdagger{}"),
)

# ---------------------------------------------------------------------------
# Chart style (consumed by charts.py via mpl_rc())
# ---------------------------------------------------------------------------
CHART_FONT = "DejaVu Sans"
CHART_FONT_SIZE = 9
CHART_FIG_WIDTH_IN = 6.3         # text width on A4 with 1in margins
CHART_FIG_HEIGHT_IN = 3.2
CHART_BAR_COLOR = PRIMARY
CHART_BAR_FAIL_COLOR = FAIL_COLOR
CHART_LIMIT_COLOR = FAIL_COLOR
CHART_NA_COLOR = NA_COLOR
CHART_GRID_COLOR = "D9D9D9"


def hex_color(name_or_hex: str) -> str:
    """'91B014' -> '#91B014' for matplotlib."""
    return name_or_hex if name_or_hex.startswith("#") else "#" + name_or_hex


def mpl_rc() -> dict:
    """matplotlib rcParams for charts, applied with ``rc_context`` only.

    Never call ``matplotlib.rcParams.update`` or ``matplotlib.use`` with
    this: the report runs inside the desktop app, whose live plots share the
    process-wide matplotlib state.
    """
    return {
        "font.family": CHART_FONT,
        "font.size": CHART_FONT_SIZE,
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": hex_color(CHART_GRID_COLOR),
        "grid.linewidth": 0.5,
        "pdf.fonttype": 42,
    }
