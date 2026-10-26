"""Campus placement format, ported from campus.ts: education first as a table
of degree, institution, score and year, shaded section bars and a dense single
column for projects, internships and achievements."""

from .latex import contact_parts, date_range, join_non_empty, sub, tex, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_tech import bullets, render_body

PREAMBLE = r"""\documentclass[a4paper,10pt]{article}
\usepackage[a4paper,top=0.45in,bottom=0.45in,left=0.5in,right=0.5in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
\setmainfont{NotoSerif}[Extension=.ttf, UprightFont=*-Regular, BoldFont=*-Bold, ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]

\definecolor{shade}{HTML}{E5E7EB}
\definecolor{muted}{HTML}{4B5563}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}
\newcommand{\sectionbar}[1]{\colorbox{shade}{\parbox{\dimexpr\linewidth-2\fboxsep}{\strut\MakeUppercase{#1}}}}
\titleformat{\section}{\normalsize\bfseries}{}{0em}{\sectionbar}
\titlespacing*{\section}{0pt}{*2}{*1}
\newcolumntype{L}{>{\raggedright\arraybackslash}X}

\newcommand{\resumeItem}[1]{\item{#1}}
\newcommand{\resumeSubheading}[4]{
  \item
  \begin{tabular*}{\linewidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \textbf{\small #2} \\
    \textit{\small #3} & \textit{\small #4} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{\linewidth}{l@{\extracolsep{\fill}}r}
    #1 & \textbf{\small #2} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt, label={}, topsep=0pt, parsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=1.1em, label={\textbullet}, topsep=0pt, parsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
"""

GAP_COL = r"@{\hspace{8pt}}"


def education(s) -> str:
    if not s.entries:
        return ""
    rows = []
    for e in s.entries:
        row = (
            tex(join_non_empty([e.degree, e.field], ", "))
            + " & "
            + tex(join_non_empty([e.institution, e.location], ", "))
            + " & "
            + tex(e.score)
            + " & "
            + date_range(e.start, e.end)
            + r" \\"
        )
        listing = bullets(e.bullets)
        space = f"\n\\addlinespace[{e.space_after}pt]" if e.space_after else ""
        rows.append(
            (
                row + "\n\\multicolumn{4}{@{}p{\\linewidth}@{}}{" + listing + r" \\"
                if listing
                else row
            )
            + space
        )
    return (
        f"\\section{{{tex(s.title)}}}\n"
        "{\\small\\begin{tabularx}{\\linewidth}{@{}L"
        + GAP_COL
        + "L"
        + GAP_COL
        + "l"
        + GAP_COL
        + "r@{}}\n"
        "\\toprule\n"
        "\\textbf{Degree} & \\textbf{Institution} & \\textbf{Score} & \\textbf{Year} \\\\\n"
        "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabularx}}"
    )


def render_campus(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    ordered = [s for s in sections if s.type == "education"] + [
        s for s in sections if s.type != "education"
    ]

    def custom(s):
        return education(s) if s.type == "education" else None

    body = render_body(ordered, custom)
    contacts = contact_parts(basics, layout.links if layout else None)
    contact_lines = [
        " \\textbar{} ".join(line) for line in (contacts[0:2], contacts[2:4], contacts[4:]) if line
    ]
    headline = "{\\small " + tex(basics.headline) + "}" if basics.headline else ""
    return apply_layout(
        sub(
            PREAMBLE
            + r"""
\begin{document}
\begin{minipage}[t]{0.5\linewidth}
  {\LARGE\bfseries ${name}}${nameGap}\par\vspace{2pt}
  ${headline}
\end{minipage}%
\begin{minipage}[t]{0.5\linewidth}
  \raggedleft\small
  ${contactLines}
\end{minipage}

${body}
\end{document}
""",
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            contactLines=" \\\\\n  ".join(contact_lines),
            body=body,
        ),
        layout,
    )
