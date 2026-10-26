"""Reading and writing the stored ATS reports used by resume and job lists."""

from __future__ import annotations

from .models import AtsReport


def save_report(user_id, resume: dict, job: dict | None, head: dict, report: dict) -> None:
    job_match = None
    job_category = next((c for c in report.get("categories", []) if c.get("id") == "job"), None)
    if job_category and job_category.get("maxScore"):
        job_match = round(job_category["score"] / job_category["maxScore"] * 100)
    AtsReport.objects.create(
        user_id=user_id,
        resume_id=resume["id"],
        job_id=job["id"] if job else None,
        version_id=head.get("id"),
        score=report["score"],
        grade=report["grade"],
        job_match=job_match,
        report=report,
    )


def _summary(row: AtsReport) -> dict:
    return {
        "score": row.score,
        "grade": row.grade,
        "jobId": row.job_id,
        "checkedAt": row.created_at,
    }


def latest_for_resumes(user_id, resume_ids) -> dict:
    latest = {}
    rows = AtsReport.objects.filter(user_id=user_id, resume_id__in=list(resume_ids)).order_by(
        "-created_at"
    )
    for row in rows:
        latest.setdefault(str(row.resume_id), _summary(row))
    return latest


def latest_for_resume(user_id, resume_id) -> dict | None:
    return latest_for_resumes(user_id, [resume_id]).get(str(resume_id))


def latest_match_for_jobs(user_id, job_ids) -> dict:
    """The newest check for each job, with the resume it was run against."""
    latest = {}
    rows = AtsReport.objects.filter(
        user_id=user_id, job_id__in=list(job_ids), job_match__isnull=False
    ).order_by("-created_at")
    for row in rows:
        latest.setdefault(
            str(row.job_id),
            {"percent": row.job_match, "resumeId": row.resume_id, "checkedAt": row.created_at},
        )
    return latest
