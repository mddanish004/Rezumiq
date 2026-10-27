"""Tests for the /v1/me lifecycle, username rules, suspension and export."""

from django.test import Client

from accounts.models import User


def make_user(email="saurav@example.com", username="saurav", name="Saurav Jha") -> User:
    user = User.objects.create_user(
        username=username, email=email, password="pw", email_verified=True, name=name
    )
    return user


def test_me_requires_sign_in(client: Client, db):
    response = client.get("/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_me_get_shape(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.get("/v1/me")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body == {
        "id": user.pk,
        "name": "Saurav Jha",
        "email": "saurav@example.com",
        "emailVerified": True,
        "image": None,
        "username": "saurav",
        "plan": "free",
        "isAnonymous": False,
        "isAdmin": False,
        "createdAt": user.date_joined.isoformat().replace("+00:00", "Z"),
    }


def test_me_is_admin_only_for_configured_verified_email(client: Client, db, settings):
    user = User.objects.create_user(username="saurav", email="saurav@example.com", password="pw")
    client.force_login(user)

    settings.ADMIN_EMAILS = [user.email]
    assert client.get("/v1/me").json()["data"]["isAdmin"] is False

    user.email_verified = True
    user.save(update_fields=["email_verified"])
    assert client.get("/v1/me").json()["data"]["isAdmin"] is True

    other = User.objects.create_user(username="other", email="other@example.com", password="pw")
    other.email_verified = True
    other.save(update_fields=["email_verified"])
    client.force_login(other)
    assert client.get("/v1/me").json()["data"]["isAdmin"] is False


def test_me_patch_name_only(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.patch("/v1/me", {"name": "New Name"}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"
    assert response.json()["data"]["username"] == "saurav"
    user.refresh_from_db()
    assert user.username_changed_at is None


def test_me_patch_rejects_empty_body(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.patch("/v1/me", {}, content_type="application/json")
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["message"] == "Provide at least one field to update"


def test_me_patch_rejects_bad_username_format(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.patch("/v1/me", {"username": "Not Valid!"}, content_type="application/json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["location"] == "body"


def test_me_patch_rename_creates_redirect(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.patch("/v1/me", {"username": "saurav-jha"}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "saurav-jha"

    user.refresh_from_db()
    assert user.username == "saurav-jha"
    assert user.username_changed_at is not None

    from accounts.models import UsernameRedirect

    redirect = UsernameRedirect.objects.get(old_username="saurav")
    assert redirect.user == user

    response = client.get("/v1/usernames/saurav")
    assert response.status_code == 200
    assert response.json()["data"]["available"] is False


def test_me_patch_cooldown(client: Client, db):
    user = make_user()
    user.username_changed_at = user.date_joined
    user.save()
    client.force_login(user)

    response = client.patch("/v1/me", {"username": "saurav-jha"}, content_type="application/json")
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "CONFLICT"
    assert error["message"].startswith("You can change your username again after ")
    assert error["message"].endswith(".")


def test_me_patch_reserved_and_taken(client: Client, db):
    user = make_user()
    other = make_user(email="other@example.com", username="other-name", name="Other")
    client.force_login(user)

    response = client.patch("/v1/me", {"username": "profile"}, content_type="application/json")
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "This username is reserved"

    response = client.patch("/v1/me", {"username": other.username}, content_type="application/json")
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "This username is taken"


def test_me_patch_takes_back_own_old_name(client: Client, db):
    user = make_user()
    client.force_login(user)

    client.patch("/v1/me", {"username": "new-name"}, content_type="application/json")

    user.refresh_from_db()
    user.username_changed_at = None
    user.save(update_fields=["username_changed_at"])

    response = client.patch("/v1/me", {"username": "saurav"}, content_type="application/json")
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "saurav"

    from accounts.models import UsernameRedirect

    assert not UsernameRedirect.objects.filter(old_username="saurav").exists()
    assert UsernameRedirect.objects.get(old_username="new-name").user == user


def test_me_delete_deletes_account_and_rows(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.delete("/v1/me")
    assert response.status_code == 204
    assert not User.objects.filter(pk=user.pk).exists()


def test_unknown_endpoint_returns_json_envelope(client: Client, db):
    response = client.get("/v1/nope")
    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Endpoint not found",
        "details": None,
    }


def test_wrong_verb_returns_405(client: Client, db):
    user = make_user()
    client.force_login(user)
    response = client.delete("/v1/profile")
    assert response.status_code == 405
    body = response.json()
    assert body["error"]["code"] == "METHOD_NOT_ALLOWED"
