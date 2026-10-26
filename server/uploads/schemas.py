"""Request and response shapes, ported from uploads.schemas.ts."""

import uuid
from datetime import datetime

from api.common.models import ApiModel


class UploadParams(ApiModel):
    upload_id: uuid.UUID


class UploadResponse(ApiModel):
    id: uuid.UUID
    kind: str
    file_name: str
    mime_type: str
    size_bytes: int
    created_at: datetime
