"""Marketing and sales, ported from marketing.ts: friendly sans, a terracotta
accent on the tagline, heading markers, companies and bullets, with the summary
up top so results lead."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_business import BUSINESS_MACROS, is_summary, order_sections, render_business_sections

BODY = (
    r"""\documentclass[a4paper,11pt]{article}
\usepackage[top=0.55in, bottom=0.55in, left=0.65in, right=0.65in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
\setmainfont{Lato}[Extension=.ttf, UprightFont=*-Regular, BoldFont=*-Bold, ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]

\definecolor{accent}{HTML}{B8461B}
\definecolor{ink}{HTML}{22252A}
\definecolor{muted}{HTML}{646A73}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\parindent}{0pt}
\color{ink}
\titleformat{\section}{\vspace{-4pt}\color{accent}\bfseries\addfontfeatures{LetterSpace=6}}{\rule[-1.5pt]{3.5pt}{11pt}}{7pt}{\MakeUppercase}[\vspace{-5pt}]
\setlist{leftmargin=0.2in, itemsep=1pt, parsep=0pt, topsep=2pt, partopsep=0pt}
\renewcommand\labelitemi{{\color{accent}\small\textbullet}}
"""
    + BUSINESS_MACROS
    + r"""
\newcommand{\linksep}{\enspace{\color{accent}\textbullet}\enspace}
\newcommand{\expentry}[4]{\par\vspace{5pt}\ifnonempty{#2#4}{\textbf{#2}\hfill{\color{muted}\small #4}\par}\ifnonempty{#1#3}{{\color{accent}\bfseries #1}\ifnonempty{#3}{{\color{muted}\enspace\textbar\enspace #3}}\par}}
\newcommand{\eduentry}[5]{\par\vspace{5pt}\textbf{#1}\hfill{\color{muted}\small #5}\par\ifnonempty{#2#3#4}{\joinwith{#2}{\enspace\textbar\enspace}{#3}\hfill{\color{muted}\small #4}\par}}
\newcommand{\projentry}[4]{\par\vspace{5pt}\textbf{#1}\ifnonempty{#2}{{\color{muted}\enspace\textbar\enspace\textit{#2}}}\ifnonempty{#3}{{\color{accent}\enspace\textbar\enspace #3}}\hfill{\color{muted}\small #4}\par}
\newcommand{\listentry}[3]{\par\vspace{2pt}\textbf{#1}\ifnonempty{#2}{\enspace{\color{muted}#2}}\hfill{\color{muted}\small #3}\par}
\newcommand{\skillline}[2]{\par\vspace{2pt}\ifnonempty{#1}{\textbf{#1}: }#2\par}
\newcommand{\summarytext}[1]{\par\vspace{3pt}#1\par}
\newcommand{\linkline}[1]{\par\vspace{3pt}{\color{accent}#1}\par}

\begin{document}
{\fontsize{28pt}{32pt}\selectfont\bfseries ${name}}${nameGap}\par\vspace{5pt}
${headline}
{\small\color{muted} ${contacts}}\par
\vspace{4pt}

${sections}
\end{document}
"""
)


def render_marketing(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections

    def rank(s):
        return 0 if is_summary(s) else 1

    ordered = order_sections(sections, rank)
    headline = (
        r"{\large\color{accent} " + tex(basics.headline) + r"}\par\vspace{4pt}"
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
