"""Inspired by Awesome-CV, ported from modern.ts: sans-serif type,
accent-colored section titles, single column."""

from .classic_body import render_sections
from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .macros import SHARED_MACROS

BODY = (
    r"""\documentclass[a4paper,10.5pt]{article}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{tabularx}
\usepackage{fontspec}
\setmainfont{texgyreheros}[Extension=.otf, UprightFont=*-regular, BoldFont=*-bold, ItalicFont=*-italic, BoldItalicFont=*-bolditalic]

\definecolor{accent}{HTML}{0F766E}
\definecolor{muted}{HTML}{4B5563}
\pagestyle{empty}
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.55in}
\addtolength{\textheight}{1.1in}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\titleformat{\section}{\vspace{-4pt}\color{accent}\raggedright\large\bfseries}{}{0em}{\MakeUppercase}[{\color{accent}\titlerule} \vspace{-5pt}]"""
    + SHARED_MACROS
    + r"""
\begin{document}
\begin{center}
  \leavevmode{\fontsize{26pt}{30pt}\selectfont\bfseries ${name}}${nameGap} \\ \vspace{4pt}
  ${headline}
  \small {\color{muted} ${contacts}}
\end{center}

${sections}
\end{document}
"""
)


def render_modern(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    headline = (
        r"{\color{accent}\small " + tex(basics.headline) + r"} \\ \vspace{2pt}"
        if basics.headline
        else ""
    )
    contacts = " \\textbullet{} ".join(contact_parts(basics, layout.links if layout else None))
    return apply_layout(
        sub(
            BODY,
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            contacts=contacts,
            sections=render_sections(sections),
        ),
        layout,
    )
