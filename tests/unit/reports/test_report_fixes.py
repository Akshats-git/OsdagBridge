"""Regression tests for defects found in the original report."""
from types import SimpleNamespace

from osdagbridge.core.reports import preamble
from osdagbridge.core.reports.chap2 import _dim_mm

KEY = "member_properties.girder_details.section_input.depth"


def test_girder_dimensions_are_printed_in_mm():
    # Design converts the dimensions to metres; the report must not label them "mm" as is.
    assert _dim_mm({f"{KEY}.G1.M1": 1.67}, KEY, 1) == "1670 mm"
    assert _dim_mm({f"{KEY}.G1.M1": 0.022}, KEY, 1) == "22 mm"
    assert _dim_mm({f"{KEY}.G1.M1": 1670.0}, KEY, 1) == "1670 mm"       # an input still in mm
    assert _dim_mm({}, KEY, 1) is None                                  # missing stays missing


def test_page_numbers_continue_after_the_title_page():
    meta = SimpleNamespace(project_name="P", project_location="L", designer="D", reviewer="R", company="C",
                           client="K", job_number="J", report_date="2026-01-01", subtitle=None)
    tex = preamble.title_page(meta, None, None)
    # \begin{titlepage} restarts the counter at 1, so the table of contents would be "page 1" again
    assert tex.rstrip().endswith(r"\setcounter{page}{2}")
    assert "Rev 0" in tex                                                # empty version falls back


def test_title_page_uses_the_organisation_logo_only_when_present():
    meta = SimpleNamespace(project_name="P", project_location="", designer="", reviewer="", company="",
                           client="", job_number="", report_date="", subtitle="Rev 1")
    assert tex_minipages(preamble.title_page(meta, "a.png", "b.png")) == 2
    assert tex_minipages(preamble.title_page(meta, "a.png", None)) == 1


def tex_minipages(tex):
    return tex.count(r"\begin{minipage}")
