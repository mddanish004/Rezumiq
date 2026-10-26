"""User AI keys, ported from modules/ai-keys."""

from __future__ import annotations

from django.utils import timezone

from ai.models import UserAiKey
from ai.secret_box import open_sealed, seal
from api.common.errors import AppError, NotFoundError

PROVIDERS = ("groq", "openai", "anthropic", "openrouter")
GROQ_BASE = "https://api.groq.com/openai/v1"


def _provider_model(provider):
    from ai.generate import DEFAULT_MODELS

    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["groq"])


def has_user_ai_key(user_id) -> bool:
    return UserAiKey.objects.filter(user_id=user_id, enabled=True).exists()


def list_keys(user_id):
    rows = UserAiKey.objects.filter(user_id=user_id).order_by("created_at")
    return [
        {
            "provider": r.provider,
            "enabled": r.enabled,
            "modelId": r.model_id,
            "modelIds": r.model_ids or [],
            "keyHint": r.key_hint,
            "verifiedAt": r.verified_at,
        }
        for r in rows
    ]


def _get(user_id, provider):
    try:
        return UserAiKey.objects.get(user_id=user_id, provider=provider)
    except UserAiKey.DoesNotExist:
        raise NotFoundError("AI key") from None


def delete_key(user_id, provider):
    deleted = UserAiKey.objects.filter(user_id=user_id, provider=provider).delete()
    if deleted[0] == 0:
        raise NotFoundError("AI key")


def _verify(provider, api_key, model_id):
    from ai.generate import _client, _model_id

    model = model_id or _model_id(
        provider, "fast", {"provider": provider, "apiKey": api_key, "modelId": model_id}
    )
    client = _client(provider, api_key)
    try:
        client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "Reply with OK."}], max_tokens=4
        )
    except Exception as exc:
        raise AppError(
            422, "AI_KEY_INVALID", "We couldn't verify this key. Check it and try again."
        ) from exc


def put_key(user_id, provider, api_key, model_id=None):
    if provider not in PROVIDERS:
        raise AppError(400, "INVALID_PROVIDER", "Unknown provider")
    if len(api_key) < 10:
        raise AppError(400, "VALIDATION_ERROR", "API key too short")
    _verify(provider, api_key, model_id)

    UserAiKey.objects.filter(user_id=user_id).exclude(provider=provider).update(enabled=False)
    hint = api_key[-4:]
    sealed = seal(api_key)
    row, _created = UserAiKey.objects.update_or_create(
        user_id=user_id,
        provider=provider,
        defaults={
            "enabled": True,
            "model_id": model_id,
            "encrypted_key": sealed,
            "key_hint": hint,
            "verified_at": timezone.now(),
        },
    )
    return {
        "provider": row.provider,
        "enabled": row.enabled,
        "modelId": row.model_id,
        "modelIds": row.model_ids or [],
        "keyHint": row.key_hint,
        "verifiedAt": row.verified_at,
    }


def update_key(user_id, provider, enabled=None, model_id=None):
    row = _get(user_id, provider)
    if enabled is not None:
        if enabled:
            UserAiKey.objects.filter(user_id=user_id).exclude(provider=provider).update(
                enabled=False
            )
        row.enabled = enabled
    if model_id is not None:
        row.model_id = model_id
    row.save()
    return {
        "provider": row.provider,
        "enabled": row.enabled,
        "modelId": row.model_id,
        "modelIds": row.model_ids or [],
        "keyHint": row.key_hint,
        "verifiedAt": row.verified_at,
    }


def list_models(user_id, provider):
    row = _get(user_id, provider)
    api_key = open_sealed(row.encrypted_key)
    try:
        from openai import OpenAI

        base = GROQ_BASE if provider == "groq" else "https://api.openai.com/v1"
        client = OpenAI(api_key=api_key, base_url=base)
        resp = client.models.list()
        return [{"id": m.id, "name": getattr(m, "id", m.id)} for m in resp.data]
    except Exception:  # noqa: BLE001
        raise AppError(
            502,
            "AI_MODELS_UNAVAILABLE",
            "We couldn't load the model list. Enter a model ID instead.",
        )
