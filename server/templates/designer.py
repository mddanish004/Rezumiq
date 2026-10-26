"""Two-column layout for UI/UX and product designers, ported from designer.ts:
a light display name, a narrow sidebar for contact, skills, education and short
lists, and the main column for experience and work. paracol lets both columns
run onto a second page."""

import re

from resumes.content import plain_text

from .classic_body import render_sections
from .latex import (
    contact_parts,
    date_range,
    display_url,
    gap,
    join_non_empty,
    sub,
    tex,
    tex_rich,
    tex_url,
    visible_content,
    with_gap,
)
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_tech import bullets, bundle_font

PREAMBLE = (
    r"""\documentclass[a4paper,10pt]{article}
\usepackage[a4paper,top=0.6in,bottom=0.6in,left=0.6in,right=0.6in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{paracol}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
"""
    + bundle_font("FiraSans")
    + r"""
\newfontface\light{FiraSans-Light.otf}
\newfontface\caps{FiraSans-SemiBold.otf}[LetterSpace=10]

\definecolor{ink}{HTML}{1C1917}
\definecolor{accent}{HTML}{C2410C}
\definecolor{muted}{HTML}{78716C}
\definecolor{hairline}{HTML}{E7E5E4}
\color{ink}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}
\titleformat{\section}{\color{accent}\footnotesize\caps}{}{0em}{\MakeUppercase}
\titlespacing*{\section}{0pt}{*3}{*1.4}
\columnratio{0.29}
\setlength{\columnsep}{20pt}
\setlength{\columnseprule}{0.4pt}
\colseprulecolor{hairline}

\newcommand{\resumeItem}[1]{\item{#1}}
\newcommand{\resumeSubheading}[4]{
  \item
  \begin{tabular*}{\linewidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \small\textcolor{muted}{#2} \\
    #3 & \small\textcolor{muted}{#4} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{\linewidth}{l@{\extracolsep{\fill}}r}
    #1 & \small\textcolor{muted}{#2} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt, label={}, topsep=0pt, parsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.9em, label={\textcolor{accent}{\textbullet}}, topsep=1pt, parsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
\newcommand{\sideEntry}[1]{\par\vspace{5pt}{\small #1}\par}
"""
)


def breakable(url: str) -> str:
    return re.sub(r"/", r"/\\hspace{0pt}", tex(display_url(url)))


def side_link(url: str, text: str) -> str:
    return "\\href{" + tex_url(url) + "}{" + text + "}"


def lines(parts: list[str | None]) -> str:
    return join_non_empty(parts, "\\\\\n")


def in_sidebar(s) -> bool:
    if s.type in ("skills", "links", "education"):
        return True
    return s.type == "list" and all(not e.bullets for e in s.entries)


def sidebar_section(s) -> str:
    if s.type == "skills":
        entries = [
            lines([f"\\textbf{{{tex(g.name)}}}", tex(", ".join(g.items))])
            for g in s.groups
            if g.items
        ]
    elif s.type == "links":
        entries = [
            lines([f"\\textbf{{{tex(l.label)}}}", side_link(l.url, breakable(l.url))])
            for l in s.links
        ]
    elif s.type == "education":
        entries = []
        for e in s.entries:
            entries.append(
                "\n".join(
                    part
                    for part in [
                        lines(
                            [
                                "\\textbf{" + tex(e.institution) + "}",
                                tex(join_non_empty([e.degree, e.field], ", ")),
                                tex(e.score),
                                "\\textcolor{muted}{"
                                + join_non_empty(
                                    [date_range(e.start, e.end), tex(e.location)], ", "
                                )
                                + "}",
                            ]
                        ),
                        bullets(e.bullets) + gap(e),
                    ]
                    if part
                )
            )
    elif s.type == "list":
        entries = []
        for e in s.entries:
            entries.append(
                lines(
                    [
                        side_link(e.url, "\\textbf{" + tex(plain_text(e.title)) + "}")
                        if e.url
                        else f"\\textbf{{{tex_rich(e.title)}}}",
                        tex_rich(e.subtitle),
                        f"\\textcolor{{muted}}{{{tex(e.date)}}}" if e.date else None,
                    ]
                )
                + gap(e)
            )
    else:
        entries = []
    entries = [e for e in entries if e]
    if not entries:
        return ""
    return f"\\section{{{tex(s.title)}}}\n" + "\n".join(f"\\sideEntry{{{e}}}" for e in entries)


def contact(basics, layout: ResumeLayout | None) -> str:
    parts = contact_parts(basics, layout.links if layout else None)
    if not parts:
        return ""
    return "\\section{Contact}\n" + "\n".join(f"\\sideEntry{{{p}}}" for p in parts)


def render_designer(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    side = [
        contact(basics, layout),
        *[with_gap(sidebar_section(s), s) for s in sections if in_sidebar(s)],
    ]
    side = [part for part in side if part]
    main = render_sections([s for s in sections if not in_sidebar(s)])
    headline = (
        r"{\color{accent}\caps\small\MakeUppercase{" + tex(basics.headline) + r"}}\par"
        if basics.headline
        else ""
    )
    return apply_layout(
        sub(
            PREAMBLE
            + r"""
\begin{document}
{\fontsize{34pt}{38pt}\selectfont\light ${name}}${nameGap}\par\vspace{6pt}
${headline}
\vspace{10pt}
\begin{paracol}{2}
${side}
\switchcolumn
${main}
\end{paracol}
\end{document}
""",
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            side="\n\n".join(side),
            main=main,
        ),
        layout,
    )
