"""AI-assisted ATS reading, ported from modules/ats/ai-match.ts and ai-review.ts."""

from __future__ import annotations

import hashlib
import re

from ai.generate import generate_structured
from ai.models import AiRun
from ai.redact import redact
from ai.runs import record_run, reserve_run
from ats.skills.match import find_skills
from usage.quotas import assert_paid_plan

MATCH_SYSTEM = """You check a resume against a few requirements from a job description.
Use only what the resume text says. Never invent or assume skills, degrees, dates, places or experience that are not written in it.
Every evidence value must be copied exactly, character for character, from the resume text: a short phrase, one line at most.
Skills: a missing skill counts as implied only when the resume names something that clearly includes it, such as PostgreSQL for SQL or Next.js for React. Related or similar skills do not count. Otherwise give null evidence.
Requirements: answer met or not-met only when the resume text clearly shows it, with the line that shows it as evidence. Otherwise answer unclear with null evidence."""

REVIEW_SYSTEM = """You are an experienced recruiter reviewing a resume for any field: software, data, finance, banking, consulting, marketing, design or others.
Use only what the resume text says. Never invent or assume skills, employers, degrees, dates, numbers or results that are not written in it.
verdict: two or three plain sentences on how the resume reads in a recruiter's first 30 seconds.
strengths: up to three things the resume already does well, each one sentence.
fixes: the three to five changes that would improve it most, most important first. title is a short instruction, why is one sentence.
line is the resume line the fix is about, copied exactly, character for character, or null when the fix is about the whole resume.
rewrite is a stronger version of that line, or null: lead with an action verb and make the result clear. A rewrite keeps every fact of the line and never adds a task, tool, skill or activity the line doesn't state; what the resume lacks belongs in the fix's why or in jobFit gaps. Where a number would help but the line has none, write a placeholder in square brackets, like [X%] or [number of users], for the person to fill in. Placeholders are only for numbers.
jobFit: only when a job description is given, otherwise null. summary is two sentences on how well the resume fits the role; gaps lists up to five things the job asks for that the resume doesn't show.
Write in simple English. No hype, and never promise interviews or offers."""

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string"},
                    "evidence": {"type": ["string", "null"]},
                },
                "required": ["skill", "evidence"],
            },
        },
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "status": {"type": "string", "enum": ["met", "not-met", "unclear"]},
                    "evidence": {"type": ["string", "null"]},
                },
                "required": ["number", "status", "evidence"],
            },
        },
    },
    "required": ["skills", "requirements"],
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "fixes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "why": {"type": "string"},
                    "line": {"type": ["string", "null"]},
                    "rewrite": {"type": ["string", "null"]},
                },
                "required": ["title", "why", "line", "rewrite"],
            },
        },
        "jobFit": {
            "type": ["object", "null"],
            "properties": {
                "summary": {"type": "string"},
                "gaps": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["summary", "gaps"],
        },
    },
    "required": ["verdict", "strengths", "fixes", "jobFit"],
}

