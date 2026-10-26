"""The Jake's Resume variant popular with Indian developers, ported from
developer.ts: small-caps name, icon header, tight margins, company above a bold
role, projects with Live and Github links. Based on Jake Gutierrez's template
(MIT), adapted for XeTeX."""

from .latex import (
    contact_parts,
    date_range,
    display_url,
    fits_one_line,
    gap,
    tex,
    tex_rich,
    tex_url,
    visible_content,
    with_gap,
)
from .layout import ResumeLayout, apply_layout, name_gap

PREAMBLE = r"""\documentclass[letterpaper,10pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{fontawesome5}
\usepackage{accsupp}

\addtolength{\oddsidemargin}{-0.7in}
\addtolength{\evensidemargin}{-0.7in}
\addtolength{\textwidth}{1.4in}
\addtolength{\topmargin}{-0.7in}
\addtolength{\textheight}{1.4in}

\titleformat{\section}{\vspace{-4pt}\scshape\raggedright\large\bfseries}{}{0em}{}[\color{black}\titlerule \vspace{-4pt}]

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
  \begin{tabular*}{1.0\textwidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & \textbf{\small #2} \\
    \textit{\small#3} & \textit{\small #4} \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{1.001\textwidth}{l@{\extracolsep{\fill}}r}
    \small#1 & \textbf{\small #2} \\
  \end{tabular*}\vspace{-7pt}
}
\renewcommand\labelitemi{$\vcenter{\hbox{\tiny$\bullet$}}$}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
"""


def header(basics, layout: ResumeLayout | None) -> str:
    return " ~\n  ".join(contact_parts(basics, layout.links if layout else None))


def bullets(items, lead: list[str] | None = None) -> str:
    if not items and not lead:
        return ""
    lead = lead or []
    return "\n".join(
        [
            "\\resumeItemListStart",
            *[f"  \\item[] \\small{{\\emph{{{line}}}}}" for line in lead],
            *[f"  \\resumeItem{{{tex_rich(item.text)}}}" for item in items],
            "\\resumeItemListEnd",
        ]
    )


def link(url: str, label: str) -> str:
    return "\\href{" + tex_url(url) + "}{\\underline{" + tex(label) + "}}"


def section(title: str, body: str) -> str:
    return f"\\section{{{tex(title)}}}\n{body}"


