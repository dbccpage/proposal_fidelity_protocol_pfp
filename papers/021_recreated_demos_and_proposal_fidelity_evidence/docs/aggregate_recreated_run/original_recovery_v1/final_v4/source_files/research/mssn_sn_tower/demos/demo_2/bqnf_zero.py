"""Exact structural and witness checks for a finite rational cochain packet.

This module does not construct a packet from a Hamiltonian or decide whether a
Hamiltonian has a sign problem. Named Phi1, Gamma2, and Xi functional values
belong to omega_functional; this Python module only checks supplied equations.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence


class PacketError(ValueError):
    """The finite cochain packet is malformed or fails ``d1 * d0 == 0``."""


class FunctionalAdapterUnavailable(RuntimeError):
    """No Rust functional adapter is connected to this historical demo."""


@dataclass(frozen=True)
class CochainPacket:
    """Parsed exact packet whose shape and cochain identity were checked."""

    d0: tuple[tuple[Fraction, ...], ...]
    d1: tuple[tuple[Fraction, ...], ...]
    c1: tuple[Fraction, ...]


def _rational(value: object, location: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise PacketError(f"{location} must be an exact rational (int, Fraction, or string)")
    if isinstance(value, str) and not value.strip():
        raise PacketError(f"{location} must be a nonempty rational string")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError, TypeError, OverflowError) as exc:
        raise PacketError(f"{location} is not a finite rational") from exc


def _sequence(value: object, location: str) -> Sequence[object]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, (list, tuple)):
        raise PacketError(f"{location} must be a list or tuple")
    return value


def _vector(value: object, location: str) -> tuple[Fraction, ...]:
    return tuple(_rational(x, f"{location}[{i}]") for i, x in enumerate(_sequence(value, location)))


def _matrix(value: object, location: str) -> tuple[tuple[Fraction, ...], ...]:
    rows = tuple(_vector(row, f"{location}[{i}]") for i, row in enumerate(_sequence(value, location)))
    if rows and any(len(row) != len(rows[0]) for row in rows):
        raise PacketError(f"{location} must be rectangular")
    return rows


def check_cochain_packet(d0: object, d1: object, c1: object) -> CochainPacket:
    """Check exact packet shape and ``d1 * d0 == 0`` without a functional.

    ``d0`` has shape ``dim(C1) x dim(C0)``, ``d1`` has shape
    ``dim(C2) x dim(C1)``, and ``c1`` has length ``dim(C1)``. ``C1`` must
    have positive dimension so the width of ``d0`` is unambiguous; ``C0``
    and ``C2`` may have dimension zero. A failed cochain identity or shape
    check raises :class:`PacketError`.
    """

    a = _matrix(d0, "d0")
    b = _matrix(d1, "d1")
    v = _vector(c1, "c1")
    m = len(a)
    if m == 0:
        raise PacketError("d0 must have at least one row (positive dim(C1))")
    n = len(a[0])
    if len(v) != m:
        raise PacketError(f"c1 has length {len(v)}; expected {m}")
    if any(len(row) != m for row in b):
        raise PacketError(f"each d1 row must have length {m}")

    for i, row in enumerate(b):
        for j in range(n):
            if sum((row[k] * a[k][j] for k in range(m)), Fraction(0)) != 0:
                raise PacketError(f"cochain identity fails: (d1*d0)[{i},{j}] != 0")

    return CochainPacket(a, b, v)


def check_alpha_witness(packet: CochainPacket, alpha: object) -> tuple[Fraction, ...]:
    """Replay only the explicitly supplied equation ``d0 * alpha == c1``."""

    candidate = _vector(alpha, "alpha")
    width = len(packet.d0[0])
    if len(candidate) != width:
        raise PacketError("alpha dimension mismatch")
    for row, target in zip(packet.d0, packet.c1):
        if sum((a * x for a, x in zip(row, candidate)), Fraction(0)) != target:
            raise PacketError("d0*alpha != c1")
    return candidate


def check_left_null_witness(packet: CochainPacket, witness: object) -> tuple[Fraction, ...]:
    """Replay a supplied separating row; do not search for one."""

    candidate = _vector(witness, "obstruction")
    if len(candidate) != len(packet.c1):
        raise PacketError("obstruction dimension mismatch")
    for column in range(len(packet.d0[0])):
        if sum((candidate[i] * packet.d0[i][column]
                for i in range(len(candidate))), Fraction(0)) != 0:
            raise PacketError("obstruction is not left-null")
    if sum((a * b for a, b in zip(candidate, packet.c1)), Fraction(0)) != 1:
        raise PacketError("obstruction does not separate c1")
    return candidate


def check_zero_defect(d0: object, d1: object, c1: object) -> None:
    """Retired solver entry point: refuse until a Rust adapter is connected."""

    check_cochain_packet(d0, d1, c1)
    raise FunctionalAdapterUnavailable(
        "Phi1 calculation requires omega_functional Rust adapter"
    )
