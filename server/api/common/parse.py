"""Request parsing.

Ports middleware/validate.ts: pydantic models take the roles zod schemas had.
Validation issues become the same {location, path, message} list shape.
"""

import json
from typing import Annotated, Any

from django.core.exceptions import RequestDataTooBig
from django.http import HttpRequest
from pydantic import BeforeValidator, TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from .errors import AppError, ValidationError

TRUE_WORDS = {"true", "1", "yes", "on"}
FALSE_WORDS = {"false", "0", "no", "off"}


def string_bool(value) -> bool:
    """zod's stringbool: query params written as words, not JSON."""
    if isinstance(value, bool):
        return value
    word = value.lower() if isinstance(value, str) else ""
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ValueError("Invalid boolean")


StringBool = Annotated[bool, BeforeValidator(string_bool)]


def parse_body(model, request: HttpRequest):
    """Validates the JSON request body through `model` or raises an AppError."""
    try:
        raw = json.loads(request.body or b"null")
    except json.JSONDecodeError:
        raise AppError(400, "INVALID_JSON", "Request body is not valid JSON") from None
    except RequestDataTooBig:
        raise AppError(413, "PAYLOAD_TOO_LARGE", "Request body is too large") from None
    return validate(model, raw, "body")


def parse_query(model, request: HttpRequest):
    """Validates query params through `model`, values arriving as strings from
    the URL; pydantic and the annotations below do the coercion."""
    return validate(model, request.GET.dict(), "query")


def validate(model: Any, raw, location: str = "body"):
    try:
        return TypeAdapter(model).validate_python(raw)
    except PydanticValidationError as exc:
        issues = []
        for error in exc.errors():
            message = error["msg"]
            prefix = "Value error, "
            message = message.removeprefix(prefix)
            issues.append(
                {
                    "location": location,
                    "path": ".".join(str(part) for part in error["loc"]),
                    "message": message,
                }
            )
        raise ValidationError(issues) from None
