"""ATS parser: PDF text extraction, resume structure parsing, quality report.

Port of modules/ats/parser/{extract,parse,quality}.js. Scoring consumes the
report as plain dicts, so the wire types stay loose like the TS version's.
"""

from __future__ import annotations

import re

from latex.compile import compile_tex
from resumes.content import ResumeContent
from templates.latex import visible_content

from .extract import extract_text_items
from .parse import parse_items
from .quality import parse_quality

PARSED_KINDS = {"experience", "education", "skills", "projects"}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def parse_pdf_items(items: list[dict], page: dict, expected: dict | None = None) -> dict | None:
    """Parse browser-extracted text items; any failure means scoring without it."""
    try:
        return parse_quality(parse_items(items, page), items, page, expected)
    except Exception:  # noqa: BLE001
        return None


def parse_tex(tex: str, expected: dict | None = None) -> dict | None:
    """Compiles the resume as it downloads and reads it back like an ATS."""
    try:
        compiled = compile_tex(tex)
        if not compiled.get("ok"):
            return None
        extracted = extract_text_items(compiled["pdf"])
        return parse_pdf_items(
            extracted["items"],
            {"width": extracted["pageWidth"], "height": extracted["pageHeight"]},
            expected,
        )
    except Exception:  # noqa: BLE001
        return None


def expected_fields(content: ResumeContent | dict) -> dict:
    """What the parser should read back from a structured resume: what the template prints."""
    if not isinstance(content, ResumeContent):
        content = ResumeContent.model_validate(content)
    visible = visible_content(content)
    shown = [
        section
        for section in visible.sections
        if len(
            section.groups
            if section.type == "skills"
            else section.links
            if section.type == "links"
            else [section.text]
            if section.type == "summary"
            else section.entries
        )
    ]
    return {
        "name": visible.basics.name or None,
        "email": visible.basics.email,
        "phone": visible.basics.phone,
        "sectionKinds": list(dict.fromkeys(s.type for s in shown if s.type in PARSED_KINDS)),
        "jobs": [
            {"title": entry.role, "company": entry.organization}
            for section in shown
            if section.type == "experience"
            for entry in section.entries
        ],
    }


def expected_from_text(text: str) -> dict | None:
    """LaTeX source has no fields, so only the email and phone found in its text are checked."""
    email = EMAIL.search(text or "")
    phone = re.search(
        r"\+?\d[\d ().-]{8,16}\d",
        re.sub(EMAIL, " ", text or ""),
    )
    if not email and not phone:
        return None
    return {
        **({"email": email.group(0)} if email else {}),
        **({"phone": phone.group(0)} if phone else {}),
    }
