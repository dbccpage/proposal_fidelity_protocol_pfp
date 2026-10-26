"""Tests for Finding F2 (Authentic Digest Validation) and F3 (Branch Metrics and Total Reducer).

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic (fractions.Fraction).
"""

import json
from fractions import Fraction

from omega_engine_prompt_civilization.domain.causal_witness import seal_causal_witness
from omega_engine_prompt_civilization.use_cases.fitness import (
    PromptFitnessCalculatorV1,
    is_valid_sealed_digest,
)


def test_f2_authentic_sealed_digest_validation() -> None:
    calc = PromptFitnessCalculatorV1()

    # A caller dict is not checker evidence, even with a well-formed digest.
    valid_receipt = {
        "obligation_id": "ob_integral_01",
        "sealed_receipt_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "verifier_status": "VERIFIED_EXACT",
    }
    assert calc.extract_obligation_success_credit("ob_integral_01", valid_receipt) == 0
    # A self-seal did not run a checker. The body string and the caller Boolean earn nothing.
    sealed = seal_causal_witness(
        {"obligation_id": "ob_integral_01", "verifier_status": "VERIFIED_EXACT"}
    )
    assert calc.extract_obligation_success_credit("ob_integral_01", sealed) == 0
    assert calc.compute_execution_metrics({"payload": "answer", "is_exact_verified": True}).success_credit == 0
    assert calc.compute_execution_metrics(
        {"payload": "answer", "exact_verifier_receipt": {"status": "ok"}}
    ).success_credit == 0

    class _CallerStatus:
        verifier_status = "VERIFIED_EXACT"
        status = "COMPLETED"

    assert calc.extract_success_credit(_CallerStatus()) == 0

    # 2. Fake / dummy string "not-a-digest" -> MUST EARN ZERO CREDIT
    fake_receipt = {
        "obligation_id": "ob_integral_01",
        "sealed_receipt_digest": "not-a-digest",
        "verifier_status": "VERIFIED_EXACT",
    }
    assert calc.extract_obligation_success_credit("ob_integral_01", fake_receipt) == 0

    # 3. Forged or stale receipt -> MUST EARN ZERO CREDIT
    stale_receipt = {
        "obligation_id": "ob_integral_01",
        "sealed_receipt_digest": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "verifier_status": "VERIFIED_EXACT",
        "is_stale": True,
    }
    assert calc.extract_obligation_success_credit("ob_integral_01", stale_receipt) == 0

    # 4. Empty or missing digest -> MUST EARN ZERO CREDIT
    unsealed_receipt = {
        "obligation_id": "ob_integral_01",
        "verifier_status": "VERIFIED_EXACT",
    }
    assert calc.extract_obligation_success_credit("ob_integral_01", unsealed_receipt) == 0

    short_receipt = {
        "obligation_id": "ob_integral_01",
        "sealed_receipt_digest": "sha256:abcd",
        "verifier_status": "VERIFIED_EXACT",
    }
    assert calc.extract_obligation_success_credit("ob_integral_01", short_receipt) == 0
    bare_hex = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    assert is_valid_sealed_digest(bare_hex) is False


