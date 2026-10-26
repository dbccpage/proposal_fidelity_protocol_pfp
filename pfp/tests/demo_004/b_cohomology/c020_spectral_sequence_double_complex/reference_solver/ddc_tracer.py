"""DDC 8-letter operational tracer for C020."""

from __future__ import annotations

from typing import Any

# DDC 8-letter alphabet: E, R, C, I, Lambda, D, M, T
VALID_DDC_LETTERS = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}


def trace_ddc_step(
    action: str,
    letter: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if letter not in VALID_DDC_LETTERS:
        raise ValueError(f"Invalid DDC letter: {letter}")
    return {
        "action": action,
        "ddc_letter": letter,
        "payload": payload or {},
    }
