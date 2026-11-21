# Report generator refactor: how to work with it

All report styling lives in `src/osdagbridge/core/reports/theme.py`. `preamble.py`, `latex_kit.py` (PyLaTeX tables and figures) and `charts.py` (matplotlib, object-oriented API only) read it. Chapter modules (`chap*.py`, `executive_summary.py`) describe content only; `tests/unit/reports/test_theme_lint.py` fails if one hard-codes a colour, length, rule or raw table.

Data for tables, verdicts and charts comes from `report_data.py` (`URRow`, vehicle and footway rows), so a table and its chart always agree.

## Run

```bash
pytest tests/unit -m "not slow"     # fast tests, no TeX needed
pytest tests/unit/reports           # adds 11 end-to-end builds (~3.5 min, needs pdflatex)

python scripts/report_dev/make_report.py --osi tests/fixtures/reports/S1_default.osi \
       --out out/S1 --save-snapshot out/S1.pkl
python scripts/report_dev/make_report.py --snapshot out/S1.pkl --out out/S1      # seconds
python scripts/report_dev/check_layout.py out/S1/report.pdf --tex out/S1/report.tex --log out/S1/report.log
```

Scenarios S1-S6 are in `tests/fixtures/reports/` (S2-S6 are generated from S1 by `scripts/report_dev/make_scenarios.py`). Headless PDFs show figure placeholders where the desktop app draws CAD views and analysis plots.

## Restyle

Edit `theme.py` only, e.g. `PRIMARY`, `TABLE_HEAD_FILL`, `MARGIN`, `UR_LIMIT`. Tables, header/footer rules and charts follow.
