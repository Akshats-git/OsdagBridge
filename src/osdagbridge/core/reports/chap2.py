# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports.latex_kit import Col
from osdagbridge.core.reports.report_utils import get_girder_entries, val, _tex

_PARAM = ("Parameter", "Value")


def _g(d, key, i, unit=""):
    """Girder-scoped value ``{key}.G{i}.M1``."""
    return val(d, f"{key}.G{i}.M1", unit)


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    d = input_dict
    include_median = str(d.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1")

    out = [r"""
\chapter{Input Parameters}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}
"""]

    out.append(K.kv_table([
        ("Project Location", m.project_location or None),
        ("Latitude / Longitude", K.join(val(d, "latitude"), ", ", val(d, "longitude"))),
        ("Seismic Zone (IRC 6)", val(d, "seismic_zone")),
        ("Basic Wind Speed (IRC 6)", val(d, "wind_speed", " m/s")),
        ("Shade Temp. Max / Min (IRC 6)",
         K.join(val(d, "shade_temp_max"), " °C / ", val(d, "shade_temp_min"), " °C")),
    ], caption="Project Location", label="subsec:project-location", header=_PARAM))

    out.append(K.kv_table([
        ("Type of Structure", val(d, KEY_STRUCTURE_TYPE)),
        ("Span (m)", val(d, KEY_SPAN, " m")),
        ("Carriageway Width (m)", val(d, KEY_CARRIAGEWAY_WIDTH, " m")),
        ("Include Median", val(d, KEY_INCLUDE_MEDIAN)),
        ("Footpath", val(d, KEY_FOOTPATH)),
        ("Skew Angle (degrees)",
         K.join(val(d, KEY_SKEW_ANGLE, "°"), K.raw(r" (IRC 24 Cl. 504.8 limit: $\pm$15\textdegree)"))),
    ], caption="Bridge Geometry", label="subsec:bridge-geometry", header=_PARAM))

    out.append(K.kv_table([
        ("Girder Steel Grade (IS 2062)", val(d, KEY_GIRDER)),
        ("Cross Bracing Steel Grade", val(d, KEY_CROSS_BRACING)),
        ("End Diaphragm Steel Grade", val(d, KEY_END_DIAPHRAGM)),
        ("Concrete Deck Grade (IRC 22)", val(d, KEY_DECK_CONCRETE_GRADE_BASIC)),
    ], caption="Material Selection", label="subsec:material", header=_PARAM))

    out.append(r"""
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.
""")

    out.append(K.kv_table([
        ("Overall Bridge Width (m)", val(d, KEY_TS_OVERALL_WIDTH)),
        ("No. of Girders", val(d, KEY_TS_NO_OF_GIRDERS)),
        ("Girder Spacing (m)", val(d, KEY_TS_GIRDER_SPACING, " m")),
        ("Deck Overhang Width (m)", val(d, KEY_TS_DECK_OVERHANG, " m")),
        ("Deck Thickness (mm)", val(d, KEY_TS_DECK_THICKNESS, " mm")),
        ("Footpath Width (m)", K.join(val(d, KEY_TS_FOOTPATH_WIDTH, " m"), " (IRC 5 Cl. 104.3.6 min: 1.5 m)")),
        ("No. of Traffic Lanes", K.join(val(d, KEY_WC_LD_LANE_TABLE_COUNT), " (per IRC 5 Cl. 104.3.1)")),
    ], caption="Typical Section Details", header=_PARAM))

    comp = [
        ("Crash Barrier Type", val(d, KEY_CB_TYPE)),
        ("Crash Barrier Load (kN/m)", val(d, KEY_CB_LOAD)),
    ]
    if include_median:
        comp.append(("Median Type", val(d, KEY_MD_TYPE)))
    comp += [
        ("Railing Type", val(d, KEY_RL_TYPE)),
        ("Railing Load (kN/m)", val(d, KEY_RL_LOAD_VALUE)),
        ("Wearing Course Material", val(d, KEY_WC_MATERIAL)),
        ("Wearing Course Thickness (mm)", val(d, KEY_WC_THICKNESS, " mm")),
    ]
    out.append(K.kv_table(comp, caption="Components Details", header=_PARAM))

    out.append(_girder_tables(d, n_girders))
    out.append(_bracing_tables(d, n_girders))
    out.append(_shear_connector_table(d, output_dict))
    out.append(_safety_factors_table(d))
    return "".join(out)


def _girder_tables(d, n_girders):
    # Backend-populated labels follow defaults.py:
    #   KEY_MP_GD_SELECT_GIRDER.G{i} = 'G{i}'   KEY_MP_GD_MEMBER_ID.G{i}.M1 = 'G{i}M1'
    #   other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    entries = get_girder_entries(d) or [(f"Girder {i}", "M1") for i in range(1, n + 1)]
    numbered = [(lbl, mid, i) for i, (lbl, mid) in enumerate(entries, start=1)]

    gen_rows = [
        (lbl, mid, val(d, KEY_DESIGN_MODE), _g(d, KEY_MP_GIRDER_TYPE, i), _g(d, KEY_MP_GIRDER_SYMMETRY, i))
        for lbl, mid, i in numbered
    ]
    dim_rows = [
        (lbl,
         _g(d, KEY_MP_GIRDER_DEPTH, i, " mm"),
         _g(d, KEY_MP_GIRDER_WEB_THICKNESS, i, " mm"),
         K.join(_g(d, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, i, " mm"), ", ",
                _g(d, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, i, " mm")),
         K.join(_g(d, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, i, " mm"), ", ",
                _g(d, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, i, " mm")))
        for lbl, _, i in numbered
    ]
    rst_rows = [
        (lbl,
         K.join(_g(d, KEY_MP_GIRDER_TORSIONAL_RESTRAINT, i), ", ", _g(d, KEY_MP_GIRDER_WARPING_RESTRAINT, i)),
         _g(d, KEY_MP_GIRDER_WEB_TYPE, i),
         K.join(_g(d, KEY_MP_STIFFENER_INTERMEDIATE, i), "; Spacing: ",
                _g(d, KEY_MP_STIFFENER_INTERMEDIATE_SPACING, i, " mm"), "; Thickness: ",
                _g(d, KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, i, " mm")),
         _g(d, KEY_MP_STIFFENER_LONGITUDINAL, i),
         K.join("No.: ", _g(d, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, i), "; Spacing: ",
                _g(d, KEY_MP_STIFFENER_SPACING, i, " mm"), "; Thickness: ",
                _g(d, KEY_MP_STIFFENER_BEARING_THICKNESS, i, " mm")))
        for lbl, _, i in numbered
    ]

    return (
        K.data_table(
            [Col("Girder", 0.14), Col("Member ID", 0.14), Col("Design Mode", 0.24),
             Col("Girder Type", 0.24), Col("Girder Symmetry", 0.24)],
            gen_rows, caption="Girder General Information")
        + K.data_table(
            [Col("Girder", 0.12), Col("Total Depth, D (mm)", 0.16), Col(K.raw("Web, $t_w$ (mm)"), 0.13),
             Col(K.raw(r"Top Flange (b\textsubscript{tf}, t\textsubscript{tf}) mm"), 0.295),
             Col(K.raw(r"Bottom Flange (b\textsubscript{bf}, t\textsubscript{bf}) mm"), 0.295)],
            dim_rows, caption="Girder Section Dimensions")
        + K.data_table(
            [Col("Girder", 0.09), Col("Torsional / Warping Restraint", 0.15), Col("Web Philosophy", 0.15),
             Col("Intermediate Stiffeners", 0.22), Col("Longitudinal Stiffeners", 0.20),
             Col("Bearing Stiffener", 0.19)],
            rst_rows, caption="Girder Restraint and Stiffener Details", compact=True)
    )


def _bracing_tables(d, n_girders):
    n = n_girders if n_girders >= 2 else 2
    cb_rows, ed_rows = [], []
    for i in range(1, n):
        pair = f"G{i}G{i + 1}"
        cb_rows.append((
            val(d, f"{KEY_MP_CB_SELECT_GIRDERS}.{pair}.B{i}M1"),
            val(d, f"{KEY_MP_CB_MEMBER_ID}.{pair}.B{i}M1"),
            val(d, f"{KEY_MP_CB_TYPE}.{pair}.B{i}M1"),
            val(d, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.{pair}.B{i}M1"),
            val(d, f"{KEY_MP_CB_SPACING}.{pair}.B{i}M1", " m"),
        ))
        ed_rows.append((
            val(d, f"{KEY_MP_ED_SELECT_GIRDERS}.{pair}.E{i}M1"),
            val(d, f"{KEY_MP_ED_MEMBER_ID}.{pair}.E{i}M1"),
            val(d, f"{KEY_MP_ED_TYPE}.{pair}.E{i}M1"),
            val(d, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.{pair}.E{i}M1"),
        ))
    return (
        K.data_table(
            [Col("Location", 0.17), Col("Member IDs", 0.17), Col("Type of Bracing", 0.24),
             Col("Bracing Section", 0.24), Col("Spacing (m)", 0.18, "c")],
            cb_rows, caption="Member Properties: Cross Bracing Details")
        + K.data_table(
            [Col("Location", 0.2), Col("Member IDs", 0.2), Col("Type of Bracing", 0.3),
             Col("Bracing Section", 0.3)],
            ed_rows, caption="Member Properties: End Diaphragm Details")
    )


def _shear_connector_table(d, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return "\n\\label{subsec:shear-connectors}\n" + K.kv_table([
        ("Stud Diameter (mm)", val(od, KEY_SD_SHEAR_DIAMETER, " mm")),
        ("Stud Height (mm)", val(od, KEY_SD_SHEAR_HEIGHT, " mm")),
        (K.raw("Stud $f_y$ (MPa)"), val(od, KEY_SD_SHEAR_YIELD_STRENGTH, " MPa")),
        (K.raw("Stud $f_u$ (MPa)"), val(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, " MPa")),
        ("No. of Studs per Section", val(od, KEY_SD_SHEAR_STUDS_PER_SECTION)),
    ], caption="Shear Connector Details", header=_PARAM)


def _safety_factors_table(d):
    return (
        "\n\\label{subsec:safety-factors}\n"
        + K.note("Note: All values are per IRC 22 Table 1 unless user-modified.", small=False)
        + K.kv_table([
            (K.raw(r"$\gamma_{M0}$ (Yielding / Buckling)"), val(d, KEY_DO_GAMMA_M0)),
            (K.raw(r"$\gamma_{M1}$ (Ultimate Stress)"), val(d, KEY_DO_GAMMA_M1)),
            (K.raw(r"$\gamma_C$ (Concrete, Basic)"), val(d, KEY_DO_GAMMA_C_BASIC)),
            (K.raw(r"$\gamma_s$ (Reinforcement)"), val(d, KEY_DO_GAMMA_S)),
            (K.raw(r"$\gamma_v$ (Shear Connectors)"), val(d, KEY_DO_GAMMA_V)),
            (K.raw(r"$\gamma_{fft}$ (Fatigue Load)"), val(d, KEY_DO_GAMMA_FLT)),
            (K.raw(r"$\gamma_{Mft}$ (Fatigue Strength)"), val(d, KEY_DO_GAMMA_MF)),
        ], caption="Partial Safety Factors", header=_PARAM)
    )
