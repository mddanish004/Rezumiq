"""Stored ATS reports: the latest score behind a resume card and job match."""

import uuid

from django.conf import settings
from django.db import models


class AtsReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey(
        "resumes.Resume", on_delete=models.CASCADE, related_name="ats_reports"
    )
    job = models.ForeignKey("resumes.Job", on_delete=models.SET_NULL, blank=True, null=True)
    version = models.ForeignKey(
        "resumes.ResumeVersion", on_delete=models.SET_NULL, blank=True, null=True
    )
    score = models.IntegerField()
    grade = models.CharField(max_length=16)
    job_match = models.IntegerField(blank=True, null=True)
    report = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["resume", "created_at"]),
            models.Index(fields=["job", "created_at"]),
        ]
