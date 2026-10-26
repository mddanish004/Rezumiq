"""Session-level account rules: suspended accounts can't use the API.

Ports the Better Auth hook in lib/auth.ts ("This account is suspended") plus
the admin action that revokes sessions on suspend.
"""

from django.contrib.auth import logout
from django.http import JsonResponse


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
