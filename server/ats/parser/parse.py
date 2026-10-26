"""Resume structure parsing and layout analysis, ported from modules/ats/parser/parse.ts."""

from __future__ import annotations

import re

from .extract import BOLD_FONT, ICON_FONT  # noqa: F401  (ICON_FONT: TS re-exports it from parse.ts)

SEPARATORS = {
    "|",
    "\u2022",
    "\u00b7",
    "\u25e6",
    "\u25aa",
    "\u25cf",
    "\u25a0",
    "\u2666",
    "\u22c4",
    "\u2219",
}
BULLET_START = re.compile(r"^[\u2022\u25e6\u25aa\u25cf\u25a0\u2666\u22c4\u2219*\-\u2013]")


def _mid(item: dict) -> float:
    return item["y"] + item["height"] / 2


def _is_separator(item: dict) -> bool:
    return item["text"].strip() in SEPARATORS or bool(ICON_FONT.search(item.get("fontName") or ""))


def body_size(items: list[dict]) -> float:
    """The font size most of the text is set in, weighted by characters."""
    ordered = sorted(items, key=lambda item: item["height"])
    remaining = sum(len(item["text"]) for item in ordered) / 2
    for item in ordered:
        remaining -= len(item["text"])
        if remaining <= 0:
            return item["height"]
    return 10


def to_line(items: list[dict]) -> dict:
    items = sorted(items, key=lambda item: item["x"])
    segments: list[dict] = []
    current: dict | None = None
    previous: dict | None = None
    for item in items:
        if _is_separator(item):
            current = None
            continue
        gap = item["x"] - current["end"] if current else float("inf")
        restyled = bool(previous) and (
            bool(previous["bold"]) != bool(item["bold"])
            or max(previous["height"], item["height"])
            > min(previous["height"], item["height"]) * 1.3
        )
        if not current or gap > item["height"] * 1.2 or (restyled and gap > item["height"] * 0.15):
            current = {
                "x": item["x"],
                "end": item["x"],
                "text": "",
                "bold": False,
                "height": 0,
                "chars": 0,
                "boldChars": 0,
            }
            segments.append(current)
        elif (
            gap > item["height"] * 0.15
            and not current["text"].endswith(" ")
            and not item["text"].startswith(" ")
        ):
            current["text"] += " "
        previous = item
        current["height"] = max(current["height"], item["height"])
        current["text"] += item["text"]
        current["end"] = max(current["end"], item["x"] + item["width"])
        chars = len(item["text"].strip())
        current["chars"] += chars
        if item["bold"]:
            current["boldChars"] += chars
        current["bold"] = current["boldChars"] * 2 > current["chars"]
    for segment in segments:
        segment["text"] = re.sub(r"\s+", " ", segment["text"]).strip()
    first = items[0]
    return {
        "page": first["page"],
        "y": min(item["y"] for item in items),
        "height": max(item["height"] for item in items),
        "x": first["x"],
        "text": " ".join(segment["text"] for segment in segments),
        "bullet": bool(BULLET_START.match(first["text"].strip())),
        "segments": [segment for segment in segments if segment["text"]],
    }


def to_lines(items: list[dict]) -> list[dict]:
    """Items whose vertical centers line up, read top to bottom, left to right."""
    groups: list[list[dict]] = []
    for item in sorted(items, key=lambda i: (i["page"], _mid(i))):
        group = groups[-1] if groups else None
        tallest = max(group, key=lambda i: i["height"]) if group else None
        if (
            group
            and tallest["page"] == item["page"]
            and abs(_mid(item) - _mid(tallest)) <= min(tallest["height"], item["height"]) / 2
        ):
            group.append(item)
        else:
            groups.append([item])
    return [line for line in (to_line(group) for group in groups) if line["segments"]]


