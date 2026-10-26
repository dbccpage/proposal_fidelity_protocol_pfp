"""Stage `requires` lists form a dependency graph, and a run may be a closed subset.

Stage 11 (evidence plan) is a stage no later stage requires, and stage 9 (receipt) does not
require stage 8 (selection), so both may be left out of a run. A VERIFIED terminal still needs
admission, the model turns before the verdict, the host verdict, the adversary, its host
replay and the receipt. Without a `requires` map the runner keeps the prefix rule.

AuthorityEffect: None.
"""

import json
import re

import pytest
from pydantic import ValidationError

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPipelineFailure, PfpPipelineStep
from omega_engine_pfp.domain.kernel.result import RefusalCode
from omega_engine_pfp.domain.stages.host_stages import (
    admit_record,
    hand_off_record,
    receipt_record,
    selection_record,
)
from omega_engine_pfp.domain.stages.stages import (
    ChallengeReplay,
    ControllerStageRef,
    ReplayOutcome,
    Stage5Response,
    WitnessReplay,
    requires_problem,
    stage_subset_problem,
)
from omega_engine_pfp.infrastructure.providers import OfflineDeterministicPfpProvider
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.use_cases.execute_stage_pipeline import ExecuteStagePipelineUseCase
from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

STORAGE = PfpFileSystemStorageAdapter()
CONTROLLER = STORAGE.load_stage_controller()
REQUIRES = CONTROLLER.requires_by_stage()
ALL = tuple(range(1, 12))
WITHOUT_PLAN = tuple(range(1, 11))
WITHOUT_SELECTION = (1, 2, 3, 4, 5, 6, 7, 9, 10, 11)
DECLARATION = {"grammar": "g", "equality_test": "e", "coefficient_profile": "c"}
RULES = STORAGE.load_stage_file(9).obligation_rules
ROUTING = STORAGE.load_terminal_routing()


def test_declared_graph():
    assert REQUIRES == {1: [], 2: [1], 3: [1, 2], 4: [2, 3], 5: [2, 4], 6: [2, 4, 5],
                        7: [4, 5, 6], 8: [5, 7], 9: [1, 5, 7], 10: [9], 11: [9]}
    for stage in ALL:
        assert STORAGE.load_stage_file(stage).requires == REQUIRES[stage]


@pytest.mark.parametrize("stage,requires,message", [
    (3, [2, 1], "sorted and distinct"),
    (3, [1, 1, 2], "sorted and distinct"),
    (4, [2, 4], "earlier stages only"),
    (2, [], "at least one earlier stage"),
    (5, [1, 2, 3], r"include \[4\]"),
    (6, [2, 4], r"include \[5\]"),
    (7, [4, 5], r"include \[6\]"),
    (8, [5], r"include \[7\]"),
    (9, [1, 5], r"include \[7\]"),
    (11, [1], r"include \[9\]"),
])
def test_requires_problems_are_named(stage, requires, message):
    problem = requires_problem(stage, requires)
    assert problem is not None and re.search(message, problem)
    ref = next(item for item in CONTROLLER.stages if item.stage == stage)
    with pytest.raises(ValidationError):
        ControllerStageRef(stage=stage, name=ref.name, executor=ref.executor, seat=ref.seat, requires=requires)


@pytest.mark.parametrize("stages,problem", [
    (ALL, None),
    (WITHOUT_PLAN, None),
    (WITHOUT_SELECTION, None),
    ((1, 2, 3, 4), None),
    ((1, 2, 3, 5), "Stage 5 requires stages [4]"),
    ((2, 3, 4), "start with stage 1"),
    ((1, 3, 2), "strictly increasing"),
    ((1, 2, 3, 4, 5, 6, 8), "Stage 8 requires stages [7]"),
    ((1, 2, 3, 4, 5, 6, 7, 10), "Stage 10 requires stages [9]"),
    ((1, 12), "known stage numbers"),
])
def test_subsets_must_be_closed_under_requires(stages, problem):
    found = stage_subset_problem(stages, REQUIRES)
    assert (found is None) if problem is None else (problem in found)


