"""Share links and their view tracking."""

import uuid

from django.conf import settings
from django.db import models


class ShareLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey("resumes.Resume", on_delete=models.CASCADE)
    slug = models.CharField(max_length=30)
    pinned_version = models.ForeignKey(
        "resumes.ResumeVersion", on_delete=models.SET_NULL, blank=True, null=True
    )
    show_contact = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    contact_password_hash = models.CharField(max_length=255, blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    view_count = models.IntegerField(default=0)
    last_viewed_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "slug")]
        indexes = [models.Index(fields=["resume"]), models.Index(fields=["pinned_version"])]


class LinkView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    share_link = models.ForeignKey(ShareLink, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now_add=True)
    visitor_hash = models.CharField(max_length=128, blank=True, null=True)
    referrer = models.CharField(max_length=512, blank=True, null=True)
    country = models.CharField(max_length=64, blank=True, null=True)
    region = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    device = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["share_link", "viewed_at"]),
            models.Index(fields=["viewed_at"]),
        ]
