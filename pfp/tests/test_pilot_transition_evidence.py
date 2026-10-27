"""Pilot transitions retain observations and reject invalid updates atomically."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from pfp.domain.value_objects.identifiers import CheckerIdVO
from pfp.domain.value_objects.taxonomy import EvaluationStatusVO, TrialStatusVO
from pfp.tests.test_pilot_use_cases import _make_sample_pilot
from pfp.use_cases.evaluate_pilot import EvaluatePilotUseCase


def _pilot():
    return replace(
        _make_sample_pilot(), expected_answer=2, extracted_answer=None,
        evaluation_status=EvaluationStatusVO("NOT_RUN"), execution_receipt_evidence="",
    )


@pytest.mark.parametrize("status", ["PASS", "COMPLETED"])
@pytest.mark.parametrize("evidence", ["", " \n"])
def test_terminal_transition_cannot_invent_execution_evidence(status, evidence):
    pilot = _pilot()
    original = deepcopy(pilot)
    with pytest.raises(ValueError, match="INV_PILOT_02"):
        pilot.with_transition(trial_status=TrialStatusVO(status), execution_receipt_evidence=evidence)
    assert pilot == original
    with pytest.raises(ValueError, match="INV_PILOT_02"):
        replace(pilot, trial_status=TrialStatusVO(status), execution_receipt_evidence=evidence)


@pytest.mark.parametrize("expected", [2, None])
def test_acceptance_cannot_invent_missing_observation(expected):
    pilot = replace(_pilot(), expected_answer=expected)
    with pytest.raises(ValueError, match="INV_PILOT_03"):
        pilot.with_transition(evaluation_status=EvaluationStatusVO("ACCEPTED"))
    assert pilot.extracted_answer is None
    assert not pilot.is_accepted


def test_rejected_evaluation_leaves_original_valid():
    pilot = _pilot()
    original = deepcopy(pilot)
    with pytest.raises(ValueError, match="INV_PILOT_03"):
        pilot.evaluate_result(3, EvaluationStatusVO("ACCEPTED"))
    assert pilot == original
    pilot.validate_invariants()
    assert pilot.evaluate_result(2, EvaluationStatusVO("ACCEPTED")) is None
    assert pilot.extracted_answer == 2
    assert pilot.is_accepted


def test_rejected_execution_update_leaves_original_valid():
    pilot = _pilot()
    original = deepcopy(pilot)
    with pytest.raises(AttributeError):
        pilot.record_execution("actual evidence", trial_status=object())
    assert pilot == original
    assert pilot.record_execution("actual evidence") is None
    assert pilot.is_completed
    assert pilot.execution_receipt_evidence == "actual evidence"


@pytest.mark.parametrize("evidence_key", ["execution_receipt_evidence", "raw_response", "reason"])
def test_explicit_successful_copy_transition_and_evidence_aliases(evidence_key):
    pilot = _pilot()
    observed = [2, 3]
    pilot.expected_answer = [2, 3]
    updated = pilot.with_transition(
        trial_status=TrialStatusVO("PASS"), evaluation_status=EvaluationStatusVO("ACCEPTED"),
        extracted_answer=observed, **{evidence_key: "original observed evidence"},
    )
    assert updated is not pilot
    assert updated.pilot_id == pilot.pilot_id
    assert updated.extracted_answer is observed
    assert updated.expected_answer == pilot.expected_answer
    assert updated.expected_answer is not pilot.expected_answer
    assert updated.execution_receipt_evidence == "original observed evidence"
    assert updated.with_transition().extracted_answer == observed
    assert pilot.trial_status.value == "NOT_RUN"
    assert pilot.extracted_answer is None


def test_omitted_observation_retains_but_explicit_none_clears():
    pilot = replace(_pilot(), extracted_answer=3, evaluation_status=EvaluationStatusVO("WRONG_ANSWER"))
    assert pilot.with_transition().extracted_answer == 3
    cleared = pilot.with_transition(extracted_answer=None)
    assert cleared.extracted_answer is None
    assert pilot.extracted_answer == 3


def _with_payload(payload, *, expected=2, checker="PFP-01-EXACT-LINALG"):
    pilot = replace(_pilot(), expected_answer=expected, checker_id=CheckerIdVO(checker))
    pilot.observations = [SimpleNamespace(extracted_terms=payload)]
    return pilot


def test_actual_accepted_checker_observation_is_retained_not_expected_object():
    observed = [2, 3, 5]
    expected = list(observed)
    pilot = _with_payload({"primes": observed}, expected=expected, checker="PFP-02-EXACT-PRIMES")
    result = EvaluatePilotUseCase().execute(pilot)
    assert result.is_ok
    accepted = result.unwrap()
    assert accepted.trial_status.value == "PASS"
    assert accepted.is_accepted
    assert accepted.extracted_answer is observed
    assert accepted.extracted_answer is not expected
    assert accepted.execution_receipt_evidence == "Prime list matches exact integer sequence"
    assert pilot.extracted_answer is None


@pytest.mark.parametrize("payload,observation,status", [
    ({"answer": 3}, 3, "WRONG_ANSWER"),
    ({"verified": True}, None, "FALSE_CERTAINTY"),
])
def test_actual_rejection_replaces_stale_observation(payload, observation, status):
    pilot = _with_payload(payload)
    pilot.extracted_answer = 2
    pilot.evaluation_status = EvaluationStatusVO("ACCEPTED")
    original = deepcopy(pilot)
    result = EvaluatePilotUseCase().execute(pilot)
    assert result.is_ok
    rejected = result.unwrap()
    assert rejected.trial_status.value == "FAILED"
    assert rejected.evaluation_status.value == status
    assert rejected.extracted_answer == observation
    assert pilot == original


def test_prompt_refusal_does_not_keep_stale_checked_answer():
    pilot = _with_payload({"answer": 2})
    pilot.seed_prompt = "This obviously solves the problem"
    pilot.extracted_answer = 2
    result = EvaluatePilotUseCase().execute(pilot).unwrap()
    assert result.trial_status.value == "REFUSED"
    assert result.extracted_answer is None
    assert pilot.extracted_answer == 2


@pytest.mark.parametrize("checker,expected,payload,observed", [
    ("PFP-05-EXACT-2X2-DETERMINANT", 1, {"answer": 1}, {"det": 1}),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL",
     {"computable": False, "reason": "function f has no declared definition"},
     {"computable": False, "reason": "  Function F has no declared definition  "},
     {"computable": False, "reason": "Function F has no declared definition"}),
])
def test_checker_defined_equivalence_preserves_actual_observation(checker, expected, payload, observed):
    pilot = _with_payload(payload, checker=checker, expected=expected)
    result = EvaluatePilotUseCase().execute(pilot)
    assert result.is_ok, result.error
    accepted = result.unwrap()
    assert accepted.is_accepted
    assert accepted.trial_status.value == "PASS"
    assert accepted.extracted_answer == observed
    assert accepted.extracted_answer != expected
    assert accepted.expected_answer == expected
    accepted.validate_invariants()


@pytest.mark.parametrize("checker,expected,wrong", [
    ("PFP-05-EXACT-2X2-DETERMINANT", 1, {"det": 2}),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL",
     {"computable": False, "reason": "function f has no declared definition"},
     {"computable": False, "reason": "different missing definition"}),
])
def test_checker_equivalence_cannot_accept_wrong_value(checker, expected, wrong):
    pilot = _with_payload(wrong, checker=checker, expected=expected)
    original = deepcopy(pilot)
    with pytest.raises(ValueError, match="INV_PILOT_03"):
        pilot.evaluate_result(wrong, EvaluationStatusVO("ACCEPTED"))
    assert pilot == original
    result = EvaluatePilotUseCase().execute(pilot).unwrap()
    assert not result.is_accepted
    assert result.extracted_answer == wrong


def test_candidate_wrapper_cannot_be_relabelled_as_extracted_observation():
    pilot = _pilot()
    with pytest.raises(ValueError, match="INV_PILOT_03"):
        pilot.evaluate_result({"answer": 2}, EvaluationStatusVO("ACCEPTED"))
    assert pilot.extracted_answer is None
    assert not pilot.is_accepted
