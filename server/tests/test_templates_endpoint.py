"""GET /v1/templates and the seed command, ported from modules/templates."""

from django.core.management import call_command
from django.test import Client

from tests.test_templates_render import OLD_ORDER


def test_seed_is_idempotent_and_preserves_order(client: Client, db):
    call_command("seed_templates")
    call_command("seed_templates")

    from resumes.models import Template

    assert Template.objects.count() == len(OLD_ORDER)

    response = client.get("/v1/templates")
    assert response.status_code == 200
    body = response.json()["data"]
    assert [t["id"] for t in body] == OLD_ORDER
    assert body[0] == {
        "id": "developer",
        "name": "Developer",
        "description": body[0]["description"],
        "atsSafe": True,
        "version": 1,
    }
    assert body[0]["description"]
    assert [t["atsSafe"] for t in body if not t["atsSafe"]] == [False]


def test_seed_updates_metadata(db):
    call_command("seed_templates")

    from resumes.models import Template

    Template.objects.filter(id="jake").update(name="Old name", version=3)
    call_command("seed_templates")

    row = Template.objects.get(id="jake")
    assert row.name == "Jake's Resume"
    assert row.version == 1


def test_list_is_public_and_json_only(client: Client, db):
    call_command("seed_templates")
    response = client.get("/v1/templates")
    assert response.status_code == 200
    assert set(response.json()["data"][0]) == {"id", "name", "description", "atsSafe", "version"}


def test_other_methods_rejected(client: Client, db):
    response = client.post("/v1/templates")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