def _replay(checked):
    witnesses = (WitnessReplay(index=0, candidate_id="c", expected_accept=False, host_accepted=False,
                               same_as_candidate=False, outcome=ReplayOutcome.CONTROL),) if checked else ()
    return ChallengeReplay(demo_id="d", stage=6, witnesses=witnesses).model_dump(mode="json")


class Port:
    """Fake port: model turns are bare, host stages use the real host rules."""

    def __init__(self, checked=True):
        self.calls = []
        self.checked = checked

    def execute_model_stage(self, stage, prior):
        self.calls.append(stage)
        assert set(REQUIRES[stage]) <= set(prior)
        data = {"stage": stage, "demo_id": "d", "authority_effect": "None"}
        if stage == 2:
            data["candidates"] = [{"candidate_id": "c"}]
        if stage == 4:
            data.update(candidate_id="c", candidate={})
        if stage == 6:
            data["challenges"] = []
        return PfpPipelineStep(data, stage != 11)

    def execute_host_stage(self, stage, prior):
        self.calls.append(stage)
        assert set(REQUIRES[stage]) <= set(prior)
        if stage == 1:
            data = admit_record("d", DECLARATION)
        elif stage == 5:
            data = {"stage": 5, "demo_id": "d", "host_verdict": "PASS", "exact_checks_passed": True,
                    "surviving_candidates": ["c"]}
        elif stage == 7:
            data = {"stage": 7, "demo_id": "d", "host_replay": _replay(self.checked)}
        elif stage == 8:
            data = selection_record("d", prior)
        elif stage == 9:
            data = receipt_record("d", prior, RULES)
        else:
            data = hand_off_record("d", prior[9], ROUTING)
        return PfpPipelineStep(data, data.get("status", "admit") == "admit")


def test_the_full_run_verifies_when_the_adversary_was_checked():
    port = Port()
    run = RunPfpPipelineUseCase().execute(ALL, port, REQUIRES)
    # Stage 11 is recorded as skipped: the receipt is VERIFIED, so it is not diagnostic only.
    assert port.calls == list(WITHOUT_PLAN)
    assert run.stage_responses[11]["skipped"] == "NOT_DIAGNOSTIC_ONLY"
    assert run.terminal_status == "VERIFIED" and run.all_stages_passed is True
    assert run.stage_responses[8]["selected_candidate_id"] == "c"
    assert run.stage_responses[10]["routing_terminal"] == ROUTING["Verified"]
    assert run.stage_responses[10]["authorized_by"] is None


def test_an_unchecked_adversary_leaves_a_residual_and_asks_for_an_evidence_plan():
    port = Port(checked=False)
    run = RunPfpPipelineUseCase().execute(ALL, port, REQUIRES)
    assert port.calls == list(ALL)
    assert run.terminal_status == "VERIFIED_WITH_RESIDUALS" and run.all_stages_passed is True
    assert [item["code"] for item in run.stage_responses[9]["remaining_obligations"]] == [
        "ADVERSARY_CHECKED_NOTHING"]


@pytest.mark.parametrize("stages", [WITHOUT_PLAN, WITHOUT_SELECTION])
def test_skipping_a_stage_nothing_needs_still_verifies(stages):
    port = Port()
    run = RunPfpPipelineUseCase().execute(stages, port, REQUIRES)
    assert run.completed_stages == stages
    assert run.terminal_status == "VERIFIED" and run.all_stages_passed is True


def test_a_subset_without_the_host_stage_is_blocked():
    run = RunPfpPipelineUseCase().execute((1, 2, 3, 4), Port(), REQUIRES)
    assert run.terminal_status == "BLOCKED_BY_EVIDENCE"
    assert run.all_stages_passed is False


