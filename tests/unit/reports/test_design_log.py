from osdagbridge.core.reports.design_log import design_log


def test_decoration_lines_are_dropped():
    tex = design_log([
        "[2026-01-01 10:00:00] ============================================================",
        "[2026-01-01 10:00:01]   STAGE 1 COMPLETE [10%] : INPUT VALIDATION",
        "[2026-01-01 10:00:02] --------------------------------------------- A N A L Y S I S   C O M P L E T E",
    ])
    assert "====" not in tex and "----" not in tex
    assert "STAGE 1 COMPLETE" in tex
    assert "A N A L Y S I S" in tex
    assert tex.count("\\hline") >= 3          # header rules + two surviving rows


def test_empty_log_says_so():
    assert "No design log entries" in design_log([])
    assert "No design log entries" in design_log(["[2026-01-01 10:00:00] =========="])
