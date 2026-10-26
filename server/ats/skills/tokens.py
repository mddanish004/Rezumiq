"""Skill tokenization, ported from modules/ats/skills/tokens.ts."""

from __future__ import annotations

import re

TOKEN = re.compile(r"(?<![\w])\.?[\w]+(?:\.[\w]+)*[+#]*", re.UNICODE)


def tokenize(text: str):
    out = []
    for m in TOKEN.finditer(text):
        raw = m.group(0)
        out.append({"raw": raw, "key": raw.lower(), "start": m.start(), "end": m.end()})
    return out


def name_key(name: str) -> str:
    return " ".join(t["key"] for t in tokenize(name))
