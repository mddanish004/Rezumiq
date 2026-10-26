"""Import endpoints, ported from imports.routes.ts."""

from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import not_allowed
from api.common.guards import require_auth
from api.common.parse import parse_body
from api.common.responses import send_data

from .schemas import CreateDraftBody, CreateImportBody, ImportOut
from .service import create_draft, create_import


@require_auth
@csrf_exempt
def imports(request: HttpRequest):
    """POST /v1/imports - returns extracted content; the client saves it with PUT /profile or POST /resumes."""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateImportBody, request)
    return send_data(ImportOut, create_import(request.user.id, body.model_dump()), status=201)


@require_auth
@csrf_exempt
def resume_drafts(request: HttpRequest):
    """POST /v1/resume-drafts - a resume written by AI from the user's notes."""
    if request.method != "POST":
        return not_allowed(["POST"])
    body = parse_body(CreateDraftBody, request)
    return send_data(ImportOut, create_draft(request.user.id, body.model_dump()), status=201)
