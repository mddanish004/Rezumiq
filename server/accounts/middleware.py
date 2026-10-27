"""Request-level account rules: Clerk bearer tokens and suspended accounts.

Ports the Better Auth hook in lib/auth.ts ("This account is suspended") plus
the admin action that revokes sessions on suspend.
"""

import jwt
from django.contrib.auth import logout
from django.http import JsonResponse

from api.common.errors import error_response


class ClerkAuthMiddleware:
    """Authenticates requests carrying a Clerk session JWT in the Authorization
    header on top of Django's session user (used by guests and the admin)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header = request.headers.get("Authorization", "")
        if header.lower().startswith("bearer "):
            from . import clerk

            try:
                user = clerk.authenticate(header[7:].strip())
            except jwt.PyJWTError:
                return error_response(401, "UNAUTHORIZED", "Invalid session token")
            if user is None:
                return error_response(401, "UNAUTHORIZED", "Invalid session token")
            request.user = user
        return self.get_response(request)


class SuspendUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_suspended:
            logout(request)
            request.session.flush()
            return JsonResponse(
                {
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "This account is suspended",
                        "details": None,
                    }
                },
                status=403,
            )
        return self.get_response(request)
