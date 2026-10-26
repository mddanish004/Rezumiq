"""Resume import and AI draft, ported from imports.service.ts.

The old backend sent the whole PDF to the model so it could see layout and bold. Here the
PDF is read with the same pdfminer pipeline the ATS parser uses, its text and bold hints
go to the model as text, and a rule-based pass restores lines the model left out.
"""

from __future__ import annotations

from ai.generate import generate_structured
from ai.models import AiRun
from ai.runs import record_run, reserve_run
from api.common.errors import AppError
from ats.parser.extract import extract_text_items
from ats.parser.parse import parse_items, to_lines
from imports.coverage import restore_missed_lines
from imports.extraction import EXTRACTION_SCHEMA, apply_bold, normalize_extraction, pdf_bold_phrases
from imports.schemas import MAX_IMPORT_TEXT
from uploads.service import read_upload
from usage.quotas import assert_ai_quota

MAX_IMPORT_PAGES = 4

SYSTEM = """You extract resumes into structured JSON.
Rules:
- Copy facts exactly as written. Never invent, infer or embellish employers, dates, numbers or skills.
- Keep each bullet's wording, without its bullet symbol ("•", "-"). Wrap text that is bold in the source in
  **double asterisks**.
- Dates: "YYYY-MM" when the month is known, otherwise "YYYY"; use "present" for ongoing roles. Use null when unknown.
- Section types: summary (a summary, profile, objective or about paragraph, in "text"), experience (jobs,
  internships), education, projects, skills (grouped lists like "Languages: ..."), links (a bare list of profile
  links such as LeetCode or Codeforces), list (achievements, certifications, positions of responsibility,
  anything else).
- The headline is only a short title under the name. A paragraph about the person is a summary section.
- Publications, talks, awards and certifications are list sections, not projects.
- A single date (a graduation year, Class X or XII) is the end date; leave start null.
- Never split one item at a comma ("Winner, Smart India Hackathon" stays one title). Words that only name a link
  ("Verify", "Live", "Code", "PDF") are not content.
- In list sections, every item is its own entry. For an item written as "Name - description" (or with a colon or
  long dash), put the name in title and the description in subtitle; otherwise the whole item is the title.
- A project's "Tech Stack:" or "Technologies:" line goes in technologies, not in bullets.
- Link labels are short names like "LinkedIn", "GitHub" or "Portfolio", never the URL itself.
- Keep the source's section order and titles.
- Fill every field; use null or [] when something doesn't apply."""

TEX_LABEL = "LaTeX source (ignore formatting commands, extract the content)"

DRAFT_SYSTEM = """You write a resume from a person's own rough notes, as structured JSON.
Rules:
- Use only facts from the notes: employers, schools, dates, numbers, tools and results. Never invent any of them, and
  never add a number, metric or skill that isn't in the notes.
- Turn each rough note into a concise resume bullet: start with a strong past-tense verb, say what was built or done and
  its result, ideally in one line. Wrap the one key technology or result of a bullet in **double asterisks**.
- The headline is a short title for the target role, like "Backend Engineer".
- Add a summary section of two sentences only when the notes give enough to say something specific about the person.
- Group skills by kind (Languages, Frameworks, Tools and so on), using only tools the notes mention.
- Education goes in its fields (institution, degree, field, score, dates), with no bullets unless the notes add
  something more, like coursework or a thesis.
- Project and job details go in bullets; leave subtitle and title null for them.
- In list sections, every achievement or certification is its own entry with its text as the title and no bullets.
- Put education first for students and freshers, experience first for everyone else.
- Dates: "YYYY-MM" when the month is known, otherwise "YYYY"; "present" for ongoing roles; null when not given.
- Section types: summary (in "text"), experience, education, projects, skills, links, list (achievements,
  certifications, positions of responsibility).
- Fill every field; use null or [] when something doesn't apply."""


