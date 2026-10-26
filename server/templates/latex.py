r"""LaTeX rendering helpers, ported from templates/latex.ts.

Every user string passes through tex(), so user input can never inject LaTeX
commands. Rich text keeps **bold** and [words](url) links; URLs are percent-
and backslash-escaped so they survive \href and tables.
"""

import re

from resumes.content import ResumeContent, link_parts

TEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex(value: str | None) -> str:
    return re.sub(r"[\\&%$#_{}~^]", lambda char: TEX_SPECIALS[char.group(0)], value or "")


def tex_bold(value: str) -> str:
    parts = re.split(r"\*\*(.+?)\*\*", value)
    return "".join(
        r"\textbf{" + tex(part) + "}" if index % 2 == 1 else tex(part)
        for index, part in enumerate(parts)
    )


def tex_rich(value: str | None) -> str:
    """Escapes text, turns **bold** markers into \textbf{} and [words](url)
    into an underlined link on those words."""
    out = []
    for part in link_parts(value or ""):
        url = part.get("url")
        out.append(
            "\\href{" + tex_url(url) + "}{\\underline{" + tex_bold(part["text"]) + "}}"
            if url
            else tex_bold(part["text"])
        )
    return "".join(out)


def tex_url(url: str) -> str:
    return re.sub(r"\^", "%5E", re.sub(r"[\\%#{}&]", r"\\\g<0>", url))


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def format_date(value: str | None) -> str:
    if not value:
        return ""
    if value == "present":
        return "Present"
    year, _, month = value.partition("-")
    return f"{MONTHS[int(month) - 1]} {year}" if month else year


def date_range(start: str | None, end: str | None) -> str:
    a = format_date(start)
    b = format_date(end)
    if a and b:
        return f"{a} -- {b}"
    return a or b


def join_non_empty(parts: list[str | None], separator: str) -> str:
    return separator.join(part for part in parts if part and part.strip())


def visible_content(content: ResumeContent | dict) -> ResumeContent:
    """Drops everything the user hid, so templates only deal with what is shown."""
    from resumes.content import ResumeContent

    if isinstance(content, dict):
        content = ResumeContent.model_validate(content)
    rendered: list = []
    for section in content.sections:
        if section.hidden:
            continue
        if section.type == "skills":
            live = [g for g in section.groups if g.items]
            if not live:
                continue
            live = [g.model_copy(update={"name": re.sub(r"\s*:+$", "", g.name)}) for g in live]
            rendered.append(section.model_copy(update={"groups": live}))
            continue
        if section.type in ("links", "summary"):
            rendered.append(section)
            continue
        entries = []
        for entry in section.entries:
            if entry.hidden:
                continue
            bullets = [b for b in entry.bullets if not b.hidden]
            entries.append(entry.model_copy(update={"bullets": bullets}))
        rendered.append(section.model_copy(update={"entries": entries}))
    return ResumeContent(basics=content.basics, sections=rendered)


def fits_one_line(parts: list[str | None], dated: bool) -> bool:
    return len(" | ".join(part for part in parts if part)) <= (75 if dated else 90)


def gap(e) -> str:
    """The extra space a user asked for after an entry; nothing when unset, so
    other resumes render unchanged."""
    pt = getattr(e, "space_after", None)
    return f"\n\\vspace{{{pt}pt}}" if pt else ""


CLOSING_LIST = re.compile(
    r"\\(?:end\{(?:itemize|enumerate|description)\}|[A-Za-z]*ListEnd)(?:\\vspace\{[^}]*\})?\s*$"
)


def with_gap(rendered: str, s) -> str:
    """A rendered section followed by the space the user asked for; empty
    sections stay empty.

    Space after a section's closing list is merged with the list's own end
    spacing and the next heading's, so LaTeX added about 10pt more than asked
    and ignored tightening. Just inside the list, before it closes, it's exact.
    """
    if not rendered or not s.space_after:
        return rendered
    end = CLOSING_LIST.search(rendered)
    if end:
        return f"{rendered[: end.start()]}\\vspace{{{s.space_after}pt}}\n{rendered[end.start() :]}"
    return rendered + gap(s)


