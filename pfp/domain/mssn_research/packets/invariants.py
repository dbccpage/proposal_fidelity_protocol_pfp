"""Domain Invariants for the Packets Bounded Context.

Codifies the 8 canonical invariants governing packet validity and stage admission.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result
from pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel

from .errors import (
    MalformedWireError,
    PacketDomainError,
    StageFloorViolationError,
)
from .value_objects import Opcode, RefusalCode


def check_delimiter_balance(raw: str) -> Result[bool, PacketDomainError]:
    """Invariant 1: Delimiters < and > must strictly match with zero unclosed scopes."""
    depth = 0
    for char in raw:
        depth += (char == "<") - (char == ">")
        if depth < 0:
            return Err(MalformedWireError(
                code=RefusalCode.MALFORMED_PACKET,
                message="Negative delimiter depth",
            ))
    if depth != 0:
        return Err(MalformedWireError(code=RefusalCode.MALFORMED_PACKET, message="Unclosed delimiter in wire"))
    return Ok(True)


def check_opcode_stage_floor(opcode: Opcode, current_stage: StageLevel) -> Result[bool, PacketDomainError]:
    """Invariant 2: Opcode cannot be used below its admitted stage floor."""
    if not opcode.is_registered:
        return Refusal(StageFloorViolationError(
            code=RefusalCode.UNKNOWN_OPCODE,
            message=f"Opcode <{opcode.binary_str}> is unregistered",
        ))
    if current_stage < opcode.stage_floor:
        return Refusal(StageFloorViolationError(
            code=RefusalCode.UNKNOWN_OPCODE,
            message=f"Opcode {opcode} requires stage {opcode.stage_floor.level}, current is {current_stage.level}",
        ))
    return Ok(True)


def check_simplex_distinctness(vertices: Sequence[str]) -> Result[bool, PacketDomainError]:
    """Invariant 3: Vertex identifiers in an abstract simplex must be mutually distinct."""
    if len(vertices) != len(set(vertices)):
        return Refusal(MalformedWireError(
            code=RefusalCode.MALFORMED_PACKET,
            message="Degenerate simplex: repeated vertex identifier"
        ))
    return Ok(True)


def check_gram_matrix_positive_definiteness(
    vertices: Sequence[str],
    lengths: dict[frozenset[str], int]
) -> Result[bool, PacketDomainError]:
    """Invariant 4 (Sylvester's Criterion): Leading principal minors of Gram matrix must be > 0.

    Precondition: Simplex vertices must be mutually distinct.
    """
    distinct_res = check_simplex_distinctness(vertices)
    if distinct_res.is_err():
        return distinct_res

    n = len(vertices) - 1
    if n <= 0:
        return Ok(True)
    root = vertices[0]
    tail = vertices[1:]

    # Construct rational Gram matrix G_ij = (d_0i^2 + d_0j^2 - d_ij^2)/2
    gram: list[list[Fraction]] = []
    for u in tail:
        row: list[Fraction] = []
        for v in tail:
            d0u_sq = lengths.get(frozenset((root, u)), 0)
            d0v_sq = lengths.get(frozenset((root, v)), 0)
            duv_sq = 0 if u == v else lengths.get(frozenset((u, v)), 0)
            g_ij = Fraction(d0u_sq + d0v_sq - duv_sq, 2)
            row.append(g_ij)
        gram.append(row)

    # Gaussian elimination determinant check on each leading k x k minor
    for k in range(1, n + 1):
        minor = [row[:k] for row in gram[:k]]
        det_val = _exact_det(minor)
        if det_val <= 0:
            return Refusal(MalformedWireError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=f"Gram matrix leading minor of order {k} is non-positive ({det_val}); non-Euclidean simplex"
            ))
    return Ok(True)


def _exact_det(matrix: list[list[Fraction]]) -> Fraction:
    a = [row[:] for row in matrix]
    out = Fraction(1)
    for j in range(len(a)):
        pivot = next((k for k in range(j, len(a)) if a[k][j]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != j:
            a[j], a[pivot] = a[pivot], a[j]
            out = -out
        val = a[j][j]
        out *= val
        for k in range(j + 1, len(a)):
            factor = a[k][j] / val
            for column in range(j, len(a)):
                a[k][column] -= factor * a[j][column]
    return out


def check_refusal_code_bounds(code_val: int) -> Result[bool, PacketDomainError]:
    """Invariant 5: Refusal error code must fall within canonical registry 0..8."""
    if code_val not in range(9):
        return Err(MalformedWireError(
            code=RefusalCode.UNKNOWN_OPCODE,
            message=f"Unknown refusal error code {code_val}; registered codes are 0..8"
        ))
    return Ok(True)
