"""Pure operation logic, ported from modules/suggestions/operations.ts."""

from __future__ import annotations

import copy
import re

BULLET_MAX = 2000


def _entries_of(section):
    return (
        section.get("entries", []) if isinstance(section, dict) else getattr(section, "entries", [])
    )


def _find_bullet(content, bullet_id):
    for section in content.get("sections", []):
        for entry in _entries_of(section):
            for b in entry.get("bullets", []):
                if b.get("id") == bullet_id:
                    return b, entry
    return None, None


def _entry_of_bullet(content, bullet_id):
    for section in content.get("sections", []):
        for entry in _entries_of(section):
            if any(b.get("id") == bullet_id for b in entry.get("bullets", [])):
                return entry
    return None


def _find_skill_group(content, group_id):
    for section in content.get("sections", []):
        if section.get("type") == "skills":
            for g in section.get("groups", []):
                if g.get("id") == group_id:
                    return g
    return None


def _child_ids(content, parent_id):
    if parent_id == "sections":
        return [s.get("id") for s in content.get("sections", [])]
    for section in content.get("sections", []):
        if section.get("id") == parent_id:
            if section.get("type") == "skills":
                return [g.get("id") for g in section.get("groups", [])]
            if section.get("type") in ("links", "summary"):
                return None
            return [e.get("id") for e in _entries_of(section)]
        for entry in _entries_of(section):
            if entry.get("id") == parent_id:
                return [b.get("id") for b in entry.get("bullets", [])]
    return None


def _has_target(content, target_id):
    for section in content.get("sections", []):
        if section.get("id") == target_id:
            return True
        for entry in _entries_of(section):
            if entry.get("id") == target_id:
                return True
            for b in entry.get("bullets", []):
                if b.get("id") == target_id:
                    return True
    return False


def _has_entry_or_section(content, target_id):
    for section in content.get("sections", []):
        if section.get("id") == target_id:
            return True
        for entry in _entries_of(section):
            if entry.get("id") == target_id:
                return True
    return False


def is_applicable(content, op):
    t = op.get("type")
    if t == "update_bullet":
        b, _ = _find_bullet(content, op["bulletId"])
        text = (op.get("text") or "").strip()
        return bool(b) and len(text) > 0 and len(op.get("text", "")) <= BULLET_MAX
    if t == "add_bullet":
        entry = _entry_of_bullet(content, op["afterBulletId"])
        text = (op.get("text") or "").strip()
        return (
            bool(entry)
            and len(entry.get("bullets", [])) < 20
            and len(text) > 0
            and len(op.get("text", "")) <= BULLET_MAX
        )
    if t == "update_headline":
        text = (op.get("text") or "").strip()
        return len(text) > 0 and len(op.get("text", "")) <= 200
    if t == "update_summary":
        section = next(
            (
                s
                for s in content.get("sections", [])
                if s.get("id") == op["targetId"] and s.get("type") == "summary"
            ),
            None,
        )
        text = (op.get("text") or "").strip()
        return bool(section) and bool(text) and len(op.get("text", "")) <= 1000
    if t == "set_hidden":
        return _has_target(content, op["targetId"])
    if t == "set_space_after":
        return -8 <= op["points"] <= 24 and _has_entry_or_section(content, op["targetId"])
    if t == "reorder":
        current = _child_ids(content, op["parentId"])
        if not current:
            return False
        ordered = op.get("orderedIds", [])
        return len(current) == len(ordered) and all(i in ordered for i in current)
    if t == "update_skills":
        g = _find_skill_group(content, op["groupId"])
        return bool(g) and len(op.get("items", [])) > 0
    if t == "replace_source":
        return bool((op.get("texSource") or "").strip())
    return False


