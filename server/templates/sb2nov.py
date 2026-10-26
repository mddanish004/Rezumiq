"""Dense layout in the style of sb2nov/resume (MIT), ported from sb2nov.ts:
name left, contact details right."""

from .classic_body import render_sections
from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap_pt
from .macros import SHARED_MACROS

BODY = (
    r"""\documentclass[a4paper,10pt]{article}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{tabularx}

\pagestyle{empty}
\addtolength{\oddsidemargin}{-0.55in}
\addtolength{\evensidemargin}{-0.55in}
\addtolength{\textwidth}{1.1in}
\addtolength{\topmargin}{-.6in}
\addtolength{\textheight}{1.2in}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlist{itemsep=0pt, topsep=2pt}
\titleformat{\section}{\vspace{-6pt}\raggedright\large\bfseries}{}{0em}{}[\color{black}\titlerule \vspace{-6pt}]"""
    + SHARED_MACROS
    + r"""
\begin{document}
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{\LARGE ${name}} & ${contactsTop} \\${rowGap}
  ${headline} & ${contactsBottom} \\
\end{tabular*}

${sections}
\end{document}
"""
)


def render_sb2nov(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    contacts = contact_parts(basics, layout.links if layout else None)
    gap = name_gap_pt(layout)
    return apply_layout(
        sub(
            BODY,
            name=tex(basics.name),
            contactsTop=" $|$ ".join(contacts[:2]),
            rowGap=f"[{gap}pt]" if gap else "",
            headline=tex(basics.headline) if basics.headline else "",
            contactsBottom=" $|$ ".join(contacts[2:]),
            sections=render_sections(sections),
        ),
        layout,
    )
