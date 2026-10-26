"""Per-IP throttling for endpoints reachable without an account.

Counters live in Django's default cache. LocMemCache is per process, so with N
Gunicorn workers an attacker gets N times the budget; point CACHES at a shared
backend (Redis) when that matters.
ponytail: per-process counter; upgrade by configuring a shared CACHES backend.
"""

from django.core.cache import cache

from .errors import AppError

MESSAGE = "Too many attempts. Wait a few minutes and try again."


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _bucket(request, action: str, key: str) -> str:
    suffix = f":{key}" if key else ""
    return f"rl:{action}:{_client_ip(request)}{suffix}"


def count(request, action: str, key: str = "") -> int:
    return cache.get(_bucket(request, action, key)) or 0


def hit(request, action: str, window: int, key: str = "") -> int:
    """Record one attempt and return how many landed inside the window."""
    bucket = _bucket(request, action, key)
    if cache.add(bucket, 1, timeout=window):
        return 1
    try:
        return cache.incr(bucket)
    except ValueError:
        cache.set(bucket, 1, timeout=window)
        return 1


def reject(request, action: str, limit: int, key: str = "") -> None:
    """Raise 429 once the window already holds `limit` attempts."""
    if count(request, action, key) >= limit:
        raise AppError(429, "RATE_LIMITED", MESSAGE)


def hit_or_429(request, action: str, limit: int, window: int, key: str = "") -> None:
    """Count this request, raising 429 when it exceeds `limit`."""
    if hit(request, action, window, key) > limit:
        raise AppError(429, "RATE_LIMITED", MESSAGE)
