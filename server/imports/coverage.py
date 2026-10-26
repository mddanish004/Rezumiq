"""Restore PDF lines the AI left out, ported from coverage.ts."""

from __future__ import annotations

import re

from imports.extraction import short_id
from resumes.content import plain_text

DATE_WORDS = re.compile(
    r"\b(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|"
    r"oct|october|nov|november|dec|december|present|current|now)\b|\b(19|20)\d{2}\b",
    re.IGNORECASE,
)


def _words(text: str) -> list[str]:
    """Dates are dropped first: the AI rewrites "May 2025" as "2025-05", which isn't a missed line."""
    return [word for word in re.split(r"[^A-Za-z0-9]+", DATE_WORDS.sub(" ", text.lower())) if word]


def _pairs(text: str) -> list[str]:
    words = _words(text)
    return [f"{words[index]} {words[index + 1]}" for index in range(len(words) - 1)]


def _strings(value) -> list[str]:
    """Every string in the content, plus each entry's fields joined, because a PDF prints them on one line."""
    if isinstance(value, str):
        return [plain_text(value)]
    if isinstance(value, list):
        return [item for value_item in value for item in _strings(value_item)]
    if isinstance(value, dict):
        fields = [(key, item) for key, item in value.items() if key != "id"]
        own = [item for key, field in fields if key != "bullets" for item in _strings(field)]
        everything = [item for _, field in fields for item in _strings(field)]
        return [*everything, " ".join(own)]
    return []


LABEL_WORDS = {
    "degree",
    "institution",
    "score",
    "year",
    "years",
    "cgpa",
    "gpa",
    "grade",
    "percentage",
    "board",
    "duration",
    "company",
    "role",
    "position",
    "location",
    "date",
    "dates",
}


def _share(line: str, known: set[str]) -> float | None:
    if all(word in LABEL_WORDS for word in _words(line)):
        return None
    pairs = _pairs(line)
    if len(pairs) < 2:
        return None
    return sum(1 for pair in pairs if pair in known) / len(pairs)


SECTION_TYPES = {
    "experience": "experience",
    "education": "education",
    "projects": "projects",
    "skills": "skills",
    "summary": "summary",
    "other": "list",
}
MAX_BULLETS = 20


def restore_missed_lines(content: dict, parsed: dict) -> dict:
    known = {pair for text in _strings(content) for pair in _pairs(text)}
    missed = []
    next_content = {**content, "sections": [dict(section) for section in content["sections"]]}

    if not next_content["basics"].get("email") and parsed.get("email"):
        next_content["basics"]["email"] = parsed["email"]
    if not next_content["basics"].get("phone") and parsed.get("phone"):
        next_content["basics"]["phone"] = parsed["phone"]

    for section in parsed.get("sections") or []:
        target = next(
            (
                s
                for s in next_content["sections"]
                if s["type"] == SECTION_TYPES.get(section.get("kind") or "other")
            ),
            None,
        )
        entries = target["entries"] if target and "entries" in target else []
        current = entries[0] if entries else None
        for line in section.get("lines") or []:
            covered = _share(line, known)
            if covered is None:
                continue
            if covered >= 0.5:
                entry_pairs = [
                    {pair for text in _strings(entry) for pair in _pairs(text)} for entry in entries
                ]
                index = next(
                    (i for i, pairs in enumerate(entry_pairs) if (_share(line, pairs) or 0) >= 0.5),
                    -1,
                )
                if index != -1:
                    current = entries[index]
                continue
            text = re.sub(r"^[\u2022\u25cf\u25aa\u25e6\-\u2013*]\s*", "", line).strip()
            placed = bool(current) and len(current["bullets"]) < MAX_BULLETS
            if placed:
                current["bullets"].append({"id": short_id(), "text": text[:600], "hidden": True})
            missed.append({"text": text, "placed": placed})

    next_content["sections"] = _in_pdf_order(next_content["sections"], parsed.get("sections") or [])
    return {"content": next_content, "missed": missed}


def _plain(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def _in_pdf_order(sections: list[dict], headings: list[dict]) -> list[dict]:
    """The model doesn't always keep the source's section order, so the PDF's own headings decide it."""
    previous = -1
    ranked = []
    for index, section in enumerate(sections):
        found = next(
            (
                i
                for i, heading in enumerate(headings)
                if _plain(heading.get("heading")) == _plain(section["title"])
            ),
            -1,
        )
        if found == -1 and section["type"] != "list":
            found = next(
                (
                    i
                    for i, heading in enumerate(headings)
                    if heading.get("kind") and SECTION_TYPES.get(heading["kind"]) == section["type"]
                ),
                -1,
            )
        if found != -1:
            previous = found
        ranked.append((found if found != -1 else previous + 0.5, index, section))
    return [section for _, _, section in sorted(ranked, key=lambda item: (item[0], item[1]))]
