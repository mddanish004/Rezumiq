"""The data export and the pydantic port of the resume content schema."""

from django.test import Client

from resumes.content import (
    BULLET_MAX,
    ResumeContent,
    link_parts,
    plain_text,
)
from tests.test_me import make_user


def test_export_shape(client: Client, db):
    user = make_user()
    client.force_login(user)

    content = {"basics": {"name": "Saurav", "links": []}, "sections": []}
    response = client.put("/v1/profile", {"content": content}, content_type="application/json")
    assert response.status_code == 200

    response = client.get("/v1/me/data")
    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="my-data.json"'
    data = response.json()["data"]
    assert data["exportedAt"]
    assert data["account"]["username"] == "saurav"
    assert data["account"]["emailVerified"] is True
    assert data["profile"]["basics"]["name"] == "Saurav"
    assert "resumes" not in data


def test_export_without_profile(client: Client, db):
    user = make_user()
    client.force_login(user)

    response = client.get("/v1/me/data")
    data = response.json()["data"]
    assert data["profile"] is None


def test_content_defaults_and_limits():
    parsed = ResumeContent.model_validate({"basics": {"name": "S"}, "sections": []})
    assert parsed.basics.name == "S"
    assert parsed.basics.links == []
    assert parsed.basics.sensitive is None
    assert parsed.model_dump(by_alias=True, exclude_none=True) == {
        "basics": {"name": "S", "links": []},
        "sections": [],
    }
    assert BULLET_MAX == 1000


def test_content_dates():
    import pydantic

    def entry(dates: dict) -> dict:
        base = {"id": "x", "organization": "A", "role": "R"}
        return {
            "basics": {"name": "S"},
            "sections": [
                {
                    "type": "experience",
                    "id": "e",
                    "title": "T",
                    "entries": [{**base, **dates}],
                }
            ],
        }

    for dates, ok in [
        ({"start": "2025-06", "end": "present"}, True),
        ({"start": "2025", "end": "2025-12"}, True),
        ({"start": "2025-13"}, False),
        ({"end": "later"}, False),
    ]:
        if ok:
            ResumeContent.model_validate(entry(dates))
        else:
            try:
                ResumeContent.model_validate(entry(dates))
                raise AssertionError(f"expected {dates} to fail")
            except pydantic.ValidationError:
                pass


def test_content_discriminated_sections():
    experience = {
        "type": "experience",
        "id": "s1",
        "title": "Work",
        "entries": [
            {
                "id": "e1",
                "organization": "Acme",
                "role": "Dev",
                "start": "2024-01",
                "end": "present",
                "bullets": [{"id": "b", "text": "t"}],
            }
        ],
    }
    parsed = ResumeContent.model_validate({"basics": {"name": "S"}, "sections": [experience]})
    assert parsed.sections[0].entries[0].end == "present"
    model_dump = parsed.model_dump(by_alias=True)["sections"][0]
    assert "spaceAfter" in model_dump or model_dump["spaceAfter"] is None
    assert model_dump["entries"][0]["hidden"] is False

    unknown = {"basics": {"name": "S"}, "sections": [{"type": "nope", "id": "x", "title": "T"}]}
    import pydantic

    try:
        ResumeContent.model_validate(unknown)
        raise AssertionError("unknown section type must fail")
    except pydantic.ValidationError:
        pass


def test_rich_text_helpers():
    assert plain_text("see [docs](https://x.dev) and **bold**") == "see docs and bold"
    parts = link_parts("see [docs](https://x.dev) now")
    assert parts == [{"text": "see "}, {"text": "docs", "url": "https://x.dev"}, {"text": " now"}]
    assert plain_text("[words](mailto:a@b.dev)") == "words"
    parts = link_parts("[no](ftp://x)")
    assert parts == [{"text": "[no](ftp://x)"}]
