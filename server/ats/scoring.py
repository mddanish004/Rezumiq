"""ATS scoring helpers, ported from modules/ats/scoring.ts (Session A: structured + code-mode)."""

from __future__ import annotations

import re
from datetime import date

from ats.skills.match import find_skills, job_requirements, skill_counts, skill_forms, title_match
from ats.words import ACTION_VERBS, CLICHES, IRREGULAR_VERBS, heading_id
from resumes.content import ResumeContent, plain_text
from templates.latex import visible_content

COUNT_WORDS_RE = re.compile(r"[\w][\w'.+#-]*", re.UNICODE)


def count_words(text: str) -> int:
    return len(COUNT_WORDS_RE.findall(text or ""))


def _email_from_text(text: str):
    m = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", text)
    return m.group(0) if m else None


def is_linkedin_url(url: str) -> bool:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).hostname or ""
    except Exception:  # noqa: BLE001
        host = ""
    return bool(re.search(r"(^|\.)linkedin\.com$", host, re.IGNORECASE))


def tex_to_text(source: str) -> str:
    body = source
    m = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", source, re.DOTALL)
    if m:
        body = m.group(1)
    body = re.sub(r"(^|[^\\])%.*$", r"\1", body, flags=re.MULTILINE)
    body = re.sub(r"\\href\{(?:mailto:)?([^{}]*)\}", r"\1 ", body)
    body = re.sub(r"\\url\{([^{}]*)\}", r"\1", body)
    body = re.sub(r"\\(?:sub)*section\*?\{([^{}]*)\}", r"\n\1\n", body)
    body = re.sub(r"\\\w*[Ii]tem(?![A-Za-z])", "\n\u2022 ", body)
    body = re.sub(r"\\\\(?:\[[^\]]*\])?", "\n", body)
    body = re.sub(r"\\(?:begin|end)\{[^{}]*\}(?:\{[^{}]*\}|\[[^\]]*\])*", "\n", body)
    body = re.sub(
        r"\\(?:vspace|hspace|vskip|hskip|setlength|addtolength|titleformat|definecolor|fontsize|includegraphics|rule|label|pagestyle|newcommand|renewcommand|input|usepackage)\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*",
        "",
        body,
    )
    body = re.sub(r"\}\s*\{", " | ", body)
    body = re.sub(r"(?<!\\)[&~$]", " ", body)
    body = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", body)
    body = re.sub(r"[{}]", "", body)
    body = re.sub(r"\\([%&$#_])", r"\1", body)
    body = re.sub(r"-{2,}", "-", body)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r" *\n *", "\n", body)
    body = body.replace("\u2022 ", "\u2022 ")
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def _contact_from_text(text, header):
    without_emails = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", " ", text)
    phones = re.findall(r"\+?\d[\d\s().-]{6,}\d", without_emails)
    phone_ok = False
    for p in phones:
        d = len(re.sub(r"\D", "", p))
        if d <= 15 and (d >= 10 or (p.startswith("+") and d >= 8)):
            phone_ok = True
            break
    location = bool(
        re.search(
            r"[A-Z][[A-Za-z].]+(?: [A-Z][[A-Za-z].]+)*, [A-Z][A-Za-z]+|\b(?:India|Remote)\b",
            header,
            re.UNICODE,
        )
    )
    linkedin = bool(re.search(r"linkedin\.com/in/", text, re.IGNORECASE))
    other_link = bool(
        re.search(
            r"(?:github\.com|gitlab\.com|bitbucket\.org|behance\.net|dribbble\.com|kaggle\.com|leetcode\.com|codeforces\.com|https?://(?!(?:www\.)?linkedin)\S+|\b[\w-]+\.(?:dev|io|me|app|tech|site|xyz)\b)",
            without_emails,
            re.IGNORECASE,
        )
    )
    return {
        "email": without_emails != text,
        "phone": phone_ok,
        "location": location,
        "linkedin": linkedin,
        "otherLink": other_link,
    }


def facts_from_text(raw):
    lines = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    parsed = []
    sections = []
    odd_headings = []
    section = None
    seen = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            parsed.append({"text": "", "section": section, "kind": "break"})
            continue
        seen += 1
        hid = heading_id(line)
        if hid:
            section = hid
            if hid not in sections:
                sections.append(hid)
            parsed.append({"text": "", "section": section, "kind": "break"})
        elif re.match(
            r"^\s*(?:[\u2022\u00b7\u25aa\u25cf\u25e6\u2023\u2219\u25cb\u25a0\u25a1\u25ba\u25b8\u27a2\u27a4\u2713\u2714]\s*|[*\u2013-]\s+)",
            line,
        ):
            listed = section in ("skills", "coursework", "links")
            parsed.append(
                {
                    "text": re.sub(
                        r"^\s*(?:[\u2022\u00b7\u25aa\u25cf\u25e6\u2023\u2219\u25cb\u25a0\u25a1\u25ba\u25b8\u27a2\u27a4\u2713\u2714]\s*|[*\u2013-]\s+)",
                        "",
                        line,
                    ),
                    "section": section,
                    "kind": "plain" if listed else "bullet",
                }
            )
        elif parsed and parsed[-1]["kind"] == "bullet" and re.match(r"^[a-z]", line, re.UNICODE):
            parsed[-1]["text"] += " " + line
        elif (
            seen > 3
            and re.match(r"^[A-Z][[A-Z] &/]{2,30}$", line, re.UNICODE)
            and len(line.split()) <= 3
        ):
            odd_headings.append(line)
            section = None
            parsed.append({"text": "", "section": section, "kind": "break"})
        else:
            parsed.append({"text": line, "section": section, "kind": "plain"})

    if not any(p["kind"] == "bullet" for p in parsed):
        for p in parsed:
            if (
                p["kind"] == "plain"
                and p["section"]
                and p["section"] in ("summary", "experience", "projects", "leadership")
                and count_words(p["text"]) >= 6
            ):
                p["kind"] = "bullet"

    paragraphs = 0
    block = 0
    for p in parsed + [{"text": "", "section": None, "kind": "break"}]:
        if p["kind"] == "plain" and (
            not p["section"] or p["section"] in ("summary", "experience", "projects", "leadership")
        ):
            block += count_words(p["text"])
            continue
        if block > 60:
            paragraphs += 1
        block = 0

    text = raw.strip()
    header_lines = [l.strip() for l in lines if l.strip()][:6]
    header = "\n".join(header_lines)
    plain_in = lambda sid: [
        p["text"] for p in parsed if p["kind"] == "plain" and p["section"] == sid
    ]
    filled = [l.strip() for l in lines if l.strip()]
    first_heading_idx = next((i for i, l in enumerate(filled) if heading_id(l)), -1)
    intro = filled[: (6 if first_heading_idx == -1 else min(first_heading_idx, 6))]

    bullets_list = [p["text"] for p in parsed if p["kind"] == "bullet"]
    sections_list = []
    for p in parsed:
        if p["section"] and p["section"] not in sections_list:
            sections_list.append(p["section"])
    sections_collected = []
    for raw_line in lines:
        l = raw_line.strip()
        if l:
            hid = heading_id(l)
            if hid and hid not in sections_collected:
                sections_collected.append(hid)

    titles = list(header_lines) + [t for t in plain_in("experience") if count_words(t) <= 12]

    return {
        "text": text,
        "structured": False,
        "words": count_words(text),
        "bullets": bullets_list,
        "sections": sections_collected,
        "oddHeadings": odd_headings,
        "paragraphs": paragraphs,
        "titles": titles,
        "headline": intro + [t for t in plain_in("summary")],
        "email": _email_from_text(text),
        "skillsText": "\n".join(plain_in("skills")),
        "experienceEntries": None,
        "undatedEntries": 0,
        "contact": _contact_from_text(text, header),
    }


