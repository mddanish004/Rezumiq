"""ATS endpoints: rule-based score, AI match, AI review."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common import ratelimit
from api.common.errors import NotFoundError, not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data
from jobs import service as jobs_service
from resumes import service as resumes_service

from . import parser, scoring
from .ai import review_resume, with_ai_match
from .schemas import (
    AtsReport,
    AtsReview,
    CreateAtsReportBody,
    CreateAtsReviewBody,
    CreateResumeAtsReportBody,
)
from .service import save_report


@require_auth
@csrf_exempt
def resume_ats_report(request: HttpRequest, resume_id):
    """POST /v1/resumes/:resumeId/ats-reports
    Scores a user's saved resume (head version). If a jobId is provided and the user
    has an AI key configured, runs the AI match step."""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateResumeAtsReportBody, request)
    user_id = request.user.id

    resume = resumes_service.get_resume(user_id, resume_id)
    head = resume.get("head")
    if not head:
        raise NotFoundError("Version")

    job = None
    if body.job_id:
        job = jobs_service.get_job(user_id, body.job_id)

    text = head.get("tex_source")
    if text:
        text = scoring.tex_to_text(text)

    from latex.compile import one_at_a_time
    from pdfs import service as pdfs_service

    expected = (
        parser.expected_fields(head["content"])
        if head.get("content") is not None
        else parser.expected_from_text(text or "")
    )
    tex = pdfs_service.tex_for_version(resume, head)
    parse = one_at_a_time(user_id, lambda: parser.parse_tex(tex, expected))

    scored = scoring.score_resume(
        {
            "content": head.get("content"),
            "text": text,
            "jobText": job.get("raw_text") if job else None,
            "parse": parse,
        }
    )

    if job and not request.user.is_guest:
        resume_text = scoring.resume_text({"content": head.get("content"), "text": text})
        scored = with_ai_match(
            scored,
            {
                "userId": user_id,
                "resumeText": resume_text,
                "jobText": job["raw_text"],
                "content": head.get("content"),
                "resumeId": resume["id"],
                "jobId": job["id"],
            },
        )

    save_report(user_id, resume, job, head, scored)
    return send_data(AtsReport, scored)


@csrf_exempt
def public_ats_report(request: HttpRequest):
    """POST /v1/ats-reports
    Public endpoint: scores arbitrary text in memory. With a job description, a signed-in
    user (not a guest) also gets the AI check."""
    if request.method != "POST":
        return not_allowed(["POST"])
    ratelimit.hit_or_429(request, "public_ats", limit=20, window=60)
    body = parse_body(CreateAtsReportBody, request)

    parse = None
    pdf = None
    if body.items and body.page:
        page = dict(body.page)
        parse = parser.parse_pdf_items(body.items, page)
        pdf = {"items": body.items, "page": page}

    scored = scoring.score_resume(
        {
            "text": body.text,
            "jobText": body.job_description,
            "parse": parse,
            "pdf": pdf,
            "file": body.file,
        }
    )

    if body.job_description and request.user.is_authenticated and not request.user.is_guest:
        resume_text = scoring.resume_text({"text": body.text})
        scored = with_ai_match(
            scored,
            {
                "userId": request.user.id,
                "resumeText": resume_text,
                "jobText": body.job_description,
            },
        )

    return send_data(AtsReport, scored)


@require_auth
@csrf_exempt
def ats_review(request: HttpRequest):
    """POST /v1/ats-reviews
    AI reviewer verdict. Season Pass/Pro only; text is never stored."""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateAtsReviewBody, request)
    user_id = request.user.id

    review = review_resume(user_id, body.text, body.job_description)
    return send_data(AtsReview, review, status=201)
