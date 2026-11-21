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


# ---------------------------------------------------------------------------
# Design check summary: one row per member / check (feeds Table 5.x, the UR chart
# and the executive summary, so the three can never disagree)
# ---------------------------------------------------------------------------

ELEMENT_ORDER = ("Girder", "Deck", "Cross bracing", "End diaphragm")


@dataclass(frozen=True)
class URRow:
    element: str                    # one of ELEMENT_ORDER
    label: str                      # table / chart label
    gov_lc: Optional[str] = None
    demand: Optional[str] = None    # display strings, units included
    capacity: Optional[str] = None
    ur: Optional[float] = None      # None -> no numeric result (n/a)
    applicable: bool = True         # False -> check does not apply to this bridge
    message: str = ""               # whole-row message, e.g. "design not available"

    @property
    def status(self) -> str:
        """'PASS' / 'FAIL' by the single rule in theme.ur_passes, else 'n/a'."""
        if self.ur is None:
            return "n/a"
        from osdagbridge.core.reports.theme import ur_passes
        return "PASS" if ur_passes(self.ur) else "FAIL"


def _num(v, nd: int = 2) -> Optional[str]:
    f = _float(v)
    return None if f is None else f"{f:.{nd}f}"


def _with_unit(v, unit) -> Optional[str]:
    s = _num(v)
    if s is None:
        return None
    u = (unit or "").strip()
    return f"{s} {u}" if u else s


class BraceResults:
    """Read-only view of a cross-bracing or end-diaphragm result pair.

    ``forces`` is ``*_forces_dict`` ({"pairs": {pair: {...gov_lc...}}}) and
    ``designs`` is ``*_design_results`` ({pair: {member: {force_type: raw}}}).
    Cross bracing and end diaphragms use the same shape but different dicts, so
    this class is what stops one from being shown as the other.
    """
    MEMBERS = ("diagonal", "chord")
    LIMITS = {"diagonal": 250.0, "chord": 400.0}

    def __init__(self, forces, designs):
        self.forces = forces if isinstance(forces, dict) else {}
        self.designs = designs if isinstance(designs, dict) else {}

    def pairs(self) -> List[str]:
        p = self.forces.get("pairs")
        return sorted(p) if isinstance(p, dict) else []

    def summary(self, pair, member, force_type) -> dict:
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        try:
            return _extract_osdag_summary(self.designs[pair][member][force_type] or {})
        except (KeyError, TypeError):
            return {}

    def has_results(self) -> bool:
        return any(_float(self.summary(p, m, ft).get("efficiency")) is not None
                   for p in self.pairs() for m in self.MEMBERS for ft in ("tension", "compression"))

    def gov_lc(self, pair, member, force_type) -> Optional[str]:
        pfx = "diag" if member == "diagonal" else "chord"
        try:
            v = self.forces["pairs"][pair].get(f"{pfx}_{force_type}_gov_lc")
            return str(v) if v else None
        except (KeyError, TypeError):
            return None

    def slenderness(self, pair, member) -> Optional[float]:
        for ft in ("compression", "tension"):
            v = _float(self.summary(pair, member, ft).get("slenderness"))
            if v is not None:
                return v
        return None

    def worst_force(self, element: str, label: str, force_type: str) -> URRow:
        best = None
        for pair in self.pairs():
            for member in self.MEMBERS:
                s = self.summary(pair, member, force_type)
                ur = _float(s.get("efficiency"))
                if ur is not None and (best is None or ur > best[0]):
                    best = (ur, pair, member, _float(s.get("capacity_kN")))
        if best is None:
            return URRow(element, label)
        ur, pair, member, cap = best
        return URRow(element, label, self.gov_lc(pair, member, force_type),
                     f"{cap * ur:.2f} kN" if cap else None,
                     f"{cap:.3f} kN" if cap else None, ur)

    def worst_slenderness(self, element: str, label: str) -> URRow:
        best = None
        for pair in self.pairs():
            for member in self.MEMBERS:
                sf = self.slenderness(pair, member)
                if sf is None:
                    continue
                lim = self.LIMITS[member]
                if best is None or sf / lim > best[0]:
                    best = (sf / lim, sf, lim)
        if best is None:
            return URRow(element, label)
        ratio, sf, lim = best
        return URRow(element, label, None, f"{sf:.1f}", f"{lim:.0f}", ratio)


