from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.latex_kit import Col
from osdagbridge.core.utils.common import KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DS_REINF_MATERIAL, KEY_GIRDER

M = K.raw

# (S.N., description template, key prefix in input_dict as produced by calculate_material_quantities)
# {girder}, {concrete} and {rebar} are filled from the user's material inputs.
_BOQ_ROWS = [
    ("1", "Structural Steel (IS 2062, {girder}) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord", "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag"),
    ("2(d)", "End Diaphragm (beam type)", "end_diaphragm"),
    ("3", "Concrete ({concrete}) for Deck Slab", "concrete_deck"),
    ("4", "Reinforcement Steel ({rebar})", "rebar_deck"),
    ("5", "Shear Stud Connectors", "shear_studs"),
    ("6", "Crash Barrier", "crash_barrier"),
]

NOTE = (r"Note: Steel density 7.85 t/m\textsuperscript{3}; concrete density 2.5 t/m\textsuperscript{3}. "
        r"Reinforcement is estimated at 120 kg per m\textsuperscript{3} of deck concrete (an assumption, not a "
        r"detailed bar schedule). N.A. = not available for this configuration (for example, end diaphragms of "
        r"cross-bracing type are not quantified).")


def _cell(value):
    """Quantity cell: LaTeX math from the BOQ is passed through; missing -> N.A."""
    if value in (None, ""):
        return "N.A."
    text = str(value)
    if r"\placeholder" in text:
        return "N.A."
    return M(text) if text.startswith("$") else text


def _grade(input_dict, key, default):
    v = input_dict.get(key)
    return str(v).strip() if v not in (None, "") else default


def ch7_quantities(input_dict, fig_paths=None):
    fig_paths = fig_paths or {}
    names = {"girder": _grade(input_dict, KEY_GIRDER, "IS 2062"),
             "concrete": _grade(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC, "concrete"),
             "rebar": _grade(input_dict, KEY_DS_REINF_MATERIAL, "Fe 500")}
    rows = []
    for sn, desc, key in _BOQ_ROWS:
        rows.append((sn, desc.format(**names)) + tuple(
            _cell(input_dict.get(f"{key}_{suffix}"))
            for suffix in ("vol_formula", "qty", "vol_total", "wt_single", "wt_total")))
    table = K.data_table(
        [Col("S.N.", 0.07, "c"), Col("Item Description", 0.25), Col(M(r"Volume (area $\times$ length)"), 0.27, "c"),
         Col("Qty", 0.07, "c"), Col(M(r"Total Vol. (m$^3$)"), 0.11, "c"), Col("Unit Wt. (MT)", 0.11, "c"),
         Col("Total Wt. (MT)", 0.12, "c")],
        rows, caption="Bill of Materials (Steel, Concrete, and Reinforcement Quantities)", compact=True)
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}
""" + (table + K.note(M(NOTE), small=False)
        + K.figure(fig_paths.get("steel_chart"), "Structural steel quantities by member group (MT)")
        + K.figure(fig_paths.get("concrete_chart"), "Concrete volume and reinforcement weight"))
