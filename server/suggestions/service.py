"""Suggestions, ported from modules/suggestions (LLM calls via Groq)."""

from __future__ import annotations

import json
import uuid

from ai.generate import generate_structured
from ai.models import AiRun
from ai.pricing import known_cost_usd_micros
from ai.runs import record_run, reserve_run
from api.common.errors import AppError, NotFoundError
from resumes import service as resumes_service
from resumes.content import ResumeContent
from suggestions.operations import apply_operations, fact_text, is_applicable, unverified_terms
from usage.quotas import assert_ai_quota

SUGGESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "update_bullet",
                            "add_bullet",
                            "update_headline",
                            "update_summary",
                            "set_hidden",
                            "set_space_after",
                            "reorder",
                            "update_skills",
                        ],
                    },
                    "targetId": {"type": ["string", "null"]},
                    "text": {"type": ["string", "null"]},
                    "hidden": {"type": ["boolean", "null"]},
                    "points": {"type": ["integer", "null"]},
                    "orderedIds": {"type": ["array", "null"], "items": {"type": "string"}},
                    "items": {"type": ["array", "null"], "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "required": [
                    "type",
                    "targetId",
                    "text",
                    "hidden",
                    "points",
                    "orderedIds",
                    "items",
                    "reason",
                ],
            },
        },
    },
    "required": ["summary", "operations"],
}

CODE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "texSource": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["summary", "texSource", "reason"],
}

RULES = """You propose edits to a resume as JSON operations.

Operation types:
- update_bullet: targetId is the bullet id, text is the new text.
- add_bullet: targetId is the bullet the new one goes after, text is the new bullet.
- update_headline: text is the new headline.
- update_summary: targetId is the summary section id, text is the rewritten paragraph.
- set_hidden: targetId is a section, entry or bullet id, hidden hides or shows it.
- set_space_after: targetId is a section or entry id, points is -8 to 24 (0 resets).
- reorder: targetId is a section id, entry id, skill group parent or "sections"; orderedIds lists every child id in the new order.
- update_skills: targetId is the skill group id, items is the new list.

Rules:
- Never invent employers, titles, dates, numbers, metrics, tools or skills. You may rephrase, reorder, emphasise with **bold**, or hide content.
- Keep bullets to one or two lines, under 200 characters, starting with a strong action verb, no first person.
- To split a long bullet, update it and add the rest after it. New bullets use only facts already present.
- A rewritten bullet is never longer than the one it replaces unless that one was under 120 characters.
- For spacing requests use set_space_after, never a text edit.
- Text like [the words](https://address) is a link on those words. Keep every link and its address exactly as written.
- Refer to items only by the ids given in the JSON. Propose only changes that clearly help.
- Text like [email 1] or [company 2] is a private placeholder. Copy it exactly; never guess what it stands for."""


def _to_op(raw, idx):
    op_type = raw.get("type")
    target = raw.get("targetId")
    op = {"type": op_type, "id": f"op{idx}", "reason": raw.get("reason") or "", "flags": []}
    if op_type == "update_bullet":
        op["bulletId"] = target
        op["text"] = raw.get("text") or ""
    elif op_type == "add_bullet":
        op["afterBulletId"] = target
        op["text"] = raw.get("text") or ""
    elif op_type == "update_headline":
        op["text"] = raw.get("text") or ""
    elif op_type == "update_summary":
        op["targetId"] = target
        op["text"] = raw.get("text") or ""
    elif op_type == "set_hidden":
        op["targetId"] = target
        op["hidden"] = bool(raw.get("hidden"))
    elif op_type == "set_space_after":
        op["targetId"] = target
        op["points"] = int(raw.get("points") or 0)
    elif op_type == "reorder":
        op["parentId"] = target
        op["orderedIds"] = raw.get("orderedIds") or []
    elif op_type == "update_skills":
        op["groupId"] = target
        op["items"] = raw.get("items") or []
    return op


