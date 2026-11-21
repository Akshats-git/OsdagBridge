"""Design log chapter: the stage-completion lines recorded during the design run."""
import re
from typing import List

from osdagbridge.core.reports import latex_kit as K
from osdagbridge.core.reports.latex_kit import Col


_RULE_RUN = re.compile(r"[=\-_*~]{4,}")


def _clean(entry: str) -> str:
    """Drop console decoration (runs of = - _ *) that cannot wrap inside a table cell."""
    return re.sub(r"\s{2,}", " ", _RULE_RUN.sub(" ", entry)).strip()


def design_log(log_entries: List[str]) -> str:
    entries = []
    for e in log_entries or []:
        text = _clean(str(e))
        # a bare "[timestamp]" left over from a decoration-only line carries no information
        if re.sub(r"^\[[^\]]*\]\s*", "", text):
            entries.append(text)
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
