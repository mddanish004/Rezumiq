"""Jobs."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_create_from_raw_text(client: Client, db):
    user = make_user()
    client.force_login(user)
    raw = "We are hiring a backend engineer. " + ("x" * 60)
    response = client.post("/v1/jobs", {"rawText": raw}, content_type="application/json")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["rawText"] == raw
    assert data["parsed"] is None

    listed = client.get("/v1/jobs").json()["data"]
    assert len(listed) == 1
    assert "rawText" not in listed[0]

    assert client.get(f"/v1/jobs/{data['id']}").status_code == 200

    assert client.delete(f"/v1/jobs/{data['id']}").status_code == 204


def test_create_invalid_too_short(client: Client, db):
    user = make_user()
    client.force_login(user)
    response = client.post("/v1/jobs", {"rawText": "short"}, content_type="application/json")
    assert response.status_code == 400


def test_job_ownership(client: Client, db):
    user = make_user()
    client.force_login(user)
    raw = "We are hiring. " + ("x" * 60)
    created = client.post("/v1/jobs", {"rawText": raw}, content_type="application/json").json()[
        "data"
    ]
    other = make_user(email="other@example.com", username="other")
    oc = Client()
    oc.force_login(other)
    assert oc.get(f"/v1/jobs/{created['id']}").status_code == 404
    assert oc.delete(f"/v1/jobs/{created['id']}").status_code == 404


def test_job_parsing_uses_ai_and_stores_requirements(client: Client, db, monkeypatch):
    user = make_user()
    client.force_login(user)
    parsed = {
        "company": "Acme",
        "role": "Backend Engineer",
        "seniority": "mid",
        "domain": "fintech",
        "mustHave": ["Go", "Postgres"],
        "niceToHave": ["Kubernetes"],
        "responsibilities": ["Build billing APIs"],
        "keywords": ["Go", "Postgres"],
    }
    seen = {}

    def fake(prompt, **kwargs):
        seen.update(kwargs)
        return {
            "data": parsed,
            "model": "openai/gpt-oss-20b",
            "provider": "groq",
            "tokens": {"input": 10, "cached": 0, "output": 5},
        }

    monkeypatch.setattr("jobs.service._ai_configured", lambda user_id: True)
    monkeypatch.setattr("jobs.service.generate_structured", fake)
    body = {
        "rawText": (
            "Acme is hiring a backend engineer for fintech billing. "
            "You need Go and Postgres, and Kubernetes is a bonus. Build billing APIs."
        )
    }
    response = client.post("/v1/jobs", body, content_type="application/json")
    assert response.status_code == 201
    data = response.json()["data"]
    assert (
        data["parsed"] == parsed
        and data["company"] == "Acme"
        and data["role"] == "Backend Engineer"
    )
    assert seen["schema"]["properties"]["mustHave"]["type"] == "array"

    from ai.models import AiRun

    run = AiRun.objects.get(user=user, step="jd_parse")
    assert run.input_tokens == 10

    monkeypatch.setattr(
        "jobs.service.generate_structured",
        lambda *a, **k: {
            "data": {**parsed, "role": "Senior Backend Engineer"},
            "model": "m",
            "provider": "groq",
            "tokens": {},
        },
    )
    response = client.post(f"/v1/jobs/{data['id']}", content_type="application/json")
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "Senior Backend Engineer"
