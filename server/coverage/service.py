"""Coverage report, ported from modules/coverage/coverage.ts."""

from __future__ import annotations

import json
import re

from resumes.content import ResumeContent, plain_text
from templates.latex import visible_content


def _normalize(value: str) -> str:
    text = plain_text(value).lower()
    text = re.sub(r"[^a-z0-9.+#/ ]+", " ", text)
    text = re.sub(r"\.(?=\s|$)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return f" {text} "


def _mentions(haystack: str, term: str) -> bool:
    needle = _normalize(term).strip()
    return bool(needle) and f" {needle} " in haystack


def coverage_report(requirements, resume, profile) -> dict:
    if resume.get("content") is not None:
        content = ResumeContent.model_validate(resume["content"])
        vc = visible_content(content)
        sections = [
            {"title": s.title, "text": _normalize(json.dumps(s.model_dump(mode="json")))}
            for s in vc.sections
        ]
        basics = _normalize(json.dumps(content.basics.model_dump(mode="json")))
    else:
        sections = [
            {
                "title": "LaTeX source",
                "text": _normalize(resume.get("tex_source") or resume.get("texSource") or ""),
            }
        ]
        basics = ""
    profile_text = _normalize(
        json.dumps(profile.model_dump(mode="json"))
        if hasattr(profile, "model_dump")
        else json.dumps(profile)
    )

    def check(term):
        found_in = [s["title"] for s in sections if _mentions(s["text"], term)]
        if found_in or _mentions(basics, term):
            status = "covered"
        elif _mentions(profile_text, term):
            status = "in_profile"
        else:
            status = "missing"
        return {"requirement": term, "status": status, "foundIn": found_in}

    def unique(items):
        seen = set()
        out = []
        for i in items:
            t = (i or "").strip()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    must_have = [check(t) for t in unique(requirements.get("mustHave", []))]
    nice_to_have = [check(t) for t in unique(requirements.get("niceToHave", []))]
    keywords = [check(t) for t in unique(requirements.get("keywords", []))]

    counted = must_have + nice_to_have
    return {
        "covered": sum(1 for r in counted if r["status"] == "covered"),
        "total": len(counted),
        "mustHave": must_have,
        "niceToHave": nice_to_have,
        "keywords": keywords,
    }