def apply_operations(content, operations):
    next_content = copy.deepcopy(content)
    last_added = {}
    for op in operations:
        t = op.get("type")
        if t == "add_bullet":
            after = last_added.get(op["afterBulletId"], op["afterBulletId"])
            entry = _entry_of_bullet(next_content, after)
            if not entry or len(entry.get("bullets", [])) >= 20:
                continue
            idx = next((i for i, b in enumerate(entry["bullets"]) if b.get("id") == after), -1)
            if idx < 0:
                continue
            entry["bullets"].insert(idx + 1, {"id": op["id"], "text": op["text"], "hidden": False})
            last_added[op["afterBulletId"]] = op["id"]
        elif t == "update_bullet":
            b, _ = _find_bullet(next_content, op["bulletId"])
            if b:
                b["text"] = op["text"]
        elif t == "update_headline":
            next_content.setdefault("basics", {})["headline"] = op["text"]
        elif t == "update_summary":
            for section in next_content.get("sections", []):
                if section.get("id") == op["targetId"] and section.get("type") == "summary":
                    section["text"] = op["text"]
        elif t == "set_space_after":

            def apply_space(target, _op=op):
                if _op["points"]:
                    target["spaceAfter"] = _op["points"]
                else:
                    target.pop("spaceAfter", None)

            for section in next_content.get("sections", []):
                if section.get("id") == op["targetId"]:
                    apply_space(section)
                for entry in _entries_of(section):
                    if entry.get("id") == op["targetId"]:
                        apply_space(entry)
        elif t == "set_hidden":
            for section in next_content.get("sections", []):
                if section.get("id") == op["targetId"]:
                    section["hidden"] = op["hidden"]
                for entry in _entries_of(section):
                    if entry.get("id") == op["targetId"]:
                        entry["hidden"] = op["hidden"]
                    for b in entry.get("bullets", []):
                        if b.get("id") == op["targetId"]:
                            b["hidden"] = op["hidden"]
        elif t == "reorder":
            if op["parentId"] == "sections":
                idmap = {s.get("id"): s for s in next_content.get("sections", [])}
                next_content["sections"] = [idmap[i] for i in op["orderedIds"] if i in idmap]
            else:
                for section in next_content.get("sections", []):
                    if section.get("id") == op["parentId"]:
                        if section.get("type") == "skills":
                            gmap = {g.get("id"): g for g in section.get("groups", [])}
                            section["groups"] = [gmap[i] for i in op["orderedIds"] if i in gmap]
                        elif "entries" in section:
                            emap = {e.get("id"): e for e in section["entries"]}
                            section["entries"] = [emap[i] for i in op["orderedIds"] if i in emap]
                    for entry in _entries_of(section):
                        if entry.get("id") == op["parentId"]:
                            bmap = {b.get("id"): b for b in entry.get("bullets", [])}
                            entry["bullets"] = [bmap[i] for i in op["orderedIds"] if i in bmap]
        elif t == "update_skills":
            g = _find_skill_group(next_content, op["groupId"])
            if g:
                g["items"] = op["items"]
    return next_content


def unverified_terms(text, fact_sources):

    fact_pattern = re.compile(
        r"\b\d+(?:[.,]\d+)?(?:\s*(?:%|x|\+|[kKmMbB]\b|cr\b|lpa\b|ms\b))?|\b[a-z]+\d+[a-z0-9]*\b|\b[A-Z][A-Za-z0-9]*(?:[.#+-][A-Za-z0-9]+)*\+{0,2}|\b[a-z]+(?:\.[a-z]+)+\b"
    )
    ignored = {
        "i",
        "a",
        "the",
        "built",
        "led",
        "developed",
        "designed",
        "implemented",
        "created",
        "improved",
    }
    corpus = " ".join(fact_sources).lower().replace(" ", "")

    def normalize(term):
        return term.lower().replace(" ", "")

    terms = set()
    for m in fact_pattern.finditer(text.replace("**", "")):
        term = m.group(0).strip()
        norm = normalize(term)
        if len(norm) < 2 or norm in ignored:
            continue
        if re.match(r"^[A-Z][a-z]+$", term) and text.strip().startswith(term):
            continue
        if norm not in corpus:
            terms.add(term)
    return list(terms)


def fact_text(content):
    import json

    from pydantic import BaseModel

    if isinstance(content, BaseModel):
        content = content.model_dump(exclude_none=True)
    return json.dumps(content).replace('"id"', " ").replace('"hidden"', " ").replace('"type"', " ")