def find_columns(lines: list[dict], page: dict) -> dict | None:
    """A second column shows up as many left-aligned segments over a shared stretch."""
    starts = sorted(
        (
            {"x": segment["x"], "end": segment["end"], "y": line["y"]}
            for line in lines
            for segment in line["segments"]
        ),
        key=lambda start: start["x"],
    )
    clusters: list[dict] = []
    for start in starts:
        cluster = clusters[-1] if clusters else None
        if cluster and start["x"] - cluster["x"] <= 4:
            cluster["count"] += 1
            cluster["top"] = min(cluster["top"], start["y"])
            cluster["bottom"] = max(cluster["bottom"], start["y"])
            cluster["ends"].append(start["end"])
        else:
            clusters.append(
                {
                    "x": start["x"],
                    "top": start["y"],
                    "bottom": start["y"],
                    "count": 1,
                    "ends": [start["end"]],
                }
            )

    def flush_right(cluster: dict) -> bool:
        edge = max(cluster["ends"])
        return (
            len([end for end in cluster["ends"] if edge - end <= 3]) >= len(cluster["ends"]) * 0.8
        )

    tall = [
        c for c in clusters if c["count"] >= 4 and c["bottom"] - c["top"] >= page["height"] * 0.1
    ]
    for left in tall:
        for right in tall:
            if right["x"] - left["x"] < page["width"] * 0.2 or flush_right(right):
                continue
            top = max(left["top"], right["top"])
            bottom = min(left["bottom"], right["bottom"])
            if bottom - top < page["height"] * 0.1:
                continue
            gutter = right["x"] - 1
            shared = [line for line in lines if top <= line["y"] <= bottom]
            crossing = [
                line
                for line in shared
                if any(s["x"] < gutter and s["end"] > gutter + 2 for s in line["segments"])
            ]
            if len(crossing) <= len(shared) * 0.1:
                return {"gutter": gutter, "top": top, "bottom": bottom}
    return None


def layout(items: list[dict], page: dict) -> dict:
    """Page headers and footers: small text apart from the body, which many ATS strip."""
    size = body_size(items)
    zone = page["height"] * 0.05

    def in_zone(item: dict) -> bool:
        return _mid(item) < zone or _mid(item) > page["height"] - zone

    def gap(a: dict, b: dict) -> float:
        return max(b["y"] - (a["y"] + a["height"]), a["y"] - (b["y"] + b["height"]))

    margins = [
        item
        for item in items
        if in_zone(item)
        and item["height"] <= size * 1.1
        and any(other["page"] == item["page"] and not in_zone(other) for other in items)
        and all(
            other["page"] != item["page"] or in_zone(other) or gap(item, other) >= size
            for other in items
        )
    ]
    lines = to_lines([item for item in items if item not in margins])
    pages = list(dict.fromkeys(line["page"] for line in lines))
    columns = []
    for number in pages:
        on_page = [line for line in lines if line["page"] == number]
        found = find_columns(on_page, page)
        if not found:
            continue
        previous = ""
        mixed = 0
        for line in (line for line in on_page if found["top"] <= line["y"] <= found["bottom"]):
            left = any(s["end"] <= found["gutter"] for s in line["segments"])
            side = (
                "both"
                if left and any(s["x"] >= found["gutter"] for s in line["segments"])
                else "left"
                if left
                else "right"
            )
            if side == "both" or (previous and side != previous):
                mixed += 1
            previous = side
        columns.append({"page": number, "mixed": mixed})
    return {"size": size, "margins": margins, "lines": lines, "columns": columns}


HEADING_KINDS = [
    (
        "experience",
        re.compile(
            r"^((work|professional|research|industry|relevant) )?(experience|employment( history)?"
            r"|work history|internships?)$",
            re.IGNORECASE,
        ),
    ),
    (
        "education",
        re.compile(
            r"^(education|academics?|academic (background|details|qualifications)|qualifications)$",
            re.IGNORECASE,
        ),
    ),
    (
        "skills",
        re.compile(
            r"^((technical|key|core|relevant) )?skills( and \w+)?$|^(technologies|tech stack"
            r"|technical expertise|(core )?competencies)$",
            re.IGNORECASE,
        ),
    ),
    (
        "projects",
        re.compile(r"^((personal|academic|key|selected|side|technical) )?projects$", re.IGNORECASE),
    ),
    (
        "summary",
        re.compile(
            r"^((professional|career) )?(summary|profile|objective)$|^about( me)?$", re.IGNORECASE
        ),
    ),
    (
        "other",
        re.compile(
            r"^((awards|honou?rs|achievements|certifications?|publications|courses|coursework|languages"
            r"|interests|hobbies|activities|leadership|references|training|volunteering|links)( and \w+)?"
            r"|profile links|relevant coursework|volunteer experience|extra ?curricular( activities)?"
            r"|positions? of responsibility|open source( contributions| projects)?)$",
            re.IGNORECASE,
        ),
    ),
]


