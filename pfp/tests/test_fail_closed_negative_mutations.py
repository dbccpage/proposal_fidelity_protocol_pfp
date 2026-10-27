"""Sovereign Test Suite for PFP Multi-Checker Fail-Closed Refusal Behavior.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Claim Hygiene Invariant.

Verifies:
1. Zero False Acceptances: Every single negative mutation payload and perturbed prompt
   token fixture evaluates to non-ACCEPTED (REFUSED, WRONG_ANSWER, MALFORMED, or FALSE_CERTAINTY).
2. Exact Refusal Code Tie-Out: Every fixture triggers the exact expected refusal code
   mandated in negative_mutation_fixtures.yaml across all five checkers:
   - PFP-01-EXACT-LINALG
   - PFP-02-EXACT-PRIMES
   - PFP-03-EXACT-FOL-DEDUCTION
   - PFP-04-EXACT-EPISTEMIC-REFUSAL
   - PFP-05-EXACT-2X2-DETERMINANT
3. Positive Control Grounding: Authentic unperturbed prompts and verified ground-truth payloads
   evaluate to ACCEPTED with null refusal code.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import yaml

from pfp.domain.types import CheckerId
from pfp.domain.types import EvaluationStatus
from pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate
from pfp.domain.types import NegativeMutationFixture
from pfp.domain.kernel.result import RefusalCode

APPLICATION_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_FIXTURES_PATH = (
    APPLICATION_ROOT
    / "domain"
    / "fixtures"
    / "negative_mutation_fixtures.yaml"
)
INFRA_FIXTURES_PATH = (
    APPLICATION_ROOT
    / "infrastructure"
    / "fixtures"
    / "negative_mutation_fixtures.yaml"
)
FIXTURES_PATH = DOMAIN_FIXTURES_PATH if DOMAIN_FIXTURES_PATH.exists() else INFRA_FIXTURES_PATH


def load_negative_fixtures() -> list[NegativeMutationFixture]:
    assert FIXTURES_PATH.exists(), f"Fixtures catalog not found at {FIXTURES_PATH}"
    raw = yaml.safe_load(FIXTURES_PATH.read_text(encoding="utf-8"))
    assert raw["schema"] == "pfp.negative-mutation-fixtures.v1"
    fixtures_data = raw.get("fixtures", [])
    assert len(fixtures_data) > 0, "No fixtures found in catalog"
    return [NegativeMutationFixture.model_validate(f) for f in fixtures_data]


ALL_FIXTURES = load_negative_fixtures()


def test_dual_home_fixtures_parity():
    """Verify negative_mutation_fixtures.yaml is identically present in domain/ and infrastructure/."""
    assert DOMAIN_FIXTURES_PATH.exists(), f"Missing {DOMAIN_FIXTURES_PATH}"
    assert INFRA_FIXTURES_PATH.exists(), f"Missing {INFRA_FIXTURES_PATH}"
    assert DOMAIN_FIXTURES_PATH.read_bytes() == INFRA_FIXTURES_PATH.read_bytes()


def test_fixtures_catalog_coverage():
    """Verify catalog contains test cases for all five checkers and both mutation kinds."""
    assert len(ALL_FIXTURES) >= 20

    checkers_present = {str(f.checker_id.value if isinstance(f.checker_id, CheckerId) else f.checker_id) for f in ALL_FIXTURES}
    expected_checkers = {
        "PFP-01-EXACT-LINALG",
        "PFP-02-EXACT-PRIMES",
        "PFP-03-EXACT-FOL-DEDUCTION",
        "PFP-04-EXACT-EPISTEMIC-REFUSAL",
        "PFP-05-EXACT-2X2-DETERMINANT",
    }
    assert checkers_present == expected_checkers, f"Missing checkers in fixtures: {expected_checkers - checkers_present}"

    # Verify both payload mutations and prompt perturbations are present
    mutation_kinds = {f.mutation_kind for f in ALL_FIXTURES}
    assert "candidate_payload_mutation" in mutation_kinds
    assert "prompt_token_perturbation" in mutation_kinds

    # Verify every checker has at least one prompt token perturbation
    for cid in expected_checkers:
        pt_count = sum(1 for f in ALL_FIXTURES if (str(f.checker_id.value if isinstance(f.checker_id, CheckerId) else f.checker_id) == cid and f.mutation_kind == "prompt_token_perturbation"))
        assert pt_count >= 1, f"Checker {cid} has no prompt token perturbation fixtures"


@pytest.mark.parametrize("fixture", ALL_FIXTURES, ids=[f.fixture_id for f in ALL_FIXTURES])
def test_negative_mutation_fail_closed(fixture: NegativeMutationFixture):
    """FAIL-CLOSED INVARIANT: No negative fixture may EVER evaluate to ACCEPTED."""
    result = FailClosedRefusalGate.evaluate_negative_fixture(fixture)

    # 1. Absolute fail-closed refusal
    assert result.status != EvaluationStatus.ACCEPTED, (
        f"CRITICAL BREACH: Negative fixture {fixture.fixture_id} evaluated to ACCEPTED! "
        f"Description: {fixture.description}"
    )

    # 2. Status match
    assert result.status == fixture.expected_status, (
        f"Status mismatch for {fixture.fixture_id}: expected {fixture.expected_status}, "
        f"got {result.status}. Reason: {result.reason}"
    )

    # 3. Refusal code match
    if fixture.expected_refusal_code is not None:
        assert result.refusal_code is not None, (
            f"Expected refusal code {fixture.expected_refusal_code} for {fixture.fixture_id}, "
            f"but refusal_code was None. Reason: {result.reason}"
        )
        assert result.refusal_code.value == fixture.expected_refusal_code, (
            f"Refusal code mismatch for {fixture.fixture_id}: expected {fixture.expected_refusal_code}, "
            f"got {result.refusal_code.value}. Reason: {result.reason}"
        )


def test_positive_controls_all_five_checkers():
    """Verify authentic unperturbed prompts and ground truth payloads pass as ACCEPTED."""
    # 1. PFP-01 Linear Algebra
    res1 = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id=CheckerId.EXACT_LINALG,
        expected_answer=3,
        payload={"answer": 3},
    )
    assert res1.status == EvaluationStatus.ACCEPTED
    assert res1.refusal_code is None
    assert res1.extracted_answer == 3

    # 2. PFP-02 Primes
    res2 = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id=CheckerId.EXACT_PRIMES,
        expected_answer=[2, 3, 5, 7, 11, 13, 17, 19],
        payload={"primes": [2, 3, 5, 7, 11, 13, 17, 19]},
    )
    assert res2.status == EvaluationStatus.ACCEPTED
    assert res2.refusal_code is None
    assert res2.extracted_answer == [2, 3, 5, 7, 11, 13, 17, 19]

    # 3. PFP-03 First-Order Logic
    res3 = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id=CheckerId.EXACT_FOL_DEDUCTION,
        expected_answer={"verdict": "YES", "premise_count": 2},
        payload={"verdict": "YES", "premise_count": 2},
    )
    assert res3.status == EvaluationStatus.ACCEPTED
    assert res3.refusal_code is None
    assert res3.extracted_answer == {"verdict": "YES", "premise_count": 2}

    # 4. PFP-04 Epistemic Refusal
    res4 = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id=CheckerId.EXACT_EPISTEMIC_REFUSAL,
        expected_answer={"computable": False, "reason": "function f has no declared definition"},
        payload={"computable": False, "reason": "function f has no declared definition"},
    )
    assert res4.status == EvaluationStatus.ACCEPTED
    assert res4.refusal_code is None
    assert res4.extracted_answer == {"computable": False, "reason": "function f has no declared definition"}

    # 5. PFP-05 Determinant
    res5 = FailClosedRefusalGate.evaluate_candidate_payload(
        checker_id=CheckerId.EXACT_2X2_DETERMINANT,
        expected_answer={"det": 1},
        payload={"det": 1},
    )
    assert res5.status == EvaluationStatus.ACCEPTED
    assert res5.refusal_code is None
    assert res5.extracted_answer == {"det": 1}


def test_claim_hygiene_firewall_blocks_hype_tokens():
    """Verify that forbidden promotional tokens in prompt text are immediately refused."""
    for word in ("proves", "guarantees", "universal", "flawless", "obviously", "clearly"):
        prompt = f"Evaluate this problem. It {word} the result without doubt."
        audit = FailClosedRefusalGate.audit_prompt_tokens(prompt, CheckerId.EXACT_LINALG)
        assert audit is not None, f"Prompt with hype token '{word}' was not caught by firewall"
        status, code, _ = audit
        assert status == EvaluationStatus.REFUSED
        assert code == RefusalCode.POLICY_VIOLATION


def test_syntax_delimiter_firewall_blocks_unclosed_brackets():
    """Verify that unclosed syntax delimiters trigger SYNTAX_VIOLATION."""
    # Unclosed angle brackets
    prompt1 = "solve< eq1<add<x, 2>, 5> "
    audit1 = FailClosedRefusalGate.audit_prompt_tokens(prompt1, CheckerId.EXACT_LINALG)
    assert audit1 is not None
    assert audit1[0] == EvaluationStatus.REFUSED
    assert audit1[1] == RefusalCode.SYNTAX_VIOLATION

    # Unclosed wire format <<...
    prompt2 = "Boundary dialect mss-boundary-v1. <<p><v1><<q><s0>><<d><s1>"
    audit2 = FailClosedRefusalGate.audit_prompt_tokens(prompt2, CheckerId.EXACT_EPISTEMIC_REFUSAL)
    assert audit2 is not None
    assert audit2[0] == EvaluationStatus.REFUSED
    assert audit2[1] == RefusalCode.SYNTAX_VIOLATION
