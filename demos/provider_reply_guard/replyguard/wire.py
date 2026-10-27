"""Shared bounded, strict provider JSON decoder. AuthorityEffect: None."""

import json
import math
from collections.abc import Mapping
from typing import Any

from replyguard.provider_types import ProviderError, check_reply_bytes


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProviderError("provider reply JSON contains duplicate object keys")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ProviderError("provider reply JSON contains a nonfinite number")
    return number


def _reject_constant(value: str) -> Any:
    raise ProviderError("provider reply JSON contains a nonfinite number")


def decode_reply(raw: bytes | bytearray | memoryview) -> Mapping[str, Any]:
    check_reply_bytes(raw)
    try:
        decoded = json.loads(
            bytes(raw).decode("utf-8"), object_pairs_hook=_unique_object,
            parse_float=_finite_float, parse_constant=_reject_constant,
        )
    except ProviderError:
        raise
    except (ValueError, RecursionError):
        raise ProviderError("provider reply is not valid UTF-8 JSON") from None
    if not isinstance(decoded, Mapping):
        raise ProviderError("provider reply must decode to a JSON object")
    return decoded


def usage_count(usage: Mapping[str, Any], key: str) -> int:
    value = usage.get(key, 0)
    if type(value) is not int or value < 0:
        raise ProviderError("provider token counts must be non-negative exact integers")
    return value


def reported_cost(value: Any) -> float | None:
    if value is None:
        return None
    if type(value) not in (str, int, float):
        raise ProviderError("invalid provider-reported cost")
    try:
        cost = float(value)
    except (ValueError, OverflowError):
        raise ProviderError("invalid provider-reported cost") from None
    if not math.isfinite(cost) or cost < 0:
        raise ProviderError("invalid provider-reported cost")
    return cost
