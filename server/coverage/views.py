"""Coverage endpoint."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import ConflictError, NotFoundError, not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_query
from api.common.responses import send_data
from jobs import service as jobs_service
from resumes import service as resumes_service

from . import service as coverage_service
from .schemas import CoverageQuery


@require_auth
@csrf_exempt
def coverage(request: HttpRequest, resume_id):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(CoverageQuery, request)
    resume = resumes_service.get_resume(request.user.id, resume_id)
    if query.version_id:
        version = resumes_service.version_row_detail(request.user.id, resume_id, query.version_id)
    else:
        version = resume.get("head")
    if not version:
        raise NotFoundError("Version")
    job = jobs_service.get_job(request.user.id, query.job_id)
    if not job.get("parsed"):
        raise ConflictError("This job hasn't been analysed yet")
    from resumes.models import Profile

    profile_row = Profile.objects.filter(user_id=request.user.id).first()
    profile_content = profile_row.data if (profile_row and profile_row.data) else None
    from resumes.content import EMPTY_RESUME_CONTENT, ResumeContent

    profile = (
        ResumeContent.model_validate(profile_content)
        if profile_content
        else ResumeContent.model_validate(EMPTY_RESUME_CONTENT)
    )
    report = coverage_service.coverage_report(job["parsed"], version, profile)
    return send_data(dict, report)
