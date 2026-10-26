"""Checker 2 (Independent Checker) for C019.

Self-contained: no reference-solver or checker-1 imports. It decides extension
over Q by its own exact elimination and verifies every submitted witness in both
modes with strict types (canonical rational strings or plain ints; floats and
Booleans are rejected):

- mode Q, EXTENDS: d1 A = B exactly and phi2 = 0;
- mode Q, OBSTRUCTED: the cycle satisfies d2 Z = 0 with <B, Z> equal to the
  reported nonzero pairing; the dual y satisfies d2 y = 0, |y_f| <= w_f and
  <B, y> equals the reported positive phi2;
- mode Z, EXTENDS_INTEGRAL: an integer A with d1 A = B exactly;
- mode Z, OBSTRUCTED_INTEGRAL: an integer modulus m >= 2 and an integer chain Z
  with d2 Z = 0 (mod m) and <B, Z> = pairing_mod != 0 (mod m). Such a Z proves
  that no integer A exists, since <d1 A, Z> = <A, d2 Z> = 0 (mod m).
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

_RATIONAL = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
_INTEGER = re.compile(r"-?(0|[1-9][0-9]*)")


def _q(value: Any) -> Fraction:
    if type(value) is int:
        return Fraction(value)
    if type(value) is str and _RATIONAL.fullmatch(value) and value != "-0":
        return Fraction(value)
    raise ValueError(f"not an exact rational: {value!r}")


def _z(value: Any) -> int:
    if type(value) is int:
        return value
    if type(value) is str and _INTEGER.fullmatch(value) and value != "-0":
        return int(value)
    raise ValueError(f"not an integer: {value!r}")


def _vector(raw: Any, keys: list[str], parse) -> dict[str, Any]:
    if not isinstance(raw, dict) or any(k not in keys for k in raw):
        raise ValueError("vector must be an object over the declared cells")
    return {k: parse(raw[k]) if k in raw else parse(0) for k in keys}


def _in_image(rows: list[list[Fraction]], target: list[Fraction]) -> bool:
    """Whether target lies in the column space of rows (faces x edges)."""
    width = len(rows[0]) if rows else 0
    aug = [r[:] + [t] for r, t in zip(rows, target)]
    rank = 0
    for col in range(width):
        pivot = next((i for i in range(rank, len(aug)) if aug[i][col] != 0), None)
        if pivot is None:
            continue
        aug[rank], aug[pivot] = aug[pivot], aug[rank]
        for i in range(len(aug)):
            if i != rank and aug[i][col] != 0:
                factor = aug[i][col] / aug[rank][col]
                aug[i] = [a - factor * b for a, b in zip(aug[i], aug[rank])]
        rank += 1
    return all(aug[i][width] == 0 for i in range(rank, len(aug)))


def check_independent_h2(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    faces = list(case.get("faces", []))
    edges = list(case.get("edges", []))
    vertices = list(case.get("vertices", []))
    d2 = case.get("d2", {})
    d1 = case.get("d1", {})
    mode = case.get("mode", "Q")

    try:
        bad_faces = [
            f
            for f in faces
            if any(
                sum(_z(d2.get(f, {}).get(e, 0)) * _z(d1.get(e, {}).get(v, 0)) for e in edges) != 0
                for v in vertices
            )
        ]
        coeff = [[Fraction(_z(d2.get(f, {}).get(e, 0))) for e in edges] for f in faces]
    except (AttributeError, ValueError) as exc:
        return False, f"Independent checker: malformed boundary data: {exc}"
    if bad_faces:
        witness = result.get("witness") if isinstance(result.get("witness"), dict) else {}
        if (
            status == "OUT_OF_SCOPE"
            and witness.get("reason") == "BOUNDARY_NOT_NILPOTENT"
            and witness.get("face") in bad_faces
        ):
            return True, "Independent checker confirms OUT_OF_SCOPE at the cited face"
        return False, "Expected OUT_OF_SCOPE citing a face where d1 d2 != 0"

    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"
    if result.get("mode", mode) != mode:
        return False, "Independent checker: answer mode differs from case mode"

    verdict = result.get("verdict")
    try:
        B = [_q(case.get("B", {}).get(f, 0)) for f in faces]
        weights = [_q(case.get("weights", {}).get(f, 1)) for f in faces]
    except ValueError as exc:
        return False, f"Independent checker: malformed case data: {exc}"

    def coboundary(A: dict[str, Any]) -> list[Fraction]:
        return [
            sum((coeff[i][j] * A[e] for j, e in enumerate(edges)), Fraction(0))
            for i in range(len(faces))
        ]

    def boundary(Z: dict[str, Any]) -> list[Fraction]:
        return [
            sum((coeff[i][j] * Z[f] for i, f in enumerate(faces)), Fraction(0))
            for j in range(len(edges))
        ]

    try:
        if mode == "Q":
            extends = _in_image(coeff, B)
            if verdict == "EXTENDS":
                if not extends:
                    return False, "Independent solve found an obstruction; EXTENDS is false"
                A = _vector(result.get("A"), edges, _q)
                if coboundary(A) != B:
                    return False, "Independent checker: d1 A != B"
                if _q(result.get("phi2")) != 0:
                    return False, "Independent checker: EXTENDS requires phi2 = 0"
                return True, "Independent checker confirms EXTENDS"
            if verdict == "OBSTRUCTED":
                if extends:
                    return False, "Independent solve found an extension; OBSTRUCTED is false"
                Z = _vector(result.get("cycle"), faces, _q)
                if any(boundary(Z)):
                    return False, "Independent checker: submitted cycle is not closed"
                pairing = sum((B[i] * Z[f] for i, f in enumerate(faces)), Fraction(0))
                if pairing == 0 or pairing != _q(result.get("pairing")):
                    return False, "Independent checker: pairing <B, Z> is zero or misreported"
                y = _vector(result.get("dual_y"), faces, _q)
                if any(boundary(y)) or any(abs(y[f]) > weights[i] for i, f in enumerate(faces)):
                    return False, "Independent checker: dual y is not a feasible closed chain"
                phi2 = sum((B[i] * y[f] for i, f in enumerate(faces)), Fraction(0))
                if phi2 <= 0 or phi2 != _q(result.get("phi2")):
                    return False, "Independent checker: phi2 is not attained by the dual"
                return True, "Independent checker confirms OBSTRUCTED"
            return False, f"Unknown mode Q verdict: {verdict}"

        if mode == "Z":
            if any(b.denominator != 1 for b in B):
                return False, "Independent checker: mode Z case has a non-integral target"
            if verdict == "EXTENDS_INTEGRAL":
                A = _vector(result.get("A"), edges, _z)
                if coboundary(A) != B:
                    return False, "Independent checker: integer A does not satisfy d1 A = B"
                return True, "Independent checker confirms EXTENDS_INTEGRAL"
            if verdict == "OBSTRUCTED_INTEGRAL":
                m = _z(result.get("modulus"))
                if m < 2:
                    return False, "Independent checker: modulus must be >= 2"
                Z = _vector(result.get("chain"), faces, _z)
                if any(int(x) % m for x in boundary(Z)):
                    return False, f"Independent checker: chain is not closed mod {m}"
                pairing = int(sum((B[i] * Z[f] for i, f in enumerate(faces)), Fraction(0))) % m
                claimed = _z(result.get("pairing_mod"))
                if pairing == 0 or claimed % m != pairing:
                    return False, f"Independent checker: <B, Z> mod {m} is zero or misreported"
                return True, "Independent checker confirms OBSTRUCTED_INTEGRAL"
            return False, f"Unknown mode Z verdict: {verdict}"
    except ValueError as exc:
        return False, f"Independent checker: {exc}"

    return False, f"Unknown mode {mode!r}"
