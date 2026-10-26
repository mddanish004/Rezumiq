"""PDF endpoints, ported from modules/pdfs/pdfs.routes.ts."""

import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import ConflictError, NotFoundError, not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_query
from latex.compile import one_at_a_time
from resumes import service as resumes_service

from . import service as pdfs_service
from .schemas import CreatePreviewBodyStructured, ResumeExportQuery, ResumePdfQuery


@require_auth
@csrf_exempt
def resume_pdf(request: HttpRequest, resume_id):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(ResumePdfQuery, request)
    resume = resumes_service.get_resume(request.user.id, resume_id)
    if query.version_id:
        version = resumes_service.version_row_detail(request.user.id, resume_id, query.version_id)
    else:
        version = resume.get("head")
    if not version:
        raise NotFoundError("Version")

    user_id = request.user.id

    def task():
        tex = pdfs_service.tex_for_version(resume, version)
        return pdfs_service.compile_or_throw(tex)

    from latex.compile import one_at_a_time

    result = one_at_a_time(str(user_id), task)
    pdf = result["pdf"]
    page_count = result.get("pageCount", 0)
    person = (
        (version.get("content") or {}).get("basics", {}).get("name")
        if isinstance(version.get("content"), dict)
        else None
    )
    file_name = pdfs_service.pdf_file_name(person, resume.get("title"))
    disposition = "attachment" if query.download else "inline"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'{disposition}; filename="{file_name}"'
    response["X-Page-Count"] = str(page_count)
    response["Access-Control-Expose-Headers"] = "X-Page-Count, Content-Disposition"
    response["Cache-Control"] = "private, max-age=0, must-revalidate"
    return response


@require_auth
@csrf_exempt
def resume_tex(request: HttpRequest, resume_id):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(ResumeExportQuery, request)
    resume = resumes_service.get_resume(request.user.id, resume_id)
    if query.version_id:
        version = resumes_service.version_row_detail(request.user.id, resume_id, query.version_id)
    else:
        version = resume.get("head")
    if not version:
        raise NotFoundError("Version")
    tex = pdfs_service.tex_for_version(resume, version)
    person = (
        (version.get("content") or {}).get("basics", {}).get("name")
        if isinstance(version.get("content"), dict)
        else None
    )
    file_name = pdfs_service.pdf_file_name(person, resume.get("title")).replace(".pdf", ".tex")
    response = HttpResponse(tex, content_type="application/x-tex")
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response


@require_auth
@csrf_exempt
def resume_json_resume(request: HttpRequest, resume_id):
    if request.method != "GET":
        return not_allowed(["GET"])
    query = parse_query(ResumeExportQuery, request)
    resume = resumes_service.get_resume(request.user.id, resume_id)
    if query.version_id:
        version = resumes_service.version_row_detail(request.user.id, resume_id, query.version_id)
    else:
        version = resume.get("head")
    if not version or not version.get("content"):
        raise ConflictError("JSON Resume export is only available for structured resumes")
    file_name = pdfs_service.pdf_file_name(
        (version["content"].get("basics", {}) or {}).get("name"), resume.get("title")
    ).replace(".pdf", ".json")
    data = pdfs_service.to_json_resume(version["content"])
    response = JsonResponse(data)
    response["Content-Disposition"] = f'attachment; filename="{file_name}"'
    return response


@require_auth
@csrf_exempt
def previews(request: HttpRequest):
    if request.method != "POST":
        return not_allowed(["POST"])
    raw = json.loads(request.body or b"null")
    if isinstance(raw, dict) and "texSource" in raw:
        tex = raw["texSource"]
    else:
        body = CreatePreviewBodyStructured.model_validate(raw)
        content = body.content
        tex = pdfs_service.render_structured(body.template_id, content, body.layout)
    user_id = request.user.id

    abandoned = {"aborted": False}

    def task():
        return pdfs_service.compile_or_throw(tex)

    try:
        result = one_at_a_time(str(user_id), task)
    except Exception:
        if abandoned["aborted"]:
            return HttpResponse(status=204)
        raise
    pdf = result["pdf"]
    page_count = result.get("pageCount", 0)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["X-Page-Count"] = str(page_count)
    return response
