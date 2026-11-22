"""UR rows, element verdicts, end-diaphragm isolation and the UR chart."""
import pathlib
import re

import pytest

from osdagbridge.core.reports import report_data as D

REPORTS = pathlib.Path(__file__).resolve().parents[3] / "src" / "osdagbridge" / "core" / "reports"


def _design(eff, cap=100.0):
    return {"Member.efficiency": eff, "Member.tension_capacity": cap, "Member.Slenderness": 120.0,
            "section_size.designation": "ISA 75x75x8"}


def _pairs(gov="LC1"):
    return {"pairs": {"G1-G2": {f"{p}_{t}_gov_lc": gov for p in ("diag", "chord")
                                for t in ("tension", "compression")}}}


def _cb_ed_output(cb_ur, ed_ur=None):
    od = {"crossbracing_forces_dict": _pairs("CB-LC"),
          "crossbracing_design_results": {"G1-G2": {m: {"tension": _design(cb_ur / 2), "compression": _design(cb_ur)}
                                                    for m in ("diagonal", "chord")}},
          "end_diaphragm_forces_dict": _pairs("ED-LC"),
          "end_diaphragm_design_results": {"G1-G2": {}}}
    if ed_ur is not None:
        od["end_diaphragm_design_results"] = {
            "G1-G2": {m: {"tension": _design(ed_ur / 2), "compression": _design(ed_ur)}
                      for m in ("diagonal", "chord")}}
    return od


def _row(rows, label):
    return next(r for r in rows if r.label == label)


def test_status_uses_single_rule():
    assert D.URRow("Girder", "x", ur=1.0).status == "PASS"       # UR <= 1.0 passes
    assert D.URRow("Girder", "x", ur=1.0001).status == "FAIL"
    assert D.URRow("Girder", "x", ur=None).status == "n/a"


def test_end_diaphragm_never_shows_cross_bracing_values():
    rows = D.collect_ur_rows({}, _cb_ed_output(cb_ur=0.9))
    cb = _row(rows, "Cross Bracing --- Compression")
    ed = _row(rows, "End Diaphragm --- Compression")
    assert cb.ur == pytest.approx(0.9) and cb.gov_lc == "CB-LC"
    assert ed.ur is None and ed.status == "n/a" and ed.message


def test_end_diaphragm_reads_its_own_results():
    rows = D.collect_ur_rows({}, _cb_ed_output(cb_ur=0.9, ed_ur=1.3))
    ed = _row(rows, "End Diaphragm --- Compression")
    assert ed.ur == pytest.approx(1.3) and ed.gov_lc == "ED-LC" and ed.status == "FAIL"
    assert ed.demand == "130.00 kN" and ed.capacity == "100.000 kN"      # demand = UR x capacity
    assert _row(rows, "Cross Bracing --- Compression").ur == pytest.approx(0.9)


def test_missing_results_are_not_zero():
    rows = D.collect_ur_rows({}, {})
    assert all(r.ur is None for r in rows)
    assert all(r.status == "n/a" for r in rows)


def test_element_verdicts_fail_pass_na():
    rows = D.collect_ur_rows({}, _cb_ed_output(cb_ur=0.9, ed_ur=1.3))
    v = D.element_verdicts(rows)
    assert v["Cross bracing"] == ("PASS", pytest.approx(0.9))
    assert v["End diaphragm"][0] == "FAIL"
    assert v["Girder"] == ("n/a", None) and v["Deck"] == ("n/a", None)


def test_one_failing_row_fails_the_element():
    rows = [D.URRow("Girder", "a", ur=0.4), D.URRow("Girder", "b", ur=1.58)]
    assert D.element_verdicts(rows)["Girder"] == ("FAIL", 1.58)


def test_chart_is_vector_pdf_and_marks_na(tmp_path):
    from osdagbridge.core.reports import charts
    rows = [D.URRow("Girder", "Girder --- Moment", ur=0.5), D.URRow("Girder", "Girder --- Fatigue", ur=1.58),
            D.URRow("End diaphragm", "End Diaphragm --- Tension")]
    out = charts.ur_chart(rows, str(tmp_path / "c.pdf"))
    assert out and (tmp_path / "c.pdf").read_bytes().startswith(b"%PDF")
    fig = charts.ur_figure(rows)
    texts = [t.get_text() for t in fig.axes[0].texts]
    assert "n/a" in texts and "0.50" in texts and "1.58" in texts
    colours = {p.get_facecolor()[:3] for p in fig.axes[0].patches}
    assert len(colours) == 2                                          # pass colour and fail colour


def test_charts_never_import_pyplot():
    src = (REPORTS / "charts.py").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines() if re.match(r"\s*(import|from)\s", ln) or "(" in ln)
    assert not re.search(r"import\s+.*pyplot|from\s+\S*pyplot|matplotlib\.use\(|rcParams\.update\(", code)


def test_quantity_charts_draw_values_and_na(tmp_path):
    from osdagbridge.core.reports import charts
    q = {"steel_girders_wt_total_num": 32.89, "bracing_top_wt_total_num": 0.11, "end_diaphragm_wt_total_num": None,
         "concrete_deck_vol_total_num": 63.0, "crash_barrier_vol_total_num": None, "rebar_deck_wt_total_num": 7.56}
    steel = [t.get_text() for t in charts.steel_tonnage_figure(q).axes[0].texts]
    assert "32.89" in steel and steel.count("N.A.") == 4          # ED + 3 groups without data
    made = charts.quantity_charts(q, str(tmp_path))
    assert set(made) == {"steel_chart", "concrete_chart"}
    assert all((tmp_path / f).read_bytes().startswith(b"%PDF") for f in made.values())


def test_ur_chart_has_ur_on_the_y_axis_and_a_horizontal_limit_line():
    from osdagbridge.core.reports import charts, theme
    rows = [D.URRow("Girder", "Girder --- Moment", ur=0.5), D.URRow("Girder", "Girder --- Fatigue", ur=1.58)]
    ax = charts.ur_figure(rows).axes[0]
    assert "tilisation ratio" in ax.get_ylabel()
    (limit,) = [ln for ln in ax.lines if ln.get_linestyle() == "--"]
    assert list(limit.get_ydata()) == [theme.UR_LIMIT, theme.UR_LIMIT]       # horizontal
    assert limit.get_color() == theme.hex_color(theme.CHART_LIMIT_COLOR)
