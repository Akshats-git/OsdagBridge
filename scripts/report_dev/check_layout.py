"""Measure report layout quality so Before/After can be compared with numbers.

Checks
------
0. margin  - text / table rules extending past the right page margin.
1. footer  - body text that runs into the footer band (below/onto the footer rule)
             or into the header band, per page.
2. headers - longtables in the .tex source and how many repeat their header
             on continuation pages (\\endhead present).
3. numbers - (with --compare) numeric tokens present in the BEFORE pdf text but
             missing from the AFTER pdf text, i.e. values lost in a refactor.

Usage
-----
  python scripts/report_dev/check_layout.py report.pdf [--tex report.tex]
  python scripts/report_dev/check_layout.py after.pdf --compare before.pdf
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

import pdfplumber

FOOTER_MARKERS = ("Osdag", "FOSSEE", "Page ", "Software default")
RULE_MAX_THICKNESS = 2.0  # pt


def _rules(page):
    """Return y-positions (top) of thin full-width horizontal rules."""
    ys = []
    min_w = page.width * 0.6
    for r in list(page.rects) + list(page.lines):
        w = abs(r["x1"] - r["x0"])
        h = abs(r["bottom"] - r["top"])
        if w >= min_w and h <= RULE_MAX_THICKNESS:
            ys.append(r["top"])
    return sorted(ys)


def _lines(page):
    words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
    rows = {}
    for w in words:
        key = round(w["top"])
        rows.setdefault(key, []).append(w)
    out = []
    for _, ws in sorted(rows.items()):
        out.append({
            "text": " ".join(w["text"] for w in ws),
            "top": min(w["top"] for w in ws),
            "bottom": max(w["bottom"] for w in ws),
        })
    return out


def check_footer(pdf_path: str) -> list[dict]:
    issues = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            rules = _rules(page)
            if not rules:
                continue  # title page etc.
            footer_y = max(rules) if max(rules) > page.height * 0.7 else None
            header_y = min(rules) if min(rules) < page.height * 0.3 else None
            for ln in _lines(page):
                txt = ln["text"].strip()
                if not txt or any(m in txt for m in FOOTER_MARKERS):
                    continue
                if footer_y is not None and ln["bottom"] > footer_y - 1.0:
                    issues.append({"page": pno, "zone": "footer", "text": txt[:70],
                                   "overlap_pt": round(ln["bottom"] - footer_y, 1)})
                if header_y is not None and ln["top"] < header_y + 1.0 and ln["top"] > 0:
                    # header text (project name / date) sits above the rule legitimately
                    if ln["bottom"] > header_y + 1.0:
                        issues.append({"page": pno, "zone": "header", "text": txt[:70],
                                       "overlap_pt": round(ln["bottom"] - header_y, 1)})
    return issues


def check_right_margin(pdf_path: str, margin_pt: float = 72.0, tol: float = 2.0) -> list[dict]:
    """Pages where text or vertical table rules extend past the right margin."""
    hits = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            limit = page.width - margin_pt + tol
            xs = [c["x1"] for c in page.chars if c["x1"] > limit]
            xs += [r["x1"] for r in list(page.rects) + list(page.lines)
                   if r["x1"] > limit and abs(r["x1"] - r["x0"]) < 2]
            if xs:
                hits.append({"page": pno, "overflow_pt": round(max(xs) - (page.width - margin_pt), 1)})
    return hits


def check_headers(tex_path: str) -> dict:
    with open(tex_path, encoding="utf-8") as fh:
        tex = fh.read()
    blocks = re.findall(r"\\begin\{longtable\}.*?\\end\{longtable\}", tex, flags=re.S)
    with_head = [b for b in blocks if "\\endhead" in b]
    captions = []
    for b in blocks:
        if "\\endhead" not in b:
            m = re.search(r"\\caption\*?\{(.*?)\}\s*(\\\\|\n)", b, flags=re.S)
            captions.append(re.sub(r"\\textbf\{|\}", "", m.group(1))[:60] if m else "(no caption)")
    return {"longtables": len(blocks), "repeat_header": len(with_head),
            "missing": captions}


def check_log(log_path: str) -> dict:
    """Summarise a pdflatex .log: hidden errors, overfull boxes, header warnings."""
    with open(log_path, encoding="utf-8", errors="ignore") as fh:
        log = fh.read()
    return {
        "errors": len(re.findall(r"^!", log, flags=re.M)),
        "overfull_hbox": len(re.findall(r"Overfull \\hbox", log)),
        "overfull_vbox": len(re.findall(r"Overfull \\vbox", log)),
        "headheight_warnings": len(re.findall(r"headheight is too small", log)),
        "open_groups": len(re.findall(r"semi simple group \(level", log)),
    }


def check_orphan_headings(pdf_path: str) -> list[dict]:
    """Section/caption headings that are the last body line of a page."""
    hits = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            lines = [l for l in _lines(page) if l["bottom"] < page.height - 90]
            if not lines:
                continue
            txt = lines[-1]["text"].strip()
            # a heading is words only; "1.5 EQ (b) 219.2 G1 ..." is a table row (load factor)
            if re.match(r"^\d+(\.\d+)+\s+[A-Z][A-Za-z ,&/()'-]+$", txt) or re.match(r"^Table \d+\.\d+", txt):
                hits.append({"page": pno, "text": txt[:60]})
    return hits


NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


_NOISE_RE = re.compile(r"Page \d+ of \d+|(?:Table|Figure|Chapter)\s+\d+(?:\.\d+)*[a-z]?")


def _numbers(pdf_path: str) -> Counter:
    """Numeric tokens in the body text, ignoring layout-dependent numbers:
    the table of contents, "Page x of y" and "Table x.y" / "Figure n" labels
    (these shift whenever pagination or table numbering changes)."""
    c = Counter()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "Table of Contents" in text:
                continue
            c.update(NUM_RE.findall(_NOISE_RE.sub(" ", text)))
    return c


def compare_numbers(before: str, after: str) -> Counter:
    return _numbers(before) - _numbers(after)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--tex", help="LaTeX source for the header-repeat check")
    ap.add_argument("--log", help="pdflatex .log for the compile-health check")
    ap.add_argument("--compare", metavar="BEFORE_PDF",
                    help="report numbers present in BEFORE but missing in this pdf")
    args = ap.parse_args()

    issues = check_footer(args.pdf)
    pages = sorted({i["page"] for i in issues})
    print(f"[footer] {len(issues)} intruding line(s) on {len(pages)} page(s)")
    for i in issues:
        print(f"   p{i['page']:>3} {i['zone']:<6} +{i['overlap_pt']:>5}pt  {i['text']}")

    rm = check_right_margin(args.pdf)
    worst = max((h["overflow_pt"] for h in rm), default=0)
    print(f"[margin] {len(rm)} page(s) overflow the right margin (worst +{worst}pt)")
    if rm:
        print("   pages: " + ", ".join(str(h["page"]) for h in rm))

    orph = check_orphan_headings(args.pdf)
    print(f"[orphans] {len(orph)} heading(s) stranded at a page bottom")
    for o in orph:
        print(f"   p{o['page']:>3} {o['text']}")

    if args.log:
        c = check_log(args.log)
        print("[compile] " + ", ".join(f"{k}={v}" for k, v in c.items()))

    if args.tex:
        h = check_headers(args.tex)
        print(f"[headers] {h['repeat_header']}/{h['longtables']} longtables repeat their header")
        for cap in h["missing"]:
            print(f"   no repeat: {cap}")

    if args.compare:
        lost = compare_numbers(args.compare, args.pdf)
        print(f"[numbers] {sum(lost.values())} numeric token(s) in BEFORE missing from AFTER")
        for tok, n in lost.most_common(40):
            print(f"   {tok!r} x{n}")


if __name__ == "__main__":
    main()
