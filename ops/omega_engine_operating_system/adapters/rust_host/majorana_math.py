"""Native exact-math calls used by the Majorana paper's Python carriers.

This adapter uses the canonical process seam. Algebra and acceptance decisions
belong to the Rust owners; no Python computational fallback is provided.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from types import MappingProxyType
from typing import Any

from omega_engine_operations.domain.rop.result import Err

from .ffi import RustSymbolGameHost


class NativeMathRefusal(ValueError):
    """A native refusal or failed process crossing, with its original evidence."""

    def __init__(self, code: str, message: str, *, outcome: Any = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.outcome = outcome


class NativeMathReply(dict):
    """Dictionary-compatible result retaining the complete native outcome."""

    def __init__(self, outcome: Mapping[str, Any]) -> None:
        super().__init__(outcome["result"])
        self.outcome = MappingProxyType(dict(outcome))


def decode_rational(value: object) -> Fraction:
    """Decode one canonical exact coefficient without admitting numeric aliases."""
    message = "native coefficient must be a canonical rational string"
    if not isinstance(value, str):
        raise NativeMathRefusal("NATIVE_MATH_RATIONAL", message, outcome=value)
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise NativeMathRefusal("NATIVE_MATH_RATIONAL", message, outcome=value) from error
    if str(result) != value:
        raise NativeMathRefusal("NATIVE_MATH_RATIONAL", message, outcome=value)
    return result


def call_native(
    action: str,
    payload: Mapping[str, Any],
    *,
    host: RustSymbolGameHost | None = None,
) -> NativeMathReply:
    """Invoke one exact native operation or raise a refusal carrying its evidence."""
    crossed = (host or RustSymbolGameHost()).invoke_runtime(action, payload)
    if isinstance(crossed, Err):
        raise NativeMathRefusal(crossed.error.code, crossed.error.message, outcome=crossed.error)
    outcome = crossed.value
    if outcome.get("success") is not True:
        raise NativeMathRefusal("NATIVE_MATH_REFUSED", str(outcome.get("error")), outcome=outcome)
    if not isinstance(outcome.get("result"), Mapping):
        raise NativeMathRefusal(
            "NATIVE_MATH_RESULT_SHAPE", "native result must be an object", outcome=outcome
        )
    return NativeMathReply(outcome)
