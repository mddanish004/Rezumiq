"""Prompt redaction, ported from lib/ai/redact.ts.

Replaces the user's sensitive values in a prompt with placeholders like
"[email 1]"; restore() puts the real values back into anything the model
returns, so they never leave the server.
"""

from __future__ import annotations

import json
import re
from typing import Any

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_PATTERN = re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{7,}\d|\b[6-9]\d{9}\b")


def sensitive_values(content) -> list[tuple[str, str | None]]:
    from resumes.content import ResumeContent

    if not isinstance(content, ResumeContent):
        content = ResumeContent.model_validate(content)
    basics = content.basics
    links = list(basics.links)
    for section in content.sections:
        if section.type == "links":
            links.extend(section.links)
        elif section.type == "projects":
            for entry in section.entries:
                links.extend(entry.links)
    found: list[tuple[str, str | None]] = [
        ("email", basics.email),
        ("phone", basics.phone),
        ("name", basics.name if "name" in (basics.sensitive or []) else None),
        ("location", basics.location if "location" in (basics.sensitive or []) else None),
        *[("link", link.url) for link in links if link.sensitive],
        *[
            ("company", entry.organization)
            for section in content.sections
            if section.type == "experience"
            for entry in section.entries
            if entry.sensitive
        ],
    ]
    return found


def _escape(text: str) -> str:
    return re.sub(r"[.*+?^${}()|[\]\\]", lambda match: "\\" + match.group(0), text)


def _map_strings(value: Any, fn) -> Any:
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, list):
        return [_map_strings(item, fn) for item in value]
    if isinstance(value, dict):
        return {key: _map_strings(item, fn) for key, item in value.items()}
    return value


class Redacted:
    def __init__(self, text: str, originals: dict[str, str] | None):
        self.text = text
        self._originals = originals

    def restore(self, value):
        if self._originals is None:
            return value
        pattern = re.compile(
            "|".join(_escape(p) for p in sorted(self._originals, key=len, reverse=True))
        )

        def fill(text: str) -> str:
            return pattern.sub(lambda m: self._originals[m.group(0)], text)

        return _map_strings(value, fill)


def redact(prompt: str, contents) -> Redacted:
    found = [pair for content in contents for pair in sensitive_values(content)]
    found += [("email", m.group(0)) for m in EMAIL_PATTERN.finditer(prompt)]
    found += [("phone", m.group(0).strip()) for m in PHONE_PATTERN.finditer(prompt)]

    placeholders: dict[str, str] = {}
    originals: dict[str, str] = {}
    counts: dict[str, int] = {}
    for kind, raw in found:
        value = (raw or "").strip()
        if not value or len(value) < 2:
            continue
        variants = [value, json.dumps(value)[1:-1], re.sub(r"[&%_#$]", r"\\\g<0>", value)]
        key = next((v.lower() for v in variants if v.lower() in placeholders), None)
        if key:
            continue
        counts[kind] = counts.get(kind, 0) + 1
        placeholder = f"[{kind} {counts[kind]}]"
        originals[placeholder] = value
        for v in variants:
            placeholders[v.lower()] = placeholder

    if not placeholders:
        return Redacted(prompt, None)

    alternatives = sorted((re.escape(v) for v in placeholders), key=len, reverse=True)
    pattern = re.compile(
        rf"(?<![A-Za-z0-9])(?:{'|'.join(alternatives)})(?![A-Za-z0-9])", re.IGNORECASE
    )

    def mask(text: str) -> str:
        return pattern.sub(lambda m: placeholders[m.group(0).lower()], text)

    return Redacted(_map_strings(prompt, mask), originals)
