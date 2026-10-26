"""Advisory knockout hints, ported from modules/ats/knockouts.ts.

These describe a job's hard requirements against the resume. They are advisory
only and never change the ATS score.
"""

from __future__ import annotations

import re

from .scoring import plural, resume_experience, resume_section

MAX_KNOCKOUTS = 8
DASH = r"[-\u2013\u2014]"
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "twelve": 12,
    "fifteen": 15,
}
NUM = rf"(\d{{1,2}}|{'|'.join(NUMBER_WORDS)})"

PREFERRED = re.compile(
    r"\b(prefer\w*|nice to have|good to have|plus|bonus|desirable|advantage\w*|ideally)\b",
    re.IGNORECASE,
)
REQ_HEADING = re.compile(
    r"requirement|qualification|what you('ll| will)? (need|bring)|who you are|you (have|bring)"
    r"|must have|eligibility|looking for|skills|about you|criteria",
    re.IGNORECASE,
)
BLURB_HEADING = re.compile(
    r"about (us|the company|the team|company)|who we are|our (story|mission|culture|values)"
    r"|benefits|perks|what we offer|why (join|work)|compensation|life at",
    re.IGNORECASE,
)
COMPANY_SUBJECT = re.compile(
    r"\b(we|our (company|team|firm|founders))\b[^.]*\b(have|has|bring|been|with)\b"
    r"(?![^.]*\b(you|candidate|looking|seeking|hiring)\b)",
    re.IGNORECASE,
)

INTERN = re.compile(r"\bintern(ship)?s?\b", re.IGNORECASE)


def _city(name: str, pattern: str, country: str) -> dict:
    return {"name": name, "re": re.compile(pattern, re.IGNORECASE), "country": country}


CITIES = [
    _city("Bengaluru", r"\b(bengaluru|bangalore)\b", "India"),
    _city("Mumbai", r"\b(mumbai|bombay)\b", "India"),
    _city("Delhi NCR", r"\b(new delhi|delhi|ncr|gurgaon|gurugram|noida)\b", "India"),
    _city("Hyderabad", r"\b(hyderabad|secunderabad)\b", "India"),
    _city("Chennai", r"\b(chennai|madras)\b", "India"),
    _city("Pune", r"\bpune\b", "India"),
    _city("Kolkata", r"\b(kolkata|calcutta)\b", "India"),
    _city("Ahmedabad", r"\bahmedabad\b", "India"),
    _city("Jaipur", r"\bjaipur\b", "India"),
    _city("Kochi", r"\b(kochi|cochin)\b", "India"),
    _city("Chandigarh", r"\bchandigarh\b", "India"),
    _city("London", r"\blondon\b", "United Kingdom"),
    _city("New York", r"\bnew york\b", "United States"),
    _city("San Francisco", r"\b(san francisco|bay area)\b", "United States"),
    _city("Seattle", r"\bseattle\b", "United States"),
    _city("Singapore", r"\bsingapore\b", "Singapore"),
    _city("Dubai", r"\bdubai\b", "United Arab Emirates"),
]

COUNTRIES = [
    {"name": "India", "re": re.compile(r"\bindia\b", re.IGNORECASE), "flags": re.IGNORECASE},
    {"name": "United States", "re": re.compile(r"\b(US|USA)\b|U\.S\.|United States"), "flags": 0},
    {"name": "United Kingdom", "re": re.compile(r"\bUK\b|U\.K\.|United Kingdom"), "flags": 0},
    {"name": "Canada", "re": re.compile(r"\bcanada\b", re.IGNORECASE), "flags": re.IGNORECASE},
    {
        "name": "Singapore",
        "re": re.compile(r"\bsingapore\b", re.IGNORECASE),
        "flags": re.IGNORECASE,
    },
]

DEGREES = [
    {
        "level": "bachelor's",
        "rank": 1,
        "re": re.compile(
            r"\b(b\.? ?tech|bachelor'?s?|b\.? ?sc|bca|b\.? ?com|b\.?s\.? in|b\.?a\.? in|undergraduate degree)\b|\bB\.?E\b",
            re.IGNORECASE,
        ),
    },
    {
        "level": "master's",
        "rank": 2,
        "re": re.compile(
            r"\b(m\.? ?tech|master'?s? (degree|of|in)|masters\b|m\.? ?sc|mca|m\.?s\.? in)\b",
            re.IGNORECASE,
        ),
    },
    {"level": "MBA", "rank": 2, "re": re.compile(r"\b(mba|pgdm|pgp)\b", re.IGNORECASE)},
    {"level": "PhD", "rank": 3, "re": re.compile(r"\b(ph\.? ?d|doctorate)\b", re.IGNORECASE)},
    {
        "level": "degree",
        "rank": 0,
        "re": re.compile(
            r"\bdegree (in|from)\b|\b(engineering|university|college) degree\b|\bgraduate in\b",
            re.IGNORECASE,
        ),
    },
]


