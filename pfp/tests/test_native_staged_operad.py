"""Native planar order and Python payload refinement over actual existing ports.

Model replies are deterministic fixtures; the host verifies the submitted
fixture payload. These are integration controls, not a live accuracy result.
"""
import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from pfp.domain.contracts.pfp_runtime import PfpPipelineFailure
from pfp.domain.contracts.staged_operad import FRAME_TYPES, StageFrame0, json_digest
from pfp.domain.kernel.result import RefusalCode, TerminalStatus
from pfp.domain.stages.stages import Stage5Response
from pfp.infrastructure.providers import OfflineDeterministicPfpProvider
from pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from pfp.use_cases.execute_stage_pipeline import (
    ExecuteStagePipelineUseCase,
    _EducationPipelineAdapter,
)
from adversary.infrastructure.pfp_staged_operad import (
    RunNativeStagedPfpUseCase,
    operation_id,
    staged_wire,
)
from operads.skill_operad.skill_compiler.op_inventory import Wire


class Provider(OfflineDeterministicPfpProvider):
    def __init__(self, mutate=None):
        self.packets = []
        self.mutate = mutate

    def generate_candidate(self, packet, temperature=0.0):
        self.packets.append(packet)
        answer = json.loads(super().generate_candidate(packet, temperature))
        if self.mutate:
            self.mutate(packet.stage, answer)
        return json.dumps(answer)


class Host:
    def __init__(self, *, passed=True, mutate=False):
        self.calls = []
        self.passed, self.mutate = passed, mutate

    def verify(self, demo_id, prior):
        self.calls.append(deepcopy(prior))
        assert list(prior) == [1, 2, 3, 4]
        valid = prior[4]["candidate"] == {"proposal": "Offline fixture; not a mathematical certificate"}
        if self.mutate:
            prior[2]["candidates"].clear()
        passed = self.passed and valid
        return Stage5Response(demo_id=demo_id, should_continue=passed,
                              host_verdict="PASS" if passed else "REFUSE", exact_checks_passed=passed,
                              surviving_candidates=[prior[4]["candidate_id"]] if passed else [])


def pipeline(provider=None, host=None):
    provider, host = provider or Provider(), host or Host()
    storage = PfpFileSystemStorageAdapter()
    owner = ExecuteStagePipelineUseCase(storage, provider, catalog=storage, host_verifier=host,
                                       pipeline_runner=RunNativeStagedPfpUseCase())
    return owner, provider, host


ALL = tuple(range(1, 12))
# The seed has no declaration, so stage 1 asks for a repair turn; stage 9 marks the run
# diagnostic, so stage 11 asks for an evidence plan. Stages 5, 7, 8, 9 and 10 are host stages.
MODEL_PACKETS = [1, 2, 3, 4, 6, 11]


def test_opt_in_executes_the_eleven_stage_native_composite_and_preserves_earlier_payloads():
    owner, provider, host = pipeline()
    seed = {"raw_seed": "Preserve λ, negation and order <>\n", "constraints": ["do not infer"]}
    original = deepcopy(seed)
    result = owner.run_pipeline("demo_000", seed, native_staged_operad=True)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == ALL and receipt.all_stages_passed
    assert receipt.final_terminal_status == TerminalStatus.VERIFIED_WITH_RESIDUALS
    assert [packet.stage for packet in provider.packets] == MODEL_PACKETS
    assert len(host.calls) == 1
    evidence = receipt.operad_execution
    assert evidence["execution"]["status"] == "COMPLETED"
    assert [item["op_id"] for item in evidence["execution"]["steps"]] == [operation_id(n) for n in ALL]
    assert evidence["execution"]["native_term_id"] and evidence["execution"]["native_plan_digest"]
    assert set(evidence["contract_manifest"]["stages"]) == set(map(str, ALL))
    frame = FRAME_TYPES[11].model_validate(evidence["final_frame"])
    assert frame.stages == ALL and frame.completed_count == 11
    assert frame.original_seed == seed == original
    assert frame.stage2_candidates == host.calls[0][2]["candidates"]
    assert frame.stage4_candidate == host.calls[0][4]["candidate"]
    assert frame.stage5_host_evidence == receipt.stage_responses[5]
    assert [item.data for item in frame.prior_results] == list(receipt.stage_responses.values())
    for packet in provider.packets:
        context = json.loads(packet.user)
        assert context["original_seed"] == seed
        assert list(map(int, context["prior_artifacts"])) == list(range(1, packet.stage))


