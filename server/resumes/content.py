"""Rich text helpers and the resume content schema.

Ports schemas/rich-text.ts and schemas/resume-content.ts (zod becomes pydantic).
The content blob is the shared currency of profiles, resume versions, AI steps
and templates, so this module is the single place that defines it.
"""

import re
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import AfterValidator, EmailStr, Field, StringConstraints

from api.common.models import ApiModel

INLINE_LINK = re.compile(r"\[([^\]\n]+)\]\(((?:https?://|mailto:)[^\s)]+)\)")


def plain_text(text: str) -> str:
    return INLINE_LINK.sub(r"\1", text.replace("**", ""))


def link_parts(text: str) -> list[dict]:
    """Splits text into plain runs and links, in order.

    [{"text": "see "}, {"text": "docs", "url": "https://x"}]
    """
    parts: list[dict] = []
    last = 0
    for match in INLINE_LINK.finditer(text):
        if match.start() > last:
            parts.append({"text": text[last : match.start()]})
        parts.append({"text": match.group(1), "url": match.group(2)})
        last = match.end()
    if last < len(text):
        parts.append({"text": text[last:]})
    return parts


ShapeId = Annotated[str, StringConstraints(min_length=1, max_length=64)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


def _check_web_url(value: str) -> str:
    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "mailto"} or (scheme != "mailto" and not parsed.netloc):
        raise ValueError("Link must be a full http(s) or mailto address")
    return value


EndDate = Annotated[str, StringConstraints(pattern=r"^(present|\d{4}(-(0[1-9]|1[0-2]))?)$")]

WebUrl = Annotated[str, AfterValidator(_check_web_url)]

BULLET_MAX = 1000

YearMonth = Annotated[str, StringConstraints(pattern=r"^\d{4}(-(0[1-9]|1[0-2]))?$")]


class Bullet(ApiModel):
    id: ShapeId
    text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=BULLET_MAX)]
    hidden: bool = False


class Link(ApiModel):
    label: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)]
    url: WebUrl
    sensitive: bool | None = None


class EntryMixin(ApiModel):
    id: ShapeId
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    bullets: list[Bullet] = Field(default_factory=list, max_length=20)


class ExperienceEntry(EntryMixin):
    organization: ShortText
    sensitive: bool | None = None
    role: ShortText
    location: ShortText | None = None
    start: YearMonth | None = None
    end: EndDate | None = None


class EducationEntry(EntryMixin):
    institution: ShortText
    degree: ShortText | None = None
    field: ShortText | None = None
    location: ShortText | None = None
    start: YearMonth | None = None
    end: EndDate | None = None
    score: Annotated[str, StringConstraints(strip_whitespace=True, max_length=20)] | None = None


class ProjectEntry(EntryMixin):
    name: ShortText
    url: WebUrl | None = None
    links: list[Link] = Field(default_factory=list, max_length=5)
    technologies: list[Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)]] = (
        Field(default_factory=list, max_length=20)
    )
    start: YearMonth | None = None
    end: EndDate | None = None


ListText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=400)]


class GenericEntry(EntryMixin):
    title: ListText
    subtitle: ListText | None = None
    date: Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)] | None = None
    url: WebUrl | None = None


class SkillGroup(ApiModel):
    id: ShapeId
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]
    items: list[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]] = Field(
        max_length=40
    )


class ExperienceSection(ApiModel):
    type: Literal["experience"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    entries: list[ExperienceEntry] = Field(max_length=30)


class EducationSection(ApiModel):
    type: Literal["education"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    entries: list[EducationEntry] = Field(max_length=10)


class ProjectsSection(ApiModel):
    type: Literal["projects"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    entries: list[ProjectEntry] = Field(max_length=30)


class SkillsSection(ApiModel):
    type: Literal["skills"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    groups: list[SkillGroup] = Field(max_length=15)


class ListSection(ApiModel):
    type: Literal["list"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    entries: list[GenericEntry] = Field(max_length=40)


class SummarySection(ApiModel):
    type: Literal["summary"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class LinksSection(ApiModel):
    type: Literal["links"]
    id: ShapeId
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    hidden: bool = False
    space_after: int | None = Field(default=None, ge=-8, le=24)
    links: list[Link] = Field(max_length=15)


Section = Annotated[
    ExperienceSection
    | EducationSection
    | ProjectsSection
    | SkillsSection
    | ListSection
    | SummarySection
    | LinksSection,
    Field(discriminator="type"),
]


class Basics(ApiModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
    headline: ShortText | None = None
    email: EmailStr | None = None
    phone: Annotated[str, StringConstraints(strip_whitespace=True, max_length=30)] | None = None
    location: ShortText | None = None
    links: list[Link] = Field(default_factory=list, max_length=10)
    sensitive: list[Literal["name", "location"]] | None = None


ResumeSection = Section


class ResumeContent(ApiModel):
    basics: Basics
    sections: list[Section] = Field(max_length=20)


EMPTY_RESUME_CONTENT = {"basics": {"name": "", "links": []}, "sections": []}