def is_degree(d: dict, text: str) -> bool:
    if d["level"] == "bachelor's":
        text = re.sub(r"\bbe\b", "", text)
    return bool(d["re"].search(text))


CS_FIELD = re.compile(r"computer|\bCSE?\b|\bIT\b|information tech|software", re.IGNORECASE)

CERTS = [
    {
        "label": "AWS certification",
        "job": re.compile(r"\bAWS[- ]certifi|\bAWS Certified", re.IGNORECASE),
        "resume": re.compile(r"\bAWS (certified|certification)", re.IGNORECASE),
    },
    {
        "label": "Azure certification",
        "job": re.compile(r"\bAzure[\w ]{0,30}certifi|\bAZ-\d{3}\b", re.IGNORECASE),
        "resume": re.compile(r"Azure[\w ]*certifi|AZ-\d{3}", re.IGNORECASE),
    },
    {
        "label": "Google Cloud certification",
        "job": re.compile(r"\b(GCP|Google Cloud)[\w ]{0,30}certifi", re.IGNORECASE),
        "resume": re.compile(r"(GCP|Google Cloud)[\w ]*certifi", re.IGNORECASE),
    },
    {
        "label": "Chartered Accountant (CA)",
        "job": re.compile(r"chartered accountant|(?<!, )\bCA\b"),
        "resume": re.compile(r"chartered accountant|\bCA\b"),
    },
    *[
        {"label": a, "job": re.compile(rf"\b{a}\b"), "resume": re.compile(rf"\b{a}\b")}
        for a in ["CFA", "CPA", "PMP", "FRM", "ACCA", "CISSP", "CKA", "CCNA", "CISA"]
    ],
]
LANGUAGES = [
    "English",
    "Hindi",
    "Tamil",
    "Telugu",
    "Kannada",
    "Marathi",
    "Bengali",
    "Gujarati",
    "Malayalam",
    "Japanese",
    "German",
    "French",
    "Spanish",
    "Mandarin",
    "Arabic",
    "Portuguese",
    "Korean",
]


def clip(s: str, n: int = 140) -> str:
    return f"{s[: n - 3].rstrip()}..." if len(s) > n else s


def to_number(s: str):
    if s.lower() in NUMBER_WORDS:
        return NUMBER_WORDS[s.lower()]
    return int(s) if s.isdigit() else 0


def line_with(text: str, pattern: re.Pattern) -> str | None:
    for line in text.split("\n"):
        if pattern.search(line):
            return clip(line.strip(), 100)
    return None


def resume_location(r: dict) -> str:
    content = r.get("content")
    if content is not None and content.basics and content.basics.location:
        return content.basics.location
    return "\n".join(r["text"].split("\n")[:6])


def education_text(r: dict) -> str:
    content = r.get("content")
    if content is None:
        return "\n".join(resume_section(r["text"], "education")) or r["text"]
    lines = []
    for section in content.sections:
        if section.type == "education" and not section.hidden:
            for e in section.entries:
                if not e.hidden:
                    lines.append(", ".join(x for x in (e.degree, e.field, e.institution) if x))
    return "\n".join(lines)