def heading_text(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def known_kind(text: str) -> str | None:
    text = heading_text(text)
    return next((kind for kind, pattern in HEADING_KINDS if pattern.match(text)), None)


def is_heading(line: dict, size: float) -> bool:
    text = re.sub(r":$", "", line["text"])
    if (
        line["bullet"]
        or len(line["segments"]) != 1
        or len(text) > 40
        or len(text.split(" ")) > 5
        or re.search(r"[@\d,.:]", text)
    ):
        return False
    if known_kind(text):
        return True
    letters = re.sub(r"[^A-Za-z]", "", text)
    return (len(letters) >= 4 and letters == letters.upper()) or line["height"] >= size * 1.15


MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
POINT = rf"(?:{MONTH}\s*'?\d{{2,4}}|\d{{1,2}}[/.-](?:19|20)?\d{{2}}|(?:19|20)\d{{2}})"
DATES = re.compile(
    rf"\b{POINT}"
    rf"(?:\s*(?:-|\u2013|\u2014|to)\s*(?:{POINT}|present|current|now|ongoing|till date))?",
    re.IGNORECASE,
)

PLACES = re.compile(
    "^(india|remote|hybrid|bengaluru|bangalore|mumbai|delhi|new delhi|gurugram|gurgaon|noida"
    "|hyderabad|chennai|pune|kolkata|ahmedabad|jaipur|chandigarh|kochi|indore|lucknow|bhopal"
    "|nagpur|surat|coimbatore|mysuru|mysore|trivandrum|thiruvananthapuram|bhubaneswar|patna|goa"
    "|vadodara|visakhapatnam|singapore|london|dubai|new york|san francisco|seattle|berlin"
    "|toronto)$",
    re.IGNORECASE,
)
CITY_REGION = re.compile(r"^[A-Z][A-Za-z .]+, ?[A-Z][A-Za-z .]+$")


def is_place(text: str) -> bool:
    return bool(PLACES.match(text) or CITY_REGION.match(text))


TITLE_WORDS = re.compile(
    r"\b(intern|engineer|developer|sde|swe|manager|analyst|lead|designer|consultant|associate"
    r"|scientist|architect|founder|head|director|officer|executive|specialist|coordinator"
    r"|researcher|assistant|trainee|fellow|president|member|volunteer|programmer|administrator"
    r"|strategist|partner|vp|cto|ceo|teaching)\b",
    re.IGNORECASE,
)


def job_from(header: list[dict]) -> dict:
    found: str | None = None
    pieces: list[str] = []
    for segment in (segment for line in header for segment in line["segments"]):
        match = DATES.search(segment["text"])
        if match and not found:
            found = re.sub(r"\s*[\u2013\u2014]\s*", " - ", match.group(0))
        rest = segment["text"].replace(match.group(0), " ", 1) if match else segment["text"]
        for piece in re.split(r"\s+(?:\||\u00b7|@|at|-|\u2013|\u2014)\s+|,\s+|\s*\|\s*", rest):
            clean = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9.)]+$", "", piece)
            if clean and not is_place(clean):
                pieces.append(clean)
    title = next((piece for piece in pieces if TITLE_WORDS.search(piece)), None)
    others = [piece for piece in pieces if piece != title]
    if title:
        return {"title": title, "company": others[0] if others else None, "dates": found}
    return {
        "title": others[1] if len(others) > 1 else None,
        "company": others[0] if others else None,
        "dates": found,
    }


