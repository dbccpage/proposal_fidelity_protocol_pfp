"""Domain entities for projection receipts, obstructions, and solver manifests.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest
from omega_engine_pfp.functional_boundary import require_rust_functional

if TYPE_CHECKING:
    from omega_engine_pfp.domain.entities.candidate_artifact import CandidateArtifactV1


class TerminalStatus(str, Enum):
    LAB_EXACT_CANDIDATE = "LabExactCandidate"
    LAB_CLOSED_RESIDUAL_CANDIDATE = "LabClosedResidualCandidate"
    LAB_ACTIVE_CLOSURE_FAILURE_CANDIDATE = "LabActiveClosureFailureCandidate"
    DETECTOR_INADEQUATE = "DetectorInadequate"
    ADAPTER_FAILURE = "AdapterFailure"
    BUDGET_EXHAUSTED = "BudgetExhausted"
    UNAUTHORIZED_CONTINUATION = "UnauthorizedContinuation"
    STUCK_CORPUS = "StuckCorpus"
    INVALID_PACKET = "InvalidPacket"


@dataclass(frozen=True, slots=True)
class Obstruction:
    obstruction_id: str
    magnitude: float
    witness: str
    closure_failure: bool = False

    def __post_init__(self) -> None:
        if not self.obstruction_id or not self.witness:
            raise ValueError("obstructions require an id and witness")
        if not math.isfinite(self.magnitude) or self.magnitude <= 0.0:
            raise ValueError("active obstruction magnitude must be finite and positive")


@dataclass(frozen=True, slots=True)
class ProjectionReceipt:
    projector_id: str
    state_hash: str
    obstructions: tuple[Obstruction, ...]
    witness: str
    representative_l1_mass: float | None = None
    authority_effect: str = field(default="None")

    def __post_init__(self) -> None:
        mass = self.representative_l1_mass
        if mass is None:
            return
        if type(mass) not in {int, float}:
            raise TypeError("representative L1 mass must be numeric when declared")
        normalized = float(mass)
        if not math.isfinite(normalized) or normalized < 0.0:
            raise ValueError("representative L1 mass must be finite and nonnegative")
        object.__setattr__(self, "representative_l1_mass", normalized)

    @property
    def raw_mass(self) -> float | None:
        return self.representative_l1_mass

    @property
    def nonclosure_obstruction_mass(self) -> float:
        return float(
            sum(
                item.magnitude for item in self.obstructions if not item.closure_failure
            )
        )

    @property
    def closure_obstruction_mass(self) -> float:
        return float(
            sum(item.magnitude for item in self.obstructions if item.closure_failure)
        )

    @property
    def phi1(self) -> float:
        require_rust_functional("ProjectionReceipt.phi1")

    @property
    def gamma2(self) -> float:
        require_rust_functional("ProjectionReceipt.gamma2")

    @property
    def obstruction_mass(self) -> float:
        return self.nonclosure_obstruction_mass + self.closure_obstruction_mass

    @property
    def active_ids(self) -> tuple[str, ...]:
        return tuple(sorted(item.obstruction_id for item in self.obstructions))

    @property
    def is_exact(self) -> bool:
        return not self.obstructions

    @property
    def measure(self) -> tuple[float, float, int]:
        return (
            self.closure_obstruction_mass,
            self.nonclosure_obstruction_mass,
            len(self.obstructions),
        )

    @property
    def control_digest(self) -> str:
        return domain_digest("omega.oesos.projection-control.v1", self)


@dataclass(frozen=True, slots=True)
class DetectorCase:
    case_id: str
    native_state: Any
    expected_active_ids: tuple[str, ...]
    expected_projection_digest: str


@dataclass(frozen=True, slots=True)
class SolverManifest:
    solver_id: str
    families: tuple[str, ...]
    version: str = "v1"
    deterministic: bool = True
    authority_effect: str = "None"

    def supports(self, family: str) -> bool:
        return family in self.families or "*" in self.families

    @property
    def manifest_id(self) -> str:
        return domain_digest("omega.oesos.solver-manifest.v1", self)


@dataclass(frozen=True, slots=True)
class SolverProposal:
    state: Any
    candidate: CandidateArtifactV1
    next_carrier_id: str
    candidate_declares_minimal_move: bool = True
    candidate_loss_claims: tuple[str, ...] = ()


__all__ = [
    "DetectorCase",
    "Obstruction",
    "ProjectionReceipt",
    "SolverManifest",
    "SolverProposal",
    "TerminalStatus",
]
