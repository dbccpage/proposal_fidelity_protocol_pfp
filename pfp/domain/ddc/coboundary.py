"""Coboundary operators d^0 and d^1 with exact nilpotency verification.

Implements the graded coboundary sequence:
    C^0(K; Q) --d^0--> C^1(K; Q) --d^1--> C^2(K; Q)

Operators:
- d^0: C^0 -> C^1, (d^0 f)(u, v) = f(v) - f(u)
- d^1: C^1 -> C^2, (d^1 h)(u, v, w) = h(v, w) - h(u, w) + h(u, v)

Nilpotency Property:
    d^1 o d^0 = 0
Verified algebraically and mechanically over Q with exact Fraction arithmetic.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Tuple

from .cochains import Cochain0, Cochain1, Cochain2
from .complex import SimplicialComplex


@dataclass(frozen=True)
class NilpotencyReceipt:
    """Tamper-evident verification receipt for d^1 o d^0 = 0."""

    is_nilpotent: bool
    num_faces_evaluated: int
    max_absolute_defect: Fraction
    details: str
    authority_effect: str = "None"


def d0(complex_: SimplicialComplex, f: Cochain0) -> Cochain1:
    """Compute 0-coboundary d^0: C^0 -> C^1.

    (d^0 f)(u, v) = f(v) - f(u) for each edge (u, v) in K.
    """
    values: Dict[Tuple[str, str], Fraction] = {}
    for edge in complex_.edges:
        f_u = f.get(edge.u)
        f_v = f.get(edge.v)
        values[edge.key] = f_v - f_u
    return Cochain1(values)


def _eval_edge(h: Cochain1, complex_: SimplicialComplex, u: str, v: str) -> Fraction:
    """Evaluate 1-cochain along oriented pair (u, v).

    If (u, v) is an edge, returns h(u, v).
    If (v, u) is an edge and (u, v) is not, returns -h(v, u) by 1-chain anti-symmetry.
    Otherwise returns Fraction(0).
    """
    if (u, v) in h.values:
        return h.get(u, v)
    if (v, u) in h.values:
        return -h.get(v, u)
    if complex_.has_edge(u, v):
        return h.get(u, v)
    if complex_.has_edge(v, u):
        return -h.get(v, u)
    return Fraction(0)


def d1(complex_: SimplicialComplex, h: Cochain1) -> Cochain2:
    """Compute 1-coboundary d^1: C^1 -> C^2.

    For each oriented 2-simplex (u, v, w) in K:
        (d^1 h)(u, v, w) = h(v, w) - h(u, w) + h(u, v)
    respecting edge orientation anti-symmetry where h(b, a) = -h(a, b).
    """
    values: Dict[Tuple[str, str, str], Fraction] = {}
    for face in complex_.faces:
        u, v, w = face.u, face.v, face.w
        h_vw = _eval_edge(h, complex_, v, w)
        h_uw = _eval_edge(h, complex_, u, w)
        h_uv = _eval_edge(h, complex_, u, v)
        values[face.key] = h_vw - h_uw + h_uv
    return Cochain2(values)


def verify_nilpotency(complex_: SimplicialComplex, f: Cochain0) -> NilpotencyReceipt:
    """Mechanically verify d^1(d^0(f)) == 0 for a given 0-cochain f."""
    h = d0(complex_, f)
    c = d1(complex_, h)

    max_defect = Fraction(0)
    for face in complex_.faces:
        defect = abs(c.get(face.u, face.v, face.w))
        if defect > max_defect:
            max_defect = defect

    is_nilpotent = max_defect == Fraction(0)
    details = (
        f"Verified d^1 o d^0 over {complex_.num_faces} faces. "
        f"Max defect: {max_defect} (exact rational)."
    )
    return NilpotencyReceipt(
        is_nilpotent=is_nilpotent,
        num_faces_evaluated=complex_.num_faces,
        max_absolute_defect=max_defect,
        details=details,
    )


def audit_nilpotency_all_basis(complex_: SimplicialComplex) -> NilpotencyReceipt:
    """Audit nilpotency d^1 o d^0 = 0 across all elementary vertex basis cochains.

    For every vertex v in V, tests delta_v (where delta_v(v) = 1, delta_v(u) = 0).
    Linearity then guarantees d^1 o d^0 = 0 for all f in C^0.
    """
    if complex_.num_faces == 0:
        return NilpotencyReceipt(
            is_nilpotent=True,
            num_faces_evaluated=0,
            max_absolute_defect=Fraction(0),
            details="Vacuously nilpotent (0 faces in complex).",
        )

    max_overall_defect = Fraction(0)
    for v in complex_.vertices:
        basis_f = Cochain0({v: Fraction(1)})
        receipt = verify_nilpotency(complex_, basis_f)
        if not receipt.is_nilpotent:
            return receipt
        if receipt.max_absolute_defect > max_overall_defect:
            max_overall_defect = receipt.max_absolute_defect

    return NilpotencyReceipt(
        is_nilpotent=True,
        num_faces_evaluated=complex_.num_faces * complex_.num_vertices,
        max_absolute_defect=max_overall_defect,
        details=f"All {complex_.num_vertices} basis potentials satisfy d^1 o d^0 = 0 identically.",
    )
