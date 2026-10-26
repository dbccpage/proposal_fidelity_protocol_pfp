"""DEV vs STRICT evaluation modes (STORY-033-005).

String mode inputs are coerced via parse_mode — never fail open on raw str.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from .mode import Mode
from .mode_verdict import ModeVerdict


def parse_mode(raw: str | None, default: Mode = Mode.STRICT) -> Mode:
    if raw is None:
        return default
    u = str(raw).upper()
    if u == "DEV":
        return Mode.DEV
    if u == "STRICT":
        return Mode.STRICT
    raise ValueError(f"UNKNOWN_MODE:{raw}")


def _coerce_mode(mode: Mode | str) -> Mode:
    if isinstance(mode, Mode):
        return mode
    if isinstance(mode, str):
        return parse_mode(mode)
    raise TypeError(f"INVALID_MODE_TYPE:{type(mode).__name__}")


def evaluate_measurement(
    mode: Mode | str,
    *,
    required: Mapping[str, str],
) -> ModeVerdict:
    """required maps fact_name -> MEASURED | INJECTED | NOT_MEASURED | OPTIONAL_SKIP.

    STRICT refuses anything other than MEASURED (including INJECTED).
    Passing the string "STRICT" is coerced — it must not fail open.
    """
    mode_e = _coerce_mode(mode)
    for name, prov in required.items():
        if prov == "OPTIONAL_SKIP":
            if mode_e == Mode.STRICT:
                return ModeVerdict(False, f"STRICT_OPTIONAL_NOT_ALLOWED:{name}")
            continue
        if mode_e == Mode.STRICT and prov != "MEASURED":
            return ModeVerdict(False, f"STRICT_MISSING_MEASUREMENT:{name}:{prov}")
        if mode_e == Mode.DEV and prov == "NOT_MEASURED":
            return ModeVerdict(False, f"DEV_REQUIRED_NOT_MEASURED:{name}")
    return ModeVerdict(True, None)