def test_non_admitted_first_stage_stops_before_any_later_model_or_host_dispatch():
    def refuse(stage, answer):
        if stage == 1:
            answer["admission_proposal"]["status"] = "needs_declaration"
    owner, provider, host = pipeline(Provider(refuse))
    result = owner.run_pipeline("demo_000", {"seed": "unchanged"}, native_staged_operad=True)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == (1,) and not receipt.all_stages_passed
    assert receipt.final_terminal_status == TerminalStatus.BLOCKED_BY_EVIDENCE
    assert [p.stage for p in provider.packets] == [1] and not host.calls
    assert receipt.operad_execution["execution"]["refusal"]["code"] == "PFP_STAGE_STOPPED"


def test_host_refusal_stops_before_adversarial_countermodel_and_evidence_plan():
    owner, provider, host = pipeline(host=Host(passed=False))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.HOST_CHECK_FAILED
    assert result.unwrap_err().stage == 5
    assert [p.stage for p in provider.packets] == [1, 2, 3, 4] and len(host.calls) == 1


def test_in_place_host_mutation_is_detected_before_stage_six():
    owner, provider, _ = pipeline(host=Host(mutate=True))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and "PFP_STAGE_PREFIX_MUTATED" in result.unwrap_err().message
    assert [p.stage for p in provider.packets] == [1, 2, 3, 4]


def test_prefix_mutation_cannot_hide_behind_python_boolean_integer_equality():
    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    original = port.execute_model_stage

    def mutate_prefix(stage, prior):
        step = original(stage, prior)
        if stage == 2:
            prior[1]["stage"] = True  # Equal to 1 in Python, different retained JSON.
        return step

    port.execute_model_stage = mutate_prefix
    with pytest.raises(PfpPipelineFailure, match="PFP_STAGE_PREFIX_MUTATED"):
        RunNativeStagedPfpUseCase().execute(ALL, port,
            demo_id="demo_000", original_seed={"seed": "literal"})
    assert [p.stage for p in provider.packets] == [1, 2] and not host.calls


def test_refused_second_execution_cannot_expose_the_first_execution_as_current():
    owner, _, _ = pipeline()
    owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True).unwrap()
    runner = owner.pipeline_runner
    assert runner.last_execution is not None
    with pytest.raises(PfpPipelineFailure) as refused:
        runner.execute((), None, demo_id="demo_000", original_seed={"seed": "literal"})
    assert refused.value.code == "UNKNOWN_STAGE" and runner.last_execution is None


def test_unknown_extracted_candidate_refuses_before_the_host():
    def tamper(stage, answer):
        if stage == 4:
            answer["candidate_id"] = "foreign-candidate"
    owner, provider, host = pipeline(Provider(tamper))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().stage == 4
    assert not host.calls and [p.stage for p in provider.packets] == [1, 2, 3, 4]


@pytest.mark.parametrize("profile,version", [("legacy", "pfp-staged.0.3"), ("canonical", "future-version")])
def test_native_path_requires_the_current_canonical_stage_contract(profile, version):
    owner, provider, host = pipeline()
    controller = owner.storage.load_stage_controller().model_copy(update={"version": version})
    owner.storage.load_stage_controller = lambda: controller
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True,
                                response_profile=profile)
    assert result.is_err and result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert not provider.packets and not host.calls


