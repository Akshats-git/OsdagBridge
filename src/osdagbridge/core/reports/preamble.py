"""LaTeX preamble and title/TOC blocks, generated from ``theme``.

No colour, length or font literal lives outside ``theme.py``; this module only
turns those constants into LaTeX.
"""
from __future__ import annotations

import re

from osdagbridge.core.reports import theme as T
from osdagbridge.core.reports.report_utils import _tex


def _colors() -> str:
    return "\n".join(
        r"\definecolor{%s}{HTML}{%s}" % (name, hexv) for name, hexv in T.LATEX_COLORS.items()
    )


def _unicode_declarations() -> str:
    return "\n".join(
        r"\DeclareUnicodeCharacter{%04X}{%s}" % (cp, repl) for cp, repl in T.UNICODE_MAP
    )


def _pdf_safe(text) -> str:
    """Plain text for PDF metadata: drop characters LaTeX would treat as markup."""
    return re.sub(r"[\\{}%#&_$^~]", "", str(text or "")).strip()


def build_preamble(project_name, job_number, report_date, report_version="Rev 0") -> str:
    pn, jn, rd, rv = (_tex(project_name), _tex(job_number), _tex(report_date), _tex(report_version))
    tex = r"""
\documentclass[<<pt>>pt,<<paper>>]{report}

% ---- Packages ---------------------------------------------------------------
\usepackage[<<paper>>, margin=<<margin>>, includeheadfoot, headheight=<<headheight>>, headsep=<<headsep>>, footskip=<<footskip>>]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{textcomp}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}
\usepackage{ragged2e}
<<microtype>>

% ---- PDF metadata (theme.PDF_*) ---------------------------------------------
\hypersetup{pdftitle={<<pdftitle>>}, pdfauthor={<<pdfauthor>>}, pdfsubject={<<pdfsubject>>}}

% ---- Characters pdflatex does not know by default (theme.UNICODE_MAP) -------
<<unicode>>

% ---- Colours (theme.LATEX_COLORS) -------------------------------------------
<<colors>>

% ---- Captions and numbering --------------------------------------------------
\captionsetup{labelfont=bf, justification=raggedright, singlelinecheck=false, format=plain,
              skip=<<capskip>>pt}
\setlength{\abovecaptionskip}{<<capskip>>pt}
\setlength{\belowcaptionskip}{<<capskip>>pt}
\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}

% ---- Tables (theme table style) ---------------------------------------------
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\setlength{\tabcolsep}{<<tabcolsep>>pt}
\renewcommand{\arraystretch}{<<stretch>>}
\setlength{\LTpre}{<<ltpre>>pt}
\setlength{\LTpost}{<<ltpost>>pt}
\setlength{\arrayrulewidth}{<<rule>>pt}
\setlength{\extrarowheight}{<<extra>>pt}
\newcommand{\urpass}[1]{\textcolor{urPass}{\textbf{#1}}}
\newcommand{\urfail}[1]{\textcolor{urFail}{\textbf{#1}}}
\newcommand{\urwarn}[1]{\textcolor{urWarn}{\textbf{#1}}}
\newcommand{\urna}[1]{\textcolor{urNA}{#1}}

% Keep a heading together with the lines that follow it
\newcommand{\keepwithnext}[1][<<needspace_h>>]{\Needspace*{#1\baselineskip}}
\let\osdagorigsection\section
\let\osdagorigsubsection\subsection
\let\osdagorigsubsubsection\subsubsection
\renewcommand{\section}{\keepwithnext\osdagorigsection}
\renewcommand{\subsection}{\keepwithnext\osdagorigsubsection}
\renewcommand{\subsubsection}{\keepwithnext\osdagorigsubsubsection}
\raggedbottom
\setlist{itemsep=<<itemsep>>pt, parsep=0pt, topsep=<<topsep>>pt}
\setlength{\emergencystretch}{<<emergency>>}

% ---- Header and footer ------------------------------------------------------
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\newcommand{\osdagfooterleft}{%
  \begin{tabular}[b]{@{}l@{}}%
    {\footnotesize\ifbool{hasSDonPage}{\textit{<<sdnote>>}}{\phantom{<<sdnote>>}}}\\%
    <<footer_left>>
  \end{tabular}}
\renewcommand{\headrulewidth}{<<rulew>>pt}
\renewcommand{\footrulewidth}{<<rulew>>pt}
\renewcommand{\headrule}{{\color{osdagGreen}\hrule width\headwidth height\headrulewidth}}
\renewcommand{\footrule}{{\color{osdagGreen}\hrule width\headwidth height\footrulewidth}}
\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{<<pn>> $|$ <<jn>>}
  \fancyhead[R]{<<rd>> $|$ <<rv>>}
  \fancyfoot[L]{\osdagfooterleft}
  \fancyfoot[R]{<<footer_right>>}
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{<<pn>> $|$ <<jn>>}
  \fancyhead[R]{<<rd>> $|$ <<rv>>}
  \fancyfoot[L]{\osdagfooterleft}
  \fancyfoot[R]{<<footer_right>>}
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{<<footer_left>>}
  \fancyfoot[R]{<<footer_right>>}
}
\pagestyle{main}
\setstretch{<<linestretch>>}

% ---- Chapter headings and TOC (defined once) --------------------------------
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{<<chapter_before>>pt}{10pt}
\setcounter{tocdepth}{2}
\titlecontents{chapter}[1.5em]{\normalfont\vspace{2pt}}{\contentslabel{1.5em}}{\hspace*{-1.5em}}{\hfill\contentspage}
\titlecontents{section}[3.8em]{\normalfont}{\contentslabel{2.3em}}{\hspace*{-2.3em}}{\hfill\contentspage}
\titlecontents{subsection}[7.0em]{\normalfont}{\contentslabel{3.2em}}{\hspace*{-3.2em}}{\hfill\contentspage}
\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}

% ---- Custom commands --------------------------------------------------------
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    values = {
        "pt": T.BASE_FONT_PT, "paper": T.PAPER, "margin": T.MARGIN,
        "headheight": T.HEADHEIGHT, "headsep": T.HEADSEP, "footskip": T.FOOTSKIP,
        "unicode": _unicode_declarations(), "colors": _colors(),
        "capskip": T.CAPTION_SKIP_PT, "itemsep": T.LIST_ITEMSEP_PT, "topsep": T.LIST_TOPSEP_PT, "tabcolsep": T.TABCOLSEP_PT,
        "stretch": T.ARRAYSTRETCH, "ltpre": T.LT_PRE_PT, "ltpost": T.LT_POST_PT,
        "rule": T.ARRAYRULE_PT, "extra": T.EXTRAROWHEIGHT_PT,
        "needspace_h": T.NEEDSPACE_HEADING_LINES,
        "sdnote": T.SD_NOTE, "footer_left": T.FOOTER_LEFT, "footer_right": T.FOOTER_RIGHT,
        "rulew": T.RULE_THICKNESS_PT, "linestretch": T.LINE_STRETCH,
        "chapter_before": T.CHAPTER_BEFORE_PT, "emergency": T.EMERGENCY_STRETCH,
        "microtype": r"\usepackage[protrusion=true,expansion=false]{microtype}" if T.MICROTYPE else "",
        "pdftitle": f"{_pdf_safe(project_name)} - {T.PDF_TITLE_SUFFIX}", "pdfauthor": T.PDF_AUTHOR,
        "pdfsubject": T.PDF_SUBJECT,
        "pn": pn, "jn": jn, "rd": rd, "rv": rv,
    }
    for key, val in values.items():
        tex = tex.replace("<<%s>>" % key, str(val))
    return tex


def toc_block() -> str:
    """Table of contents page (formatting is already in the preamble)."""
    return "\n\\newpage\n\\tableofcontents\n"


def _title_logos(osdag_logo, org_logo) -> str:
    """Logo row: Osdag left and organisation right, or the Osdag logo centred without one."""
    osdag = (r"\includegraphics[width=\linewidth,keepaspectratio]{%s}" % osdag_logo.replace("\\", "/")
             if osdag_logo else r"\textit{(Osdag Logo)}")
    if not org_logo:
        return (r"\begin{minipage}[c]{0.5\textwidth}" + "\n\\centering\n" + osdag + "\n"
                r"\end{minipage}" + "\n" + r"\\[%s]" % T.TITLE_LOGO_GAP + "\n")
    org = (r"\includegraphics[width=\linewidth,height=%s,keepaspectratio]{%s}"
           % (T.TITLE_ORG_LOGO_HEIGHT, org_logo.replace("\\", "/")))
    return (r"\noindent" + "\n"
            r"\begin{minipage}[c]{0.6\textwidth}" + "\n\\raggedright\n" + osdag + "\n" r"\end{minipage}%" + "\n"
            r"\hfill" + "\n"
            r"\begin{minipage}[c]{0.35\textwidth}" + "\n\\raggedleft\n" + org + "\n" r"\end{minipage}" + "\n"
            + r"\\[%s]" % T.TITLE_LOGO_GAP + "\n")


def title_page(meta, osdag_logo, org_logo) -> str:
    """Title page with the project details table; ``meta`` is a ``ReportMetadata``."""
    details = (
        ("Project Name", meta.project_name),
        ("Project Location", meta.project_location),
        ("Author / Designer", meta.designer),
        ("Reviewer", meta.reviewer),
        ("Organization", meta.company),
        ("Client Name and Organization", meta.client),
        ("Job Number", meta.job_number),
        ("Date", meta.report_date),
        ("Report Version", meta.subtitle or "Rev 0"),
    )
    rows = "\n".join(r"\hline" + "\n" + r"\textbf{%s} & %s \\" % (label, _tex(value)) for label, value in details)
    return (
        "\n" r"\begin{titlepage}" "\n"
        r"\thispagestyle{firstpage}" "\n"
        r"\centering" "\n"
        r"\vspace*{%s}" % T.TITLE_TOP_GAP + "\n"
        + _title_logos(osdag_logo, org_logo)
        + r"{\Huge \textbf{%s}}\\[%s]" % (T.TITLE_PRODUCT, T.TITLE_NAME_GAP) + "\n"
        + r"{\large %s}\\[%s]" % (T.TITLE_TAGLINE, T.TITLE_SUBTITLE_GAP) + "\n"
        + r"{\Large Design Report}\\[%s]" % T.TITLE_SUBTITLE_GAP + "\n"
        + r"\begin{tabular}{|L{%s}|L{%s}|}" % (T.TITLE_LABEL_WIDTH, T.TITLE_VALUE_WIDTH) + "\n"
        + rows + "\n" r"\hline" "\n"
        r"\end{tabular}" "\n"
        r"\end{titlepage}" "\n"
        # \begin{titlepage} resets the page counter; carry on from page 2 so the TOC is not "page 1" again
        r"\setcounter{page}{2}" "\n"
    )