def _prompt_from_upload(
    user_id, upload_id
) -> tuple[str, list[dict] | None, dict | None, list[str]]:
    info, body = read_upload(user_id, upload_id)
    if info["kind"] == "pdf":
        try:
            extracted = extract_text_items(body)
        except Exception:  # noqa: BLE001
            raise AppError(
                422,
                "PDF_UNREADABLE",
                "This PDF couldn't be read. Export it again, or paste its text.",
            ) from None
        if extracted["pageCount"] > MAX_IMPORT_PAGES:
            raise AppError(
                400,
                "PDF_TOO_LONG",
                f"Import works on resumes up to {MAX_IMPORT_PAGES} pages. This PDF has {extracted['pageCount']}.",
            )
        text = "\n".join(line["text"] for line in to_lines(extracted["items"]))
        prompt = f"Extract this resume:\n\n<resume>\n{text}\n</resume>"
        bold = pdf_bold_phrases(extracted["items"])
        if bold:
            prompt += (
                "\n\nThese phrases are bold in the PDF. Wherever one appears inside a bullet, summary or "
                "list item, wrap it in **double asterisks**:\n"
                + "\n".join(f"- {phrase}" for phrase in bold)
            )
        return prompt, extracted["items"], extracted, bold

    text = body.decode("utf-8", "replace")
    if len(text) > MAX_IMPORT_TEXT:
        raise AppError(
            400,
            "FILE_TOO_LONG",
            f"Import works on files up to {MAX_IMPORT_TEXT:,} characters. This one is longer.",
        )
    label = TEX_LABEL if info["kind"] == "tex" else "text"
    return f"Extract this resume from its {label}:\n\n<resume>\n{text}\n</resume>", None, None, []


def create_import(user_id, body: dict) -> dict:
    assert_ai_quota(user_id, "import")
    pdf_items = None
    extracted = None
    bold_phrases: list[str] = []
    if body.get("upload_id") is not None:
        prompt, pdf_items, extracted, bold_phrases = _prompt_from_upload(user_id, body["upload_id"])
    elif body.get("tex_source") is not None:
        prompt = f"Extract this resume from its {TEX_LABEL}:\n\n<resume>\n{body['tex_source']}\n</resume>"
    else:
        prompt = f"Extract this resume:\n\n<resume>\n{body['text']}\n</resume>"

    run_id = reserve_run(user_id, "import", AiRun.Step.IMPORT)
    try:
        result = generate_structured(prompt, tier="fast", system=SYSTEM, schema=EXTRACTION_SCHEMA)
    except Exception:
        record_run(user_id, run_id, step=AiRun.Step.IMPORT, error=True)
        raise
    ai_run_id = record_run(user_id, run_id, step=AiRun.Step.IMPORT, result=result)

    content = apply_bold(normalize_extraction(result.get("data") or {}), bold_phrases)
    missed = []
    if pdf_items is not None and extracted is not None:
        try:
            parsed = parse_items(
                pdf_items, {"width": extracted["pageWidth"], "height": extracted["pageHeight"]}
            )
            coverage = restore_missed_lines(content, parsed)
            content, missed = coverage["content"], coverage["missed"]
        except Exception:  # noqa: BLE001
            missed = []
    return {"content": content, "aiRunId": ai_run_id or run_id, "missed": missed}


def create_draft(user_id, body: dict) -> dict:
    """Writes a first resume from notes for someone starting from nothing."""
    assert_ai_quota(user_id, "draft")
    run_id = reserve_run(user_id, "draft", AiRun.Step.DRAFT)
    prompt = f"Target role: {body['role']}\n\nNotes:\n<notes>\n{body['notes']}\n</notes>"
    try:
        result = generate_structured(
            prompt, tier="smart", system=DRAFT_SYSTEM, schema=EXTRACTION_SCHEMA
        )
    except Exception:
        record_run(user_id, run_id, step=AiRun.Step.DRAFT, error=True)
        raise
    ai_run_id = record_run(user_id, run_id, step=AiRun.Step.DRAFT, result=result)

    content = normalize_extraction(result.get("data") or {})
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(id=user_id).first()
    if user and not user.is_guest:
        content["basics"]["name"] = content["basics"].get("name") or user.name
        content["basics"]["email"] = content["basics"].get("email") or user.email
    return {"content": content, "aiRunId": ai_run_id or run_id, "missed": []}
