"""Parse quality report, ported from modules/ats/parser/quality.ts."""

from __future__ import annotations

import re

from .extract import ICON_FONT
from .parse import layout

Expected = dict | None

SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")
UNREADABLE = re.compile(r"[\ue000-\uf8ff\ufffd]")


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9@]", "", text.lower())


def _same(found: str | None, expected: str) -> bool:
    if not found:
        return False
    a = norm(found)
    b = norm(expected)
    return b in a and len(a) <= len(b) * 2


def same_company(found: str | None, expected: str) -> bool:
    if _same(found, expected):
        return True
    trimmed = re.sub(r",[^,]*$", "", expected)
    if trimmed == expected:
        return False
    return _same(found, trimmed)


def same_phone(found: str | None, expected: str) -> bool:
    if not found:
        return False
    return re.sub(r"\D", "", found)[-10:] == re.sub(r"\D", "", expected)[-10:]


def plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def _score_job(found: dict, job: dict) -> int:
    score = 0
    if job.get("title") and _same(found.get("title"), job["title"]):
        score += 1
    if job.get("company") and same_company(found.get("company"), job["company"]):
        score += 1
    return score


def compare(parsed: dict, expected: Expected) -> list[dict]:
    fields: list[dict] = []

    def add(pk_id: str, label: str, found: str | None, wanted: str | None, ok: bool):
        fields.append(
            {
                "id": pk_id,
                "label": label,
                "found": found,
                "expected": wanted,
                "ok": ok,
            }
        )

    if expected.get("name"):
        add(
            "name",
            "Name",
            parsed["name"],
            expected["name"],
            _same(parsed["name"], expected["name"]),
        )
    if expected.get("email"):
        add(
            "email",
            "Email",
            parsed["email"],
            expected["email"],
            _same(parsed["email"], expected["email"]),
        )
    if expected.get("phone"):
        add(
            "phone",
            "Phone",
            parsed["phone"],
            expected["phone"],
            same_phone(parsed["phone"], expected["phone"]),
        )
    for kind in expected.get("sectionKinds") or []:
        section = next((s for s in parsed["sections"] if s["kind"] == kind), None)
        add(
            f"section.{kind}",
            f"{kind[0].upper()}{kind[1:]} section",
            section["heading"] if section else None,
            kind,
            section is not None,
        )
    for index, job in enumerate(expected.get("jobs") or []):
        best: dict | None = None
        for found in parsed["jobs"]:
            if not best or _score_job(found, job) > _score_job(best, job):
                best = found
        n = index + 1
        if job.get("title"):
            add(
                f"job{n}.title",
                f"Job {n} title",
                best["title"] if best else None,
                job["title"],
                _same(best["title"] if best else None, job["title"]),
            )
        if job.get("company"):
            add(
                f"job{n}.company",
                f"Job {n} company",
                best["company"] if best else None,
                job["company"],
                same_company(best["company"] if best else None, job["company"]),
            )
    return fields


