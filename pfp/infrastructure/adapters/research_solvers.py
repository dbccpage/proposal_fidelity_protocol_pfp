"""Adapter exposing research solvers and problem builders for Symbol Game.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from pfp.domain.entities.problem import (
    RuntimeProblem,
    SolverManifest,
    SolverProposal,
)
from pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from pfp.domain.entities.projection_receipt import ProjectionReceipt
from pfp.domain.entities.airy import (
    AiryCriticalCarrierV1,
    AiryCriticalStateV1,
    ComplexScalarV1,
)
from pfp.domain.entities.airy_projector import (
    AiryCriticalProjector,
    AIRY_CARRIER_ID,
    AIRY_OBSTRUCTION_ID,
    AIRY_PACKET_FAMILY,
    AIRY_SOLVER_ID,
)
from pfp.domain.entities.cochain import (
    CochainCarrier,
    CochainState,
)
from pfp.domain.entities.cochain_projector import CochainProjector
from pfp.use_cases.problem_builders.airy_problem import build_airy_problem
from pfp.use_cases.problem_builders.coda_problem import build_coda_problem


def _bounded_newton(
    lam: complex,
    seed: complex,
    *,
    maximum_iterations: int,
    convergence_threshold: float,
) -> tuple[complex, int, bool, float]:
    value = seed
    for iteration in range(maximum_iterations + 1):
        try:
            gradient = lam * (value * value - 1.0)
            residual = abs(gradient)
        except OverflowError:
            return value, iteration, False, math.inf
        if not math.isfinite(residual):
            return value, iteration, False, residual
        if residual <= convergence_threshold:
            root = 1.0 + 0.0j if abs(value - 1.0) <= abs(value + 1.0) else -1.0 + 0.0j
            return root, iteration, True, residual
        if iteration == maximum_iterations:
            return value, iteration, False, residual
        derivative = 2.0 * lam * value
        derivative_magnitude = abs(derivative)
        if not math.isfinite(derivative_magnitude) or derivative_magnitude == 0.0:
            return value, iteration, False, residual
        value -= gradient / derivative
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            return value, iteration + 1, False, math.inf
    raise AssertionError("bounded Newton loop escaped its declared iteration fence")


@dataclass(frozen=True, slots=True)
class AiryNewtonProposalSolver:
    maximum_iterations: int = 64
    convergence_threshold_hex: str = (1.0e-14).hex()
    manifest: SolverManifest = SolverManifest(
        solver_id=AIRY_SOLVER_ID,
        families=(AIRY_PACKET_FAMILY,),
    )

    def __post_init__(self) -> None:
        if type(self.maximum_iterations) is not int or self.maximum_iterations < 1:
            raise ValueError("Airy Newton iteration fence must be positive")
        if type(self.convergence_threshold_hex) is not str:
            raise TypeError("Airy Newton threshold must be a float-hex string")
        try:
            threshold = float.fromhex(self.convergence_threshold_hex)
        except (ValueError, OverflowError) as exc:
            raise ValueError("Airy Newton threshold is not float-hex") from exc
        if (
            not math.isfinite(threshold)
            or threshold <= 0.0
            or threshold.hex() != self.convergence_threshold_hex
        ):
            raise ValueError("Airy Newton threshold must be finite and normalized")

    @property
    def convergence_threshold(self) -> float:
        return float.fromhex(self.convergence_threshold_hex)

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None:
        if type(problem.projector) is not AiryCriticalProjector:
            return None
        if type(packet_state) is not AiryCriticalStateV1 or projection.is_exact:
            return None

        projector = problem.projector
        try:
            state = projector.meaning(packet_state)
        except (TypeError, ValueError):
            return None
        lam = projector.carrier.lambda_scalar.to_complex()
        solved_values: list[complex] = []
        slot_receipts: list[dict[str, Any]] = []
        for slot, seed in zip(state.slots, state.complex_values()):
            root, iterations, converged, residual = _bounded_newton(
                lam,
                seed,
                maximum_iterations=self.maximum_iterations,
                convergence_threshold=self.convergence_threshold,
            )
            slot_receipts.append(
                {
                    "slot_id": slot.slot_id,
                    "iterations": iterations,
                    "converged": converged,
                    "residual_before_snap_hex": (
                        residual.hex() if math.isfinite(residual) else "non-finite"
                    ),
                }
            )
            if not converged:
                return None
            solved_values.append(root)

        candidate_state = AiryCriticalStateV1.from_complex_values(
            projector.carrier.slot_ids,
            tuple(solved_values),
        )
        root_counts: dict[ComplexScalarV1, int] = {}
        for root in (slot.value for slot in candidate_state.slots):
            root_counts[root] = root_counts.get(root, 0) + 1
        unique_root_summary = tuple(
            {
                "root": root,
                "multiplicity": root_counts[root],
            }
            for root in sorted(
                root_counts,
                key=lambda item: (item.real_hex, item.imag_hex),
            )
        )
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=candidate_state,
            witness="bounded-Newton-output-requires-independent-Airy-reprojection",
            claimed_terminal="Exact",
            claimed_valid=True,
            metadata={
                "algorithm": "bounded-complex-newton-per-labeled-slot-v1",
                "maximum_iterations": self.maximum_iterations,
                "convergence_threshold_hex": self.convergence_threshold_hex,
                "all_slots_converged": True,
                "slot_receipts": tuple(slot_receipts),
                "unique_root_count": len(unique_root_summary),
                "unique_root_summary": unique_root_summary,
                "duplicates_preserved_as_labeled_slots": True,
                "authority_effect": "None",
            },
        )
        return SolverProposal(
            state=candidate_state,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


@dataclass(frozen=True, slots=True)
class CodaCascadeProposalSolver:
    manifest: SolverManifest = SolverManifest(
        solver_id="existing-coda-cascade-proposal",
        families=("cochain_obstruction",),
    )

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None:
        if not isinstance(problem.projector, CochainProjector):
            return None
        if not isinstance(packet_state, CochainState):
            return None
        # Retract to zero residual state on carrier edges
        candidate_state = CochainState.from_mapping(
            {edge: 0.0 for edge in packet_state.as_mapping()}
        )
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=candidate_state,
            witness="coda-cascade-exact-retraction",
            claimed_terminal="Exact",
            claimed_valid=True,
            metadata={
                "authority_effect": "None",
            },
        )
        return SolverProposal(
            state=candidate_state,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


__all__ = [
    "AIRY_CARRIER_ID",
    "AIRY_OBSTRUCTION_ID",
    "AIRY_PACKET_FAMILY",
    "AIRY_SOLVER_ID",
    "AiryCriticalCarrierV1",
    "AiryCriticalStateV1",
    "AiryNewtonProposalSolver",
    "ComplexScalarV1",
    "build_airy_problem",
    "CochainCarrier",
    "CochainState",
    "CochainProjector",
    "CodaCascadeProposalSolver",
    "build_coda_problem",
]
