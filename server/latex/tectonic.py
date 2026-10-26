"""Tectonic invocation, ported from lib/latex/tectonic.ts.

No imports from Django settings here: the standalone compiler process must
run without app secrets, and these helpers stay pure functions of their input.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

MAX_LOG_CHARS = 1_000_000
MAX_PDF_BYTES = 10_000_000

PdftexOnly = [
    re.compile(r"^\s*\\input\{glyphtounicode\}.*$", re.MULTILINE),
    re.compile(r"^\s*\\pdfgentounicode\s*=\s*1.*$", re.MULTILINE),
]


def make_xetex_compatible(source: str) -> str:
    tex = source
    for pattern in PdftexOnly:
        tex = pattern.sub("% removed: pdfTeX-only", tex)
    return tex


HINTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"Misplaced alignment tab character &"), "Write \\& for a literal ampersand."),
    (
        re.compile(r"Missing \$ inserted"),
        "Characters like _ ^ or $ need a backslash, e.g. \\_ or \\$.",
    ),
    (
        re.compile(r"Undefined control sequence"),
        "A command is misspelled or its package is missing.",
    ),
    (
        re.compile(r"File `(.+)' not found"),
        "This package or file isn't available. Remove it or use a supported package.",
    ),
    (
        re.compile(r"File ended while scanning|Emergency stop|end of file", re.IGNORECASE),
        "A brace { or environment \\begin{...} is probably not closed.",
    ),
]


def parse_errors(output: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for raw in output.split("\n"):
        match = re.match(r"^error: (?:[^:]*\.tex:(\d+): )?(.+)$", raw)
        if not match:
            continue
        message = match.group(2).strip().removeprefix("! ").strip()
        if re.search(
            r"something bad happened|unrecoverable error|halted on potentially-recoverable", message
        ):
            continue
        hint = None
        for pattern, text in HINTS:
            if pattern.search(message):
                hint = text
                break
        entry: dict[str, Any] = {
            "line": int(match.group(1)) if match.group(1) else None,
            "message": message,
        }
        if hint:
            entry["hint"] = hint
        errors.append(entry)
    if not errors:
        errors.append({"line": None, "message": "LaTeX compilation failed"})
    return errors


def create_tectonic(
    bin_path: str, only_cached: bool, timeout_ms: int, concurrency: int
) -> Callable:
    running = 0
    waiting: list[threading.Event] = []
    lock = threading.Lock()
    cond = threading.Condition(lock)

    def compile_fn(source: str, cancel=None) -> dict[str, Any]:
        nonlocal running
        slot_acquired = threading.Event()

        def acquire():
            nonlocal running
            with cond:
                while running >= concurrency:
                    ev = threading.Event()
                    waiting.append(ev)
                    cond.release()
                    ev.wait()
                    cond.acquire()
                running += 1
                slot_acquired.set()

        acquire()
        try:
            if cancel is not None and getattr(cancel, "is_set", lambda: False)():
                raise RuntimeError("aborted")
            if hasattr(cancel, "throw_if_aborted"):
                cancel.throw_if_aborted()
            dir_path = tempfile.mkdtemp(prefix="rb-tex-")
            try:
                tex = make_xetex_compatible(source)
                main_tex = Path(dir_path) / "main.tex"
                main_tex.write_text(tex, encoding="utf-8")
                args = ["--untrusted", "--chatter", "minimal"]
                if only_cached:
                    args.append("--only-cached")
                args.append("main.tex")

                env = {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", dir_path),
                    "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME", ""),
                }
                timed_out = False
                output_parts: list[str] = []
                total = 0

                def collect(chunk: bytes) -> None:
                    nonlocal total
                    if total < MAX_LOG_CHARS:
                        text = chunk.decode("utf-8", errors="replace")
                        output_parts.append(text)
                        total += len(text)

                proc = subprocess.Popen(
                    [bin_path, *args],
                    cwd=dir_path,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                import threading as _t

                reader_done = _t.Event()

                def reader():
                    try:
                        for chunk in iter(lambda: proc.stdout.read(4096), b""):
                            if not chunk:
                                break
                            collect(chunk)
                    finally:
                        reader_done.set()

                rt = _t.Thread(target=reader, daemon=True)
                rt.start()
                try:
                    proc.wait(timeout=timeout_ms / 1000.0)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    proc.kill()
                    proc.wait()
                reader_done.wait(timeout=2)
                output = "".join(output_parts)[:MAX_LOG_CHARS]

                if cancel is not None and getattr(cancel, "is_set", lambda: False)():
                    raise RuntimeError("aborted")

                if timed_out:
                    return {
                        "ok": False,
                        "errors": [
                            {
                                "line": None,
                                "message": "Compilation took too long and was stopped",
                                "hint": "Check for loops or very large content.",
                            }
                        ],
                    }
                if proc.returncode != 0:
                    return {"ok": False, "errors": parse_errors(output)}

                pdf_path = Path(dir_path) / "main.pdf"
                size = pdf_path.stat().st_size
                if size > MAX_PDF_BYTES:
                    return {
                        "ok": False,
                        "errors": [
                            {
                                "line": None,
                                "message": "The PDF is larger than 10 MB",
                                "hint": "Shorten the content or shrink images.",
                            }
                        ],
                    }
                return {"ok": True, "pdf": pdf_path.read_bytes()}
            finally:
                shutil.rmtree(dir_path, ignore_errors=True)
        finally:
            with cond:
                running -= 1
                if waiting:
                    ev = waiting.pop(0)
                    ev.set()
                cond.notify_all()

    return compile_fn
