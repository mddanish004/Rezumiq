"""Turn the model's loose resume extraction into resume content, ported from extraction.ts."""

from __future__ import annotations

import re
import uuid
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError

from resumes.content import BULLET_MAX, ResumeContent

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AiLink(BaseModel):
    label: str
    url: str


class AiEntry(BaseModel):
    organization: str | None = None
    role: str | None = None
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    score: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    url: str | None = None
    location: str | None = None
    start: str | None = None
    end: str | None = None
    date: str | None = None
    technologies: list[str] = Field(default_factory=list)
    links: list[AiLink] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class AiGroup(BaseModel):
    name: str
    items: list[str] = Field(default_factory=list)


class AiSection(BaseModel):
    type: Literal["experience", "education", "projects", "skills", "list", "links", "summary"]
    title: str
    text: str | None = None
    entries: list[AiEntry] = Field(default_factory=list)
    groups: list[AiGroup] = Field(default_factory=list)
    links: list[AiLink] = Field(default_factory=list)


class AiBasics(BaseModel):
    name: str
    headline: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[AiLink] = Field(default_factory=list)


class ExtractionOut(BaseModel):
    basics: AiBasics
    sections: list[AiSection] = Field(default_factory=list)


EXTRACTION_SCHEMA = ExtractionOut.model_json_schema()


def short_id() -> str:
    return uuid.uuid4().hex[:12]


_LEFTOVERS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u00ad\ufffe\uffff]")


def clean(value):
    """A removed icon leaves its spaces behind: "(36k+ )" becomes "(36k+)"."""
    if value is None:
        return None
    text = _LEFTOVERS.sub("", str(value)).strip()
    text = re.sub(r"\( +", "(", text)
    text = re.sub(r" +\)", ")", text)
    text = text.strip()
    return text or None


def plain(value):
    """Names, titles and labels are never formatted; bold markers only belong in bullets and descriptions."""
    text = clean(value)
    return clean(text.replace("**", "")) if text else None


_YEAR_MONTH = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")


def _date(value):
    text = clean(value)
    if not text:
        return None
    text = text.lower()
    return text if _YEAR_MONTH.match(text) else None


def _end_date(value):
    text = clean(value)
    if text and text.lower() == "present":
        return "present"
    return _date(value)


def url_of(value):
    text = clean(value)
    if not text:
        return None
    with_scheme = text if re.match(r"^https?://", text, re.IGNORECASE) else f"https://{text}"
    parsed = urlparse(with_scheme)
    if parsed.scheme in ("http", "https") and parsed.hostname and "." in parsed.hostname:
        return with_scheme
    return None


SITE_NAMES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"linkedin\."), "LinkedIn"),
    (re.compile(r"github\.com"), "GitHub"),
    (re.compile(r"gitlab\.com"), "GitLab"),
    (re.compile(r"(twitter|x)\.com"), "X"),
    (re.compile(r"leetcode\."), "LeetCode"),
    (re.compile(r"codeforces\."), "Codeforces"),
    (re.compile(r"codechef\."), "CodeChef"),
    (re.compile(r"kaggle\."), "Kaggle"),
    (re.compile(r"behance\."), "Behance"),
    (re.compile(r"dribbble\."), "Dribbble"),
    (re.compile(r"medium\.com"), "Medium"),
]
_URL_LABEL = re.compile(r":\/\/|^www\.|\.(com|in|io|dev|org|me)\b", re.IGNORECASE)


def _link_label(label: str, url: str) -> str:
    """A label that is itself a URL prints the address; show the site's name instead."""
    if _URL_LABEL.search(label):
        return next((name for pattern, name in SITE_NAMES if pattern.search(url)), "Portfolio")
    return label.strip()[:40]


def links(items) -> list[dict]:
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        address = url_of(item.get("url"))
        label = plain(item.get("label"))
        if address and label:
            out.append({"label": _link_label(label, address), "url": address})
    return out


BULLET_MARKER = re.compile(
    r"^(?:\s*(?:[\u2022\u00b7\u25aa\u25b8\u25ba\u2023\u2043\u25e6\u25cb\u25cf\u25a0\u25a1\u27a2\u27a4\u2713\u2714\u2192]|[-\u2013\u2014](?=\s)))+\s*"
)


def bullets(items) -> list[dict]:
    out = []
    for item in items or []:
        text = clean(BULLET_MARKER.sub("", str(item or "")))
        if text:
            out.append({"id": short_id(), "text": text[:BULLET_MAX], "hidden": False})
    return out


def _with_leftovers(entry: dict, fields: tuple[str, ...], kept) -> list[dict]:
    """Text the model put in a field this entry type doesn't have becomes the first bullet."""
    extras = [entry.get(field) for field in fields if entry.get(field) not in kept]
    return bullets([*extras, *(entry.get("bullets") or [])])