def create_suggestion(user_id, resume_id, data) -> dict:

    resume = resumes_service.get_resume(user_id, resume_id)
    base_version = resume.get("head")
    if not base_version:
        raise NotFoundError("Version")
    content = base_version.get("content")

    job = None
    if data.get("jobId") or data.get("job_id"):
        from jobs import service as jobs_service

        job = jobs_service.get_job(user_id, data.get("jobId") or data.get("job_id"))

    user_key = None
    s_type = data.get("type", "edit")
    instruction = data.get("instruction") or data.get("instructions") or ""
    job_id = job["id"] if job else None
    kind = "tailor" if s_type == "tailor" else "edit"

    if s_type == "fix_compile":
        tex_source = base_version.get("tex_source")
        if not tex_source:
            raise AppError(422, "NOT_LATEX", "Compile fixes require a LaTeX resume")
        step = "fix_compile"
        assert_ai_quota(user_id, kind)
        run_id = reserve_run(user_id, kind, step)
        try:
            result = generate_structured(
                "Fix this LaTeX resume so it compiles. Return the complete document, changing only what is needed.\n\n"
                + tex_source[:60000],
                tier="smart",
                system="You fix LaTeX compile errors. Keep every resume fact unchanged. Reply with JSON.",
                schema=CODE_SCHEMA,
            )
        except Exception as exc:  # noqa: BLE001
            record_run(user_id, run_id, step=step, error=True)
            raise_app_error(exc)
        run_id = record_run(user_id, run_id, step=step, result=result)
        output = result.get("data")
        if not isinstance(output, dict) or not output.get("texSource"):
            raise AppError(
                502, "AI_BAD_OUTPUT", "The AI answer wasn't in the expected shape. Try again."
            )
        op = {
            "id": "op1",
            "type": "replace_source",
            "reason": output.get("reason") or "Compile fix",
            "flags": [],
            "texSource": output["texSource"],
        }
        return _store_suggestion(
            run_id,
            user_id,
            resume_id,
            job_id,
            base_version["id"],
            s_type,
            output.get("summary") or "Compile fix",
            [op],
        )

    step = "rewrite" if kind == "tailor" else "chat_edit"
    scoped = data.get("targetIds") or data.get("target_ids") or []
    allowed = _allowed_ids(content, scoped)
    if allowed is not None:
        prompt_scope = (
            "\n\nOnly change the content whose ids are listed here, and nothing else: "
            + ", ".join(sorted(allowed))
        )
    else:
        prompt_scope = ""

    if s_type == "tailor" and job:
        prompt = f"Tailor this resume for the job. Job: {job.get('raw_text', '')[:4000]}\n\nResume JSON:\n{json.dumps(content)[:12000]}\n\nInstructions: {instruction}"
    else:
        prompt = f"Apply this edit: {instruction}\n\nResume JSON:\n{json.dumps(content)[:12000]}"
    prompt += prompt_scope

    assert_ai_quota(user_id, kind)
    run_id = reserve_run(user_id, kind, step)
    try:
        result = generate_structured(
            prompt, tier="smart", system=RULES, user_key=user_key, schema=SUGGESTION_SCHEMA
        )
    except Exception as exc:  # noqa: BLE001
        record_run(user_id, run_id, step=step, error=True)
        raise_app_error(exc)
    run_id = record_run(user_id, run_id, step=step, result=result)
    data = result.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("operations"), list):
        raise AppError(
            502, "AI_BAD_OUTPUT", "The AI answer wasn't in the expected shape. Try again."
        )
    raw_ops = data["operations"]
    summary = data.get("summary") or "Suggested edits"
    facts = [fact_text(ResumeContent.model_validate(content))]

    ops = []
    for idx, raw in enumerate(raw_ops):
        op = _to_op(raw, idx + 1)
        if op["type"] == "update_summary":
            op["targetId"] = raw.get("targetId")
        if allowed is not None and not (_op_ids(op) & allowed):
            continue
        flags = []
        if op["type"] in ("update_bullet", "add_bullet", "update_headline", "update_summary"):
            flags = unverified_terms(op.get("text", ""), facts)
            flags = [f"Not found in your profile: {t}" for t in flags]
        if not is_applicable(content, op):
            continue
        op["flags"] = flags
        ops.append(op)

    return _store_suggestion(
        run_id, user_id, resume_id, job_id, base_version["id"], s_type, summary, ops
    )


def raise_app_error(exc: Exception):
    if "not configured" in str(exc).lower():
        raise AppError(503, "AI_NOT_CONFIGURED", "No AI provider configured") from None
    raise AppError(502, "AI_FAILED", "The AI request failed. Try again.") from None


def _op_ids(op: dict) -> set:
    return {
        value
        for key in ("bulletId", "afterBulletId", "targetId", "parentId", "groupId")
        if (value := op.get(key))
    }


