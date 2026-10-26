"""Job lifecycle, ported from modules/jobs/jobs.service.ts."""

from __future__ import annotations

import hashlib
import urllib.request

from ai.generate import generate_structured
from ai.models import AiRun
from ai.runs import record_run, reserve_run
from api.common.errors import AppError, NotFoundError
from resumes.models import Job
from usage.quotas import assert_ai_quota

PARSED_JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": ["string", "null"]},
        "role": {"type": ["string", "null"]},
        "seniority": {
            "type": "string",
            "enum": ["intern", "entry", "mid", "senior", "lead", "unknown"],
        },
        "domain": {"type": ["string", "null"]},
        "mustHave": {"type": "array", "items": {"type": "string"}},
        "niceToHave": {"type": "array", "items": {"type": "string"}},
        "responsibilities": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "company",
        "role",
        "seniority",
        "domain",
        "mustHave",
        "niceToHave",
        "responsibilities",
        "keywords",
    ],
}

SYSTEM = """You extract structured requirements from job descriptions.
Copy requirements faithfully; don't add skills that aren't mentioned. Keep items short (1-5 words each).
Use null when the company or role isn't stated."""


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.lower().replace("  ", " ").strip().encode()).hexdigest()


def _fetch_job_text(url: str) -> str:
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="replace").strip()
    except Exception:  # noqa: BLE001
        text = ""
    if len(text) < 200:
        raise AppError(
            422,
            "JOB_URL_UNREADABLE",
            "Couldn't read that job page. Paste the job description text instead.",
        )
    return text[:30000]


def _summary(row: Job, latest_match=None) -> dict:
    return {
        "id": row.id,
        "company": row.company,
        "role": row.role,
        "source_url": row.source_url,
        "created_at": row.created_at,
        "latest_match": latest_match,
    }


def _ai_configured(user_id) -> bool:
    from django.conf import settings

    from ai_keys.service import has_user_ai_key

    if has_user_ai_key(user_id):
        return True
    return bool(
        {
            "groq": settings.GROQ_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "openrouter": settings.OPENROUTER_API_KEY,
        }.get(settings.AI_PROVIDER)
    )


def _parse(user_id, raw_text: str) -> dict | None:
    """A failed parse leaves the raw posting saved and usable; it can be retried."""
    if not _ai_configured(user_id):
        return None
    assert_ai_quota(user_id, "job")
    run_id = reserve_run(user_id, "job", AiRun.Step.JD_PARSE)
    try:
        result = generate_structured(
            f"Extract the requirements from this job description:\n\n<job>\n{raw_text}\n</job>",
            tier="fast",
            system=SYSTEM,
            schema=PARSED_JOB_SCHEMA,
        )
    except Exception:  # noqa: BLE001
        record_run(user_id, run_id, step=AiRun.Step.JD_PARSE, error=True)
        return None
    record_run(user_id, run_id, step=AiRun.Step.JD_PARSE, result=result)
    data = result.get("data")
    return data if isinstance(data, dict) else None


def parse_job(user_id, job_id) -> dict:
    """Reads a saved posting again, for jobs created while AI was unavailable."""
    from django.utils import timezone

    try:
        row = Job.objects.get(id=job_id, user_id=user_id)
    except Job.DoesNotExist:
        raise NotFoundError("Job") from None
    parsed = _parse(user_id, row.raw_text)
    if parsed is None:
        raise AppError(503, "AI_NOT_CONFIGURED", "Job analysis is unavailable right now")
    row.parsed = parsed
    row.company = parsed.get("company")
    row.role = parsed.get("role")
    row.updated_at = timezone.now()
    row.save(update_fields=["parsed", "company", "role", "updated_at"])
    return _detail(row)


def _detail(row: Job) -> dict:
    return {
        "id": row.id,
        "company": row.company,
        "role": row.role,
        "source_url": row.source_url,
        "raw_text": row.raw_text,
        "parsed": row.parsed,
        "created_at": row.created_at,
    }


def list_jobs(user_id) -> list[dict]:
    rows = list(Job.objects.filter(user_id=user_id).order_by("-created_at"))
    from ats.service import latest_match_for_jobs

    matches = latest_match_for_jobs(user_id, [row.id for row in rows])
    return [_summary(row, matches.get(str(row.id))) for row in rows]


def create_job(user_id, data: dict) -> dict:
    if "sourceUrl" in data or "source_url" in data:
        url = data.get("sourceUrl") or data.get("source_url")
        raw_text = _fetch_job_text(url)
        source_url = url
    else:
        raw_text = data.get("rawText") or data.get("raw_text")
        source_url = None
    text_hash = _hash_text(raw_text)

    previous = Job.objects.filter(text_hash=text_hash, parsed__isnull=False).first()
    parsed = previous.parsed if previous else None
    if parsed is None:
        parsed = _parse(user_id, raw_text)

    row = Job.objects.create(
        user_id=user_id,
        company=(parsed or {}).get("company") if parsed else None,
        role=(parsed or {}).get("role") if parsed else None,
        source_url=source_url,
        raw_text=raw_text,
        text_hash=text_hash,
        parsed=parsed,
    )
    return _detail(row)


def get_job(user_id, job_id) -> dict:
    try:
        row = Job.objects.get(id=job_id, user_id=user_id)
    except Job.DoesNotExist:
        raise NotFoundError("Job") from None
    return _detail(row)


def delete_job(user_id, job_id) -> None:
    deleted = Job.objects.filter(id=job_id, user_id=user_id).delete()
    if deleted[0] == 0:
        raise NotFoundError("Job")
