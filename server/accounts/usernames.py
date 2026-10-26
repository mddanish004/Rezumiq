"""Username rules, ported from modules/users/usernames.ts."""

import re
import secrets
from datetime import datetime, timedelta

USERNAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,28}[a-z0-9])$")

USERNAME_COOLDOWN = timedelta(days=30)

RESERVED = frozenset(
    {
        "about",
        "account",
        "admin",
        "analytics",
        "api",
        "app",
        "assets",
        "ats",
        "ats-checker",
        "auth",
        "billing",
        "blog",
        "dashboard",
        "docs",
        "edit",
        "guides",
        "help",
        "home",
        "jobs",
        "login",
        "logout",
        "me",
        "my-templates",
        "new",
        "pricing",
        "privacy",
        "profile",
        "public",
        "register",
        "resume",
        "resumes",
        "settings",
        "share",
        "sign-in",
        "sign-up",
        "signin",
        "signup",
        "static",
        "status",
        "support",
        "templates",
        "terms",
        "u",
        "user",
        "users",
        "workspace",
        "www",
    }
)


def is_reserved_username(username: str) -> bool:
    return username in RESERVED


def username_cooldown_end(
    changed_at: datetime | None, now: datetime | None = None
) -> datetime | None:
    """Renames reserve the old name, so renaming often would park many names.

    None means the user may rename now.
    """
    if not changed_at:
        return None
    from django.utils import timezone

    end = changed_at + USERNAME_COOLDOWN
    now = now if now is not None else timezone.now()
    return end if end > now else None


def slugify(value: str, max_length: int = 24) -> str:
    from unicodedata import normalize

    value = normalize("NFKD", value)
    value = re.sub(r"[\u0300-\u036f]", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:max_length].rstrip("-")


def is_username_taken(username: str) -> bool:
    from .models import User, UsernameRedirect

    return (
        User.objects.filter(username=username).exists()
        or UsernameRedirect.objects.filter(old_username=username).exists()
    )


def is_username_available(username: str) -> bool:
    return (
        bool(USERNAME_PATTERN.fullmatch(username))
        and not is_reserved_username(username)
        and not (is_username_taken(username))
    )


def generate_username(name: str | None, email: str) -> str:
    base = slugify(name or "")
    if len(base) < 3:
        base = slugify(email.split("@")[0])
    if len(base) < 3:
        base = "user"

    if is_username_available(base):
        return base
    for _ in range(10):
        candidate = f"{base}-{secrets.randbelow(9000) + 1000}"
        if is_username_available(candidate):
            return candidate
    return f"user-{secrets.randbelow(9 * 10**7) + 10**7}"
