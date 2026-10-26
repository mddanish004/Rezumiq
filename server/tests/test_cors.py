"""CORS preflight for the separate React frontend."""

from django.test import Client


def test_preflight_allows_the_vite_origin_with_credentials(client: Client, db):
    response = client.options(
        "/v1/usage",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert response["Access-Control-Allow-Credentials"] == "true"


def test_page_count_header_is_exposed_to_javascript(client: Client, db):
    response = client.get("/v1/usage", HTTP_ORIGIN="http://localhost:5173")
    assert "X-Page-Count" in response["Access-Control-Expose-Headers"]
