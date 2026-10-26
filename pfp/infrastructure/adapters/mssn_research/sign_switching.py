"""Exact finite sign switching in a specified real Hamiltonian basis.

For a real symmetric matrix H and a diagonal sign gauge
S = diag((-1)**alpha_i), this module decides whether S H S has
nonpositive off-diagonal entries.  Every nonzero off-diagonal entry
imposes one Z2 constraint:

    alpha_i XOR alpha_j = 1 if H[i][j] > 0, else 0.

The spanning-forest assignment is a complete decision procedure for
*this fixed-basis diagonal-sign gauge family*.  A failed constraint yields
a closed cycle with odd constraint parity, which proves that no such gauge
exists.  Neither outcome decides general BQNF-FSIGN sign freedom or supplies
a sign-reversing meron involution on path-integral configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Sequence

Matrix = tuple[tuple[Fraction, ...], ...]


@dataclass(frozen=True)
class SignGaugeResult:
    """One exact certificate for the specified diagonal-sign gauge family.

    On success, ``gauge`` gives alpha bits and ``transformed`` is S H S.
    On failure, ``cycle`` is a closed vertex walk over nonzero edges whose
    required XOR labels sum to 1.  Exactly one certificate kind is present.
    """

    matrix: Matrix
    gauge: tuple[int, ...] | None
    cycle: tuple[int, ...] | None
    transformed: Matrix | None

    @property
    def gaugeable(self) -> bool:
        return self.gauge is not None


def _rational(value: object, i: int, j: int) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError(f"H[{i}][{j}] must be exact rational, not {type(value).__name__}")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"H[{i}][{j}] must be finite")
        return Fraction(value)
    if isinstance(value, (int, Fraction)):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"H[{i}][{j}] is not an exact rational string") from exc
    raise ValueError(f"H[{i}][{j}] must be an exact rational value")


def parse_matrix(matrix: Sequence[Sequence[object]]) -> Matrix:
    """Validate and canonicalize a nonempty finite real symmetric matrix.

    Accepted scalar encodings are integers, Fractions, finite Decimals, and
    rational strings (for lossless JSON transport).  Binary floats, bools,
    nonfinite values, complex values, ragged rows, and asymmetry are rejected.
    """

    if not isinstance(matrix, (list, tuple)) or not matrix:
        raise ValueError("H must be a nonempty square matrix")
    n = len(matrix)
    if n > 128:
        raise ValueError("H exceeds the native signed transport dimension bound")
    rows: list[tuple[Fraction, ...]] = []
    for i, row in enumerate(matrix):
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise ValueError(f"H row {i} must have exactly {n} entries")
        rows.append(tuple(_rational(value, i, j) for j, value in enumerate(row)))
    result = tuple(rows)
    for i in range(n):
        for j in range(i + 1, n):
            if result[i][j] != result[j][i]:
                raise ValueError(f"H must be symmetric at ({i}, {j})")
    return result


class SignGaugeNativeUnavailable(RuntimeError):
    """Native execution or certificate replay refused; no Python fallback."""


MAX_DIMENSION = 128
MAX_SCALAR_BYTES = 256


def _matrix_payload(h: Matrix) -> list[list[str]]:
    if len(h) > MAX_DIMENSION:
        raise ValueError("H exceeds the native signed transport dimension bound")
    wire = [[str(q) for q in row] for row in h]
    if any(len(s) > MAX_SCALAR_BYTES for row in wire for s in row):
        raise ValueError("H exceeds the native rational encoding byte bound")
    return wire


def _native(operation: str, h: Matrix, **witness: object) -> dict:
    from omega_engine_pfp.ffi import get_default_host

    payload = {"operation": operation, "matrix": _matrix_payload(h), **witness}
    try:
        outcome = get_default_host().invoke("signed_transport", payload)
    except (FileNotFoundError, OSError) as exc:
        raise SignGaugeNativeUnavailable("NATIVE_SIGNED_TRANSPORT_UNAVAILABLE") from exc
    if outcome.is_err:
        raise SignGaugeNativeUnavailable(str(outcome.unwrap_err()))
    record = outcome.unwrap()
    if not isinstance(record, dict) or record.get("success") is not True:
        raise SignGaugeNativeUnavailable(
            str(record.get("error") if isinstance(record, dict) else record)
        )
    result = record.get("result")
    if not isinstance(result, dict) or result.get("authority_effect") != "None":
        raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
    return result


def verify_gauge(matrix: Sequence[Sequence[object]], gauge: Sequence[int]) -> bool:
    """Replay the proposed bits in the native complete-coefficient checker."""
    h = parse_matrix(matrix)
    if not isinstance(gauge, (list, tuple)) or len(gauge) != len(h):
        return False
    if any(type(bit) is not int or bit not in (0, 1) for bit in gauge):
        return False
    result = _native("verify_gauge", h, gauge=list(gauge))
    if type(result.get("valid")) is not bool:
        raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
    return result["valid"]


def verify_cycle(matrix: Sequence[Sequence[object]], cycle: Sequence[int]) -> bool:
    """Replay a supplied odd simple cycle in native signed transport."""
    h = parse_matrix(matrix)
    if not isinstance(cycle, (list, tuple)) or len(cycle) < 4 or len(cycle) > len(h) + 1:
        return False
    if any(type(v) is not int or v < 0 or v >= len(h) for v in cycle):
        return False
    result = _native("verify_cycle", h, cycle=list(cycle))
    if type(result.get("valid")) is not bool:
        raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
    return result["valid"]


def classify_sign_gauge(matrix: Sequence[Sequence[object]]) -> SignGaugeResult:
    """Native bounded forest search with independent native certificate replay.

    Python only validates exact input encodings and decodes the checked outcome.
    Component root bits and conflict-cycle traversal preserve the prior API.
    """
    h = parse_matrix(matrix)
    result = _native("classify", h)
    if result.get("certificate_verified") is not True or result.get("matrix") != _matrix_payload(h):
        raise SignGaugeNativeUnavailable("NATIVE_CERTIFICATE_NOT_VERIFIED")
    gauge, cycle, transformed = result.get("gauge"), result.get("cycle"), result.get("transformed")
    if gauge is not None:
        if (
            not isinstance(gauge, list)
            or len(gauge) != len(h)
            or any(type(bit) is not int or bit not in (0, 1) for bit in gauge)
            or cycle is not None
        ):
            raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
        try:
            decoded = parse_matrix(transformed)
        except (ValueError, TypeError) as exc:
            raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE") from exc
        if len(decoded) != len(h):
            raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
        return SignGaugeResult(h, tuple(gauge), None, decoded)
    if (
        not isinstance(cycle, list)
        or len(cycle) < 4
        or len(cycle) > len(h) + 1
        or any(type(v) is not int or v < 0 or v >= len(h) for v in cycle)
        or transformed is not None
    ):
        raise SignGaugeNativeUnavailable("INVALID_NATIVE_SIGNED_TRANSPORT_RESPONSE")
    return SignGaugeResult(h, None, tuple(cycle), None)


__all__ = [
    "Matrix",
    "SignGaugeResult",
    "SignGaugeNativeUnavailable",
    "parse_matrix",
    "classify_sign_gauge",
    "verify_gauge",
    "verify_cycle",
]