def check_experience(s: str, r: dict, job: str | None = None) -> list[dict]:
    range_match = re.search(
        rf"{NUM}\s*(?:{DASH}|to)\s*{NUM}\+?\s*(?:years?|yrs?)\b", s, re.IGNORECASE
    )
    single = re.search(rf"{NUM}\s*\+?\s*(?:years?|yrs?)\b", s, re.IGNORECASE)
    fresher = re.search(r"\bfreshers?\b", s, re.IGNORECASE)
    if not range_match and not single and not fresher:
        return []
    min_years = (
        to_number(range_match.group(1))
        if range_match
        else to_number(single.group(1))
        if single
        else 0
    )
    max_years = (
        to_number(range_match.group(2)) if range_match else (1 if fresher and not single else None)
    )
    asked = f"{min_years}+ years" if max_years is None else f"{min_years} to {max_years} years"
    exp = resume_experience(r)
    dates_advice = "Add start and end dates (month and year) to every role so an ATS can work out your years of experience."
    if not exp or exp["roles"] == 0:
        if max_years is not None and max_years <= 1:
            return [
                {
                    "status": "met",
                    "evidence": "No full-time roles on your resume, which fits a fresher role",
                    "advice": "Lead with projects and internships, with dates, since they stand in for work experience.",
                }
            ]
        return [
            {
                "status": "not-met" if exp else "unclear",
                "evidence": "No full-time roles on your resume" if exp else None,
                "advice": f"The job asks for {asked}; list any full-time, freelance or part-time work with dates."
                if exp
                else dates_advice,
            }
        ]
    evidence = f"About {exp['years']} years from your experience dates, not counting internships"
    if exp["years"] < min_years and exp["undated"] > 0:
        return [
            {
                "status": "unclear",
                "evidence": f"{evidence}; {plural(exp['undated'], 'role')} without dates",
                "advice": dates_advice,
            }
        ]
    if exp["years"] < min_years:
        return [
            {
                "status": "not-met",
                "evidence": evidence,
                "advice": f"The job asks for {asked}; if internships or freelance work close the gap, list them with dates.",
            }
        ]
    if max_years is not None and exp["years"] > max_years + 1:
        return [
            {
                "status": "unclear",
                "evidence": evidence,
                "advice": f"The job asks for {asked} and you have more; say in your summary why this role fits you now.",
            }
        ]
    return [
        {
            "status": "met",
            "evidence": evidence,
            "advice": "Add your total years of experience to your summary so a recruiter sees it at once.",
        }
    ]


def check_degree(s: str, r: dict, job: str | None = None) -> list[dict]:
    want = [d for d in DEGREES if is_degree(d, s)]
    edu = education_text(r)
    have = [d for d in DEGREES if d["rank"] > 0 and is_degree(d, edu)]
    specific = [d for d in want if d["rank"] > 0]
    first_line = next((line for line in edu.split("\n") if line.strip()), "") if edu else ""
    evidence = clip(first_line, 100) if edu else None
    asked = " or ".join(d["level"] for d in specific) or "a degree"
    if not edu.strip():
        return [
            {
                "status": "not-met",
                "evidence": None,
                "advice": f"The job asks for {asked}; add your education with the degree name.",
            }
        ]
    if not have:
        return [
            {
                "status": "unclear",
                "evidence": evidence,
                "advice": 'Write your degree and field in full, for example "B.Tech in Computer Science", '
                "so an ATS can match it.",
            }
        ]
    level_ok = not specific or any(
        (h["level"] == "MBA" and w["level"] == "MBA")
        or (w["level"] != "MBA" and h["rank"] >= w["rank"])
        for w in specific
        for h in have
    )
    if not level_ok:
        return [
            {
                "status": "not-met",
                "evidence": evidence,
                "advice": f"The job asks for {asked}; if you have an equivalent, name it the way the job does.",
            }
        ]
    if CS_FIELD.search(s) and not CS_FIELD.search(edu):
        if re.search(r"related|equivalent|similar|allied", s, re.IGNORECASE):
            return [
                {
                    "status": "unclear",
                    "evidence": evidence,
                    "advice": "The job wants Computer Science or a related field; name your field in full "
                    "so a recruiter can judge the fit.",
                }
            ]
        return [
            {
                "status": "not-met",
                "evidence": evidence,
                "advice": "The job asks for a Computer Science degree; show related coursework or certifications "
                "if your field differs.",
            }
        ]
    return [
        {
            "status": "met",
            "evidence": evidence,
            "advice": 'Keep the degree written the way the job writes it, for example "B.Tech in Computer Science", '
            "so keyword filters match.",
        }
    ]


