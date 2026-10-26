"""Resume import and AI draft endpoints, plus extraction normalization."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


EXTRACTION = {
    "basics": {
        "name": "Aarav Sharma",
        "headline": "Backend Engineer",
        "email": "aarav@example.com",
        "phone": "+91 98765 43210",
        "location": "Bengaluru",
        "links": [{"label": "github.com/aarav", "url": "github.com/aarav"}],
    },
    "sections": [
        {
            "type": "experience",
            "title": "Experience",
            "entries": [
                {
                    "organization": "Acme",
                    "role": "Backend Engineer at Acme",
                    "start": "2024-01",
                    "end": "present",
                    "bullets": ["• Built the billing API", "- Scaled it to 2M requests"],
                }
            ],
        },
        {
            "type": "skills",
            "title": "Skills",
            "groups": [{"name": "Languages:", "items": ["Go", "Python"]}],
        },
    ],
}


def test_import_requires_auth(client: Client, db):
    response = client.post("/v1/imports", {"text": "x" * 20}, content_type="application/json")
    assert response.status_code == 401


def test_import_text_normalizes_and_logs(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    monkeypatch.setattr(
        "imports.service.generate_structured",
        lambda *a, **k: {
            "data": EXTRACTION,
            "model": "llama-3.3-70b-versatile",
            "provider": "groq",
            "tokens": {"input": 10, "cached": 0, "output": 5},
        },
    )
    response = client.post(
        "/v1/imports",
        {"text": "Aarav Sharma, backend engineer since 2024."},
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["content"]["basics"]["name"] == "Aarav Sharma"
    link = data["content"]["basics"]["links"][0]
    assert link["label"] == "GitHub" and link["url"] == "https://github.com/aarav"
    experience = data["content"]["sections"][0]
    assert experience["type"] == "experience"
    entry = experience["entries"][0]
    assert entry["role"] == "Backend Engineer"
    assert entry["end"] == "present" and entry["start"] == "2024-01"
    assert [b["text"] for b in entry["bullets"]] == [
        "Built the billing API",
        "Scaled it to 2M requests",
    ]
    assert data["content"]["sections"][1]["groups"][0]["name"] == "Languages"
    assert data["missed"] == []
    from ai.models import AiRun

    run = AiRun.objects.get(id=data["aiRunId"])
    assert run.step == "import" and run.status == "succeeded" and run.input_tokens == 10


def test_import_prompt_carries_text(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    seen = {}

    def fake(prompt, **kwargs):
        seen["prompt"] = prompt
        return {"data": EXTRACTION, "model": "m", "provider": "groq", "tokens": {}}

    monkeypatch.setattr("imports.service.generate_structured", fake)
    client.post(
        "/v1/imports",
        {"text": "Aarav Sharma, backend engineer since 2024."},
        content_type="application/json",
    )
    assert "<resume>" in seen["prompt"] and "Aarav Sharma" in seen["prompt"]


def test_import_short_text_rejected(client: Client, db):
    client.force_login(make_user())
    response = client.post("/v1/imports", {"text": "short"}, content_type="application/json")
    assert response.status_code == 400


def test_import_model_failure_marks_run_failed(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)

    def fail(*a, **k):
        raise RuntimeError("AI not configured")

    monkeypatch.setattr("imports.service.generate_structured", fail)
    response = client.post(
        "/v1/imports",
        {"text": "Aarav Sharma, backend engineer since 2024."},
        content_type="application/json",
    )
    assert response.status_code == 500
    from ai.models import AiRun

    run = AiRun.objects.get(user=user, step="import")
    assert run.status == "failed"


def test_draft_fills_account_name_and_email(client: Client, db, monkeypatch):
    user = make_user(name="Saurav Jha")
    client.force_login(user)
    monkeypatch.setattr(
        "imports.service.generate_structured",
        lambda *a, **k: {
            "data": {"basics": {"name": None, "links": []}, "sections": []},
            "model": "m",
            "provider": "groq",
            "tokens": {},
        },
    )
    response = client.post(
        "/v1/resume-drafts",
        {"role": "Backend Engineer", "notes": "I built billing APIs in Go at Acme for two years."},
        content_type="application/json",
    )
    assert response.status_code == 201
    content = response.json()["data"]["content"]
    assert content["basics"]["name"] == "Saurav Jha"
    assert content["basics"]["email"] == "saurav@example.com"


def test_draft_quota_is_once_on_free(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    monkeypatch.setattr(
        "imports.service.generate_structured",
        lambda *a, **k: {
            "data": {"basics": {"name": "A", "links": []}, "sections": []},
            "model": "m",
            "provider": "groq",
            "tokens": {},
        },
    )
    payload = {
        "role": "Backend Engineer",
        "notes": "I built billing APIs in Go at Acme for two years.",
    }
    assert (
        client.post("/v1/resume-drafts", payload, content_type="application/json").status_code
        == 201
    )
    second = client.post("/v1/resume-drafts", payload, content_type="application/json")
    assert second.status_code == 402
    assert second.json()["error"]["code"] == "QUOTA_EXCEEDED"
    assert "free AI-written resume" in second.json()["error"]["message"]


def test_normalize_extraction_edges():
    from imports.extraction import normalize_extraction

    content = normalize_extraction(
        {
            "basics": {"name": "A", "headline": "x" * 120, "links": []},
            "sections": [
                {
                    "type": "projects",
                    "title": "Projects",
                    "entries": [
                        {
                            "name": "LedgerLite",
                            "start": "2024",
                            "end": "2024",
                            "bullets": ["Tech Stack: Go, Kafka, Postgres", "Built a ledger"],
                        }
                    ],
                },
                {
                    "type": "list",
                    "title": "Achievements",
                    "entries": [{"title": "**Winner:** Smart India Hackathon", "bullets": []}],
                },
            ],
        }
    )
    sections = content["sections"]
    assert sections[0]["type"] == "summary" and sections[0]["text"] == "x" * 120
    project = sections[1]["entries"][0]
    assert project["technologies"] == ["Go", "Kafka", "Postgres"]
    assert project.get("start") is None and project["end"] == "2024"
    assert [b["text"] for b in project["bullets"]] == ["Built a ledger"]
    achievement = sections[2]["entries"][0]
    assert achievement["title"] == "Winner" and achievement["subtitle"] == "Smart India Hackathon"


def test_apply_bold_marks_whole_words():
    from imports.extraction import apply_bold

    content = {
        "basics": {"name": "A", "links": []},
        "sections": [
            {
                "id": "s",
                "title": "Summary",
                "hidden": False,
                "type": "summary",
                "text": "Used Go and Google",
            }
        ],
    }
    out = apply_bold(content, ["Go"])
    assert out["sections"][0]["text"] == "Used **Go** and Google"


def test_import_and_draft_send_the_extraction_schema(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    seen = []

    def fake(prompt, **kwargs):
        seen.append(kwargs.get("schema"))
        return {
            "data": {"basics": {"name": "A", "links": []}, "sections": []},
            "model": "m",
            "provider": "groq",
            "tokens": {},
        }

    monkeypatch.setattr("imports.service.generate_structured", fake)
    client.post(
        "/v1/imports",
        {"text": "Aarav Sharma, backend engineer since 2024."},
        content_type="application/json",
    )
    client.post(
        "/v1/resume-drafts",
        {"role": "Backend Engineer", "notes": "I built billing APIs in Go at Acme for two years."},
        content_type="application/json",
    )
    assert len(seen) == 2
    for schema in seen:
        basics = schema["$defs"]["AiBasics"]
        assert basics["properties"]["name"]["type"] == "string"
        assert "sections" in schema["properties"]
