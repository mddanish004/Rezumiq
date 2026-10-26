"""Public pages."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def _setup(client):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    link = client.post(
        f"/v1/resumes/{resume['id']}/share-links",
        {"isListed": True},
        content_type="application/json",
    ).json()["data"]
    client.logout()
    return user, resume, link


def test_public_profile(client: Client, db):
    user, _resume, _link = _setup(client)
    response = client.get(f"/v1/public/users/{user.username}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == user.username
    assert len(data["resumes"]) == 1


def test_public_resume(client: Client, db):
    user, _resume, link = _setup(client)
    response = client.get(f"/v1/public/users/{user.username}/resumes/{link['slug']}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "R"
    assert data["content"]["basics"]["name"] == "Aarav Sharma"
    assert data["contactMasked"] is True


def test_public_resume_pdf(client: Client, db):
    user, _resume, link = _setup(client)
    response = client.get(f"/v1/public/users/{user.username}/resumes/{link['slug']}/pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
