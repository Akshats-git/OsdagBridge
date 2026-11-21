"""PyLaTeX-based building blocks for the design report.

Chapter modules describe *what* a table contains (columns, rows, caption); this
module decides *how* it looks, reading every visual value from ``theme``.

Tables are PyLaTeX ``LongTable`` objects, so every table:

* repeats its header on continuation pages and prints "(continued)" in the
  caption row (``\\endfirsthead`` / ``\\endhead``),
* ends with a "Continued on next page" foot on every page but the last,
* always terminates its caption line with ``\\\\`` (an unterminated caption in a
  longtable is a LaTeX error),
* uses column widths that sum to exactly the line width, corrected for cell
  padding and rule thickness, so nothing sticks out of the right margin,
* can keep related rows together (``groups``) by ending all but the last row of
  a group with ``\\\\*`` (longtable's "no page break after this row").

Cells can be plain text (escaped here) or ``NoEscape`` LaTeX (used as is).
Missing values (``None``) render as ``theme.MISSING``, never as ``0``.

This module returns LaTeX strings; it never touches the file system.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Union

from pylatex import Figure, LongTable, MultiColumn, NoEscape
from pylatex.utils import escape_latex

from osdagbridge.core.reports import theme as T

Cell = Union[str, int, float, None, NoEscape]

_ALIGN_CMD = {
    "l": r">{\raggedright\arraybackslash}",
    "c": r">{\centering\arraybackslash}",
    "r": r">{\raggedleft\arraybackslash}",
}

# Same normalisation the old _tex() did for glyphs pdflatex cannot print.
_ASCII_FALLBACK = (("∠", "L"), ("ⅹ", "x"))


# ---------------------------------------------------------------------------
# Escaping and small inline helpers
# ---------------------------------------------------------------------------

def esc(value) -> NoEscape:
    """Escape plain text for LaTeX; ``NoEscape`` input is passed through.

    ``None`` becomes ``theme.MISSING``.  Underscores and colons get a break
    opportunity so long identifiers wrap instead of overflowing a column.
    """
    if isinstance(value, NoEscape):
        return value
    if value is None:
        return NoEscape(T.MISSING)
    s = str(value)
    for uni, ascii_ in _ASCII_FALLBACK:
        s = s.replace(uni, ascii_)
    s = escape_latex(s).replace(r"\_", r"\_\allowbreak{}").replace(":", r":\allowbreak{}")
    return NoEscape(s)


def raw(latex: str) -> NoEscape:
    """Mark a string as LaTeX that must not be escaped (e.g. ``$b_f$``)."""
    return NoEscape(latex)


def pass_fail(text: str) -> NoEscape:
    """'PASS' / 'FAIL' (case-insensitive) in the theme colours; anything else as n/a."""
    t = str(text).strip().upper()
    if t == "PASS":
        return NoEscape(r"\urpass{PASS}")
    if t == "FAIL":
        return NoEscape(r"\urfail{FAIL}")
    return na()


def status(ur: Optional[float]) -> NoEscape:
    """PASS/FAIL from a utilisation ratio using the single theme rule; None -> n/a."""
    if ur is None:
        return na()
    return pass_fail("PASS" if T.ur_passes(ur) else "FAIL")


def na(text: str = "n/a") -> NoEscape:
    return NoEscape(r"\urna{%s}" % text)


def bold(text) -> NoEscape:
    return NoEscape(r"\textbf{%s}" % esc(text))


def note(text, small: bool = True) -> str:
    """A short explanatory paragraph under a table or figure."""
    size = r"\footnotesize " if small else ""
    return "\n" + r"\noindent{" + size + str(esc(text)) + "}\n\n"


def keep_with_next(lines: int = T.NEEDSPACE_HEADING_LINES) -> str:
    return r"\needspace{%d\baselineskip}" % lines + "\n"


def section_gap() -> str:
    return r"\vspace{%gpt}" % T.SECTION_GAP_PT + "\n"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Col:
    """A table column: header text, share of the table width, alignment."""
    title: str
    frac: float
    align: str = "l"


def column_spec(columns: Sequence[Col], width_fraction: float = T.TABLE_WIDTH_FRACTION) -> str:
    """Return the longtable column spec with widths that sum to the line width.

    Each ``p`` column is ``frac * width - 2*tabcolsep - share of the vertical
    rules``.  The ``(n+1)/n`` rule share is what keeps the table from being a
    fraction of a point wider than the text block.
    """
    total = sum(c.frac for c in columns)
    if total <= 0:
        raise ValueError("column fractions must be positive")
    n = len(columns)
    rule_share = (n + 1) / n
    parts = []
    for c in columns:
        if c.align not in _ALIGN_CMD:
            raise ValueError(f"unknown alignment {c.align!r}")
        f = c.frac / total * width_fraction
        parts.append(
            "%sp{\\dimexpr %.5f\\linewidth-2\\tabcolsep-%.4f\\arrayrulewidth\\relax}"
            % (_ALIGN_CMD[c.align], f, rule_share)
        )
    return "|" + "|".join(parts) + "|"


def _cells(cells: Iterable[Cell]) -> str:
    return " & ".join(str(esc(c)) for c in cells)


def _caption_block(caption: Optional[str], label: Optional[str], continued: bool) -> str:
    if not caption:
        return ""
    title = str(esc(caption))
    if continued:
        return (r"\caption*{\textbf{\tablename~\thetable:} \textbf{%s} \textit{%s}}\\*"
                % (title, T.CONTINUED_TEXT) + "\n")
    lab = r"\label{%s}" % label if label else ""
    return r"\caption{\textbf{%s}}%s\\*" % (title, lab) + "\n"


def _header_rows(columns: Sequence[Col], header_groups) -> str:
    n = len(columns)
    out = []
    if header_groups:
        spans, col = [], 1
        for title, span in header_groups:
            spans.append((title, col, span))
            col += span
        if col - 1 != n:
            raise ValueError("header_groups spans must cover every column")
        cells, rules = [], []
        for title, start, span in spans:
            if title:
                cells.append(MultiColumn(span, align="|c|", data=NoEscape(r"\textbf{%s}" % esc(title))).dumps())
                rules.append(r"\cline{%d-%d}" % (start, start + span - 1))
            else:
                cells.append(MultiColumn(span, align="c", data=NoEscape("")).dumps())
        # rule above the group titles, then the titles, then a rule under them
        out.append(" ".join(rules))
        out.append(" & ".join(c.rstrip("%\n ") for c in cells) + r" \\*")
        out.append(" ".join(rules))
    head = " & ".join(r"\textbf{%s}" % esc(c.title) if T.HEADER_BOLD else str(esc(c.title))
                      for c in columns)
    if T.TABLE_HEAD_FILL:
        head = r"\rowcolor[HTML]{%s} " % T.TABLE_HEAD_FILL + head
    out.append(r"\hline")
    out.append(head + r" \\")
    out.append(r"\hline")
    return "\n".join(out) + "\n"


def data_table(
    columns: Sequence[Col],
    rows: Sequence[Sequence[Cell]],
    caption: Optional[str] = None,
    label: Optional[str] = None,
    groups: Optional[Sequence[int]] = None,
    header_groups: Optional[Sequence[tuple]] = None,
    size: Optional[str] = None,
    width_fraction: float = T.TABLE_WIDTH_FRACTION,
    after: str = "",
) -> str:
    """Build a longtable and return its LaTeX.

    Args:
        columns: column definitions; fractions are normalised to sum to 1.
        rows: one sequence of cells per row (``len(row) == len(columns)``).
        caption: table title; the "Table x.y:" number is added by LaTeX.
        label: optional ``\\label`` key.
        groups: sizes of consecutive row groups that must not be split across
            pages, e.g. ``[6, 6, 6]``.  Only the first row of a group shows
            the group label (first column), and no horizontal rule is drawn
            between rows of one group, so the group reads as one merged cell
            without ``\\multirow``.
        header_groups: ``[(title, span), ...]`` for a merged super-header
            (``""`` title = no label above that span).
        size: a LaTeX size command (e.g. ``"\\small"``) scoped to this table.
        after: LaTeX appended after the table (kept inside the same group).
    """
    n = len(columns)
    for r in rows:
        if len(r) != n:
            raise ValueError(f"row has {len(r)} cells, table has {n} columns: {r!r}")
    if groups is not None and sum(groups) != len(rows):
        raise ValueError("group sizes must add up to the number of rows")

    table = LongTable(column_spec(columns, width_fraction))
    first = _caption_block(caption, label, continued=False)
    cont = _caption_block(caption, label, continued=True)
    head = _header_rows(columns, header_groups)

    # First-page head, then continuation head, foot and last foot.
    if first:
        table.append(NoEscape(first.rstrip("\n")))
    table.append(NoEscape(head.rstrip("\n")))
    table.append(NoEscape(r"\endfirsthead"))
    if cont:
        table.append(NoEscape(cont.rstrip("\n")))
    table.append(NoEscape(head.rstrip("\n")))
    table.end_table_header()                       # \endhead
    table.append(NoEscape(r"\multicolumn{%d}{r}{\footnotesize\textit{%s}} \\" % (n, T.CONTINUES_TEXT)))
    table.end_table_footer()                       # \endfoot
    table.end_table_last_footer()                  # \endlastfoot (no foot on the last page)

    first_in_group, last_in_group = set(), set()
    if groups:
        pos = 0
        for g in groups:
            first_in_group.add(pos)
            last_in_group.add(pos + g - 1)
            pos += g

    for i, row in enumerate(rows):
        cells = list(row)
        in_group = bool(groups)
        label_col_blank = in_group and i not in first_in_group
        if label_col_blank:
            cells[0] = NoEscape("")
        fill = ""
        if T.TABLE_ZEBRA_FILL and i % 2 == 1:
            fill = r"\rowcolor[HTML]{%s} " % T.TABLE_ZEBRA_FILL
        line = fill + _cells(cells)
        if in_group:
            if i in last_in_group:
                table.append(NoEscape(line + r" \\"))
                table.add_hline()
            else:
                # "\\*" forbids a page break after this row.  No rule is drawn inside
                # a group: longtable puts a legal break point after every \hline
                # (and \cline), which would let the group split.
                table.append(NoEscape(line + r" \\*"))
        else:
            table.append(NoEscape(line + r" \\"))
            table.add_hline()

    body = table.dumps()
    if size:
        body = "{" + size + "\n" + body + "\n}"
    return "\n" + body + "\n" + after + "\n"


def kv_table(
    pairs: Sequence[Sequence[Cell]],
    caption: Optional[str] = None,
    label: Optional[str] = None,
    header: Sequence[str] = ("Parameter", "Value"),
    fracs: Sequence[float] = (0.4, 0.6),
    **kwargs,
) -> str:
    """Two-column parameter/value table (the most common shape in the report)."""
    cols = [Col(header[0], fracs[0], "l"), Col(header[1], fracs[1], "l")]
    return data_table(cols, [tuple(p) for p in pairs], caption=caption, label=label, **kwargs)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def figure(path: Optional[str], caption: str, label: Optional[str] = None,
           max_height: str = T.FIGURE_MAX_HEIGHT, width: str = T.FIGURE_FULL_WIDTH,
           numbered: bool = False) -> str:
    """A centred figure with a height cap, built with PyLaTeX ``Figure``.

    With ``path=None`` a boxed placeholder with the same caption is produced, so
    a missing image never breaks the document.
    """
    if not path:
        return placeholder(caption)
    fig = Figure(position="H")
    fig.add_image(path.replace("\\", "/"),
                  width=NoEscape(r"%s,height=%s,keepaspectratio" % (width, max_height)))
    if numbered:
        fig.append(NoEscape(r"\caption{%s}%s" % (esc(caption), r"\label{%s}" % label if label else "")))
    else:
        fig.append(NoEscape(r"\caption*{\small %s}" % esc(caption)))
    return "\n" + fig.dumps() + "\n"


def placeholder(caption: str) -> str:
    """Boxed 'figure not available' block that keeps the layout and the caption."""
    return (
        "\n" + r"\begin{figure}[H]" + "\n" + r"\centering" + "\n"
        + r"\fbox{\parbox{0.97\linewidth}{\centering\textit{[ Figure not available: "
        + str(esc(caption)) + " ]}}}\n"
        + r"\caption*{\small " + str(esc(caption)) + "}\n" + r"\end{figure}" + "\n"
    )