def _allowed_ids(content: dict, targets: list) -> set | None:
    """A section target includes its entries, bullets and groups; an entry includes its bullets."""
    if not targets:
        return None
    allowed = set(targets)
    for _ in range(2):
        for section in content.get("sections", []):
            section_targeted = section.get("id") in allowed
            if section_targeted:
                allowed.update(g.get("id") for g in section.get("groups", []) if g.get("id"))
            for entry in section.get("entries", []):
                if section_targeted or entry.get("id") in allowed:
                    allowed.update(b.get("id") for b in entry.get("bullets", []) if b.get("id"))
    return allowed


def _store_suggestion(run_id, user_id, resume_id, job_id, base_version_id, s_type, summary, ops):
    run_id = uuid.UUID(run_id) if isinstance(run_id, str) else run_id
    AiRun.objects.filter(id=run_id).update(
        resume_id=resume_id,
        job_id=job_id,
        version_id=base_version_id,
        patch_ops={
            "type": s_type,
            "baseVersionId": str(base_version_id),
            "summary": summary,
            "operations": ops,
        },
    )
    run = AiRun.objects.get(id=run_id)
    return {
        "id": run.id,
        "type": s_type,
        "status": "pending",
        "baseVersionId": base_version_id,
        "appliedVersionId": None,
        "summary": summary,
        "operations": ops,
        "model": run.model,
        "byok": run.byok,
        "costUsdMicros": known_cost_usd_micros(
            run.cost_usd_micros, run.input_tokens, run.output_tokens
        ),
        "createdAt": run.created_at,
    }


def list_suggestions(user_id, resume_id) -> list[dict]:
    runs = AiRun.objects.filter(
        user_id=user_id, resume_id=resume_id, patch_ops__isnull=False
    ).order_by("-created_at")
    out = []
    for r in runs:
        po = r.patch_ops or {}
        out.append(
            {
                "id": r.id,
                "type": po.get("type"),
                "status": "applied" if r.accepted_op_ids else "pending",
                "baseVersionId": po.get("baseVersionId"),
                "appliedVersionId": r.version_id,
                "summary": po.get("summary", ""),
                "model": r.model,
                "byok": r.byok,
                "costUsdMicros": r.cost_usd_micros,
                "createdAt": r.created_at,
            }
        )
    return out


def get_suggestion(user_id, resume_id, suggestion_id) -> dict:
    try:
        r = AiRun.objects.get(id=suggestion_id, user_id=user_id, resume_id=resume_id)
    except AiRun.DoesNotExist:
        raise NotFoundError("Suggestion") from None
    po = r.patch_ops or {}
    ops = po.get("operations", [])
    return {
        "id": r.id,
        "type": po.get("type"),
        "status": "applied" if r.accepted_op_ids else "pending",
        "baseVersionId": po.get("baseVersionId"),
        "appliedVersionId": r.version_id,
        "summary": po.get("summary", ""),
        "operations": ops,
        "model": r.model,
        "byok": r.byok,
        "costUsdMicros": r.cost_usd_micros,
        "createdAt": r.created_at,
    }


def apply_suggestion(user_id, resume_id, suggestion_id, accepted_ids) -> dict:
    suggestion = get_suggestion(user_id, resume_id, suggestion_id)
    base_version_id = suggestion["baseVersionId"]
    _ = resumes_service.get_resume(user_id, resume_id)
    base_version = resumes_service.version_row_detail(user_id, resume_id, base_version_id)
    ops = [o for o in suggestion["operations"] if o["id"] in accepted_ids]

    from resumes.models import Resume

    resume_row = Resume.objects.get(id=resume_id, user_id=user_id)
    if any(op["type"] == "replace_source" for op in ops):
        tex_source = next(op.get("texSource") for op in ops if op["type"] == "replace_source")
        if not tex_source:
            raise AppError(422, "EMPTY_SOURCE", "The fixed LaTeX came back empty")
        version = resumes_service.append_version(
            resume_row, "ai", None, tex_source, label=None, semver=None
        )
    else:
        content = base_version.get("content")
        if not content:
            raise AppError(422, "NOT_STRUCTURED", "Suggestions require a structured resume")
        version = resumes_service.append_version(
            resume_row, "ai", apply_operations(content, ops), None, label=None, semver=None
        )
    run = AiRun.objects.get(id=suggestion_id)
    run.accepted_op_ids = accepted_ids
    run.version_id = version.id
    run.save(update_fields=["accepted_op_ids", "version_id"])
    new_version_detail = resumes_service.version_detail(version)
    return {
        "version": new_version_detail,
        "suggestion": get_suggestion(user_id, resume_id, suggestion_id),
    }
