"""AI generation, ported from lib/ai/generate.ts. Groq is the default provider."""

from __future__ import annotations

import json

from django.conf import settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

DEFAULT_MODELS = {
    "groq": {"fast": "openai/gpt-oss-20b", "smart": "openai/gpt-oss-120b"},
    "openai": {"fast": "gpt-4o-mini", "smart": "gpt-4o"},
}


def _provider_and_key(user_key=None):
    provider = (user_key or {}).get("provider") or getattr(settings, "AI_PROVIDER", "groq")
    if user_key and user_key.get("apiKey"):
        api_key = user_key["apiKey"]
    elif provider == "groq":
        api_key = getattr(settings, "GROQ_API_KEY", None)
    elif provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", None)
    else:
        api_key = None
    if not api_key:
        raise RuntimeError("AI not configured")
    return provider, api_key


def _model_id(provider, tier, user_key=None):
    if user_key and user_key.get("modelId"):
        return user_key["modelId"]
    override = getattr(settings, "AI_MODEL_FAST" if tier == "fast" else "AI_MODEL_SMART", None)
    if override:
        return override
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["groq"])[tier]


def _client(provider, api_key):
    from openai import OpenAI

    base_url = GROQ_BASE_URL if provider == "groq" else OPENAI_BASE_URL
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_text(prompt, *, tier="fast", system=None, user_key=None, max_tokens=1024):
    provider, api_key = _provider_and_key(user_key)
    model_id = _model_id(provider, tier, user_key)
    client = _client(provider, api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(model=model_id, messages=messages, max_tokens=max_tokens)
    return resp.choices[0].message.content or ""


def _schema_text(schema) -> str:
    """The JSON shape the model must fill. The TS version sent this through generateObject;
    here it goes into the prompt, which every provider reads."""
    if hasattr(schema, "model_json_schema"):
        schema = schema.model_json_schema()
    return json.dumps(schema, separators=(",", ":"))


def generate_structured(
    prompt, *, tier="fast", system=None, schema=None, user_key=None, max_tokens=2048
):
    provider, api_key = _provider_and_key(user_key)
    model_id = _model_id(provider, tier, user_key)
    client = _client(provider, api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    json_prompt = prompt
    if schema is not None:
        json_prompt += (
            "\n\nRespond with one JSON object matching this JSON Schema. "
            "Include every field; use null where the resume says nothing:\n" + _schema_text(schema)
        )
    json_prompt += "\n\nRespond with valid JSON only, no markdown fences."
    messages.append({"role": "user", "content": json_prompt})

    def ask():
        return client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

    try:
        resp = ask()
    except Exception as exc:
        if "json_validate_failed" not in str(exc):
            raise
        messages.append(
            {
                "role": "user",
                "content": "Your reply was not valid JSON. Reply with a single JSON object only.",
            }
        )
        resp = ask()
    text = resp.choices[0].message.content or "{}"
    data = json.loads(text)
    usage = getattr(resp, "usage", None)
    details = getattr(usage, "prompt_tokens_details", None)
    return {
        "data": data,
        "model": model_id,
        "provider": provider,
        "tokens": {
            "input": getattr(usage, "prompt_tokens", 0) or 0,
            "cached": getattr(details, "cached_tokens", 0) or 0,
            "output": getattr(usage, "completion_tokens", 0) or 0,
        },
    }
