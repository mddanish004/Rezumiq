"""Coverage schemas."""

import uuid

from api.common.models import ApiModel


class CoverageQuery(ApiModel):
    job_id: uuid.UUID
    version_id: uuid.UUID | None = None
