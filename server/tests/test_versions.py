"""Immutable versions: appends, conflict rejection, restore, pagination."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def create_resume(client: Client, extra: dict | None = None) -> dict:
    body = {"title": "Res", "source": {"type": "content", "content": CONTENT}}
    response = client.post(
        "/v1/resumes", {**body, **(extra or {})}, content_type="application/json"
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_save_appends_version(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)

    body = {"kind": "manual", "content": CONTENT, "baseVersionId": resume["headVersionId"]}
    response = client.post(
        f"/v1/resumes/{resume['id']}/versions", body, content_type="application/json"
    )
    assert response.status_code == 201
    version = response.json()["data"]
    assert version["kind"] == "manual"
    assert version["parentId"] == resume["headVersionId"]
    assert version["content"]["basics"]["name"] == "Aarav Sharma"

    row = client.get(f"/v1/resumes/{resume['id']}").json()["data"]
    assert row["headVersionId"] == version["id"]


def test_named_checkpoint(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)

    body = {"kind": "manual", "content": CONTENT, "label": "Sent to Google", "semver": "1.2.0"}
    response = client.post(
        f"/v1/resumes/{resume['id']}/versions", body, content_type="application/json"
    )
    version = response.json()["data"]
    assert version["kind"] == "named"
    assert version["label"] == "Sent to Google"
    assert version["semver"] == "1.2.0"


def test_mode_payload_ghosts(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)

    response = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "manual"},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["message"] == "Structured resumes need content"


def test_version_conflict(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)
    saved = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "manual", "content": CONTENT},
        content_type="application/json",
    ).json()["data"]

    response = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "manual", "content": CONTENT, "baseVersionId": resume["headVersionId"]},
        content_type="application/json",
    )
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "VERSION_CONFLICT",
        "message": "This resume was changed somewhere else",
        "details": None,
    }

    fresh = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "manual", "content": CONTENT, "baseVersionId": saved["id"]},
        content_type="application/json",
    )
    assert fresh.status_code == 201


def test_restore_version(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)
    first_head = resume["headVersionId"]

    saved = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "manual", "content": CONTENT},
        content_type="application/json",
    ).json()["data"]

    response = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "restore", "fromVersionId": first_head},
        content_type="application/json",
    )
    assert response.status_code == 201
    restored = response.json()["data"]
    assert restored["kind"] == "restore"
    assert restored["parentId"] == saved["id"]
    assert restored["label"].startswith("Restored from ")
    assert restored["content"]["basics"]["name"] == "Aarav Sharma"


def test_restore_switches_mode_back(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)

    client.patch(f"/v1/resumes/{resume['id']}", {"mode": "code"}, content_type="application/json")
    detail = client.get(f"/v1/resumes/{resume['id']}").json()["data"]
    assert detail["mode"] == "code"
    latex_version = detail["headVersionId"]

    response = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {"kind": "restore", "fromVersionId": latex_version},
        content_type="application/json",
    )
    assert response.status_code == 201
    restored = response.json()["data"]
    assert restored["kind"] == "restore"
    assert restored["texSource"] == detail["head"]["texSource"]
    assert client.get(f"/v1/resumes/{resume['id']}").json()["data"]["mode"] == "code"


def test_versions_pagination(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)

    def save():
        return client.post(
            f"/v1/resumes/{resume['id']}/versions",
            {"kind": "manual", "content": CONTENT},
            content_type="application/json",
        ).json()["data"]

    second = save()
    third = save()

    page = client.get(f"/v1/resumes/{resume['id']}/versions?limit=2").json()["data"]
    assert [v["id"] for v in page] == [third["id"], second["id"]]
    assert page[1]["parentId"] == resume["headVersionId"]

    cursor = client.get(
        f"/v1/resumes/{resume['id']}/versions?limit=2&before={second['createdAt']}"
    ).json()["data"]
    assert [v["id"] for v in cursor] == [resume["headVersionId"]]


def test_get_single_version(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)
    head = resume["headVersionId"]

    response = client.get(f"/v1/resumes/{resume['id']}/versions/{head}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == head
    assert "content" in data and "texSource" in data
    assert data["content"]["basics"]["name"] == "Aarav Sharma"

    import uuid

    missing = client.get(f"/v1/resumes/{resume['id']}/versions/{uuid.uuid4()}")
    assert missing.status_code == 404


def test_update_version_label(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)
    head = resume["headVersionId"]

    response = client.patch(
        f"/v1/resumes/{resume['id']}/versions/{head}",
        {"label": "Checkpoint A", "semver": "0.1.0"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["kind"] == "import"
    assert data["label"] == "Checkpoint A"
    assert data["semver"] == "0.1.0"

    response = client.patch(
        f"/v1/resumes/{resume['id']}/versions/{head}",
        {"label": None},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["data"]["label"] is None

    response = client.patch(
        f"/v1/resumes/{resume['id']}/versions/{head}",
        {"semver": "not a semver"},
        content_type="application/json",
    )
    assert response.status_code == 400


def test_ai_version_stubbed_until_ai_module(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = create_resume(client)
    response = client.post(
        f"/v1/resumes/{resume['id']}/versions",
        {
            "kind": "ai",
            "suggestionId": str(__import__("uuid").uuid4()),
            "acceptedOperationIds": ["op1"],
        },
        content_type="application/json",
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_UNAVAILABLE"