def facts_from_content(full):

    content = visible_content(
        full if not isinstance(full, dict) else ResumeContent.model_validate(full)
    )
    strip = plain_text

    def join(parts):
        return " | ".join(p for p in parts if p)

    lines = [
        content.basics.name,
        content.basics.headline or "",
        join([content.basics.email, content.basics.phone, content.basics.location]),
    ] + [f"{l.label} {l.url}" for l in content.basics.links]

    bullets = []
    sections = []
    odd_headings = []
    urls = [l.url for l in content.basics.links]
    titles = [content.basics.headline] if content.basics.headline else []
    skills = []
    experience_entries = 0
    undated_entries = 0

    for section in content.sections:
        lines.append("")
        lines.append(section.title)
        hid = heading_id(section.title)
        typed = section.type not in ("list", "links")
        if typed and hid != section.type:
            odd_headings.append(section.title)
        canonical = section.type if typed else hid
        if canonical and canonical not in sections:
            sections.append(canonical)

        if section.type == "skills":
            groups = [f"{g.name}: {', '.join(g.items)}" for g in section.groups]
            skills.extend(groups)
            lines.extend(groups)
            continue
        if section.type == "summary":
            lines.append(section.text)
            continue
        if section.type == "links":
            lines.extend(f"{l.label} {l.url}" for l in section.links)
            urls.extend(l.url for l in section.links)
            continue

        if section.type == "experience":
            headers = []
            for e in section.entries:
                experience_entries += 1
                titles.append(e.role)
                if not e.start:
                    undated_entries += 1
                headers.append(join([e.role, e.organization, e.location, e.start, e.end]))
        elif section.type == "education":
            headers = [
                join([e.institution, e.degree, e.field, e.score, e.start, e.end])
                for e in section.entries
            ]
        elif section.type == "projects":
            headers = []
            for e in section.entries:
                urls.extend([e.url] if e.url else [])
                urls.extend(l.url for l in e.links)
                headers.append(join([e.name, ", ".join(e.technologies), e.url]))
        else:
            headers = [join([e.title, e.subtitle, e.date, e.url]) for e in section.entries]

        for idx, entry in enumerate(section.entries):
            lines.append(headers[idx])
            for b in entry.bullets:
                bt = strip(b.text)
                bullets.append(bt)
                lines.append(f"\u2022 {bt}")

    text = "\n".join(lines).strip()
    is_li = is_linkedin_url
    return {
        "text": text,
        "structured": True,
        "words": count_words(text),
        "bullets": bullets,
        "sections": sections,
        "oddHeadings": odd_headings,
        "paragraphs": sum(1 for b in bullets if count_words(b) > 60),
        "titles": titles,
        "headline": ([content.basics.headline] if content.basics.headline else [])
        + [s.text for s in content.sections if s.type == "summary"],
        "email": content.basics.email,
        "skillsText": "\n".join(skills),
        "experienceEntries": experience_entries,
        "undatedEntries": undated_entries,
        "contact": {
            "email": bool(content.basics.email),
            "phone": bool(content.basics.phone),
            "location": bool(content.basics.location),
            "linkedin": any(is_li(u) for u in urls),
            "otherLink": any(not is_li(u) for u in urls),
        },
    }


WEIGHTS = {
    "withoutJob": {
        "parsing": 20,
        "contact": 15,
        "sections": 15,
        "impact": 35,
        "length": 15,
        "job": 0,
    },
    "withJob": {
        "parsing": 15,
        "contact": 10,
        "sections": 15,
        "impact": 25,
        "length": 10,
        "job": 25,
    },
}

