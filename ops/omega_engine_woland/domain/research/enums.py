"""Domain enumerations and types for Woland research repair workflows.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

SCHEMA_VERSION = "urn:omega:paper_run_graph:v0.1"
AUTHORITY_EFFECT = "None"


class Role(StrEnum):
    PROPOSER = "proposer"
    EVALUATOR = "evaluator"
    WITNESS = "witness"
    AUTHORIZER = "authorizer"


class ClaimKind(StrEnum):
    DEFINITION = "definition"
    THEOREM = "theorem"
    MECHANIZATION = "mechanization"
    COMPUTATIONAL = "computational"
    EMPIRICAL = "empirical"
    LITERATURE = "literature"
    RELEASE = "release"
    SCOPE_FENCE = "scope_fence"
    UNKNOWN = "unknown"


class ObligationKind(StrEnum):
    PROSE_CONSISTENCY = "prose_consistency"
    PROSE_PROOF = "prose_proof"
    COUNTERMODEL = "countermodel"
    LEAN_KERNEL = "lean_kernel"
    PROSE_LEAN_BINDING = "prose_lean_binding"
    CODE_TEST = "code_test"
    MUTATION = "mutation"
    REPLAY = "replay"
    CITATION = "citation"
    PACKAGE_BUILD = "package_build"
    HASH_AUDIT = "hash_audit"
    NONCLAIM_FENCE = "nonclaim_fence"


class ObligationDisposition(StrEnum):
    UNCHECKED = "unchecked"
    DISCHARGED = "discharged"
    RESIDUAL = "residual"
    REFUSED = "refused"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    HUMAN_DECISION_REQUIRED = "human_decision_required"


RoleType = Role | str
ClaimKindType = ClaimKind | str
ObligationKindType = ObligationKind | str
ObligationDispositionType = ObligationDisposition | str
ClaimCeilingType = (
    Literal[
        "DECLARED",
        "CONJECTURE",
        "PROVEN_PROSE_UNDER_ASSUMPTIONS",
        "MECHANIZED_CORE_ONLY",
        "SCOPE_FENCE",
        "UNKNOWN",
    ]
    | str
)

CLAIM_CEILINGS = frozenset(
    {
        "DECLARED",
        "CONJECTURE",
        "PROVEN_PROSE_UNDER_ASSUMPTIONS",
        "MECHANIZED_CORE_ONLY",
        "SCOPE_FENCE",
        "UNKNOWN",
    }
)

__all__ = [
    "AUTHORITY_EFFECT",
    "CLAIM_CEILINGS",
    "ClaimCeilingType",
    "ClaimKind",
    "ClaimKindType",
    "ObligationDisposition",
    "ObligationDispositionType",
    "ObligationKind",
    "ObligationKindType",
    "Role",
    "RoleType",
    "SCHEMA_VERSION",
]
