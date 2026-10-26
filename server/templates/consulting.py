"""Clean one-page consulting layout, ported from consulting.ts: humanist sans,
letterspaced headings under a heavy rule, firm and dates on one line with the
role below, square bullets for impact-first results. Education leads early on."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_business import (
    BUSINESS_MACROS,
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
\setmainfont{SourceSansPro}[Extension=.otf, UprightFont=*-Regular, BoldFont=*-Semibold, ItalicFont=*-RegularIt, BoldItalicFont=*-SemiboldIt]

\definecolor{ink}{HTML}{1A1A1A}
\definecolor{muted}{HTML}{5B6168}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\parindent}{0pt}
\color{ink}
\titleformat{\section}{\vspace{-6pt}{\titlerule[0.9pt]}\vspace{2pt}\bfseries\small\addfontfeatures{LetterSpace=10}}{}{0em}{\MakeUppercase}[\vspace{-6pt}]
\setlist{leftmargin=0.18in, itemsep=1pt, parsep=0pt, topsep=1pt, partopsep=0pt}
\renewcommand\labelitemi{\raisebox{0.3ex}{\rule{3.2pt}{3.2pt}}}
"""
    + BUSINESS_MACROS
    + r"""
\newcommand{\linksep}{\enspace{\color{muted}/}\enspace}
\newcommand{\expentry}[4]{\par\vspace{4pt}\ifnonempty{#1#3#4}{\textbf{#1}\ifnonempty{#3}{\enspace{\color{muted}#3}}\hfill #4\par}\ifnonempty{#2}{\textit{#2}\par}}
\newcommand{\eduentry}[5]{\par\vspace{4pt}\textbf{#1}\ifnonempty{#4}{\enspace{\color{muted}#4}}\hfill #5\par\ifnonempty{#2#3}{\joinwith{\textit{#2}}{; }{#3}\par}}
\newcommand{\projentry}[4]{\par\vspace{4pt}\textbf{#1}\ifnonempty{#2}{\enspace{\color{muted}#2}}\ifnonempty{#3}{\linksep #3}\hfill #4\par}
\newcommand{\listentry}[3]{\par\vspace{2pt}\textbf{#1}\ifnonempty{#2}{: #2}\hfill #3\par}
\newcommand{\skillline}[2]{\par\vspace{2pt}\ifnonempty{#1}{\textbf{#1}: }#2\par}
\newcommand{\summarytext}[1]{\par\vspace{2pt}#1\par}
\newcommand{\linkline}[1]{\par\vspace{2pt}#1\par}

\begin{document}
{\centering
  {\fontsize{20pt}{24pt}\selectfont\bfseries\addfontfeatures{LetterSpace=12}\MakeUppercase{${name}}}${nameGap}\par\vspace{4pt}
  ${headline}
  {\small\color{muted} ${contacts}}\par
}
\vspace{2pt}

${sections}
\end{document}
"""
)


def render_consulting(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    early = leads_with_education(sections)

    def rank(s):
        if is_summary(s):
            return 0
        return 1 if (early and s.type == "education") else 2

    ordered = order_sections(sections, rank)
    headline = "{" + tex(basics.headline) + r"}\par\vspace{1pt}" if basics.headline else ""
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
