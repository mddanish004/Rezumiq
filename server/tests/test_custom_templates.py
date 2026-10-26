"""Custom templates."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_create_from_resume(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    response = client.post(
        "/v1/custom-templates",
        {"type": "resume", "name": "My template", "resumeId": resume["id"]},
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "My template"
    assert data["mode"] == "structured"
    assert data["content"]["basics"]["name"] == "Aarav Sharma"

    assert len(client.get("/v1/custom-templates").json()["data"]) == 1
    assert client.get(f"/v1/custom-templates/{data['id']}").status_code == 200

    r = client.patch(
        f"/v1/custom-templates/{data['id']}", {"name": "Renamed"}, content_type="application/json"
    )
    assert r.json()["data"]["name"] == "Renamed"

    assert client.delete(f"/v1/custom-templates/{data['id']}").status_code == 204


def test_create_from_tex_and_limit(client: Client, db):
    user = make_user()
    client.force_login(user)
    response = client.post(
        "/v1/custom-templates",
        {
            "type": "tex",
            "name": "Latex T",
            "texSource": "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}",
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["mode"] == "code"
    assert data["texSource"].startswith("\\documentclass")

    r = client.patch(
        f"/v1/custom-templates/{data['id']}",
        {"texSource": "\\documentclass{article}\n\\begin{document}\nBye\n\\end{document}"},
        content_type="application/json",
    )
    assert r.status_code == 200


def test_custom_template_limit(client: Client, db, monkeypatch):
    from custom_templates import service as s

    monkeypatch.setattr(s, "MAX_CUSTOM_TEMPLATES", 1)
    user = make_user()
    client.force_login(user)
    client.post(
        "/v1/custom-templates",
        {
            "type": "tex",
            "name": "A",
            "texSource": "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}",
        },
        content_type="application/json",
    )
    r = client.post(
        "/v1/custom-templates",
        {
            "type": "tex",
            "name": "B",
            "texSource": "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}",
        },
        content_type="application/json",
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "CUSTOM_TEMPLATE_LIMIT"
