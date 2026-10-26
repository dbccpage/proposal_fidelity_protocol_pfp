"""Six-part lesson check. Completeness is not promotion. AuthorityEffect: None."""

from __future__ import annotations

import json
import re
from typing import Mapping

# The plan's six parts. Source is split into path and revision. The correction
# part is split into the change and the check. The lesson part is split into
# where it applies and where it does not.
LESSON_FIELDS: tuple[str, ...] = (
    "source_path",
    "source_revision",
    "failed_claim",
    "counterexample",
    "cause",
    "correction",
    "verification",
    "applicability",
    "exceptions",
)

_LABEL = re.compile(r"^\s*-?\s*\**([a-z_]+)\**\s*:\s*`?(.+?)`?\s*$", re.IGNORECASE)


def _from_mapping(payload: Mapping[str, object]) -> dict[str, str]:
    found: dict[str, str] = {}
    for key in LESSON_FIELDS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            found[key] = value.strip()
    return found


def _from_markdown(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        match = _LABEL.match(line)
        if not match:
            continue
        key = match.group(1).lower()
        if key in LESSON_FIELDS and key not in found:
            value = match.group(2).strip()
            if value:
                found[key] = value
    return found


def extract_lesson_fields(text: str) -> dict[str, str]:
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            return _from_mapping(payload)
    return _from_markdown(text)


def lesson_status(text: str) -> tuple[str, dict[str, str]]:
    """Return ``(touch_provenance|lesson_candidate|lesson_incomplete|none, fields)``.

    ``none`` means the text does not attempt a lesson. A session that only says
    ``record_kind: touch_provenance`` is provenance, not an incomplete lesson.
    """
    if re.search(r"record_kind\**\s*:\s*`?touch_provenance`?", text, re.IGNORECASE):
        return "touch_provenance", {}
    fields = extract_lesson_fields(text)
    if not fields:
        return "none", {}
    missing = [key for key in LESSON_FIELDS if key not in fields]
    if missing:
        return "lesson_incomplete", fields
    return "lesson_candidate", fields
