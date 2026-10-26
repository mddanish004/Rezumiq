"""AI keys."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_list_empty(client: Client, db):
    user = make_user()
    client.force_login(user)
    r = client.get("/v1/me/ai-keys")
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_delete_missing(client: Client, db):
    user = make_user()
    client.force_login(user)
    r = client.delete("/v1/me/ai-keys/groq")
    assert r.status_code == 404


def test_put_requires_key(client: Client, db):
    user = make_user()
    client.force_login(user)
    r = client.put("/v1/me/ai-keys/groq", {"apiKey": "short"}, content_type="application/json")
    assert r.status_code == 400