def test_fitness_uses_actual_bound_checker_and_rejects_changed_candidate():
    from omega_engine_woland.domain.evidence import CheckerVerdict
    from omega_engine_woland.domain.models import SymbolGameRequestV1
    from omega_engine_woland.infrastructure.symbol_game_checker import SymbolGameCandidateChecker

    case = {"challenge": "c011", "nodes": ["a", "b"], "edges": [["a", "b"]], "claims": {"a->b": "1/10"}}
    solution = {"status": "SOLVED", "phi1": "0", "potential": {"a": "0", "b": "1/10"}, "repair": {}, "dual": {}}
    calc = PromptFitnessCalculatorV1(candidate_checker=SymbolGameCandidateChecker(SymbolGameRequestV1(json.dumps(case))))
    check = calc.check_candidate(run_key="exact-task", objective="check C011", candidate_id="candidate", candidate_bytes=json.dumps(solution).encode(), carrier_context=None).unwrap()
    assert check.verdict is CheckerVerdict.ACCEPTED
    assert calc.checked_success_credit(check) == 1
    sealed_after_check = seal_causal_witness(
        {"obligation_id": "exact-task", "verifier_status": "VERIFIED_EXACT"}
    )
    assert calc.extract_obligation_success_credit("exact-task", sealed_after_check) == 0
    assert calc.compute_execution_metrics({"payload": "answer", "is_exact_verified": True}).success_credit == 0
    changed = calc.check_candidate(run_key="exact-task", objective="check C011", candidate_id="candidate", candidate_bytes=json.dumps({**solution, "phi1": "1"}).encode(), carrier_context=None).unwrap()
    assert changed.verdict is CheckerVerdict.REJECTED
    assert calc.checked_success_credit(changed) == 0
    foreign = PromptFitnessCalculatorV1()
    assert foreign.checked_success_credit(check) == 0
    assert len(calc.observed_checks) == 2

    class ReplayedChecker:
        def check_candidate(self, **kwargs):
            from omega_engine_operations.domain.rop.result import Ok
            return Ok(check)

    stale = PromptFitnessCalculatorV1(candidate_checker=ReplayedChecker())
    replayed = stale.check_candidate(
        run_key="different-task", objective="check C011", candidate_id="candidate",
        candidate_bytes=json.dumps(solution).encode(), carrier_context=None,
    )
    assert replayed.is_err
    assert replayed.unwrap_err().code == "CHECKER_EVIDENCE_MISMATCH"
    assert stale.observed_checks == ()


def test_f3_true_denominator_completion_rate() -> None:
    calc = PromptFitnessCalculatorV1()

    # 1 pass out of 100 assigned tasks (99 refusals):
    # Conditional rate S / (S + F) was 1 / (1 + 0) = 1 (100% inflated!)
    # True assigned completion rate S / N_assigned is 1 / 100
    rate = calc.completion_rate(passes=1, n_assigned=100)
    assert rate == Fraction(1, 100)

    # 0 assigned -> None
    assert calc.completion_rate(passes=0, n_assigned=0) is None


def test_f3_total_selected_attempt_outcome_table() -> None:
    calc = PromptFitnessCalculatorV1()

    # Priority 1: Any TaskFail -> TaskFail
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "TaskFail"], "AllowedTask"
        )
        == "TaskFail"
    )

    # Priority 2: Otherwise any InvalidRefusal -> InvalidRefusal
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "InvalidRefusal"], "AllowedTask"
        )
        == "InvalidRefusal"
    )

    # Priority 3: Otherwise any InfrastructureError -> InfrastructureError
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "InfrastructureError"], "AllowedTask"
        )
        == "InfrastructureError"
    )

    # Priority 4: Otherwise any NotMeasured -> NotMeasured
    # CRITICAL F3 invariant: Early ValidRefusal with unexecuted required check (NotMeasured)
    # MUST evaluate to NotMeasured, preventing early refusal from hiding incompleteness!
    assert (
        calc.reduce_selected_attempt_outcome(
            ["ValidRefusal", "NotMeasured"],
            "RefusalRequired",
            root_outcome="ValidRefusal",
        )
        == "NotMeasured"
    )

    # Priority 5: Otherwise any Inconclusive -> Inconclusive
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "Inconclusive"], "AllowedTask"
        )
        == "Inconclusive"
    )

    # Priority 6: Otherwise AllowedTask with any ValidRefusal -> ValidRefusal (no solved-task credit)
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "ValidRefusal"], "AllowedTask"
        )
        == "ValidRefusal"
    )

    # Priority 7: Otherwise AllowedTask (all mandatory TaskPass) -> TaskPass
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass", "TaskPass"], "AllowedTask"
        )
        == "TaskPass"
    )

    # Priority 8: Otherwise RefusalRequired and root is ValidRefusal -> ValidRefusal
    assert (
        calc.reduce_selected_attempt_outcome(
            ["ValidRefusal"], "RefusalRequired", root_outcome="ValidRefusal"
        )
        == "ValidRefusal"
    )

    # Priority 9: Otherwise RefusalRequired (root is TaskPass without required refusal) -> InvalidRefusal
    assert (
        calc.reduce_selected_attempt_outcome(
            ["TaskPass"], "RefusalRequired", root_outcome="TaskPass"
        )
        == "InvalidRefusal"
    )
