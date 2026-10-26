from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """The auth user.

    `email` is the login identity and unique because allauth authenticates by
    email. Plan is derived from subscriptions (see the billing port), stored on
    the row after every subscription change, and never the source of truth.
    """

    class Plan(models.TextChoices):
        FREE = "free", "Free"
        SEASON_PASS = "season_pass", "Season Pass"
        PRO = "pro", "Pro"

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True, default="")
    plan = models.CharField(max_length=16, choices=Plan.choices, default=Plan.FREE)
    is_guest = models.BooleanField(default=False)
    guest_expires_at = models.DateTimeField(null=True, blank=True)
    usage_reset_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    username_changed_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_suspended(self) -> bool:
        return self.suspended_at is not None

    def suspend(self) -> None:
        self.suspended_at = self.suspended_at or timezone.now()
        self.save(update_fields=["suspended_at"])

    def unsuspend(self) -> None:
        if self.suspended_at:
            self.suspended_at = None
            self.save(update_fields=["suspended_at"])

    def __str__(self) -> str:
        return self.username or self.email


class UsernameRedirect(models.Model):
    """Old usernames keep redirecting to their owner so shared links don't break,
    and stay reserved so nobody else can take them."""

    old_username = models.CharField(max_length=30, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
