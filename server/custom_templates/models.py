"""Custom templates: user-saved resume starting points."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q


class CustomTemplate(models.Model):
    class Mode(models.TextChoices):
        STRUCTURED = "structured", "Structured"
        CODE = "code", "Code"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    mode = models.CharField(max_length=16, choices=Mode.choices)
    template = models.ForeignKey(
        "resumes.Template", on_delete=models.PROTECT, blank=True, null=True
    )
    content = models.JSONField(blank=True, null=True)
    tex_source = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]
        constraints = [
            CheckConstraint(
                condition=(
                    Q(mode="structured", content__isnull=False)
                    | Q(mode="code", tex_source__isnull=False)
                ),
                name="custom_templates_body_matches_mode",
            ),
        ]