CACHE_SIZE = 500
_cache = {}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _as_number(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return int(value) if isinstance(value, float) and value.is_integer() else None


def grounded(ai: dict, resume_text: str, asked: dict) -> dict:
    """Drops anything the model can't back with words that are really in the resume."""
    resume = _norm(resume_text)
    unicode_letters = re.compile(r"[^\W\d_]{2}", re.UNICODE)

    def found(evidence) -> str | None:
        return (
            evidence
            if evidence and unicode_letters.search(evidence) and _norm(evidence) in resume
            else None
        )

    skills = []
    for s in ai.get("skills") or []:
        skill = next(
            (name for name in asked["skills"] if _norm(name) == _norm(s.get("skill") or "")), None
        )
        evidence = found(s.get("evidence"))
        names = [hit["skill"] for hit in find_skills(evidence)] if evidence else []
        if skill and any(name != skill for name in names):
            skills.append({"skill": skill, "evidence": evidence})

    requirements = [
        {"number": number, "status": r["status"], "evidence": r.get("evidence")}
        for r in ai.get("requirements") or []
        if (number := _as_number(r.get("number"))) is not None
        and r.get("status") in ("met", "not-met")
        and 1 <= number <= asked["requirements"]
        and found(r.get("evidence"))
    ]
    return {"skills": skills, "requirements": requirements}


def merge_ai_match(report: dict, ai: dict) -> dict:
    """The score is never touched: implied skills stay missing, and only unclear requirements change."""
    keywords = report.get("keywords")
    knockouts = report.get("knockouts")
    if not keywords or not knockouts:
        return report
    missing = keywords["hard"]["missing"]
    implied = [
        {"skill": skill, "evidence": hit["evidence"]}
        for skill in missing
        if (
            hit := next(
                (s for s in ai["skills"] if s["skill"] == skill and s.get("evidence")), None
            )
        )
    ]
    unclear = 0
    new_knockouts = []
    for knockout in knockouts:
        if knockout["status"] != "unclear":
            new_knockouts.append(knockout)
            continue
        unclear += 1
        verdict = next((r for r in ai["requirements"] if r["number"] == unclear), None)
        new_knockouts.append(
            dict(
                knockout,
                status=verdict["status"],
                evidence=verdict["evidence"],
                checkedWithAi=True,
            )
            if verdict and verdict["status"] != "unclear" and verdict["evidence"]
            else knockout
        )
    return {**report, "keywords": {**keywords, "implied": implied}, "knockouts": new_knockouts}


def with_ai_match(
    report: dict,
    input: dict,
) -> dict:
    """Adds an AI reading of what the rules couldn't decide; any failure returns the report unchanged."""
    skills = (((report.get("keywords") or {}).get("hard") or {}).get("missing")) or []
    requirements = [k for k in (report.get("knockouts") or []) if k["status"] == "unclear"]
    if not skills and not requirements:
        return report

    key = hashlib.sha256(f"{input['resumeText']}\0{input['jobText']}".encode()).hexdigest()
    try:
        ai = _cache.get(key)
        if ai:
            _cache.pop(key)
        else:
            prompt = f"""Missing skills:
{(chr(10).join(f"- {s}" for s in skills)) or "(none)"}

Unclear requirements:
{(chr(10).join(f"{i + 1}. {r['label']}: {r['requirement']}" for i, r in enumerate(requirements))) or "(none)"}

<resume>
{input["resumeText"][:15000]}
</resume>"""
            redacted = redact(prompt, [input["content"]] if input.get("content") else [])
            reserved = reserve_run(
                input["userId"],
                "ats",
                AiRun.Step.ATS_MATCH,
                resume_id=input.get("resumeId"),
                job_id=input.get("jobId"),
            )
            try:
                result = generate_structured(
                    redacted.text, tier="fast", system=MATCH_SYSTEM, schema=MATCH_SCHEMA
                )
            except Exception:
                record_run(
                    input["userId"],
                    reserved,
                    resume_id=input.get("resumeId"),
                    job_id=input.get("jobId"),
                    error=True,
                )
                raise
            record_run(
                input["userId"],
                reserved,
                resume_id=input.get("resumeId"),
                job_id=input.get("jobId"),
                result=result,
            )
            ai = grounded(
                redacted.restore(result.get("data") or {}),
                input["resumeText"],
                {
                    "skills": skills,
                    "requirements": len(requirements),
                },
            )
        _cache[key] = ai
        if len(_cache) > CACHE_SIZE:
            _cache.pop(next(iter(_cache)))
        return merge_ai_match(report, ai)
    except Exception:  # noqa: BLE001
        return report


def _parse_review(data: dict) -> dict:
    fixes = []
    for fix in data.get("fixes") or []:
        if not isinstance(fix, dict):
            continue
        fixes.append(
            {
                "title": str(fix.get("title") or ""),
                "why": str(fix.get("why") or ""),
                "line": fix.get("line"),
                "rewrite": fix.get("rewrite"),
            }
        )
    job_fit = data.get("jobFit")
    if isinstance(job_fit, dict):
        job_fit = {
            "summary": str(job_fit.get("summary") or ""),
            "gaps": [str(gap) for gap in (job_fit.get("gaps") or []) if isinstance(gap, str)],
        }
    else:
        job_fit = None
    return {
        "verdict": str(data.get("verdict") or ""),
        "strengths": [str(s) for s in (data.get("strengths") or []) if isinstance(s, (str,))],
        "fixes": fixes,
        "jobFit": job_fit,
    }


def _unbullet(text: str) -> str:
    return re.sub(r"^[\s\u2022\u25e6\u25aa*\u00b7\u2013-]+", "", text)


def _numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)*", re.sub(r"\[[^\]]*\]", "", text or ""))


def grounded_review(review: dict, resume_text: str) -> dict:
    """A fix's line must be a real resume line, and its rewrite must only reuse the line's numbers."""
    resume = _norm(resume_text)

    def pick_line(fix: dict) -> str | None:
        line = fix.get("line")
        if line and len(line.strip().split()) >= 3 and _norm(line) in resume:
            return line
        return None

    fixes = []
    for fix in review["fixes"][:5]:
        line = pick_line(fix)
        line_numbers = set(_numbers(line or ""))
        rewrite = fix.get("rewrite")
        if not (
            line
            and rewrite
            and _norm(rewrite) != _norm(line)
            and all(number in line_numbers for number in _numbers(rewrite))
        ):
            rewrite = None
        fixes.append(
            {
                "title": fix["title"],
                "why": fix["why"],
                "line": _unbullet(line) if line else None,
                "rewrite": _unbullet(rewrite) if rewrite else None,
            }
        )
    job_fit = review.get("jobFit")
    return {
        "verdict": review["verdict"],
        "strengths": review["strengths"][:3],
        "fixes": fixes,
        "jobFit": {"summary": job_fit["summary"], "gaps": job_fit["gaps"][:5]} if job_fit else None,
    }


def review_resume(user_id: str, text: str, job_description: str | None) -> dict:
    """Season Pass and Pro only. The text is never stored; only the run is logged."""
    assert_paid_plan(user_id, "The AI review")
    prompt = f"<resume>\n{text[:15000]}\n</resume>"
    if job_description:
        prompt += f"\n\n<job>\n{job_description[:8000]}\n</job>"
    redacted = redact(prompt, [])
    reserved = reserve_run(user_id, "review", AiRun.Step.ATS_REVIEW)
    try:
        result = generate_structured(
            redacted.text, tier="fast", system=REVIEW_SYSTEM, schema=REVIEW_SCHEMA
        )
    except Exception:
        record_run(user_id, reserved, step=AiRun.Step.ATS_REVIEW, error=True)
        raise
    record_run(user_id, reserved, step=AiRun.Step.ATS_REVIEW, result=result)
    return grounded_review(_parse_review(redacted.restore(result.get("data") or {})), text)