def parse_jobs(lines: list[dict]) -> list[dict]:
    """Each job is one or two header lines (title, company, dates) followed by bullets."""
    jobs: list[dict] = []
    xs = [line["x"] for line in lines if not line["bullet"]]
    left = min(xs) if xs else 0
    header: list[dict] = []
    in_body = False

    def flush():
        nonlocal header
        if header:
            jobs.append(job_from(header))
        header = []

    for line in lines:
        starts_job = bool(DATES.search(line["text"])) or line["segments"][0]["bold"]
        if line["bullet"] or line["x"] > left + 4:
            flush()
            in_body = True
        elif (
            header
            and len(header) < 2
            and not (DATES.search(header[0]["text"]) and DATES.search(line["text"]))
        ):
            header.append(line)
        else:
            flush()
            if starts_job or not in_body:
                header.append(line)
    flush()
    return jobs


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LINK_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*"
    r"\.(?:com|in|dev|io|org|net|me|co|ai|app|xyz|tech|site)\b(?:/[^\s|,]*)?",
    re.IGNORECASE,
)


def parse_items(items: list[dict], page: dict) -> dict:
    parsed = layout(items, page)
    size = parsed["size"]
    lines = parsed["lines"]

    first_heading = next(
        (
            index
            for index, line in enumerate(lines)
            if is_heading(line, size) and known_kind(line["text"])
        ),
        -1,
    )
    top = [
        line for line in lines[: first_heading if first_heading != -1 else 6] if line["page"] == 1
    ]

    def word_count(text: str) -> int:
        collapsed = re.sub(r"\b([A-Za-z]) (?=[A-Za-z]\b)", r"\1", text)
        return len(collapsed.split(" "))

    best = None
    for line in top:
        for segment in line["segments"]:
            if (
                re.match(r"^[A-Za-z][A-Za-z.' -]+$", segment["text"])
                and word_count(segment["text"]) <= 4
                and not known_kind(segment["text"])
            ) and (not best or segment["height"] > best["segment"]["height"]):
                best = {"line": line, "segment": segment}

    sections: list[dict] = []
    intro: list[dict] = []
    for index, line in enumerate(lines):
        if first_heading is not None and index >= first_heading and is_heading(line, size):
            heading = re.sub(r":$", "", line["text"])
            sections.append(
                {"heading": heading, "kind": known_kind(heading), "lines": [], "body": []}
            )
        else:
            section = sections[-1] if sections else None
            if section:
                section["lines"].append(line["text"])
                section["body"].append(line)
            else:
                intro.append(line)

    all_text = "\n".join(
        " | ".join(segment["text"] for segment in line["segments"]) for line in lines
    )
    email = EMAIL_RE.search(all_text)
    phone = next(
        (
            match
            for match in re.findall(r"\+?\d[\d ().-]{8,16}\d", all_text)
            if 10 <= len(re.sub(r"\D", "", match)) <= 13
        ),
        None,
    )
    links = list(dict.fromkeys(LINK_RE.findall(re.sub(EMAIL_RE, " ", all_text))))
    location = next(
        (
            re.sub(r"^[^A-Za-z]+", "", piece).strip()
            for line in intro
            for segment in line["segments"]
            for piece in re.split(r"\s*[|\u2022\u00b7]\s*", segment["text"])
            if is_place(re.sub(r"^[^A-Za-z]+", "", piece).strip())
        ),
        None,
    )

    jobs = [
        job
        for section in sections
        if section["kind"] == "experience" and section["body"]
        for job in parse_jobs(section["body"])
    ]
    return {
        "name": best["segment"]["text"] if best else None,
        "email": email.group(0) if email else None,
        "phone": phone,
        "location": location,
        "links": links,
        "sections": [
            {"heading": section["heading"], "kind": section["kind"], "lines": section["lines"]}
            for section in sections
        ],
        "jobs": jobs,
        "readingOrderIssues": sum(column["mixed"] for column in parsed["columns"]),
    }
