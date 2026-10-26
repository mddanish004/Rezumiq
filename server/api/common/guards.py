"""Auth guards.

Ports middleware/require-auth.ts and require-admin.ts. Suspended accounts are
blocked earlier, by accounts.middleware.SuspendedUserMiddleware.
"""

from functools import wraps

from django.http import HttpRequest

from .errors import ForbiddenError, UnauthorizedError


def require_auth(view):
    @wraps(view)
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            raise UnauthorizedError()
        return view(request, *args, **kwargs)

    return wrapper


def email_verified(user) -> bool:
    """Verified-ness lives in allauth's EmailAddress table, not the user row."""
    from allauth.account.models import EmailAddress

    address = EmailAddress.objects.filter(user=user, email=user.email).first()
    return bool(address and address.verified)


def is_admin(user) -> bool:
    from django.conf import settings

    return user.email in settings.ADMIN_EMAILS and email_verified(user)


def require_admin(view):
    @wraps(view)
    @require_auth
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not is_admin(request.user):
            raise ForbiddenError()
        return view(request, *args, **kwargs)

    return wrapper
