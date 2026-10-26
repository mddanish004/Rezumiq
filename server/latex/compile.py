"""Compile orchestration, ported from lib/latex/compile.ts.

Caches compiled PDFs in storage keyed by a sha256 of the (XeTeX-normalized)
source, remembers recent failures in process memory, and serializes compiles
per user so one busy tab can't starve the CPU.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from typing import Any


def _settings():
    from django.conf import settings as s

    return s


from storage import storage

from .tectonic import (
    create_tectonic,
    make_xetex_compatible,
)

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

_local_compile = None
if not getattr(_settings(), "COMPILER_URL", None):
    _local_compile = create_tectonic(
        bin_path=getattr(_settings(), "TECTONIC_BIN", "tectonic"),
        only_cached=getattr(_settings(), "TECTONIC_ONLY_CACHED", False),
        timeout_ms=getattr(_settings(), "COMPILE_TIMEOUT_MS", 20_000),
        concurrency=getattr(_settings(), "COMPILE_CONCURRENCY", 2),
    )

FAILURE_TTL_MS = 5 * 60_000
FAILURE_CAP = 500
_failures: dict[str, dict[str, Any]] = {}
_failures_lock = threading.Lock()

_user_queues: dict[str, threading.Event] = {}
_user_queues_lock = threading.Lock()


def _unavailable() -> Exception:
    from api.common.errors import AppError

    return AppError(502, "COMPILER_UNAVAILABLE", "The LaTeX compiler is unavailable. Try again.")


def _remote_compile(tex: str, cancel=None) -> dict[str, Any]:
    s = _settings()
    url = getattr(s, "COMPILER_URL", None)
    timeout_ms = getattr(s, "COMPILE_TIMEOUT_MS", 20_000)
    timeout = (timeout_ms + 5_000) / 1000.0
    data = tex.encode("utf-8")
    req = urllib.request.Request(
        url + "/compile",
        data=data,
        headers={"Content-Type": "text/plain; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            pdf = resp.read()
            return {"ok": True, "pdf": pdf}
    except urllib.error.HTTPError as exc:
        if exc.code == 422:
            body = json.loads(exc.read() or b"{}")
            return {"ok": False, "errors": body.get("errors", [])}
        if exc.code == 413:
            from api.common.errors import AppError

            raise AppError(413, "PAYLOAD_TOO_LARGE", "The LaTeX source is too large")
        raise _unavailable()
    except (urllib.error.URLError, TimeoutError, OSError):
        raise _unavailable()


def _page_count(pdf: bytes) -> int:
    if PdfReader is None:
        return 0
    try:
        reader = PdfReader(__import__("io").BytesIO(pdf))
        return len(reader.pages)
    except Exception:  # noqa: BLE001
        return 0


def one_at_a_time(user_id: str, task):
    """Serializes `task` per user within this process."""
    with _user_queues_lock:
        prev = _user_queues.get(user_id)
        done = threading.Event()
        _user_queues[user_id] = done

    result_holder: dict[str, Any] = {}

    def run():
        if prev is not None:
            prev.wait()
        try:
            result_holder["value"] = task()
        except Exception as exc:  # noqa: BLE001
            result_holder["error"] = exc
        finally:
            done.set()
            with _user_queues_lock:
                if _user_queues.get(user_id) is done:
                    del _user_queues[user_id]

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join()
    if "error" in result_holder:
        raise result_holder["error"]
    return result_holder["value"]


def compile_tex(source: str, cancel=None) -> dict[str, Any]:
    tex = make_xetex_compatible(source)
    digest = hashlib.sha256(tex.encode("utf-8")).hexdigest()
    cache_key = f"compiled/{digest}.pdf"

    with _failures_lock:
        failed = _failures.get(digest)
        if failed and failed["until"] > time.time() * 1000:
            return failed["result"]

    cached_pdf = storage.get(cache_key)
    if cached_pdf is not None:
        return {"ok": True, "pdf": cached_pdf, "pageCount": _page_count(cached_pdf), "cached": True}

    if _local_compile is not None:
        result = _local_compile(tex, cancel)
    else:
        result = _remote_compile(tex, cancel)

    if not result.get("ok"):
        with _failures_lock:
            if len(_failures) >= FAILURE_CAP:
                oldest = min(_failures.items(), key=lambda kv: kv[1]["until"])[0]
                del _failures[oldest]
            _failures[digest] = {
                "result": result,
                "until": time.time() * 1000 + FAILURE_TTL_MS,
            }
        return result

    pdf = result["pdf"]
    try:
        storage.put(cache_key, pdf, "application/pdf")
    except Exception:  # noqa: BLE001, S110
        pass
    return {"ok": True, "pdf": pdf, "pageCount": _page_count(pdf), "cached": False}
