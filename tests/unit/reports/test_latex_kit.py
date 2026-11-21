import re

import pytest
from pylatex import NoEscape

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.latex_kit import Col


def _cols():
    return [Col("Item", 0.3), Col("Value", 0.4, "r"), Col("Note", 0.3, "c")]


def test_escape_plain_text_and_passthrough():
    assert str(K.esc("a_b & 5% #1")).startswith(r"a\_\allowbreak{}b \& 5\% \#1")
    assert str(K.esc(NoEscape(r"$b_f$"))) == r"$b_f$"
    assert str(K.esc(None)) == T.MISSING
    assert "∠" not in str(K.esc("∠ 100"))


def test_missing_is_never_zero():
    tex = K.data_table(_cols(), [("x", None, "")])
    assert T.MISSING in tex


def test_column_widths_sum_to_line_width():
    spec = K.column_spec(_cols())
    fracs = [float(m) for m in re.findall(r"dimexpr ([0-9.]+)\\linewidth", spec)]
    assert pytest.approx(sum(fracs), abs=1e-4) == 1.0
    assert spec.startswith("|") and spec.endswith("|")


def test_bad_alignment_and_row_length_rejected():
    with pytest.raises(ValueError):
        K.column_spec([Col("a", 1, "x")])
    with pytest.raises(ValueError):
        K.data_table(_cols(), [("only", "two")])


def test_every_table_has_repeating_header_and_foot():
    tex = K.data_table(_cols(), [("a", "1", "n")], caption="Cap", label="tab:x")
    assert tex.count(r"\endfirsthead") == 1
    assert tex.count(r"\endhead") == 1
    assert tex.count(r"\endfoot") == 1
    assert tex.count(r"\endlastfoot") == 1
    assert T.CONTINUED_TEXT in tex and T.CONTINUES_TEXT in tex
    # order matters for longtable
    assert tex.index(r"\endfirsthead") < tex.index(r"\endhead") < tex.index(r"\endfoot") < tex.index(r"\endlastfoot")


def test_caption_line_always_ends_with_row_terminator():
    tex = K.data_table(_cols(), [("a", "1", "n")], caption="Cap")
    for line in tex.splitlines():
        if line.startswith(r"\caption"):
            assert line.rstrip("%").rstrip().endswith(r"\\*") or line.rstrip("%").rstrip().endswith(r"\\")


def test_groups_stay_together_with_star_and_no_multirow():
    rows = [("G1", "a", "1"), ("G1", "b", "2"), ("G2", "a", "3"), ("G2", "b", "4")]
    tex = K.data_table(_cols(), rows, groups=[2, 2])
    assert r"\multirow" not in tex
    body = tex.split(r"\endlastfoot")[1]
    assert body.count(r"\\*") == 2          # first row of each group blocks the break
    assert r"\cline" not in body and body.count(r"\hline") == 2   # rules only between groups
    # label shown only on the first row of a group
    assert body.count("G1") == 1 and body.count("G2") == 1


def test_group_sizes_validated():
    with pytest.raises(ValueError):
        K.data_table(_cols(), [("a", "b", "c")], groups=[2])


def test_merged_header_uses_multicolumn():
    cols = [Col("Vehicle", 0.4), Col("Considered", 0.2), Col("Value", 0.2), Col("Ecc", 0.2)]
    tex = K.data_table(cols, [("A", "Yes", "1", "2")], header_groups=[("", 1), ("Braking", 3)])
    assert r"\multicolumn{3}{|c|}" in tex and "Braking" in tex
    with pytest.raises(ValueError):
        K.data_table(cols, [("A", "Yes", "1", "2")], header_groups=[("", 1), ("Braking", 2)])


def test_kv_table_is_two_columns():
    tex = K.kv_table([("Span", "30 m")], caption="Geometry")
    assert tex.count("&") >= 3


def test_status_uses_single_pass_rule():
    assert r"urpass" in str(K.status(T.UR_LIMIT))
    assert r"urfail" in str(K.status(T.UR_LIMIT + 0.001))
    assert r"urna" in str(K.status(None))


def test_figure_without_path_is_placeholder_and_with_path_is_capped():
    assert "not available" in K.figure(None, "Cap")
    tex = K.figure("images/a.png", "Cap")
    assert r"keepaspectratio" in tex and T.FIGURE_MAX_HEIGHT in tex and r"\includegraphics" in tex


def test_table_compiles_cleanly_and_fits(compile_tex):
    rows = [(f"Item {i}", f"{i * 1.5:.2f}", "ok") for i in range(120)]
    body = K.data_table(_cols(), rows, caption="Long table", label="tab:long")
    rows_g = [(f"G{g}", f"P{r}", f"{g}.{r}") for g in range(1, 13) for r in range(6)]
    body += K.data_table(_cols(), rows_g, caption="Grouped", groups=[6] * 12)
    cols4 = [Col("Vehicle", 0.4), Col("On", 0.2), Col("Value", 0.2), Col("Ecc", 0.2)]
    body += K.data_table(cols4, [("A", "Yes", "1", "2")], caption="Merged",
                         header_groups=[("", 1), ("Braking Load", 3)])
    rc, log, pdf = compile_tex(r"\chapter{T}" + body)
    errors = [l for l in log.splitlines() if l.startswith("!")]
    assert errors == [] and rc == 0
    assert not re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log) or \
        max(float(x) for x in re.findall(r"Overfull \\hbox \(([0-9.]+)pt", log)) <= 1.0
    assert pdf.exists()


def test_groups_never_split_across_pages(compile_tex):
    pdfplumber = pytest.importorskip("pdfplumber")
    rows_g = [(f"G{g}", f"P{r}", f"{g}.{r}") for g in range(1, 15) for r in range(6)]
    body = K.data_table(_cols(), rows_g, caption="Grouped", groups=[6] * 14)
    rc, log, pdf = compile_tex(r"\chapter{T}" + body)
    assert rc == 0
    with pdfplumber.open(pdf) as doc:
        assert len(doc.pages) >= 3          # the table must span several pages to prove anything
        for page in doc.pages[1:]:
            data = [ln.split() for ln in (page.extract_text() or "").splitlines()
                    if re.match(r"^(G\d+ )?P\d ", ln)]
            if not data:
                continue
            assert data[0][-2] == "P0" or data[0][0].startswith("P0") or data[0][1] == "P0", data[0]
            assert data[-1][0] == "P5" or data[-1][1] == "P5", data[-1]