@pytest.mark.parametrize("wire", [
    Wire(op=operation_id(2), args=("State.StageFrame0",)),
    staged_wire(tuple(range(1, 11))),
])
def test_wrong_native_slot_type_or_truncated_tree_refuses_before_provider_dispatch(wire):
    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    modes = []
    port.prepare_modes = lambda: modes.append("executed")
    with pytest.raises(PfpPipelineFailure) as error:
        RunNativeStagedPfpUseCase().execute(ALL, port,
            demo_id="demo_000", original_seed={"seed": "literal"}, wire=wire)
    assert error.value.code == "TYPING_VIOLATION"
    assert not provider.packets and not host.calls and not modes


@pytest.mark.parametrize("mutation", ["seed", "index", "boolean-index", "prior-stage", "foreign-demo"])
def test_refined_frame_payloads_reject_tampering(mutation):
    owner, _, _ = pipeline()
    receipt = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True).unwrap()
    frame = deepcopy(receipt.operad_execution["final_frame"])
    if mutation == "seed":
        frame["original_seed"]["seed"] = "changed"
    elif mutation == "index":
        frame["completed_count"] = 10
    elif mutation == "boolean-index":
        frame["completed_count"] = True
    elif mutation == "prior-stage":
        frame["prior_results"][1]["stage"] = 4
    else:
        frame["prior_results"][3]["data"]["demo_id"] = "foreign"
    with pytest.raises(ValidationError):
        FRAME_TYPES[11].model_validate(frame)


def test_frame_zero_keeps_literal_seed_and_rejects_nonfinite_values():
    seed = {"text": "first then not second\nλ"}
    frame = StageFrame0(stages=(1,), demo_id="demo_000", original_seed=seed, original_seed_sha256=json_digest(seed))
    assert frame.original_seed == seed
    with pytest.raises(ValueError):
        StageFrame0(stages=(1,), demo_id="demo_000", original_seed={"x": float("nan")}, original_seed_sha256="0" * 64)


def test_default_pipeline_keeps_its_previous_result_and_has_no_native_receipt():
    owner, provider, host = pipeline()
    receipt = owner.run_pipeline("demo_000", {"seed": "literal"}).unwrap()
    # The fixture has no stage 6 witness, so the host does not grant VERIFIED.
    assert receipt.final_terminal_status == TerminalStatus.VERIFIED_WITH_RESIDUALS
    assert receipt.operad_execution is None
    assert [packet.stage for packet in provider.packets] == MODEL_PACKETS and len(host.calls) == 1


def test_final_stage_independent_failure_cannot_keep_the_all_stages_passed_flag():
    from dataclasses import replace

    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    original = port.execute_model_stage
    def fail_final(stage, prior):
        step = original(stage, prior)
        return replace(step, data={**step.data, "independent_check_passed": False}) if stage == 11 else step
    port.execute_model_stage = fail_final
    result = RunNativeStagedPfpUseCase().execute(ALL, port,
        demo_id="demo_000", original_seed={"seed": "literal"})
    assert result.terminal_status == "BLOCKED_BY_EVIDENCE"
    assert not result.all_stages_passed
    assert [packet.stage for packet in provider.packets] == MODEL_PACKETS and len(host.calls) == 1


def test_provider_failure_keeps_its_own_typed_reason_and_stops_downstream():
    def unavailable(stage, _answer):
        if stage == 3:
            raise RuntimeError("controlled unavailable provider")
    owner, provider, host = pipeline(Provider(unavailable))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.INFRASTRUCTURE_FAILURE
    assert result.unwrap_err().stage == 3
    assert [packet.stage for packet in provider.packets] == [1, 2, 3] and not host.calls


