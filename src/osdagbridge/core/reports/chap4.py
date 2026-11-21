from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.latex_kit import Col

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _merged_row(lc, bm_d, rxn_d):
        bm_d = bm_d or {}
        rxn_d = rxn_d or {}
        return (
            lc,
            T.fmt(bm_d.get('max_bm'), 3), bm_d.get('bm_girder', None), T.fmt(bm_d.get('bm_location'), 3),
            T.fmt(bm_d.get('max_sf'), 3), bm_d.get('sf_girder', None), T.fmt(bm_d.get('sf_location'), 3),
            T.fmt(rxn_d.get('left_kN'), 3), T.fmt(rxn_d.get('right_kN'), 3),
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]
    merged_rows = [_merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc)) for lc in all_lcs] \
        or [(None,) * 9]

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status = (K.pass_fail("PASS" if _live_mm <= _allow_live_mm else "FAIL")
                    if _live_mm is not None else None)
    _total_status = (K.pass_fail("PASS" if _total_mm <= _allow_total_mm else "FAIL")
                     if _total_mm is not None else None)

    cols = [Col("Load Case / Comb.", 0.211), Col("Max (kNm)", 0.116, "c"), Col("Girder", 0.082, "c"),
            Col("Loc. (m)", 0.088, "c"), Col("Max (kN)", 0.116, "c"), Col("Girder", 0.082, "c"),
            Col("Loc. (m)", 0.088, "c"), Col("Left", 0.109, "c"), Col("Right", 0.109, "c")]
    summary_tbl = K.data_table(
        cols, merged_rows, caption="Summary of Maximum Demands", compact=True,
        header_groups=[("", 1), ("Bending Moment", 3), ("Shear Force", 3), ("Reaction at Supports", 2)])

    defl_tbl = K.kv_table([
        (K.raw(r"Deflection due to Live Load, $\delta_{LL}$"), _live_str),
        (K.raw(r"Allowable Live Load Deflection ($\Delta_{allow}$)"), _allow_live_str),
        ("Live Load Deflection Check Status", _live_status),
        (K.raw(r"Deflection due to Total Load, $\delta_{total}$"), _total_str),
        (K.raw(r"Allowable Total Deflection ($\Delta_{allow}$)"), _allow_total_str),
        ("Total Load Deflection Check Status", _total_status),
    ], caption="Deflection Summary (Live Load & Total Load)", header=("Parameter", "Value"), fracs=(0.45, 0.55))

    figs = "".join([
        K.figure(fig_paths.get('bm_envelope'),
                 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).'),
        K.figure(fig_paths.get('sf_envelope'),
                 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).'),
        K.figure(fig_paths.get('defl_ll'),
                 K.raw('Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.')),
    ])
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.
""" + summary_tbl + defl_tbl + figs
