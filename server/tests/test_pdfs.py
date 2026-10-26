"""PDF/tex/json-resume/preview endpoints."""

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


def test_resume_pdf(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    response = client.get(f"/v1/resumes/{resume['id']}/pdf")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert "X-Page-Count" in response


def test_resume_tex(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    response = client.get(f"/v1/resumes/{resume['id']}/tex")
    assert response.status_code == 200
    assert "\\documentclass" in response.content.decode()


def test_resume_json_resume(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = _resume(client)
    response = client.get(f"/v1/resumes/{resume['id']}/json-resume")
    assert response.status_code == 200
    data = response.json()
    assert data["basics"]["name"] == "Aarav Sharma"


def test_preview_structured(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = {"templateId": "developer", "content": CONTENT}
    response = client.post("/v1/previews", body, content_type="application/json")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_preview_tex(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = {"texSource": "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}"}
    response = client.post("/v1/previews", body, content_type="application/json")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
