"""Analytics."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_analytics_empty(client: Client, db):
    user = make_user()
    client.force_login(user)
    r = client.get("/v1/analytics?days=7&timeZone=UTC")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["days"] == 7
    assert data["totals"]["views"] == 0
    assert len(data["viewsByDay"]) == 7