def check_graduation_year(s: str, r: dict, job: str | None = None) -> list[dict]:
    want = re.findall(r"\b20\d{2}\b", s)
    if not want:
        return []
    content = r.get("content")
    if content is not None:
        ends = [
            str(e.end)[:4] if e.end else None
            for section in content.sections
            if section.type == "education"
            for e in section.entries
        ]
    else:
        ends = re.findall(r"\b20\d{2}\b", " ".join(resume_section(r["text"], "education")))
    found = [y for y in ends if y and re.fullmatch(r"\d{4}", y)]
    if not found:
        return [
            {
                "status": "unclear",
                "evidence": None,
                "advice": "Add your graduation year (or expected year) to your education so a recruiter can check the batch.",
            }
        ]
    unique = list(dict.fromkeys(found))
    evidence = f"Graduation years on your resume: {', '.join(unique)}"
    if any(y in want for y in found):
        return [
            {
                "status": "met",
                "evidence": evidence,
                "advice": 'Keep the year next to your degree, for example "B.Tech, 2026 (expected)".',
            }
        ]
    return [
        {
            "status": "not-met",
            "evidence": evidence,
            "advice": f"This hiring is for {' or '.join(want)} graduates; check the eligibility before applying.",
        }
    ]


def check_location(s: str, r: dict, job: str | None = None) -> list[dict]:
    content = r.get("content")
    stored = content.basics.location if content is not None and content.basics else None
    where = resume_location(r)
    cities = [c for c in CITIES if c["re"].search(s)]
    country = (
        next((c for c in COUNTRIES if c["re"].search(s)), None)
        if re.search(r"\bremote\b", s, re.IGNORECASE)
        else None
    )
    based = re.search(r"\b(?:based in|located in|office in)\s+([A-Z][a-z]+)", s)
    if country:
        city_parts = (
            "|".join(c["re"].pattern for c in CITIES if c["country"] == country["name"]) or "$^"
        )
        targets = [
            {
                "name": f"{country['name']} (remote)",
                "re": re.compile(f"{country['re'].pattern}|{city_parts}", country["flags"]),
            }
        ]
    elif cities and re.search(
        r"\b(on-?site|in[- ]office|office|work from|wfo|hybrid|based|located|location|relocat)",
        s,
        re.IGNORECASE,
    ):
        targets = cities
    elif based:
        targets = [
            {"name": based.group(1), "re": re.compile(rf"\b{based.group(1)}\b", re.IGNORECASE)}
        ]
    else:
        targets = []
    if not targets:
        return []
    names = " or ".join(t["name"] for t in targets)
    label = "Remote, country restricted" if country else "Job location"
    if not where.strip():
        return [
            {
                "label": label,
                "status": "not-on-resume",
                "evidence": None,
                "advice": "Add your city and country to the top of your resume; recruiters filter by location.",
            }
        ]
    evidence = f"Your resume says {clip(where.strip(), 60)}"
    hit = next((t for t in targets if t["re"].search(where)), None)
    if hit:
        hit_line = stored if stored else line_with(where, hit["re"])
        return [
            {
                "label": label,
                "status": "met",
                "evidence": f"Your resume says {hit_line}",
                "advice": "Keep your city in the header so location filters match you.",
            }
        ]
    return [
        {
            "label": label,
            "status": "not-met" if stored else "unclear",
            "evidence": evidence if stored else None,
            "advice": f"This remote role hires in {'the ' if country and country['name'].startswith('United') else ''}"
            f"{country['name']} only; apply if you live there and put it in your header."
            if country
            else f'If you can work from {names}, add "Open to relocating to {names}" next to your location.',
        }
    ]


def not_on_resume(advice: str) -> list[dict]:
    return [
        {
            "status": "not-on-resume",
            "evidence": None,
            "advice": f"Not on your resume; be ready to answer this. {advice}",
        }
    ]


def mentioned(r: dict, pattern: re.Pattern, advice: str, missing: str) -> list[dict]:
    line = line_with(r["text"], pattern)
    if line:
        return [{"status": "met", "evidence": f'Your resume says "{line}"', "advice": advice}]
    return not_on_resume(missing)


def check_work_authorization(s: str, r: dict, job: str) -> list[dict]:
    found = next((c for c in COUNTRIES if c["re"].search(s)), None)
    name = (
        found["name"]
        if found
        else next((c["name"] for c in COUNTRIES if c["re"].search(job)), None)
    )
    country = ("the " + name) if name and name.startswith("United") else (name or "that country")
    missing = (
        f"This job does not sponsor visas, so apply only if you can already work in {country}."
        if re.search(
            r"\bno\b[^.]*sponsor|not (able to |be )?sponsor|unable to sponsor|without (visa )?sponsor|does not sponsor",
            job,
            re.IGNORECASE,
        )
        else f'If you can work in {country} without sponsorship, add "Authorized to work in {country}" near your location.'
    )
    return mentioned(
        r,
        re.compile(
            r"authori[sz]ed to work|work permit|green card|\bcitizen\b|permanent resident",
            re.IGNORECASE,
        ),
        "Keep it near your location so a recruiter sees it.",
        missing,
    )


