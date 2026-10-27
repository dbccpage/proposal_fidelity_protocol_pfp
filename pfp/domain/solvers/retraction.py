"""Discrete Manifold Retraction Turn Machine and Strict Descent Verification.

Evaluates discrete retraction turns against the obstruction triad:
    (Gamma_2, Phi_1, defect_count)
where:
    - Phi_1: Simplicial boundary defect evaluated via sovereign ExactHomologyPort (core_homology).
    - Gamma_2: Discrete holonomy curvature defect evaluated via sovereign ExactHolonomyPort (core_holonomy).
    - defect_count: Active count of unsatisfied requirements in the extended regime.

Governing Invariant: Symbol Game Non-Prose Communication & Zero Data-Loss Invariant.
Governing Invariant: Strict Descent on (Gamma_2, Phi_1, defect_count).
Governing Invariant: Value Object Exact-Type Equality Invariant (RULE_VALUE_OBJECT_EXACT_TYPE_EQUALITY_001).
AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from ..exact.q import Q
from ..models import ObstructionScore, StepVerdict
from ..ports.exact_ports import get_retraction_port
from .canon import dumps, sha256_tag
from .errors import ClaimFrozen, SolverRefusal
from .kinds import (
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    RegimeOracle,
    SimplicialBoundaryLawSatisfied,
    get_functional_port,
    get_holonomy_port,
    get_homology_port,
    satisfies,
)
from .regime import Delta
from .regimek import (
    RegimeK,
    Stage,
    admit_response,
    check_witness_only,
    claims_unchanged,
)
from .search import delta_json


def compute_obstruction_score(s: RegimeK) -> ObstructionScore:
    """Computes the exact obstruction triad (Gamma_2, Phi_1, defect_count) for an extended regime.

    Topological and curvature obligations delegate directly to sovereign Rust crates.
    Operates strictly via exact rational arithmetic (Fraction / Q).
    """
    phi_1 = Fraction(0)
    gamma_2 = Fraction(0)

    hom_port = get_homology_port()
    hol_port = get_holonomy_port()

    for q in s.reqs:
        if isinstance(q, HomologyBoundaryClosed):
            if not hom_port.verify_boundary_closed(q.faces):
                # Measure net boundary violation across open cell complexes
                violation = Fraction(0)
                for terms in q.faces:
                    net: dict[int, int] = {}
                    for t, h, sign in terms:
                        net[h] = net.get(h, 0) + sign
                        net[t] = net.get(t, 0) - sign
                    net_sum = sum(abs(v) for v in net.values())
                    violation += Fraction(net_sum, 2)
                phi_1 += max(Fraction(1), violation)
        elif isinstance(q, HolonomyLoopClosed):
            if not hol_port.is_ordered_closure(q.tables, q.word):
                prod = hol_port.ordered_loop_product(q.tables, q.word)
                dim = len(prod)
                diff = Fraction(0)
                for i in range(dim):
                    for j in range(dim):
                        expected = 1 if i == j else 0
                        val = prod[i][j]
                        if isinstance(val, Q):
                            diff += abs(Fraction(val.num, val.den) - expected)
                        elif hasattr(val, "num") and hasattr(val, "den"):
                            diff += abs(Fraction(val.num, val.den) - expected)
                        else:
                            diff += abs(Fraction(val) - expected)
                gamma_2 += max(Fraction(1), diff)
        elif isinstance(q, SimplicialBoundaryLawSatisfied):
            report = hom_port.verify_simplicial_boundary_law(q.simplices)
            if not report.get("boundary_law_verified", False):
                phi_1 += Fraction(1)
        elif hasattr(q, "d0") and hasattr(q, "d1") and hasattr(q, "residual"):
            # A requirement that only the functional port can measure is never
            # scored as zero because the measurement was unavailable or failed.
            func_port = getattr(s, "functional_port", None)
            if func_port is None:
                func_port = get_functional_port()
            if func_port is None:
                raise SolverRefusal(
                    "FUNCTIONAL_PORT_REQUIRED",
                    f"requirement {getattr(q, 'rid', '?')} needs the functional port "
                    "and none is registered",
                )
            try:
                receipt = func_port.evaluate(q.d0, q.d1, q.residual)
            except SolverRefusal:
                raise
            except Exception as err:
                raise SolverRefusal(
                    "FUNCTIONAL_EVALUATION_FAILED",
                    f"requirement {getattr(q, 'rid', '?')}: {err}",
                ) from err
            phi_1 += receipt.phi1
            gamma_2 += receipt.gamma2

    o = RegimeOracle(s.base)
    unsatisfied = tuple(sorted(q.rid for q in s.reqs if not satisfies(o, q)))
    active_count = len(unsatisfied)

    return ObstructionScore(
        gamma_2=gamma_2,
        phi_1=phi_1,
        active_count=active_count,
        active_obstruction_ids=unsatisfied,
    )


def _common_scale(scores: Sequence[ObstructionScore]) -> int:
    """Least common denominator of every Gamma_2 and Phi_1 in ``scores``."""
    scale = 1
    for score in scores:
        scale = math.lcm(scale, score.gamma_2.denominator, score.phi_1.denominator)
    return scale


def _scaled_triad(score: ObstructionScore, scale: int) -> dict[str, int]:
    """One score as integers on a shared scale, so triads stay comparable."""
    gamma_2 = score.gamma_2 * scale
    phi_1 = score.phi_1 * scale
    if gamma_2.denominator != 1 or phi_1.denominator != 1:
        raise SolverRefusal("TRIAD_SCALE_INEXACT", f"scale {scale} does not clear {score}")
    return {
        "gamma_2": gamma_2.numerator,
        "phi_1": phi_1.numerator,
        "defect_count": score.active_count,
    }


def _to_exact_triad_ints(
    score_a: ObstructionScore, score_b: ObstructionScore
) -> tuple[dict[str, int], dict[str, int]]:
    """Converts exact rational obstruction scores to scaled integers for native DescentTriad."""
    scale = _common_scale((score_a, score_b))
    return _scaled_triad(score_a, scale), _scaled_triad(score_b, scale)




@dataclass(frozen=True)
class RetractionTurnOutcome:
    """Discrete retraction turn outcome with exact-type equality and immutable evidence."""

    turn_index: int
    task_id: str
    stage: Stage
    delta: Delta
    prior_score: ObstructionScore
    new_score: ObstructionScore
    verdict: StepVerdict
    is_exact: bool
    child_state: RegimeK | None
    evidence_sha256: str
    details: str = "OK"
    authority_effect: Literal["None"] = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.turn_index == other.turn_index
            and self.task_id == other.task_id
            and self.stage == other.stage
            and self.delta == other.delta
            and self.prior_score == other.prior_score
            and self.new_score == other.new_score
            and self.verdict == other.verdict
            and self.is_exact == other.is_exact
            and self.child_state == other.child_state
            and self.evidence_sha256 == other.evidence_sha256
            and self.details == other.details
            and self.authority_effect == other.authority_effect
        )


def _refused_turn(
    *,
    task_id: str,
    turn_index: int,
    stage: Stage,
    delta: Delta,
    prior: ObstructionScore,
    reason: str,
    new_score: ObstructionScore | None = None,
) -> RetractionTurnOutcome:
    """A REFUSAL outcome that keeps the prior state and records why."""
    measured = new_score if new_score is not None else prior
    evidence = sha256_tag(
        dumps({
            "task_id": task_id,
            "turn_index": turn_index,
            "delta": delta_json(delta),
            "prior_score": [str(prior.gamma_2), str(prior.phi_1), prior.active_count],
            "new_score": [str(measured.gamma_2), str(measured.phi_1), measured.active_count],
            "error": reason,
            "verdict": StepVerdict.REFUSAL.value,
        })
    )
    return RetractionTurnOutcome(
        turn_index=turn_index,
        task_id=task_id,
        stage=stage,
        delta=delta,
        prior_score=prior,
        new_score=measured,
        verdict=StepVerdict.REFUSAL,
        is_exact=False,
        child_state=None,
        evidence_sha256=evidence,
        details=reason,
    )


def execute_retraction_turn(
    *,
    task_id: str,
    turn_index: int,
    state: RegimeK,
    candidate_delta: Delta,
    stage: Stage,
    prior_score: ObstructionScore | None = None,
) -> RetractionTurnOutcome:
    """Executes a single discrete manifold retraction turn with strict descent verification.

    An unmeasurable prior state raises ``SolverRefusal``: there is no score to
    attach to a refusal outcome, so the caller gets the typed refusal itself.
    """
    prior = prior_score if prior_score is not None else compute_obstruction_score(state)

    try:
        check_witness_only(state, stage, candidate_delta)
        child_state = admit_response(state, stage, candidate_delta)
        if not claims_unchanged(state, child_state):
            raise ClaimFrozen("CLAIM_FROZEN", "candidate touched frozen claim forms")
    except (SolverRefusal, Exception) as err:
        evidence = sha256_tag(
            dumps({
                "task_id": task_id,
                "turn_index": turn_index,
                "delta": delta_json(candidate_delta),
                "error": str(err),
                "verdict": StepVerdict.REFUSAL.value,
            })
        )
        return RetractionTurnOutcome(
            turn_index=turn_index,
            task_id=task_id,
            stage=stage,
            delta=candidate_delta,
            prior_score=prior,
            new_score=prior,
            verdict=StepVerdict.REFUSAL,
            is_exact=False,
            child_state=None,
            evidence_sha256=evidence,
            details=f"Admission refused: {err}",
        )

    try:
        new_score = compute_obstruction_score(child_state)
    except SolverRefusal as err:
        return _refused_turn(
            task_id=task_id,
            turn_index=turn_index,
            stage=stage,
            delta=candidate_delta,
            prior=prior,
            reason=f"Measurement refused: {err}",
        )
    is_exact = new_score.is_exact
    improves = new_score.strictly_improves(prior)

    # A registered RetractionEnginePort is a second, independent judge of
    # descent. A turn the local check already refuses needs no second opinion;
    # otherwise the port's word is required, and an error from it is a refusal,
    # never a quiet fallback to the local check alone.
    retraction_port = getattr(child_state, "retraction_port", None)
    if retraction_port is None:
        retraction_port = get_retraction_port()

    port_note = "local strict-descent check only; no retraction port registered"
    if retraction_port is not None and improves:
        try:
            triad_before, triad_after = _to_exact_triad_ints(prior, new_score)
            candidate_payload = {
                "token_stream": f"TURN_{turn_index}",
                "cochain_projection": [bool(d) for d in candidate_delta] if candidate_delta else [True],
                "triad": triad_after,
            }
            res = retraction_port.retraction_turn(
                before=triad_before,
                after=triad_after,
                candidate=candidate_payload,
            )
        except Exception as err:
            return _refused_turn(
                task_id=task_id,
                turn_index=turn_index,
                stage=stage,
                delta=candidate_delta,
                prior=prior,
                reason=f"Retraction port failed: {err}",
                new_score=new_score,
            )
        if res.get("admitted") is not True:
            reason = str(res.get("refusal", "retraction port did not admit the turn"))
            return _refused_turn(
                task_id=task_id,
                turn_index=turn_index,
                stage=stage,
                delta=candidate_delta,
                prior=prior,
                reason=f"Retraction port refused: {reason}",
                new_score=new_score,
            )
        port_note = "retraction port admitted the turn"

    if is_exact and improves:
        verdict = StepVerdict.EXACT
        details = (
            "Exact terminal certificate reached: Phi_1 = 0, Gamma_2 = 0, defect_count = 0"
            f" ({port_note})"
        )
        accepted_child = child_state
    elif improves:
        verdict = StepVerdict.DESCENT
        details = f"Strict descent verified on (Gamma_2, Phi_1, defect_count) ({port_note})"
        accepted_child = child_state
    else:
        verdict = StepVerdict.REFUSAL
        details = f"Non-contractive proposal: prior={prior}, new={new_score}"
        accepted_child = None
        is_exact = False

    evidence = sha256_tag(
        dumps({
            "task_id": task_id,
            "turn_index": turn_index,
            "delta": delta_json(candidate_delta),
            "prior_score": [str(prior.gamma_2), str(prior.phi_1), prior.active_count],
            "new_score": [str(new_score.gamma_2), str(new_score.phi_1), new_score.active_count],
            "verdict": verdict.value,
        })
    )

    return RetractionTurnOutcome(
        turn_index=turn_index,
        task_id=task_id,
        stage=stage,
        delta=candidate_delta,
        prior_score=prior,
        new_score=new_score,
        verdict=verdict,
        is_exact=is_exact,
        child_state=accepted_child,
        evidence_sha256=evidence,
        details=details,
    )


@dataclass(frozen=True)
class RetractionLoopResult:
    """Result of a multi-turn discrete retraction chase."""

    task_id: str
    initial_score: ObstructionScore
    final_score: ObstructionScore
    turns: tuple[RetractionTurnOutcome, ...]
    final_state: RegimeK
    converged: bool
    is_exact: bool
    total_descent_steps: int
    native_check: str = "NOT_RUN"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.task_id == other.task_id
            and self.initial_score == other.initial_score
            and self.final_score == other.final_score
            and self.turns == other.turns
            and self.final_state == other.final_state
            and self.converged == other.converged
            and self.is_exact == other.is_exact
            and self.total_descent_steps == other.total_descent_steps
            and self.native_check == other.native_check
        )


def run_retraction_loop(
    *,
    task_id: str,
    initial_state: RegimeK,
    stage: Stage,
    candidate_deltas: Sequence[Delta],
) -> RetractionLoopResult:
    """Executes a multi-turn retraction loop over candidate deltas, verifying strict descent."""
    current_state = initial_state
    current_score = compute_obstruction_score(current_state)
    initial_score = current_score

    turns: list[RetractionTurnOutcome] = []
    descent_steps = 0

    for idx, delta in enumerate(candidate_deltas):
        if current_score.is_exact:
            break

        turn_outcome = execute_retraction_turn(
            task_id=task_id,
            turn_index=idx,
            state=current_state,
            candidate_delta=delta,
            stage=stage,
            prior_score=current_score,
        )
        turns.append(turn_outcome)

        if turn_outcome.verdict in (StepVerdict.DESCENT, StepVerdict.EXACT):
            assert turn_outcome.child_state is not None
            current_state = turn_outcome.child_state
            current_score = turn_outcome.new_score
            descent_steps += 1

    native_check = "NOT_RUN"
    retraction_port = getattr(initial_state, "retraction_port", None)
    if retraction_port is None:
        retraction_port = get_retraction_port()
    if retraction_port is not None:
        native_check = _replay_on_port(retraction_port, initial_score, turns, descent_steps)

    # Converged means an exact terminal certificate, nothing less. When the
    # port was asked and did not agree, the loop claims neither.
    agreed = native_check in ("NOT_RUN", "AGREED")
    is_exact = current_score.is_exact and agreed
    return RetractionLoopResult(
        task_id=task_id,
        initial_score=initial_score,
        final_score=current_score,
        turns=tuple(turns),
        final_state=current_state,
        converged=is_exact,
        is_exact=is_exact,
        total_descent_steps=descent_steps,
        native_check=native_check,
    )


def _replay_on_port(
    port: object,
    initial_score: ObstructionScore,
    turns: Sequence[RetractionTurnOutcome],
    descent_steps: int,
) -> str:
    """Replays every turn on the retraction port and compares its count of admissions.

    Every triad is put on one shared integer scale so the port compares like
    with like. Returns ``AGREED`` or a ``DISAGREED``/``REFUSED`` string.
    """
    if not callable(getattr(port, "retraction_loop", None)):
        return "NOT_RUN"
    try:
        scale = _common_scale([initial_score, *(t.new_score for t in turns)])
        candidates_wire = [
            {
                "token_stream": f"TURN_{t.turn_index}",
                "cochain_projection": [True],
                "triad": _scaled_triad(t.new_score, scale),
            }
            for t in turns
        ]
        receipt = port.retraction_loop(  # type: ignore[attr-defined]
            intake=_scaled_triad(initial_score, scale),
            candidates=candidates_wire,
            open_obligations=initial_score.active_count,
        )
    except Exception as err:
        return f"REFUSED: {err}"
    native_admitted = receipt.get("admitted") if hasattr(receipt, "get") else None
    if native_admitted != descent_steps:
        return f"DISAGREED: port admitted {native_admitted}, loop admitted {descent_steps}"
    return "AGREED"


__all__ = [
    "RetractionLoopResult",
    "RetractionTurnOutcome",
    "compute_obstruction_score",
    "execute_retraction_turn",
    "run_retraction_loop",
]
