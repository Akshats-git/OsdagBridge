# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR
)

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports import report_data as D
from osdagbridge.core.reports.latex_kit import Col, Span
from osdagbridge.core.reports.report_utils import get_girder_entries, val

if TYPE_CHECKING:
    pass

M = K.raw                      # LaTeX fragment that must not be escaped


def _num(v, nd=2):
    """Formatted number or None (never '0.00' for a missing value)."""
    try:
        if v is None or v == "":
            return None
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return None


def _with(v, unit):
    """'<v> <unit>' (unit may hold LaTeX) or None when v is missing."""
    if v is None:
        return None
    return K.join(v, M(" " + unit)) if unit else v


def _le(provided, required):
    """PASS when provided >= required (e.g. capacity vs demand)."""
    try:
        return "PASS" if float(provided) >= float(required) else "FAIL"
    except (TypeError, ValueError):
        return None


def _grouped(entries, make_rows):
    """Rows for a per-girder table: the girder label opens each group of rows."""
    rows, groups = [], []
    for gi, (lbl, _) in enumerate(entries, start=1):
        rs = make_rows(lbl, gi)
        rows.extend((lbl,) + tuple(r) for r in rs)
        groups.append(len(rs))
    return rows, groups


def _band_status(ratio):
    """Engine bands for interaction/LTB: PASS < 0.90, WARN < 1.00, FAIL otherwise."""
    if ratio < 0.90:
        return "PASS"
    if ratio < T.UR_LIMIT:
        return "WARN"
    return "FAIL"


def _ur_cell(v):
    """UR with 2 decimals, in the FAIL colour above the limit; None -> dash."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    txt = f"{f:.2f}"
    return M(r"\urfail{%s}" % txt) if not T.ur_passes(f) else txt


PAIR = [Col("Girder", 0.13, "c")]   # leading label column of per-girder tables


def ch5_design_checks(checks_data, bridge, fig_paths=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    """
    od = bridge.output_dict
    idc = bridge.input_dict
    entries = get_girder_entries(idc)
    if not entries:
        n = int(idc.get(KEY_TS_NO_OF_GIRDERS, 1))
        entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]

    out = [r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}
