# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports import report_data as D
from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.latex_kit import Col
from osdagbridge.core.reports.report_utils import val


def _live_load_tables(d):
    """Vehicular and footway live load tables (Chapter 3), from report_data."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    rows = D.collect_vehicle_rows(d)
    out = []
    if not rows:
        out.append(K.note("No IRC vehicle is selected in Additional Inputs, so no vehicular live load is applied.",
                          small=False))
    else:
        def impact_cell(r):
            if r.impact is None:
                return f"N/A ({r.impact_ref})" if r.key == "sv" else "---"
            return f"{r.impact:.3f} ({r.impact_ref})"

        def considered(r):
            return "N/A" if r.braking_considered is None else ("Yes" if r.braking_considered else "No")

        table_rows = []
        for r in rows:
            name = K.join(r.name, K.raw(r"$^{\dagger}$")) if not r.analysed else r.name
            table_rows.append((
                name, T.fmt(r.total_kN, 2), impact_cell(r), considered(r),
                T.fmt(r.braking_kN, 2) if r.braking_kN is not None else ("N/A" if r.braking_considered is None else "---"),
                T.fmt(r.eccentricity_m, 2) if r.eccentricity_m is not None else "---"))
        out.append(K.data_table(
            [Col("Vehicle", 0.22), Col("Total Load (kN)", 0.11, "c"), Col("Impact Factor", 0.19, "c"),
             Col("Considered?", 0.17, "c"), Col("Value (kN)", 0.12, "c"), Col("Eccentricity (m)", 0.19, "c")],
            table_rows, caption="Vehicular Live Load (IRC 6:2017)", compact=True,
            header_groups=[("", 3), ("Braking Load (Cl. 211)", 3)]))
        notes = [
            "Impact factors are per vehicle as given in IRC 6 Cl. 208.2 (Class A) and Cl. 208.3 "
            "(Class AA / 70R) for steel bridges; no impact is applied to braking (Cl. 211.2) or to the "
            "footway load (Cl. 208.4). Braking is 20% of the vehicle load (first train, Cl. 211.2) and acts "
            "at the eccentricity above the deck given in Cl. 211.3.",
        ]
        sv = [r for r in rows if r.key == "sv"]
        if sv and sv[0].note:
            notes.append("Class SV: " + sv[0].note)
        if any(not r.analysed for r in rows):
            notes.append(K.join(
                K.raw(r"$^{\dagger}$"), " Selected in Additional Inputs but not placed by the grillage analysis "
                "in this version: the analysis uses IRC 6 Table 6A combinations of Class A and Class 70R "
                "(wheeled) loading."))
        span = D._float(d.get(KEY_SPAN))
        if span is not None:
            try:
                notes.append("The grillage analysis applies one dynamic load allowance, 1 + %.3f, to all vehicle "
                             "load cases." % IRC6_2017.cl_208_3_impact_factor(span))
            except Exception:
                pass
        for n in notes:
            out.append(K.note(n))
        out.append(K.kv_table([
            ("Braking force (Cl. 211)", "Considered per vehicle, see the vehicular live load table"),
            ("Centrifugal force (Cl. 212)",
             "Not applicable: the alignment is straight (the inputs contain no curvature)"),
        ], caption="Other Live Load Effects (IRC 6:2017)", header=("Effect", "Status")))

    fw = D.collect_footway(d)
    if fw.present:
        out.append(K.kv_table([
            ("Footway pressure mode", fw.mode),
            ("Footway intensity", K.join(T.fmt(fw.intensity_kN_m2, 3), K.raw(r" kN/m$^2$"), f" ({fw.clause})")),
            ("Footpaths \u00d7 width", f"{fw.footpaths} \u00d7 {fw.width_m:g} m"),
            ("Footway line load (per footpath)", K.join(T.fmt(fw.line_load_kN_m, 3), " kN/m")),
            ("Impact", fw.impact_note),
        ], caption="Footway Live Load (IRC 6:2017)", header=("Parameter", "Value")))
    else:
        out.append(K.kv_table([("Footway", "No footpath provided: no footway live load is applied")],
                              caption="Footway Live Load (IRC 6:2017)", header=("Parameter", "Value")))
    return "".join(out)


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, factor in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(factor, dict):  # permanent load with adding/relieving
                add = factor.get('adding')
                rel = factor.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if factor is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({factor:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        lc_rows.append((f"ULS-{i:02d}", _fmt_factors(combo['factors'])))
    for i, combo in enumerate(sls_combos, start=1):
        lc_rows.append((f"SLS-{i:02d}", _fmt_factors(combo['factors'])))

    d = input_dict
    P = ("Parameter", "Value")
    sup3 = K.raw(r" kN/m\textsuperscript{3}")
    sup2_n = K.raw(r" N/m\textsuperscript{2}")
    deg_c = K.raw(r" $^\circ$C")

    parts = [r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.
"""]

    parts.append(K.kv_table([
        ("Steel Self-Weight Applied", K.join(val(d, KEY_MATERIAL_GIRDER_DENSITY), sup3)),
        ("Concrete Deck Weight", K.join(val(d, KEY_MATERIAL_DECK_DENSITY), sup3)),
        ("Self-Weight Factor", val(d, KEY_PL_SELF_WEIGHT_FACTOR)),
    ], caption="Dead Load -- Self Weight", header=P))

    parts.append(K.kv_table([
        ("Wearing Course Load", K.join(val(d, KEY_WC_MATERIAL), " x ", val(d, KEY_WC_THICKNESS))),
        ("Additional SIDL (Crash Barrier)", K.join(val(d, KEY_CB_LOAD), " kN/m per barrier")),
        ("Railing Load", K.join(val(d, KEY_RL_LOAD_VALUE), K.raw(r" kN/m\sdstar{}"))),
    ], caption="Dead Load for Surfacing (DW)", header=P))

    parts.append(_live_load_tables(d))

    parts.append(K.kv_table([
        ("Basic Wind Speed, Vb", K.join(val(d, "wind_speed", " m/s"), " [from Project Location]")),
        ("Terrain Type", val(d, KEY_WL_TERRAIN_TYPE)),
        ("Average Exposed Height, H (m)", val(d, KEY_WL_AVG_EXPOSED_HEIGHT, " m")),
        ("Hourly Mean Wind Speed, Vz", val(d, KEY_WL_HOURLY_MEAN_WIND, " m/s")),
        ("Hourly Wind Pressure, Pz", K.join(val(d, KEY_WL_HOURLY_WIND_PRESSURE), sup2_n)),
        ("Transverse Wind Force", val(d, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")),
        ("Longitudinal Wind Force", val(d, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")),
        ("Vertical Wind Force", val(d, KEY_WL_VERTICAL_WIND_FORCE, " kN")),
    ], caption="Wind Load (WL) --- per IRC 6", header=P))

    parts.append(K.kv_table([
        ("Seismic Zone", K.join(val(d, "seismic_zone"), " [from Project Location]")),
        ("Zone Factor, Z", val(d, KEY_SL_ZONE_FACTOR)),
        ("Importance Factor, I", val(d, KEY_SL_IMPORTANCE_FACTOR)),
        ("Type of Soil", val(d, KEY_SL_SOIL_TYPE)),
        ("Sa/g", val(d, KEY_SL_SPECTRAL_COEFF)),
        ("Horizontal Seismic Coefficient, Ah", val(d, KEY_SL_HORIZONTAL_COEFF)),
        ("Vertical Seismic Coefficient, Av", val(d, KEY_SL_VERTICAL_COEFF)),
        ("Horizontal Seismic Force (longitudinal)", K.na("not computed in this version")),
        ("Horizontal Seismic Force (transverse)", K.na("not computed in this version")),
    ], caption="Earthquake Load (EL) --- per IRC 6", header=P))

    parts.append(K.kv_table([
        ("Maximum Shade Temperature", K.join(val(d, "shade_temp_max"), deg_c)),
        ("Minimum Shade Temperature", K.join(val(d, "shade_temp_min"), deg_c)),
        ("Effective Bridge Temp. Range",
         K.join(val(d, KEY_TL_BRIDGE_TEMP_MIN), " to ", val(d, KEY_TL_BRIDGE_TEMP_MAX), deg_c)),
        ("Temperature Rise / Fall for Design",
         K.join("+", val(d, KEY_TL_TEMP_RISE), deg_c, K.raw(r" / \textminus{}"),
                val(d, KEY_TL_TEMP_FALL), deg_c)),
    ], caption="Temperature Load (TL) --- per IRC 6", header=P))

    parts.append(K.data_table(
        [Col("Combination ID", 0.26, "c"), Col("Load Cases", 0.74)],
        lc_rows, caption="Load Combinations"))
    parts.append(K.note("Note: All IRC 6 load combinations are auto-generated by OsdagBridge. "
                        "User-defined custom combinations, if any, are appended.", small=False))
    return "".join(parts)
