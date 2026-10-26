import sys

import pytest
from django.core.cache import cache

PROVIDER_ENV = (
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "DODO_API_KEY",
    "DODO_WEBHOOK_KEY",
    "DODO_SEASON_PASS_PRODUCT_ID",
    "DODO_PRO_PRODUCT_ID",
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Rate-limit counters live in the process cache; no test inherits another's budget."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def no_live_providers(settings, monkeypatch):
    """The developer's .env must never make the suite call a real provider."""
    for name in PROVIDER_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in PROVIDER_ENV:
        setattr(settings, name, None)


@pytest.fixture
def tectonic(settings):
    """A compiler path that always exists, so the check target is logic, not the install."""
    settings.TECTONIC_BIN = sys.executable
