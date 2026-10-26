import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Index, Q


class Profile(models.Model):
    """The master profile: every fact the user has given us. Tailoring can only
    draw from this. One per user, current state only (no history for MVP)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    data = models.JSONField(default=dict)
    schema_version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Template(models.Model):
    """Metadata for the LaTeX templates. The bodies live in code
    (templates/); these rows are what the API list and resume rows read."""

    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    ats_safe = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Job(models.Model):
    """A job description the user pasted or linked, plus its parsed
    requirements. The parsing endpoints come with the jobs module port."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.CharField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=200, blank=True, null=True)
    source_url = models.CharField(max_length=2048, blank=True, null=True)
    raw_text = models.TextField()
    text_hash = models.CharField(max_length=64)
    parsed = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [Index(fields=["text_hash"])]


def _default_layout() -> dict:
    return {"spacing": "normal"}


class Resume(models.Model):
    """One resume or variant. Metadata only: content lives in
    ResumeVersion (the head points at the newest snapshot)."""

    class Mode(models.TextChoices):
        STRUCTURED = "structured", "Structured"
        CODE = "code", "Code"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.STRUCTURED)
    template = models.ForeignKey(Template, on_delete=models.PROTECT, blank=True, null=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True)
    source_resume = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="variants"
    )
    head_version = models.ForeignKey(
        "ResumeVersion", on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )
    page_limit = models.IntegerField(default=1)
    layout = models.JSONField(default=_default_layout, blank=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ResumeVersion(models.Model):
    """Immutable snapshots of a resume's content. Never updated except to add
    a label or version; the snapshots themselves are only appended."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Kind(models.TextChoices):
        IMPORT = "import", "Import"
        MANUAL = "manual", "Manual"
        AI = "ai", "AI"
        RESTORE = "restore", "Restore"
        NAMED = "named", "Named"

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="versions")
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    content = models.JSONField(blank=True, null=True)
    tex_source = models.TextField(blank=True, null=True)
    label = models.CharField(max_length=80, blank=True, null=True)
    semver = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["resume", "created_at"])]
        constraints = [
            CheckConstraint(
                condition=Q(content__isnull=False, tex_source__isnull=True)
                | Q(content__isnull=True, tex_source__isnull=False),
                name="resume_versions_one_content",
            ),
        ]
