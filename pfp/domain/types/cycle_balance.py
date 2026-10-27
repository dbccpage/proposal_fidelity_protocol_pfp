"""PFP Cycle Balance Quartet: Carrier, Cell Bounds, Matrices, Problem, Candidate, Verifier, Receipt.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field, model_validator

from .base import AuthorityEffect, PfpBaseModel, object_digest
from .prompt_templates import PfpClaimHygiene


class PfpArithmeticDomain(str, Enum):
    EXACT_INTEGER = "EXACT_INTEGER"


class PfpClaimedMove(str, Enum):
    ATTACH_2CELL = "ATTACH_2CELL"


class PfpVerificationRule(str, Enum):
    STATIC_CELL_BOUNDS_CHECK = "STATIC_CELL_BOUNDS_CHECK"
    CHAIN_COMPLEX_NILPOTENCY_CHECK = "CHAIN_COMPLEX_NILPOTENCY_CHECK"
    INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE = "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE"


class PfpVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class PfpStaticCellBounds(PfpBaseModel):
    max_vertices: int = Field(ge=0)
    max_edges: int = Field(ge=0)
    max_faces: int = Field(ge=0)


class PfpEdge(PfpBaseModel):
    id: str = Field(min_length=1)
    source: int
    target: int


class PfpFace(PfpBaseModel):
    id: str = Field(min_length=1)
    boundary_edges: list[str] = Field(default_factory=list)


class PfpCarrier(PfpBaseModel):
    name: str = Field(min_length=1)
    vertices: list[int] = Field(default_factory=list)
    edges: list[PfpEdge] = Field(default_factory=list)
    faces: list[PfpFace] = Field(default_factory=list)
    static_cell_bounds: PfpStaticCellBounds

    @model_validator(mode="after")
    def _validate_carrier(self) -> PfpCarrier:
        b = self.static_cell_bounds
        if len(self.vertices) > b.max_vertices:
            raise ValueError("vertex count exceeds static_cell_bounds.max_vertices")
        if len(self.edges) > b.max_edges:
            raise ValueError("edge count exceeds static_cell_bounds.max_edges")
        if len(self.faces) > b.max_faces:
            raise ValueError("face count exceeds static_cell_bounds.max_faces")
        return self


class PfpBoundaryMatrices(PfpBaseModel):
    d1: list[list[int]] = Field(default_factory=list)
    d2: list[list[int]] = Field(default_factory=list)


class PfpActiveObstruction(PfpBaseModel):
    cycle_z: list[int] = Field(default_factory=list)
    cycle_edges: list[str] = Field(default_factory=list)
    d1_z: list[int] = Field(default_factory=list)
    homology_status: PfpVerificationStatus


class PfpCycleBalanceProblem(PfpBaseModel):
    schema_version: Literal["core.symbol_game.cycle_balance.problem.v1"] = "core.symbol_game.cycle_balance.problem.v1"
    problem_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    carrier: PfpCarrier
    boundary_matrices: PfpBoundaryMatrices
    active_obstruction: PfpActiveObstruction


class PfpCycleBalanceCandidate(PfpBaseModel):
    schema_version: Literal["core.symbol_game.cycle_balance.candidate.v1"] = "core.symbol_game.cycle_balance.candidate.v1"
    candidate_id: str = Field(min_length=1)
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    claimed_move: PfpClaimedMove = PfpClaimedMove.ATTACH_2CELL
    repair_face_name: str = Field(min_length=1)
    constituent_edges: list[str] = Field(default_factory=list)
    repair_boundary_column: list[int] = Field(default_factory=list)
    preserves_chain_law: bool
    claimed_integer_preimage_c: list[int] = Field(default_factory=list)
    claimed_h1_status: str = Field(min_length=1)


class PfpCycleBalanceVerifier(PfpBaseModel):
    schema_version: Literal["core.symbol_game.cycle_balance.verifier.v1"] = "core.symbol_game.cycle_balance.verifier.v1"
    verifier_id: str = Field(min_length=1)
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verification_rules: list[PfpVerificationRule] = Field(min_length=1)
    static_bounds: PfpStaticCellBounds


class PfpCycleBalanceReceipt(PfpBaseModel):
    schema_version: Literal["core.symbol_game.cycle_balance.receipt.v1"] = "core.symbol_game.cycle_balance.receipt.v1"
    receipt_id: str = Field(min_length=1)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verification_status: PfpVerificationStatus
    terminal_status: str | None = None
    residuals: Any | None = None
    exact_witness: Any | None = None
    claim_hygiene: PfpClaimHygiene
    receipt_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class PfpCycleBalanceQuartet(PfpBaseModel):
    problem: PfpCycleBalanceProblem
    candidate: PfpCycleBalanceCandidate
    verifier: PfpCycleBalanceVerifier
    receipt: PfpCycleBalanceReceipt

    def check_digest_bindings(self, raw: dict[str, dict[str, Any]]) -> bool:
        pd = object_digest(raw["problem"])
        cd = object_digest(raw["candidate"])
        vd = object_digest(raw["verifier"])
        receipt_raw = dict(raw["receipt"])
        receipt_raw["receipt_digest"] = ""
        return (
            self.candidate.problem_digest == pd
            and self.verifier.problem_digest == pd
            and self.receipt.problem_digest == pd
            and self.receipt.candidate_digest == cd
            and self.receipt.verifier_digest == vd
            and self.receipt.receipt_digest == object_digest(receipt_raw)
        )


# Aliases
ArithmeticDomain = PfpArithmeticDomain
ClaimedMove = PfpClaimedMove
VerificationRule = PfpVerificationRule
VerificationStatus = PfpVerificationStatus
StaticCellBounds = PfpStaticCellBounds
Edge = PfpEdge
Face = PfpFace
Carrier = PfpCarrier
BoundaryMatrices = PfpBoundaryMatrices
ActiveObstruction = PfpActiveObstruction
CycleBalanceProblem = PfpCycleBalanceProblem
CycleBalanceCandidate = PfpCycleBalanceCandidate
CycleBalanceVerifier = PfpCycleBalanceVerifier
CycleBalanceReceipt = PfpCycleBalanceReceipt
CycleBalanceQuartet = PfpCycleBalanceQuartet
