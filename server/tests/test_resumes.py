"""Resume CRUD, sources and mode switch, ported from resumes.service.ts."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


CONTENT = {
    "basics": {"name": "Aarav Sharma", "headline": "Backend Engineer", "links": []},
    "sections": [
        {
            "id": "exp",
            "type": "experience",
            "title": "Experience",
            "entries": [
                {
                    "id": "e1",
                    "organization": "Razorpay",
                    "role": "SDE Intern",
                    "start": "2025-05",
                    "end": "2025-07",
                    "bullets": [{"id": "b1", "text": "Cut **latency** by 40%"}],
                }
            ],
        }
    ],
}


def test_list_requires_sign_in(client: Client, db):
    assert client.get("/v1/resumes").status_code == 401


def test_create_blank_default(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.post("/v1/resumes", {"title": "Blank"}, content_type="application/json")
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["title"] == "Blank"
    assert body["mode"] == "structured"
    assert body["templateId"] == "developer"
    assert body["pageLimit"] == 1
    assert body["layout"] == {"spacing": "normal"}
    assert body["headVersionId"] == body["head"]["id"]
    assert body["head"]["kind"] == "manual"
    assert body["head"]["content"] == {
        "basics": {"name": "", "links": []},
        "sections": [],
    }
    assert body["head"]["texSource"] is None


def test_create_with_content_normalizes_bullets(client: Client, db):
    user = make_user()
    client.force_login(user)

    body = {"title": "Backend", "source": {"type": "content", "content": CONTENT}}
    response = client.post("/v1/resumes", body, content_type="application/json")
    assert response.status_code == 201
    head = response.json()["data"]["head"]
    assert head["content"]["basics"]["name"] == "Aarav Sharma"
    assert response.json()["data"]["headVersionId"] == head["id"]


def test_create_code_mode_renders_template_tex(client: Client, db):
    user = make_user()
    client.force_login(user)

    body = {
        "title": "Latex",
        "mode": "code",
        "templateId": "jake",
        "source": {"type": "content", "content": CONTENT},
    }
    response = client.post("/v1/resumes", body, content_type="application/json")
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["mode"] == "code"
    assert data["templateId"] is None
    assert "\\documentclass" in data["head"]["texSource"]
    assert "Razorpay" in data["head"]["texSource"]
    assert data["head"]["content"] is None


def test_create_pasted_tex_rejects_structured_mode(client: Client, db):
    user = make_user()
    client.force_login(user)

    body = {
        "title": "Old Tailwind",
        "mode": "structured",
        "source": {"type": "tex", "texSource": "\\documentclass{article}"},
    }
    response = client.post("/v1/resumes", body, content_type="application/json")
    assert response.status_code == 400
    issue = response.json()["error"]["details"][0]
    assert issue["message"] == "Pasted LaTeX creates a code-mode resume; convert it with an import"


def test_create_copy_of_resume(client: Client, db):
    user = make_user()
    client.force_login(user)

    original = client.post(
        "/v1/resumes", {"title": "Original"}, content_type="application/json"
    ).json()["data"]
    body = {"title": "Copy", "source": {"type": "resume", "resumeId": original["id"]}}
    response = client.post("/v1/resumes", body, content_type="application/json")
    assert response.status_code == 201
    copy = response.json()["data"]
    assert copy["sourceResumeId"] == original["id"]
    assert copy["head"]["content"] == original["head"]["content"]


def test_create_unknown_template_and_job(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.post(
        "/v1/resumes", {"title": "T", "templateId": "nope"}, content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    from resumes.models import Job

    other_user = make_user(email="other@example.com", username="other")
    job = Job.objects.create(user=other_user, raw_text="x", text_hash="y" * 64)
    response = client.post(
        "/v1/resumes", {"title": "T", "jobId": str(job.id)}, content_type="application/json"
    )
    assert response.status_code == 404


def test_resume_quota_message(client: Client, db, monkeypatch):
    from usage import quotas

    monkeypatch.setitem(quotas.PLAN_LIMITS["free"], "resumes", 1)
    user = make_user()
    client.force_login(user)

    first = client.post("/v1/resumes", {"title": "First"}, content_type="application/json")
    assert first.status_code == 201
    second = client.post("/v1/resumes", {"title": "Second"}, content_type="application/json")
    assert second.status_code == 402
    error = second.json()["error"]
    assert error["code"] == "QUOTA_EXCEEDED"
    assert (
        error["message"] == "You've reached the limit of 1 resumes. Delete some you no longer need."
    )
    assert error["details"] == {"limit": 1, "used": 1}


def test_deleted_resumes_free_quota(client: Client, db, monkeypatch):
    from usage import quotas

    monkeypatch.setitem(quotas.PLAN_LIMITS["free"], "resumes", 1)
    user = make_user()
    client.force_login(user)
    created = client.post("/v1/resumes", {"title": "Res"}, content_type="application/json").json()[
        "data"
    ]
    assert client.delete(f"/v1/resumes/{created['id']}").status_code == 204

    response = client.post("/v1/resumes", {"title": "Res"}, content_type="application/json")
    assert response.status_code == 201


def test_list_resumes_and_archive_filter(client: Client, db):
    user = make_user()
    client.force_login(user)
    a = client.post("/v1/resumes", {"title": "A"}, content_type="application/json").json()["data"]
    client.post("/v1/resumes", {"title": "B"}, content_type="application/json").json()["data"]

    response = client.get("/v1/resumes")
    assert [r["title"] for r in response.json()["data"]] == ["B", "A"]

    client.patch(f"/v1/resumes/{a['id']}", {"archived": True}, content_type="application/json")
    active = client.get("/v1/resumes").json()["data"]
    assert [r["title"] for r in active] == ["B"]
    archived = client.get("/v1/resumes?archived=true").json()["data"]
    assert [r["title"] for r in archived] == ["A"]
    assert archived[0]["archivedAt"] is not None

    client.patch(f"/v1/resumes/{a['id']}", {"archived": False}, content_type="application/json")
    assert len(client.get("/v1/resumes").json()["data"]) == 2


def test_ownership_scoping(client: Client, db):
    user_two = make_user()
    client.force_login(user_two)
    created = client.post(
        "/v1/resumes", {"title": "Scoped"}, content_type="application/json"
    ).json()["data"]

    other = make_user(email="other@example.com", username="other")
    client_two = Client()
    client_two.force_login(other)
    assert client_two.get(f"/v1/resumes/{created['id']}").status_code == 404
    assert (
        client_two.post(
            f"/v1/resumes/{created['id']}/versions",
            {"kind": "manual", "content": CONTENT},
            content_type="application/json",
        ).status_code
        == 404
    )


def test_get_resume_with_head(client: Client, db):
    user = make_user()
    client.force_login(user)
    created = client.post("/v1/resumes", {"title": "Head"}, content_type="application/json").json()[
        "data"
    ]

    response = client.get(f"/v1/resumes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["head"]["content"]["basics"]["name"] == ""
    assert response.json()["data"]["head"]["parentId"] is None


def test_update_resume_summary_fields(client: Client, db):
    user = make_user()
    client.force_login(user)
    created = client.post(
        "/v1/resumes", {"title": "Editable"}, content_type="application/json"
    ).json()["data"]
    from resumes.models import Job

    job = Job.objects.create(user=user, raw_text="x", text_hash="z" * 64)

    body = {"title": "New title", "templateId": "jake", "jobId": str(job.id), "pageLimit": 2}
    response = client.patch(f"/v1/resumes/{created['id']}", body, content_type="application/json")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "New title"
    assert data["templateId"] == "jake"
    assert data["jobId"] == str(job.id)
    assert data["pageLimit"] == 2

    response = client.patch(
        f"/v1/resumes/{created['id']}", {"jobId": None}, content_type="application/json"
    )
    assert response.json()["data"]["jobId"] is None

    response = client.patch(f"/v1/resumes/{created['id']}", {}, content_type="application/json")
    assert response.status_code == 400
    assert (
        response.json()["error"]["details"][0]["message"] == "Provide at least one field to update"
    )


def test_update_code_mode_guards(client: Client, db):
    user = make_user()
    client.force_login(user)
    created = client.post(
        "/v1/resumes",
        {"title": "X", "mode": "code", "templateId": "jake"},
        content_type="application/json",
    ).json()["data"]

    response = client.patch(
        f"/v1/resumes/{created['id']}", {"templateId": "jake"}, content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "TEMPLATE_NOT_ALLOWED"

    response = client.patch(
        f"/v1/resumes/{created['id']}",
        {"layout": {"spacing": "relaxed"}},
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LAYOUT_NOT_ALLOWED"


def test_switch_to_code_mode(client: Client, db):
    user = make_user()
    client.force_login(user)
    created = client.post(
        "/v1/resumes",
        {"title": "Switching", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]

    response = client.patch(
        f"/v1/resumes/{created['id']}", {"mode": "code"}, content_type="application/json"
    )
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["mode"] == "code"
    assert summary["templateId"] == "developer"

    detail = client.get(f"/v1/resumes/{created['id']}").json()["data"]
    assert detail["head"]["kind"] == "manual"
    assert detail["head"]["label"] == "Switched to LaTeX"
    assert "\\documentclass" in detail["head"]["texSource"]
    assert "Razorpay" in detail["head"]["texSource"]


def test_delete_resume_soft(client: Client, db):
    user = make_user()
    client.force_login(user)
    created = client.post(
        "/v1/resumes", {"title": "Doomed"}, content_type="application/json"
    ).json()["data"]

    response = client.delete(f"/v1/resumes/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/v1/resumes/{created['id']}").status_code == 404
    assert client.get("/v1/resumes").json()["data"] == []
