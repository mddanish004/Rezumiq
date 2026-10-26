"""Upload lifecycle, ported from modules/uploads/uploads.service.ts."""

from __future__ import annotations

import uuid

from api.common.errors import AppError, NotFoundError
from storage import storage
from uploads.models import Upload

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

MIME_TYPES = {"pdf": "application/pdf", "tex": "application/x-tex", "text": "text/plain"}


def detect_kind(file_name: str, body: bytes) -> str:
    if body[:5].decode("latin-1") == "%PDF-":
        return "pdf"
    if b"\x00" in body:
        raise AppError(415, "UNSUPPORTED_FILE", "Upload a PDF, .tex or .txt file")
    head = body[:4096].decode("utf-8", errors="replace")
    if file_name.lower().endswith(".tex") or "\\documentclass" in head:
        return "tex"
    return "text"


def create_upload(user_id, file_name: str, body: bytes) -> dict:
    if len(body) > MAX_UPLOAD_BYTES:
        raise AppError(413, "PAYLOAD_TOO_LARGE", "File is too large")
    kind = detect_kind(file_name, body)
    upload_id = uuid.uuid4()
    storage_key = f"users/{user_id}/uploads/{upload_id}"
    storage.put(storage_key, body, MIME_TYPES[kind])
    row = Upload.objects.create(
        id=upload_id,
        user_id=user_id,
        kind=kind,
        storage_key=storage_key,
        file_name=file_name[:200],
        mime_type=MIME_TYPES[kind],
        size_bytes=len(body),
    )
    return {
        "id": row.id,
        "kind": row.kind,
        "file_name": row.file_name,
        "mime_type": row.mime_type,
        "size_bytes": row.size_bytes,
        "created_at": row.created_at,
    }


def get_owned_upload(user_id, upload_id) -> dict:
    try:
        row = Upload.objects.get(id=upload_id, user_id=user_id)
    except Upload.DoesNotExist:
        raise NotFoundError("Upload") from None
    return {
        "id": row.id,
        "kind": row.kind,
        "file_name": row.file_name,
        "mime_type": row.mime_type,
        "size_bytes": row.size_bytes,
        "storage_key": row.storage_key,
        "created_at": row.created_at,
    }


def read_upload(user_id, upload_id) -> tuple[dict, bytes]:
    info = get_owned_upload(user_id, upload_id)
    body = storage.get(info["storage_key"])
    if body is None:
        raise NotFoundError("Upload file")
    return info, body


def delete_upload(user_id, upload_id) -> None:
    info = get_owned_upload(user_id, upload_id)
    storage.delete_prefix(info["storage_key"])
    Upload.objects.filter(id=info["id"]).delete()
