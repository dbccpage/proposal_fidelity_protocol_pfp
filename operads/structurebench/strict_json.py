"""Pure strict-JSON policy used by StructureBench constraints."""

import json
import math
from typing import Any

from .errors import StructureBenchError


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StructureBenchError("MALFORMED_JSON", f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise StructureBenchError("MALFORMED_JSON", f"nonfinite JSON token {token!r}")


def _finite_float(token: str) -> float:
    number = float(token)
    if not math.isfinite(number):
        raise StructureBenchError(
            "MALFORMED_JSON", f"JSON number exceeds finite binary64: {token!r}"
        )
    return number


def decode_json(raw: bytes | str) -> Any:
    """Decode unique-key JSON with finite binary64 floats and strict UTF-8."""
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise StructureBenchError("MALFORMED_JSON", str(exc)) from exc


def keys_in_order(node: Any) -> bool:
    """Return whether every object preserves ordinally sorted key order."""
    if isinstance(node, dict):
        keys = list(node)
        return keys == sorted(keys) and all(keys_in_order(value) for value in node.values())
    if isinstance(node, list):
        return all(keys_in_order(item) for item in node)
    return True


def jsonl_key_order_findings(raw: bytes, tape: str) -> tuple[list[str], list[str]]:
    """Return unsorted and unreadable JSONL line descriptions."""
    unsorted: list[str] = []
    unchecked: list[str] = []
    for index, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            step = decode_json(line)
        except StructureBenchError as exc:
            unchecked.append(f"{tape} line {index} ({exc})")
            continue
        if not keys_in_order(step):
            unsorted.append(f"{tape} line {index}")
    return unsorted, unchecked


__all__ = ["decode_json", "jsonl_key_order_findings", "keys_in_order"]
