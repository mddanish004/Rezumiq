from django.test import Client


def test_health_returns_ok(client: Client, db):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_deep_with_db_and_compiler(client: Client, db, tectonic):
    response = client.get("/health/deep")
    assert response.status_code == 200, response.content
    assert response.json() == {"status": "ok", "components": {"database": "ok", "compiler": "ok"}}


def test_health_deep_without_tectonic(client: Client, db, settings):
    settings.TECTONIC_BIN = "definitely-not-installed-0000"
    response = client.get("/health/deep")
    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "components": {"database": "ok", "compiler": "missing"},
    }
