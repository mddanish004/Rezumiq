"""Skill matching, ported from modules/ats/skills/match.ts."""

from __future__ import annotations

import json
import os
import re

from .tokens import name_key, tokenize

_DATA_PATH = os.path.join(os.path.dirname(__file__), "skills.json")
with open(_DATA_PATH) as f:
    DATA = json.load(f)

NAMES = {}
LONGEST = [1]


def _init():
    for entry in DATA:
        for name in [entry["name"]] + (entry.get("aliases") or []):
            key = name_key(name)
            if key in NAMES:
                continue
            ambiguous = name == entry["name"] and bool(entry.get("ambiguous"))
            cased = ambiguous or (name in (entry.get("cased") or []))
            NAMES[key] = {"entry": entry, "name": name, "ambiguous": ambiguous, "cased": cased}
            LONGEST[0] = max(LONGEST[0], len(key.split()))


_init()

AFTER = {
    "programming",
    "language",
    "lang",
    "developer",
    "developers",
    "programmer",
    "programmers",
    "engineer",
    "engineers",
    "code",
    "coding",
    "scripting",
    "scripts",
    "skills",
    "spreadsheet",
    "spreadsheets",
    "vba",
    "macros",
    "formulas",
    "pivot",
    "vlookup",
    "modeling",
    "modelling",
    "models",
    "model",
    "dashboards",
    "sdk",
    "framework",
    "services",
    "microservices",
    "backend",
    "runtime",
}
BEFORE = {"microsoft", "ms", "advanced", "apple", "using"}
BEFORE_PREP = {"in", "with", "of"}
BEFORE_LEAD = {
    "proficient",
    "proficiency",
    "experience",
    "experienced",
    "expertise",
    "skilled",
    "knowledge",
    "fluent",
    "fluency",
    "working",
    "programming",
    "coding",
    "developed",
    "built",
    "written",
    "wrote",
    "writing",
}
LIST_GAP = re.compile(r"^[\s,|/;&()\u00b7\u2022+]*[,|/;&()\u00b7\u2022+][\s,|/;&()\u00b7\u2022+]*$")


def _has_cue(tokens, o):
    before = tokens[o["first"] - 1]["key"] if o["first"] - 1 >= 0 else ""
    lead = tokens[o["first"] - 2]["key"] if o["first"] - 2 >= 0 else ""
    after_key = tokens[o["last"] + 1]["key"] if o["last"] + 1 < len(tokens) else ""
    return after_key in AFTER or before in BEFORE or (before in BEFORE_PREP and lead in BEFORE_LEAD)


def _scan(text, in_skills_section):
    tokens = tokenize(text)
    found = []
    i = 0
    n_tokens = len(tokens)
    while i < n_tokens:
        hit = None
        max_n = min(LONGEST[0], n_tokens - i)
        for n in range(max_n, 0, -1):
            key = " ".join(t["key"] for t in tokens[i : i + n])
            name = NAMES.get(key)
            if not name:
                continue
            matched_as = text[tokens[i]["start"] : tokens[i + n - 1]["end"]]
            case_ok = (
                (not name["cased"])
                or matched_as == name["name"]
                or (not name["ambiguous"] and matched_as == name["name"].upper())
            )
            if case_ok:
                hit = {"name": name, "first": i, "last": i + n - 1, "matchedAs": matched_as}
                break
        if hit:
            found.append(hit)
            i = hit["last"] + 1
        else:
            i += 1

    accepted = [
        not o["name"]["ambiguous"] or in_skills_section or _has_cue(tokens, o) for o in found
    ]

    def listed(k, j):
        left, right = (found[k], found[j]) if k < j else (found[j], found[k])
        if not left or not right or not accepted[j]:
            return False
        between = tokens[left["last"] + 1 : right["first"]]
        if len(between) > 1:
            return False
        if len(between) == 1 and between[0]["key"] not in ("and", "or"):
            return False
        if len(between) == 1:
            return True
        gap_text = text[tokens[left["last"]]["end"] : tokens[right["first"]]["start"]]
        return bool(LIST_GAP.match(gap_text))

    for k in range(1, len(found)):
        if not accepted[k] and listed(k, k - 1):
            accepted[k] = True
    for k in range(len(found) - 2, -1, -1):
        if not accepted[k] and listed(k, k + 1):
            accepted[k] = True

    return [o for idx, o in enumerate(found) if accepted[idx]]


def _to_hit(o):
    return {
        "skill": o["name"]["entry"]["name"],
        "kind": o["name"]["entry"]["kind"],
        "category": o["name"]["entry"]["category"],
        "matchedAs": o["matchedAs"],
    }


