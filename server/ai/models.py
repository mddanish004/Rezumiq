"""AI run log and user API keys."""

import uuid

from django.conf import settings
from django.db import models


class AiRun(models.Model):
    class Step(models.TextChoices):
        IMPORT = "import"
        JD_PARSE = "jd_parse"
        PLAN = "plan"
        REWRITE = "rewrite"
        VERIFY = "verify"
        INLINE_EDIT = "inline_edit"
        CHAT_EDIT = "chat_edit"
        FIX_COMPILE = "fix_compile"
        DRAFT = "draft"
        ATS_MATCH = "ats_match"
        ATS_REVIEW = "ats_review"

    class Status(models.TextChoices):
        PENDING = "pending"
        SUCCEEDED = "succeeded"
        FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey("resumes.Resume", on_delete=models.SET_NULL, blank=True, null=True)
    job = models.ForeignKey("resumes.Job", on_delete=models.SET_NULL, blank=True, null=True)
    version = models.ForeignKey(
        "resumes.ResumeVersion", on_delete=models.SET_NULL, blank=True, null=True
    )
    step = models.CharField(max_length=16, choices=Step.choices)
    status = models.CharField(max_length=16, choices=Status.choices)
    model = models.CharField(max_length=128)
    input_tokens = models.IntegerField(default=0)
    cached_input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    cost_usd_micros = models.IntegerField(default=0)
    latency_ms = models.IntegerField(blank=True, null=True)
    patch_ops = models.JSONField(blank=True, null=True)
    accepted_op_ids = models.JSONField(blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    byok = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["resume"]),
            models.Index(fields=["version"]),
            models.Index(fields=["job"]),
        ]


class UserAiKey(models.Model):
    class Provider(models.TextChoices):
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        OPENROUTER = "openrouter"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=16, choices=Provider.choices)
    enabled = models.BooleanField(default=True)
    model_id = models.CharField(max_length=128, blank=True, null=True)
    model_ids = models.JSONField(default=list, blank=True)
    encrypted_key = models.TextField()
    key_hint = models.CharField(max_length=16)
    verified_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "provider")]