def render_section(s) -> str:
    kind = s.type
    if kind == "skills":
        lines = " \\\\\n".join(
            "    \\textbf{" + tex(group.name) + "}{: " + tex(", ".join(group.items)) + "}"
            for group in s.groups
            if group.items
        )
        if not lines:
            return ""
        return section(
            s.title,
            "\\begin{itemize}[leftmargin=0.15in, label={}]\n  \\item \\small{\n"
            + lines
            + "\n  }\n\\end{itemize}",
        )
    if kind == "summary":
        if not s.text:
            return ""
        return section(
            s.title,
            "\\begin{itemize}[leftmargin=0.15in, label={}]\n  \\item \\small{"
            + tex_rich(s.text)
            + "}\n\\end{itemize}",
        )
    if kind == "links":
        if not s.links:
            return ""
        return section(
            s.title,
            "\\begin{itemize}[leftmargin=0.15in, label={}]\n  \\item \\small{\n    "
            + ", ".join(
                f"\\mbox{{{tex(l.label)}: {link(l.url, display_url(l.url))}}}" for l in s.links
            )
            + "\n  }\n\\end{itemize}",
        )
    if kind == "experience":
        if not s.entries:
            return ""
        entries = []
        for e in s.entries:
            entries.append(
                "\\resumeSubheading\n  {"
                + tex(e.organization)
                + "}{"
                + date_range(e.start, e.end)
                + "}\n  {\\textbf{"
                + tex(e.role)
                + "}}{"
                + tex(e.location)
                + "}\n"
                + bullets(e.bullets)
                + gap(e)
            )
        return section(
            s.title,
            "\\resumeSubHeadingListStart\n"
            + "\n\\vspace{-5pt}\n".join(entries)
            + "\n\\resumeSubHeadingListEnd",
        )
    if kind == "education":
        if not s.entries:
            return ""
        entries = []
        for e in s.entries:
            degree = [
                tex(e.degree) if e.degree else "",
                f"\\textbf{{{tex(e.field)}}}" if e.field else "",
            ]
            degree = " in ".join(part for part in degree if part)
            subtitle = " ".join(
                part for part in [degree, f"({tex(e.score)})" if e.score else ""] if part
            )
            entries.append(
                "\\resumeSubheading\n  {"
                + tex(e.institution)
                + "}{"
                + date_range(e.start, e.end)
                + "}\n  {"
                + subtitle
                + "}{"
                + tex(e.location)
                + "}\n"
                + bullets(e.bullets)
                + gap(e)
            )
        return section(
            s.title,
            "\\resumeSubHeadingListStart\n" + "\n".join(entries) + "\n\\resumeSubHeadingListEnd",
        )
    if kind == "projects":
        if not s.entries:
            return ""
        entries = []
        for e in s.entries:
            title = (
                "\\href{" + tex_url(e.url) + "}{\\textbf{" + tex(e.name) + "}}"
                if e.url
                else f"\\textbf{{{tex(e.name)}}}"
            )
            techs = ", ".join(e.technologies)
            inline = fits_one_line(
                [e.name, techs, *[l.label for l in e.links]], bool(e.start or e.end)
            )
            bold = ", ".join(f"\\textbf{{{tex(t)}}}" for t in e.technologies)
            tech = f" $|$ \\emph{{{bold}}}" if (techs and inline) else ""
            links = "".join(f" $|$ {link(l.url, l.label)}" for l in e.links)
            entries.append(
                "\\resumeProjectHeading\n  {"
                + title
                + tech
                + links
                + "}{"
                + date_range(e.start, e.end)
                + "}\n\\vspace{-10pt}\n"
                + bullets(e.bullets, [bold] if (techs and not inline) else [])
                + gap(e)
            )
        return section(
            s.title,
            "\\resumeSubHeadingListStart\n"
            + "\n\\vspace{-13pt}\n".join(entries)
            + "\n\\resumeSubHeadingListEnd",
        )
    if kind == "list":
        if not s.entries:
            return ""
        if all(not e.bullets for e in s.entries):
            from .latex import compact_list

            return section(s.title, compact_list(s.entries))
        entries = []
        for e in s.entries:
            title = link(e.url, e.title) if e.url else f"\\textbf{{{tex(e.title)}}}"
            subtitle = f" $|$ \\emph{{{tex(e.subtitle)}}}" if e.subtitle else ""
            entries.append(
                "\\resumeProjectHeading\n  {"
                + title
                + subtitle
                + "}{"
                + tex(e.date)
                + "}\n"
                + bullets(e.bullets)
                + gap(e)
            )
        return section(
            s.title,
            "\\resumeSubHeadingListStart\n"
            + "\n\\vspace{-13pt}\n".join(entries)
            + "\n\\resumeSubHeadingListEnd",
        )
    return ""


def render_developer(content, layout: ResumeLayout | None = None) -> str:
    visible = visible_content(content)
    basics, sections = visible.basics, visible.sections
    lines = [f"\\leavevmode{{\\Huge \\scshape {tex(basics.name)}}}{name_gap(layout)}"]
    if basics.headline:
        lines.append(f"\\small {tex(basics.headline)}")
    contacts = header(basics, layout)
    if contacts:
        lines.append(contacts)
    return apply_layout(
        PREAMBLE
        + "\n\\begin{document}\n\\begin{center}\n  "
        + " \\\\ \\vspace{1pt}\n  ".join(lines)
        + "\n  \\vspace{-3pt}\n\\end{center}\n\n"
        + "\n\n".join(text for text in (with_gap(render_section(s), s) for s in sections) if text)
        + "\n\n\\end{document}\n",
        layout,
    )
