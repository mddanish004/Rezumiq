"""ATS scoring and endpoints."""

import pytest
from django.core.management import call_command
from django.test import Client

from tests.test_me import make_user


@pytest.fixture(autouse=True)
def templates(db):
    call_command("seed_templates")


CONTENT = {
    "basics": {
        "name": "Aarav Sharma",
        "headline": "Backend Engineer",
        "email": "aarav.sharma@gmail.com",
        "phone": "+91 98765 43210",
        "location": "Bengaluru, India",
        "links": [{"label": "LinkedIn", "url": "https://linkedin.com/in/aarav"}],
    },
    "sections": [
        {
            "id": "s1",
            "type": "summary",
            "title": "Summary",
            "text": "Backend engineer with 6 years of experience building APIs.",
        },
        {
            "id": "s2",
            "type": "experience",
            "title": "Experience",
            "entries": [
                {
                    "id": "e1",
                    "role": "Backend Engineer",
                    "organization": "Acme",
                    "start": "2020",
                    "end": "present",
                    "bullets": [
                        {
                            "id": "b1",
                            "text": "Built and scaled REST APIs serving 2M requests daily.",
                        },
                        {
                            "id": "b2",
                            "text": "Led migration to microservices improving latency by 40%.",
                        },
                    ],
                }
            ],
        },
        {
            "id": "s3",
            "type": "education",
            "title": "Education",
            "entries": [{"id": "e2", "institution": "IISc", "degree": "B.Tech", "field": "CS"}],
        },
        {
            "id": "s4",
            "type": "skills",
            "title": "Skills",
            "groups": [{"id": "g1", "name": "Languages", "items": ["Python", "Go"]}],
        },
    ],
}


