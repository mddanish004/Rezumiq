"""Academic-leaning CV for ML engineers and researchers, ported from
ml-research.ts: serif type, small-caps headings with a leader rule, and
numbered, citation-style entries for list sections titled Publications."""

from .latex import contact_parts, gap, join_non_empty, sub, tex, tex_url, visible_content
from .layout import ResumeLayout, apply_layout, name_gap
from .shared_tech import bullets, bundle_font, is_publications, render_body

PREAMBLE = (
    r"""\documentclass[a4paper,11pt]{article}
\usepackage[a4paper,top=0.6in,bottom=0.6in,left=0.7in,right=0.7in]{geometry}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{accsupp}
\usepackage{fontspec}
"""
    + bundle_font("LibertinusSerif")
    + r"""

\definecolor{accent}{HTML}{7A1F2B}
\definecolor{muted}{HTML}{4A4A4A}
\pagestyle{empty}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}
\newcommand{\sectionfill}[1]{#1\hspace{0.5em}\leaders\hbox{\rule[0.55ex]{1pt}{0.5pt}}\hfill\kern0pt}
\titleformat{\section}{\large\scshape\color{accent}}{}{0em}{\sectionfill}
\titlespacing*{\section}{0pt}{*2.6}{*1.2}

\newcommand{\resumeItem}[1]{\item{#1}}
\newcommand{\resumeSubheading}[4]{
  \item
  \begin{tabular*}{\linewidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \textit{#2} \\
    \textit{#3} & \textcolor{muted}{\small #4} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{\linewidth}{l@{\extracolsep{\fill}}r}
    #1 & \textit{#2} \\
  \end{tabular*}\ignorespaces
}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0pt, label={}, topsep=0pt, parsep=0pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=1.4em, label={\textcolor{accent}{\small$\circ$}}, topsep=1pt, parsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}}
"""
)


def publications(s) -> str:
    if not s.entries:
        return ""
    items = []
    for e in s.entries:
        title = (
            "\\href{" + tex_url(e.url) + "}{\\textbf{" + tex(e.title) + "}}"
            if e.url
            else f"\\textbf{{{tex(e.title)}}}"
        )
        cite = join_non_empty(
            [title, "{\\textit{" + tex(e.subtitle) + "}}" if e.subtitle else None, tex(e.date)],
            ". ",
        )
        listing = bullets(e.bullets) + gap(e)
        items.append(f"\\item {cite}.")
        if listing:
            items.append(listing)
    return (
        f"\\section{{{tex(s.title)}}}\n"
        "\\begin{enumerate}[label={\\textcolor{accent}{[\\arabic*]}}, leftmargin=2.2em, topsep=0pt, parsep=0pt, itemsep=2pt]\n"
        + "\n".join(items)
        + "\n\\end{enumerate}"
    )


def render_ml_research(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections

    def custom(s):
        return publications(s) if is_publications(s) else None

    body = render_body(sections, custom)
    headline = (
        r"{\itshape " + tex(basics.headline) + r"}\par\vspace{2pt}" if basics.headline else ""
    )
    contacts = "\\enspace\\textperiodcentered\\enspace ".join(
        contact_parts(basics, layout.links if layout else None)
    )
    return apply_layout(
        sub(
            PREAMBLE
            + r"""
\begin{document}
{\fontsize{24pt}{28pt}\selectfont\scshape\color{accent} ${name}}${nameGap}\par\vspace{3pt}
${headline}
{\small ${contacts}}\par
\vspace{4pt}{\color{accent}\rule{\linewidth}{0.8pt}}

${body}
\end{document}
""",
            name=tex(basics.name),
            nameGap=name_gap(layout),
            headline=headline,
            contacts=contacts,
            body=body,
        ),
        layout,
    )