BULLET = re.compile(
    r"^\s*(?:[\u2022\u00b7\u25aa\u25cf\u25e6\u2023\u2219\u25cb\u25a0\u25a1\u25ba\u25b8\u27a2\u27a4\u2713\u2714]\s*|[*\u2013-]\s+)"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
INFORMAL_EMAIL = re.compile(
    r"sexy|cutie|babygirl|babyboy|rockstar|xoxo|lover|swag|killer|gamer|hottie|naughty|devil|crazy|cool(?!ey)",
    re.IGNORECASE,
)
PROSE_SECTIONS = {"summary", "experience", "projects", "leadership"}
EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff\u2190-\u21ff\u2300-\u23ff]")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = [m.lower() for m in MONTHS]
STATUS_VALUE = {"pass": 1, "warn": 0.5, "fail": 0}
WORST = {"pass": 0, "warn": 1, "fail": 2}
GRADES = [
    {
        "min": 85,
        "grade": "excellent",
        "text": "Excellent: a typical ATS and recruiter scan will read this resume well.",
    },
    {
        "min": 70,
        "grade": "good",
        "text": "Good: most ATS will read this resume, with a few gaps to close.",
    },
    {
        "min": 50,
        "grade": "fair",
        "text": "Fair: an ATS can read parts of this, but key details are weak or missing.",
    },
    {
        "min": 0,
        "grade": "poor",
        "text": "Poor: an ATS and a recruiter will likely miss important details.",
    },
]
PARSE_WEIGHTS = {
    "columns": 3,
    "density": 3,
    "glyphs": 2,
    "contact": 2,
    "sections": 2,
    "jobs": 2,
    "name": 2,
}
GENERIC_FILE_WORDS = re.compile(
    r"\b(?:resume|cv|copy|final|draft|new|updated|latest|untitled|document\d*|doc|scan|img|image|file|v\d+)\b",
    re.IGNORECASE,
)
FIRST_PERSON_RE = re.compile(r"\bI(?:'m|'ve|'d)?(?![\w/.])", re.IGNORECASE)
PRONOUN_RE = re.compile(r"\b(?:me|my|myself)\b", re.IGNORECASE)
NAMED_DATE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]{0,6}\.?\s+(?:19|20)\d{2}\b",
    re.IGNORECASE,
)
NUMERIC_DATE = re.compile(
    r"\b(?:0?[1-9]|1[0-2])[/.](?:19|20)\d{2}\b|\b(?:19|20)\d{2}[-/.](?:0[1-9]|1[0-2])\b"
)
SEASON_DATE = re.compile(
    r"\b(?:spring|summer|fall|autumn|winter)\s+(?:19|20)\d{2}\b", re.IGNORECASE
)
INTERN = re.compile(r"\bintern(ship)?s?\b", re.IGNORECASE)
MONTHS_LOWER = [m.lower() for m in MONTHS]
RANGE = re.compile(
    r"(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\.?\s*)?((?:19|20)\d{2})\s*(?:[-\u2013\u2014]|to)\s*"
    r"(?:(present|current|now|till date|today)|(?:(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\.?\s*)?((?:19|20)\d{2}))",
    re.IGNORECASE,
)


def check(
    id: str,
    label: str,
    weight: int,
    status: str,
    detail: str,
    fix: str,
    lines: list[dict] | None = None,
) -> dict:
    result = {
        "id": id,
        "label": label,
        "weight": weight,
        "status": status,
        "detail": detail,
        "fix": None if status == "pass" else fix,
    }
    if status != "pass" and lines:
        unique: list[dict] = []
        seen: set[str] = set()
        for line in lines:
            if line["text"] in seen:
                continue
            seen.add(line["text"])
            unique.append(line)
        result["lines"] = unique[:3]
    return result


def line_of(raw: str, highlight: str | None = None) -> dict:
    text = BULLET.sub("", raw).strip()
    if len(text) > 160:
        text = text[:157].rstrip() + "..."
    line: dict = {"text": text}
    if highlight:
        line["highlight"] = highlight
    return line


def band(value: float, pass_at: float, warn_at: float) -> str:
    if value >= pass_at:
        return "pass"
    if value >= warn_at:
        return "warn"
    return "fail"


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' if n != 1 else ''}"


def quote(text: str) -> str:
    shown = text[:67].rstrip() + "..." if len(text) > 70 else text
    return f'"{shown}"'


def share(part: int, whole: int) -> float:
    return 0 if whole == 0 else part / whole


def month_label(index: int) -> str:
    return f"{MONTHS[(index % 12) % 12]} {index // 12}"


def month_of(name: str | None) -> int | None:
    if not name:
        return None
    return MONTH_NAMES.index(name[:3].lower()) + 1


def current_month() -> int:
    today = date.today()
    return today.year * 12 + (today.month - 1)


def parsing_checks(facts: dict) -> list[dict]:
    unreadable = len(re.findall(r"[\uFFFD\uE000-\uF8FF]", facts["text"]))
    icons = len(
        EMOJI.findall(
            "\n".join(
                line.replace(BULLET.pattern, "") if BULLET.search(line) else line
                for line in facts["text"].split("\n")
            )
        )
    )
    years = len(YEAR.findall(facts["text"]))

    checks = [
        check(
            "readable",
            "Readable text",
            3,
            "pass" if facts["structured"] else band(facts["words"], 100, 50),
            "Built from structured fields, so the text layer is clean."
            if facts["structured"]
            else f"{plural(facts['words'], 'word')} came through as text.",
            "Most of this resume didn't come through as text. Export a text PDF from your editor (not a scan or a photo), and keep text out of images.",
        ),
        check(
            "characters",
            "Standard characters",
            2,
            "pass" if unreadable == 0 else "warn" if unreadable <= 5 else "fail",
            "No unreadable characters found."
            if unreadable == 0
            else f"{plural(unreadable, 'character')} can't be read, usually from icon fonts or unusual symbols.",
            'Replace icon fonts and special symbols (for phone, email, or skill ratings) with plain words like "Phone:" or the value itself.',
        ),
        check(
            "icons",
            "No emoji or icons",
            1,
            "pass" if icons <= 2 else "warn",
            "No emoji or pictographs."
            if icons == 0
            else f"{plural(icons, 'emoji or icon')} found.",
            "Remove emoji and pictographs. Parsers drop them or turn them into junk characters.",
        ),
    ]
    if facts["structured"]:
        checks.append(
            check(
                "dates",
                "Dates on roles",
                2,
                "pass" if facts["undatedEntries"] == 0 else "warn",
                "Every role has a start date."
                if facts["undatedEntries"] == 0
                else f"{plural(facts['undatedEntries'], 'role')} without a start date.",
                "Add start and end dates to every role. An ATS uses them to work out your years of experience.",
            ),
        )
    else:
        checks.append(
            check(
                "dates",
                "Dates on roles",
                2,
                "pass" if years > 0 else "fail",
                f"{plural(years, 'year')} found in dates."
                if years > 0
                else "No years found anywhere in the resume.",
                'Add month and year to every role and degree, for example "Jun 2023 - Present".',
            ),
        )
    return checks


def experience(facts: dict, content) -> dict | None:
    from resumes.content import ResumeContent

    resume: dict = {"text": facts["text"]}
    if content is not None:
        resume["content"] = (
            content if isinstance(content, ResumeContent) else ResumeContent.model_validate(content)
        )
    return resume_experience(resume)


