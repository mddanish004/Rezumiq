"""AI run history endpoint and model pricing."""

import pytest
from django.core.management import call_command
from django.test import Client

from ai.models import AiRun
from ai.pricing import cost_usd_micros, known_cost_usd_micros
from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_pricing_known_and_unknown_models():
    assert (
        cost_usd_micros("gpt-5.4-mini", {"input": 1_000_000, "cached": 0, "output": 0}) == 750_000
    )
    assert (
        cost_usd_micros("gpt-5.4-mini", {"input": 1_000_000, "cached": 1_000_000, "output": 0})
        == 75_000
    )
    assert (
        cost_usd_micros("openai/gpt-5.4-mini", {"input": 1_000_000, "cached": 0, "output": 0})
        == 750_000
    )
    assert (
        cost_usd_micros("llama-3.3-70b-versatile", {"input": 100, "cached": 0, "output": 100}) == 0
    )
    assert known_cost_usd_micros(0, 10, 5) is None
    assert known_cost_usd_micros(0, 0, 0) == 0


def test_ai_runs_requires_auth(client: Client, db):
    assert client.get("/v1/me/ai-runs").status_code == 401


def test_ai_runs_lists_usage_only(client: Client, db):
    user = make_user()
    other = make_user(email="other@example.com", username="other")
    AiRun.objects.create(
        user=user,
        step="rewrite",
        status="succeeded",
        model="groq:llama",
        cost_usd_micros=12,
        input_tokens=10,
        output_tokens=5,
        latency_ms=90,
    )
    AiRun.objects.create(
        user=user,
        step="draft",
        status="failed",
        model="groq:llama",
        cost_usd_micros=0,
        input_tokens=0,
        output_tokens=0,
        error="boom",
        latency_ms=None,
    )
    AiRun.objects.create(user=other, step="import", status="succeeded", model="groq:llama")

    client.force_login(user)
    data = client.get("/v1/me/ai-runs").json()["data"]
    assert data["monthCostUsdMicros"] == 12
    assert data["monthUnpricedRuns"] == 0
    assert len(data["runs"]) == 2
    assert data["runs"][0]["step"] == "draft"
    assert data["runs"][0]["costUsdMicros"] == 0
    assert data["runs"][1]["costUsdMicros"] == 12
    assert "error" not in data["runs"][0]


def test_schema_is_included_in_the_prompt():
    from ai.generate import _schema_text

    class Out:
        @staticmethod
        def model_json_schema():
            return {"type": "object", "properties": {"name": {"type": "string"}}}

    assert '"name"' in _schema_text(Out)
    assert '"type":"object"' in _schema_text({"type": "object"})


def test_json_validation_failure_is_retried_once(monkeypatch):
    from types import SimpleNamespace

    import ai.generate as gen

    calls = []

    class Completions:
        def create(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError("json_validate_failed: empty generation")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))],
                usage=SimpleNamespace(
                    prompt_tokens=3, completion_tokens=2, prompt_tokens_details=None
                ),
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    monkeypatch.setattr(gen, "_provider_and_key", lambda user_key=None: ("groq", "key"))
    monkeypatch.setattr(gen, "_client", lambda provider, api_key: client)

    result = gen.generate_structured("say ok", schema={"type": "object"})
    assert result["data"] == {"ok": True}
    assert len(calls) == 2
    assert "not valid JSON" in calls[1]["messages"][-1]["content"]
