"""Chapter modules must describe content only: all look-and-feel lives in theme.py,
preamble.py, latex_kit.py and charts.py (the single source of styling).

If this test fails you hard-coded a colour, length, table environment or rule in a
chapter file.  Use the kit (latex_kit.data_table / kv_table / figure / note) and add
any new visual constant to theme.py instead.
"""
import pathlib
import re

import pytest

REPORTS = pathlib.Path(__file__).resolve().parents[3] / "src" / "osdagbridge" / "core" / "reports"
CHAPTER_FILES = sorted(list(REPORTS.glob("chap*.py")) + [REPORTS / "executive_summary.py"])

# (regex, why)
FORBIDDEN = [
    (r"\\setlength", "lengths belong in theme.py"),
    (r"\\renewcommand", "global redefinitions belong in preamble.py"),
    (r"\\definecolor|\\textcolor|\\colorbox|\\rowcolor|\\color\{", "colours belong in theme.py (use K.status / K.pass_fail)"),
    (r"\\multirow", "use latex_kit row groups instead of multirow"),
    (r"\\\\\[\s*[0-9.]+\s*(pt|mm|cm|em|ex)\s*\]", "row padding comes from theme.ARRAYSTRETCH"),
    (r"\\hline|\\cline", "rules are drawn by the kit"),
    (r"\\begin\{(longtable|tabular|tabularx|table)\}", "tables are built with latex_kit.data_table / kv_table"),
    (r"\\begingroup|\\endgroup", "unbalanced groups leaked settings into later chapters; the kit scopes its own"),
    (r"\{\s*[0-9.]+\s*(cm|mm|pt)\s*\}", "hard-coded lengths belong in theme.py"),
    (r"\\vspace\{[^}]*\}", "use K.section_gap() so spacing comes from the theme"),
    (r"\\newpage|\\clearpage", "forced page breaks create half-empty pages; headings use needspace"),
]
# Chapter openings are the one place a page break is legitimate.
ALLOWED_PAGEBREAK = {"executive_summary.py"}


def _strip_comments(src: str) -> str:
    return "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))


@pytest.mark.parametrize("path", CHAPTER_FILES, ids=lambda p: p.name)
def test_chapter_has_no_hardcoded_styling(path):
    src = _strip_comments(path.read_text(encoding="utf-8"))
    problems = []
    for pattern, why in FORBIDDEN:
        if "newpage" in pattern and path.name in ALLOWED_PAGEBREAK:
            continue
        for m in re.finditer(pattern, src):
            line = src.count("\n", 0, m.start()) + 1
            problems.append(f"{path.name}:{line}: {m.group(0)!r}: {why}")
    assert not problems, "\n".join(problems)


def test_there_are_chapter_files_to_lint():
    assert len(CHAPTER_FILES) >= 10
