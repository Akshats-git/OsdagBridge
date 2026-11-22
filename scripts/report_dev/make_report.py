"""Headless OsdagBridge report harness.

Regenerates the design report without clicking through the GUI, so report-code
changes can be checked in seconds.

Two modes:

  1. From a saved .osi (runs the full design pipeline, same calls as the GUI):
       python scripts/report_dev/make_report.py --osi cases/S1_default.osi \
              --out out/S1 --save-snapshot snapshots/S1.pkl

  2. From a snapshot (skips the design, regenerates the report only, ~seconds):
       python scripts/report_dev/make_report.py --snapshot snapshots/S1.pkl --out out/S1

The snapshot pickles input_dict / output_dict (plus the analysis summaries the
backend attaches), which is everything generate_report() consumes.

Note: CAD views and analysis plots are only rendered by the desktop GUI, so
reports made here show figure placeholders. Use the GUI for the final PDFs.
"""
from __future__ import annotations

import argparse
import datetime
import os
import pickle
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

ALL_SECTIONS = [
    "exec_summary", "project_info", "input_parameters", "loads", "analysis",
    "design_checks", "drawings", "quantities", "standards",
    "design_log_window", "references",
]


def _request(out_dir: str, stem: str, sections=None):
    from osdagbridge.core.reports.report_generator import (
        ReportMetadata, ReportOptions, ReportRequest,
    )
    md = ReportMetadata(
        project_name="OsdagBridge Report Test S1",
        project_location="Darjeeling, West Bengal",
        designer="Akshat Gupta",
        reviewer="FOSSEE Osdag Team",
        client="Screening Task Demo",
        company="FOSSEE, IIT Bombay",
        group_name="FOSSEE",
        subtitle="Rev 0",
        job_number="OB-S1-001",
        additional_comments="",
        logo_path=None,
        report_date=datetime.date.today().isoformat(),
    )
    opts = ReportOptions(sections=list(sections or ALL_SECTIONS), include_figures=True,
                         include_toc=True, include_pdf=True)
    return ReportRequest(metadata=md, options=opts,
                         output_dir=os.path.abspath(out_dir), file_stem=stem)


