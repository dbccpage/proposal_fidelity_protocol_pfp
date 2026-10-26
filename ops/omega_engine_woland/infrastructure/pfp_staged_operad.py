"""Explicit native-checked planar composition over existing numbered-stage ports.

The native engine checks arity and ordered frame colours. Pydantic validates
their JSON refinement here; provider preparation, schemas, reference checking,
the host stages, and continuation policy keep their existing owners. A run may
be any runnable stage subset: the k-th requested stage maps frame k-1 to frame k.
"""
from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import replace

from omega_engine_pfp.domain.contracts.pfp_runtime import PfpPipelineFailure, PfpPipelineRun
from omega_engine_pfp.domain.contracts.staged_operad import (
    CONTROLLER_VERSION,
    FRAME_PROFILE,
    FRAME_TYPES,
    MAX_STAGE,
    StageFrame0,
    StageResult,
    json_digest,
)
from omega_engine_pfp.domain.stages.stages import HOST_STAGES, StageController
from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase
from omega_engine_operads.skill_operad.resolver.native_runtime import (
    NativeOperadRefusal,
    native_validate,
    run_native,
)
from omega_engine_operads.skill_operad.resolver.resolver import RunReceipt
from omega_engine_operads.skill_operad.skill_compiler.op_inventory import (
    AntiOpSpec,
    HostBinding,
    OpInventory,
    OpSpec,
    PfpTurnBinding,
    SkillDecomposition,
    Wire,
)


def operation_id(stage: int) -> str:
    return f"pfp.staged.stage-{stage}.v1"


def _subset(stages) -> tuple[int, ...]:
    if (type(stages) is not tuple or not 1 <= len(stages) <= MAX_STAGE or stages[0] != 1
            or any(type(stage) is not int or not 1 <= stage <= MAX_STAGE for stage in stages)
            or any(a >= b for a, b in zip(stages, stages[1:]))):
        raise PfpPipelineFailure("UNKNOWN_STAGE",
            f"Native staged execution requires a strictly increasing stage tuple from stage 1 (stages <= {MAX_STAGE})")
    return stages


def staged_wire(stages: tuple[int, ...] = tuple(range(1, MAX_STAGE + 1))) -> Wire:
    wire = "State.StageFrame0"
    for stage in _subset(stages):
        wire = Wire(op=operation_id(stage), args=(wire,))
    return wire


def staged_inventory(stages: tuple[int, ...] = tuple(range(1, MAX_STAGE + 1)), *,
                     controller_bound: bool = True) -> OpInventory:
    ops, guards = [], []
    for k, stage in enumerate(_subset(stages), start=1):
        source, target = f"State.StageFrame{k - 1}", f"State.StageFrame{k}"
        binding = (HostBinding(target=(
            "omega_engine_pfp/use_cases/execute_stage_pipeline.py::_EducationPipelineAdapter.execute_host_stage"
            if controller_bound else "omega_engine_pfp/domain/contracts/pfp_runtime.py::PfpPipelinePort.execute_host_stage"))
            if stage in HOST_STAGES else PfpTurnBinding(role_id=f"pfp.stage.{stage}",
                role_version=CONTROLLER_VERSION if controller_bound else "unbound"))
        summary = (f"Canonical PFP stage {stage} with retained earlier results" if controller_bound
                   else f"Unbound PFP stage {stage} with retained earlier results")
        ops.append(OpSpec(op_id=operation_id(stage), summary=summary,
                          inputs=(source,), output=target, binding=binding))
        guards.append(AntiOpSpec(op_id=f"pfp.staged.frame-{k - 1}.v1",
            summary="Validate earlier results and honor existing stop decision",
            guards=operation_id(stage), slot=0, inspects=source, refusal="PFP_STAGE_STOPPED"))
    return OpInventory(schema_version="omega.oewas.op_inventory.v3",
        subcolours={"State": tuple(f"StageFrame{n}" for n in range(MAX_STAGE + 1))},
        skills=(SkillDecomposition(skill_id="pfp-staged-operad", ops=tuple(ops), anti_ops=tuple(guards),
                                   wiring=staged_wire(stages)),))


