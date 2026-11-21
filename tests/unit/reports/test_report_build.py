"""End-to-end report builds: .osi -> design -> report.pdf, measured.

Each scenario runs the full design pipeline (about 20 s) and then the real report
generator, so these are marked ``slow``.  Skip them with ``pytest -m "not slow"``;
they also skip themselves when pdflatex or pdfplumber is missing.

Every scenario must satisfy the same layout contract (the acceptance criteria of
the report refactor): LaTeX compiles with no errors, no overfull boxes, no fancyhdr
warnings, no unclosed groups, nothing in the footer or past the right margin, no
orphaned headings and a repeating header on every longtable.  Scenario-specific
checks then confirm the report follows the inputs.
"""
import importlib.util
import os
import pathlib

import pytest

pdfplumber = pytest.importorskip("pdfplumber")

ROOT = pathlib.Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "fixtures" / "reports"
HARNESS = ROOT / "scripts" / "report_dev"

SCENARIOS = [
    "S1_default", "S2_long_span", "S3_vehicle_subset_footway",
    "S4_short_span", "S5_end_diaphragm_beam", "S6_custom_grades",
]

pytestmark = pytest.mark.slow


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HARNESS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def harness():
    return _load("make_report"), _load("check_layout")


@pytest.fixture(scope="session")
def build(pdflatex, harness, tmp_path_factory):
    make_report, _ = harness
    cache = {}

    def _build(name):
        if name not in cache:
            out = tmp_path_factory.mktemp(name)
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
            snap = make_report.run_design(str(FIXTURES / f"{name}.osi"))
            make_report.make_report(snap, str(out), "report")
            cache[name] = out
        return cache[name]

    return _build


def _text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def _flat(text):
    return " ".join(text.split())


@pytest.mark.parametrize("name", SCENARIOS)
def test_layout_contract(name, build, harness):
    _, layout = harness
    out = build(name)
    pdf, tex, log = out / "report.pdf", out / "report.tex", out / "report.log"
    assert pdf.exists() and tex.exists() and log.exists()

    c = layout.check_log(str(log))
    assert c == {"errors": 0, "overfull_hbox": 0, "overfull_vbox": 0,
                 "headheight_warnings": 0, "open_groups": 0}, c
    assert layout.check_footer(str(pdf)) == []
    assert layout.check_right_margin(str(pdf)) == []
    assert layout.check_orphan_headings(str(pdf)) == []
    h = layout.check_headers(str(tex))
    assert h["longtables"] > 40
    assert h["repeat_header"] == h["longtables"], h["missing"]


def test_saved_tex_has_no_absolute_paths(build):
    tex = (build("S1_default") / "report.tex").read_text(encoding="utf-8")
    assert "/tmp/" not in tex


def test_s1_fatigue_failure_is_reported(build):
    text = _text(build("S1_default") / "report.pdf")
    assert "Overall Design Status" in text
    assert "FAIL" in text
    assert "Design pass" not in text            # the old hard-coded verdict lines


def test_s3_vehicle_table_follows_the_ticks(build):
    text = _text(build("S3_vehicle_subset_footway") / "report.pdf")
    start = text.index("Vehicular Live Load (IRC")
    table = text[start:text.index("Footway Live Load", start)]
    assert "Class A" in table and "Class 70R (Wheeled)" in table and "Class SV" in table
    rows = [ln for ln in table.splitlines() if ln.startswith(("Class", "Fatigue"))]
    for unticked in ("Class AA", "Class 70R (Tracked)", "Class 70R (Bogie)", "Fatigue Vehicle"):
        assert not any(r.startswith(unticked) for r in rows), (unticked, rows)
    footway = text[text.index("Footway Live Load"):]
    assert "3.000 kN/m" in footway and "2 × 1.5 m" in footway


def test_s5_unsupported_diaphragm_type_is_explicit(build):
    text = _text(build("S5_end_diaphragm_beam") / "report.pdf")
    assert "Rolled Beam) is not designed in this version" in text.replace("\n", " ")


def test_s6_grades_follow_the_inputs(build):
    tex = (build("S6_custom_grades") / "report.tex").read_text(encoding="utf-8")
    assert "Concrete (M30)" in tex
    assert "Reinforcement Steel (Fe 415)" in tex
    assert "Fe 500 (" not in tex and "Reinforcement Steel (Fe 500)" not in tex