def merged_months(ranges: list[list[int]]) -> int:
    total = 0
    reach = float("-inf")
    for start, end in sorted(ranges, key=lambda r: r[0]):
        if end <= reach:
            continue
        total += end - max(start, reach)
        reach = end
    return total


def month_index(year: str, month: str | None, end: bool) -> int:
    value = int(year) * 12
    if month:
        value += int(month) - (0 if end else 1)
    return value


def resume_section(text: str, section_id: str) -> list[str]:
    out: list[str] = []
    inside = False
    for line in text.split("\n"):
        key = re.sub(r"[^a-z& ]+", " ", line.lower()).strip()
        key = re.sub(r"\s+", " ", key)
        found_id = heading_id(line) if len(line) <= 40 else None
        if found_id:
            inside = found_id == section_id
        elif inside:
            out.append(line)
    return out


def resume_experience(resume: dict) -> dict | None:
    content = resume.get("content")
    ranges: list[list[int]] = []
    undated = 0
    roles = 0
    if content is not None:
        for section in content.sections:
            if section.type != "experience" or section.hidden:
                continue
            for entry in section.entries:
                if entry.hidden or INTERN.search(f"{entry.role} {entry.organization}"):
                    continue
                roles += 1
                if not entry.start:
                    undated += 1
                    continue
                start_year, _, start_month = entry.start.partition("-")
                end_year, _, end_month = (entry.end or "present").partition("-")
                end = (
                    current_month()
                    if end_year == "present" or not end_year
                    else month_index(end_year, end_month or None, True)
                )
                ranges.append([month_index(start_year, start_month or None, False), end])
    else:
        lines = resume_section(resume["text"], "experience")
        if not lines:
            return None
        for line in (l for l in lines if not INTERN.search(l)):
            for m in RANGE.finditer(line):
                roles += 1
                end = (
                    current_month()
                    if m.group(3)
                    else month_index(m.group(5) or "", month_of(m.group(4)), True)
                )
                start_month = month_of(m.group(1))
                ranges.append([month_index(m.group(2) or "", start_month, False), end])
    return {
        "years": round(merged_months([r for r in ranges if r[1] > r[0]]) / 1.2) / 10,
        "roles": roles,
        "undated": undated,
        "ranges": ranges,
    }


def date_checks(facts: dict, content) -> list[dict]:
    named = [] if facts["structured"] else NAMED_DATE.findall(facts["text"])
    numeric = [] if facts["structured"] else NUMERIC_DATE.findall(facts["text"])
    seasons = SEASON_DATE.findall(facts["text"])
    exp = experience(facts, content)
    ranges = exp["ranges"] if exp else []
    reversed_ranges = [r for r in ranges if r[1] <= r[0]]
    future = [r for r in ranges if r[0] > current_month() + 1]
    mixed = len(named) > 0 and len(numeric) > 0
    problems = [
        f"a role that ends ({month_label(end - 1)}) before it starts ({month_label(start)})"
        for start, end in reversed_ranges
    ]
    problems += [f"a role starting in the future ({month_label(start)})" for start, _end in future]
    if mixed:
        problems.append(f'mixed formats, like "{named[0]}" and "{numeric[0]}"')
    if seasons:
        problems.append(f'seasons instead of months, like "{seasons[0]}"')
    lines: list[dict] = [line_of(numeric[0])] if mixed else []
    lines += [line_of(s) for s in seasons[:1]]
    return [
        check(
            "date-format",
            "Consistent dates",
            2,
            "fail" if reversed_ranges else ("warn" if problems else "pass"),
            "Dates use one format and run in order."
            if not problems
            else f"Found {'; '.join(problems)}.",
            'Write every date the same way, month and year, like "Jun 2024 - Present". An ATS works out your experience from these dates, and a season or a mixed format can stop it reading them.',
            lines,
        ),
    ]


def gap_checks(facts: dict, content) -> list[dict]:
    if is_early_career(facts):
        return []
    exp = experience(facts, content)
    ranges = (
        sorted([r for r in (exp["ranges"] if exp else []) if r[1] > r[0]], key=lambda r: r[0])
        if exp
        else []
    )
    if len(ranges) < 2:
        return []
    gaps: list[str] = []
    reach = ranges[0][1]
    for start, end in ranges[1:]:
        if start - reach > 6:
            gaps.append(
                f"{start - reach} months between {month_label(reach - 1)} and {month_label(start)}"
            )
        reach = max(reach, end)
    return [
        check(
            "gaps",
            "Gaps between roles",
            1,
            "pass" if not gaps else "warn",
            "No gaps over six months between roles."
            if not gaps
            else f"A gap of {', and one of '.join(gaps)}.",
            "Recruiters often ask about gaps over six months. If you studied, freelanced, travelled or cared for family, add one line for it so the gap is explained before they ask.",
        ),
    ]


def file_checks(file: dict) -> list[dict]:
    words = re.sub(r"\.pdf$", "", file.get("name") or "", flags=re.IGNORECASE)
    words = re.sub(r"[_\-.()]+", " ", words)
    vague = len(re.sub(GENERIC_FILE_WORDS, "", re.sub(r"[^a-z]", "", words.lower()))) < 3
    mb = file.get("sizeBytes", 0) / 1024 / 1024
    return [
        check(
            "file-name",
            "File name",
            1,
            "warn" if vague else "pass",
            f'"{file.get("name")}" doesn\'t say whose resume it is.'
            if vague
            else f'"{file.get("name")}" names the file clearly.',
            'Name the file after yourself, like "Aarav-Sharma-Resume.pdf". Recruiters download dozens of files called resume.pdf.',
        ),
        check(
            "file-size",
            "File size",
            1,
            "fail" if mb > 2.5 else "warn" if mb > 1 else "pass",
            f"{max(1, round(file.get('sizeBytes', 0) / 1024)) if mb < 0.1 else f'{mb:.1f} MB'}.",
            "Keep the PDF under 1 MB. Some ATS reject files over 2 MB, and large files usually mean images or embedded fonts a parser can't read anyway. Export again without photos or background images.",
        ),
    ]


