"""Derive the report test scenarios S2-S6 from the S1 default input file.

Each scenario overrides a few inputs of tests/fixtures/reports/S1_default.osi to
exercise a different report path (see SCENARIOS). Run from the repo root:

    python scripts/report_dev/make_scenarios.py

The generated files are committed, so this only needs re-running if S1 changes.
"""
from __future__ import annotations

import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.normpath(os.path.join(HERE, "..", "..", "tests", "fixtures", "reports"))

SCENARIOS = {
    # Long span and wide carriageway: more and longer tables, page-breaking groups.
    "S2_long_span": {"geometry.span": "45", "geometry.carriageway_width": "10.5"},
    # Vehicle subset + user-defined footway pressure + footpaths on both sides.
    "S3_vehicle_subset_footway": {
        "loading.live_load.irc.70r_bogie": False, "loading.live_load.irc.70r_tracked": False,
        "loading.live_load.irc.aa_tracked": False, "loading.live_load.irc.aa_wheeled": False,
        "loading.live_load.irc.class_fatigue": False, "bl_irc_class_sv": False,
        "geometry.footpath": "Both Sides",
        "typical_section.no_of_footpaths": 2, "typical_section.footpath_width": 1.5,
        "loading.live_load.footpath_pressure.mode": "Custom",
        "loading.live_load.footpath_pressure.value": "3.0",
    },
    # Short span: a lightly loaded design that should mostly pass.
    "S4_short_span": {"geometry.span": "20"},
    # End diaphragm as a rolled beam instead of cross bracing (no diaphragm UR).
    "S5_end_diaphragm_beam": {
        f"member_properties.end_diaphragm_details.type.{p}.E{i}M{m}": "Rolled Beam"
        for i, p in enumerate(("G1G2", "G2G3", "G3G4"), start=1) for m in (1, 2)
    },
    # Non-default material grades: BOQ and report must follow the inputs.
    "S6_custom_grades": {
        "material.deck": "M30", "material.deck.fck": "30.0", "material.deck.ecm": "31.0",
        "material.deck.fctm": "2.5", "design_options.deck.reinforcement_material": "Fe 415",
    },
}


def main() -> None:
    with open(os.path.join(FIXTURES, "S1_default.osi")) as fh:
        base = yaml.safe_load(fh)
    for name, overrides in SCENARIOS.items():
        data = dict(base)
        missing = [k for k in overrides if k not in data]
        if missing:
            print(f"[{name}] adding keys not in S1: {missing}")
        data.update(overrides)
        path = os.path.join(FIXTURES, f"{name}.osi")
        with open(path, "w") as fh:
            yaml.safe_dump(data, fh, sort_keys=True, allow_unicode=True)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
