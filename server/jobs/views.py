"""Job endpoints, ported from modules/jobs."""

import json

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import validate as _validate
from api.common.responses import send_data

from . import service
from .schemas import CreateJobRaw, CreateJobUrl, JobResponse, JobSummary


@require_auth
@csrf_exempt
def jobs(request: HttpRequest):
    if request.method == "GET":
        return send_data(list[JobSummary], service.list_jobs(request.user.id))
    if request.method == "POST":
        raw = json.loads(request.body or b"null")
        if isinstance(raw, dict) and "sourceUrl" in raw:
            _validate(CreateJobUrl, raw)
        else:
            _validate(CreateJobRaw, raw)
        data = service.create_job(request.user.id, raw)
        return send_data(JobResponse, data, status=201)
    return not_allowed(["GET", "POST"])


@require_auth
@csrf_exempt
def job_detail(request: HttpRequest, job_id):
    if request.method == "GET":
        return send_data(JobResponse, service.get_job(request.user.id, job_id))
    if request.method == "DELETE":
        service.delete_job(request.user.id, job_id)
        return HttpResponse(status=204)
    if request.method == "POST":
        return send_data(JobResponse, service.parse_job(request.user.id, job_id))
    return not_allowed(["GET", "DELETE"])
