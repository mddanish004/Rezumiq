"""API error types and the JSON error envelope.

Ports lib/errors.ts and the error handler: business failures raise one of the
classes below and the middleware turns anything uncaught into JSON, so the
client always sees {"error": {code, message, details?}}.
"""

import logging

from django.db import IntegrityError
from django.http import Http404, HttpResponseNotAllowed, JsonResponse

from .responses import json_data

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details


class ValidationError(AppError):
    def __init__(self, issues):
        super().__init__(400, "VALIDATION_ERROR", "Request validation failed", issues)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Sign in required"):
        super().__init__(401, "UNAUTHORIZED", message)


class ForbiddenError(AppError):
    def __init__(self, message: str = "You don't have access to this resource"):
        super().__init__(403, "FORBIDDEN", message)


class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)


def error_response(status: int, code: str, message: str, details=None) -> JsonResponse:
    return json_data({"error": {"code": code, "message": message, "details": details}}, status)


class JsonErrorMiddleware:
    """Turns AppError, Http404, IntegrityError (lost uniqueness races) and anything
    uncaught into the JSON envelope."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, AppError):
            return error_response(
                exception.status, exception.code, str(exception), exception.details
            )
        if isinstance(exception, Http404):
            return error_response(404, "NOT_FOUND", "Endpoint not found")
        if isinstance(exception, IntegrityError):
            return error_response(
                409,
                "CONFLICT",
                "That already exists. Try a different name, or refresh and try again.",
            )
        logger.exception("Unhandled error on %s %s", request.method, request.path)
        return error_response(500, "INTERNAL_ERROR", "Something went wrong")


def not_found(request, exception=None):
    """Django's URL-level 404 hook, kept on the same JSON envelope."""
    return error_response(404, "NOT_FOUND", "Endpoint not found")


_NOT_ALLOWED_BODY = b'{"error":{"code":"METHOD_NOT_ALLOWED","message":"Method not allowed"}}'


def not_allowed(methods: list[str]):
    """405 for views that dispatch methods themselves; Allow names the verbs."""
    return HttpResponseNotAllowed(methods, _NOT_ALLOWED_BODY, content_type="application/json")


def method_not_allowed(request, exception=None):
    """Django's URL-level 405 hook: the path exists, the verb does not."""
    return not_allowed()


def internal_error(request):
    """Django's 500 hook. DEBUG mode renders its own page before reaching this."""
    logger.exception("Unhandled server error on %s %s", request.method, request.path)
    return error_response(500, "INTERNAL_ERROR", "Something went wrong")
