"""Design log chapter: the stage-completion lines recorded during the design run."""
from typing import List

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports.latex_kit import Col


def design_log(log_entries: List[str]) -> str:
    entries = [str(e).strip() for e in (log_entries or []) if str(e).strip()]
    head = r"""
\chapter{Design Log}
\label{ch:design-log}

This chapter lists the stages the design run completed, in order, as recorded by the software.
"""
    if not entries:
        return head + "\n\\noindent No design log entries were recorded for this run.\n"
    table = K.data_table([Col("No.", 0.08, "c"), Col("Log entry", 0.92)],
                         [(str(i), e) for i, e in enumerate(entries, start=1)],
                         caption="Design Run Log", compact=True)
    return head + table
