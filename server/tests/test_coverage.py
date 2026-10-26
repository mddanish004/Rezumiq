"""Coverage."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user
from tests.test_resumes import CONTENT


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


def test_coverage_unparsed_job(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    raw = "We are hiring. " + ("x" * 60)
    job = client.post("/v1/jobs", {"rawText": raw}, content_type="application/json").json()["data"]
    r = client.get(f"/v1/resumes/{resume['id']}/coverage?jobId={job['id']}")
    assert r.status_code == 409


def test_coverage_report(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "R", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    raw = "We are hiring. " + ("x" * 60)
    job = client.post("/v1/jobs", {"rawText": raw}, content_type="application/json").json()["data"]
    from resumes.models import Job as J

    j = J.objects.get(id=job["id"])
    j.parsed = {"mustHave": ["Razorpay"], "niceToHave": ["Kubernetes"], "keywords": ["Python"]}
    j.save()

    r = client.get(f"/v1/resumes/{resume['id']}/coverage?jobId={job['id']}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] == 2
    assert any(
        x["requirement"] == "Razorpay" and x["status"] == "covered" for x in data["mustHave"]
    )


def test_requirement_at_the_end_of_a_sentence_is_covered():
    from coverage.service import coverage_report

    report = coverage_report(
        {"mustHave": ["Go"], "niceToHave": [], "keywords": ["Postgres"]},
        {"content": None, "tex_source": "Built billing APIs in Go. Data lived in Postgres."},
        {},
    )
    assert report["mustHave"][0]["status"] == "covered"
    assert report["keywords"][0]["status"] == "covered"