class RunNativeStagedPfpUseCase:
    def __init__(self, *, host=None, occurrence_checker=None):
        self.host = host
        self.occurrence_checker = occurrence_checker
        self.last_execution: RunReceipt | None = None

    def _validate(self, inventory, wire):
        try:
            return native_validate(inventory, wire, host=self.host)
        except NativeOperadRefusal as exc:
            raise PfpPipelineFailure("TYPING_VIOLATION", f"{exc.code}: {exc.message}") from exc
        except Exception as exc:
            raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE",
                f"NATIVE_STAGED_HOST_FAILED: {type(exc).__name__}: {exc}") from exc

    def execute(self, stages: tuple[int, ...], port, *, demo_id: str, original_seed: dict,
                wire: Wire | None = None) -> PfpPipelineRun:
        self.last_execution = None
        stages = _subset(stages)
        expected_wire = staged_wire(stages)
        if wire is not None and wire != expected_wire:
            self._validate(staged_inventory(stages), wire)
            raise PfpPipelineFailure("TYPING_VIOLATION", "PFP_STAGE_COMPOSITE_CHANGED")
        if self.occurrence_checker is not None and not callable(self.occurrence_checker):
            raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE", "OCCURRENCE_CHECK_INVALID")
        controller = getattr(port, "controller", None)
        if controller is not None and getattr(controller, "version", None) != CONTROLLER_VERSION:
            raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_CONTROLLER_VERSION_MISMATCH")
        try:
            initial = StageFrame0(stages=stages, demo_id=demo_id, original_seed=deepcopy(original_seed),
                                 original_seed_sha256=json_digest(original_seed))
        except (ValueError, TypeError) as exc:
            raise PfpPipelineFailure("SCHEMA_VIOLATION", f"PFP_STAGE_FRAME_INVALID: {exc}") from exc
        contracts = getattr(port, "native_staged_contracts", None)
        controller_bound = controller is not None or contracts is not None
        manifest = None

        def read_contracts():
            try:
                return deepcopy(contracts(stages))
            except PfpPipelineFailure:
                raise
            except Exception as exc:
                raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE",
                    f"NATIVE_STAGED_CONTRACT_UNAVAILABLE: {type(exc).__name__}") from exc

        if controller_bound:
            if not isinstance(controller, StageController) or not callable(contracts):
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_CANONICAL_BINDING_REQUIRED")
            try:
                StageController.model_validate_json(controller.model_dump_json())
            except (ValueError, TypeError) as exc:
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_CANONICAL_BINDING_REQUIRED") from exc
            manifest = read_contracts()
            if (type(manifest) is not dict or set(manifest) != {"controller", "stages"}
                    or manifest.get("controller") != json_digest(controller.model_dump(mode="json"))
                    or type(manifest.get("stages")) is not dict
                    or set(manifest["stages"]) != {str(stage) for stage in stages}
                    or any(type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None
                           for value in manifest["stages"].values())):
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_CANONICAL_BINDING_REQUIRED")
        inventory = staged_inventory(stages, controller_bound=controller_bound)
        self._validate(inventory, expected_wire)
        # Mode helpers may execute host checks. Admit the complete operation tree
        # and initial refined payload before those existing checks or model turns.
        prepare_modes = getattr(port, "prepare_modes", None)
        if prepare_modes is not None:
            prepare_modes()
        latest = initial
        failure = None
        stopped_by_policy = False
        policy = RunPfpPipelineUseCase()

        def require_frozen_contract(stage):
            if json_digest(getattr(port, "seed", initial.original_seed)) != initial.original_seed_sha256:
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "PFP_STAGE_PREFIX_MUTATED", stage)
            if controller_bound and read_contracts() != manifest:
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "PFP_STAGE_CONTRACT_CHANGED", stage)

        def parse_frame(value, stage):
            try:
                frame = FRAME_TYPES[stage].model_validate(value)
                if json_digest(frame.model_dump(mode="json")) != json_digest(latest.model_dump(mode="json")):
                    raise ValueError("PFP_STAGE_PREFIX_CHANGED")
                return frame
            except (ValueError, TypeError) as exc:
                raise PfpPipelineFailure("SCHEMA_VIOLATION", str(exc), stage + 1) from exc

        def detector(k):
            def stopped(value):
                nonlocal failure
                try:
                    return not parse_frame(value, k - 1).continue_pipeline
                except PfpPipelineFailure as exc:
                    failure = exc
                    raise
            return stopped

        def executor(k, stage):
            def execute(value):
                nonlocal latest, failure, stopped_by_policy
                try:
                    frame = parse_frame(value, k - 1)
                    prior = {item.stage: deepcopy(item.data) for item in frame.prior_results}
                    before = deepcopy(prior)
                    require_frozen_contract(stage)
                    step = policy.dispatch(stage, port, prior)
                    if json_digest(prior) != json_digest(before):
                        raise PfpPipelineFailure("SCHEMA_VIOLATION", "PFP_STAGE_PREFIX_MUTATED", stage)
                    require_frozen_contract(stage)
                    data = deepcopy(step.data)
                    responses = {**before, stage: data}
                    terminal = policy.terminal_after(stage, responses, step.should_continue)
                    stopped_by_policy = terminal is not None
                    if terminal is None and k == len(stages):
                        terminal = policy.finish(tuple(responses), responses, stages).terminal_status
                    latest = FRAME_TYPES[k](stages=stages, demo_id=demo_id, original_seed=deepcopy(frame.original_seed),
                        original_seed_sha256=frame.original_seed_sha256,
                        prior_results=(*frame.prior_results, StageResult(stage=stage, data=data,
                                                                       controller_continue=step.should_continue)),
                        continue_pipeline=terminal is None, terminal_status=terminal)
                    return latest.model_dump(mode="json")
                except PfpPipelineFailure as exc:
                    failure = exc
                    raise
                except (ValueError, TypeError, KeyError) as exc:
                    failure = PfpPipelineFailure("SCHEMA_VIOLATION", f"PFP_STAGE_FRAME_INVALID: {exc}", stage)
                    raise failure from exc
            return execute

        try:
            receipt = run_native(inventory, expected_wire,
                [initial.model_dump(mode="json")],
                {operation_id(stage): executor(k, stage) for k, stage in enumerate(stages, start=1)},
                {f"pfp.staged.frame-{k - 1}.v1": detector(k) for k in range(1, len(stages) + 1)}, host=self.host,
                occurrence_checker=self.occurrence_checker)
        except Exception as exc:
            raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE",
                f"NATIVE_STAGED_HOST_FAILED: {type(exc).__name__}: {exc}") from exc
        self.last_execution = receipt
        if failure is not None:
            raise failure
        checked_rejection = receipt.refusal is not None and receipt.refusal.code == "CHECKED_OCCURRENCE_REJECTED"
        if receipt.refusal is not None and receipt.refusal.code.startswith("OCCURRENCE_CHECK_"):
            raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE",
                f"{receipt.refusal.code}: {receipt.refusal.message}", latest.last_stage)
        if receipt.refusal is not None and receipt.refusal.code != "PFP_STAGE_STOPPED" and not checked_rejection:
            raise PfpPipelineFailure("TYPING_VIOLATION", f"{receipt.refusal.code}: {receipt.refusal.message}")
        responses = {item.stage: deepcopy(item.data) for item in latest.prior_results}
        pipeline = policy.finish(tuple(responses), responses, stages)
        if stopped_by_policy or latest.terminal_status != pipeline.terminal_status:
            pipeline = replace(pipeline, all_stages_passed=False if stopped_by_policy
                else pipeline.all_stages_passed, terminal_status=latest.terminal_status)
        if checked_rejection:
            pipeline = replace(pipeline, all_stages_passed=False, terminal_status="BLOCKED_BY_EVIDENCE")
        evidence = {"frame_profile": FRAME_PROFILE,
            "frame_schema_controller_version": CONTROLLER_VERSION,
            "controller_binding": "BOUND" if controller_bound else "UNBOUND",
            "controller_version": CONTROLLER_VERSION if controller_bound else None,
            "native_scope": "planar order, operation arity and frame colour",
            "payload_scope": "Python source/earlier-result refinement and existing canonical stage checks",
            "contract_manifest": manifest, "final_frame": latest.model_dump(mode="json"),
            "execution": receipt.to_json()}
        return replace(pipeline, operad_execution=evidence)