def test_a_subset_without_the_receipt_is_not_verified():
    run = RunPfpPipelineUseCase().execute((1, 2, 3, 4, 5, 6, 7), Port(), REQUIRES)
    assert run.terminal_status == "VERIFIED_WITH_RESIDUALS"
    assert run.all_stages_passed is False


def test_an_unclosed_subset_is_refused_before_any_stage_runs():
    port = Port()
    with pytest.raises(PfpPipelineFailure) as error:
        RunPfpPipelineUseCase().execute((1, 2, 3, 5, 6, 7, 9), port, REQUIRES)
    assert error.value.code == "UNKNOWN_STAGE" and port.calls == []


def test_without_a_requires_map_only_prefixes_run():
    with pytest.raises(PfpPipelineFailure, match="contiguous PFP prefix"):
        RunPfpPipelineUseCase().execute(WITHOUT_SELECTION, Port())


def test_a_receipt_that_disagrees_with_host_facts_is_refused():
    class Lying(Port):
        def execute_host_stage(self, stage, prior):
            step = super().execute_host_stage(stage, prior)
            if stage == 9:
                return PfpPipelineStep({**step.data, "terminal": "VERIFIED", "remaining_obligations": []}, True)
            return step

    with pytest.raises(PfpPipelineFailure, match="RECEIPT_DOES_NOT_MATCH_HOST_FACTS"):
        RunPfpPipelineUseCase().execute(WITHOUT_PLAN, Lying(checked=False), REQUIRES)


class Host:
    def verify(self, demo_id, prior_responses):
        return Stage5Response(demo_id=demo_id, should_continue=True, host_verdict="PASS",
                              exact_checks_passed=True, surviving_candidates=[prior_responses[4]["candidate_id"]])

    def verify_challenges(self, demo_id, stage, items, prior_responses):
        witnesses = tuple(
            WitnessReplay(index=i, candidate_id=item["candidate_id"], expected_accept=item["expected_accept"],
                          host_accepted=False, same_as_candidate=False,
                          outcome=ReplayOutcome.CONTROL if not item["expected_accept"] else ReplayOutcome.DISCARDED)
            for i, item in enumerate(items)
        )
        return ChallengeReplay(demo_id=demo_id, stage=stage, witnesses=witnesses)


class Recording(OfflineDeterministicPfpProvider):
    def __init__(self):
        self.packets = []

    def generate_candidate(self, packet, temperature=0.0):
        self.packets.append(packet)
        return super().generate_candidate(packet, temperature)


def _owner(provider, **kwargs):
    return ExecuteStagePipelineUseCase(STORAGE, provider, catalog=STORAGE, host_verifier=Host(), **kwargs)


def test_canonical_pipeline_runs_a_subset_with_model_calls_only_for_model_stages():
    provider = Recording()
    result = _owner(provider).run_pipeline("demo_000", {"raw_seed": "<>"}, stages=WITHOUT_SELECTION)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == WITHOUT_SELECTION
    # Stage 1 is a repair turn because the seed has no declaration.
    assert [packet.stage for packet in provider.packets] == [1, 2, 3, 4, 6, 11]
    stage_11_context = json.loads(provider.packets[-1].user)["prior_artifacts"]
    assert sorted(stage_11_context, key=int) == ["1", "2", "3", "4", "5", "6", "7", "9", "10"]


def test_a_declared_seed_is_admitted_without_a_model_turn():
    provider = Recording()
    result = _owner(provider).run_pipeline("demo_000", {"raw_seed": "<>", "declaration": DECLARATION},
                                           stages=WITHOUT_PLAN)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert [packet.stage for packet in provider.packets] == [2, 3, 4, 6]
    assert receipt.stage_responses[1]["declaration_source"] == "seed"


def test_stages_and_stage_count_are_exclusive():
    result = _owner(Recording()).run_pipeline("demo_000", {}, stages=WITHOUT_SELECTION, stage_count=4)
    assert result.is_err and result.unwrap_err().code == RefusalCode.UNKNOWN_STAGE
