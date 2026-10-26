"""Small finite CSP carrier used as a complete packet/solver vertical slice."""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from omega_engine_pfp.domain.entities.projection_receipt import (
    Obstruction,
    ProjectionReceipt,
    DetectorCase,
    SolverManifest,
    SolverProposal,
)
from omega_engine_pfp.domain.entities.problem import (
    IdentityAdapter,
    RuntimeProblem,
)
from omega_engine_pfp.domain.shared_kernel.canonical import canonical_json, domain_digest, freeze
from omega_engine_pfp.domain import CandidateArtifactV1, PacketEnvelopeV2


State = tuple[tuple[str, int], ...]


def normalize_state(state: Any) -> State:
    if isinstance(state, dict):
        pairs = state.items()
    else:
        pairs = state
    normalized = tuple(sorted((str(name), int(value)) for name, value in pairs))
    if len({name for name, _ in normalized}) != len(normalized):
        raise ValueError("state has duplicate variable names")
    return normalized


@dataclass(frozen=True, slots=True)
class FiniteConstraint:
    constraint_id: str
    coefficients: tuple[tuple[str, int], ...]
    rhs: int
    closure_failure: bool = False

    def violation(self, state: State) -> float:
        values = dict(normalize_state(state))
        total = sum(
            coefficient * values[name] for name, coefficient in self.coefficients
        )
        return float(abs(total - self.rhs))


@dataclass(frozen=True, slots=True)
class FiniteCspProjector:
    domains: tuple[tuple[str, tuple[int, ...]], ...]
    constraints: tuple[FiniteConstraint, ...]
    projector_id: str = "finite-csp-projector-v1"

    @property
    def config_digest(self) -> str:
        return domain_digest(
            "omega.oesos.projector-config.v1",
            {
                "projector_id": self.projector_id,
                "domains": self.domains,
                "constraints": self.constraints,
            },
        )

    def meaning(self, state: Any) -> Any:
        return normalize_state(state)

    def skeleton(self, state: Any) -> Any:
        normalized = normalize_state(state)
        return {
            "variables": tuple(name for name, _ in normalized),
            "domains": self.domains,
            "constraints": tuple(
                (item.constraint_id, item.coefficients, item.rhs, item.closure_failure)
                for item in self.constraints
            ),
        }

    def validate_packet(
        self,
        envelope: PacketEnvelopeV2,
        native_initial_state: Any,
    ) -> bool:
        normalized_initial = normalize_state(native_initial_state)
        expected_payload = {
            "domains": self.domains,
            "constraints": tuple(
                {
                    "constraint_id": item.constraint_id,
                    "coefficients": item.coefficients,
                    "rhs": item.rhs,
                    "closure_failure": item.closure_failure,
                }
                for item in self.constraints
            ),
            "initial_state": normalized_initial,
        }
        return (
            envelope.carrier_id == "finite-csp-v1"
            and envelope.constraints
            == tuple(item.constraint_id for item in self.constraints)
            and envelope.payload == freeze(expected_payload)
            and envelope.source_digest
            == domain_digest("omega.oesos.fixture-source.v1", expected_payload)
        )

    def project(self, state: Any) -> ProjectionReceipt:
        normalized = normalize_state(state)
        domain_map = dict(self.domains)
        state_map = dict(normalized)
        if set(state_map) != set(domain_map):
            raise ValueError("state variables do not match the carrier")
        for name, value in normalized:
            if value not in domain_map[name]:
                raise ValueError(f"{name}={value} lies outside its declared domain")
        obstructions = []
        for constraint in self.constraints:
            magnitude = constraint.violation(normalized)
            if magnitude > 0.0:
                obstructions.append(
                    Obstruction(
                        obstruction_id=constraint.constraint_id,
                        magnitude=magnitude,
                        witness=f"{constraint.constraint_id}:linear-residual={magnitude:g}",
                        closure_failure=constraint.closure_failure,
                    )
                )
        return ProjectionReceipt(
            projector_id=self.projector_id,
            state_hash=domain_digest("omega.oesos.state.v1", self.meaning(normalized)),
            obstructions=tuple(obstructions),
            witness="finite-csp-independent-replay-v1",
        )

    def enumerate_states(self) -> Iterable[State]:
        names = tuple(name for name, _ in self.domains)
        domains = tuple(values for _, values in self.domains)
        for values in itertools.product(*domains):
            yield tuple(zip(names, values))

    def best_state(self) -> State:
        return min(
            self.enumerate_states(),
            key=lambda state: (self.project(state).measure, canonical_json(state)),
        )

    def verify_retraction(
        self,
        solver_id: str,
        before_state: Any,
        after_state: Any,
    ) -> bool:
        """Replay a declared finite retraction independently of its producer."""

        before = dict(normalize_state(before_state))
        after = dict(normalize_state(after_state))
        if solver_id == "finite-exhaustive-retraction":
            return normalize_state(after_state) == self.best_state()
        for variable, domain in self.domains:
            for target in domain:
                if solver_id != f"set-{variable}-{target}":
                    continue
                expected = dict(before)
                expected[variable] = target
                return after == expected and after != before
        return False