def _unique(occurrences):
    seen = {}
    for o in occurrences:
        if o["name"]["entry"]["name"] not in seen:
            seen[o["name"]["entry"]["name"]] = _to_hit(o)
    return list(seen.values())


def find_skills(text, skills_section=None):
    occ = _scan(text, False)
    if skills_section:
        occ = occ + _scan(skills_section, True)
    return _unique(occ)


def skill_forms(skill):
    for entry in DATA:
        if entry["name"] == skill:
            return [entry["name"]] + (entry.get("aliases") or [])
    return [skill]


def skill_counts(text):
    counts = {}
    for o in _scan(text, False):
        name = o["name"]["entry"]["name"]
        counts[name] = counts.get(name, 0) + 1
    return counts


NICE = re.compile(
    r"\b(?:nice|good)[ -]to[ -]have\b|\bpreferred\b|\bpreferably\b|\bbonus\b|\ba plus\b|\bplus point\b|\badvantage(?:ous)?\b|\bdesirable\b|\bdesired\b|\boptional\b|\bnot (?:required|mandatory)\b",
    re.IGNORECASE,
)
MUST = re.compile(
    r"\brequire[ds]?\b|\brequirements?\b|\bmust\b|\bmandatory\b|\bminimum\b|\bessential\b|\byou(?:'ll| will)? have\b|\bwhat you(?:'ll)? need\b|\bqualifications?\b|\bstrong (?:knowledge|experience|proficiency|understanding|command)\b|\bproficien(?:t|cy)\b|\bexpertise\b|\bhands[ -]on\b|\b\d+\+?\s*(?:years?|yrs)\b",
    re.IGNORECASE,
)
BULLET = re.compile(r"^\s*(?:[-*\u2022\u00b7\u25aa\u25cf\u2013]|\d+[.)])\s*", re.UNICODE)


def job_requirements(job_text):
    all_occ = []
    must_have = set()
    section = "neutral"

    def mode_of(text, fallback):
        if NICE.search(text):
            return "nice"
        if MUST.search(text):
            return "must"
        return fallback

    for raw_line in job_text.split("\n"):
        line = re.sub(r"^#+\s*|\*\*", "", raw_line).strip()
        if not line:
            continue
        found = _scan(line, False)
        heading = (
            (not BULLET.match(raw_line))
            and len(found) == 0
            and len(line.split()) <= 6
            and not re.search(r"[.,]$", line)
            and (line.endswith(":") or (line and line[0].isupper()))
        )
        if heading:
            section = mode_of(line, "neutral")
            continue
        for clause in re.split(r"(?<=[.;!?])\s+", line):
            occs = _scan(clause, False)
            if mode_of(clause, section) == "must":
                for o in occs:
                    must_have.add(o["name"]["entry"]["name"])
            all_occ.extend(occs)

    hits = _unique(all_occ)
    hard = [h for h in hits if h["kind"] == "hard"]
    soft = [h for h in hits if h["kind"] == "soft"]
    return {"hard": hard, "soft": soft, "mustHave": must_have}


WEIGHT = {"mustHard": 3, "hard": 2, "soft": 1}


def match_job(resume_text, job_text, skills_section=None):
    job = job_requirements(job_text)
    have = {
        h["skill"]
        for h in find_skills(
            resume_text, {"skillsSection": skills_section} if skills_section else None
        )
    }

    def split(hits):
        return {
            "matched": [h["skill"] for h in hits if h["skill"] in have],
            "missing": [h["skill"] for h in hits if h["skill"] not in have],
        }

    skills = job["hard"] + job["soft"]
    total = sum(
        WEIGHT["mustHard"]
        if (h["kind"] != "soft" and h["skill"] in job["mustHave"])
        else (WEIGHT["hard"] if h["kind"] != "soft" else WEIGHT["soft"])
        for h in skills
    )
    earned = sum(
        (
            WEIGHT["mustHard"]
            if (h["kind"] != "soft" and h["skill"] in job["mustHave"])
            else (WEIGHT["hard"] if h["kind"] != "soft" else WEIGHT["soft"])
        )
        for h in skills
        if h["skill"] in have
    )
    return {
        "hard": split(job["hard"]),
        "soft": split(job["soft"]),
        "mustHave": [h["skill"] for h in skills if h["skill"] in job["mustHave"]],
        "mustHaveMissing": [
            h["skill"] for h in skills if h["skill"] in job["mustHave"] and h["skill"] not in have
        ],
        "score": 0 if total == 0 else earned / total,
    }