def test_invalid_initial_payload_refuses_before_mode_host_checks(monkeypatch):
    owner, provider, host = pipeline()
    def unexpected_modes(_self):
        pytest.fail("invalid initial frame reached mode host checks")
    monkeypatch.setattr(_EducationPipelineAdapter, "prepare_modes", unexpected_modes)
    result = owner.run_pipeline("demo_000", {"bad": float("nan")}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert not provider.packets and not host.calls


@pytest.mark.parametrize("mutation", ["version", "schema", "host-preservation"])
def test_canonical_stage_contract_preflight_runs_before_any_model_or_mode_checks(mutation, monkeypatch):
    owner, provider, host = pipeline()
    load = owner.storage.load_stage_file
    def altered(stage):
        spec = load(stage)
        if mutation == "version" and stage == 10:
            return spec.model_copy(update={"version": "unsupported"})
        if mutation == "schema" and stage == 6:
            return spec.model_copy(update={"response_schema": {"type": "invented-json-type"}})
        if mutation == "host-preservation" and stage == 5:
            return spec.model_copy(update={"input_contract": spec.input_contract.model_copy(
                update={"preserve_original_seed": False})})
        return spec
    owner.storage.load_stage_file = altered
    monkeypatch.setattr(_EducationPipelineAdapter, "prepare_modes",
                        lambda _self: pytest.fail("invalid contract reached mode checks"))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert not provider.packets and not host.calls


@pytest.mark.parametrize("mutation", ["seed", "contract"])
def test_mode_preparation_cannot_change_frozen_inputs_before_dispatch(mutation, monkeypatch):
    owner, provider, host = pipeline()
    load = owner.storage.load_stage_file

    def alter_after_preflight(port):
        if mutation == "seed":
            port.seed["seed"] = "changed during mode preparation"
        else:
            def changed(stage):
                spec = load(stage)
                return spec.model_copy(update={"user_prompt": spec.user_prompt + "\nchanged"}) if stage == 1 else spec
            owner.storage.load_stage_file = changed

    monkeypatch.setattr(_EducationPipelineAdapter, "prepare_modes", alter_after_preflight)
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert result.unwrap_err().stage == 1
    assert not provider.packets and not host.calls


def test_throwing_native_host_refuses_before_mode_provider_or_verifier_effects(monkeypatch):
    class UnavailableNativeHost:
        def invoke_runtime(self, _action, _payload):
            raise OSError("controlled unavailable native transport")

    owner, provider, host = pipeline()
    owner.pipeline_runner = RunNativeStagedPfpUseCase(host=UnavailableNativeHost())
    modes = []
    monkeypatch.setattr(_EducationPipelineAdapter, "prepare_modes", lambda _port: modes.append("called"))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.INFRASTRUCTURE_FAILURE
    assert "OSError: controlled unavailable native transport" in result.unwrap_err().message
    assert not modes and not provider.packets and not host.calls


def test_legacy_evidence_plan_default_cannot_replace_the_canonical_evidence_plan():
    def legacy(stage, answer):
        if stage == 11:
            answer.clear()
            answer.update(stage=11, demo_id="demo_000", should_continue=True,
                          evidence_items=[], final_terminal_status="Verified", immutable_receipt_hash="")
    owner, provider, _host = pipeline(Provider(legacy))
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.SCHEMA_VIOLATION
    assert result.unwrap_err().stage == 11
    assert [packet.stage for packet in provider.packets] == MODEL_PACKETS


def test_opt_in_without_an_injected_composition_runner_refuses_before_dispatch():
    owner, provider, host = pipeline()
    owner.pipeline_runner = None
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert "NATIVE_STAGED_RUNNER_UNAVAILABLE" in result.unwrap_err().message
    assert not provider.packets and not host.calls


def test_checked_stage_occurrence_stops_the_composite_before_later_dispatch():
    from operads.skill_operad.resolver.resolver import CheckedOccurrenceRejection

    snapshots = []
    def checked(invocation):
        snapshots.append(invocation)
        if invocation.op_id == operation_id(2):
            return CheckedOccurrenceRejection(invocation.digest(), "PFP-02-DEFECT-HUNTER",
                "CONTROLLED_BOUND_STAGE_FAILURE", "a" * 64, '{"scope":"controlled host port"}')

    owner, provider, host = pipeline()
    owner.pipeline_runner = RunNativeStagedPfpUseCase(occurrence_checker=checked)
    result = owner.run_pipeline("demo_000", {"seed": "retain original"}, native_staged_operad=True)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == (1, 2) and not receipt.all_stages_passed
    assert receipt.final_terminal_status == TerminalStatus.BLOCKED_BY_EVIDENCE
    assert [p.stage for p in provider.packets] == [1, 2] and not host.calls
    execution = receipt.operad_execution["execution"]
    assert execution["refusal"]["code"] == "CHECKED_OCCURRENCE_REJECTED"
    assert execution["null_tree"]["root_output"] == "State.StageFrame11"
    assert json.loads(snapshots[-1].output_json)["completed_count"] == 2
    assert json.loads(snapshots[-1].args_json)[0]["original_seed"] == {"seed": "retain original"}


def test_unavailable_occurrence_check_is_operational_and_stops_later_stages():
    def unavailable(invocation):
        if invocation.op_id == operation_id(2):
            raise OSError("controlled unavailable check")
    owner, provider, host = pipeline()
    owner.pipeline_runner = RunNativeStagedPfpUseCase(occurrence_checker=unavailable)
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.INFRASTRUCTURE_FAILURE
    assert "OCCURRENCE_CHECK_UNAVAILABLE" in result.unwrap_err().message
    assert [p.stage for p in provider.packets] == [1, 2] and not host.calls


@pytest.mark.parametrize("contracts", [None, lambda _stages: {},
    lambda stages: {"controller": "0" * 64, "stages": {str(s): "1" * 64 for s in stages}}])
def test_claimed_canonical_port_needs_actual_controller_manifest_before_effects(contracts):
    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    port.native_staged_contracts = contracts
    modes = []
    port.prepare_modes = lambda: modes.append("called")
    with pytest.raises(PfpPipelineFailure, match="NATIVE_STAGED_CANONICAL_BINDING_REQUIRED"):
        RunNativeStagedPfpUseCase().execute(ALL, port,
            demo_id="demo_000", original_seed={"seed": "literal"})
    assert not modes and not provider.packets and not host.calls


def test_generic_stage_port_is_explicitly_unbound_without_a_fabricated_controller_claim():
    owner, provider, host = pipeline()
    delegate = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    class GenericPort:
        execute_model_stage = staticmethod(delegate.execute_model_stage)
        execute_host_stage = staticmethod(delegate.execute_host_stage)
    result = RunNativeStagedPfpUseCase().execute(ALL, GenericPort(),
        demo_id="demo_000", original_seed={"seed": "literal"})
    assert result.all_stages_passed
    assert result.operad_execution["controller_binding"] == "UNBOUND"
    assert result.operad_execution["controller_version"] is None
    assert result.operad_execution["contract_manifest"] is None
    assert [packet.stage for packet in provider.packets] == MODEL_PACKETS and len(host.calls) == 1


def test_staged_occurrences_bind_the_complete_native_model_and_actual_host_result():
    class CheckedStages:
        def __init__(self):
            self.model = None
            self.observed = []

        def bind_native_model(self, model):
            self.model = model

        def __call__(self, snapshot):
            assert self.model is not None
            self.model.verify_invocation(snapshot)
            self.observed.append(snapshot)

    checker = CheckedStages()
    owner, provider, host = pipeline()
    owner.pipeline_runner = RunNativeStagedPfpUseCase(occurrence_checker=checker)
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, native_staged_operad=True).unwrap()
    assert result.all_stages_passed and len(checker.observed) == 11
    assert [snapshot.ordinal for snapshot in checker.observed] == list(range(11))
    assert len(checker.model.to_json()["occurrences"]) == 11
    checker.model.verify_receipt(owner.pipeline_runner.last_execution)
    assert result.operad_execution["execution"]["schema"] == "core.oewas.run_receipt.v5"
    fifth = json.loads(checker.observed[4].output_json)
    assert fifth["prior_results"][4]["data"] == result.stage_responses[5]
    assert len(host.calls) == 1 and [packet.stage for packet in provider.packets] == MODEL_PACKETS


