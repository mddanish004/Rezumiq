"""Uploads: files stored for later import, ported from modules/uploads."""

import uuid

from django.conf import settings
from django.db import models


class Upload(models.Model):
    class Kind(models.TextChoices):
        PDF = "pdf", "PDF"
        TEX = "tex", "Tex"
        TEXT = "text", "Text"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=8, choices=Kind.choices)
    storage_key = models.CharField(max_length=512)
    file_name = models.CharField(max_length=200)
    mime_type = models.CharField(max_length=64)
    size_bytes = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]
