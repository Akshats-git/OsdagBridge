"""Bill of quantities: end diaphragm row, numeric companions, crash-barrier units."""
import pytest

from osdagbridge.core.boq.boq_generator import _barrier_area_m2, calculate_material_quantities
from osdagbridge.core.utils.common import KEY_SPAN, KEY_TS_NO_OF_GIRDERS

ED = "transverse_member_design.ed.section_properties.end_diaphragm."
TYPE = "member_properties.end_diaphragm_details.type."


def _inputs(**extra):
    d = {KEY_SPAN: "30", KEY_TS_NO_OF_GIRDERS: "4"}
    d.update(extra)
    return d


def _ed_outputs(kind):
    o = {}
    for pair in ("G1G2", "G2G3", "G3G4"):
        o[ED + pair + ".A"] = 45.0          # cm2
        o[ED + pair + ".L"] = 2.1           # m
        o[TYPE + pair + ".E1M1"] = kind
    return o


def test_beam_end_diaphragm_hand_calc():
    q = calculate_material_quantities(_inputs(), _ed_outputs("Rolled Beam"))
    # 3 bays x 2 supports = 6 members, each 45 cm2 x 2.1 m = 0.00945 m3
    assert q["end_diaphragm_qty"] == "6"
    assert q["end_diaphragm_vol_total_num"] == pytest.approx(6 * 0.0045 * 2.1, abs=0.005)
    assert q["end_diaphragm_wt_total"] == "0.45"            # 0.0567 m3 x 7.85 t/m3
    assert q["end_diaphragm_wt_single"] == "0.0742"


def test_bracing_type_end_diaphragm_is_not_estimated():
    q = calculate_material_quantities(_inputs(), _ed_outputs("Cross Bracing"))
    assert q["end_diaphragm_qty"] == "N.A." and q["end_diaphragm_wt_total_num"] is None


def test_numeric_companions_are_none_for_na():
    q = calculate_material_quantities({}, {})
    assert q["steel_girders_wt_total_num"] is None and q["concrete_deck_vol_total_num"] is None


@pytest.mark.parametrize("raw, expected", [(0.3023, 0.3023), (302282.768, 0.302282768), (500, 0.0), ("x", 0.0), (0, 0.0)])
def test_crash_barrier_area_units(raw, expected):
    assert _barrier_area_m2(raw) == pytest.approx(expected)


def test_crash_barrier_in_m2_is_not_reported_as_zero():
    q = calculate_material_quantities(_inputs(**{"typical_section.crash_barrier.area": 0.3023}), {})
    assert q["crash_barrier_qty"] == "2"
    assert q["crash_barrier_vol_total_num"] == pytest.approx(2 * 0.3023 * 30, abs=0.005)
