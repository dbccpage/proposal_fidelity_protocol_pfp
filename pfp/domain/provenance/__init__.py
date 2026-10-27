"""Provenance gates for the Proposal Fidelity Protocol.

AuthorityEffect: None.

The three-role gate checks the shape of a provenance packet
``(proposer, evaluator, authorizer)`` against a declared role policy. It
never mints promotion: an admitted packet only says the authorizer may act.
"""

from __future__ import annotations

from pfp.domain.provenance.three_role_gate import (
    AUTHORITY_EFFECT,
    GateVerdict,
    ObserverDeclaration,
    PacketShapeError,
    ProvenancePacket,
    RefusalReason,
    Role,
    RoleBinding,
    RolePolicy,
    ThreeRoleGate,
    VerdictCode,
)

__all__ = [
    "AUTHORITY_EFFECT",
    "GateVerdict",
    "ObserverDeclaration",
    "PacketShapeError",
    "ProvenancePacket",
    "RefusalReason",
    "Role",
    "RoleBinding",
    "RolePolicy",
    "ThreeRoleGate",
    "VerdictCode",
]
