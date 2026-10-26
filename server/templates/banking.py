"""The dense one-page Wall Street layout, ported from banking.ts: Times-style
serif, firm names in bold with locations and dates flush right, uppercase ruled
headings and tight spacing. Education leads for students."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_business import (
    BUSINESS_MACROS,
    RUPEE_FALLBACK,
    is_summary,
    leads_with_education,
    order_sections,
    render_business_sections,
)

BODY = (
    r"""\documentclass[a4paper,10pt]{article}
\usepackage[top=0.45in, bottom=0.45in, left=0.55in, right=0.55in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
\setmainfont{texgyretermes}[Extension=.otf, UprightFont=*-regular, BoldFont=*-bold, ItalicFont=*-italic, BoldItalicFont=*-bolditalic]
"""
    + RUPEE_FALLBACK
    + r"""

\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\parindent}{0pt}
\titleformat{\section}{\vspace{-5pt}\bfseries\small}{}{0em}{\MakeUppercase}[\vspace{-1pt}{\titlerule[0.6pt]}\vspace{-5pt}]
\setlist{leftmargin=0.17in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt}
\renewcommand\labelitemi{\raisebox{0.1ex}{\scriptsize\textbullet}}
"""
    + BUSINESS_MACROS
    + r"""
\newcommand{\linksep}{\enspace|\enspace}
\newcommand{\expentry}[4]{\par\vspace{3pt}\ifnonempty{#1#3}{\textbf{#1}\hfill #3\par}\ifnonempty{#2#4}{\textit{#2}\hfill #4\par}}
\newcommand{\eduentry}[5]{\par\vspace{3pt}\textbf{#1}\hfill #4\par\ifnonempty{#2#3#5}{\joinwith{#2}{; }{#3}\hfill #5\par}}
\newcommand{\projentry}[4]{\par\vspace{3pt}\textbf{#1}\ifnonempty{#2}{\enspace\textit{#2}}\ifnonempty{#3}{\linksep #3}\hfill #4\par}
\newcommand{\listentry}[3]{\par\vspace{1pt}\textbf{#1}\ifnonempty{#2}{, #2}\hfill #3\par}
\newcommand{\skillline}[2]{\par\vspace{1pt}\ifnonempty{#1}{\textbf{#1}: }#2\par}
\newcommand{\summarytext}[1]{\par\vspace{2pt}#1\par}
\newcommand{\linkline}[1]{\par\vspace{2pt}#1\par}

\begin{document}
{\centering
  {\LARGE\bfseries ${name}}${nameGap}\par\vspace{2pt}
  ${headline}
  {\small ${contacts}}\par
}

${sections}
\end{document}
"""
)


def render_banking(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    early = leads_with_education(sections)

    def rank(s):
        if is_summary(s):
            return 0
        return 1 if (early and s.type == "education") else 2

    ordered = order_sections(sections, rank)
    headline = r"{\small " + tex(basics.headline) + r"}\par\vspace{1pt}" if basics.headline else ""
    contacts = "\\linksep ".join(contact_parts(basics, layout.links if layout else None))
    return apply_layout(
        sub(
            BODY,
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            contacts=contacts,
            sections=render_business_sections(ordered),
        ),
        layout,
    )
