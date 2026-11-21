from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports.latex_kit import Col

# (S.N., description, key prefix in input_dict as produced by calculate_material_quantities)
_BOQ_ROWS = [
    ("1", "Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord", "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag"),
    ("3", "Concrete (M40) for Deck Slab", "concrete_deck"),
    ("4", "Reinforcement Steel (Fe 500)", "rebar_deck"),
    ("5", "Shear Stud Connectors", "shear_studs"),
    ("6", "Crash Barrier", "crash_barrier"),
]


def ch7_quantities(input_dict):
    rows = []
    for sn, desc, key in _BOQ_ROWS:
        rows.append((sn, desc) + tuple(
            input_dict.get(f"{key}_{suffix}", "N.A.")
            for suffix in ("vol_formula", "qty", "vol_total", "wt_single", "wt_total")))
    table = K.data_table(
        [Col("S.N.", 0.085, "c"), Col("Item Description", 0.255), Col("Volume", 0.19, "c"),
         Col("Quantity", 0.12, "c"), Col("Total Volume", 0.13, "c"), Col("Weight (MT)", 0.11, "c"),
         Col("Total Weight (MT)", 0.11, "c")],
        rows, caption="Bill of Materials (Steel, Concrete, and Reinforcement Quantities)", compact=True)
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}
""" + table
