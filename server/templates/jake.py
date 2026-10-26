"""The Jake's Resume variant most developers use, ported from jake.ts.

Based on Jake Gutierrez's resume template (MIT), adapted for XeTeX.
"""

from .classic_body import render_sections
from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .macros import SHARED_MACROS

BODY = (
    r"""\documentclass[a4paper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fancyhdr}
\usepackage{tabularx}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\titleformat{\section}{\vspace{-4pt}\scshape\raggedright\large}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]"""
    + SHARED_MACROS
    + r"""
\begin{document}
\begin{center}
  \textbf{\Huge \scshape ${name}}${nameGap} \\ \vspace{1pt}
  ${headline}
  \small ${contacts}
\end{center}

${sections}
\end{document}
"""
)


def render_jake(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    headline = r"\small " + tex(basics.headline) + r" \\ \vspace{1pt}" if basics.headline else ""
    contacts = " $|$ ".join(contact_parts(basics, layout.links if layout else None))
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
