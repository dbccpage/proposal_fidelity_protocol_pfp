"""Prompt fitness, Pareto selection, and obligation verification for Prompt Civ.

Enforces:
- F-WOLAND-01: Act VII AUTHORIZED never grants success credit to prompt fitness.
- F-SELECT-01: Pareto front selection + lexicographic tiebreak with no composite scalar.
- F-SELECT-03: A caller receipt or a self-sealed body is not obligation success.
- F-RES-06: Validity or emptiness alone earns no success credit.
- F-RES-09: Comparative claims require held-out split and multiplicity correction.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from omega_engine_operations.domain.rop.result import Err, Refusal, Result
from omega_engine_prompt_civilization.domain.causal_witness import SealedCausalWitness
from omega_engine_woland.domain.evidence import CandidateCheckV1, CheckerVerdict, sha256_ref

if TYPE_CHECKING:
    from omega_engine_woland.domain.ports import CandidateCheckerPort


@dataclass(frozen=True, slots=True)
class ExecutionMetricsV1:
    success_credit: int
    is_empty_or_syntax_only: bool


_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def is_valid_sealed_digest(digest: Any) -> bool:
    """Accept only a lowercase sha256-prefixed 32-byte hex digest.

    A word denylist is not a digest check. Short tokens and unprefixed hex earn no credit.
    """
    return isinstance(digest, str) and _SHA256_DIGEST.fullmatch(digest) is not None


def reduce_selected_attempt_outcome(
    mandatory_outcomes: Sequence[str],
    expected_behavior: str,
    root_outcome: str | None = None,
) -> str:
    """F3: Total Selected-Attempt Outcome Table (Epic PCIV V1.0RC Table 4.7).

    Priority:
    1. Any TaskFail -> TaskFail
    2. Otherwise any InvalidRefusal -> InvalidRefusal
    3. Otherwise any InfrastructureError -> InfrastructureError
    4. Otherwise any NotMeasured -> NotMeasured
    5. Otherwise any Inconclusive -> Inconclusive
    6. Otherwise AllowedTask with any ValidRefusal -> ValidRefusal
    7. Otherwise AllowedTask (all mandatory outcomes are TaskPass) -> TaskPass
    8. Otherwise RefusalRequired and root is ValidRefusal -> ValidRefusal
    9. Otherwise RefusalRequired (root is TaskPass without required refusal) -> InvalidRefusal
    """
    if "TaskFail" in mandatory_outcomes:
        return "TaskFail"
    if "InvalidRefusal" in mandatory_outcomes:
        return "InvalidRefusal"
    if "InfrastructureError" in mandatory_outcomes:
        return "InfrastructureError"
    if "NotMeasured" in mandatory_outcomes:
        return "NotMeasured"
    if "Inconclusive" in mandatory_outcomes:
        return "Inconclusive"
    if expected_behavior == "AllowedTask":
        if "ValidRefusal" in mandatory_outcomes:
            return "ValidRefusal"
        if all(o == "TaskPass" for o in mandatory_outcomes):
            return "TaskPass"
    elif expected_behavior == "RefusalRequired":
        if root_outcome == "ValidRefusal" or (root_outcome is None and "ValidRefusal" in mandatory_outcomes):
            return "ValidRefusal"
        return "InvalidRefusal"
    return "InvalidRefusal"


class PromptFitnessCalculatorV1:
    def __init__(self, *, candidate_checker: CandidateCheckerPort | None = None) -> None:
        self._candidate_checker = candidate_checker
        self._observed_checks: list[CandidateCheckV1] = []
        self._observed_inputs: list[tuple[str, str, str, bytes]] = []

    @property
    def observed_checks(self) -> tuple[CandidateCheckV1, ...]:
        return tuple(self._observed_checks)

    @property
    def observed_inputs(self) -> tuple[tuple[str, str, str, bytes], ...]:
        return tuple(self._observed_inputs)

    def check_candidate(
        self, *, run_key: str, objective: str, candidate_id: str,
        candidate_bytes: bytes, carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        """Execute the host-bound independent checker on the actual candidate.

        The composition root owns checker trust. A caller-supplied result or
        digest cannot substitute for this execution or grant admission.
        """
        if self._candidate_checker is None:
            return Err(Refusal("CHECKER_UNAVAILABLE", "No independent checker is bound", "prompt_civilization.fitness"))
        checked = self._candidate_checker.check_candidate(
            run_key=run_key, objective=objective, candidate_id=candidate_id,
            candidate_bytes=candidate_bytes, carrier_context=carrier_context,
        )
        if checked.is_err:
            return checked
        result = checked.unwrap()
        if not result.binds(candidate_id, (sha256_ref(candidate_bytes),)):
            return Err(Refusal("CHECKER_EVIDENCE_MISMATCH", "Candidate bytes differ", "prompt_civilization.fitness"))
        if result.verdict is not CheckerVerdict.NOT_MEASURED:
            try:
                payload = json.loads(result.checker_receipt_bytes)
                expected = {
                    "run_key": run_key, "candidate_id": candidate_id,
                    "candidate_content_sha256": sha256_ref(candidate_bytes),
                    "checker_id": result.checker_id, "verdict": result.verdict.value,
                }
                if any(payload.get(key) != value for key, value in expected.items()):
                    raise ValueError("checker receipt belongs to a different task or candidate")
            except (ValueError, TypeError, AttributeError) as exc:
                return Err(Refusal("CHECKER_EVIDENCE_MISMATCH", str(exc), "prompt_civilization.fitness"))
        self._observed_checks.append(result)
        self._observed_inputs.append((run_key, objective, candidate_id, candidate_bytes))
        return checked

    def checked_success_credit(self, check: CandidateCheckV1) -> int:
        """Credit only an accepted check actually executed by this bound host."""
        return int(
            check.verdict is CheckerVerdict.ACCEPTED
            and any(observed is check for observed in self._observed_checks)
        )

    def extract_success_credit(self, receipt: Any) -> int:
        """Caller status is not a bound checker.

        Act VII AUTHORIZED is strictly diagnostic data (AuthorityEffect: None)
        and never grants operational success credit. ``VERIFIED_EXACT``,
        ``PASS``, ``SUCCESS``, and ``COMPLETED`` do not either.
        """
        if receipt is None or isinstance(receipt, dict):
            return 0
        gate_status = getattr(receipt, "gate_status", "")
        if gate_status in {"AUTHORIZED", "REFUSED", "NOT_RUN"}:
            return 0
        return 0

    def extract_obligation_success_credit(
        self,
        target_obligation_id: str,
        verifier_receipt: dict[str, Any],
    ) -> int:
        """A self-sealed body is not a bound checker.

        A caller dict, including one with ``VERIFIED_EXACT`` and a well-formed digest, earns nothing.
        A ``SealedCausalWitness`` whose body says ``VERIFIED_EXACT`` earns nothing.
        Credit is ``checked_success_credit`` after this calculator runs its checker.
        """
        if not isinstance(verifier_receipt, SealedCausalWitness):
            return 0
        try:
            body = json.loads(verifier_receipt.canonical_body)
        except json.JSONDecodeError:
            return 0
        if not isinstance(body, dict):
            return 0
        if body.get("obligation_id") != target_obligation_id:
            return 0
        if body.get("is_stale") or body.get("is_unsupported") or body.get("is_fake"):
            return 0
        return 0

    def completion_rate(self, passes: int, n_assigned: int) -> Fraction | None:
        """F3: Completion rate defined as S / N_assigned across all assigned units.

        Preserves true denominators and prevents early valid refusal from inflating completion rates.
        """
        if n_assigned <= 0:
            return None
        return Fraction(passes, n_assigned)

    def reduce_selected_attempt_outcome(
        self,
        mandatory_outcomes: Sequence[str],
        expected_behavior: str,
        root_outcome: str | None = None,
    ) -> str:
        return reduce_selected_attempt_outcome(
            mandatory_outcomes, expected_behavior, root_outcome
        )

    def compute_execution_metrics(self, packet: dict[str, Any]) -> ExecutionMetricsV1:
        """Valid syntax, empty output, a caller Boolean, or a receipt object earns no credit."""
        is_empty = packet.get("is_empty", False) or not packet.get("payload")
        is_syntax_only = packet.get("syntax_valid", False)
        return ExecutionMetricsV1(
            success_credit=0,
            is_empty_or_syntax_only=bool(is_empty or is_syntax_only),
        )


class ParetoFrontSelectorV1:
    def partition_fronts(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:
        """Partition candidates into non-dominated Pareto fronts.

        Within each front, ties are broken lexicographically, never by a composite scalar.
        Assumes metrics: 'correctness' (higher is better), 'cost' (lower is better).
        """
        if not candidates:
            return []

        remaining = list(candidates)
        fronts: list[list[dict[str, Any]]] = []

        while remaining:
            current_front: list[dict[str, Any]] = []
            next_remaining: list[dict[str, Any]] = []

            for i, p in enumerate(remaining):
                is_dominated = False
                for j, q in enumerate(remaining):
                    if i == j:
                        continue
                    # q dominates p if q has >= correctness and <= cost, and strictly better in at least one
                    p_m = p.get("metrics", p)
                    q_m = q.get("metrics", q)
                    def _to_fraction(val: Any, default: Fraction) -> Fraction:
                        if val is None:
                            return default
                        if isinstance(val, Fraction):
                            return val
                        if isinstance(val, int):
                            return Fraction(val, 1)
                        if isinstance(val, str):
                            return Fraction(val)
                        if isinstance(val, float):
                            return Fraction(str(val))
                        return Fraction(val)

                    p_corr = _to_fraction(p_m.get("correctness"), Fraction(0, 1))
                    p_cost = _to_fraction(p_m.get("cost"), Fraction(1, 1))
                    q_corr = _to_fraction(q_m.get("correctness"), Fraction(0, 1))
                    q_cost = _to_fraction(q_m.get("cost"), Fraction(1, 1))

                    if q_corr >= p_corr and q_cost <= p_cost:
                        if q_corr > p_corr or q_cost < p_cost:
                            is_dominated = True
                            break

                if not is_dominated:
                    current_front.append(p)
                else:
                    next_remaining.append(p)

            # Lexicographic tiebreak within front: correctness desc, cost asc, id asc
            def _tiebreak_key(x: dict[str, Any]) -> tuple[Fraction, Fraction, str]:
                m = x.get("metrics", x)
                corr = _to_fraction(m.get("correctness"), Fraction(0, 1))
                cost = _to_fraction(m.get("cost"), Fraction(1, 1))
                return (-corr, cost, str(x.get("id", "")))

            current_front.sort(key=_tiebreak_key)

            fronts.append(current_front)
            remaining = next_remaining

        return fronts


class ComparativeClaimAuditorV1:
    """Enforces F-RES-09: Comparative benefit claims require holdout split and multiplicity correction."""

    def evaluate_claim(
        self,
        *,
        claim_type: str,
        has_held_out_split: bool,
        multiplicity_correction: str | None = None,
    ) -> bool:
        if claim_type == "COMPARATIVE_BENEFIT":
            if not has_held_out_split:
                raise ValueError("COMPARATIVE_CLAIM_HOLDOUT_REQUIRED: Comparative benefit claims require a held-out evaluation split")
            if not multiplicity_correction:
                raise ValueError("COMPARATIVE_CLAIM_MULTIPLICITY_REQUIRED: Comparative benefit claims require multiplicity correction")
        return True


__all__ = [
    "ExecutionMetricsV1",
    "ParetoFrontSelectorV1",
    "PromptFitnessCalculatorV1",
    "ComparativeClaimAuditorV1",
]