def _range(entry: dict) -> dict:
    """A lone date comes back as the same start and end; keep it once, as the end."""
    start = _date(entry.get("start"))
    end = _end_date(entry.get("end"))
    return {"end": end} if start and start == end else {"start": start, "end": end}


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _shown(value: str | None) -> str | None:
    if not value:
        return None
    if value == "present":
        return "Present"
    year, _, month = value.partition("-")
    return f"{MONTH_NAMES[int(month) - 1]} {year}" if month else year


def _list_date(entry: dict) -> str | None:
    """List items keep one free-text date, even when jobs in a list give a start and end."""
    dates = _range(entry)
    return (
        " \u2013 ".join(filter(None, [_shown(dates.get("start")), _shown(dates.get("end"))]))
        or None
    )


def _project_links(entry: dict) -> dict:
    """A project's repo URL is shown as a labelled link too, unless it already is the title."""
    name = (plain(entry.get("name")) or "").lower()
    all_links = links(entry.get("links"))
    on_name = next((link for link in all_links if link["label"].lower() == name), None)
    listed = [link for link in all_links if link is not on_name]
    address = url_of(entry.get("url")) or (on_name or {}).get("url")
    if (
        not address
        or address == (on_name or {}).get("url")
        or any(l["url"] == address for l in listed)
    ):
        return {"url": address, "links": listed}
    label = next((label for pattern, label in SITE_NAMES if pattern.search(address)), "Live")
    return {"url": address, "links": [{"label": label, "url": address}, *listed][:5]}


TECH_LINE = re.compile(
    r"^(tech(nologies|nology)?( stack)?|stack|built with|tools( used)?)\s*:", re.IGNORECASE
)


def _project_tech(entry: dict) -> list[str]:
    """A "Tech Stack: React, Node" line belongs in the project's technologies, not its bullets."""
    listed = [plain(t) or "" for t in entry.get("technologies") or []]
    listed = [t for t in listed if t]
    line = next(
        (
            b
            for b in entry.get("bullets") or []
            if TECH_LINE.match(BULLET_MARKER.sub("", (b or "").strip()))
        ),
        None,
    )
    from_line = []
    if line:
        rest = plain(TECH_LINE.sub("", BULLET_MARKER.sub("", line.strip())))
        if rest:
            from_line = [part.strip() for part in re.split(r",(?![^(]*\))", rest) if part.strip()]
    return (listed if listed else from_line)[:20]


def _stack_parts(text: str) -> list[str]:
    return [part.strip() for part in re.split(r",(?![^(]*\))", text.replace("**", ""))]


def _stack_list(text: str) -> bool:
    """A comma list of short names with no sentence in it is a project's stack."""
    parts = _stack_parts(text)
    return (
        len(parts) >= 3
        and not re.search(r"[.!?]$", text.strip())
        and all(part and len(part) <= 30 and len(part.split()) <= 4 for part in parts)
    )


_SMALL_WORD = re.compile(
    r"^(a|an|and|&|as|at|by|for|in|of|on|or|the|to|with|via|[/+|-])$", re.IGNORECASE
)


def _heading_line(text: str) -> bool:
    """A short Title Case line among bullets is a tagline or heading, not something the person did."""
    words = text.replace("**", "").strip().split()
    return (
        len(words) <= 7
        and not re.search(r"[.:;!?]$", text.strip())
        and all(
            _SMALL_WORD.match(word)
            or re.match(r"^[^A-Za-z]*[A-Z]", word)
            or not re.search(r"[A-Za-z]", word)
            for word in words
        )
    )


def _hide_headings(items: list[dict]) -> list[dict]:
    return [
        {**bullet, "hidden": True} if _heading_line(bullet["text"]) else bullet for bullet in items
    ]


LINK_WORD = re.compile(
    r"^(verify|verified|link|code|live|demo|pdf|github|website|certificate|credential|view|here)$",
    re.IGNORECASE,
)


def _stack_only(text: str, technologies: list[str]) -> bool:
    """A line under a project's name that only repeats its stack and link labels."""
    known = {t.lower() for t in technologies}
    parts = [part for part in re.split(r"\s*[|,\u00b7]\s*", text.replace("**", "")) if part]
    return bool(known) and all(part.lower() in known or LINK_WORD.match(part) for part in parts)


def _bare_role(role: str, organization: str) -> str:
    """ "Full Stack Developer - Acme" when Acme is already the organization, printed separately."""
    if not organization:
        return role
    org = re.escape(organization)
    sep = r"\s*(?:[|,@\-\u2013\u2014]|\bat\b)\s*"
    return re.sub(rf"{sep}{org}$|^{org}{sep}", "", role, flags=re.IGNORECASE).strip() or role