def hidden_text_checks(items: list[dict], page: dict) -> list[dict]:
    hidden = [
        item
        for item in items
        if (item.get("text") or "").strip()
        and (
            item.get("height", 0) < 4.5
            or item.get("x", 0) > page.get("width")
            or item.get("x", 0) + item.get("width", 0) < 0
            or item.get("y", 0) > page.get("height")
            or item.get("y", 0) + item.get("height", 0) < 0
        )
    ]
    return [
        check(
            "hidden-text",
            "No hidden text",
            2,
            "pass" if not hidden else "fail",
            "No tiny or off-page text found."
            if not hidden
            else f"{plural(len(hidden), 'piece')} of text too small to see or outside the page.",
            "Remove tiny or off-page text. Pasting keywords in invisible text is easy for an ATS to read and for a recruiter to spot, and it gets resumes rejected.",
            [line_of(item["text"].strip()) for item in hidden],
        ),
    ]


def parser_checks(facts: dict, parse: dict) -> list[dict]:
    checks = [
        {**issue, "weight": PARSE_WEIGHTS.get(issue["id"], 1)}
        for issue in parse.get("issues") or []
        if issue["id"] != "contact" or (facts["contact"]["email"] and facts["contact"]["phone"])
    ]
    if parse.get("parseRate") is None:
        return checks
    missed = [f for f in parse.get("fields") or [] if not f["ok"]]
    return [
        check(
            "parse-rate",
            "Parse rate",
            4,
            band(parse.get("parseRate") or 0, 0.9, 0.7),
            f"A parser read {len(parse.get('fields') or []) - len(missed)} of {len(parse.get('fields') or [])} fields correctly.",
            f"It missed or misread: {', '.join(f['label'] for f in missed)}. Keep one column, plain headings, and each job's title, company and dates on its own lines.",
        ),
        *checks,
    ]


def contact_checks(facts: dict) -> list[dict]:
    email = facts["contact"]["email"]
    phone = facts["contact"]["phone"]
    location = facts["contact"]["location"]
    linkedin = facts["contact"]["linkedin"]
    other_link = facts["contact"]["otherLink"]
    label_only = (
        not facts["structured"]
        and not linkedin
        and bool(re.search(r"\blinked\s?in\b", facts["text"], re.IGNORECASE))
    )
    checks = [
        check(
            "email",
            "Email",
            3,
            "pass" if email else "fail",
            "Email address found." if email else "No email address found.",
            "Add your email at the top, as plain text in the body (not in a header or footer, which some parsers skip).",
        ),
        check(
            "phone",
            "Phone",
            2,
            "pass" if phone else "fail",
            "Phone number found." if phone else "No phone number found.",
            "Add a phone number with your country code, for example +91 98765 43210.",
        ),
        check(
            "location",
            "Location",
            1,
            "pass" if location else "warn",
            "Location found." if location else "No city found near your name.",
            'Add your city and country, like "Bengaluru, India". Recruiters filter by location, and "Remote" works too.',
        ),
        check(
            "linkedin",
            "LinkedIn",
            2,
            "pass" if linkedin else "warn",
            "LinkedIn profile link found."
            if linkedin
            else '"LinkedIn" appears as a label, but the address isn\'t in the text.'
            if label_only
            else "No LinkedIn profile link found.",
            "Write the link out as linkedin.com/in/your-name, since a parser may read only the visible text."
            if label_only
            else "Add your LinkedIn profile link, like linkedin.com/in/your-name.",
        ),
        check(
            "links",
            "GitHub or portfolio",
            1,
            "pass" if other_link else "warn",
            "GitHub, portfolio or other profile link found."
            if other_link
            else "No GitHub or portfolio link found.",
            "Add a GitHub, portfolio or coding profile link so reviewers can see your work.",
        ),
    ]
    if facts["email"]:
        checks.append(
            check(
                "email-address",
                "Professional email",
                1,
                "warn"
                if INFORMAL_EMAIL.search((facts["email"] or "").split("@")[0] or "")
                else "pass",
                f'"{facts["email"]}" reads as informal.'
                if INFORMAL_EMAIL.search((facts["email"] or "").split("@")[0] or "")
                else "Your email address looks professional.",
                "Use an address built from your name, like firstname.lastname@gmail.com. It's the first thing a recruiter reads.",
            ),
        )
    return checks


def is_early_career(facts: dict) -> bool:
    if facts["experienceEntries"] is not None:
        return facts["experienceEntries"] <= 1
    return "experience" not in facts["sections"]


def section_checks(facts: dict) -> list[dict]:
    has = lambda section_id: section_id in facts["sections"]
    early = is_early_career(facts)
    return [
        check(
            "experience",
            "Experience",
            3,
            "pass" if has("experience") else "warn" if has("projects") else "fail",
            "Experience section found." if has("experience") else "No Experience section found.",
            'Add an Experience section headed "Experience". Internships, freelance work and open source contributions all count.',
        ),
        check(
            "education",
            "Education",
            3,
            "pass" if has("education") else "fail",
            "Education section found." if has("education") else "No Education section found.",
            "Add an Education section with your degree, college, years and CGPA or percentage.",
        ),
        check(
            "skills",
            "Skills",
            3,
            "pass" if has("skills") else "fail",
            "Skills section found." if has("skills") else "No Skills section found.",
            'Add a Skills section headed "Skills", grouped like Languages, Frameworks, Tools. Recruiters search an ATS by skill first.',
        ),
        check(
            "projects",
            "Projects",
            2,
            "pass" if has("projects") or not early else "fail",
            "Projects section found."
            if has("projects")
            else "No Projects section, and little work experience to stand in for it."
            if early
            else "No Projects section; optional once you have work experience.",
            "Add a Projects section with 2 or 3 projects, the stack you used, and a link to each.",
        ),
        check(
            "headings",
            "Standard headings",
            2,
            "pass" if (not facts["oddHeadings"] and facts["sections"]) else "warn",
            "No standard section headings found."
            if not facts["sections"]
            else f"Found {plural(len(facts['sections']), 'standard heading')}.",
            "Rename headings to the standard ones: Experience, Education, Skills, Projects, Achievements.",
        ),
    ]


