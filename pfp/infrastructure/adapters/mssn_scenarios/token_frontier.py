"""Executable Demonstration of TokenFrontier Dynamic Logit Masking and Bayesian Conditioning.

Demonstrates:
1. Dynamic grammar support filtering over discrete vocabularies (e.g. Sigma_36).
2. Exact rational base probability assignment and retained mass computation.
3. Bayesian probability conditioning over retained candidate tokens:
       P_constrained(t) = P_base(t) / M_retained
   ensuring exact normalization: sum_{t in Support} P_constrained(t) == 1.
4. Fail-stop boundary refusal on zero retained mass (RefusalCode.ZERO_RETAINED_MASS).
5. Incremental token-by-token decoding trajectory with RFC 8785 canonical receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Sequence

from omega_engine_pfp.domain.mssn_research.grammar.lexical import (
    FrontierCandidate,
    ParserStateId,
    ProbabilityMass,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import Rational
from omega_engine_pfp.domain.mssn_research.grammar.entities import (
    TokenFrontier,
)
from omega_engine_pfp.domain.mssn_research.grammar.errors import (
    GrammarDomainError,
    ZeroRetainedMassError,
)
from omega_engine_pfp.domain.mssn_research.packets.value_objects import (
    RefusalCode,
)


def _canonical_json(data: Any) -> str:
    """Serialize data into RFC 8785 canonical JSON (sorted keys, compact whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_sha256(data: str) -> str:
    """Compute SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MockModelLogits:
    """Simulated raw discrete logits over a vocabulary."""
    vocabulary: tuple[str, ...]
    unnormalized_weights: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.vocabulary) != len(self.unnormalized_weights):
            raise ValueError("Vocabulary and weights must have identical length")

    @property
    def vocabulary_size(self) -> int:
        return len(self.vocabulary)

    def total_weight(self) -> int:
        return sum(self.unnormalized_weights)

    def get_base_rational_probability(self, token_idx: int) -> Rational:
        """Compute exact rational probability for token index."""
        tot = self.total_weight()
        if tot <= 0:
            raise ValueError("Total weight must be positive")
        w = self.unnormalized_weights[token_idx]
        frac = Fraction(w, tot)
        return Rational(frac.numerator, frac.denominator)


def evaluate_token_frontier_step(
    logits: MockModelLogits,
    admitted_token_indices: Sequence[int],
    parser_state_label: str = "state_active",
) -> Result[TokenFrontier, GrammarDomainError]:
    """Evaluate a dynamic token generation step under an active grammar mask.

    1. Computes total retained base probability mass M.
    2. If M == 0, returns Refusal(ZeroRetainedMassError).
    3. Normalizes admitted tokens via Bayes formula:
           p_constrained = p_base / M
    4. Constructs and returns the validated TokenFrontier entity.
    """
    V = logits.vocabulary_size
    cand_indices = sorted(set(admitted_token_indices))

    # Compute base rational probabilities for admitted candidates
    cand_base_fractions: list[tuple[int, Fraction]] = []
    total_retained_fraction = Fraction(0)

    for idx in cand_indices:
        if not (0 <= idx < V):
            return Err(ZeroRetainedMassError(
                code=RefusalCode.WRONG_ARITY,
                message=f"Token index {idx} out of vocabulary range [0, {V})"
            ))
        p_base_rat = logits.get_base_rational_probability(idx)
        p_base_frac = Fraction(p_base_rat.numerator, p_base_rat.denominator)
        cand_base_fractions.append((idx, p_base_frac))
        total_retained_fraction += p_base_frac

    # Invariant: Zero retained mass triggers fail-stop boundary refusal
    if total_retained_fraction == Fraction(0):
        return Refusal(ZeroRetainedMassError(
            code=RefusalCode.ZERO_RETAINED_MASS,
            message="Retained probability mass dropped to zero; zero unconstrained token escapes"
        ))

    retained_mass = ProbabilityMass(Rational(total_retained_fraction.numerator, total_retained_fraction.denominator))

    # Condition probabilities on retained mass
    candidates: list[FrontierCandidate] = []
    p_state = ParserStateId(parser_state_label)

    for idx, p_base_frac in cand_base_fractions:
        p_const_frac = p_base_frac / total_retained_fraction
        cand = FrontierCandidate(
            token_id=idx,
            emitted_bytes=logits.vocabulary[idx].encode("utf-8"),
            parser_state_after=p_state,
            base_probability=Rational(p_base_frac.numerator, p_base_frac.denominator),
            constrained_probability=Rational(p_const_frac.numerator, p_const_frac.denominator),
        )
        candidates.append(cand)

    return TokenFrontier.create(
        vocabulary_size=V,
        candidates=candidates,
        retained_mass=retained_mass,
    )


def run_frontier_scenarios() -> dict[str, Any]:
    """Execute four canonical scenarios demonstrating TokenFrontier behavior."""
    results: dict[str, Any] = {
        "schema": "symbol_game.demo_token_frontier.v1",
        "scenarios": {},
    }

    # Define a toy discrete alphabet representing Sigma_8
    vocab = ("0", "1", "2", "3", "<", ">", "op", "diff")
    weights = (10, 20, 15, 5, 25, 10, 10, 5)  # Sum = 100
    logits = MockModelLogits(vocabulary=vocab, unnormalized_weights=weights)

    # ---------------------------------------------------------
    # Scenario 1: Standard Grammatical Masking (admit digits only)
    # ---------------------------------------------------------
    # Digits "0", "1", "2", "3" -> indices 0, 1, 2, 3
    # Base weights: 10 + 20 + 15 + 5 = 50 / 100 -> M = 1/2
    step1_res = evaluate_token_frontier_step(logits, admitted_token_indices=[0, 1, 2, 3], parser_state_label="parse_digits")
    if not (step1_res.is_ok()):
        raise ValueError(f"Scenario 1 failed: {step1_res}")
    f1 = step1_res.unwrap()
    results["scenarios"]["scenario_1_digits_mask"] = {
        "status": "PASS",
        "vocabulary_size": f1.vocabulary_size,
        "support_width": f1.support_width,
        "masked_token_count": f1.masked_token_count,
        "retained_mass": str(Fraction(f1.retained_mass.mass.numerator, f1.retained_mass.mass.denominator)),
        "candidates": [
            {
                "token": vocab[c.token_id],
                "token_id": c.token_id,
                "base_p": f"{c.base_probability.numerator}/{c.base_probability.denominator}",
                "constrained_p": f"{c.constrained_probability.numerator}/{c.constrained_probability.denominator}",
            }
            for c in f1.candidates
        ],
    }

    # ---------------------------------------------------------
    # Scenario 2: Single-Token Support (Deterministic Collapse)
    # ---------------------------------------------------------
    # Only closing delimiter ">" admitted -> index 5
    # Base weight: 10 / 100 -> M = 1/10 -> Constrained P = 1.0
    step2_res = evaluate_token_frontier_step(logits, admitted_token_indices=[5], parser_state_label="parse_close_delim")
    if not (step2_res.is_ok()):
        raise ValueError(f"Scenario 2 failed: {step2_res}")
    f2 = step2_res.unwrap()
    results["scenarios"]["scenario_2_deterministic_collapse"] = {
        "status": "PASS",
        "support_width": f2.support_width,
        "retained_mass": str(Fraction(f2.retained_mass.mass.numerator, f2.retained_mass.mass.denominator)),
        "constrained_p": f"{f2.candidates[0].constrained_probability.numerator}/{f2.candidates[0].constrained_probability.denominator}",
    }

    # ---------------------------------------------------------
    # Scenario 3: Boundary Refusal (Zero Retained Mass)
    # ---------------------------------------------------------
    # No tokens admitted by active filter -> empty set
    step3_res = evaluate_token_frontier_step(logits, admitted_token_indices=[], parser_state_label="empty_support")
    if not (step3_res.is_refusal()):
        raise ValueError("Scenario 3 expected Refusal")
    if not (isinstance(step3_res, Refusal)):
        raise ValueError('scenario invariant failed')
    err3 = step3_res.refusal
    if not (isinstance(err3, ZeroRetainedMassError)):
        raise ValueError(f"Expected ZeroRetainedMassError, got {err3}")
    results["scenarios"]["scenario_3_zero_retained_mass_refusal"] = {
        "status": "REFUSED_EXPECTED",
        "refusal_code": err3.code.value,
        "message": err3.message,
    }

    # ---------------------------------------------------------
    # Scenario 4: Step-by-Step Trajectory (< op 0 >)
    # ---------------------------------------------------------
    trajectory_steps: list[dict[str, Any]] = []
    # Step A: Expecting opening delimiter '<' (index 4)
    res_a = evaluate_token_frontier_step(logits, [4], parser_state_label="step_0_open")
    if not (res_a.is_ok()):
        raise ValueError('scenario invariant failed')
    trajectory_steps.append({"step": 0, "token": "<", "retained_mass": str(Fraction(res_a.unwrap().retained_mass.mass.numerator, res_a.unwrap().retained_mass.mass.denominator)), "status": "OK"})

    # Step B: Expecting opcode 'op' (index 6) or 'diff' (index 7)
    res_b = evaluate_token_frontier_step(logits, [6, 7], parser_state_label="step_1_opcode")
    if not (res_b.is_ok()):
        raise ValueError('scenario invariant failed')
    trajectory_steps.append({"step": 1, "token": "op", "retained_mass": str(Fraction(res_b.unwrap().retained_mass.mass.numerator, res_b.unwrap().retained_mass.mass.denominator)), "status": "OK"})

    # Step C: Expecting payload digit '0'..'3' (indices 0..3)
    res_c = evaluate_token_frontier_step(logits, [0, 1, 2, 3], parser_state_label="step_2_payload")
    if not (res_c.is_ok()):
        raise ValueError('scenario invariant failed')
    trajectory_steps.append({"step": 2, "token": "0", "retained_mass": str(Fraction(res_c.unwrap().retained_mass.mass.numerator, res_c.unwrap().retained_mass.mass.denominator)), "status": "OK"})

    # Step D: Expecting closing delimiter '>' (index 5)
    res_d = evaluate_token_frontier_step(logits, [5], parser_state_label="step_3_close")
    if not (res_d.is_ok()):
        raise ValueError('scenario invariant failed')
    trajectory_steps.append({"step": 3, "token": ">", "retained_mass": str(Fraction(res_d.unwrap().retained_mass.mass.numerator, res_d.unwrap().retained_mass.mass.denominator)), "status": "OK"})

    results["scenarios"]["scenario_4_packet_trajectory"] = {
        "status": "ILLUSTRATION_ONLY",
        "scope": "scripted token choices; terminal text is not a parsed tower packet",
        "trajectory": trajectory_steps,
        "terminal_packet": "<op0>",
    }

    # Record cryptographic hash chain of execution receipt
    canonical_bytes = _canonical_json(results)
    results["receipt_sha256"] = _compute_sha256(canonical_bytes)
    return results
