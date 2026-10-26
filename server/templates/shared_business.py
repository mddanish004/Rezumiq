r"""Section bodies shared by the business templates (banking, finance,
consulting, marketing, executive), ported from shared-business.ts.

Each template defines these macros in its preamble and lays them out its own way:
\expentry{organization}{role}{location}{dates}, \eduentry{institution}{degree}{score}{location}{dates},
\projentry{name}{technologies}{links}{dates}, \listentry{title}{subtitle}{date}, \skillline{group}{items},
\summarytext{text}, \linkline{links} with \linksep between links, and \competencies{group}{items}
with \compsep between items when the competencies option is on.
Bullets are a plain itemize, so the layout presets apply to them.
"""

import re
from dataclasses import dataclass
from math import inf, isfinite

from resumes.content import ResumeSection, plain_text

from .latex import date_range, display_url, gap, join_non_empty, tex, tex_rich, tex_url, with_gap

RUPEE_FALLBACK = (
    r"\usepackage{newunicodechar}"
    + "\n"
    + "\\newfontfamily\\rupeefont{EBGaramond}[Extension=.otf, UprightFont=*-Regular, BoldFont=*-Bold, "
    "ItalicFont=*-Italic, BoldItalicFont=*-BoldItalic]"
    + "\n"
    + r"\newunicodechar{₹}{{\rupeefont ₹}}"
)

BUSINESS_MACROS = (
    r"\newcommand{\ifnonempty}[2]{\if\relax\detokenize{#1}\relax\else#2\fi}"
    + "\n"
    + r"\newcommand{\joinwith}[3]{#1\ifnonempty{#1}{\ifnonempty{#3}{#2}}#3}"
)


def is_summary(s: ResumeSection) -> bool:
    return s.type == "summary" or (
        s.type == "list"
        and bool(re.search("summary|profile|about|objective", s.title, re.IGNORECASE))
    )


def is_certifications(s: ResumeSection) -> bool:
    return s.type == "list" and bool(
        re.search("certif|licen|credential|qualification|charter", s.title, re.IGNORECASE)
    )


def is_board(s: ResumeSection) -> bool:
    return s.type == "list" and bool(
        re.search("board|director|advis|governance", s.title, re.IGNORECASE)
    )


def _year(value: str | None) -> float | None:
    if value == "present":
        return inf
    return float(value[:4]) if value else None


def leads_with_education(sections: list[ResumeSection]) -> bool:
    graduated_values = []
    for s in sections:
        if s.type != "education":
            continue
        for e in s.entries:
            end_year = _year(e.end)
            start_year = _year(e.start)
            end = (
                end_year
                if end_year is not None
                else (start_year if start_year is not None else -inf)
            )
            graduated_values.append(end)
    graduated = max(graduated_values) if graduated_values else -inf
    if not isfinite(graduated):
        return True
    since = []
    for s in sections:
        if s.type != "experience":
            continue
        for e in s.entries:
            start = _year(e.start)
            if start is not None and start >= graduated:
                since.append(start)
    return len(since) < 2 and not any(start - graduated >= 3 for start in since)


def order_sections(sections: list[ResumeSection], rank) -> list[ResumeSection]:
    return sorted(sections, key=rank)


def _bullets(items: list) -> str:
    if not items:
        return ""
    return "\n".join(
        [
            "\\begin{itemize}",
            *[f"  \\item {tex_rich(item.text)}" for item in items],
            "\\end{itemize}",
        ]
    )


def _linked(url: str | None, label: str) -> str:
    return f"\\href{{{tex_url(url)}}}{{{tex(plain_text(label))}}}" if url else tex_rich(label)


@dataclass
class BusinessOptions:
    competencies: bool = False
    group_roles: bool = False


def _render_body(s: ResumeSection, options: BusinessOptions) -> str:
    if is_summary(s) and s.type == "list":
        out = []
        for e in s.entries:
            parts = []
            if e.title or e.subtitle:
                parts.append(
                    "\\summarytext{" + tex_rich(join_non_empty([e.title, e.subtitle], " ")) + "}"
                )
            listing = _bullets(e.bullets) + gap(e)
            if listing:
                parts.append(listing)
            out.append("\n".join(parts))
        return "\n".join(out)
    kind = s.type
    if kind == "experience":
        out = []
        for i, e in enumerate(s.entries):
            repeat = (
                options.group_roles and i > 0 and s.entries[i - 1].organization == e.organization
            )
            out.append(
                "\\expentry{"
                + ("" if repeat else tex(e.organization))
                + "}{"
                + tex(e.role)
                + "}{"
                + ("" if repeat else tex(e.location))
                + "}{"
                + date_range(e.start, e.end)
                + "}"
            )
            out.append(_bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "education":
        out = []
        for e in s.entries:
            out.append(
                "\\eduentry{"
                + tex(e.institution)
                + "}{"
                + tex(join_non_empty([e.degree, e.field], ", "))
                + "}{"
                + tex(e.score)
                + "}{"
                + tex(e.location)
                + "}{"
                + date_range(e.start, e.end)
                + "}"
            )
            out.append(_bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "projects":
        out = []
        for e in s.entries:
            out.append(
                "\\projentry{"
                + _linked(e.url, e.name)
                + "}{"
                + tex(", ".join(e.technologies))
                + "}{"
                + ", ".join(_linked(l.url, l.label) for l in e.links)
                + "}{"
                + date_range(e.start, e.end)
                + "}"
            )
            out.append(_bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "list":
        out = []
        for e in s.entries:
            out.append(
                "\\listentry{"
                + _linked(e.url, e.title)
                + "}{"
                + tex_rich(e.subtitle)
                + "}{"
                + tex(e.date)
                + "}"
            )
            out.append(_bullets(e.bullets) + gap(e))
        return "\n".join(out)
    if kind == "skills":
        groups = [g for g in s.groups if g.items]
        if options.competencies:
            out = []
            for g in groups:
                items = " \\compsep ".join("\\mbox{" + tex(item) + "}" for item in g.items)
                name = tex(g.name) if len(groups) > 1 else ""
                out.append(f"\\competencies{{{name}}}{{{items}}}")
            return "\n".join(out)
        return "\n".join(
            "\\skillline{" + tex(g.name) + "}{" + tex(", ".join(g.items)) + "}" for g in groups
        )
    if kind == "summary":
        return f"\\summarytext{{{tex_rich(s.text)}}}" if s.text else ""
    if kind == "links":
        if not s.links:
            return ""
        inner = "\\linksep ".join(
            "\\mbox{" + tex(l.label) + ": " + _linked(l.url, display_url(l.url)) + "}"
            for l in s.links
        )
        return f"\\linkline{{{inner}}}"
    return ""


def render_business_sections(sections, options: BusinessOptions | None = None) -> str:
    options = options or BusinessOptions()
    out = []
    for s in sections:
        body = _render_body(s, options)
        if body:
            out.append(with_gap(f"\\section{{{tex(s.title)}}}\n{body}", s))
    return "\n\n".join(out)
