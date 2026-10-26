"""Corporate finance, audit and CA/CFA candidates, ported from finance.ts:
Palatino-style serif, navy small-caps headings with a hairline to the margin,
credentials under the name and certifications right after the summary."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_business import (
    BUSINESS_MACROS,
    RUPEE_FALLBACK,
    is_certifications,
    is_summary,
    leads_with_education,
    order_sections,
    render_business_sections,
)

BODY = (
    r"""\documentclass[a4paper,11pt]{article}
\usepackage[top=0.5in, bottom=0.5in, left=0.6in, right=0.6in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
\setmainfont{texgyrepagella}[Extension=.otf, UprightFont=*-regular, BoldFont=*-bold, ItalicFont=*-italic, BoldItalicFont=*-bolditalic]
"""
    + RUPEE_FALLBACK
    + r"""

\definecolor{navy}{HTML}{1F3A5F}
\definecolor{muted}{HTML}{4A5560}
\definecolor{hairline}{HTML}{9AA7B4}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\parindent}{0pt}
\newcommand{\ruledtitle}[1]{#1\enspace{\color{hairline}\leaders\hrule height \dimexpr0.55ex+0.25pt\relax depth -0.55ex\hfill}}
\titleformat{\section}{\vspace{-5pt}\color{navy}\large\scshape}{}{0em}{\ruledtitle}[\vspace{-6pt}]
\setlist{leftmargin=0.2in, itemsep=1pt, parsep=0pt, topsep=1pt, partopsep=0pt}
\renewcommand\labelitemi{{\color{navy}\small\textbullet}}
"""
    + BUSINESS_MACROS
    + r"""
\newcommand{\linksep}{\enspace{\color{hairline}|}\enspace}
\newcommand{\expentry}[4]{\par\vspace{4pt}\ifnonempty{#2#4}{\textbf{#2}\hfill #4\par}\ifnonempty{#1#3}{{\color{navy}\itshape #1}\hfill{\color{muted}\small #3}\par}}
\newcommand{\eduentry}[5]{\par\vspace{4pt}\textbf{#1}\hfill #5\par\ifnonempty{#2#3#4}{{\itshape\joinwith{#2}{\enspace|\enspace}{#3}}\hfill{\color{muted}\small #4}\par}}
\newcommand{\projentry}[4]{\par\vspace{4pt}\textbf{#1}\ifnonempty{#2}{,\ \textit{#2}}\ifnonempty{#3}{\linksep #3}\hfill #4\par}
\newcommand{\listentry}[3]{\par\vspace{2pt}\textbf{#1}\ifnonempty{#2}{\linksep{\color{muted}#2}}\hfill #3\par}
\newcommand{\skillline}[2]{\par\vspace{2pt}\ifnonempty{#1}{\textbf{#1}: }#2\par}
\newcommand{\summarytext}[1]{\par\vspace{2pt}#1\par}
\newcommand{\linkline}[1]{\par\vspace{2pt}#1\par}

\begin{document}
{\color{navy}\fontsize{24pt}{28pt}\selectfont ${name}}${nameGap}\par\vspace{3pt}
${headline}
{\small\color{muted} ${contacts}}\par
\vspace{4pt}{\color{navy}\rule{\textwidth}{1.2pt}}\par

${sections}
\end{document}
"""
)


def render_finance(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    early = leads_with_education(sections)

    def rank(s):
        if is_summary(s):
            return 0
        if is_certifications(s):
            return 1
        return 2 if (early and s.type == "education") else 3

    ordered = order_sections(sections, rank)
    headline = (
        r"{\large\itshape\color{navy} " + tex(basics.headline) + r"}\par\vspace{2pt}"
        if basics.headline
        else ""
    )
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