def _normalize_section(section: dict):
    title = plain(section.get("title")) or section.get("type") or ""
    base = {"id": short_id(), "title": title[:60], "hidden": False}
    entries = section.get("entries") or []
    section_type = section.get("type")
    jobs = (
        section_type == "list"
        and entries
        and all(plain(x.get("role")) and not clean(x.get("title")) for x in entries)
    )
    kind = "experience" if jobs else section_type

    if kind == "experience":
        out = []
        for x in entries:
            organization = plain(x.get("organization"))
            role = plain(x.get("role"))
            if not organization and not role:
                continue
            out.append(
                {
                    "id": short_id(),
                    "hidden": False,
                    "organization": organization or "",
                    "role": _bare_role(role or "", organization or ""),
                    "location": plain(x.get("location")),
                    **_range(x),
                    "bullets": _hide_headings(
                        _with_leftovers(
                            x,
                            ("title", "subtitle", "name"),
                            [x.get("organization"), x.get("role"), x.get("location")],
                        )
                    ),
                }
            )
        return {**base, "type": "experience", "entries": out}

    if kind == "education":
        out = []
        for x in entries:
            institution = plain(x.get("institution"))
            if not institution:
                continue
            out.append(
                {
                    "id": short_id(),
                    "hidden": False,
                    "institution": institution,
                    "degree": plain(x.get("degree")),
                    "field": plain(x.get("field")),
                    "score": (plain(x.get("score")) or "")[:20] or None,
                    "location": plain(x.get("location")),
                    **_range(x),
                    "bullets": _with_leftovers(
                        x,
                        ("title", "subtitle"),
                        [x.get("institution"), x.get("degree"), x.get("field"), x.get("location")],
                    ),
                }
            )
        return {**base, "type": "education", "entries": out}

    if kind == "projects":
        out = []
        for x in entries:
            name = plain(x.get("name"))
            if not name:
                continue
            lines = _with_leftovers(x, ("title", "subtitle"), [x.get("name")])
            stack = next(
                (b for b in lines if not TECH_LINE.match(b["text"]) and _stack_list(b["text"])),
                None,
            )
            technologies = list(
                dict.fromkeys(
                    [
                        *(t for t in _project_tech(x) if t),
                        *((plain(t) or "") for t in (_stack_parts(stack["text"]) if stack else [])),
                    ]
                )
            )
            technologies = [t for t in technologies if t][:20]
            out.append(
                {
                    "id": short_id(),
                    "hidden": False,
                    "name": name,
                    **_project_links(x),
                    "technologies": technologies,
                    **_range(x),
                    "bullets": _hide_headings(
                        [
                            b
                            for b in lines
                            if b is not stack
                            and not TECH_LINE.match(b["text"])
                            and not _stack_only(b["text"], technologies)
                        ]
                    ),
                }
            )
        return {**base, "type": "projects", "entries": out}

    if kind == "skills":
        groups = [
            {
                "id": short_id(),
                "name": re.sub(r"\s*:+$", "", plain(g.get("name")) or "")[:60],
                "items": [plain(i) or "" for i in g.get("items") or [] if plain(i)],
            }
            for g in section.get("groups") or []
            if g.get("items")
        ]
        return {**base, "type": "skills", "groups": groups[:15]}

    if kind == "links":
        return {**base, "type": "links", "links": links(section.get("links"))[:15]}

    if kind == "summary":
        return {**base, "type": "summary", "text": (clean(section.get("text")) or "")[:1000]}

    if kind == "list":
        out = []
        for x in entries:
            raw = clean(x.get("title")) or plain(x.get("name"))
            title = raw[2:-2] if raw and re.fullmatch(r"\*\*[^*]+\*\*", raw) else raw
            if not title:
                out.extend(
                    {"id": short_id(), "hidden": False, "title": b["text"], "bullets": []}
                    for b in bullets(x.get("bullets"))
                )
                continue
            joined = (
                None
                if clean(x.get("subtitle"))
                else re.match(r"^\*\*(.+?):?\*\*\s*[:\-\u2013\u2014]?\s*(.+)$", title)
            )
            subtitle = joined.group(2) if joined else clean(x.get("subtitle"))
            date = clean(x.get("date")) or _list_date(x)
            out.append(
                {
                    "id": short_id(),
                    "hidden": False,
                    "title": (joined.group(1).strip() if joined else title)[:400],
                    "subtitle": (
                        subtitle
                        if subtitle
                        and not LINK_WORD.match(subtitle)
                        and subtitle != clean(x.get("date"))
                        else None
                    ),
                    "date": date,
                    "url": url_of(x.get("url")),
                    "bullets": bullets(x.get("bullets")),
                }
            )
        return {**base, "type": "list", "entries": out[:40]}

    return None


