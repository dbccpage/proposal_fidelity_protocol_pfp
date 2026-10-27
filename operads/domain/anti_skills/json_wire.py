"""Strict JSON loader for the anti-skill wire boundary.

Pure parsing, no I/O; carried over unchanged from the retired
`engine/crates/prompt_civilization/infrastructure/json_wire.py`.
"""

from __future__ import annotations

import json
from typing import Any


def _exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is forbidden: {value}")


def loads_strict_json(text: str) -> Any:
    if type(text) is not str:
        raise TypeError("JSON input must be an exact string")
    return json.loads(
        text,
        object_pairs_hook=_exact_object,
        parse_constant=_reject_constant,
    )


__all__ = ["loads_strict_json"]
