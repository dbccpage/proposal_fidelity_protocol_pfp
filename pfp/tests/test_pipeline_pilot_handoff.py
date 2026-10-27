"""Pilot entrypoints share current inputs without borrowing prior answer acceptance."""

import json
from copy import deepcopy

import pytest

from pfp.domain.kernel.result import RefusalCode
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.tests.test_canonical_stage_execution import Host, ObservingProvider
from pfp.tests.test_pilot_use_cases import _make_sample_pilot
from pfp.tests.test_typed_pilot_response_handoff import _inputs
from pfp.use_cases.evaluate_pilot import EvaluatePilotUseCase
from pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase


class StoppingHost(Host):
    def verify(self, demo_id, prior_responses):
        return super().verify(demo_id, prior_responses).model_copy(update={"should_continue": False})


def _pipeline(host):
    provider = ObservingProvider()
    storage = PfpFileSystemStorageAdapter()
    return ExecuteStagePipelineUseCase(storage, provider, catalog=storage, host_verifier=host), provider


@pytest.mark.parametrize("host,count,trial", [(Host(), 11, "PASS"), (StoppingHost(), 5, "NOT_RUN")])
def test_pilot_entrypoints_share_seed_prompts_and_clear_prior_acceptance(host, count, trial):
    pilot = _make_sample_pilot()
    pilot.seed_prompt = "Preserve <x> exactly.\nSecond line π"
    original = deepcopy(pilot)
    direct, direct_provider = _pipeline(host)
    aggregate, aggregate_provider = _pipeline(host)
    receipt = direct.run_for_pilot(pilot).unwrap()
    updated = aggregate.execute_pilot(pilot).unwrap()
    assert [packet.model_dump() for packet in direct_provider.packets] == [
        packet.model_dump() for packet in aggregate_provider.packets
    ]
    assert json.loads(direct_provider.packets[0].user)["original_seed"] == {
        "pilot_id": pilot.pilot_id.value,
        "seed_prompt": pilot.seed_prompt,
        "checker_id": pilot.checker_id.value,
    }
    assert receipt.completed_stages == tuple(range(1, count + 1))
    assert receipt.all_stages_passed is (count == 11)
    assert updated.trial_status.value == trial
    assert updated.completed_stages_count.value == count
    assert updated.evaluation_status.value == "NOT_RUN"
    assert updated.extracted_answer is None
    assert updated.pilot_id == pilot.pilot_id
    assert updated is not pilot
    assert pilot == original


def test_fresh_prompt_is_used_without_sending_private_expected_answer():
    use_case, provider = _pipeline(Host())
    pilot = _make_sample_pilot()
    private_answer = {"host_only_answer": [11, 17]}
    pilot.expected_answer = deepcopy(private_answer)
    pilot.extracted_answer = deepcopy(private_answer)
    pilot.seed_prompt = "Current task, with the original spacing.  \n"
    pilot.observations = [{"extracted_terms": "prior observed answer"}]
    pilot.execution_receipt = {"response_payload": "prior candidate"}
    original = deepcopy(pilot)
    updated = use_case.execute_pilot(pilot).unwrap()
    assert all("host_only_answer" not in packet.user for packet in provider.packets)
    assert all(json.loads(packet.user)["original_seed"]["seed_prompt"] == pilot.seed_prompt
               for packet in provider.packets)
    assert updated.expected_answer == private_answer
    assert not hasattr(updated, "observations")
    assert not hasattr(updated, "execution_receipt")
    updated.expected_answer["host_only_answer"].append(19)
    assert pilot == original
    assert pilot.expected_answer == private_answer
    assert pilot.observations == original.observations
    assert pilot.execution_receipt == original.execution_receipt


@pytest.mark.parametrize("method", ["execute_pilot", "run_for_pilot"])
def test_non_pilot_refuses_without_dispatch(method):
    use_case, provider = _pipeline(Host())
    result = getattr(use_case, method)(object())
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.TYPING_VIOLATION
    assert not provider.packets


@pytest.mark.parametrize("method", ["execute_pilot", "run_for_pilot"])
def test_missing_host_refusal_propagates_and_keeps_original_pilot(method):
    use_case, provider = _pipeline(None)
    pilot = _make_sample_pilot()
    original = deepcopy(pilot)
    result = getattr(use_case, method)(pilot)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert result.unwrap_err().stage == 5
    assert [packet.stage for packet in provider.packets] == [1, 2, 3, 4]
    assert pilot == original


@pytest.mark.parametrize("method", ["execute_pilot", "run_for_pilot"])
def test_unknown_current_target_refuses_before_dispatch(method):
    use_case, provider = _pipeline(Host())
    pilot = _make_sample_pilot(target="unregistered-current-target")
    original = deepcopy(pilot)
    result = getattr(use_case, method)(pilot)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.UNKNOWN_DEMO
    assert not provider.packets
    assert pilot == original


@pytest.mark.parametrize("host,trial", [(Host(), "PASS"), (StoppingHost(), "NOT_RUN")])
def test_new_pipeline_cannot_regrade_the_original_typed_response(host, trial):
    spec, seed, response = _inputs()
    evaluator = EvaluatePilotUseCase()
    original = evaluator.execute(spec.to_aggregate(seed, response)).unwrap()
    snapshot = deepcopy(original)
    assert original.is_accepted
    use_case, _ = _pipeline(host)
    current = use_case.execute_pilot(original).unwrap()
    assert current.trial_status.value == trial
    assert current.evaluation_status.value == "NOT_RUN"
    assert current.extracted_answer is None
    evaluated = evaluator.execute(current).unwrap()
    assert evaluated.evaluation_status.value == "NOT_RUN"
    assert evaluated.extracted_answer is None
    assert current.response is None
    assert original == snapshot
    assert original.response.raw_reply == response.raw_reply
    checked_original = evaluator.execute(original).unwrap()
    assert checked_original.is_accepted
    assert checked_original.extracted_answer == 2
    assert checked_original.response == response


def test_failed_new_pipeline_preserves_original_typed_response():
    spec, seed, response = _inputs()
    original = spec.to_aggregate(seed, response)
    snapshot = deepcopy(original)
    use_case, _ = _pipeline(None)
    result = use_case.execute_pilot(original)
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert original == snapshot
    assert original.response == response
    assert EvaluatePilotUseCase().execute(original).unwrap().is_accepted