def gui_parity(data: dict) -> None:
    """Apply the input-dict updates the GUI makes when Design is clicked.

    The desktop app (template_page.common_design_func) runs every Additional
    Inputs ``on_change_compute`` function on the input dict right before the
    design. Some of these overwrite stored values: for "IRC 5 - RCC Railing" the
    railing load becomes 6.806 kN/m (IRC 5 barrier body) instead of the 1.4715
    kN/m (IRC 6 Cl. 206.5) written by the core defaults. Without this step a
    headless run differs from the GUI by ~0.3 % in governing forces.

    The real dialog is built on Qt's offscreen platform so the GUI's own code
    is reused rather than re-implemented.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict
    from osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs import AdditionalInputs

    _app = QApplication.instance() or QApplication([])
    # solve_extend_basic_input_dict re-seeds the Loading tab defaults (all vehicles
    # ticked ...). In the GUI the user's Additional Inputs are applied after it, so
    # keep what the .osi says for those keys.
    saved = {k: v for k, v in data.items() if k.startswith(("loading.", "bl_", "design_options", "material."))}
    solve_extend_basic_input_dict(data)          # as loadOSI_inputs / Design do
    data.update(saved)
    dlg = AdditionalInputs()
    dlg.set_input_dictionary(data)               # as _show_additional_inputs does
    changed = {}
    for name in dlg._compute_functions:           # as _sync_compute_results_to_input_dict
        fn = getattr(dlg, name, None)
        if fn is None:
            continue
        result = fn(data)
        if isinstance(result, dict):
            for k, v in result.items():
                if str(data.get(k)) != str(v):
                    changed[k] = (data.get(k), v)
            data.update(result)
    print(f"[harness] gui-parity: {len(dlg._compute_functions)} compute fn(s), "
          f"{len(changed)} value(s) changed")
    for k, (old, new) in changed.items():
        print(f"           {k}: {old!r} -> {new!r}")


def run_design(osi_path: str, parity: bool = True) -> dict:
    """Load an .osi and run the design exactly as the GUI worker does."""
    import yaml
    from osdagbridge.core.utils.osi_validator import validate_osi_inputs
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge

    with open(osi_path, "r") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SystemExit(f"{osi_path}: not a valid input dictionary")
    res = validate_osi_inputs(data)
    if not res.is_valid:
        raise SystemExit(f"{osi_path}: invalid OSI inputs: {res}")

    if parity:
        gui_parity(data)

    bridge = PlateGirderBridge()
    t0 = time.time()
    bridge.set_input(data)
    bridge.design()
    print(f"[harness] design finished in {time.time() - t0:.1f}s")

    output_dict = dict(bridge.output_dict)
    lc_sum = getattr(bridge, "_lc_summary", None)
    rxn_sum = getattr(bridge, "_reaction_summary", None)
    if lc_sum is not None or rxn_sum is not None:
        output_dict["analysis_summary"] = {"load_cases": lc_sum or {},
                                           "reactions": rxn_sum or {}}
    return {"input_dict": dict(bridge.input_dict), "output_dict": output_dict,
            "source": os.path.abspath(osi_path)}


def save_snapshot(snap: dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        with open(path, "wb") as fh:
            pickle.dump(snap, fh)
    except Exception as exc:  # some solver objects may not pickle; drop them
        print(f"[harness] full pickle failed ({exc}); dropping unpicklable keys")
        clean = {}
        for part in ("input_dict", "output_dict"):
            clean[part] = {}
            for k, v in snap[part].items():
                try:
                    pickle.dumps(v)
                    clean[part][k] = v
                except Exception:
                    print(f"[harness]   skipped {part}[{k!r}] ({type(v).__name__})")
        clean["source"] = snap.get("source")
        with open(path, "wb") as fh:
            pickle.dump(clean, fh)
    print(f"[harness] snapshot -> {path}")


def make_report(snap: dict, out_dir: str, stem: str, sections=None) -> None:
    from osdagbridge.core.reports.report_generator import build_report_payload, generate_report

    os.environ["OSDAGBRIDGE_KEEP_LATEX_LOG"] = "1"      # keep the real build log next to the PDF
    req = _request(out_dir, stem, sections)
    payload = build_report_payload(req, dict(snap["input_dict"]), dict(snap["output_dict"]))
    t0 = time.time()
    result = generate_report(payload, req)
    print(f"[harness] report generated in {time.time() - t0:.1f}s")
    print(f"[harness] pdf: {result.pdf_path}")
    print(f"[harness] tex: {result.tex_path}")
    if not result.pdf_path:
        raise SystemExit(1)
    if not os.path.exists(os.path.join(out_dir, stem + ".log")):
        _write_log(result.tex_path, out_dir)


def _write_log(tex_path: str, out_dir: str) -> None:
    """Recompile the saved .tex once so a pdflatex .log sits next to the PDF
    (generate_report compiles in a temp dir that is deleted)."""
    import shutil
    import subprocess
    exe = shutil.which("pdflatex")
    if not exe:
        try:
            from osdag_latex_env import OsdagLatexEnv  # type: ignore
            exe = str(OsdagLatexEnv().pdflatex)
        except Exception:
            exe = None
    if not exe:
        print("[harness] pdflatex not found, skipping .log")
        return
    work = os.path.join(out_dir, "_build")
    os.makedirs(work, exist_ok=True)
    stem = os.path.splitext(os.path.basename(tex_path))[0]
    shutil.copy2(tex_path, work)
    for _ in range(2):
        subprocess.run([exe, "-interaction=nonstopmode", stem + ".tex"], cwd=work,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    shutil.copy2(os.path.join(work, stem + ".log"), os.path.join(out_dir, stem + ".log"))
    shutil.rmtree(work, ignore_errors=True)
    print(f"[harness] log: {os.path.join(out_dir, stem + '.log')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--osi", help="saved .osi input file (runs the design)")
    src.add_argument("--snapshot", help="pickled snapshot from a previous --osi run")
    ap.add_argument("--out", required=True, help="output directory for the PDF/.tex")
    ap.add_argument("--stem", default="report", help="output file name without extension")
    ap.add_argument("--save-snapshot", help="where to write the snapshot (with --osi)")
    ap.add_argument("--no-gui-parity", action="store_true",
                    help="skip the GUI Design-time compute step (see gui_parity)")
    ap.add_argument("--sections", help="comma-separated section keys to include (default: all)")
    args = ap.parse_args()

    if args.osi:
        snap = run_design(args.osi, parity=not args.no_gui_parity)
        if args.save_snapshot:
            save_snapshot(snap, args.save_snapshot)
    else:
        with open(args.snapshot, "rb") as fh:
            snap = pickle.load(fh)

    make_report(snap, args.out, args.stem, args.sections.split(",") if args.sections else None)


if __name__ == "__main__":
    main()
