"""Hand calculations for the live-load rows (IRC 6:2017)."""
import pytest

from osdagbridge.core.reports import report_data as D
from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV, KEY_FOOTPATH, KEY_LL_ECCENTRICITY, KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE, KEY_LL_IRC_70R_BOGIE, KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_AA_WHEELED, KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV, KEY_SPAN, KEY_TS_FOOTPATH_WIDTH,
)

ALL = [KEY_LL_IRC_CLASS_A, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_AA_WHEELED,
       KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_CLASS_SV, KEY_LL_IRC_70R_BOGIE, KEY_LL_IRC_CLASS_FATIGUE]


def _inputs(ticked=ALL, span=30, **extra):
    d = {k: (k in ticked) for k in ALL}
    d.update({KEY_SPAN: str(span), KEY_LL_ECCENTRICITY: "1.2", KEY_BL_IRC_CLASS_SV: True})
    d.update(extra)
    return d


def _by_key(rows):
    return {r.key: r for r in rows}


def test_only_ticked_vehicles_appear_in_ui_order():
    rows = D.collect_vehicle_rows(_inputs(ticked=[KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_CLASS_A]))
    assert [r.key for r in rows] == ["class_a", "70r_wheeled"]
    assert D.collect_vehicle_rows(_inputs(ticked=[])) == []


def test_all_eight_ticked_gives_eight_rows():
    assert len(D.collect_vehicle_rows(_inputs())) == 8


def test_class_a_hand_calc_30m():
    r = _by_key(D.collect_vehicle_rows(_inputs()))["class_a"]
    assert r.total_kN == pytest.approx(543.474, abs=1e-3)       # 55.4 t x 9.81
    assert r.impact == pytest.approx(9 / 43.5, abs=1e-9)        # Cl. 208.2: 9/(13.5+30) = 0.207
    assert round(r.impact, 3) == 0.207
    assert r.braking_kN == pytest.approx(108.6948, abs=1e-3)    # 20 % of 543.474, no impact
    assert r.eccentricity_m == 1.2 and r.analysed


def test_70r_wheeled_hand_calc():
    r = _by_key(D.collect_vehicle_rows(_inputs()))["70r_wheeled"]
    assert r.total_kN == pytest.approx(981.0, abs=1e-6)         # 100 t
    assert r.braking_kN == pytest.approx(196.2, abs=1e-6)       # 20 %
    assert r.impact == pytest.approx(9 / 43.5)                  # L = 30 >= 23 -> Fig. 9 curve


def test_wheeled_and_tracked_impact_rules():
    assert D.impact_wheeled(15) == 0.25 and D.impact_wheeled(5) == 0.25
    assert D.impact_wheeled(23) == pytest.approx(9 / 36.5)
    assert D.impact_tracked(30) == 0.10 and D.impact_tracked(9) == 0.10
    assert D.impact_tracked(4) == 0.25
    assert D.impact_tracked(7) == pytest.approx(0.25 - 0.15 * 2 / 4)
    assert D.impact_class_a(30) == pytest.approx(9 / 43.5)
    assert D.impact_class_a(1) == pytest.approx(9 / 16.5)       # clamped to 3 m
    assert D.impact_class_a(100) == pytest.approx(9 / 58.5)     # clamped to 45 m


def test_tracked_and_wheeled_differ_for_the_same_span():
    rows = _by_key(D.collect_vehicle_rows(_inputs(span=15)))
    assert rows["70r_wheeled"].impact == 0.25 and rows["70r_tracked"].impact == 0.10
    assert rows["aa_wheeled"].impact == 0.25 and rows["aa_tracked"].impact == 0.10


def test_special_vehicle_has_no_impact_and_braking_follows_the_checkbox():
    on = _by_key(D.collect_vehicle_rows(_inputs()))["sv"]
    assert on.impact is None and "204.5.4" in on.impact_ref
    assert on.total_kN == pytest.approx(3776.85, abs=1e-2)
    assert on.braking_considered and on.braking_kN == pytest.approx(0.2 * 3776.85, abs=1e-2)
    off = _by_key(D.collect_vehicle_rows(_inputs(**{KEY_BL_IRC_CLASS_SV: False})))["sv"]
    assert off.braking_considered is False and off.braking_kN is None and off.eccentricity_m is None


def test_fatigue_truck_uses_half_the_wheeled_impact_and_no_braking():
    r = _by_key(D.collect_vehicle_rows(_inputs()))["fatigue"]
    assert r.impact == pytest.approx(0.5 * 9 / 43.5)
    assert r.braking_considered is None and r.braking_kN is None
    assert r.total_kN == pytest.approx(392.4, abs=1e-6)


def test_only_class_a_and_70r_wheeled_are_marked_analysed():
    rows = D.collect_vehicle_rows(_inputs())
    assert {r.key for r in rows if r.analysed} == {"class_a", "70r_wheeled"}


def test_missing_span_gives_no_impact_instead_of_a_wrong_number():
    d = _inputs()
    d[KEY_SPAN] = ""
    assert all(r.impact is None for r in D.collect_vehicle_rows(d) if r.key != "sv")


def test_footway_default_and_custom():
    d = _inputs()
    f = D.collect_footway(d)
    assert not f.present and f.footpaths == 0
    d.update({KEY_FOOTPATH: "Both Sides", KEY_TS_FOOTPATH_WIDTH: "1.5"})
    f = D.collect_footway(d)
    assert f.present and f.footpaths == 2 and f.intensity_kN_m2 == pytest.approx(4.905)
    assert f.line_load_kN_m == pytest.approx(4.905 * 1.5) and "208.4" in f.impact_note
    d.update({KEY_LL_FOOTPATH_PRESSURE_MODE: "Custom", KEY_LL_FOOTPATH_PRESSURE_VALUE: "3.0"})
    f = D.collect_footway(d)
    assert f.intensity_kN_m2 == 3.0 and f.line_load_kN_m == pytest.approx(4.5) and f.clause == "User-defined"
