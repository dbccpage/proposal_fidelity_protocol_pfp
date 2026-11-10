"""Strict JSON envelope validation for C023 certificates."""

from __future__ import annotations

from typing import Any

CASE_ID_KEY = "id"
STATUS_SCHEMAS = {
    "SOLVED": ({"id", "status", "circuit"},),
    "UNKNOWN": ({"id", "status", "refusal_code"},),
    "OUT_OF_SCOPE": ({"id", "status", "witness"},),
}
_BOOL_KEYS: set[str] = set()


def _validate_json(value: Any, path: tuple[str, ...] = ()) -> str | None:
    if value is None or isinstance(value, str) or type(value) is int:
        return None
    if type(value) is bool:
        if path and path[-1] in _BOOL_KEYS:
            return None
        return f"boolean is not permitted at {'.'.join(path)}"
    if isinstance(value, list):
        for index, item in enumerate(value):
            error = _validate_json(item, (*path, str(index)))
            if error:
                return error
        return None
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"non-string object key at {'.'.join(path)}"
            error = _validate_json(item, (*path, key))
            if error:
                return error
        return None
    return f"non-JSON value {type(value).__name__} at {'.'.join(path)}"


def validate_certificate(case: Any, answer: Any) -> str | None:
    if not isinstance(case, dict) or not isinstance(answer, dict):
        return "case and certificate must be JSON objects"
    case_id = case.get(CASE_ID_KEY)
    if not isinstance(case_id, str) or not case_id:
        return f"case must contain a non-empty {CASE_ID_KEY!r}"
    if answer.get("id") != case_id or type(answer.get("id")) is not str:
        return "certificate id must exactly match the case id"
    status = answer.get("status")
    schemas = STATUS_SCHEMAS.get(status)
    if schemas is None:
        return f"unsupported status: {status!r}"
    keys = set(answer)
    if not any(keys == schema for schema in schemas):
        return f"certificate keys do not match the {status} schema: {sorted(keys)}"
    return _validate_json(answer)
