"""Dense sans layout for data scientists and analysts, ported from
data-analyst.ts: accent-bar headings, a two-column skills block that reads like
a key and value list, and muted metadata so the numbers in bullets stand out."""

from .latex import contact_parts, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_tech import bundle_font, render_body

PREAMBLE = (
    r"""\documentclass[a4paper,10pt]{article}
\usepackage[a4paper,top=0.5in,bottom=0.5in,left=0.6in,right=0.6in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
"""
    + bundle_font("IBMPlexSans")
    + r"""
\newfontface\headingfont{IBMPlexSans-SemiBold.otf}[LetterSpace=6]

\definecolor{accent}{HTML}{1F5C99}
\definecolor{muted}{HTML}{5B6573}
\definecolor{hairline}{HTML}{C9D1DB}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}
\titleformat{\section}{\color{accent}\small\headingfont}{}{0em}{{\color{accent}\rule[-0.25ex]{3pt}{1.9ex}}\hspace{6pt}\MakeUppercase}[\vspace{1pt}{\color{hairline}\titlerule}]
\titlespacing*{\section}{0pt}{*2.4}{*1.4}

\newcommand{\resumeItem}[1]{\item{#1}}
\newcommand{\resumeSubheading}[4]{
  \item
  \begin{tabular*}{\linewidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \textcolor{muted}{#2} \\
    \textcolor{accent}{#3} & \textcolor{muted}{\small #4} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{\linewidth}{l@{\extracolsep{\fill}}r}
    #1 & \textcolor{muted}{#2} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt, label={}, topsep=0pt, parsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=1.1em, label={\textcolor{accent}{\textbullet}}, topsep=1pt, parsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
"""
)


def skills(s) -> str:
    groups = [group for group in s.groups if group.items]
    if not groups:
        return ""
    items = [f"  \\item[{{\\textbf{{{tex(g.name)}}}}}] {tex(', '.join(g.items))}" for g in groups]
    return (
        f"\\section{{{tex(s.title)}}}\n"
        "\\begin{itemize}[leftmargin=1.5in, labelwidth=1.4in, labelsep=0.1in, align=left, topsep=0pt, parsep=0pt]\n"
        + "\n".join(items)
        + "\n\\end{itemize}"
    )


def render_data_analyst(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections

    def custom(s):
        return skills(s) if s.type == "skills" else None

    body = render_body(sections, custom)
    headline = (
        rf"\hspace{{10pt}}{{\color{{accent}}\Large {tex(basics.headline)}}}"
        if basics.headline
        else ""
    )
    contacts = "\\hspace{4pt}{\\color{hairline}|}\\hspace{4pt}".join(
        contact_parts(basics, layout.links if layout else None)
    )
    return apply_layout(
        sub(
            PREAMBLE
            + r"""
\begin{document}
{\fontsize{22pt}{26pt}\selectfont\bfseries ${name}}${headline}${nameGap}\par\vspace{4pt}
{\small\color{muted} ${contacts}}\par

${body}
\end{document}
""",
            name=tex(basics.name),
            headline=headline,
            nameGap=name_gap(layout),
            contacts=contacts,
            body=body,
        ),
        layout,
    )
