"""Pure data for the design report: no LaTeX, no Qt, no file access.

Chapters turn these records into tables and charts, so the table, the chart and
the executive summary always agree.  Every rule here cites the IRC 6:2017 clause
it implements (text verified against the official code, 2017 edition).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

G = 9.81  # m/s2, tonne-force -> kN, as used by irc6_2017.py

# ---------------------------------------------------------------------------
# Live load: vehicles
# ---------------------------------------------------------------------------

# Nominal class weights in tonnes (IRC 6:2017 Cl. 204.1, 204.5, 204.6).  Totals for the
# vehicles that irc6_2017.py defines are taken from its wheel-load data so the report
# ties to the code constants; the others use these nominal weights.
NOMINAL_TONNES = {
    "class_a": 55.4,       # Cl. 204.1.1, train of 8 wheels
    "70r_wheeled": 100.0,  # Cl. 204.1.2
    "70r_tracked": 70.0,   # Cl. 204.1.2
    "aa_wheeled": 40.0,    # Cl. 204.1.3, two 20 t axles
    "aa_tracked": 70.0,    # Cl. 204.1.3
    "70r_bogie": 40.0,     # Cl. 204.1.2, two 20 t axles
    "sv": 385.0,           # Cl. 204.5.1
    "fatigue": 40.0,       # Cl. 204.6
}

# Vehicles the grillage analysis actually places: analyser.vehicle_lane_coordinates()
# builds IRC 6 Table 6A combinations of Class A and Class 70R (wheeled) only.
ANALYSED = {"class_a", "70r_wheeled"}

BRAKING_FRACTION = 0.20   # Cl. 211.2: 20 % of the first train of loads (one vehicle)
FATIGUE_IMPACT_FRACTION = 0.5   # Cl. 204.6: 50 % of the Cl. 208 impact factors


def impact_class_a(span_m: float) -> float:
    """Impact fraction for Class A/B on steel bridges, 3 m <= L <= 45 m (Cl. 208.2)."""
    L = min(max(float(span_m), 3.0), 45.0)
    return 9.0 / (13.5 + L)


def impact_wheeled(span_m: float) -> float:
    """Class AA / 70R **wheeled** on steel bridges (Cl. 208.3).

    25 % up to 23 m, then the Fig. 9 curve (9 / (13.5 + L)); 25 % for spans < 9 m.
    """
    L = float(span_m)
    if L < 23.0:
        return 0.25
    return 9.0 / (13.5 + min(L, 45.0))


def impact_tracked(span_m: float) -> float:
    """Class AA / 70R **tracked** on steel bridges (Cl. 208.3).

    10 % for L >= 9 m; below 9 m: 25 % up to 5 m, falling linearly to 10 % at 9 m.
    """
    L = float(span_m)
    if L >= 9.0:
        return 0.10
    if L <= 5.0:
        return 0.25
    return 0.25 - 0.15 * (L - 5.0) / 4.0


@dataclass(frozen=True)
class VehicleRow:
    key: str
    name: str
    total_kN: Optional[float]
    impact: Optional[float]          # None -> not applicable
    impact_ref: str                  # clause the impact value / "N/A" comes from
    braking_considered: Optional[bool]   # None -> not applicable
    braking_kN: Optional[float]
    eccentricity_m: Optional[float]
    analysed: bool                   # placed by the grillage analysis in this version
    note: str = ""


def _truthy(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "1")
    return bool(v)


def _float(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _code_total_kN(key: str) -> float:
    """Total vehicle load in kN: from the code data when available, else nominal tonnes."""
    try:
        from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017 as I
        if key == "class_a":
            return sum(I.cl_204_1_ClassA_vehicle()["wheel_loads"]) / 1000.0
        if key == "70r_wheeled":
            return sum(I.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]) / 1000.0
        if key == "sv":
            return float(I.cl_204_5_1_special_vehicle()["total_load_kN"])
        if key == "fatigue":
            return sum(I.cl_204_6_fatigue_load()["wheel_loads"]) / 1000.0
    except Exception:
        pass
    return NOMINAL_TONNES[key] * G


def collect_vehicle_rows(input_dict: dict) -> List[VehicleRow]:
    """One row per vehicle ticked in Additional Inputs -> Loading -> Live Load.

    Only ticked vehicles appear, in the order of the UI.  Braking follows the UI:
    it is derived for every ticked vehicle (Cl. 211.2); Class SV has its own opt-in
    checkbox (Cl. 204.5.4 does not require braking with SV); the fatigue truck is a
    stress-range check only.
    """
    from osdagbridge.core.utils.common import (
        KEY_BL_IRC_CLASS_SV, KEY_LL_CUSTOM_VEHICLES, KEY_LL_ECCENTRICITY, KEY_LL_IRC_70R_BOGIE,
        KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_AA_WHEELED,
        KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_IRC_CLASS_SV, KEY_SPAN,
    )
    span = _float(input_dict.get(KEY_SPAN))
    ecc = _float(input_dict.get(KEY_LL_ECCENTRICITY))
    sv_braking = _truthy(input_dict.get(KEY_BL_IRC_CLASS_SV, True))

    def imp(kind):
        if span is None:
            return None
        return {"a": impact_class_a, "w": impact_wheeled, "t": impact_tracked}[kind](span)

    spec = [
        ("class_a", KEY_LL_IRC_CLASS_A, "Class A", "a", "Cl. 208.2", True, ""),
        ("70r_wheeled", KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)", "w", "Cl. 208.3", True, ""),
        ("70r_tracked", KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)", "t", "Cl. 208.3", True, ""),
        ("aa_wheeled", KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)", "w", "Cl. 208.3", True, ""),
        ("aa_tracked", KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)", "t", "Cl. 208.3", True, ""),
        ("sv", KEY_LL_IRC_CLASS_SV, "Class SV", None, "Cl. 204.5.4", sv_braking,
         "Braking is not required with SV (Cl. 204.5.4); included because the SV braking option is ticked."
         if sv_braking else "Braking not considered (Cl. 204.5.4)."),
        ("70r_bogie", KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)", "w", "Cl. 208.3", True, ""),
        ("fatigue", KEY_LL_IRC_CLASS_FATIGUE, "Fatigue Vehicle", "f", "Cl. 204.6", None,
         "Used for the fatigue stress-range check only."),
    ]
    rows: List[VehicleRow] = []
    for key, ui_key, name, impact_kind, ref, braking, note in spec:
        if not _truthy(input_dict.get(ui_key)):
            continue
        total = _code_total_kN(key)
        if impact_kind is None:                 # SV
            impact_val = None
        elif impact_kind == "f":                # fatigue truck: 50 % of the wheeled value
            w = imp("w")
            impact_val = None if w is None else FATIGUE_IMPACT_FRACTION * w
        else:
            impact_val = imp(impact_kind)
        brk_on = None if key == "fatigue" else bool(braking)
        brk_kN = BRAKING_FRACTION * total if brk_on else None
        rows.append(VehicleRow(
            key=key, name=name, total_kN=total, impact=impact_val, impact_ref=ref,
            braking_considered=brk_on, braking_kN=brk_kN,
            eccentricity_m=ecc if brk_on else None,
            analysed=key in ANALYSED, note=note))

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for c in custom:
            name = c.get("name") if isinstance(c, dict) else (c if isinstance(c, str) else None)
            if name:
                rows.append(VehicleRow(
                    key="custom", name=str(name), total_kN=None, impact=None, impact_ref="user-defined",
                    braking_considered=None, braking_kN=None, eccentricity_m=None, analysed=False,
                    note="User-defined vehicle."))
    return rows


# ---------------------------------------------------------------------------
# Live load: footway
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FootwayRow:
    present: bool
    mode: str                         # "As per IRC 6" | "Custom"
    intensity_kN_m2: Optional[float]
    clause: str
    footpaths: int
    width_m: Optional[float]
    line_load_kN_m: Optional[float]   # intensity x width, per footpath
    impact_note: str = "Not applicable (Cl. 208.4)"


def collect_footway(input_dict: dict) -> FootwayRow:
    from osdagbridge.core.utils.common import (
        KEY_FOOTPATH, KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
        KEY_TS_FOOTPATH_WIDTH,
    )
    footpath = str(input_dict.get(KEY_FOOTPATH, "") or "").strip().lower()
    n_paths = {"single side": 1, "single": 1, "both sides": 2, "both": 2}.get(footpath, 0)
    try:
        n_paths = n_paths or int(float(input_dict.get("typical_section.no_of_footpaths", 0) or 0))
    except (TypeError, ValueError):
        pass
    width = _float(input_dict.get(KEY_TS_FOOTPATH_WIDTH))
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "As per IRC 6") or "As per IRC 6").strip()
    custom = _float(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
    if mode.lower().startswith("as per") or mode.lower() == "automatic":
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            intensity = IRC6_2017.cl_206_1_footway_load()
        except Exception:
            intensity = None
        clause, mode = "IRC 6 Cl. 206.1", "As per IRC 6"
    else:
        intensity, clause = custom, "User-defined"
    present = n_paths > 0 and bool(width)
    line = intensity * width if (present and intensity is not None and width) else None
    return FootwayRow(present=present, mode=mode, intensity_kN_m2=intensity, clause=clause,
                      footpaths=n_paths, width_m=width, line_load_kN_m=line)