def check_certification(s: str, r: dict, job: str | None = None) -> list[dict]:
    findings = []
    for c in CERTS:
        if not c["job"].search(s):
            continue
        line = line_with(r["text"], c["resume"])
        if line:
            findings.append(
                {
                    "label": c["label"],
                    "status": "met",
                    "evidence": f'Your resume says "{line}"',
                    "advice": "List it under Certifications with the year so a keyword filter finds it.",
                }
            )
        else:
            findings.append(
                {
                    "label": c["label"],
                    "status": "not-met",
                    "evidence": None,
                    "advice": f"If you hold {c['label']} or are pursuing it "
                    '(for example "Level I candidate"), list it under Certifications.',
                }
            )
    return findings


LANGUAGE_TEST = re.compile(
    rf"\b(fluen\w*|proficien\w*|native|business[- ]level|speak\w*|written and spoken|spoken and written)\b"
    rf"[^.]*\b({'|'.join(LANGUAGES[1:])})\b"
    rf"|\b({'|'.join(LANGUAGES[1:])})\b[^.]*\b(fluen\w*|proficien\w*|speak\w*|native)\b",
    re.IGNORECASE,
)


def check_language(s: str, r: dict, job: str | None = None) -> list[dict]:
    findings = []
    for lang in LANGUAGES[1:]:
        if not re.search(rf"\b{lang}\b", s, re.IGNORECASE):
            continue
        for f in mentioned(
            r,
            re.compile(rf"\b{lang}\b", re.IGNORECASE),
            "Keep it in a Languages line.",
            f"If you speak {lang}, add it to a Languages line with your level.",
        ):
            findings.append({**f, "label": f"{lang} language"})
    return findings


def _check_degree_rule(s: str, r: dict, job: str | None = None) -> list[dict]:
    return check_degree(s, r) if any(is_degree(d, s) for d in DEGREES) else []


RULES = [
    {
        "id": "experience-years",
        "label": "Years of experience",
        "test": re.compile(
            r"\bfreshers?\b|\b(years?|yrs?)\b[^.]*\b(experience|exp)\b|\b(experience|exp)\b[^.]*\b(years?|yrs?)\b",
            re.IGNORECASE,
        ),
        "skip": COMPANY_SUBJECT,
        "check": check_experience,
    },
    {"id": "degree", "label": "Degree", "test": re.compile(r"."), "check": _check_degree_rule},
    {
        "id": "graduation-year",
        "label": "Graduation year",
        "test": re.compile(
            r"\b20\d{2}\b[^.]*\b(batch|graduat\w*|pass(ing)?[- ]?outs?)\b|\b(batch|class) of 20\d{2}\b|\bgraduating in 20\d{2}\b",
            re.IGNORECASE,
        ),
        "check": check_graduation_year,
    },
    {"id": "location", "label": "Job location", "test": re.compile(r"."), "check": check_location},
    {
        "id": "relocation",
        "label": "Willing to relocate",
        "test": re.compile(r"\brelocat", re.IGNORECASE),
        "skip": re.compile(
            r"relocation (assistance|support|package|bonus|allowance|benefits?|provided|reimburse\w*)",
            re.IGNORECASE,
        ),
        "check": lambda s, r, job: mentioned(
            r,
            re.compile(r"relocat", re.IGNORECASE),
            "Good: recruiters filter on this.",
            'If you are open to moving, add "Open to relocation" next to your location.',
        ),
    },
    {
        "id": "work-authorization",
        "label": "Work authorization",
        "test": re.compile(
            r"authori[sz]ed to work|work authori[sz]ation|right to work|sponsor|\bvisas?\b|work permit|green card|\bcitizens?(hip)?\b|\bH-?1B\b",
            re.IGNORECASE,
        ),
        "check": check_work_authorization,
    },
    {
        "id": "notice-period",
        "label": "Notice period",
        "test": re.compile(
            r"immediate(ly)? (joiners?|join|start|available)|notice period|join (within|in) \d+ days|early joiners?|serving notice",
            re.IGNORECASE,
        ),
        "check": lambda s, r, job: mentioned(
            r,
            re.compile(
                r"notice period|immediate(ly)? (available|joiner)|available to join", re.IGNORECASE
            ),
            "Recruiters on Naukri filter on this, so keep it visible.",
            'If your notice period is short, say so in your summary, for example "Notice period: 15 days".',
        ),
    },
    {
        "id": "certification",
        "label": "Certification",
        "test": re.compile(r"."),
        "check": check_certification,
    },
    {"id": "language", "label": "Language", "test": LANGUAGE_TEST, "check": check_language},
    {
        "id": "clearance",
        "label": "Security clearance",
        "test": re.compile(
            r"\bsecurity clearance\b|\bclearance (required|eligible|eligibility)\b|\btop secret\b|\bTS/SCI\b|\b(SC|DV) clearance\b",
            re.IGNORECASE,
        ),
        "check": lambda s, r, job: not_on_resume(
            "If you hold a clearance, name its level; otherwise check whether you are eligible to get one."
        ),
    },
    {
        "id": "travel",
        "label": "Travel",
        "test": re.compile(
            r"\btravel\w*\b[^.]*(\d{1,3}\s?%|\brequired\b)|\b(willing\w* to|ability to|frequent|extensive|occasional) travel",
            re.IGNORECASE,
        ),
        "check": lambda s, r, job: not_on_resume(
            "Decide how much travel you can take before the interview."
        ),
    },
    {
        "id": "shift",
        "label": "Shift timings",
        "test": re.compile(
            r"\b(night|rotational|rotating|graveyard|evening|US|UK|EST|PST) shifts?\b|\b24 ?(x|/) ?7\b|\bweekend (work|shifts?)\b|\bshift timings?\b",
            re.IGNORECASE,
        ),
        "check": lambda s, r, job: not_on_resume(
            "Check that you can work these hours before applying."
        ),
    },
]


