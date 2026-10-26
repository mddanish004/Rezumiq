"""Suggestions."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_create_requires_ai_config(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    r = client.post(
        f"/v1/resumes/{resume['id']}/suggestions",
        {"type": "edit", "instruction": "tighten bullets"},
        content_type="application/json",
    )
    assert r.status_code == 503


def test_operations_pure():
    from suggestions.operations import apply_operations, is_applicable

    content = {
        "basics": {"name": "A", "headline": "H", "links": []},
        "sections": [
            {
                "id": "s1",
                "type": "experience",
                "title": "Exp",
                "entries": [
                    {
                        "id": "e1",
                        "organization": "X",
                        "role": "Y",
                        "start": "2020",
                        "end": "2021",
                        "bullets": [{"id": "b1", "text": "Did thing", "hidden": False}],
                        "hidden": False,
                    }
                ],
                "hidden": False,
            }
        ],
    }
    op = {
        "type": "update_bullet",
        "id": "op1",
        "bulletId": "b1",
        "text": "Did great thing",
        "reason": "r",
        "flags": [],
    }
    assert is_applicable(content, op) is True
    new = apply_operations(content, [op])
    assert new["sections"][0]["entries"][0]["bullets"][0]["text"] == "Did great thing"


def test_fact_text_accepts_the_content_model():
    from resumes.content import ResumeContent
    from suggestions.operations import fact_text

    content = ResumeContent.model_validate(
        {"basics": {"name": "Aarav Sharma", "links": []}, "sections": []}
    )
    assert "Aarav Sharma" in fact_text(content)


def test_suggestion_quota_is_charged_per_tailor(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    job = client.post(
        "/v1/jobs",
        {
            "rawText": "Backend engineer with Go and Postgres. Build billing APIs. Three years experience."
        },
        content_type="application/json",
    ).json()["data"]
    monkeypatch.setattr(
        "suggestions.service.generate_structured",
        lambda *a, **k: {
            "data": {
                "summary": "Tightened",
                "operations": [
                    {
                        "type": "update_bullet",
                        "targetId": "b1",
                        "text": "Cut latency by 40%",
                        "reason": "shorten",
                        "hidden": None,
                        "points": None,
                        "orderedIds": None,
                        "items": None,
                    }
                ],
            },
            "model": "m",
            "provider": "groq",
            "tokens": {},
        },
    )
    first = client.post(
        f"/v1/resumes/{resume['id']}/suggestions",
        {"type": "tailor", "jobId": job["id"]},
        content_type="application/json",
    )
    assert first.status_code == 201
    usage = client.get("/v1/usage").json()["data"]
    assert usage["tailor"]["used"] == 1

    second = client.post(
        f"/v1/resumes/{resume['id']}/suggestions",
        {"type": "tailor", "jobId": job["id"]},
        content_type="application/json",
    )
    assert second.status_code == 402
    assert second.json()["error"]["code"] == "QUOTA_EXCEEDED"


def test_scoped_target_ids_are_in_the_prompt_and_filter_operations(monkeypatch, db):
    from suggestions.service import create_suggestion

    user = make_user()
    client = Client()
    client.force_login(user)
    scoped_content = {
        "basics": {"name": "A", "headline": "H", "links": []},
        "sections": [
            {"id": "sum", "type": "summary", "title": "Summary", "text": "Old summary."},
            {
                "id": "exp",
                "type": "experience",
                "title": "Experience",
                "entries": [
                    {
                        "id": "e1",
                        "organization": "Acme",
                        "role": "Engineer",
                        "bullets": [{"id": "b1", "text": "Built things"}],
                    }
                ],
            },
        ],
    }
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": scoped_content}},
        content_type="application/json",
    ).json()["data"]
    seen = {}

    def fake(prompt, **kwargs):
        seen["prompt"] = prompt
        return {
            "data": {
                "summary": "Polish",
                "operations": [
                    {
                        "type": "update_summary",
                        "targetId": "sum",
                        "text": "A tighter summary.",
                        "reason": "shorten",
                        "hidden": None,
                        "points": None,
                        "orderedIds": None,
                        "items": None,
                    },
                    {
                        "type": "update_bullet",
                        "targetId": "b1",
                        "text": "Outside scope",
                        "reason": "nope",
                        "hidden": None,
                        "points": None,
                        "orderedIds": None,
                        "items": None,
                    },
                ],
            },
            "model": "m",
            "provider": "groq",
            "tokens": {},
        }

    monkeypatch.setattr("suggestions.service.generate_structured", fake)
    suggestion = create_suggestion(
        user.id,
        resume["id"],
        {"type": "edit", "instruction": "Polish the summary", "target_ids": ["sum"]},
    )
    assert "Only change the content whose ids are listed" in seen["prompt"]
    assert [op["type"] for op in suggestion["operations"]] == ["update_summary"]

    applied = client.post(
        f"/v1/resumes/{resume['id']}/suggestions/{suggestion['id']}/apply",
        {"acceptedOperationIds": [suggestion["operations"][0]["id"]]},
        content_type="application/json",
    )
    assert applied.status_code == 200
    assert (
        applied.json()["data"]["version"]["content"]["sections"][0]["text"] == "A tighter summary."
    )


def test_fix_compile_returns_and_applies_tex_source(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {
            "title": "Code",
            "mode": "code",
            "source": {
                "type": "tex",
                "texSource": "\\documentclass{article}\\n\\begin{document}\\nHi\\n\\end{document}",
            },
        },
        content_type="application/json",
    ).json()["data"]
    fixed = "\\documentclass{article}\\n\\begin{document}\\nFixed\\n\\end{document}"
    monkeypatch.setattr(
        "suggestions.service.generate_structured",
        lambda *a, **k: {
            "data": {"summary": "Fixed", "texSource": fixed, "reason": "escape"},
            "model": "m",
            "provider": "groq",
            "tokens": {},
        },
    )
    response = client.post(
        f"/v1/resumes/{resume['id']}/suggestions",
        {"type": "fix_compile"},
        content_type="application/json",
    )
    assert response.status_code == 201
    suggestion = response.json()["data"]
    assert suggestion["operations"][0]["type"] == "replace_source"
    applied = client.post(
        f"/v1/resumes/{resume['id']}/suggestions/{suggestion['id']}/apply",
        {"acceptedOperationIds": [suggestion["operations"][0]["id"]]},
        content_type="application/json",
    )
    assert applied.status_code == 200
    assert applied.json()["data"]["version"]["texSource"] == fixed
