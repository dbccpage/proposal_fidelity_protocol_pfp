"""Payload quotient boundary and Primitive Difference / LGGR verification for PO-001.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from exact import exact_equal, exact_matrix_from_matrix
from exactsym import Matrix


@dataclass(frozen=True)
class CurvaturePacket:
    """A data packet carrying both a local payload and a global curvature defect."""

    payload: Matrix
    curvature: Matrix

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", exact_matrix_from_matrix(self.payload))
        object.__setattr__(self, "curvature", exact_matrix_from_matrix(self.curvature))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CurvaturePacket):
            return False
        return exact_equal(self.payload, other.payload) and exact_equal(self.curvature, other.curvature)


class PayloadPrimitiveDifference:
    """Primitive Difference relation comparing only local payloads: delta(x, y) = (x.payload, y.payload)."""

    @staticmethod
    def zero_rel(x: CurvaturePacket, y: CurvaturePacket) -> bool:
        """True if and only if x and y have identical local payloads."""
        return exact_equal(x.payload, y.payload)

    @staticmethod
    def observe_payload(packet: CurvaturePacket) -> Matrix:
        """Observation map extracting local payload."""
        return packet.payload

    @staticmethod
    def observe_curvature(packet: CurvaturePacket) -> Matrix:
        """Observation map extracting global curvature."""
        return packet.curvature

    @classmethod
    def payload_is_invariant_congruent(cls, packets: list[CurvaturePacket]) -> bool:
        """Verify that payload observation is invariant under payload equivalence:
        
        forall x, y in packets: zero_rel(x, y) => observe_payload(x) == observe_payload(y).
        """
        for i, x in enumerate(packets):
            for y in packets[i:]:
                if cls.zero_rel(x, y):
                    if not exact_equal(cls.observe_payload(x), cls.observe_payload(y)):
                        return False
        return True

    @classmethod
    def curvature_is_invariant_congruent(cls, packets: list[CurvaturePacket]) -> bool:
        """Check whether curvature observation is invariant under payload equivalence:
        
        forall x, y in packets: zero_rel(x, y) => observe_curvature(x) == observe_curvature(y).
        Fails if any two packets have identical payloads but differing curvatures.
        """
        for i, x in enumerate(packets):
            for y in packets[i:]:
                if cls.zero_rel(x, y):
                    if not exact_equal(cls.observe_curvature(x), cls.observe_curvature(y)):
                        return False
        return True


def certify_local_green_global_red(
    payload: Matrix,
    curvature_k: Matrix,
    curvature_l: Matrix,
) -> dict[str, Any]:
    """Certify Theorem 3.5: Local Green, Global Red (LGGR).
    
    Given a single local payload and two distinct curvature states k != l:
    1. Local payload factors through the payload-only quotient (Local Green).
    2. Curvature observation fails to factor through the quotient (Global Red).
    """
    if exact_equal(curvature_k, curvature_l):
        raise ValueError("curvature_k and curvature_l must be distinct to demonstrate LGGR")

    p1 = CurvaturePacket(payload=payload, curvature=curvature_k)
    p2 = CurvaturePacket(payload=payload, curvature=curvature_l)
    packet_pair = [p1, p2]

    # Under payload primitive difference, p1 ~ p2
    equiv = PayloadPrimitiveDifference.zero_rel(p1, p2)
    payload_ok = PayloadPrimitiveDifference.payload_is_invariant_congruent(packet_pair)
    curvature_ok = PayloadPrimitiveDifference.curvature_is_invariant_congruent(packet_pair)

    return {
        "payload_equivalent": equiv,
        "local_payload_factors": payload_ok,        # True (Green)
        "global_curvature_factors": curvature_ok,    # False (Red)
        "lggr_boundary_confirmed": payload_ok and (not curvature_ok),
        "witness": {
            "p1_curvature": curvature_k,
            "p2_curvature": curvature_l,
            "difference": curvature_k - curvature_l,
        },
    }
