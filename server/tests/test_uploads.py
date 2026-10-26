"""Uploads: file detection, storage, ownership."""

import io

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_upload_text(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = b"Hello world, this is plain text."
    buf = io.BytesIO(body)
    buf.name = "notes.txt"
    response = client.post(
        "/v1/uploads",
        {"file": buf},
        format="multipart",
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["kind"] == "text"
    assert data["mimeType"] == "text/plain"
    assert data["sizeBytes"] == len(body)
    assert data["fileName"] == "notes.txt"

    fetched = client.get(f"/v1/uploads/{data['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == data["id"]

    assert client.delete(f"/v1/uploads/{data['id']}").status_code == 204
    assert client.get(f"/v1/uploads/{data['id']}").status_code == 404


def test_upload_tex_detection(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = b"\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}"
    response = client.post(
        "/v1/uploads",
        {"file": (io.BytesIO(body), "resume.tex")},
        format="multipart",
    )
    assert response.status_code == 201
    assert response.json()["data"]["kind"] == "tex"


def test_upload_pdf_magic(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = b"%PDF-1.4\n%fake"
    response = client.post(
        "/v1/uploads",
        {"file": (io.BytesIO(body), "resume.pdf")},
        format="multipart",
    )
    assert response.status_code == 201
    assert response.json()["data"]["kind"] == "pdf"


def test_upload_requires_file(client: Client, db):
    user = make_user()
    client.force_login(user)
    response = client.post("/v1/uploads", {}, format="multipart")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_REQUIRED"


def test_upload_ownership(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = b"secret"
    created = client.post(
        "/v1/uploads",
        {"file": (io.BytesIO(body), "x.txt")},
        format="multipart",
    ).json()["data"]

    other = make_user(email="other@example.com", username="other")
    other_client = Client()
    other_client.force_login(other)
    assert other_client.get(f"/v1/uploads/{created['id']}").status_code == 404
    assert other_client.delete(f"/v1/uploads/{created['id']}").status_code == 404


def test_upload_unsupported_binary(client: Client, db):
    user = make_user()
    client.force_login(user)
    body = b"\x00\x01\x02binary"
    response = client.post(
        "/v1/uploads",
        {"file": (io.BytesIO(body), "blob.bin")},
        format="multipart",
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE"