"""]
    out += _girder_tables(od, idc, entries)
    out += _shear_connector_tables(od, idc)
    out.append(_deck_section(bridge, od, idc))
    out.append(_cross_bracing_section(bridge, od))
    out.append(_end_diaphragm_section(bridge, od))
    out.append(_overall_summary(bridge, od, idc, fig_paths or {}))
    return "".join(out)


# ---------------------------------------------------------------------------
# 5.1  Plate girder
# ---------------------------------------------------------------------------

def _girder_tables(od, idc, entries):
    t = []
    g3 = [Col("Girder", 0.115, "c"), Col("Parameter", 0.315), Col("Formula", 0.25),
          Col("Value", 0.20, "c"), Col("Status", 0.12, "c")]

    # Table 5.1 — section properties
    props = [
        (r"Depth, D (mm)", KEY_SD_TOTAL_DEPTH),
        (r"Top Flange Width, $b_f$ (mm)", KEY_SD_TOP_FLANGE_WIDTH),
        (r"Bottom Flange Width, $b_f$ (mm)", KEY_SD_BOTTOM_FLANGE_WIDTH),
        (r"Top Flange Thickness, $t_f$ (mm)", KEY_SD_TOP_FLANGE_THICKNESS),
        (r"Bottom Flange Thickness, $t_f$ (mm)", KEY_SD_BOTTOM_FLANGE_THICKNESS),
        (r"Web Thickness, $t_w$ (mm)", KEY_SD_WEB_THICKNESS),
        (r"Gross Area, A (cm$^2$)", KEY_SD_SECTION_PROP_AREA),
        (r"Moment of Inertia, $I_z$ (cm$^4$)", KEY_SD_SECTION_PROP_IZ),
        (r"Elastic Section Modulus, $Z_{ez}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZZ),
        (r"Plastic Section Modulus, $Z_{pz}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZUZ),
        (r"Effective Slab Width, $b_{eff}$ (mm)", KEY_SD_EFFECTIVE_SLAB_WIDTH),
        (r"Transformed Composite $I_z$ (cm$^4$)", KEY_SD_COMPOSITE_IZ),
        (r"Depth to Plastic Neutral Axis (mm)", KEY_SD_PNA_DEPTH),
    ]
    rows, groups = _grouped(entries, lambda lbl, gi: [(M(title), val(od, k)) for title, k in props])
    t.append(K.data_table([Col("Girder", 0.16, "c"), Col("Property", 0.52), Col("Value", 0.32, "c")],
                          rows, caption="Girder Section Properties (Final Optimized / User-selected)",
                          groups=groups))

    # Table 5.2 — section classification
    rows, groups = _grouped(entries, lambda lbl, gi: [
        ("Top Flange", val(od, KEY_SD_FLANGE_SLENDERNESS), val(od, KEY_SD_FLANGE_CLASS_LIMIT), val(od, KEY_SD_CLASS_FLANGE)),
        ("Web", val(od, KEY_SD_WEB_SLENDERNESS), val(od, KEY_SD_WEB_CLASS_LIMIT), val(od, KEY_SD_CLASS_WEB)),
        ("Overall Section", None, None, val(od, KEY_SD_SECTION_CLASS)),
    ])
    t.append(K.data_table([Col("Girder", 0.15, "c"), Col("Element", 0.19), Col("Slenderness Ratio", 0.22, "c"),
                           Col("Class Limit", 0.16, "c"), Col("Classification", 0.28, "c")],
                          rows, caption="Girder Section Classification", groups=groups))
    t.append(K.note("Note: IS 800:2007 Table 2", small=False))

    # Flexure / shear / ... URs are stored as percent (cat_urs x 100) -> ratio.
    def _ratio(key):
        try:
            return float(od.get(key)) / 100.0
        except (TypeError, ValueError):
            return None

    flex = _ratio(KEY_UTIL_FLEXURE)
    flex_st = ("PASS" if T.ur_passes(flex) else "FAIL") if flex is not None else None
    rows, groups = _grouped(entries, lambda lbl, gi: [
        (M(r"Applied Moment, $M_u$"), "Governing LC (ULS)", _with(val(od, KEY_SD_MU_APPLIED), "kN-m"), None),
        (M(r"Design Moment Capacity, $M_d$"), "IRC 22 Cl. 603.3.1", _with(val(od, KEY_SD_MD_CAPACITY), "kN-m"), None),
        (M(r"Utilization Ratio, $M_u / M_d$"), M(r"$M_u / M_d$"), _num(flex), K.pass_fail(flex_st)),
    ])
    t.append(K.data_table(g3, rows, caption="Moment Capacity Check", groups=groups))
    t.append(K.note("Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1", small=False))

    shear = _ratio(KEY_UTIL_SHEAR)
    shear_st = ("PASS" if T.ur_passes(shear) else "FAIL") if shear is not None else None
    rows, groups = _grouped(entries, lambda lbl, gi: [
        (M(r"Applied Shear, $V_u$"), "Governing LC (ULS)", _with(val(od, KEY_SD_SHEAR_VU), "kN"), None),
        (M(r"Shear Area, $A_v$"), M(r"$d_w \times t_w$"), _with(val(od, KEY_SD_SHEAR_AV), "mm$^2$"), None),
        ("Panel Aspect Ratio, c/d", None, val(od, KEY_SD_PANEL_CD), None),
        (M(r"Shear Buckling Coefficient, $k_v$"), "IS 800 Cl. 8.4.2.2", val(od, KEY_SD_SHEAR_KV), None),
        (M(r"Web Slenderness, $\lambda_w$"), M(r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$"), val(od, KEY_SD_SHEAR_LAMBDA_W), None),
        (M(r"Design Shear Stress, $\tau_b$"), "IRC 22 Cl. 603.3.3.2", _with(val(od, KEY_SD_SHEAR_TAU_B), "MPa"), None),
        (M(r"Shear Buckling Resistance, $V_{cr}$"), M(r"$A_v \times \tau_b$"), _with(val(od, KEY_SD_SHEAR_VCR), "kN"), None),
        (M(r"Utilization Ratio, $V_u / V_d$"), M(r"$V_u / V_d$"), _num(shear), K.pass_fail(shear_st)),
    ])
    t.append(K.data_table(g3, rows, caption="Shear Capacity Check", groups=groups))
    t.append(K.note("Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2", small=False))

    mv = _ratio(KEY_UTIL_INTERACTION)
    mv_st = _band_status(mv) if mv is not None else None
    mn_r, mn_ax, mn_mo = od.get(KEY_SD_MN_RATIO), od.get(KEY_SD_MN_AXIAL), od.get(KEY_SD_MN_MOMENT)
    if mn_r is None or mn_ax is None or mn_mo is None:
        mn_cond, mn_val, mn_st = "N/A", "N/A", "N/A"
    else:
        mn_cond, mn_val, mn_st = f"{mn_ax:.2f} + {mn_mo:.2f} = {mn_r:.3f}", f"{mn_r:.3f}", _band_status(mn_r)
    rows, groups = _grouped(entries, lambda lbl, gi: [
        ("High Shear Condition?", M(r"$V_u > 0.6\,V_d$"), val(od, KEY_SD_HIGH_SHEAR), None),
        (M(r"Reduced Moment Capacity, $M_{dv}$"), "IRC 22 Cl. 603.3.3.3", _with(val(od, KEY_SD_MDV), "kN-m"), None),
        (M(r"Interaction Check: $M_u \leq M_{dv}$"), None, _num(mv), K.pass_fail(mv_st)),
        (M(r"Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$"), mn_cond, mn_val, K.pass_fail(mn_st)),
    ])
    t.append(K.data_table([Col("Girder", 0.115, "c"), Col("Check", 0.335), Col("Condition", 0.25),
                           Col("Value", 0.18, "c"), Col("Status", 0.12, "c")],
                          rows, caption="Interaction Checks (M-V and M-N)", groups=groups))
    t.append(K.note("Note: IRC 22 Cl. 603.3.3.3", small=False))

    ltb = _ratio(KEY_UTIL_LTB)
    ltb_st = _band_status(ltb) if ltb is not None else None
    rows, groups = _grouped(entries, lambda lbl, gi: [
        (M(r"Elastic Critical Moment, $M_{cr}$"), "IRC 22 Cl. 603.3.3.1", _with(val(od, KEY_SD_LTB_MCR), "kN-m"), None),
        (M(r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$"), M(r"$\sqrt{M_p / M_{cr}}$"), val(od, KEY_SD_LTB_LAMBDA), None),
        (M(r"LTB Reduction Factor, $\chi_{LT}$"), "IS 800 Cl. 8.2.2", val(od, KEY_SD_LTB_CHI), None),
        (M(r"LTB Resistance, $M_b$"), M(r"$\chi_{LT}\,M_p / \gamma_{m0}$"), _with(val(od, KEY_SD_LTB_MB), "kN-m"), None),
        (M(r"$M_u \leq M_b$"), M(r"$M_u / M_b$"), _num(ltb), K.pass_fail(ltb_st)),
    ])
    t.append(K.data_table(g3, rows, caption="Lateral Torsional Buckling Check -- Construction Stage",
                          groups=groups))
    t.append(K.note("Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2", small=False))

    # Stiffeners
    rows, groups = _grouped(entries, lambda lbl, gi: [
        ("Shear Buckling Design Method", val(od, KEY_SD_STIFF_METHOD)),
        ("Intermediate Stiffener Thickness (mm)", val(od, KEY_SD_STIFF_INT_THICK)),
        ("Intermediate Stiffener Spacing (mm)", val(od, KEY_SD_STIFF_INT_SPACING)),
        ("End Panel Stiffener Thickness (mm)", val(od, KEY_SD_STIFF_END_THICK)),
        ("No. of End Panel Stiffeners", val(od, KEY_SD_STIFF_END_COUNT)),
        ("Longitudinal Stiffeners", val(od, KEY_SD_STIFF_LONG)),
    ])
    t.append(K.data_table([Col("Girder", 0.16, "c"), Col("Parameter", 0.42), Col("Value", 0.42)],
                          rows, caption="Stiffener Design Summary", groups=groups))

    # Intermediate stiffener checks exist only when stiffener sizes were user-supplied.
    if str(idc.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}:
        iys = _le(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))
        fqd = _le(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))
        rows, groups = _grouped(entries, lambda lbl, gi: [
            (M(r"Min. Moment of Inertia, $I_s$"), _with(val(od, KEY_SD_IS_IYS_MIN), "mm$^4$"),
             _with(val(od, KEY_SD_IS_IYS_PROV), "mm$^4$"), K.pass_fail(iys)),
            (M(r"Buckling Resistance, $F_{qd} \geq F_q$"), _with(val(od, KEY_SD_IS_FQ), "kN"),
             _with(val(od, KEY_SD_IS_FQD), "kN"), K.pass_fail(fqd)),
        ])
        t.append(K.data_table([Col("Girder", 0.115, "c"), Col("Check", 0.305), Col("Required", 0.20, "c"),
                               Col("Provided", 0.26, "c"), Col("Status", 0.12, "c")],
                              rows, caption="Intermediate Stiffener Checks", groups=groups))
        t.append(K.note("Note: IS 800 Cl. 8.7.1.2", small=False))

    # End panel / bearing stiffener checks (IS 800 Cl. 8.7.3)
    bs_r = od.get(KEY_SD_BS_R)

    def _bs(key):
        prov = od.get(key)
        if prov is None or float(prov) <= 0.0 or bs_r is None:     # guidance-only mode
            return ("N/A", "N/A", "N/A")
        return (f"{bs_r} kN", f"{prov} kN", _le(prov, bs_r))

    bs = {k: _bs(k) for k in (KEY_SD_BS_FCDW_WB, KEY_SD_BS_FCDW_LC, KEY_SD_BS_FPSD, KEY_SD_BS_FCD)}
    names = [("Web Buckling Resistance", KEY_SD_BS_FCDW_WB), ("Local Crushing Resistance", KEY_SD_BS_FCDW_LC),
             ("Bearing Capacity", KEY_SD_BS_FPSD), ("Column Buckling Resistance", KEY_SD_BS_FCD)]
    rows, groups = _grouped(entries, lambda lbl, gi: [
        (nm, bs[k][0], bs[k][1], K.pass_fail(bs[k][2])) for nm, k in names])
    t.append(K.data_table([Col("Girder", 0.115, "c"), Col("Check", 0.305), Col("Required", 0.20, "c"),
                           Col("Provided", 0.26, "c"), Col("Status", 0.12, "c")],
                          rows, caption="End Panel Stiffener Checks", groups=groups))
    t.append(K.note("Note: IS 800 Cl. 8.4.2.2", small=False))

    # Serviceability: deflection (allowable from span; actual from the per-girder cache values)
    try:
        span_m = float(idc.get(KEY_SPAN))
        allow_live, allow_total = span_m * 1000.0 / 800.0, span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        allow_live = allow_total = None
    al_s = f"L/800 = {allow_live:.1f} mm" if allow_live is not None else None
    at_s = f"L/600 = {allow_total:.1f} mm" if allow_total is not None else None

    def _defl_rows(lbl, gi):
        live = od.get(f"{KEY_SD_DEFL_LIVE}.G{gi}")
        total = od.get(f"{KEY_SD_DEFL_TOTAL}.G{gi}")
        return [
            (M(r"Live Load Deflection, $\delta_{LL}$ (mm)"), al_s, _num(live, 3),
             K.pass_fail(_le(allow_live, live) if allow_live is not None and live is not None else None)),
            (M(r"Total Load Deflection, $\delta_{total}$ (mm)"), at_s, _num(total, 3),
             K.pass_fail(_le(allow_total, total) if allow_total is not None and total is not None else None)),
        ]
    rows, groups = _grouped(entries, _defl_rows)
    t.append(K.data_table([Col("Girder", 0.115, "c"), Col("Check", 0.325), Col("Allowable", 0.20, "c"),
                           Col("Actual", 0.24, "c"), Col("Status", 0.12, "c")],
                          rows, caption="Serviceability -- Deflection Checks", groups=groups))
    t.append(K.note("Note: IRC 22 Cl. 604.3.2", small=False))

    # Serviceability: steel stress (single envelope-SLS value; allowable 0.9 fy)
    dr = od.get("design_results", {}) or {}
    sig, allow = dr.get(KEY_SD_STRESS_STEEL), dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    stress_rows = [(lbl, M(r"Structural Steel ($0.9\,f_y$)"), _with(_num(allow), "MPa"),
                    _with(_num(sig), "MPa"), K.pass_fail(_le(allow, sig))) for lbl, _ in entries]
    t.append(K.data_table([Col("Girder", 0.115, "c"), Col("Element", 0.285), Col("Allowable Stress", 0.22, "c"),
                           Col("Actual Stress", 0.26, "c"), Col("Status", 0.12, "c")],
                          stress_rows, caption="Serviceability -- Maximum Stress Limitation"))

    # Serviceability: fatigue (governing of normal / shear by DCR)
    fat = ((dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {})
    fat_rows = []
    for gi, (lbl, _) in enumerate(entries, start=1):
        g = fat.get(f"G{gi}", {}) or {}
        fat_rows.append((lbl, _with(_num(g.get("demand")), "MPa"), _with(_num(g.get("capacity")), "MPa"),
                         _num(g.get("ur")), K.pass_fail(g.get("status"))))
    t.append(K.data_table([Col("Girder", 0.13, "c"), Col(M(r"Stress Range, $\Delta\sigma$ (MPa)"), 0.25, "c"),
                           Col(M(r"Fatigue Limit, $f_{fd}$ (MPa)"), 0.25, "c"), Col("Utilization Ratio", 0.22, "c"),
                           Col("Status", 0.15, "c")],
                          fat_rows, caption="Serviceability -- Fatigue Assessment"))
    t.append(K.note(M(r"Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). "
                      r"Capacity reduction factor $\mu_r$ applied where plate thickness $>$ 25 mm."), small=False))

    # Girder design summary (controlling check per girder)
    pg = dr.get("per_girder", {}) or {}

    def _unit(value, unit):
        s = _num(value)
        if s is None:
            return None
        return (s + " " + unit) if unit and str(unit) not in ("-", "\u2013") else s

    summ = []
    for gi, (lbl, _) in enumerate(entries, start=1):
        gd = pg.get(f"G{gi}", {}) or {}
        checks = gd.get("checks") or []
        if not checks:
            summ.append((lbl, None, None, None, None, None, None))
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        ctrl_lc, best = None, None
        for lc_name, lc_data in (gd.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best:
                        best, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (gd.get("demand") or {}).get("governing_combination") or None
        summ.append((lbl, str(ctrl_lc) if ctrl_lc else None, ctrl.get("name") or None,
                     _unit(ctrl.get("demand"), ctrl.get("demand_unit")),
                     _unit(ctrl.get("capacity"), ctrl.get("capacity_unit")),
                     _num(ctrl.get("dcr"), 3), K.pass_fail(ctrl.get("status"))))
    t.append(K.data_table([Col("Girder", 0.10, "c"), Col("Controlling LC / Combination", 0.25, "c"),
                           Col("Controlling Check", 0.17, "c"), Col("Demand", 0.14, "c"),
                           Col("Capacity", 0.15, "c"), Col("UR", 0.09, "c"), Col("Status", 0.10, "c")],
                          summ, caption="Girder Design Summary (DCR / Utilization Ratio)", compact=True))
    t.append(K.note(M(r"Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling "
                      r"check is the criterion with the highest UR for each girder, with the real load "
                      r"case/combination that drives it."), small=False))
    return t


# ---------------------------------------------------------------------------
# 5.1 (cont.)  Shear connectors
# ---------------------------------------------------------------------------

def _shear_connector_tables(od, idc):
    t = []
    dr = od.get("design_results", {}) or {}

    def kn(v):
        return _with(_num(v), "kN")

    def mm(v, nd=1):
        return _with(_num(v, nd), "mm")

    t.append(K.data_table(
        [Col("Parameter", 0.24), Col("Formula", 0.36, "c"), Col("Value", 0.16, "c"), Col("Reference", 0.24)],
        [(M(r"Design Resistance, $Q_u$"),
          M(r"\footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$"
            r"\\$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$}"),
          kn(dr.get(KEY_SD_SC_Qu_kN)), "IRC 22 Cl. 606.3.1 (Eq. 6.1)"),
         (M(r"Fatigue Shear Resistance, $Q_r$"), M(r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)"),
          kn(dr.get(KEY_SD_SC_Qr_kN)), "IRC 22 Cl. 606.3.2 (Table 8)")],
        caption="Shear Connector Capacity"))

    prov = dr.get("stud_spacing_provided_mm")

    def sp(crit, req):
        return (crit, mm(req), mm(prov), K.pass_fail(_le(req, prov)))

    t.append(K.data_table(
        [Col("Criterion", 0.28), Col("Governing Spacing", 0.28, "c"), Col("Actual Spacing Provided", 0.28, "c"),
         Col("Status", 0.16, "c")],
        [sp("ULS Shear (SL1)", dr.get(KEY_SD_SC_SL1)), sp("Full Composite (SL2)", dr.get(KEY_SD_SC_SL2)),
         sp("SLS Fatigue (SR)", dr.get(KEY_SD_SC_SR)), sp("Max Spacing Limit (IRC 22)", dr.get("stud_spacing_max_mm"))],
        caption="Shear Connector Spacing"))
    t.append(K.note(M(r"Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$."), small=False))

    # Transverse shear and detailing
    vl, vrd = dr.get(KEY_SD_TS_VL), dr.get(KEY_SD_TS_VRD)
    try:
        ur = f"{float(vl) / float(vrd):.2f}" if float(vrd) > 0 else None
    except (TypeError, ValueError):
        ur = None
    ok = dr.get("transverse_shear_ok")
    ts_status = ("FAIL" if ok is False else "PASS") if ok is not None else None
    dd = od.get("deck_design_results", {}) or {}
    try:
        ast_prov = (float(dd.get("rebar_bottom_area") or 0) + float(dd.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        ast_prov = None
    ast_req = dr.get("Ast_required_cm2_per_m")
    stud_d, d_lim = idc.get(KEY_DS_STUD_DIAMETER), dr.get(KEY_SD_SC_D_LIMIT)
    edge, edge_req = dr.get(KEY_SD_SC_EDGE_DIST), dr.get(KEY_SD_SC_REQ_EDGE_DIST)

    def cm2m(v):
        return _with(_num(v), "cm$^2$/m")

    t.append(K.data_table(
        [Col("Check", 0.36), Col("Value", 0.50), Col("Status", 0.14, "c")],
        [(M(r"Longitudinal Shear per unit length, $V_L$"), _with(_num(vl), "kN/m"), None),
         (M(r"Transverse Shear Capacity of Slab, $V_{Rd}$"), _with(_num(vrd), "kN/m"), None),
         ("Transverse Shear Check", K.join(M("$V_L/V_{Rd}$ = "), ur), K.pass_fail(ts_status)),
         (M(r"Min. Transverse Reinforcement, $A_{st,min}$"),
          K.join("Required ", cm2m(ast_req), ", Provided ", cm2m(ast_prov)), K.pass_fail(_le(ast_prov, ast_req))),
         (M(r"Stud Diameter $\leq 2\,t_f$"), K.join(M("$d$ = "), mm(stud_d), M(r" $\leq 2t_f$ = "), mm(d_lim)),
          K.pass_fail(_le(d_lim, stud_d))),
         ("Stud Edge Distance", K.join("Provided ", mm(edge), M(r" (req. $\geq$ "), mm(edge_req), ")"),
          K.pass_fail(_le(edge, edge_req)))],
        caption="Transverse Shear and Detailing Checks"))
    t.append(K.note("Note: IRC 22 Cl. 606.6, 606.10.", small=False))
    return t


# ---------------------------------------------------------------------------
# 5.2  Deck slab
# ---------------------------------------------------------------------------

def _deck_section(bridge, od, idc):
    rpt = od.get("deck_report_values", {}) or {}
    has = bool(rpt)
    has_oh = bool(rpt.get(KEY_DD_HAS_OVERHANG))

    def dkv(key, default=0.0):
        v = rpt.get(key)
        try:
            return float(v) if v not in (None, "") else default
        except (TypeError, ValueError):
            return default

    def dkf(key, nd=2, scale=1.0):
        """Display string, None when deck design has not been run / value missing."""
        if not has:
            return None
        v = rpt.get(key)
        if v is None or v == "":
            return None
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return str(v)

    def dku(key, unit, nd=2, scale=1.0):
        return _with(dkf(key, nd, scale), unit)

    def dks(ok):
        return K.pass_fail(("PASS" if ok else "FAIL") if has else None)

    def dkoh(key, unit="kN-m/m", nd=2):
        if not has:
            return None
        return _with(dkf(key, nd), unit) if has_oh else "N/A"

    wks = [dkv(KEY_DD_WK_BOT), dkv(KEY_DD_WK_TOP)] + ([dkv(KEY_DD_WK_OH)] if has_oh else [])
    gov_wk = max(wks)
    crack_ok = has and gov_wk <= dkv(KEY_DD_WK_LIMIT)
    gdl, gll = dkf(KEY_DD_GAMMA_DL), dkf(KEY_DD_GAMMA_LL)
    P = ("Parameter", "Value")

    t = [r"""
