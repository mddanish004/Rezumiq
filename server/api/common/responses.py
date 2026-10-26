"""JSON responses.

Ports lib/http.ts sendData: bodies always come back as {"data": ...}. Every
body is parsed through its schema and serialized with camelCase aliases, so
the wire contract is single-sourced in the schema. Schemas can be a model
class or any typing annotation (list[T], unions) via pydantic's TypeAdapter.
"""

from typing import Any

from django.http import JsonResponse
from pydantic import TypeAdapter


def json_data(data: Any, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status, safe=False)


def send_data(schema: Any, data: Any, status: int = 200) -> JsonResponse:
    adapter = TypeAdapter(schema)
    body = adapter.dump_python(adapter.validate_python(data), by_alias=True, mode="json")
    return JsonResponse({"data": body}, status=status)