def section_order_checks(facts: dict) -> list[dict]:
    experience_at = (
        facts["sections"].index("experience") if "experience" in facts["sections"] else -1
    )
    education_at = facts["sections"].index("education") if "education" in facts["sections"] else -1
    if experience_at == -1 or education_at == -1:
        return []
    early = is_early_career(facts)
    ok = education_at < experience_at if early else experience_at < education_at
    if ok:
        detail = (
            "Education comes first, as recruiters expect from students and freshers."
            if early
            else "Experience comes before Education, as recruiters expect once you have worked."
        )
        fix = (
            "Move Education to the top, followed by Skills and Projects, then Experience."
            if early
            else "Move Experience to the top and Education to the end."
        )
    elif early:
        detail = "Experience comes before Education, but with little work experience recruiters look for your education first."
        fix = "Move Education to the top, followed by Skills and Projects, then Experience."
    else:
        detail = "Education comes before Experience. With work experience, recruiters look for your roles first."
        fix = "Move Experience to the top and Education to the end."
    return [
        check(
            "section-order",
            "Section order",
            1,
            "pass" if ok else "warn",
            detail,
            fix,
        ),
    ]


def starts_with_action_verb(bullet: str) -> bool:
    word = re.sub(r"^[^\w]+", "", bullet, flags=re.UNICODE)
    tokens = re.split(r"[^\w]+", word, maxsplit=1)
    stem = tokens[0].lower() if tokens else ""
    if stem in ACTION_VERBS or stem in IRREGULAR_VERBS or re.fullmatch(r"[a-z]{3,}ed", stem):
        return True
    for suffix in ("s", "es", "d", "ing"):
        if stem.endswith(suffix):
            base = stem[: -len(suffix)] + ("e" if suffix == "ing" else "")
            if base in ACTION_VERBS:
                return True
    return False


def first_word(bullet: str) -> str:
    word = re.sub(r"^[^\w]+", "", bullet, flags=re.UNICODE)
    tokens = re.split(r"[^\w]+", word, maxsplit=1)
    return tokens[0] if tokens else ""


def first_person_lines(text: str) -> list[dict]:
    lines: list[dict] = []
    for line in text.split("\n"):
        found = FIRST_PERSON_RE.search(line) or PRONOUN_RE.search(line)
        if found:
            lines.append(line_of(line.strip(), found.group(0)))
    return lines


def is_quantified(bullet: str) -> bool:
    return bool(re.search(r"[\d%]", re.sub(r"\b(?:19|20)\d{2}\b", "", bullet)))


def impact_checks(facts: dict) -> list[dict]:
    bullets = facts["bullets"]
    total = len(bullets)
    weak_verbs = [b for b in bullets if not starts_with_action_verb(b)]
    unquantified = [b for b in bullets if not is_quantified(b)]
    long = [b for b in bullets if count_words(b) > 35]
    short = [b for b in bullets if count_words(b) < 5]
    first_person = len(FIRST_PERSON_RE.findall(facts["text"])) + len(
        PRONOUN_RE.findall(facts["text"])
    )
    normalized = f" {re.sub(r'[^a-z]+', ' ', facts['text'].lower())} "
    cliches = [phrase for phrase in CLICHES if f" {phrase} " in normalized]
    verb_share = share(total - len(weak_verbs), max(total, 6))
    number_share = share(total - len(unquantified), max(total, 6))
    bad_length = share(len(long) + len(short), total)

    openers: dict[str, list[str]] = {}
    for bullet in bullets:
        word = first_word(bullet)
        if len(word) > 2:
            openers.setdefault(word.lower(), []).append(bullet)
    repeated = sorted(
        [(word, group) for word, group in openers.items() if len(group) >= 3],
        key=lambda item: -len(item[1]),
    )
    stuffed = sorted(skill_counts(facts["text"]).items(), key=lambda item: -item[1])
    stuffed = [item for item in stuffed if item[1] >= 8]

    checks = [
        check(
            "bullet-count",
            "Bullet points",
            4,
            band(total, 6, 3),
            f"{plural(total, 'bullet point')} found.",
            "Describe each role and project in 2 to 4 bullet points instead of paragraphs, so a recruiter can skim them.",
        ),
        check(
            "action-verbs",
            "Action verbs",
            3,
            "fail" if total == 0 else band(verb_share, 0.7, 0.4),
            f"{total - len(weak_verbs)} of {total} bullets start with an action verb.",
            "Start each bullet with a strong verb like Built, Led, Reduced or Shipped. For example, rewrite "
            + quote(weak_verbs[0])
            + "."
            if weak_verbs
            else "Start each bullet with a strong verb like Built, Led, Reduced or Shipped.",
            [line_of(bullet, first_word(bullet)) for bullet in weak_verbs],
        ),
        check(
            "quantified",
            "Quantified results",
            4,
            "fail" if total == 0 else band(number_share, 0.5, 0.25),
            f"{total - len(unquantified)} of {total} bullets have a number.",
            "Add a number to show scale or results (users, %, time saved, rank). For example, "
            + quote(unquantified[0])
            + ": how many, how fast, how much?"
            if unquantified
            else "Add a number to show scale or results (users, %, time saved, rank).",
            [line_of(bullet) for bullet in unquantified],
        ),
        check(
            "bullet-length",
            "Bullet length",
            2,
            "warn"
            if total == 0
            else ("pass" if bad_length <= 0.2 else "warn" if bad_length <= 0.4 else "fail"),
            f"{plural(len(long), 'bullet')} over 35 words, {plural(len(short), 'bullet')} under 5 words.",
            "Keep bullets to one or two lines. Split or trim " + quote(long[0]) + "."
            if long
            else "Give short bullets the what, how and result. For example, expand "
            + quote(short[0])
            + "."
            if short
            else "Write bullets of one or two lines: what you did, how, and the result.",
            [line_of(bullet) for bullet in long + short],
        ),
        check(
            "first-person",
            "No first person",
            2,
            "pass" if first_person == 0 else "warn" if first_person <= 2 else "fail",
            'No "I", "me" or "my" found.'
            if first_person == 0
            else f'"I", "me" or "my" used {plural(first_person, "time")}.',
            'Drop "I", "me" and "my": write "Built X" rather than "I built X".',
            first_person_lines(facts["text"]),
        ),
        check(
            "paragraphs",
            "No long paragraphs",
            2,
            "pass" if facts["paragraphs"] == 0 else "warn" if facts["paragraphs"] == 1 else "fail",
            "No blocks of text over 60 words."
            if facts["paragraphs"] == 0
            else f"{plural(facts['paragraphs'], 'block')} of text over 60 words.",
            "Break long paragraphs into short bullet points. Recruiters skim, and parsers handle bullets better.",
        ),
        check(
            "repeated-openers",
            "Varied verbs",
            1,
            "pass" if not repeated else "warn",
            "No verb starts more than two bullets."
            if not repeated
            else "; ".join(
                f'"{first_word(group[0])}" starts {plural(len(group), "bullet")}'
                for _word, group in repeated
            )
            + ".",
            "Vary your opening verbs so each bullet reads as its own achievement: Built, Cut, Launched, Led, Automated, Designed.",
            [line_of(bullet, first_word(bullet)) for _word, group in repeated for bullet in group],
        ),
        check(
            "keyword-stuffing",
            "No keyword stuffing",
            1,
            "pass" if not stuffed else "warn",
            "No skill is repeated suspiciously often."
            if not stuffed
            else "; ".join(f"{skill} appears {n}" for skill, n in stuffed) + ".",
            "Name each skill once in Skills and in the bullets where you used it. Repeating it many times doesn't rank you higher, and recruiters read it as stuffing.",
        ),
        check(
            "cliches",
            "No filler phrases",
            1,
            "pass" if not cliches else "warn" if len(cliches) <= 2 else "fail",
            "No filler phrases found."
            if not cliches
            else f"Filler phrases found: {', '.join('"' + phrase + '"' for phrase in cliches)}.",
            'Replace filler like "team player" or "responsible for" with what you did and what changed because of it.',
            [
                line_of(line, phrase)
                for phrase in cliches
                if (
                    line := next(
                        (l for l in facts["text"].split("\n") if phrase in l.lower()), None
                    )
                )
                is not None
            ],
        ),
    ]
    return checks