def end_diaphragm_type(input_dict: dict) -> str:
    from osdagbridge.core.utils.common import KEY_MP_ED_TYPE
    for k, v in input_dict.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            return str(v).strip()
    return ""


def cross_bracing_results(output_dict: dict) -> BraceResults:
    return BraceResults(output_dict.get("crossbracing_forces_dict"),
                        output_dict.get("crossbracing_design_results"))


def end_diaphragm_results(output_dict: dict) -> BraceResults:
    return BraceResults(output_dict.get("end_diaphragm_forces_dict"),
                        output_dict.get("end_diaphragm_design_results"))


def _pg_gov_lc(pg: dict, g, ids) -> Optional[str]:
    best = None
    for lc, ld in (pg.get(g) or {}).get("per_lc", {}).items():
        if str(lc).lower().startswith("envelope"):
            continue
        for chk in ld.get("checks") or []:
            if chk.get("id") in ids:
                d = chk.get("dcr") or 0.0
                if best is None or d > best[0]:
                    best = (d, lc)
    return str(best[1]).strip() if best else None


def _pg_row(pg: dict, element: str, label: str, ids, fallback_unit: str = "") -> URRow:
    """Governing (largest-UR) result of check ids ``ids`` over all non-edge girders."""
    best = None
    for g, gd in pg.items():
        if str(g).startswith("EB"):
            continue
        for chk in gd.get("checks") or []:
            if chk.get("check_id") in ids:
                d = chk.get("dcr") or 0.0
                if best is None or d > best[0]:
                    best = (d, chk.get("demand"), chk.get("capacity"),
                            chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
    if best is not None:
        d, dem, cap, du, cu, g = best
        return URRow(element, label, _pg_gov_lc(pg, g, ids), _with_unit(dem, du), _with_unit(cap, cu), _float(d))
    best = None                    # per-load-case fallback (no units), e.g. deflection
    for g, gd in pg.items():
        if str(g).startswith("EB"):
            continue
        for lc, ld in (gd.get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in ld.get("checks") or []:
                if chk.get("id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"), lc)
    if best is None:
        return URRow(element, label)
    d, dem, cap, lc = best
    return URRow(element, label, str(lc).strip(), _with_unit(dem, fallback_unit),
                 _with_unit(cap, fallback_unit), _float(d))


def _gov_sls_frequent(pg: dict) -> str:
    best = None
    for g, gd in pg.items():
        if str(g).startswith("EB"):
            continue
        for lc, ld in (gd.get("per_lc") or {}).items():
            if "frequent" not in str(lc).lower():
                continue
            d = ld.get("max_dcr") or 0.0
            if best is None or d > best[0]:
                best = (d, lc)
    return str(best[1]).strip() if best else "Frequent SLS"


def collect_ur_rows(input_dict: dict, output_dict: dict) -> List[URRow]:
    """Every utilisation-ratio row of the design check summary, in report order.

    Values are read from stored results only; nothing is recalculated.  A check
    with no result gets ``ur=None`` (shown as a dash, plotted as n/a), never 0.
    End diaphragms read ``end_diaphragm_*`` results, never the cross-bracing ones.
    """
    from osdagbridge.core.utils.common import (
        KEY_DD_GAMMA_DL, KEY_DD_GAMMA_LL, KEY_DD_HAS_OVERHANG, KEY_DD_M_ULS_HOG, KEY_DD_M_ULS_OH,
        KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, KEY_DD_MU_OH, KEY_DD_MU_TOP, KEY_DD_PUNCH_VED,
        KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, KEY_DD_VRD_C_MPA, KEY_DD_WK_BOT, KEY_DD_WK_LIMIT,
        KEY_DD_WK_OH, KEY_DD_WK_TOP,
    )
    od = output_dict or {}
    pg = (od.get("design_results", {}) or {}).get("per_girder", {}) or {}
    rpt = od.get("deck_report_values", {}) or {}
    has = bool(rpt)
    has_oh = bool(rpt.get(KEY_DD_HAS_OVERHANG))

    def dkv(key, default=0.0):
        f = _float(rpt.get(key))
        return default if f is None else f

    combo = f"Basic ULS: {dkv(KEY_DD_GAMMA_DL):g}DL + {dkv(KEY_DD_GAMMA_LL):g}LL" if has else None

    def deck(label, dem_key, cap_key, unit, overhang=False) -> URRow:
        if not has:
            return URRow("Deck", label)
        if overhang and not has_oh:
            return URRow("Deck", label, combo, "N/A", "N/A", None, applicable=False)
        dem, cap = dkv(dem_key), dkv(cap_key)
        return URRow("Deck", label, combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}",
                     dem / cap if cap > 0 else None)

    wks = [dkv(KEY_DD_WK_BOT), dkv(KEY_DD_WK_TOP)] + ([dkv(KEY_DD_WK_OH)] if has_oh else [])
    gov_wk, wk_lim = max(wks), dkv(KEY_DD_WK_LIMIT)
    crack = (URRow("Deck", "Crack Width (slab)", _gov_sls_frequent(pg), f"{gov_wk:.3f} mm", f"{wk_lim:.3f} mm",
                   gov_wk / wk_lim if wk_lim > 0 else None)
             if has else URRow("Deck", "Crack Width (slab)"))

    cb = cross_bracing_results(od)
    ed = end_diaphragm_results(od)
    ed_type = end_diaphragm_type(input_dict or {})
    if ed.has_results():
        ed_rows = [ed.worst_force("End diaphragm", "End Diaphragm --- Compression", "compression"),
                   ed.worst_force("End diaphragm", "End Diaphragm --- Tension", "tension"),
                   ed.worst_slenderness("End diaphragm", "End Diaphragm --- Slenderness")]
    else:
        if "brac" in ed_type.lower():
            msg = "Design results not available for this configuration"
        elif ed_type:
            msg = "Rolled / Welded section --- design to be added"
        else:
            msg = "No end diaphragm type selected; no design performed"
        ed_rows = [URRow("End diaphragm", "End Diaphragm --- Compression", message=msg, applicable=False),
                   URRow("End diaphragm", "End Diaphragm --- Tension", message=msg, applicable=False)]

    return [
        *_girder_rows(pg),
        _pg_row(pg, "Deck", "Transverse Shear (slab)", {16}),
        crack,
        deck("Deck --- Flexure (sagging)", KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m"),
        deck("Deck --- Flexure (hogging)", KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m"),
        deck("Deck --- Cantilever Overhang", KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", overhang=True),
        deck("Deck --- Punching Shear", KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa"),
        deck("Deck --- One-Way Shear", KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m"),
        cb.worst_force("Cross bracing", "Cross Bracing --- Compression", "compression"),
        cb.worst_force("Cross bracing", "Cross Bracing --- Tension", "tension"),
        cb.worst_slenderness("Cross bracing", "Cross Bracing --- Slenderness"),
        *ed_rows,
    ]


def _girder_rows(pg: dict) -> List[URRow]:
    return [
        _pg_row(pg, "Girder", "Girder --- Moment", {1}),
        _pg_row(pg, "Girder", "Girder --- Shear", {2}),
        _pg_row(pg, "Girder", "Girder --- LTB (constr.)", {5}),
        _pg_row(pg, "Girder", "Girder --- Deflection", {13, 14}, "mm"),
        _pg_row(pg, "Girder", "Girder --- Stress", {11}, "MPa"),
        _pg_row(pg, "Girder", "Girder --- Fatigue", {8, 9}, "MPa"),
    ]


def element_verdicts(rows: List[URRow]) -> dict:
    """Per element: ('PASS'|'FAIL'|'n/a', max UR or None).  FAIL if any row fails."""
    out = {}
    for el in ELEMENT_ORDER:
        urs = [r.ur for r in rows if r.element == el and r.ur is not None]
        if not urs:
            out[el] = ("n/a", None)
            continue
        from osdagbridge.core.reports.theme import ur_passes
        m = max(urs)
        out[el] = ("PASS" if ur_passes(m) else "FAIL", m)
    return out