\section{Deck Slab Design}
\label{sec:deck-design}

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.
"""]
    t.append(K.kv_table([
        (M(r"Effective Span of Deck Slab, $l_{eff}$"), K.join(dkf(KEY_DD_SPAN, 0, 1000.0), " mm (girder spacing, c/c)")),
        (M(r"Deck Thickness, $t_s$"), K.join(val(idc, KEY_TS_DECK_THICKNESS), " mm")),
        ("Clear Cover (IRC 112 Cl. 15.2)",
         K.join("Top ", val(idc, KEY_DS_TOP_CLEAR_COVER), " / Bottom ", val(idc, KEY_DS_BOTTOM_CLEAR_COVER), " mm")),
        ("Concrete Grade (IRC 112 Cl. 6.4)",
         K.join(val(idc, KEY_DECK_CONCRETE_GRADE_BASIC), M(" ($f_{ck}$ = "), val(idc, KEY_MATERIAL_DECK_FCK),
                M(" MPa, $f_{ctm}$ = "), val(idc, KEY_MATERIAL_DECK_FCTM), " MPa)")),
        ("Reinforcement Grade (IRC 112 Cl. 6.2)",
         K.join(val(idc, KEY_DS_REINF_MATERIAL), M(" ($f_y$ = "), dkf(KEY_DD_FY, 0), " MPa)")),
        (M(r"Dead Load per Unit Area, $w_{DL}$"), K.join(dkf(KEY_DD_WDL), " kN/m\u00b2 (slab self-weight)")),
        ("IRC 6 Wheel Load (Class A / 70R)", K.join(dkf(KEY_DD_WHEEL_LOAD, 1), " kN")),
        ("Tyre Contact Width (IRC 6 Annex A)", K.join(dkf(KEY_DD_TYRE_WIDTH, 0, 1000.0), " mm (transverse)")),
        ("Impact Factor (IRC 6 Cl. 208.2)", dkf(KEY_DD_IMPACT_FACTOR, 3)),
        ("Governing Live Load Case", dkf(KEY_DD_VEHICLE)),
    ], caption="Deck Slab --- Loading and Geometry", header=P, fracs=(0.36, 0.64)))

    g5 = [Col("Location", 0.18, "c"), Col("Parameter", 0.27), Col("Formula / Reference", 0.24),
          Col("Value", 0.19, "c"), Col("Status", 0.12, "c")]
    rows = [
        ("At Midspan (Sagging)", M(r"Transverse BM (DL), $M_{T,DL}$"),
         M(r"$w_{DL}\,l_{eff}^2/10$"), dku(KEY_DD_M_DL, "kN-m/m"), None),
        (None, M(r"Transverse BM (LL), $M_{T,LL}$"), "Effective width (IRC 112 B3.1)", dku(KEY_DD_M_LL, "kN-m/m"), None),
        (None, M(r"Total Design BM, $M_{u,sag}$"), K.join(gdl, " DL + ", gll, " LL"), dku(KEY_DD_M_ULS_SAG, "kN-m/m"), None),
        (None, M(r"Effective depth, $d$"), M(r"$t_s - c_{nom} - \phi/2$"), dku(KEY_DD_D_BOT, "mm", 1), None),
        (None, M(r"Moment Capacity, $M_{Rd}$"), "IRC 112 Cl. 12.2", dku(KEY_DD_MU_BOT, "kN-m/m"),
         dks(dkv(KEY_DD_MU_BOT) >= dkv(KEY_DD_M_ULS_SAG))),
        ("At Support (Hogging)", M(r"Total Design BM, $M_{u,hog}$"), K.join(gdl, " DL + ", gll, " LL (at support)"),
         dku(KEY_DD_M_ULS_HOG, "kN-m/m"), None),
        (None, M(r"Required Top Steel, $A_{st,top}$"), M(r"$M_u / (0.87\,f_y\,d)$"), dku(KEY_DD_AS_REQ_TOP, "mm\u00b2/m", 0), None),
        (None, M(r"Moment Capacity, $M_{Rd}$"), "IRC 112 Cl. 12.2", dku(KEY_DD_MU_TOP, "kN-m/m"),
         dks(dkv(KEY_DD_MU_TOP) >= dkv(KEY_DD_M_ULS_HOG))),
    ]
    t.append(K.data_table(g5, rows, caption="Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)",
                          groups=[5, 3]))
    t.append(K.note("Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20% of main "
                    "steel moment (IRC 21 Cl. 305.18).", small=False))

    g4 = [Col("Parameter", 0.38), Col("Formula / Reference", 0.24, "c"), Col("Value", 0.24, "c"),
          Col("Status", 0.14, "c")]
    oh_status = (dks(dkv(KEY_DD_MU_OH) >= dkv(KEY_DD_M_ULS_OH)) if has_oh
                 else (K.pass_fail("N/A") if has else K.pass_fail(None)))
    t.append(K.data_table(
        [Col("Parameter", 0.38), Col("Formula", 0.24, "c"), Col("Value", 0.24, "c"), Col("Status", 0.14, "c")],
        [(M(r"Overhang Length, $l_{oh}$"), None, _with(val(idc, KEY_TS_DECK_OVERHANG), "m"), None),
         ("Crash Barrier Load Moment", "IRC 6 Cl. 206.4", dkoh(KEY_DD_M_BARRIER), None),
         ("Dead Load Moment", M(r"$w_{DL}\,l_{oh}^2/2$ + railing"), dkoh(KEY_DD_M_DL_OH), None),
         ("Live Load Moment (eccentric wheel)", M(r"Wheel load $\times$ arm"), dkoh(KEY_DD_M_LL_OH), None),
         (M(r"Total Hogging Moment, $M_{u,oh}$"), K.join(gdl, " DL + ", gll, " (LL + CB)"), dkoh(KEY_DD_M_ULS_OH), None),
         (M(r"Moment Capacity (top steel), $M_{Rd,oh}$"), "IRC 112 Cl. 12.2", dkoh(KEY_DD_MU_OH), oh_status)],
        caption="Deck Slab --- Cantilever Overhang Flexure Check"))
    t.append(K.note("Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.",
                    small=False))

    pu = (f"{dkv(KEY_DD_PUNCH_VED) / dkv(KEY_DD_VRD_C_MPA):.2f}" if (has and dkv(KEY_DD_VRD_C_MPA) > 0) else None)
    t.append(K.data_table(g4, [
        (M(r"Design Wheel Load (ULS), $V_{Ed}$"), M(r"$\gamma_Q\,(1+IF)\,P_w$"), dku(KEY_DD_PUNCH_VED_KN, "kN", 1), None),
        ("Tyre Contact Area", M(r"$a \times b$ (IRC 6 Annex A)"),
         K.join(dkf(KEY_DD_TYRE_WIDTH, 0, 1000.0), M(r" $\times$ "), dkf(KEY_DD_TYRE_LENGTH, 0), " mm"), None),
        (M(r"Loaded Area at mid-depth, $b_0$"), M(r"$c_1 \times c_2$ (incl.\ WC dispersion)"),
         K.join(dkf(KEY_DD_PUNCH_C1, 0), M(r" $\times$ "), dkf(KEY_DD_PUNCH_C2, 0), " mm"), None),
        (M(r"Control Perimeter, $u_1$"), M(r"$2(c_1+c_2) + 4\pi d$"), dku(KEY_DD_PUNCH_U1, "mm", 0), None),
        (M(r"Punching Shear Stress, $v_{Ed}$"), M(r"$V_{Ed} / (u_1\,d)$"), dku(KEY_DD_PUNCH_VED, "MPa", 3), None),
        (M(r"Punching Resistance, $v_{Rd,c}$"), M(r"IRC 112 Eq.\ 10.1"), dku(KEY_DD_VRD_C_MPA, "MPa", 3), None),
        ("Punching Shear Check", M(r"$v_{Ed} \leq v_{Rd,c}$"), pu, dks(bool(rpt.get(KEY_DD_PUNCH_OK))))],
        caption="Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)"))
    t.append(K.note(M(r"Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm "
                      r"and adequate longitudinal reinforcement."), small=False))

    t.append(K.kv_table([
        (M(r"Min. Reinforcement for Crack Control, $A_{s,min}$"), K.join(dkf(KEY_DD_AS_MIN, 0), " mm\u00b2/m [IRC 112 Cl. 16.5.1]")),
        ("Provided Reinforcement (bottom)",
         K.join(M(r"$\phi$"), dkf(KEY_DD_DIA_BOT, 0), " @ ", dkf(KEY_DD_SPC_BOT, 0), " mm c/c (", dkf(KEY_DD_AS_BOT, 0), " mm\u00b2/m)")),
        ("Max. Permissible Crack Width", K.join(dkf(KEY_DD_WK_LIMIT, 2), " mm")),
        (M(r"Calculated Crack Width, $w_k$ (governing)"), K.join(f"{gov_wk:.4f}" if has else None, " mm")),
        ("Crack Width Check", dks(crack_ok)),
    ], caption="Crack Width Check (Deck Slab)", header=("Parameter", "Value / Reference"), fracs=(0.45, 0.55)))

    k_size = (f"{min(1.0 + (200.0 / dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (has and dkv(KEY_DD_D_BOT) > 0) else None)
    rho = (f"{min(dkv(KEY_DD_AS_BOT) / (1000.0 * dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (has and dkv(KEY_DD_D_BOT) > 0) else None)
    ow = (f"{dkv(KEY_DD_SHEAR_VED) / dkv(KEY_DD_SHEAR_VRDC):.2f}" if (has and dkv(KEY_DD_SHEAR_VRDC) > 0) else None)
    t.append(K.data_table(g4, [
        (M(r"Design Shear per unit width, $V_{Ed}$"), M(r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$"),
         dku(KEY_DD_SHEAR_VED, "kN/m"), None),
        (M(r"Effective depth, $d$"), M(r"$t_s - c_{nom} - \phi/2$"), dku(KEY_DD_D_BOT, "mm", 1), None),
        (M(r"Size factor, $k$"), M(r"$1 + \sqrt{200/d} \leq 2.0$"), k_size, None),
        (M(r"Long.\ reinforcement ratio, $\rho_l$"), M(r"$A_{sl}/(b_w\,d) \leq 0.02$"), rho, None),
        (M(r"Shear resistance (no stirrups), $V_{Rd,c}$"), M(r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)"),
         dku(KEY_DD_SHEAR_VRDC, "kN/m"), None),
        ("One-Way Shear Check", M(r"$V_{Ed} \leq V_{Rd,c}$"), ow, dks(bool(rpt.get(KEY_DD_SHEAR_OK))))],
        caption="One-Way (Beam) Shear Check (Deck Slab)"))
    t.append(K.note("Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on "
                    "concrete and main reinforcement.", small=False))

    def sub(s):
        return Span(4, K.bold(s))

    t.append(K.data_table(
        [Col("Parameter", 0.32), Col("Required / Limit", 0.26, "c"), Col("Provided", 0.26, "c"), Col("Status", 0.16, "c")],
        [(sub("Main Reinforcement --- Bottom (Transverse)"),),
         (M(r"Required Area, $A_{st,req}$ (mm\texttwosuperior/m)"), dku(KEY_DD_AS_REQ_BOT, "mm\u00b2/m", 0),
          dku(KEY_DD_AS_BOT, "mm\u00b2/m", 0), dks(dkv(KEY_DD_AS_BOT) >= dkv(KEY_DD_AS_REQ_BOT))),
         (M(r"Bar Diameter $\times$ Spacing"), M(r"$\phi \geq 10$ mm (IRC 112)"),
          K.join(M(r"$\phi$"), dkf(KEY_DD_DIA_BOT, 0), " @ ", dkf(KEY_DD_SPC_BOT, 0), " mm c/c"), None),
         (M(r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)"), dku(KEY_DD_AS_MIN, "mm\u00b2/m", 0),
          dku(KEY_DD_AS_BOT, "mm\u00b2/m", 0), dks(dkv(KEY_DD_AS_BOT) >= dkv(KEY_DD_AS_MIN))),
         (M(r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)"), dku(KEY_DD_SPACING_MAX, "mm", 0), dku(KEY_DD_SPC_BOT, "mm", 0),
          dks(0.0 < dkv(KEY_DD_SPC_BOT) <= dkv(KEY_DD_SPACING_MAX))),
         (sub("Distribution Reinforcement --- Longitudinal"),),
         (M(r"Required Area, $A_{st,dist}$ (mm\texttwosuperior/m)"), M(r"$\geq 20\%$ of main steel"),
          dku(KEY_DD_AS_LONG, "mm\u00b2/m", 0),
          dks(dkv(KEY_DD_AS_LONG) >= max(0.20 * dkv(KEY_DD_AS_BOT), dkv(KEY_DD_AS_MIN)))),
         (sub("Top Reinforcement (Support / Cantilever Overhang)"),),
         (M(r"Required Area, $A_{st,top}$ (mm\texttwosuperior/m)"), dku(KEY_DD_AS_REQ_TOP, "mm\u00b2/m", 0),
          dku(KEY_DD_AS_TOP, "mm\u00b2/m", 0), dks(dkv(KEY_DD_AS_TOP) >= dkv(KEY_DD_AS_REQ_TOP))),
         (sub("Cover and Detailing"),),
         ("Clear Cover (IRC 112 Cl. 15.2)", K.join(M(r"$\geq$ "), dkf(KEY_DD_MIN_COVER, 0), " mm (Table 14.2)"),
          K.join("Top ", val(idc, KEY_DS_TOP_CLEAR_COVER), " / Bottom ", val(idc, KEY_DS_BOTTOM_CLEAR_COVER), " mm"),
          dks(bool(rpt.get(KEY_DD_COVER_OK))))],
        caption="Reinforcement Detailing Summary (Deck Slab)"))
    t.append(K.note("Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and "
                    "detailing requirements.", small=False))
    return "".join(t)


# ---------------------------------------------------------------------------
# 5.3 / 5.4  Cross bracing and end diaphragm
# ---------------------------------------------------------------------------

_NOTE_PROPS = "Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration."
_NOTE_SLENDER = ("Note: Limit = 250 for compression members, 400 for tension members. "
                 "$K = 1.0$ for members with both ends pinned.")
_NOTE_CAP = ("Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). "
             "OsdagBridge cross-bracing module used.")


def _brace_tables(bridge, od, title):
    """Connection/properties, slenderness and capacity tables for bracing-type members."""
    pairs = bridge.get_cb_pairs()
    t = []

    # (a) connection and section properties
    rows, groups = [], []
    if not pairs:
        rows, groups = [("Between Girders", "Diagonal", None, None, None, None)], [1]
    for pair in pairs:
        pair_id = pair.replace("-", "")
        for member, label in (("diagonal", "Diagonal"), ("chord", "Top / Bottom chord")):
            _, ftype = bridge.get_cb_governing_force(pair, member)
            conn = bridge.get_cb_connection(pair, member, ftype)
            section = bridge.get_cb_section(pair, member, ftype)
            if member == "diagonal":
                pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
            else:
                pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                if od.get(f"{pfx}.A") is None:
                    pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"
            area, rv = od.get(f"{pfx}.A"), od.get(f"{pfx}.rv")
            rows.append((pair, label, conn or None, section or None,
                         f"{float(area) * 100:.1f}" if area is not None else None,   # cm2 -> mm2
                         f"{float(rv) * 10:.1f}" if rv is not None else None))        # cm -> mm
        groups.append(2)
    t.append(K.data_table(
        [Col("Panel", 0.15, "c"), Col("Member", 0.20), Col("Connection", 0.17), Col("Section", 0.18, "c"),
         Col(M("$A_g$ (mm\\texttwosuperior)"), 0.15, "c"), Col(M("$r_{min}$ (mm)"), 0.15, "c")],
        rows, caption=f"{title} --- Connection and Section Properties", groups=groups))
    t.append(K.note(M(_NOTE_PROPS), small=False))

    # (b) slenderness
    def sl_status(s, limit):
        try:
            return "PASS" if float(s) <= limit else "FAIL"
        except (TypeError, ValueError):
            return None

    rows, groups = [], []
    if not pairs:
        rows, groups = [("Between Girders", "Diagonal", "C", None, None, None)], [1]
    top_on = od.get("member_properties.cross_bracing_details.top_chord", True)
    bot_on = od.get("member_properties.cross_bracing_details.bottom_chord", True)
    for pair in pairs:
        kl_d, sl_d = bridge.get_cb_effective_length("diagonal"), bridge.get_cb_slenderness(pair, "diagonal")
        kl_c, sl_c = bridge.get_cb_effective_length("chord"), bridge.get_cb_slenderness(pair, "chord")
        r = [(pair, "Diagonal", "C", kl_d, sl_d or None, K.join("250 --- ", K.pass_fail(sl_status(sl_d, 250))))]
        if top_on:
            r.append((pair, "Top chord", "C", kl_c, sl_c or None, K.join("250 --- ", K.pass_fail(sl_status(sl_c, 250)))))
        if bot_on:
            r.append((pair, "Bottom chord", "T", kl_c, sl_c or None, K.join("400 --- ", K.pass_fail(sl_status(sl_c, 400)))))
        rows += r
        groups.append(len(r))
    t.append(K.data_table(
        [Col("Panel", 0.15, "c"), Col("Member", 0.17), Col("Nature", 0.14, "c"),
         Col(M(r"Eff.\ Length $KL$ (mm)"), 0.18, "c"), Col(M("$KL/r$"), 0.14, "c"), Col("Limit / Status", 0.22, "c")],
        rows, caption=f"{title} --- Slenderness Ratio Check (IS 800 Cl. 3.8)", groups=groups))
    t.append(K.note(M(_NOTE_SLENDER), small=False))

    # (c) capacity summary
    rows, groups = [], []
    for pair in pairs:
        for member, label in (("diagonal", "Diagonal"), ("chord", "Chord")):
            force, ftype = bridge.get_cb_governing_force(pair, member)
            rows.append((pair, label, bridge.get_cb_section(pair, member, ftype) or None,
                         bridge.get_cb_gov_lc(pair, member, ftype) or None, force or None,
                         bridge.get_cb_capacity(pair, member, ftype) or None,
                         bridge.get_cb_efficiency(pair, member, ftype) or None,
                         K.pass_fail(bridge.get_cb_status(pair, member, ftype))))
        groups.append(2)
    if not rows:
        rows, groups = [(None,) * 8], [1]
    t.append(K.data_table(
        [Col("Panel", 0.12, "c"), Col("Member", 0.12), Col("Section", 0.14, "c"), Col("Governing LC", 0.17, "c"),
         Col("Demand (kN)", 0.13, "c"), Col("Capacity (kN)", 0.14, "c"), Col("UR", 0.08, "c"),
         Col("Status", 0.10, "c")],
        rows, caption=f"{title} Design --- Capacity Summary", groups=groups, compact=True))
    t.append(K.note(M(_NOTE_CAP), small=False))
    return "".join(t)


def _cross_bracing_section(bridge, od):
    return (r"""