def test_unavailable_controller_manifest_is_typed_and_precedes_any_effect():
    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    def unavailable(_stages):
        raise OSError("controlled manifest unavailable")
    port.native_staged_contracts = unavailable
    modes = []
    port.prepare_modes = lambda: modes.append("called")
    with pytest.raises(PfpPipelineFailure, match="NATIVE_STAGED_CONTRACT_UNAVAILABLE") as error:
        RunNativeStagedPfpUseCase().execute(ALL, port,
            demo_id="demo_000", original_seed={"seed": "literal"})
    assert error.value.code == "INFRASTRUCTURE_FAILURE"
    assert not modes and not provider.packets and not host.calls


def test_canonical_controller_label_and_self_authored_digest_are_not_a_controller():
    owner, provider, host = pipeline()
    port = _EducationPipelineAdapter(owner, "demo_000", {"seed": "literal"}, owner.storage.load_stage_controller())
    class ControllerLabel:
        version = "pfp-staged.0.3"
        def model_dump(self, **_kwargs):
            return {}
    port.controller = ControllerLabel()
    port.native_staged_contracts = lambda stages: {
        "controller": json_digest({}), "stages": {str(stage): "1" * 64 for stage in stages}}
    modes = []
    port.prepare_modes = lambda: modes.append("called")
    with pytest.raises(PfpPipelineFailure, match="NATIVE_STAGED_CANONICAL_BINDING_REQUIRED"):
        RunNativeStagedPfpUseCase().execute(ALL, port,
            demo_id="demo_000", original_seed={"seed": "literal"})
    assert not modes and not provider.packets and not host.calls