def length_checks(facts: dict, real_pages: int | None = None) -> list[dict]:
    words = facts["words"]
    early = is_early_career(facts)
    pages = real_pages if real_pages is not None else max(1, round(words / 550))
    by_words = (
        "fail"
        if words < 150 or words > 1200
        else "warn"
        if words < 300 or words > 900 or (early and words > 750)
        else "pass"
    )
    by_pages = (
        "pass"
        if real_pages is None
        else "fail"
        if pages > (2 if early else 3)
        else "warn"
        if pages > (1 if early else 2)
        else "pass"
    )
    status = by_pages if WORST[by_pages] > WORST[by_words] else by_words
    if words < 300:
        fix = "Add detail: 2 to 4 bullets per role and project, and your key skills. Aim for 400 to 700 words."
    elif early:
        fix = "Trim to one page (about 400 to 700 words). Cut older or weaker bullets first."
    else:
        fix = "Trim to two pages at most (under 900 words). Cut bullets older roles don't need."
    detail = (
        f"{plural(words, 'word')}, about {plural(pages, 'page')}."
        if real_pages is None
        else f"{plural(pages, 'page')}, {plural(words, 'word')}."
    )
    return [check("word-count", "Length", 1 if real_pages is None else 2, status, detail, fix)]


def job_match(facts: dict, job_text: str) -> dict:
    job = job_requirements(job_text)
    have = {h["skill"] for h in find_skills(facts["text"], facts.get("skillsSection"))}
    hard = job["hard"]
    soft = job["soft"]

    def split(hits: list[dict]) -> dict:
        return {
            "matched": [h["skill"] for h in hits if h["skill"] in have],
            "missing": [h["skill"] for h in hits if h["skill"] not in have],
        }

    hard = split(hard)
    soft = split(soft)
    must_have = set(job["mustHave"])
    must_hard = [s for s in hard["matched"] + hard["missing"] if s in must_have]
    must_missing = [s for s in hard["missing"] if s in must_have]
    other = {
        "matched": [s for s in hard["matched"] if s not in must_have],
        "missing": [s for s in hard["missing"] if s not in must_have],
    }
    other_total = len(other["matched"]) + len(other["missing"])
    soft_total = len(soft["matched"]) + len(soft["missing"])

    checks: list[dict] = []
    if must_hard:
        checks.append(
            check(
                "must-have",
                "Must-have skills",
                4,
                "pass" if not must_missing else "fail",
                f"All {plural(len(must_hard), 'must-have skill')} found."
                if not must_missing
                else f"Missing {len(must_missing)} of {plural(len(must_hard), 'must-have skill')}: {joined(must_missing)}.",
                f"Add the must-haves you really have to Skills and to the bullets where you used them: {joined(must_missing)}.",
            ),
        )
    if other_total > 0:
        checks.append(
            check(
                "hard-skills",
                "Other hard skills",
                3,
                band(share(len(other["matched"]), other_total), 0.75, 0.5),
                f"{len(other['matched'])} of {plural(other_total, 'other hard skill')} in the job found.",
                f"Add the ones you really have, in Skills and in your bullets: {joined(other['missing'])}.",
            ),
        )
    if soft_total > 0:
        checks.append(
            check(
                "soft-skills",
                "Soft skills",
                1,
                "pass" if share(len(soft["matched"]), soft_total) >= 0.5 else "warn",
                f"{len(soft['matched'])} of {plural(soft_total, 'soft skill')} in the job found.",
                f"Show these through what you did rather than listing them: {joined(soft['missing'])}.",
            ),
        )

    found = title_match(facts["titles"], job_text)
    title = (
        {"jobTitle": found["jobTitle"], "best": found["best"], "level": found["level"]}
        if found["jobTitle"]
        else None
    )
    if title:
        checks.append(
            check(
                "job-title",
                "Job title",
                2,
                "pass"
                if title["level"] == "exact"
                else "warn"
                if title["level"] == "close"
                else "fail",
                "Your resume uses the job's title, \"" + str(title["jobTitle"]) + '".'
                if title["level"] == "exact"
                else 'Closest on your resume: "'
                + str(title["best"])
                + '", a close match for "'
                + str(title["jobTitle"])
                + '".'
                if title["level"] == "close"
                else "The job's title, \"" + str(title["jobTitle"]) + "\", isn't on your resume.",
                "Use the job's title, "
                + str(title["jobTitle"])
                + ", in your headline if it's true for you.",
            ),
        )
    if title and title["level"] != "none":
        in_headline = title_match(facts["headline"], job_text)["level"]
        checks.append(
            check(
                "title-headline",
                "Title in your headline",
                1,
                "pass" if in_headline == "none" else "warn",
                '"' + str(title["jobTitle"]) + "\" isn't in your headline or summary."
                if in_headline == "none"
                else "Your headline or summary names the job's title.",
                'Put "'
                + str(title["jobTitle"])
                + '" in the line under your name or in your summary, if it describes you.',
            ),
        )
    if hard["matched"]:
        one_form = []
        for skill in hard["matched"]:
            forms = skill_forms(skill)
            short = next((f for f in forms if re.fullmatch(r"[A-Z][A-Z0-9&]{1,5}", f)), None)
            long = next((f for f in forms if " " in f and re.fullmatch(r"[A-Za-z ]+", f)), None)
            if not short or not long:
                continue
            has_short = (
                re.search(
                    r"(?<![A-Za-z0-9])" + re.escape(short) + r"(?![A-Za-z0-9])", facts["text"]
                )
                is not None
            )
            has_long = long.lower() in facts["text"].lower()
            if has_short != has_long:
                one_form.append(f"{long} ({short})")
        checks.append(
            check(
                "acronyms",
                "Acronyms spelled out",
                1,
                "pass" if not one_form else "warn",
                "Skills with a short form are written both ways, or need no expanding."
                if not one_form
                else f"Written only one way: {joined(one_form)}.",
                "Write both forms once, like "
                + (one_form[0] if one_form else "Machine Learning (ML)")
                + ". Some ATS searches match only the exact form the recruiter typed.",
            ),
        )
    return {
        "checks": checks,
        "hasSkills": len(hard["matched"])
        + len(hard["missing"])
        + len(soft["matched"])
        + len(soft["missing"])
        > 0,
        "keywords": {
            "matched": hard["matched"],
            "missing": hard["missing"],
            "hard": hard,
            "soft": soft,
            "mustHaveMissing": must_missing,
            "implied": [],
        },
        "title": title,
    }


