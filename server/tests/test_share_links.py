"""Share links."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def _resume(client):
    return client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]


def test_create_and_list(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    r = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"showContact": True, "isListed": True},
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["showContact"] is True
    assert data["hasPassword"] is False
    assert data["slug"]
    assert data["url"].endswith(f"/{data['slug']}")

    listed = client.get(f"/v1/resumes/{resume['id']}/share-links").json()["data"]
    assert len(listed) == 1

    detail = client.get(f"/v1/share-links/{data['id']}").json()["data"]
    assert detail["id"] == data["id"]

    stats = client.get(f"/v1/share-links/{data['id']}/stats").json()["data"]
    assert stats["viewCount"] == 0


def test_password_and_slug_conflict(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    r1 = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"slug": "my-slug"},
        content_type="application/json",
    ).json()["data"]
    r2 = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"slug": "my-slug"},
        content_type="application/json",
    )
    assert r2.status_code == 409

    r = client.patch(
        f"/v1/share-links/{r1['id']}", {"password": "secret123"}, content_type="application/json"
    )
    assert r.json()["data"]["hasPassword"] is True

    r = client.patch(
        f"/v1/share-links/{r1['id']}", {"password": None}, content_type="application/json"
    )
    assert r.json()["data"]["hasPassword"] is False


def test_contact_lock_validation(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    r = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"showContact": True, "contactPassword": "secret123"},
        content_type="application/json",
    )
    assert r.status_code == 400

    r = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"contactPassword": "secret123"},
        content_type="application/json",
    )
    assert r.status_code == 201
    assert r.json()["data"]["hasContactPassword"] is True


def test_delete(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    data = client.post(
        f"/v1/resumes/{resume['id']}/share-links", {}, content_type="application/json"
    ).json()["data"]
    assert client.delete(f"/v1/share-links/{data['id']}").status_code == 204
    assert client.get(f"/v1/share-links/{data['id']}").status_code == 404
