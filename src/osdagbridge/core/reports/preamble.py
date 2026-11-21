"""LaTeX preamble and title/TOC blocks, generated from ``theme``.

No colour, length or font literal lives outside ``theme.py``; this module only
turns those constants into LaTeX.
"""
from __future__ import annotations

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
        "capskip": T.CAPTION_SKIP_PT, "tabcolsep": T.TABCOLSEP_PT,
        "stretch": T.ARRAYSTRETCH, "ltpre": T.LT_PRE_PT, "ltpost": T.LT_POST_PT,
        "rule": T.ARRAYRULE_PT, "extra": T.EXTRAROWHEIGHT_PT,
        "needspace_h": T.NEEDSPACE_HEADING_LINES, "needspace_t": T.NEEDSPACE_TABLE_LINES,
        "sdnote": T.SD_NOTE, "footer_left": T.FOOTER_LEFT, "footer_right": T.FOOTER_RIGHT,
        "rulew": T.RULE_THICKNESS_PT, "linestretch": T.LINE_STRETCH,
        "chapter_before": T.CHAPTER_BEFORE_PT, "emergency": T.EMERGENCY_STRETCH,
        "pn": pn, "jn": jn, "rd": rd, "rv": rv,
    }
    for key, val in values.items():
        tex = tex.replace("<<%s>>" % key, str(val))
    return tex


def toc_block() -> str:
    """Table of contents page (formatting is already in the preamble)."""
    return "\n\\newpage\n\\tableofcontents\n"
