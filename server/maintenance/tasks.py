"""Maintenance tasks, ported from jobs/maintenance.ts."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from ai.models import AiRun
from billing.models import Subscription
from billing.service import recompute_plan
from resumes.models import Resume
from storage import storage
from uploads.models import Upload

User = get_user_model()
DAY = timedelta(days=1)


def expire_subscriptions():
    lapsed = list(
        Subscription.objects.filter(
            status__in=["active", "cancelled", "past_due"],
            current_period_end__isnull=False,
            current_period_end__lt=timezone.now(),
        )
    )
    Subscription.objects.filter(id__in=[s.id for s in lapsed]).update(status="expired")
    for uid in {s.user_id for s in lapsed}:
        recompute_plan(uid)
    print(f"Expired {len(lapsed)} subscriptions")


def purge_deleted_resumes():
    cutoff = timezone.now() - timedelta(days=30)
    due = list(Resume.objects.filter(deleted_at__isnull=False, deleted_at__lt=cutoff))
    ids = [r.id for r in due]
    if not ids:
        print("Purged 0 deleted resumes")
        return
    AiRun.objects.filter(resume_id__in=ids).update(patch_ops=None, accepted_op_ids=None, error=None)
    Resume.objects.filter(id__in=ids).delete()
    print(f"Purged {len(ids)} deleted resumes")


def purge_old_uploads():
    cutoff = timezone.now() - timedelta(days=30)
    old = list(Upload.objects.filter(created_at__lt=cutoff))
    purged = 0
    for u in old:
        try:
            storage.delete_prefix(u.storage_key)
        except Exception:  # noqa: BLE001, S112
            continue
        u.delete()
        purged += 1
    print(f"Purged {purged} old uploads (failed {len(old) - purged})")


def purge_compiled_pdfs():
    removed = storage.delete_older("compiled/", timezone.now() - timedelta(days=30))
    print(f"Purged {removed} cached PDFs")


def purge_guest_users():
    cutoff = timezone.now() - timedelta(days=7)
    guests = list(User.objects.filter(is_guest=True, date_joined__lt=cutoff))
    purged = 0
    for g in guests:
        try:
            storage.delete_prefix(f"users/{g.id}/")
        except Exception:  # noqa: BLE001, S112
            continue
        g.delete()
        purged += 1
    print(f"Purged {purged} guest users (failed {len(guests) - purged})")


TASKS = {
    "expire-subscriptions": expire_subscriptions,
    "purge-deleted-resumes": purge_deleted_resumes,
    "purge-old-uploads": purge_old_uploads,
    "purge-compiled-pdfs": purge_compiled_pdfs,
    "purge-guest-users": purge_guest_users,
}
