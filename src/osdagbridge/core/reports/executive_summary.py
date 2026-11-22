# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import report_data as D
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.latex_kit import Col
from osdagbridge.core.reports.report_utils import val, get_girder_entries
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if out is None or f > out:
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Maximum Osdag 'efficiency' (utilization ratio) over a cross-bracing or
    end-diaphragm result dump (nested pair -> member -> force_type -> raw).
    Reads already-computed results only; nothing is recalculated here."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for raw in force_types.values():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best is None or f > best:
                    best = f
    return best


def executive_summary(input_dict, output_dict, fig_paths, has_checks_chapter=True) -> str:
    plan_fig = K.figure(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan',
                       max_height=T.FIGURE_SUMMARY_HEIGHT)
    cs_fig = K.figure(fig_paths.get('cross_section'),
                      'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)',
                      max_height=T.FIGURE_SUMMARY_HEIGHT)
    geom_fig = K.figure(fig_paths.get('final_geometry'), 'Figure 3 -- 3D View of Bridge Superstructure',
                        max_height=T.FIGURE_SUMMARY_HEIGHT)

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = val(output_dict, KEY_SD_SECTION_DESIGNATION)

    # ── Pull the stored result dicts once, then work off these locals ─────────
    # (no value is recomputed here — the pipeline already filled these in).
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    # Overall Design Status — girder checks only: Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):     # skip edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and not T.ur_passes(dcr))
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    if not per_girder:
        overall_design_status = ""
    elif failing:
        overall_design_status = "Fail (" + ", ".join(failing) + ")"
    else:
        overall_design_status = "Pass"

    # Overall Utilization Ratio — the maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.05 (Deck slab)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    for results, label in ((cb_results, "Cross bracing"), (ed_results, "End diaphragm")):
        m = _max_member_efficiency(results)
        if m is not None:
            component_urs.append((m, label))
    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

    gov = gov_name if gov_name not in (None, '', 'None') else None
    ur = overall_utilization_ratio or None

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    n_cols = len(labels)
    per_col = 0.8 / n_cols
    table1 = K.data_table(
        [Col("", 0.2, "c")] + [Col(lbl, per_col, "c") for lbl, _ in labels],
        [("Member ID",) + tuple(mid for _, mid in labels),
         ("Section Designation",) + (sec,) * n_cols,
         ("Governing Check",) + (gov,) * n_cols,
         ("Utilization Ratio",) + (ur,) * n_cols],
        caption="Final Bridge Geometry (after optimization)", numbered=False)

    overview = K.kv_table([
        ("Bridge Type", val(input_dict, KEY_STRUCTURE_TYPE)),
        ("Design Standard", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800"),
        ("Span", val(input_dict, KEY_SPAN, " m")),
        ("Carriageway Width", val(input_dict, KEY_CARRIAGEWAY_WIDTH, " m")),
        ("No. of Girders", val(input_dict, KEY_TS_NO_OF_GIRDERS)),
        ("Girder Spacing", val(input_dict, KEY_TS_GIRDER_SPACING, " m")),
        ("Deck Thickness", val(input_dict, KEY_TS_DECK_THICKNESS, " mm")),
        ("Overall Design Status", overall_design_status or None),
        ("Governing Check", gov),
        ("Overall Utilization Ratio (max)", ur),
    ], header=("Item", "Value"), fracs=(0.4, 0.6))

    ur_rows = D.collect_ur_rows(input_dict, output_dict)
    verdicts = K.data_table(
        [Col("Element", 0.40, "c"), Col("Max UR", 0.25, "c"), Col("Verdict", 0.35, "c")],
        [(el, T.fmt(mx, T.DECIMALS_RATIO), K.pass_fail(v))
         for el, (v, mx) in D.element_verdicts(ur_rows).items()],
        caption="Design Verdict by Element", numbered=False)

    where = (r" (Section~\ref{sec:overall-summary})" if has_checks_chapter else "")
    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}
""" + overview + plan_fig + cs_fig + geom_fig + table1 + K.note(
        K.raw(r"Note: Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check."),
        small=False) + r"""
\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent Verdicts come from the same utilisation-ratio rows as the design checks""" + where + r""": an element passes when its largest UR is $\leq 1.0$, and an element with no design result is reported as n/a, never as a pass.
""" + verdicts + r"""
\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions-summary}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

"""