\section{Cross Bracing Design}
\label{sec:cross-bracing}

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).
""" + _brace_tables(bridge, od, "Cross Bracing"))


def _end_diaphragm_section(bridge, od):
    intro = r"""
\section{End Diaphragm Design}
\label{sec:end-diaphragm}

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.
"""
    ed = D.end_diaphragm_results(od)
    if not ed.has_results():
        ed_type = D.end_diaphragm_type(bridge.input_dict)
        if "brac" in ed_type.lower():
            why = "Design results are not available for the selected bracing-type end diaphragms."
        elif ed_type:
            why = ("The selected end diaphragm type (%s) is not designed in this version, "
                   "so no results are reported." % ed_type)
        else:
            why = "No end diaphragm type was selected, so no end diaphragm design was performed."
        return intro + "\n\\noindent " + why + "\n"
    rows, groups = [], []
    for pair in ed.pairs():
        for member, label in (("diagonal", "Diagonal"), ("chord", "Chord")):
            best = None
            for ft in ("compression", "tension"):
                sm = ed.summary(pair, member, ft)
                ur = D._float(sm.get("efficiency"))
                if ur is not None and (best is None or ur > best[0]):
                    best = (ur, ft, sm)
            if best is None:
                rows.append((pair, label, None, None, None, None, None, None))
            else:
                ur, ft, sm = best
                cap = D._float(sm.get("capacity_kN"))
                rows.append((pair, label, sm.get("section"), ed.gov_lc(pair, member, ft),
                             _num(cap * ur) if cap else None, _num(cap, 3), _ur_cell(ur),
                             K.pass_fail("PASS" if T.ur_passes(ur) else "FAIL")))
        groups.append(2)
    table = K.data_table(
        [Col("Panel", 0.12, "c"), Col("Member", 0.12), Col("Section", 0.14, "c"), Col("Governing LC", 0.17, "c"),
         Col("Demand (kN)", 0.13, "c"), Col("Capacity (kN)", 0.14, "c"), Col("UR", 0.08, "c"),
         Col("Status", 0.10, "c")],
        rows, caption="End Diaphragm Design --- Capacity Summary", groups=groups, compact=True)
    return intro + table + K.note(M(_NOTE_CAP), small=False)


# ---------------------------------------------------------------------------
# 5.5  Overall summary
# ---------------------------------------------------------------------------

def _ur_row_cells(r):
    """Table cells for one URRow; a message row spans the data columns."""
    if r.message:
        return (r.label, Span(4, r.message, "c"))
    if not r.applicable and r.demand == "N/A":
        return (r.label, r.gov_lc, "N/A", "N/A", "N/A")
    return (r.label, r.gov_lc, r.demand, r.capacity, _ur_cell(r.ur))


def _overall_summary(bridge, od, idc, fig_paths):
    rows = D.collect_ur_rows(idc, od)
    return (r"""
\section{Overall Design Check Summary}
\label{sec:overall-summary}
""" + K.data_table(
        [Col("Member / Check", 0.23, "c"), Col("Governing Load Combo", 0.31), Col("Demand", 0.17, "c"),
         Col("Capacity", 0.17, "c"), Col("UR", 0.12, "c")],
        [_ur_row_cells(r) for r in rows], caption="Overall Design Check Summary --- All Members", compact=True)
        + K.note(M(r"Note: UR = Demand / Capacity. A check passes when UR $\leq 1.0$. Checks without a result "
                   r"are shown as a dash and are not counted as passing. The governing check "
                   r"for each component is highlighted in the individual design check sections above."),
                 small=False)
        + K.figure(fig_paths.get("ur_chart"), "Utilisation ratio of every design check (limit = 1.0)",
                   max_height=T.FIGURE_TALL_HEIGHT))
