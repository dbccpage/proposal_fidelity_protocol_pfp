"""Run the routing policy through the same packet/projection machinery.

Learning is proposal-only by default.  An explicit caller may apply a policy to
the current lab object after held-out non-regression checks; production promotion
remains outside this package.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pfp.domain.shared_kernel.canonical import domain_digest, freeze
from ..entities.packet_envelope import CandidateArtifactV1, PacketEnvelopeV2

from pfp.domain.shared_kernel.authority_effect import AuthorityEffect
from pfp.domain.entities.oesos_evidence_bundle import DdaLetter
from pfp.domain.entities.projection_receipt import (
    DetectorCase,
    Obstruction,
    ProjectionReceipt,
    SolverManifest,
    SolverProposal,
    TerminalStatus,
)
from pfp.domain.entities.problem import (
    CandidateSolver,
    IdentityAdapter,
    RuntimeProblem,
)




@dataclass(frozen=True, slots=True)
class FrozenCorpus:
    corpus_id: str
    problems: tuple[RuntimeProblem, ...] = ()
    expected_terminal_statuses: tuple[str, ...] = ()
    corpus_sha256: str | None = None
    sample_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.problems or self.expected_terminal_statuses:
            if len(self.problems) != len(self.expected_terminal_statuses):
                raise ValueError("frozen corpus requires one external label per problem")
            packet_ids = tuple(problem.envelope.packet_id for problem in self.problems)
            if len(packet_ids) != len(set(packet_ids)):
                raise ValueError("frozen corpus packet ids must be unique")

    @classmethod
    def create(
        cls,
        *,
        corpus_id: str,
        corpus_sha256: str,
        sample_ids: Sequence[str],
    ) -> FrozenCorpus:
        return cls(
            corpus_id=corpus_id,
            corpus_sha256=str(corpus_sha256),
            sample_ids=tuple(sample_ids),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus_id": self.corpus_id,
            "corpus_sha256": self.corpus_sha256,
            "sample_ids": list(self.sample_ids),
        }

    @property
    def digest(self) -> str:
        return domain_digest(
            "core.oesos.frozen-corpus.v1",
            {
                "corpus_id": self.corpus_id,
                "cases": tuple(
                    {
                        "packet_id": problem.envelope.packet_id,
                        "runtime_id": problem.runtime_id,
                        "expected_terminal_status": expected,
                    }
                    for problem, expected in zip(
                        self.problems,
                        self.expected_terminal_statuses,
                    )
                ),
            },
        )


@dataclass(frozen=True, slots=True)
class PolicyScore:
    policy: tuple[str, ...] = ()
    correct_terminal_count: int = 0
    false_terminal_count: int = 0
    total_attempts: int = 0
    terminal_statuses: tuple[str, ...] = ()
    policy_id: str | None = None
    corpus_id: str | None = None
    success_rate: float | None = None
    average_residual_drop: float | None = None
    efficiency: float | None = None

    @classmethod
    def create(
        cls,
        *,
        policy_id: str,
        corpus_id: str,
        success_rate: float,
        average_residual_drop: float,
        efficiency: float,
    ) -> PolicyScore:
        return cls(
            policy_id=policy_id,
            corpus_id=corpus_id,
            success_rate=success_rate,
            average_residual_drop=average_residual_drop,
            efficiency=efficiency,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "corpus_id": self.corpus_id,
            "success_rate": self.success_rate,
            "average_residual_drop": self.average_residual_drop,
            "efficiency": self.efficiency,
        }

    @property
    def performance_key(self) -> tuple[int, int, int]:
        return (
            -self.correct_terminal_count,
            self.false_terminal_count,
            self.total_attempts,
        )

    @property
    def selection_key(self) -> tuple[int, int, int, tuple[str, ...]]:
        return (*self.performance_key, self.policy)



def evaluate_policy(
    solvers: tuple[CandidateSolver, ...] | tuple[Any, ...],
    policy: tuple[str, ...],
    corpus: FrozenCorpus,
) -> PolicyScore:
    try:
        from pfp.domain.entities.lab import OesosLab, RunReceipt
    except ImportError:
        from .lab import OesosLab, RunReceipt  # type: ignore

    evaluator = OesosLab(solvers, policy=policy)
    receipts_list: list[RunReceipt] = []
    for problem in corpus.problems:
        first = evaluator.solve(problem)
        replay = evaluator.solve(problem)
        if first.to_wire_receipt().receipt_id != replay.to_wire_receipt().receipt_id:
            raise ValueError(
                "determinism replay mismatch for "
                f"packet {problem.envelope.packet_id} under policy {policy}"
            )
        receipts_list.append(first)
    receipts = tuple(receipts_list)
    exact_candidate = TerminalStatus.LAB_EXACT_CANDIDATE.value
    correct = sum(
        receipt.terminal_status.value == expected
        and (expected != exact_candidate or receipt.locally_resolved)
        for receipt, expected in zip(receipts, corpus.expected_terminal_statuses)
    )
    false_terminal = sum(
        receipt.terminal_status.value == exact_candidate
        and (expected != exact_candidate or not receipt.locally_resolved)
        for receipt, expected in zip(receipts, corpus.expected_terminal_statuses)
    )
    return PolicyScore(
        policy=policy,
        correct_terminal_count=correct,
        false_terminal_count=false_terminal,
        total_attempts=sum(len(receipt.attempts) for receipt in receipts),
        terminal_statuses=tuple(receipt.terminal_status.value for receipt in receipts),
    )


def _paired_promotion_rescore(
    solvers: tuple[CandidateSolver, ...],
    baseline_policy: tuple[str, ...],
    proposed_policy: tuple[str, ...],
    corpus: FrozenCorpus,
) -> tuple[PolicyScore, PolicyScore]:
    baseline_first = evaluate_policy(solvers, baseline_policy, corpus)
    proposed_first = evaluate_policy(solvers, proposed_policy, corpus)
    proposed_second = evaluate_policy(solvers, proposed_policy, corpus)
    baseline_second = evaluate_policy(solvers, baseline_policy, corpus)
    if baseline_first != baseline_second or proposed_first != proposed_second:
        raise ValueError(
            f"promotion paired rescore mismatch for corpus {corpus.corpus_id}"
        )
    return baseline_second, proposed_second


@dataclass(frozen=True, slots=True)
class RoutingPolicyProjector:
    solvers: tuple[CandidateSolver, ...]
    corpus: FrozenCorpus
    baseline: PolicyScore
    target: PolicyScore
    solver_registry_hash: str
    held_out_corpus_digest: str
    projector_id: str = "routing-policy-projector-v1"

    @property
    def solver_ids(self) -> tuple[str, ...]:
        return tuple(solver.manifest.solver_id for solver in self.solvers)

    @property
    def config_digest(self) -> str:
        return domain_digest(
            "core.oesos.projector-config.v1",
            {
                "projector_id": self.projector_id,
                "corpus_digest": self.corpus.digest,
                "held_out_corpus_digest": self.held_out_corpus_digest,
                "solver_registry_hash": self.solver_registry_hash,
                "baseline": self.baseline,
                "target": self.target,
                "terminalizer_id": TERMINALIZER_ID,
            },
        )

    def meaning(self, state: Any) -> Any:
        return tuple(str(item) for item in state)

    def skeleton(self, state: Any) -> Any:
        return {
            "registered_solvers": tuple(sorted(self.solver_ids)),
            "solver_registry_hash": self.solver_registry_hash,
            "corpus_digest": self.corpus.digest,
            "terminalizer_id": TERMINALIZER_ID,
        }

    def validate_packet(
        self,
        envelope: PacketEnvelopeV2,
        native_initial_state: Any,
    ) -> bool:
        expected_payload = {
            "frozen_solver_registry": self.solver_ids,
            "solver_registry_hash": self.solver_registry_hash,
            "training_corpus_digest": self.corpus.digest,
            "held_out_corpus_digest": self.held_out_corpus_digest,
            "terminalizer_id": TERMINALIZER_ID,
            "baseline_policy": self.baseline.policy,
            "target_score": {
                "correct_terminal_count": self.target.correct_terminal_count,
                "false_terminal_count": self.target.false_terminal_count,
                "total_attempts": self.target.total_attempts,
            },
        }
        expected_constraints = (
            "preserve frozen solver registry",
            "do not reduce externally labeled correct terminals",
            "do not increase false terminal proposals",
            "minimize matched-budget proposal attempts",
        )
        return (
            tuple(native_initial_state) == self.baseline.policy
            and envelope.carrier_id == "routing-policy-v1"
            and envelope.constraints == expected_constraints
            and envelope.payload == freeze(expected_payload)
            and envelope.source_digest
            == domain_digest("core.oesos.policy-source.v1", expected_payload)
        )

    def project(self, state: Any) -> ProjectionReceipt:
        policy = self.meaning(state)
        obstructions: list[Obstruction] = []
        if len(policy) != len(set(policy)):
            obstructions.append(
                Obstruction(
                    "policy:duplicate-solver",
                    1.0,
                    "routing policy repeats a solver id",
                    closure_failure=True,
                )
            )
        if set(policy) != set(self.solver_ids):
            obstructions.append(
                Obstruction(
                    "policy:unknown-or-missing-solver",
                    1.0,
                    "routing policy does not preserve the frozen registry",
                    closure_failure=True,
                )
            )
        if not obstructions:
            score = evaluate_policy(self.solvers, policy, self.corpus)
            solved_regression = (
                self.baseline.correct_terminal_count - score.correct_terminal_count
            )
            if solved_regression > 0:
                obstructions.append(
                    Obstruction(
                        "policy:solved-regression",
                        float(solved_regression),
                        "candidate policy solves fewer frozen training packets",
                        closure_failure=True,
                    )
                )
            false_terminal_growth = (
                score.false_terminal_count - self.baseline.false_terminal_count
            )
            if false_terminal_growth > 0:
                obstructions.append(
                    Obstruction(
                        "policy:false-terminal-growth",
                        float(false_terminal_growth),
                        "candidate policy increases false terminal proposals",
                        closure_failure=True,
                    )
                )
            attempt_excess = score.total_attempts - self.target.total_attempts
            if attempt_excess > 0:
                obstructions.append(
                    Obstruction(
                        "policy:attempt-excess",
                        float(attempt_excess),
                        "candidate policy uses more proposals than the best observed policy",
                    )
                )
        return ProjectionReceipt(
            projector_id=self.projector_id,
            state_hash=domain_digest("core.oesos.state.v1", policy),
            obstructions=tuple(obstructions),
            witness=f"matched-budget-corpus:{self.corpus.digest}",
        )

    def verify_retraction(
        self,
        solver_id: str,
        before_state: Any,
        after_state: Any,
    ) -> bool:
        return (
            solver_id == "routing-policy-exhaustive-search"
            and tuple(after_state) == self.target.policy
            and tuple(before_state) != tuple(after_state)
        )


@dataclass(frozen=True, slots=True)
class PolicySearchSolver:
    best_policy: tuple[str, ...]
    manifest: SolverManifest = SolverManifest(
        solver_id="routing-policy-exhaustive-search",
        families=("oesos_routing_policy",),
    )

    def propose(
        self,
        problem: RuntimeProblem,
        packet_state: Any,
        projection: ProjectionReceipt,
    ) -> SolverProposal | None:
        if tuple(packet_state) == self.best_policy:
            return None
        candidate = CandidateArtifactV1(
            packet_id=problem.envelope.packet_id,
            producer_id=self.manifest.solver_id,
            payload=self.best_policy,
            witness="complete-permutation-search-over-frozen-solver-registry",
            claimed_terminal="Exact",
        )
        return SolverProposal(
            state=self.best_policy,
            candidate=candidate,
            next_carrier_id=problem.adapter.target_carrier_id,
        )


@dataclass(frozen=True, slots=True)
class SelfImprovementReceipt:
    baseline_policy: tuple[str, ...]
    proposed_policy: tuple[str, ...]
    training_baseline: PolicyScore
    training_proposed: PolicyScore
    held_out_baseline: PolicyScore
    held_out_proposed: PolicyScore
    policy_packet_run: RunReceipt
    non_regression_passed: bool
    strict_improvement: bool
    promotion_isolation_attested: bool
    promotion_rescore_passed: bool
    applied_locally: bool
    authority_effect: str = field(default="None")


def propose_routing_update(
    engine: OesosLab | Any,
    training: FrozenCorpus,
    held_out: FrozenCorpus,
    *,
    apply: bool = False,
) -> SelfImprovementReceipt:
    from collections.abc import Iterable, Sequence
    from pfp.domain.entities.problem import (
        DetectorCase,
        IdentityAdapter,
        RuntimeProblem,
    )
    try:
        from pfp.domain.entities.lab import OesosLab
    except ImportError:
        from .lab import OesosLab  # type: ignore

    """Evaluate every finite routing permutation and packetize the best proposal."""

    if apply and not engine.promotion_isolation_attested:
        findings = ",".join(engine.promotion_isolation_findings)
        raise ValueError(f"promotion isolation is not attested: {findings}")
    if apply and not engine.solver_registry_identity_valid():
        raise ValueError("promotion solver registry identity drift")

    solvers = engine.solvers
    initial_registry_hash = engine.solver_registry_hash
    if not solvers:
        raise ValueError("routing search requires at least one solver")
    if len(solvers) > 7:
        raise ValueError("policy permutation search is capped at seven solvers")
    training_ids = {problem.envelope.packet_id for problem in training.problems}
    held_out_ids = {problem.envelope.packet_id for problem in held_out.problems}
    if training_ids & held_out_ids:
        raise ValueError("training and held-out packet ids must be disjoint")
    solver_ids = tuple(solver.manifest.solver_id for solver in solvers)
    policies = tuple(itertools.permutations(solver_ids))
    scores = tuple(evaluate_policy(solvers, policy, training) for policy in policies)
    baseline_score = evaluate_policy(solvers, engine.policy, training)
    searched_best = min(scores, key=lambda score: score.selection_key)
    strict_improvement = searched_best.performance_key < baseline_score.performance_key
    best_score = searched_best if strict_improvement else baseline_score
    projector = RoutingPolicyProjector(
        solvers=solvers,
        corpus=training,
        baseline=baseline_score,
        target=best_score,
        solver_registry_hash=engine.solver_registry_hash,
        held_out_corpus_digest=held_out.digest,
    )
    duplicate_control = tuple(solver_ids[0] for _ in solver_ids)
    best_projection = projector.project(best_score.policy)
    duplicate_projection = projector.project(duplicate_control)
    payload = {
        "frozen_solver_registry": solver_ids,
        "solver_registry_hash": engine.solver_registry_hash,
        "training_corpus_digest": training.digest,
        "held_out_corpus_digest": held_out.digest,
        "terminalizer_id": TERMINALIZER_ID,
        "baseline_policy": engine.policy,
        "target_score": {
            "correct_terminal_count": best_score.correct_terminal_count,
            "false_terminal_count": best_score.false_terminal_count,
            "total_attempts": best_score.total_attempts,
        },
    }
    envelope = PacketEnvelopeV2(
        task_id=f"routing-policy:{training.corpus_id}",
        packet_family="oesos_routing_policy",
        carrier_id="routing-policy-v1",
        initial_state_hash=domain_digest("core.oesos.native-state.v1", engine.policy),
        payload=payload,
        constraints=(
            "preserve frozen solver registry",
            "do not reduce externally labeled correct terminals",
            "do not increase false terminal proposals",
            "minimize matched-budget proposal attempts",
        ),
        protected_boundaries=(
            "policy:duplicate-solver",
            "policy:unknown-or-missing-solver",
            "policy:solved-regression",
            "policy:false-terminal-growth",
        ),
        step_budget=1,
        source_digest=domain_digest("core.oesos.policy-source.v1", payload),
    )
    problem = RuntimeProblem(
        envelope=envelope,
        native_initial_state=engine.policy,
        projector=projector,
        adapter=IdentityAdapter("routing-policy-v1", "routing-policy-v1"),
        detector_cases=(
            DetectorCase(
                "best-observed-policy",
                best_score.policy,
                (),
                best_projection.control_digest,
            ),
            DetectorCase(
                "duplicate-policy-control",
                duplicate_control,
                duplicate_projection.active_ids,
                duplicate_projection.control_digest,
            ),
        ),
        primitive_difference="matched-budget policy score residual",
        zero_relation="no registry/regression/false-terminal/attempt residual",
        observer_id=projector.projector_id,
        witness_certificate=f"training-corpus:{training.digest}",
        protected_obstruction_ids=(
            "policy:duplicate-solver",
            "policy:unknown-or-missing-solver",
            "policy:solved-regression",
            "policy:false-terminal-growth",
        ),
    )
    policy_engine = OesosLab((PolicySearchSolver(best_score.policy),))
    packet_run = policy_engine.solve(problem)
    proposed_policy = (
        tuple(packet_run.final_native_state)
        if packet_run.locally_resolved
        else engine.policy
    )
    proposed_training = evaluate_policy(solvers, proposed_policy, training)
    held_out_baseline = evaluate_policy(solvers, engine.policy, held_out)
    held_out_proposed = evaluate_policy(solvers, proposed_policy, held_out)
    non_regression = (
        proposed_training.correct_terminal_count
        >= baseline_score.correct_terminal_count
        and proposed_training.false_terminal_count
        <= baseline_score.false_terminal_count
        and held_out_proposed.correct_terminal_count
        >= held_out_baseline.correct_terminal_count
        and held_out_proposed.false_terminal_count
        <= held_out_baseline.false_terminal_count
        and held_out_proposed.total_attempts <= held_out_baseline.total_attempts
    )
    promotion_rescore_passed = False
    if apply and packet_run.locally_resolved and strict_improvement:
        promotion_training_baseline, promotion_training_proposed = (
            _paired_promotion_rescore(
                solvers,
                engine.policy,
                proposed_policy,
                training,
            )
        )
        promotion_held_out_baseline, promotion_held_out_proposed = (
            _paired_promotion_rescore(
                solvers,
                engine.policy,
                proposed_policy,
                held_out,
            )
        )
        baseline_score = promotion_training_baseline
        proposed_training = promotion_training_proposed
        held_out_baseline = promotion_held_out_baseline
        held_out_proposed = promotion_held_out_proposed
        strict_improvement = (
            proposed_training.performance_key < baseline_score.performance_key
        )
        non_regression = (
            proposed_training.correct_terminal_count
            >= baseline_score.correct_terminal_count
            and proposed_training.false_terminal_count
            <= baseline_score.false_terminal_count
            and held_out_proposed.correct_terminal_count
            >= held_out_baseline.correct_terminal_count
            and held_out_proposed.false_terminal_count
            <= held_out_baseline.false_terminal_count
            and held_out_proposed.total_attempts <= held_out_baseline.total_attempts
        )
        promotion_rescore_passed = True
    applied = bool(
        apply
        and packet_run.locally_resolved
        and non_regression
        and strict_improvement
        and promotion_rescore_passed
    )
    if applied:
        if (
            engine.solver_registry_hash != initial_registry_hash
            or not engine.solver_registry_identity_valid()
        ):
            raise ValueError("promotion solver registry identity drift")
        engine._apply_verified_local_policy(
            proposed_policy,
            expected_registry_hash=initial_registry_hash,
        )
    return SelfImprovementReceipt(
        baseline_policy=baseline_score.policy,
        proposed_policy=proposed_policy,
        training_baseline=baseline_score,
        training_proposed=proposed_training,
        held_out_baseline=held_out_baseline,
        held_out_proposed=held_out_proposed,
        policy_packet_run=packet_run,
        non_regression_passed=non_regression,
        strict_improvement=strict_improvement,
        promotion_isolation_attested=engine.promotion_isolation_attested,
        promotion_rescore_passed=promotion_rescore_passed,
        applied_locally=applied,
    )


@dataclass(frozen=True, slots=True)
class RoutingHypothesis:
    hypothesis_id: str
    target_regime: str
    routing_weights: dict[str, float]
    predicted_efficiency: float

    @classmethod
    def create(
        cls,
        *,
        hypothesis_id: str,
        target_regime: str,
        routing_weights: dict[str, float],
        predicted_efficiency: float,
    ) -> RoutingHypothesis:
        return cls(
            hypothesis_id=hypothesis_id,
            target_regime=target_regime,
            routing_weights=dict(routing_weights),
            predicted_efficiency=predicted_efficiency,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "target_regime": self.target_regime,
            "routing_weights": self.routing_weights,
            "predicted_efficiency": self.predicted_efficiency,
        }


LearningPolicyV1 = RoutingHypothesis