def score_resume(input: dict) -> dict:
    content = input.get("content")
    facts = (
        facts_from_content(content)
        if content is not None
        else facts_from_text(input.get("text") or "")
    )
    file = input.get("file")
    pdf = input.get("pdf")
    parse = input.get("parse")
    behind = [
        u
        for u in (file or {}).get("hiddenLinks") or []
        if re.match(r"^https?://", u, re.IGNORECASE)
    ]
    if any(is_linkedin_url(u) for u in behind):
        facts["contact"]["linkedin"] = True
    if any(not is_linkedin_url(u) for u in behind):
        facts["contact"]["otherLink"] = True
    match = job_match(facts, input["jobText"]) if input.get("jobText") else None
    has_job = bool(match and match["hasSkills"])
    weights = WEIGHTS["withJob"] if has_job else WEIGHTS["withoutJob"]

    checks = parser_checks(facts, parse) if parse is not None else parsing_checks(facts)
    checks += date_checks(facts, content)
    if file is not None:
        checks += file_checks(file)
    if pdf is not None:
        checks += hidden_text_checks(pdf.get("items") or [], pdf.get("page") or {})

    sections_checks = [c for c in section_checks(facts) if parse is None or c["id"] != "headings"]
    sections_checks += section_order_checks(facts)
    sections_checks += gap_checks(facts, content)

    groups: list[dict] = [
        {"id": "parsing", "label": "Parsing and format", "checks": checks},
        {"id": "contact", "label": "Contact details", "checks": contact_checks(facts)},
        {"id": "sections", "label": "Standard sections", "checks": sections_checks},
        {"id": "impact", "label": "Impact and content", "checks": impact_checks(facts)},
        {
            "id": "length",
            "label": "Length",
            "checks": length_checks(facts, (file or {}).get("pages")),
        },
        *(
            [{"id": "job", "label": "Job match", "checks": match["checks"]}]
            if has_job and match
            else []
        ),
    ]

    losses: list[dict] = []
    categories: list[dict] = []
    for group in groups:
        max_score = weights[group["id"]]
        group_checks = group["checks"]
        total_weight = sum(c["weight"] for c in group_checks)
        earned = sum(c["weight"] * STATUS_VALUE[c["status"]] for c in group_checks)
        for c in group_checks:
            losses.append(
                {
                    "label": c["label"],
                    "lost": (max_score * c["weight"] * (1 - STATUS_VALUE[c["status"]]))
                    / total_weight,
                }
            )
        categories.append(
            {
                "id": group["id"],
                "label": group["label"],
                "score": round((max_score * earned) / total_weight),
                "maxScore": max_score,
                "checks": [{k: v for k, v in c.items() if k != "weight"} for c in group_checks],
            },
        )

    score = sum(c["score"] for c in categories)
    grade = next(g for g in GRADES if score >= g["min"])
    top = [
        l["label"]
        for l in sorted((l for l in losses if l["lost"] > 0), key=lambda l: -l["lost"])[:2]
    ]
    summary = (
        f"{grade['text']} Fix first: {', '.join(top)}."
        if top
        else f"{grade['text']} Nothing major to fix."
    )

    knockouts = None
    if input.get("jobText"):
        knockouts = [
            dict(k, checkedWithAi=False)
            for k in find_knockouts(
                input["jobText"],
                {
                    "text": facts["text"],
                    **({"content": visible_content(content)} if content is not None else {}),
                },
            )
        ]

    return {
        "score": score,
        "grade": grade["grade"],
        "summary": summary,
        "categories": categories,
        "keywords": match["keywords"] if match else None,
        "title": match["title"] if match else None,
        "parse": None
        if parse is None
        else {"parseRate": parse.get("parseRate"), "fields": parse.get("fields")},
        "knockouts": knockouts,
        "stats": {
            "words": facts["words"],
            "bullets": len(facts["bullets"]),
            "sections": facts["sections"],
            "quantifiedBullets": len([b for b in facts["bullets"] if is_quantified(b)]),
        },
    }


def resume_text(input: dict) -> str:
    return (
        facts_from_content(input.get("content"))
        if input.get("content") is not None
        else facts_from_text(input.get("text") or "")
    )["text"]


def joined(skills: list[str], max: int = 6) -> str:
    return ", ".join(skills[:max])


def find_knockouts(job_text: str, resume: dict) -> list[dict]:
    """Advisory knockout hints: see ats.knockouts; they never change the score."""
    from . import knockouts

    return knockouts.find_knockouts(job_text, resume)
