# Strict shared PFP ingress, owned by Symbol Game. AuthorityEffect: None.
from __future__ import annotations

import json
import math
from typing import Any

MAX_REPLY_BYTES = 1_048_576
MAX_JSON_DEPTH = 64


def unique_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(raw: str, *, max_bytes: int = MAX_REPLY_BYTES) -> Any:
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("JSON_SIZE_LIMIT_INVALID")
    if len(raw.encode("utf-8")) > max_bytes:
        raise ValueError("REPLY_TOO_LARGE")
    _check_depth(raw)
    return json.loads(
        raw,
        object_pairs_hook=unique_pairs,
        parse_constant=_invalid_constant,
        parse_float=_finite_float,
    )


def _check_depth(raw: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for character in raw:
        if escaped:
            escaped = False
            continue
        if character == "\\" and quoted:
            escaped = True
        elif character == '"':
            quoted = not quoted
        elif not quoted:
            depth += (character in "[{") - (character in "]}")
            if depth > MAX_JSON_DEPTH:
                raise ValueError("JSON_DEPTH_EXCEEDED")


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("NON_FINITE_JSON_NUMBER")
    return parsed


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