def normalize_extraction(extraction: dict) -> dict:
    basics = extraction.get("basics") or {}
    email = clean(basics.get("email"))
    email = re.sub(r"^mailto:", "", email, flags=re.IGNORECASE) if email else None
    sections = [
        normalized
        for section in extraction.get("sections") or []
        if isinstance(section, dict) and (normalized := _normalize_section(section)) is not None
    ]
    headline = plain(basics.get("headline"))
    if headline and len(headline) > 100 and not any(s["type"] == "summary" for s in sections):
        sections.insert(
            0,
            {
                "id": short_id(),
                "title": "Summary",
                "hidden": False,
                "type": "summary",
                "text": headline,
            },
        )
        headline = None

    content = {
        "basics": {
            "name": plain(basics.get("name")) or "",
            "headline": headline,
            "email": email if email and EMAIL_PATTERN.match(email) else None,
            "phone": (clean(basics.get("phone")) or "")[:30] or None,
            "location": plain(basics.get("location")),
            "links": links(basics.get("links")),
        },
        "sections": [s for s in sections if s is not None][:20],
    }
    return _fit_to_limits(content)


def _fit_to_limits(content: dict) -> dict:
    """Cut each over-long string or list to its schema limit instead of failing the whole import."""
    for _ in range(20):
        try:
            return ResumeContent.model_validate(content).model_dump(
                by_alias=False, exclude_none=True
            )
        except ValidationError as error:
            too_big = [
                issue
                for issue in error.errors()
                if issue["type"] in ("string_too_long", "too_long")
            ]
            if len(too_big) != len(error.errors()):
                raise
            for issue in too_big:
                loc = list(issue["loc"])
                parent = content
                for key in loc[:-1]:
                    if isinstance(parent, list):
                        parent = parent[int(key)]
                    elif key not in parent and parent.get("type") == key:
                        continue
                    else:
                        parent = parent[key]
                key = loc[-1]
                limit = (issue.get("ctx") or {}).get("max_length")
                if isinstance(parent, list) and limit:
                    parent[int(key)] = parent[int(key)][: int(limit)]
                elif isinstance(parent, dict) and limit:
                    value = parent.get(key)
                    parent[key] = value[: int(limit)] if isinstance(value, (str, list)) else value
    raise ValueError("Could not fit the extraction into resume content")


def pdf_bold_phrases(items: list[dict]) -> list[str]:
    """Bold runs on the same line join into one phrase; only inline bold counts, not headings."""
    bold: set[str] = set()
    phrase: list[str] = []
    inline = False
    was_inline = False
    previous = None

    def flush():
        nonlocal phrase, was_inline
        text = " ".join(run.strip() for run in phrase).strip()
        if inline and 1 < len(text) <= 80:
            bold.add(text)
        was_inline = bool(phrase) and inline
        phrase = []

    for item in items:
        same_line = previous is not None and abs(previous["y"] - item["y"]) < 2
        if item.get("bold") and phrase and same_line:
            phrase.append(item["text"])
        else:
            continues = not same_line and bool(previous and previous.get("bold"))
            flush()
            if item.get("bold"):
                phrase.append(item["text"])
                inline = same_line or (continues and was_inline)
        previous = item
    flush()
    return sorted(bold)[:80]


def apply_bold(content: dict, phrases: list[str]) -> dict:
    """The model doesn't always wrap the PDF's bold words in **, so this does it for bullets and summaries."""
    usable = sorted((p for p in phrases if len(p) > 1 and "*" not in p), key=len, reverse=True)
    if not usable:
        return content
    pattern = re.compile(
        rf"(?<![A-Za-z0-9])({'|'.join(map(re.escape, usable))})(?![A-Za-z0-9])", re.IGNORECASE
    )

    def bold(text: str, limit: int) -> str:
        parts = re.split(r"(\*\*[^*]+\*\*|\[[^\]\n]+\]\([^\s)]+\))", text or "")
        bolded = "".join(
            part if part.startswith(("**", "[")) else pattern.sub(r"**\1**", part) for part in parts
        )
        return text if len(bolded) > limit else bolded

    out = {**content, "sections": []}
    for section in content["sections"]:
        if section["type"] == "summary":
            out["sections"].append({**section, "text": bold(section["text"], 1000)})
        elif "entries" in section:
            out["sections"].append(
                {
                    **section,
                    "entries": [
                        {
                            **entry,
                            "bullets": [
                                {**bullet, "text": bold(bullet["text"], BULLET_MAX)}
                                for bullet in entry["bullets"]
                            ],
                        }
                        for entry in section["entries"]
                    ],
                }
            )
        else:
            out["sections"].append(section)
    return out
