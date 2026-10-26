"""Upload endpoints, ported from modules/uploads."""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.common.errors import AppError, not_allowed
from api.common.guards import require_auth
from api.common.responses import send_data

from . import service
from .schemas import UploadResponse


@require_auth
@csrf_exempt
def uploads(request: HttpRequest):
    if request.method == "POST":
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise AppError(400, "FILE_REQUIRED", 'Send the file in a multipart field named "file"')
        body = uploaded.read()
        data = service.create_upload(request.user.id, uploaded.name or "file", body)
        return send_data(UploadResponse, data, status=201)
    return not_allowed(["POST"])


@require_auth
@csrf_exempt
def upload_detail(request: HttpRequest, upload_id):
    if request.method == "GET":
        info = service.get_owned_upload(request.user.id, upload_id)
        return send_data(UploadResponse, info)
    if request.method == "DELETE":
        service.delete_upload(request.user.id, upload_id)
        return HttpResponse(status=204)
    return not_allowed(["GET", "DELETE"])
