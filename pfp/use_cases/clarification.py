"""Check a missing-input residual against host-selected task requirements.

This checks an explicit input contract. It neither invents task premises nor
proves that an arbitrary natural-language question is mathematically determined.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import sha256

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result


@dataclass(frozen=True)
class ClarificationCheck:
    outcome: str
    missing_fields: tuple[str, ...]
    seed_sha256: str
    requirements_sha256: str
    mathematical_acceptance: str = "NOT_SOLVED"
    authority_effect: str = "None"


def _json_value(value, depth=0):
    if depth > 64:
        return False
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        value.encode("utf-8")
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item, depth + 1) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(key, depth + 1)
                   and _json_value(item, depth + 1) for key, item in value.items())
    return False


def check_clarification(candidate: dict, *, seed: str, required_fields: tuple[str, ...],
                        supplied_fields: dict) -> Result[ClarificationCheck, Refusal]:
    """Accept QUERY_USER_MORE_INFO only for actually absent declared inputs."""
    def refused(code):
        return Err(Refusal(code, "Clarification does not match the declared missing task inputs.", __name__))

    if (type(seed) is not str or not seed.strip() or type(required_fields) is not tuple
            or not required_fields or any(type(field) is not str or not field.strip() for field in required_fields)
            or len(set(required_fields)) != len(required_fields)
            or type(supplied_fields) is not dict or not set(supplied_fields) <= set(required_fields)):
        return refused("TASK_REQUIREMENTS_INVALID")
    try:
        seed_bytes = seed.encode("utf-8")
        if not _json_value(supplied_fields) or not _json_value(candidate):
            return refused("TASK_REQUIREMENTS_INVALID")
    except (UnicodeError, RecursionError):
        return refused("TASK_REQUIREMENTS_INVALID")
    # None/blank strings are absent. Other explicit JSON values are premises,
    # including false/zero; do not silently discard them by truthiness.
    missing = tuple(field for field in required_fields if field not in supplied_fields
        or supplied_fields[field] is None or (type(supplied_fields[field]) is str
                                              and not supplied_fields[field].strip()))
    if not missing:
        return refused("QUERY_WITHOUT_MISSING_INPUTS")
    if (type(candidate) is not dict or set(candidate) != {
            "outcome", "seed", "missing_fields", "questions", "proposal"}
            or candidate["outcome"] != "QUERY_USER_MORE_INFO"
            or type(candidate["seed"]) is not str or candidate["seed"] != seed
            or candidate["proposal"] != "" or type(candidate["proposal"]) is not str
            or type(candidate["missing_fields"]) is not list
            or any(type(field) is not str for field in candidate["missing_fields"])
            or candidate["missing_fields"] != list(missing)):
        return refused("CLARIFICATION_BINDING_MISMATCH")
    questions = candidate["questions"]
    if type(questions) is not list or len(questions) != len(missing):
        return refused("CLARIFICATION_QUESTIONS_REQUIRED")
    for field, question in zip(missing, questions, strict=True):
        if (type(question) is not dict or set(question) != {"field", "question"}
                or question["field"] != field or type(question["question"]) is not str
                or not question["question"].strip() or len(question["question"]) > 500):
            return refused("CLARIFICATION_QUESTIONS_REQUIRED")
    try:
        wire = json.dumps({"required_fields": required_fields, "supplied_fields": supplied_fields},
                          sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        wire_bytes = wire.encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return refused("TASK_REQUIREMENTS_INVALID")
    return Ok(ClarificationCheck(outcome="QUERY_USER_MORE_INFO", missing_fields=missing,
        seed_sha256=sha256(seed_bytes).hexdigest(),
        requirements_sha256=sha256(wire_bytes).hexdigest()))
