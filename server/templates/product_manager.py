"""Roomy, outcome-first layout for product managers, ported from
product-manager.ts: a heavy accent rule under the header, sentence-case
headings, company names in the accent color and square bullets."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_tech import bundle_font, render_body

PREAMBLE = (
    r"""\documentclass[a4paper,11pt]{article}
\usepackage[a4paper,top=0.6in,bottom=0.6in,left=0.75in,right=0.75in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
"""
    + bundle_font("Inter")
    + r"""
\newfontface\semibold{Inter-SemiBold.otf}

\definecolor{ink}{HTML}{111827}
\definecolor{accent}{HTML}{15803D}
\definecolor{muted}{HTML}{6B7280}
\definecolor{hairline}{HTML}{D1D5DB}
\color{ink}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}
\titleformat{\section}{\large\semibold}{}{0em}{}[\vspace{2pt}{\color{hairline}\titlerule}]
\titlespacing*{\section}{0pt}{*3.2}{*1.6}

\newcommand{\resumeItem}[1]{\item{\small #1}}
\newcommand{\resumeSubheading}[4]{
  \item
  \begin{tabular*}{\linewidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \small\textcolor{muted}{#2} \\
    \semibold\textcolor{accent}{#3} & \small\textcolor{muted}{#4} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{\linewidth}{l@{\extracolsep{\fill}}r}
    #1 & \small\textcolor{muted}{#2} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt, label={}, topsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=1.1em, label={\textcolor{accent}{\rule[0.3ex]{3.5pt}{3.5pt}}}, topsep=2pt, parsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
"""
)


def render_product_manager(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    headline = (
        r"{\large\semibold\color{accent} " + tex(basics.headline) + r"}\par\vspace{3pt}"
        if basics.headline
        else ""
    )
    contacts = "\\hspace{10pt}".join(contact_parts(basics, layout.links if layout else None))
    return apply_layout(
        sub(
            PREAMBLE
            + r"""
\begin{document}
{\fontsize{26pt}{30pt}\selectfont\bfseries ${name}}${nameGap}\par\vspace{4pt}
${headline}
{\small\color{muted} ${contacts}}\par
\vspace{6pt}{\color{accent}\rule{\linewidth}{2.5pt}}

${sections}
\end{document}
""",
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            contacts=contacts,
            sections=render_body(sections),
        ),
        layout,
    )
