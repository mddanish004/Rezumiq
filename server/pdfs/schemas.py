"""PDF module schemas, ported from pdfs.schemas.ts."""

import uuid

from api.common.models import ApiModel
from api.common.parse import StringBool


class ResumePdfQuery(ApiModel):
    version_id: uuid.UUID | None = None
    download: StringBool = False


class ResumeExportQuery(ApiModel):
    version_id: uuid.UUID | None = None


class CreatePreviewBodyText(ApiModel):
    tex_source: str


class CreatePreviewBodyStructured(ApiModel):
    template_id: str = "developer"
    content: dict
    layout: dict | None = None


CreatePreviewBody = CreatePreviewBodyStructured