def parse_quality(
    parsed: dict,
    items: list[dict],
    page: dict,
    expected: Expected = None,
) -> dict:
    found_layout = layout(items, page)
    margins = found_layout["margins"]
    columns = found_layout["columns"]
    if expected:
        fields = compare(parsed, expected)
    else:
        fields = [
            {
                "id": pk_id,
                "label": label,
                "found": found,
                "expected": None,
                "ok": found is not None,
            }
            for pk_id, label, found in [
                ("name", "Name", parsed["name"]),
                ("email", "Email", parsed["email"]),
                ("phone", "Phone", parsed["phone"]),
                ("location", "Location", parsed["location"]),
            ]
        ]
    issues: list[dict] = []

    margin_text = " ".join(item["text"] for item in margins)
    missing = [field for field in ("email", "phone") if not parsed[field]]
    in_margins = [
        field
        for field in missing
        if (
            re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", margin_text)
            if field == "email"
            else re.search(r"\d[\d ().-]{8,}\d", margin_text)
        )
    ]
    if in_margins:
        issues.append(
            {
                "id": "contact",
                "label": "Contact details in the main text",
                "status": "fail",
                "detail": f"Your {' and '.join(in_margins)} only appear{'s' if len(in_margins) == 1 else ''} "
                "in the page header or footer.",
                "fix": "Move your email and phone into the main body; many ATS drop page headers.",
            }
        )
    elif missing:
        issues.append(
            {
                "id": "contact",
                "label": "Contact details in the main text",
                "status": "warn" if parsed["email"] else "fail",
                "detail": f"No {' or '.join(missing)} could be read from your resume.",
                "fix": "Add your email and phone as plain text near your name, not as an image or icon link.",
            }
        )
    else:
        issues.append(
            {
                "id": "contact",
                "label": "Contact details in the main text",
                "status": "pass",
                "detail": f"Read {parsed['email']} and {parsed['phone']} from the main text.",
                "fix": None,
            }
        )

    mixed = parsed["readingOrderIssues"]
    if columns or mixed:
        issues.append(
            {
                "id": "columns",
                "label": "Columns and reading order",
                "status": "fail" if mixed >= 5 else "warn",
                "detail": f"Your resume uses columns. Read top to bottom and left to right, "
                f"{plural(mixed, 'line')} mix or jump between columns, so sections get jumbled.",
                "fix": "Use a single-column layout so every ATS reads each section in order.",
            }
        )
    else:
        issues.append(
            {
                "id": "columns",
                "label": "Columns and reading order",
                "status": "pass",
                "detail": "Single column. The text reads top to bottom in the right order.",
                "fix": None,
            }
        )

    glyphs = sum(len(UNREADABLE.findall(item["text"])) for item in items)
    icon_items = [item for item in items if ICON_FONT.search(item.get("fontName") or "")]
    icon_fonts = list(
        dict.fromkeys(SUBSET_PREFIX.sub("", item.get("fontName") or "") for item in icon_items)
    )
    bad = glyphs + len(icon_items)
    issues.append(
        {
            "id": "glyphs",
            "label": "Icons and unreadable characters",
            "status": "pass" if bad == 0 else "fail" if bad >= 10 else "warn",
            "detail": "Every character is readable text."
            if bad == 0
            else f"Found {plural(bad, 'icon or unreadable character')}"
            + (f" (icon fonts: {', '.join(icon_fonts)})" if icon_fonts else "")
            + ". An ATS reads these as junk characters or drops them.",
            "fix": None
            if bad == 0
            else "Replace icons with plain words like Email, Phone or LinkedIn, or remove them.",
        }
    )

    known = [s for s in parsed["sections"] if s["kind"]]
    unknown = [s["heading"] for s in parsed["sections"] if not s["kind"]]
    absent = [
        kind
        for kind in (expected or {}).get("sectionKinds") or []
        if not any(s["kind"] == kind for s in parsed["sections"])
    ]
    issues.append(
        {
            "id": "sections",
            "label": "Standard section headings",
            "status": "fail" if not known else "warn" if absent or unknown else "pass",
            "detail": "No standard section headings like Experience, Education or Skills were found."
            if not known
            else " ".join(
                part
                for part in [
                    f"Found {', '.join(s['heading'] for s in known)}.",
                    f"Could not find your {', '.join(absent)} section." if absent else "",
                    f"These headings are not standard: {', '.join(unknown)}." if unknown else "",
                ]
                if part
            ),
            "fix": None
            if known and not absent and not unknown
            else "Use plain headings like Experience, Education, Skills and Projects on their own line.",
        }
    )

    has_experience = any(s["kind"] == "experience" for s in parsed["sections"])
    partial = [
        job for job in parsed["jobs"] if not job["title"] or not job["company"] or not job["dates"]
    ]
    if not has_experience:
        issues.append(
            {
                "id": "jobs",
                "label": "Job titles, companies and dates",
                "status": "fail" if (expected or {}).get("jobs") else "pass",
                "detail": "Your experience section could not be found, so no jobs were read."
                if (expected or {}).get("jobs")
                else "No experience section, nothing to check.",
                "fix": "Put your jobs under a heading named Experience."
                if (expected or {}).get("jobs")
                else None,
            }
        )
    elif not parsed["jobs"]:
        issues.append(
            {
                "id": "jobs",
                "label": "Job titles, companies and dates",
                "status": "fail",
                "detail": "Found an experience section but could not read any job in it.",
                "fix": "Start each job with a line holding the title, company and dates, then the bullets.",
            }
        )
    else:
        issues.append(
            {
                "id": "jobs",
                "label": "Job titles, companies and dates",
                "status": "warn" if partial else "pass",
                "detail": f"Read {plural(len(parsed['jobs']), 'job')}: "
                + "; ".join(
                    f"{job['title'] or 'no title'} at {job['company'] or 'no company'} ({job['dates'] or 'no dates'})"
                    for job in parsed["jobs"]
                )
                + ".",
                "fix": "Give each job its title, company and dates (like Jun 2024 - Aug 2024) on its first one or two lines."
                if partial
                else None,
            }
        )

    first_word = parsed["name"].split(" ")[0] if parsed["name"] else None
    name_item = (
        next((item for item in items if item["page"] == 1 and first_word in item["text"]), None)
        if first_word
        else None
    )
    name_off = bool((expected or {}).get("name")) and not _same(parsed["name"], expected["name"])
    if not parsed["name"] or name_off:
        issues.append(
            {
                "id": "name",
                "label": "Name at the top",
                "status": "fail",
                "detail": f'Your name was read as "{parsed["name"]}".'
                if parsed["name"]
                else "No name was found at the top of the first page.",
                "fix": "Put your full name alone on the first line, in larger text than the rest.",
            }
        )
    elif re.match(r"^([A-Za-z] )+[A-Za-z]$", parsed["name"]):
        issues.append(
            {
                "id": "name",
                "label": "Name at the top",
                "status": "warn",
                "detail": f'Your name is letter-spaced ("{parsed["name"]}"), so some ATS read it as single letters.',
                "fix": "Set your name without extra letter spacing.",
            }
        )
    elif name_item and name_item["y"] > page["height"] * 0.25:
        issues.append(
            {
                "id": "name",
                "label": "Name at the top",
                "status": "warn",
                "detail": f'Found "{parsed["name"]}" but it is not near the top of the page.',
                "fix": "Move your name to the very top of the first page.",
            }
        )
    else:
        issues.append(
            {
                "id": "name",
                "label": "Name at the top",
                "status": "pass",
                "detail": f'Read your name as "{parsed["name"]}".',
                "fix": None,
            }
        )

    chars = sum(len(re.sub(r"\s", "", item["text"])) for item in items)
    pages = max([item["page"] for item in items], default=0) or 1
    issues.append(
        {
            "id": "density",
            "label": "Readable text",
            "status": "fail" if chars < 200 else "warn" if chars / pages < 300 else "pass",
            "detail": f"Only {plural(chars, 'character')} of text could be read. This looks like a scanned or image PDF."
            if chars < 200
            else f"{chars} characters of text read across {plural(pages, 'page')}.",
            "fix": "Export your resume as a PDF from a text editor or our builder, not as a scan or image."
            if chars < 200
            else (
                "Some pages have very little text. Check that nothing is an image."
                if chars / pages < 300
                else None
            ),
        }
    )

    return {
        "parseRate": (
            len([f for f in fields if f["ok"]]) / len(fields) if expected and fields else None
        ),
        "fields": fields,
        "issues": issues,
        "parsed": parsed,
    }
