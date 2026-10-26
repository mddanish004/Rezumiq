"""Helpers for the field-specific templates (research, analyst, product,
designer, campus), ported from shared-tech.ts."""

import re

from resumes.content import ResumeSection

from .classic_body import render_sections
from .latex import display_url, tex, tex_rich, tex_url, with_gap


def bullets(items: list) -> str:
    if not items:
        return ""
    return "\n".join(
        [
            "\\resumeItemListStart",
            *[f"  \\resumeItem{{{tex_rich(item.text)}}}" for item in items],
            "\\resumeItemListEnd",
        ]
    )


def is_publications(section: ResumeSection) -> bool:
    return section.type == "list" and bool(
        re.search("publication|paper|preprint", section.title, re.IGNORECASE)
    )


def bundle_font(family: str, ext: str = ".otf") -> str:
    return (
        rf"\setmainfont{{{family}}}[Extension={ext}, "
        r"UprightFont=*-Regular, BoldFont=*-Bold, ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]"
    )


def _skills_block(section) -> str:
    lines = [
        "\\textbf{" + tex(g.name) + "}: " + tex(", ".join(g.items))
        for g in section.groups
        if g.items
    ]
    if not lines:
        return ""
    return f"\\section{{{tex(section.title)}}}\n" + " \\\\\n".join(lines) + "\\par"


def _links_block(section) -> str:
    if not section.links:
        return ""
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
    return f"\\section{{{tex(section.title)}}}\n{links}\\par"


def _summary_block(section) -> str:
    return (
        f"\\section{{{tex(section.title)}}}\n{tex_rich(section.text)}\\par" if section.text else ""
    )


def render_body(sections, custom=None) -> str:
    """Renders each section with the template's own renderer where it has one,
    else flush skills, links and summary blocks, else the shared classic body."""
    custom = custom or (lambda s: None)
    out = []
    for section in sections:
        own = custom(section)
        if own is None:
            if section.type == "skills":
                own = _skills_block(section)
            elif section.type == "links":
                own = _links_block(section)
            elif section.type == "summary":
                own = _summary_block(section)
        if own is None:
            own = render_sections([section])
        else:
            own = with_gap(own, section)
        if own:
            out.append(own)
    return "\n\n".join(out)
