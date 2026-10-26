"""Section bodies shared by the classic templates, ported from classic-body.ts.

Each template defines these macros in its preamble:
\resumeSubheading{title}{right}{subtitle}{right-sub}, \resumeProjectHeading{left}{right},
\resumeItem{text}, \resumeSubHeadingListStart/End, \resumeItemListStart/End.
"""

from .latex import (
    compact_list,
    date_range,
    display_url,
    fits_one_line,
    gap,
    join_non_empty,
    tex,
    tex_rich,
    tex_url,
    with_gap,
)


def bullets(items: list, lead: list[str] | None = None) -> str:
    """`lead` lines go first without a bullet, like a project's tech list."""
    if not items and not lead:
        return ""
    lead = lead or []
    lines = [
        "\\resumeItemListStart",
        *[f"  \\item[] \\small{{\\emph{{{tex(line)}}}}}" for line in lead],
        *[f"  \\resumeItem{{{tex_rich(item.text)}}}" for item in items],
        "\\resumeItemListEnd",
    ]
    return "\n".join(lines)


def render_section_body(section) -> str:
    kind = section.type
    if kind == "experience":
        out = []
        for e in section.entries:
            out.append(
                "\\resumeSubheading{"
                + tex(e.role)
                + "}{"
                + date_range(e.start, e.end)
                + "}{"
                + tex(e.organization)
                + "}{"
                + tex(e.location)
                + "}"
            )
            out.append(bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "education":
        out = []
        for e in section.entries:
            degree = join_non_empty([e.degree, e.field], ", ")
            subtitle = join_non_empty(
                [tex(degree), tex(e.score) if e.score else None], r" \textbar{} "
            )
            out.append(
                "\\resumeSubheading{"
                + tex(e.institution)
                + "}{"
                + tex(e.location)
                + "}{"
                + subtitle
                + "}{"
                + date_range(e.start, e.end)
                + "}"
            )
            out.append(bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "projects":
        out = []
        for e in section.entries:
            if e.url:
                name = "\\href{" + tex_url(e.url) + "}{\\textbf{" + tex(e.name) + "}}"
            else:
                name = f"\\textbf{{{tex(e.name)}}}"
            techs = ", ".join(e.technologies)
            inline = fits_one_line(
                [e.name, techs, *[l.label for l in e.links]], bool(e.start or e.end)
            )
            tech = f" $|$ \\emph{{{tex(techs)}}}" if (techs and inline) else ""
            links = "".join(
                " $|$ \\href{" + tex_url(l.url) + "}{\\underline{" + tex(l.label) + "}}"
                for l in e.links
            )
            out.append(
                "\\resumeProjectHeading{"
                + name
                + tech
                + links
                + "}{"
                + date_range(e.start, e.end)
                + "}"
            )
            out.append(bullets(e.bullets, [techs] if (techs and not inline) else []) + gap(e))
        return "\n".join(out)
    if kind == "list":
        out = []
        for e in section.entries:
            if e.url:
                title = "\\href{" + tex_url(e.url) + "}{\\textbf{" + tex(e.title) + "}}"
            else:
                title = f"\\textbf{{{tex(e.title)}}}"
            subtitle = f" -- {tex(e.subtitle)}" if e.subtitle else ""
            out.append("\\resumeProjectHeading{" + title + subtitle + "}{" + tex(e.date) + "}")
            out.append(bullets(e.bullets) + gap(e))
        return "\n".join(out)
    return ""


def render_sections(sections) -> str:
    rendered: list[tuple[str, object]] = []
    for section in sections:
        if section.type == "skills":
            lines = " \\\n".join(
                "\\textbf{" + tex(group.name) + "}{: " + tex(", ".join(group.items)) + "}"
                for group in section.groups
                if group.items
            )
            body = (
                f"\\section{{{tex(section.title)}}}\n"
                "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
                "\\small{\\item{\n" + lines + "\n}}\n\\end{itemize}"
            )
        elif section.type == "summary":
            if not section.text:
                continue
            body = (
                f"\\section{{{tex(section.title)}}}\n"
                "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
                "\\small{\\item{" + tex_rich(section.text) + "}}\n"
                "\\end{itemize}"
            )
        elif section.type == "links":
            if not section.links:
                continue
            links = ", ".join(
                "\\mbox{"
                + tex(l.label)
                + ": \\href{"
                + tex_url(l.url)
                + "}{\\underline{"
                + tex(display_url(l.url))
                + "}}}"
                for l in section.links
            )
            body = (
                f"\\section{{{tex(section.title)}}}\n"
                "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
                "\\small{\\item{" + links + "}}\n"
                "\\end{itemize}"
            )
        elif not section.entries:
            continue
        elif section.type == "list" and all(not e.bullets for e in section.entries):
            body = f"\\section{{{tex(section.title)}}}\n{compact_list(section.entries)}"
        else:
            body = (
                f"\\section{{{tex(section.title)}}}\n\\resumeSubHeadingListStart\n"
                + render_section_body(section)
                + "\n\\resumeSubHeadingListEnd"
            )
        rendered.append((with_gap(body, section), section))
    return "\n\n".join(text for text, _ in rendered if text)