@pytest.mark.parametrize("stages,packets,terminal", [
    # No evidence plan: stage 11 is the one stage nothing requires.
    (tuple(range(1, 11)), [1, 2, 3, 4, 6], TerminalStatus.VERIFIED_WITH_RESIDUALS),
    # No selection: stage 9 does not require stage 8.
    ((1, 2, 3, 4, 5, 6, 7, 9, 10, 11), MODEL_PACKETS, TerminalStatus.VERIFIED_WITH_RESIDUALS),
])
def test_native_runner_accepts_a_closed_non_prefix_subset(stages, packets, terminal):
    owner, provider, host = pipeline()
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, stages=stages, native_staged_operad=True)
    assert result.is_ok, result.error
    receipt = result.unwrap()
    assert receipt.completed_stages == stages and receipt.all_stages_passed
    assert receipt.final_terminal_status == terminal
    assert [packet.stage for packet in provider.packets] == packets and len(host.calls) == 1
    steps = receipt.operad_execution["execution"]["steps"]
    assert [item["op_id"] for item in steps] == [operation_id(n) for n in stages]
    frame = FRAME_TYPES[len(stages)].model_validate(receipt.operad_execution["final_frame"])
    assert frame.stages == stages and [item.stage for item in frame.prior_results] == list(stages)


def test_native_runner_refuses_an_unclosed_subset_before_any_dispatch():
    owner, provider, host = pipeline()
    result = owner.run_pipeline("demo_000", {"seed": "literal"}, stages=(1, 2, 3, 5), native_staged_operad=True)
    assert result.is_err and result.unwrap_err().code == RefusalCode.UNKNOWN_STAGE
    assert "Stage 5 requires stages [4]" in result.unwrap_err().message
    assert not provider.packets and not host.calls


def test_a_frame_cannot_claim_a_stage_outside_its_subset():
    owner, _, _ = pipeline()
    receipt = owner.run_pipeline("demo_000", {"seed": "literal"}, stages=tuple(range(1, 11)),
                                 native_staged_operad=True).unwrap()
    frame = deepcopy(receipt.operad_execution["final_frame"])
    frame["stages"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
    with pytest.raises(ValidationError, match="PFP_STAGE_SUBSET_MISMATCH"):
        FRAME_TYPES[10].model_validate(frame)