def job_sentences(job_text: str) -> list[dict]:
    out: list[dict] = []
    kind = "other"
    sectioned = False
    for raw in job_text.split("\n"):
        line = re.sub(r"^[\s>#*\u2022\u00b7\u25aa\u25cf-]+|\*+$", "", raw).strip()
        if not line:
            continue
        is_heading = (
            len(line.split()) <= 6
            and not re.search(r"[.;]$", line)
            and not re.search(r":\s*\S", line)
            and not re.match(r"[-*\u2022]", raw.strip())
        )
        heading = re.sub(r":$", "", line) if is_heading else ""
        if heading and (
            BLURB_HEADING.search(heading)
            or PREFERRED.search(heading)
            or REQ_HEADING.search(heading)
        ):
            kind = (
                "blurb"
                if BLURB_HEADING.search(heading)
                else "pref"
                if PREFERRED.search(heading)
                else "req"
            )
            sectioned = sectioned or kind != "blurb"
            continue
        if kind == "blurb":
            continue
        for text in re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9])", line):
            for piece in re.findall(r".{1,400}", text, re.DOTALL):
                out.append({"text": piece.strip(), "kind": kind})
    if sectioned:
        not_other = [s for s in out if s["kind"] != "other"]
        other = [s for s in out if s["kind"] == "other"]
        out = not_other + other
    return out


def find_knockouts(job_text: str, resume: dict) -> list[dict]:
    found: dict[str, dict] = {}
    for sentence in job_sentences(job_text):
        for rule in RULES:
            if not rule["test"].search(sentence["text"]):
                continue
            if rule.get("skip") and rule["skip"].search(sentence["text"]):
                continue
            for finding in rule["check"](sentence["text"], resume, job_text):
                label = finding.get("label") or rule["label"]
                key = f"{rule['id']}:{label}"
                if key in found:
                    continue
                required = sentence["kind"] != "pref" and not PREFERRED.search(sentence["text"])
                rest = {k: v for k, v in finding.items() if k != "label"}
                found[key] = {
                    "id": rule["id"],
                    "label": label,
                    "requirement": clip(sentence["text"]),
                    "required": required,
                    **rest,
                }

    def clean(value: str) -> str:
        value = re.sub(r"[\ue000-\uf8ff\ufffd]", "", value)
        value = re.sub(r"\s*[\u2013\u2014]\s*", " - ", value)
        return re.sub(r"\s{2,}", " ", value).strip()

    result = [
        {**k, "evidence": clean(k["evidence"]) if k["evidence"] else k["evidence"]}
        for k in found.values()
    ]
    result = sorted(result, key=lambda k: not k["required"])
    return result[:MAX_KNOCKOUTS]
