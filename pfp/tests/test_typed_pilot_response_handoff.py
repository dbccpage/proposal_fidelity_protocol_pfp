"""Typed pilot handoff rechecks actual raw replies without promoting saved claims."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from pfp.domain.kernel.result import RefusalCode
from pfp.domain.types.pilot_response import PilotResponse
from pfp.domain.types.pilot_spec import PilotSpec
from pfp.domain.types.seed_prompts import SeedPrompt
from pfp.domain.value_objects.identifiers import CheckerIdVO, PilotId, RequestId
from pfp.tests.types.test_pilot_yaml_roundtrip import (
    RESPONSE_YAML,
    SEED_YAML,
    SPEC_YAML,
)
from pfp.use_cases.evaluate_pilot import EvaluatePilotUseCase


def _inputs(raw='{"answer": 2}', *, expected=2, checker="PFP-01-EXACT-LINALG"):
    spec_data = PilotSpec.from_yaml(SPEC_YAML).model_dump()
    spec_data["host_gate"]["checker_id"] = checker
    spec = PilotSpec.model_validate(spec_data)
    seed_data = SeedPrompt.from_yaml(SEED_YAML).model_dump()
    seed_data.update(seed_prompt="Compute the declared result.", expected_outcome={"answer": expected})
    seed = SeedPrompt.model_validate(seed_data)
    response_data = PilotResponse.from_yaml(RESPONSE_YAML).model_dump()
    response_data.update(raw_reply=raw, parsed_json={"answer": 2}, extracted_answer=2, trial_status="PASS")
    response_data["evaluation"].update(checker_id=checker, status="ACCEPTED", expected=2, received=2)
    response_data["receipt"]["evidence"] = "Historical claimed PASS; no current check"
    return spec, seed, PilotResponse.model_validate(response_data)


def test_conversion_keeps_response_but_does_not_import_claimed_verdict():
    spec, seed, response = _inputs()
    pilot = spec.to_aggregate(seed, response)
    assert pilot.trial_status.value == "NOT_RUN"
    assert pilot.evaluation_status.value == "NOT_RUN"
    assert pilot.extracted_answer is None
    assert pilot.execution_receipt_evidence == ""
    assert pilot.response == response
    assert pilot.response is not response
    response.parsed_json["answer"] = 99
    assert pilot.response.parsed_json == {"answer": 2}


@pytest.mark.parametrize("raw", ['{"answer": 2}', '```json\n{"answer": 2}\n```'])
def test_real_typed_raw_candidate_reaches_existing_checker(raw):
    spec, seed, response = _inputs(raw)
    pilot = spec.to_aggregate(seed, response)
    result = EvaluatePilotUseCase().execute(pilot)
    assert result.is_ok, result.error
    checked = result.unwrap()
    assert checked.is_accepted
    assert checked.trial_status.value == "PASS"
    assert checked.extracted_answer == 2
    assert checked.response == response
    assert checked.response.raw_reply == raw
    assert pilot.trial_status.value == "NOT_RUN"


@pytest.mark.parametrize("which", ["seed_pilot", "response_pilot", "response_request", "response_checker"])
def test_conversion_rejects_mismatched_identity(which):
    spec, seed, response = _inputs()
    if which == "seed_pilot":
        seed = seed.model_copy(update={"pilot_id": "other_pilot"})
    elif which == "response_pilot":
        response = response.model_copy(update={"pilot_id": "other_pilot"})
    elif which == "response_request":
        response = response.model_copy(update={"request_id": "other_request"})
    else:
        response = response.model_copy(update={"evaluation": response.evaluation.model_copy(
            update={"checker_id": "PFP-05-EXACT-2X2-DETERMINANT"})})
    with pytest.raises(ValueError, match="INV_PILOT_01"):
        spec.to_aggregate(seed, response)


@pytest.mark.parametrize("field,value", [
    ("pilot_id", PilotId("other_pilot")),
    ("request_id", RequestId("other_request")),
    ("checker_id", CheckerIdVO("PFP-05-EXACT-2X2-DETERMINANT")),
])
def test_evaluation_rechecks_mutable_aggregate_bindings(field, value):
    spec, seed, response = _inputs()
    pilot = spec.to_aggregate(seed, response)
    setattr(pilot, field, value)
    original = deepcopy(pilot)
    result = EvaluatePilotUseCase().execute(pilot)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert "INV_PILOT_01" in result.unwrap_err().message
    assert pilot == original


def test_raw_wrong_answer_overrides_cached_success_and_legacy_dynamic_payload():
    spec, seed, response = _inputs('{"answer": 3}')
    pilot = spec.to_aggregate(seed, response)
    pilot.observations = [SimpleNamespace(extracted_terms={"answer": 2})]
    checked = EvaluatePilotUseCase().execute(pilot).unwrap()
    assert checked.evaluation_status.value == "WRONG_ANSWER"
    assert checked.extracted_answer == 3
    assert checked.response == response
    assert checked.response.extracted_answer == 2
    assert checked.response.evaluation.status.value == "ACCEPTED"


@pytest.mark.parametrize("raw", ['{bad', '{"answer": 3, "answer": 2}', '{"answer": NaN}', 'null'])
def test_invalid_raw_never_falls_back_to_cached_or_dynamic_candidate(raw):
    spec, seed, response = _inputs(raw)
    pilot = spec.to_aggregate(seed, response)
    pilot.observations = [SimpleNamespace(extracted_terms={"answer": 2})]
    checked = EvaluatePilotUseCase().execute(pilot).unwrap()
    assert checked.evaluation_status.value == "MALFORMED"
    assert checked.trial_status.value == "FAILED"
    assert checked.extracted_answer is None
    assert checked.response == response


@pytest.mark.parametrize("raw", [None, "", "  \n"])
def test_absent_raw_response_stays_unchecked(raw):
    spec, seed, response = _inputs(raw)
    pilot = spec.to_aggregate(seed, response)
    pilot.observations = [SimpleNamespace(extracted_terms={"answer": 2})]
    checked = EvaluatePilotUseCase().execute(pilot).unwrap()
    assert checked.evaluation_status.value == "NOT_RUN"
    assert checked.trial_status.value == "NOT_RUN"
    assert checked.extracted_answer is None
    assert checked.response == response


@pytest.mark.parametrize("checker,expected,raw,observed", [
    ("PFP-05-EXACT-2X2-DETERMINANT", 11, '{"det": 11}', {"det": 11}),
    ("PFP-04-EXACT-EPISTEMIC-REFUSAL",
     {"computable": False, "reason": "function f has no declared definition"},
     '{"computable": false, "reason": "Function F has no declared definition"}',
     {"computable": False, "reason": "Function F has no declared definition"}),
])
def test_typed_handoff_preserves_original_checker_representations(checker, expected, raw, observed):
    spec, seed, response = _inputs(raw, checker=checker, expected=expected)
    checked = EvaluatePilotUseCase().execute(spec.to_aggregate(seed, response)).unwrap()
    assert checked.is_accepted
    assert checked.extracted_answer == observed
    assert checked.response == response


def test_no_response_and_batch_keep_public_api():
    spec, seed, response = _inputs()
    pending = spec.to_aggregate(seed)
    assert pending.response is None
    results = EvaluatePilotUseCase().execute_batch([pending, spec.to_aggregate(seed, response)]).unwrap()
    assert results[0].trial_status.value == "NOT_RUN"
    assert results[1].trial_status.value == "PASS"