@dataclass(frozen=True, slots=True)
class NoOpClaimingSolver:
    manifest: SolverManifest = SolverManifest(
        solver_id="candidate-claim-only",
        families=("finite_csp",),
    )

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal:
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=packet_state,
            witness="candidate-authored-claim-without-descent",
            claimed_terminal="Exact",
            claimed_valid=True,
        )
        return SolverProposal(
            state=packet_state,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


@dataclass(frozen=True, slots=True)
class ExhaustiveCspSolver:
    manifest: SolverManifest = SolverManifest(
        solver_id="finite-exhaustive-retraction",
        families=("finite_csp",),
    )

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None:
        if not isinstance(problem.projector, FiniteCspProjector):
            return None
        best = problem.projector.best_state()
        if problem.projector.project(best).measure >= projection.measure:
            return None
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=best,
            witness="complete-finite-enumeration-with-independent-reprojection",
            claimed_terminal="Exact",
            metadata={
                "enumerated_states": len(tuple(problem.projector.enumerate_states()))
            },
        )
        return SolverProposal(
            state=best,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


@dataclass(frozen=True, slots=True)
class NamedVariableRetraction:
    variable: str
    target: int

    @property
    def manifest(self) -> SolverManifest:
        return SolverManifest(
            solver_id=f"set-{self.variable}-{self.target}",
            families=("finite_csp",),
        )

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None:
        state = dict(normalize_state(packet_state))
        if state.get(self.variable) == self.target:
            return None
        state[self.variable] = self.target
        candidate_state = normalize_state(state)
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=candidate_state,
            witness=f"canonical-retraction:{self.variable}->{self.target}",
        )
        return SolverProposal(
            state=candidate_state,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


def build_demo_problem(
    *,
    task_id: str = "finite-csp-demo",
    initial: State = (("x", 0), ("y", 0)),
    step_budget: int = 4,
) -> RuntimeProblem:
    domains = (("x", (0, 1)), ("y", (0, 1)))
    constraints = (
        FiniteConstraint("fixed:x", (("x", 1),), 1),
        FiniteConstraint("fixed:y", (("y", 1),), 1),
        FiniteConstraint(
            "closure:x+y",
            (("x", 1), ("y", 1)),
            2,
            closure_failure=True,
        ),
    )
    projector = FiniteCspProjector(domains=domains, constraints=constraints)
    normalized_initial = normalize_state(initial)
    initial_state_hash = domain_digest(
        "omega.oesos.native-state.v1", normalized_initial
    )
    exact_state: State = (("x", 1), ("y", 1))
    payload = {
        "domains": domains,
        "constraints": tuple(
            {
                "constraint_id": item.constraint_id,
                "coefficients": item.coefficients,
                "rhs": item.rhs,
                "closure_failure": item.closure_failure,
            }
            for item in constraints
        ),
        "initial_state": normalized_initial,
    }
    envelope = PacketEnvelopeV2(
        task_id=task_id,
        packet_family="finite_csp",
        carrier_id="finite-csp-v1",
        initial_state_hash=initial_state_hash,
        payload=payload,
        constraints=tuple(item.constraint_id for item in constraints),
        protected_boundaries=tuple(item.constraint_id for item in constraints),
        step_budget=step_budget,
        source_digest=domain_digest("omega.oesos.fixture-source.v1", payload),
    )
    adapter = IdentityAdapter(
        source_carrier_id="finite-csp-v1",
        target_carrier_id="finite-csp-v1",
    )
    exact_projection = projector.project(exact_state)
    initial_projection = projector.project(normalized_initial)
    return RuntimeProblem(
        envelope=envelope,
        native_initial_state=normalized_initial,
        projector=projector,
        adapter=adapter,
        detector_cases=(
            DetectorCase(
                "known-exact",
                exact_state,
                (),
                exact_projection.control_digest,
            ),
            DetectorCase(
                "known-obstructed",
                normalized_initial,
                initial_projection.active_ids,
                initial_projection.control_digest,
            ),
        ),
        primitive_difference="integer linear constraint residual",
        zero_relation="all declared constraint residuals are zero",
        observer_id=projector.projector_id,
        witness_certificate="finite-csp-positive-negative-controls-v1",
        protected_obstruction_ids=tuple(item.constraint_id for item in constraints),
    )
