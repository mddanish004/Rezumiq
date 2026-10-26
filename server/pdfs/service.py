"""PDF rendering helpers, ported from modules/pdfs/pdfs.service.ts."""

from __future__ import annotations

import json
import re
import unicodedata

from api.common.errors import AppError, NotFoundError
from latex.compile import compile_tex
from resumes.content import ResumeContent
from resumes.service import layout_instance
from templates import find_template
from templates.layout import ResumeLayout


def render_structured(template_id, content, layout=None):
    template = find_template(template_id or "developer")
    if not template:
        raise NotFoundError("Template")
    if isinstance(content, dict):
        content = ResumeContent.model_validate(content)
    rl = layout if isinstance(layout, ResumeLayout) else layout_instance(layout)
    return template.render(content, rl)


def tex_for_version(resume, version):
    if version.get("content") is not None:
        return render_structured(
            resume.get("template_id") or resume.get("templateId"),
            version["content"],
            resume.get("layout"),
        )
    return version.get("tex_source") or version.get("texSource")


def compile_or_throw(tex, cancel=None):
    result = compile_tex(tex, cancel)
    if not result.get("ok"):
        raise AppError(
            422, "COMPILE_FAILED", "The resume could not be compiled", result.get("errors")
        )
    return result


def slugify(value, max_length=24):
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    text = text[:max_length]
    text = text.rstrip("-")
    return text


def pdf_file_name(person, title):
    if re.search(
        r"\b(resume|cv)\b", (title or "").replace("_", " ").replace("-", " "), re.IGNORECASE
    ):
        parts = [title]
    else:
        parts = [person, title]
    slugs = []
    for part in parts:
        s = slugify(part or "", 40)
        if s and s not in slugs:
            slugs.append(s)
    filtered = [s for s in slugs if not any(o != s and s in o for o in slugs)]
    name = "_".join(filtered)
    return f"{name or 'resume'}.pdf"


def to_json_resume(content):
    if isinstance(content, dict):
        content = ResumeContent.model_validate(content)

    inline_link = re.compile(r"\[([^\]\n]+)\]\(((?:https?://|mailto:)[^\s)]+)\)")

    def bullets(items):
        return [
            inline_link.sub(lambda m: f"{m.group(1)} ({m.group(2)})", b.text).replace("**", "")
            for b in items
            if not b.hidden
        ]

    def add(key, items):
        out[key] = (out.get(key) or []) + items

    out = {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": {
            "name": content.basics.name,
            "label": content.basics.headline,
            "email": content.basics.email,
            "phone": content.basics.phone,
            "location": {"address": content.basics.location} if content.basics.location else None,
            "profiles": [{"network": link.label, "url": link.url} for link in content.basics.links],
        },
    }

    for section in content.sections:
        if section.hidden:
            continue
        st = section.type
        if st == "experience":
            add(
                "work",
                [
                    {
                        "name": e.organization,
                        "position": e.role,
                        "location": e.location,
                        "startDate": e.start,
                        "endDate": None if e.end == "present" else e.end,
                        "highlights": bullets(e.bullets),
                    }
                    for e in section.entries
                    if not e.hidden
                ],
            )
        elif st == "education":
            add(
                "education",
                [
                    {
                        "institution": e.institution,
                        "studyType": e.degree,
                        "area": e.field,
                        "score": e.score,
                        "startDate": e.start,
                        "endDate": None if e.end == "present" else e.end,
                    }
                    for e in section.entries
                    if not e.hidden
                ],
            )
        elif st == "projects":
            add(
                "projects",
                [
                    {
                        "name": e.name,
                        "url": e.url or (e.links[0].url if e.links else None),
                        "keywords": e.technologies,
                        "startDate": e.start,
                        "endDate": None if e.end == "present" else e.end,
                        "highlights": bullets(e.bullets),
                    }
                    for e in section.entries
                    if not e.hidden
                ],
            )
        elif st == "skills":
            add("skills", [{"name": g.name, "keywords": g.items} for g in section.groups])
        elif st == "list":
            add(
                "awards",
                [
                    {"title": e.title, "summary": e.subtitle, "date": e.date}
                    for e in section.entries
                    if not e.hidden
                ],
            )
        elif st == "summary":
            out["basics"]["summary"] = section.text or None
        elif st == "links":
            out["basics"]["profiles"] = (out["basics"].get("profiles") or []) + [
                {"network": link.label, "url": link.url} for link in section.links
            ]

    return json.loads(json.dumps(out))