def test_ats_score_resume_structured(client: Client, db):
    user = make_user()
    client.force_login(user)

    body = {"title": "Backend", "source": {"type": "content", "content": CONTENT}}
    resp = client.post("/v1/resumes", body, content_type="application/json")
    assert resp.status_code == 201
    resume_id = resp.json()["data"]["id"]

    resp = client.post(
        f"/v1/resumes/{resume_id}/ats-reports", {"jobId": None}, content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "score" in data and isinstance(data["score"], int)
    assert "grade" in data and data["grade"] in ("excellent", "good", "fair", "poor")
    assert "summary" in data and isinstance(data["summary"], str)
    assert "categories" in data and isinstance(data["categories"], list)
    assert "stats" in data
    assert data["stats"]["words"] > 0
    assert data["stats"]["bullets"] >= 2
    assert data["keywords"] is None
    assert data["title"] is None
    assert data["knockouts"] is None


def test_ats_public_report(client: Client, db):
    text = """Aarav Sharma
Backend Engineer
aarav.sharma@gmail.com | +91 98765 43210 | Bengaluru, India
LinkedIn: linkedin.com/in/aarav

Summary
Backend engineer with 6 years of experience building APIs.

Experience
Backend Engineer | Acme | 2020 - present
• Built and scaled REST APIs serving 2M requests daily.
• Led migration to microservices improving latency by 40%.

Education
B.Tech CS | IISc

Skills
Languages: Python, Go"""

    resp = client.post(
        "/v1/ats-reports", {"text": text, "jobDescription": None}, content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "score" in data
    assert "grade" in data
    assert data["parse"] is None


def test_ats_public_report_with_job(client: Client, db):
    text = """Aarav Sharma
Backend Engineer
aarav.sharma@gmail.com | +91 98765 43210 | Bengaluru, India

Experience
Backend Engineer | Acme | 2020 - present
• Built and scaled REST APIs serving 2M requests daily.
• Led migration to microservices improving latency by 40%.

Skills
Python, Go, Django, REST APIs"""

    job = """We are looking for a Backend Engineer with Python, Django, and REST API experience.
Required: 3+ years Python, Django, REST APIs.
Nice to have: Go, microservices."""

    resp = client.post(
        "/v1/ats-reports", {"text": text, "jobDescription": job}, content_type="application/json"
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["keywords"] is not None
    assert "matched" in data["keywords"] and "missing" in data["keywords"]
    assert data["title"] is not None
    assert data["title"]["jobTitle"] is not None


def test_ats_public_report_short_text_rejected(client: Client, db):
    resp = client.post("/v1/ats-reports", {"text": "short"}, content_type="application/json")
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_resume_ats_report_not_found(client: Client, db):
    user = make_user()
    client.force_login(user)
    import uuid

    fake_id = uuid.uuid4()
    resp = client.post(
        f"/v1/resumes/{fake_id}/ats-reports", {"jobId": None}, content_type="application/json"
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"


def test_resume_ats_report_no_head_version(client: Client, db):
    user = make_user()
    client.force_login(user)
    from resumes import service as resumes_service
    from resumes.schemas import BlankSource, CreateResumeBody

    body = CreateResumeBody(title="Empty", source=BlankSource(type="blank"))
    resume = resumes_service.create_resume(user, body)
    from resumes.models import Resume

    Resume.objects.filter(id=resume["id"]).update(head_version_id=None)
    resp = client.post(
        f"/v1/resumes/{resume['id']}/ats-reports", {"jobId": None}, content_type="application/json"
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"


KNOCKOUT_JOB = """Backend Engineer

We have 15 years of experience serving clients.

Requirements:
- 4+ years of experience
- Bachelor's degree in Computer Science
- Must have AWS certification
"""

KNOCKOUT_RESUME = """Aarav Sharma
Backend Engineer
aarav.sharma@gmail.com | +91 98765 43210 | Bengaluru, India

Experience
Backend Engineer | Acme | 2020 - present
Built and scaled REST APIs.

Education
B.Tech CS | IISc | 2021
"""


def test_knockouts_rules():
    """Advisory knockouts find hard requirements and never change the score."""
    from ats.knockouts import find_knockouts
    from ats.scoring import score_resume

    out = find_knockouts(KNOCKOUT_JOB, {"text": KNOCKOUT_RESUME})
    assert all("clients" not in k["requirement"] for k in out)
    aws = next((k for k in out if k.get("label") == "AWS certification"), None)
    assert aws and aws["required"] and aws["status"] == "not-met"
    required_flags = [k["required"] for k in out]
    assert required_flags == sorted(required_flags, reverse=True)

    scored = score_resume({"text": KNOCKOUT_RESUME, "jobText": KNOCKOUT_JOB})
    assert len(scored["knockouts"]) > 0
    assert scored["knockouts"][0]["checkedWithAi"] is False


def _flat_items(lines, x=50, y=30, size=10, big=False):
    """One item per line, like a single-run PDF; `big` marks the first line bold."""
    items = []
    for index, line in enumerate(lines):
        large = big and index == 0
        items.append(
            {
                "text": line,
                "x": x,
                "y": y,
                "width": len(line) * size * 0.5,
                "height": size * 1.4 if large else size,
                "page": 1,
                "fontName": "Helvetica-Bold" if large else "Helvetica",
                "bold": large,
            }
        )
        y += size + 6
    return items


PARSER_RESUME_LINES = [
    "Aarav Sharma",
    "Backend Engineer | Bengaluru, India",
    "aarav.sharma@gmail.com | +91 98765 43210",
    "linkedin.com/in/aarav",
    "Experience",
    "Backend Engineer, Acme",
    "Jun 2022 - Present",
    "• scaled REST APIs to 2M requests daily",
    "• led a migration to microservices",
    "Education",
    "B.Tech, IISc, 2023",
    "Skills",
    "Python, Go",
]


def test_parser_extracts_resume_structure():
    from ats.parser.parse import parse_items

    page = {"width": 595, "height": 842}
    parsed = parse_items(_flat_items(PARSER_RESUME_LINES, big=True), page)
    assert parsed["name"] == "Aarav Sharma"
    assert parsed["email"] == "aarav.sharma@gmail.com"
    assert parsed["phone"] == "+91 98765 43210"
    assert parsed["location"] == "Bengaluru, India"
    assert [(s["heading"], s["kind"]) for s in parsed["sections"]] == [
        ("Experience", "experience"),
        ("Education", "education"),
        ("Skills", "skills"),
    ]
    assert parsed["jobs"] == [
        {"title": "Backend Engineer", "company": "Acme", "dates": "Jun 2022 - Present"}
    ]
    assert parsed["readingOrderIssues"] == 0


def test_parser_flags_two_column_layout():
    from ats.parser.parse import parse_items
    from ats.parser.quality import parse_quality

    page = {"width": 595, "height": 842}
    items = list(_flat_items(PARSER_RESUME_LINES, big=True))
    for row, (label, width) in enumerate(
        [("Node 1", 90), ("Node 2", 95), ("Node 3", 85), ("Node 4", 100), ("Node 5", 92)]
    ):
        items.append(
            {
                "text": label,
                "x": 350,
                "y": 100 + row * 25,
                "width": width,
                "height": 10,
                "page": 1,
                "fontName": "Helvetica",
                "bold": False,
            }
        )
    parsed = parse_items(items, page)
    assert parsed["readingOrderIssues"] > 0
    report = parse_quality(parsed, items, page)
    columns = next(issue for issue in report["issues"] if issue["id"] == "columns")
    assert columns["status"] in ("warn", "fail")


def test_pdf_items_decode_failure_returns_none():
    from ats.parser import parse_pdf_items

    assert parse_pdf_items([{"boom": 1}], {}) is None


def test_ats_public_report_with_pdf_items(client: Client, db):
    items = _flat_items(PARSER_RESUME_LINES, big=True)
    text = "\n".join(PARSER_RESUME_LINES)
    body = {
        "text": text,
        "jobDescription": None,
        "items": items,
        "page": {"width": 595, "height": 842},
    }
    resp = client.post("/v1/ats-reports", body, content_type="application/json")
    assert resp.status_code == 200
    data = resp.json()["data"]
    categories = {category["id"]: category for category in data["categories"]}
    parsing_ids = [check["id"] for check in categories["parsing"]["checks"]]
    assert "hidden-text" in parsing_ids
    assert "columns" in parsing_ids


def _ai_report():
    return {
        "keywords": {
            "matched": ["python"],
            "missing": ["SQL"],
            "hard": {"matched": ["python"], "missing": ["SQL"]},
            "soft": {"matched": [], "missing": []},
            "mustHaveMissing": [],
            "implied": [],
        },
        "knockouts": [
            {
                "id": "experience-years",
                "label": "Years of experience",
                "requirement": "3+ years of experience",
                "required": True,
                "status": "unclear",
                "evidence": None,
                "advice": "Add dates.",
                "checkedWithAi": False,
            },
        ],
    }


def test_redact_masks_contact_details():
    from ai.redact import redact

    redacted = redact("Contact me at jane.doe@example.com or +91 98765 43210.", [])
    assert "jane.doe@example.com" not in redacted.text
    assert "[email 1]" in redacted.text
    restored = redacted.restore({"skill": "x", "evidence": "[email 1]"})
    assert restored["evidence"] == "jane.doe@example.com"


def test_with_ai_match_merges_grounded_output(monkeypatch, db):
    from ats import ai as ats_ai

    monkeypatch.setattr(
        ats_ai,
        "generate_structured",
        lambda *a, **k: {
            "data": {
                "skills": [{"skill": "SQL", "evidence": "PostgreSQL for analytics"}],
                "requirements": [{"number": 1, "status": "met", "evidence": "5 years scaling"}],
            }
        },
    )
    user = make_user()
    report = _ai_report()
    resume_text = "Built pipelines with PostgreSQL for analytics. 5 years scaling data platforms."
    merged = ats_ai.with_ai_match(
        report,
        {"userId": user.id, "resumeText": resume_text, "jobText": "Needs SQL and 3+ years"},
    )
    assert merged["keywords"]["implied"] == [
        {"skill": "SQL", "evidence": "PostgreSQL for analytics"}
    ]
    assert merged["knockouts"][0]["status"] == "met"
    assert merged["knockouts"][0]["checkedWithAi"] is True
    report2 = _ai_report()
    assert ats_ai.with_ai_match(
        report2, {"userId": user.id, "resumeText": resume_text, "jobText": "Needs SQL and 3+ years"}
    )["keywords"]["implied"]


def test_with_ai_match_drops_ungrounded_evidence(monkeypatch, db):
    from ats import ai as ats_ai

    monkeypatch.setattr(
        ats_ai,
        "generate_structured",
        lambda *a, **k: {
            "data": {
                "skills": [{"skill": "SQL", "evidence": "a database I used once"}],
                "requirements": [{"number": 1, "status": "met", "evidence": "led the team"}],
            }
        },
    )
    report = _ai_report()
    merged = ats_ai.with_ai_match(
        report,
        {
            "userId": make_user().id,
            "resumeText": "Built pipelines quickly.",
            "jobText": "Needs SQL",
        },
    )
    assert merged["keywords"]["implied"] == []
    assert merged["knockouts"][0]["status"] == "unclear"
    assert merged["knockouts"][0]["checkedWithAi"] is False


def test_with_ai_match_keeps_rule_report_on_model_failure(monkeypatch, db):
    from ats import ai as ats_ai

    def fail(*a, **k):
        raise RuntimeError("AI not configured")

    monkeypatch.setattr(ats_ai, "generate_structured", fail)
    ats_ai._cache.clear()
    report = _ai_report()
    merged = ats_ai.with_ai_match(
        report, {"userId": make_user().id, "resumeText": "text", "jobText": "job"}
    )
    assert merged == report


def test_grounded_review_constrains_rewrites():
    from ats.ai import grounded_review

    review = {
        "verdict": "Solid resume.",
        "strengths": ["Clear layout", "Good verbsToo", "Numbers used", "extra"],
        "fixes": [
            {
                "title": "Add numbers",
                "why": " recruiters scan",
                "line": "built an api",
                "rewrite": "built an api for 5m users existing 40m",
            },
        ],
        "jobFit": {
            "summary": "Fits.",
            "gaps": ["kubernetes", "terraform", "go", "rust", "c++", "extra gap"],
        },
    }
    review["fixes"][0]["why"] = "recruiters scan for results"
    out = grounded_review(review, "John Doe\nbuilt an api for Node")
    fixes = out["fixes"]
    assert fixes[0]["rewrite"] is None
    assert fixes[0]["line"] == "built an api"
    assert out["strengths"] == review["strengths"][:3]
    assert out["jobFit"]["gaps"] == review["jobFit"]["gaps"][:5]


def test_ats_report_is_stored_on_resume_and_job(client: Client, db):
    user = make_user()
    client.force_login(user)
    resume = client.post(
        "/v1/resumes",
        {"title": "Stored", "source": {"type": "content", "content": CONTENT}},
        content_type="application/json",
    ).json()["data"]
    job_text = (
        "Backend engineer needed. Must have Python and Go. "
        "Three or more years of experience. Work on billing APIs and services."
    )
    job = client.post("/v1/jobs", {"rawText": job_text}, content_type="application/json").json()[
        "data"
    ]

    response = client.post(
        f"/v1/resumes/{resume['id']}/ats-reports",
        {"jobId": job["id"]},
        content_type="application/json",
    )
    assert response.status_code == 200

    from ats.models import AtsReport

    stored = AtsReport.objects.get(user=user, resume_id=resume["id"])
    assert stored.report["score"] == response.json()["data"]["score"]
    assert stored.job_id is not None and stored.job_match is not None

    listed = client.get("/v1/resumes").json()["data"][0]
    assert listed["latestAts"]["score"] == stored.score
    assert listed["latestAts"]["jobId"] == str(job["id"])

    jobs = client.get("/v1/jobs").json()["data"]
    match = next(row for row in jobs if row["id"] == job["id"])["latestMatch"]
    assert match["percent"] == stored.job_match and match["resumeId"] == resume["id"]


def test_latex_source_with_only_an_email_still_scores():
    """A code resume with an email but no phone must not 500 on its expected fields."""
    from ats.parser import expected_from_text

    assert expected_from_text(r"\section*{Dev Rao} dev@example.com") == {"email": "dev@example.com"}
    assert expected_from_text(r"\section*{Dev Rao} +91 98765 43210") == {"phone": "+91 98765 43210"}
    assert expected_from_text(r"\section*{Dev Rao}") is None
