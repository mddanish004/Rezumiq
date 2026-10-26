"""Tests for the master profile (/v1/profile) and username availability."""

from django.test import Client

from tests.test_me import make_user


def test_usernames_availability(client: Client, db):
    make_user()

    cases = {
        "saurav": False,
        "about": False,
        "ab": False,
        "free-name": True,
    }
    for username, expected in cases.items():
        response = client.get(f"/v1/usernames/{username}")
        assert response.status_code == 200, username
        assert response.json()["data"] == {"username": username, "available": expected}


def test_profile_defaults_when_unset(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.get("/v1/profile")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body == {
        "content": {"basics": {"name": "", "links": []}, "sections": []},
        "updatedAt": None,
    }


def test_profile_put_stores_and_returns_camel_case(client: Client, db):
    user = make_user()
    client.force_login(user)

    content = {
        "basics": {"name": "  Saurav Jha ", "links": [{"label": "Site", "url": "https://x.dev"}]},
        "sections": [
            {
                "type": "experience",
                "id": "exp1",
                "title": "Work",
                "spaceAfter": -3,
                "entries": [
                    {
                        "id": "e1",
                        "organization": "Acme",
                        "role": "Dev",
                        "bullets": [{"id": "b1", "text": "shipped **stuff**"}],
                    }
                ],
            }
        ],
    }
    response = client.put("/v1/profile", {"content": content}, content_type="application/json")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["content"]["basics"]["name"] == "Saurav Jha"
    entry = body["content"]["sections"][0]["entries"][0]
    assert entry["hidden"] is False
    assert body["content"]["sections"][0]["spaceAfter"] == -3
    assert "T" in body["updatedAt"]

    stored = user.profile.data
    assert stored["sections"][0]["spaceAfter"] == -3
    assert stored["basics"]["links"][0]["url"] == "https://x.dev"


def test_profile_get_replays_stored_defaults(client: Client, db):
    user = make_user()
    client.force_login(user)
    client.put(
        "/v1/profile",
        {"content": {"basics": {"name": "A"}, "sections": []}},
        content_type="application/json",
    )
    response = client.get("/v1/profile")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["content"] == {"basics": {"name": "A", "links": []}, "sections": []}


def test_profile_put_rejects_bad_links_and_unknown_types(client: Client, db):
    user = make_user()
    client.force_login(user)

    bad = {
        "basics": {"name": "X", "links": [{"label": "click", "url": "javascript:alert(1)"}]},
        "sections": [],
    }
    response = client.put("/v1/profile", {"content": bad}, content_type="application/json")
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"

    unknown = {
        "basics": {"name": "X", "links": []},
        "sections": [{"type": "mystery", "id": "s", "title": "t"}],
    }
    response = client.put("/v1/profile", {"content": unknown}, content_type="application/json")
    assert response.status_code == 400

    response = client.put("/v1/profile", {"nope": True}, content_type="application/json")
    assert response.status_code == 400
