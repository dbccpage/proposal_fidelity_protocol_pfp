"""Exact-wire payload builders for the theory runtime actions.

Builders only: nothing here spawns a process or evaluates anything. A value
crosses the seam as a canonical rational string -- ``"p"`` or ``"p/q"`` in
lowest terms with a positive denominator -- because the host refuses every
other spelling. Floats and booleans are refused here, before a request exists,
rather than rounded into something the host would then certify.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

_LOCUS = "omega_engine_operating_system.adapters.rust_host.theory_requests"


def _refuse(code: str, message: str) -> Err:
    return Err(Refusal(code=code, message=message, locus=_LOCUS))


def exact_wire(value: Any) -> str:
    """Canonical rational string for ``value``, or ``ValueError``/``TypeError``.

    ``"1"`` never ``"1/1"``: a unit denominator is dropped, as the host's
    parser requires.
    """
    if isinstance(value, bool):
        raise TypeError("a boolean is not a rational")
    if isinstance(value, float):
        raise TypeError(f"float {value!r} refused: exact values only")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Fraction):
        return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    if isinstance(value, str):
        numerator, _, denominator = value.partition("/")
        if denominator and int(denominator) == 0:
            raise ValueError(f"{value!r} has a zero denominator")
        canonical = exact_wire(Fraction(int(numerator), int(denominator or "1")))
        if canonical != value:
            raise ValueError(f"{value!r} is not canonical; the host expects {canonical!r}")
        return value
    raise TypeError(f"{type(value).__name__} is not an exact rational")


def matrix_wire(rows: Sequence[Sequence[Any]]) -> dict[str, list[list[str]]]:
    return {"rows": [[exact_wire(entry) for entry in row] for row in rows]}


def functional_evaluate_payload(
    d0: Sequence[Sequence[Any]],
    d1: Sequence[Sequence[Any]],
    residual: Sequence[Any],
    *,
    weights: Sequence[Any] | None = None,
    budget: int | None = None,
) -> Result[dict[str, Any], Refusal]:
    """Payload for ``functional_evaluate``: ``d0: C^0 -> C^1``, ``d1: C^1 -> C^2``."""
    try:
        payload: dict[str, Any] = {
            "d0": matrix_wire(d0),
            "d1": matrix_wire(d1),
            "residual": [exact_wire(value) for value in residual],
        }
        if weights is not None:
            payload["weights"] = [exact_wire(value) for value in weights]
    except (TypeError, ValueError) as exc:
        return _refuse("THEORY_REQUEST_NOT_EXACT", str(exc))
    if budget is not None:
        if isinstance(budget, bool) or not isinstance(budget, int) or budget < 0:
            return _refuse("THEORY_REQUEST_NOT_EXACT", "budget must be a non-negative integer")
        payload["budget"] = budget
    return Ok(payload)


def functional_verify_payload(
    request: Mapping[str, Any], receipt: Mapping[str, Any]
) -> Result[dict[str, Any], Refusal]:
    """Payload for ``functional_verify``: a request and the receipt claimed for it."""
    if not isinstance(request, Mapping) or not isinstance(receipt, Mapping):
        return _refuse("THEORY_REQUEST_NOT_EXACT", "request and receipt must be mappings")
    return Ok({"request": dict(request), "receipt": dict(receipt)})


__all__ = [
    "exact_wire",
    "functional_evaluate_payload",
    "functional_verify_payload",
    "matrix_wire",
]