SENIORITY = {
    "senior",
    "sr",
    "jr",
    "junior",
    "lead",
    "staff",
    "principal",
    "associate",
    "trainee",
    "entry",
    "level",
    "mid",
    "i",
    "ii",
    "iii",
    "iv",
    "v",
    "1",
    "2",
    "3",
}
TITLE_SYNONYMS = [
    (
        re.compile(
            r"\b(?:sde|swe|software development engineer|software developer|software engineering|programmer)\b",
            re.IGNORECASE,
        ),
        "software engineer",
    ),
    (re.compile(r"\bback end\b", re.IGNORECASE), "backend"),
    (re.compile(r"\bfront end\b", re.IGNORECASE), "frontend"),
    (re.compile(r"\bfull stack\b|\bfullstack\b", re.IGNORECASE), "fullstack"),
    (re.compile(r"\b(?:developer|dev)\b", re.IGNORECASE), "engineer"),
    (re.compile(r"\b(?:pm|apm)\b", re.IGNORECASE), "product manager"),
    (re.compile(r"\bmachine learning\b", re.IGNORECASE), "ml"),
    (re.compile(r"\bsre\b", re.IGNORECASE), "site reliability engineer"),
    (
        re.compile(
            r"\b(?:sdet|test engineer|qa engineer|quality assurance engineer)\b", re.IGNORECASE
        ),
        "qa engineer",
    ),
    (re.compile(r"\bib\b", re.IGNORECASE), "investment banking"),
    (re.compile(r"\bba\b", re.IGNORECASE), "business analyst"),
    (re.compile(r"\bui ux\b|\bux ui\b", re.IGNORECASE), "ux"),
]
ROLE_NOUNS = re.compile(
    r"\b(?:engineer|developer|analyst|manager|designer|scientist|consultant|associate|intern|architect|specialist|administrator|executive|officer|accountant|tester|sde|swe|pm|apm|lead|head|director|strategist|researcher|programmer)s?\b",
    re.IGNORECASE,
)


def _normalize_title(title):
    text = " " + re.sub(r"[^a-z0-9]+", " ", title.lower().replace("(", " ").replace(")", " ")) + " "
    for pat, repl in TITLE_SYNONYMS:
        text = pat.sub(repl, text)
    return " ".join(w for w in text.split() if w and w not in SENIORITY)


def _job_title_of(job_text):
    m = re.search(
        r"(?:\b(?:hiring|looking for|seeking)\s+(?:an?\s+)?|\b(?:role|position|job title|title|designation)\s*[:-]\s*)([^\n.,!;:(]+)",
        job_text,
        re.IGNORECASE,
    )
    phrase = m.group(1) if m else None
    from_phrase = None
    if phrase:
        from_phrase = re.split(
            r"\s+(?:to|who|with|for|in|at|on|that|from)\s+", phrase, flags=re.IGNORECASE
        )[0].strip()
    heading = None
    for line in job_text.split("\n"):
        l = re.sub(r"^#+\s*|\*\*", "", line).strip()
        l = re.sub(
            r"^(?:role|position|job title|title|designation)\s*[:-]\s*", "", l, flags=re.IGNORECASE
        ).strip()
        if l:
            heading = l.split(" - ")[0].split("|")[0].split(",")[0].strip()
            break
    if (
        heading
        and len(heading.split()) <= 6
        and not re.search(r"[.!?]$", heading)
        and ROLE_NOUNS.search(heading)
    ):
        return heading
    if from_phrase and ROLE_NOUNS.search(from_phrase):
        return from_phrase
    return None


def title_match(resume_titles, job_text):
    job_title = _job_title_of(job_text)
    job = _normalize_title(job_title) if job_title else ""
    if not job:
        return {"jobTitle": job_title, "best": None, "level": "none"}
    job_words = job.split()
    junior = re.compile(r"\b(intern|internship|trainee|apprentice)\b")
    job_is_junior = bool(junior.search(job))
    candidates = []
    for t in resume_titles:
        for part in re.split(r"\s*[|,/\u00b7\u2022]\s*|\s+[-\u2013]\s+", t):
            if part.strip():
                candidates.append(part.strip())
    best = None
    best_level = None
    for title in candidates:
        own = _normalize_title(title)
        if f" {own} ".find(f" {job} ") != -1:
            if job_is_junior or not junior.search(own):
                return {"jobTitle": job_title, "best": title, "level": "exact"}
            if best is None:
                best = title
                best_level = "close"
            continue
        words = own.split()
        if best is None and words and job_words and words[-1] == job_words[-1]:
            a = [w for w in job_words[:-1] if w != "software"]
            b = [w for w in words[:-1] if w != "software"]
            if not a or not b or any(w in b for w in a):
                best = title
                best_level = "close"
    return {"jobTitle": job_title, "best": best, "level": best_level or "none"}