def compact_list(entries) -> str:
    """Achievements and certifications without bullets of their own read best as
    one tight bulleted list: "Name, a dash, description" with the name bold (and
    linked), or the item as plain text when it is one sentence."""
    items = []
    for e in entries:
        if not e.url:
            title = f"\\textbf{{{tex_rich(e.title)}}}" if e.subtitle else tex_rich(e.title)
        elif e.subtitle:
            title = (
                "\\href{" + tex_url(e.url) + "}{\\underline{\\textbf{" + tex_rich(e.title) + "}}}"
            )
        else:
            title = f"{tex_rich(e.title)}\\,\\href{{{tex_url(e.url)}}}{{{icon(r'\\faLink')}}}"
        subtitle = f" -- {tex_rich(e.subtitle)}" if e.subtitle else ""
        date = f" ({tex(e.date)})" if e.date else ""
        items.append(f"  \\item \\small{{{title}{subtitle}{date}}}{gap(e)}")
    body = "\n".join(items)
    return (
        "\\begin{itemize}[leftmargin=0.15in, itemsep=1pt, parsep=0pt, topsep=2pt]\n"
        + body
        + "\n\\end{itemize}"
    )


LINK_ICONS: list[tuple[re.Pattern, str]] = [
    (re.compile("linkedin"), r"\faLinkedin"),
    (re.compile("github"), r"\faGithub"),
    (re.compile("gitlab"), r"\faGitlab"),
    (re.compile("twitter|x\\.com"), r"\faTwitter"),
    (re.compile("kaggle"), r"\faKaggle"),
    (re.compile(r"medium\.com"), r"\faMedium"),
    (re.compile("behance"), r"\faBehance"),
    (re.compile("dribbble"), r"\faDribbble"),
    (re.compile("stackoverflow"), r"\faStackOverflow"),
    (re.compile("youtube"), r"\faYoutube"),
    (re.compile("instagram"), r"\faInstagram"),
    (re.compile("leetcode|codeforces|codechef|hackerrank|geeksforgeeks"), r"\faCode"),
]


def icon(name: str) -> str:
    return r"\BeginAccSupp{ActualText={}}\raisebox{-0.1\height}{" + name + r"}\EndAccSupp{}\,"


def icon_link(url: str, name: str, label: str) -> str:
    return "\\href{" + tex_url(url) + "}{" + icon(name) + "\\underline{" + tex(label) + "}}"


def display_url(url: str) -> str:
    """A link as it reads on the page: "linkedin.com/in/aarav", not
    "https://www.linkedin.com/in/aarav/"."""
    url = re.sub(r"^https?://(www\.)?", "", url, flags=re.IGNORECASE)
    return re.sub(r"/$", "", re.sub(r"[?#].*$", "", url))


def sub(tex_source: str, **values: str) -> str:
    """Fills a template body: every literal ${name} token, exactly like the
    TypeScript template literals the bodies were ported from."""
    for key, value in values.items():
        tex_source = tex_source.replace("${" + key + "}", value)
    return tex_source


def contact_parts(basics: ResumeContent, links_mode: str | None = None) -> list[str]:
    """Contact details with an icon each; email and links are underlined and
    clickable. Templates load fontawesome5 and accsupp. Links show their
    address, not a label like "LinkedIn": an ATS keeps only the visible text,
    so a label alone leaves the recruiter without the address.

    "icon-and-name" shows a profile link as its icon and name ("LinkedIn"), so
    an ATS and a printed copy lose the address (the editor says so); "link"
    drops every icon. Email and phone always stay readable.
    """

    mark = (lambda name: "") if links_mode == "link" else (lambda name: icon(name))
    parts = []
    if basics.phone:
        parts.append(f"{mark(r'\faPhone')}{tex(basics.phone)}")
    if basics.email:
        if links_mode == "link":
            parts.append(
                "\\href{mailto:"
                + tex_url(basics.email)
                + "}{\\underline{"
                + tex(basics.email)
                + "}}"
            )
        else:
            parts.append(icon_link(f"mailto:{basics.email}", r"\faEnvelope", basics.email))
    if basics.location:
        parts.append(f"{mark(r'\faMapMarker')}{tex(basics.location)}")
    for link in basics.links:
        target = f"{link.label} {link.url}".lower()
        name = next((macro for pattern, macro in LINK_ICONS if pattern.search(target)), r"\faGlobe")
        address = display_url(link.url)
        if links_mode == "icon-and-name":
            parts.append(icon_link(link.url, name, link.label.strip() or address))
        elif links_mode == "link":
            parts.append("\\href{" + tex_url(link.url) + "}{\\underline{" + tex(address) + "}}")
        else:
            parts.append(icon_link(link.url, name, address))
    return [f"\\allowbreak\\mbox{{{part}}}" for part in parts]
