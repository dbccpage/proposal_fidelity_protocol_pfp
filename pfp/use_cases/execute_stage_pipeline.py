"""Stage Pipeline Execution Use Case for PFP (Stages 1 through 11).

Orchestrates model turns and the host stages (1, 5, 7, 8, 9, 10) using Railway-Oriented Programming (ROP).
Education response validation and host-verifier adapter for runtime stage control.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import SchemaError

from omega_engine_pfp.domain.contracts.pfp_runtime import (
    PfpPipelineFailure,
    PfpPipelineRunnerPort,
    PfpPipelineStep,
    PfpStagePromptInput,
)
from omega_engine_pfp.use_cases.pfp_prompt import AssemblePfpStagePromptUseCase
from omega_engine_pfp.use_cases.pfp_stages import RunPfpPipelineUseCase

from ..domain.aggregates.pilot_aggregate import PilotAggregate
from ..domain.kernel.ports import (
    PfpDemoCatalogPort,
    PfpHostVerifierPort,
    PfpLlmProviderPort,
    PfpSolverPort,
    PfpStoragePort,
)
from ..domain.kernel.result import (
    DomainError,
    RefusalCode,
    Result,
    TerminalStatus,
)
from ..domain.prompts.packets import PacketEnvelope
from ..domain.prompts.prompts import PromptPacket
from ..domain.stages.host_stages import (
    admit_record,
    hand_off_record,
    receipt_record,
    selection_record,
)
from ..domain.stages.stages import (
    HOST_STAGES,
    SCHEMA_RESPONSE_MODELS,
    STAGE_COUNT,
    ChallengeReplay,
    Stage5Response,
    Stage7Response,
    stage_subset_problem,
)
from ..domain.value_objects.identifiers import PilotId
from ..domain.value_objects.numerics import StageNumber
from ..domain.value_objects.taxonomy import EvaluationStatusVO, TrialStatusVO


@dataclass(frozen=True)
class PipelineExecutionReceipt:
    demo_id: Union[str, PilotId]
    all_stages_passed: bool
    completed_stages: Tuple[int, ...]
    stage_responses: Mapping[int, Dict[str, Any]]
    final_terminal_status: TerminalStatus
    authority_effect: str = "None"
    operad_execution: Mapping[str, Any] | None = None

    @property
    def pilot_id_vo(self) -> PilotId:
        return self.demo_id if isinstance(self.demo_id, PilotId) else PilotId(str(self.demo_id))

    @property
    def completed_stages_vo(self) -> StageNumber:
        count = len(self.completed_stages)
        return StageNumber(max(1, min(STAGE_COUNT, count)))

    @property
    def completed_stages_tuple(self) -> Tuple[StageNumber, ...]:
        return tuple(StageNumber(s) for s in self.completed_stages)

    def __hash__(self) -> int:
        d_val = self.demo_id.value if isinstance(self.demo_id, PilotId) else str(self.demo_id)
        return hash(
            (
                d_val,
                self.all_stages_passed,
                self.completed_stages,
                self.final_terminal_status,
                self.authority_effect,
            )
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PipelineExecutionReceipt):
            return False
        d_self = self.demo_id.value if isinstance(self.demo_id, PilotId) else str(self.demo_id)
        d_other = other.demo_id.value if isinstance(other.demo_id, PilotId) else str(other.demo_id)
        return (
            d_self == d_other
            and self.all_stages_passed == other.all_stages_passed
            and self.completed_stages == other.completed_stages
            and self.stage_responses == other.stage_responses
            and self.final_terminal_status == other.final_terminal_status
            and self.authority_effect == other.authority_effect
            and self.operad_execution == other.operad_execution
        )


class ExecuteStagePipelineUseCase:
    """Executes the staged PFP pipeline (11 stages) with fail-closed ROP chaining.

    The demo must exist in ``catalog`` and Stage 5 must be decided by
    ``host_verifier``. Without either, the run refuses rather than reporting a
    pass nobody checked.
    """

    def __init__(
        self,
        storage: PfpStoragePort,
        provider: PfpLlmProviderPort,
        solver: Optional[PfpSolverPort] = None,
        catalog: Optional[PfpDemoCatalogPort] = None,
        host_verifier: Optional[PfpHostVerifierPort] = None,
        pipeline_runner: PfpPipelineRunnerPort | None = None,
    ) -> None:
        self.storage = storage
        self.provider = provider
        self.solver = solver
        self.catalog = catalog
        self.host_verifier = host_verifier
        self.pipeline_runner = pipeline_runner

    def run_pipeline(
        self,
        demo_id: Union[str, PilotId],
        initial_seed: Dict[str, Any],
        *,
        modes: Tuple[int, ...] = (),
        candidate_schema: Optional[Dict[str, Any]] = None,
        response_profile: str = "canonical",
        stage_count: int = STAGE_COUNT,
        mode_inputs: Optional[Dict[int, Dict[str, Any]]] = None,
        native_staged_operad: bool = False,
        stages: Optional[Tuple[int, ...]] = None,
    ) -> Result[PipelineExecutionReceipt, DomainError]:
        """Run stages 1 through `stage_count`, or the runnable subset `stages`.

        `stages` and a `stage_count` other than the full count are exclusive. A subset is
        checked against the controller's `requires` lists, by both runners.
        """
        d_id = demo_id.value if isinstance(demo_id, PilotId) else str(demo_id)

        if self.catalog is None:
            return Result.err(
                DomainError(
                    code=RefusalCode.CATALOG_UNAVAILABLE,
                    message="No demo catalog was supplied; the pipeline cannot check the demo id.",
                )
            )
        if self.catalog.get_demo(d_id) is None:
            return Result.err(
                DomainError(
                    code=RefusalCode.UNKNOWN_DEMO,
                    message=f"Demo {d_id!r} is not in the supplied demo catalog.",
                )
            )
        try:
            if response_profile == "legacy":
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "LEGACY_RESPONSE_PROFILE_RETIRED")
            if response_profile != "canonical":
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "UNKNOWN_RESPONSE_PROFILE")
            if type(native_staged_operad) is not bool:
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_OPT_IN_MUST_BE_BOOLEAN")
            if native_staged_operad and self.pipeline_runner is None:
                raise PfpPipelineFailure("HOST_VERIFIER_UNAVAILABLE", "NATIVE_STAGED_RUNNER_UNAVAILABLE")
            if type(stage_count) is not int or not 1 <= stage_count <= STAGE_COUNT:
                raise PfpPipelineFailure(
                    "UNKNOWN_STAGE", f"stage_count must be an integer from 1 through {STAGE_COUNT}")
            if stages is not None and stage_count != STAGE_COUNT:
                raise PfpPipelineFailure("UNKNOWN_STAGE", "Pass either stages or stage_count, not both")
            if type(modes) is not tuple or any(type(m) is not int or not 1 <= m <= 20 for m in modes):
                raise PfpPipelineFailure("UNKNOWN_MODE", "Modes must be a tuple of distinct integer IDs")
            if len(set(modes)) != len(modes):
                raise PfpPipelineFailure("UNKNOWN_MODE", "Duplicate mode IDs")
            controller = self.storage.load_stage_controller()
            adapter = _EducationPipelineAdapter(
                self, d_id, deepcopy(initial_seed), controller,
                modes, candidate_schema, mode_inputs,
            )
            requires = None
            if stages is None:
                stages = tuple(ref.stage for ref in controller.stages[:stage_count])
            else:
                requires = controller.requires_by_stage()
            native_execution = None
            if native_staged_operad:
                problem = stage_subset_problem(stages, controller.requires_by_stage())
                if problem is not None:
                    raise PfpPipelineFailure("UNKNOWN_STAGE", problem)
                run = self.pipeline_runner.execute(stages, adapter, demo_id=d_id,
                    original_seed=deepcopy(initial_seed))
                native_execution = run.operad_execution
            else:
                adapter.prepare_modes()
                run = RunPfpPipelineUseCase().execute(stages, adapter, requires)
        except PfpPipelineFailure as exc:
            return Result.err(
                DomainError(code=RefusalCode[exc.code], message=str(exc), stage=exc.stage)
            )
        return Result.ok(
            PipelineExecutionReceipt(
                demo_id=demo_id,
                all_stages_passed=run.all_stages_passed,
                completed_stages=run.completed_stages,
                stage_responses=run.stage_responses,
                final_terminal_status=TerminalStatus[run.terminal_status],
                authority_effect="None",
                operad_execution=native_execution,
            )
        )

    def execute(
        self,
        demo_id: Union[str, PilotId],
        initial_seed: Optional[Dict[str, Any]] = None,
    ) -> Result[PipelineExecutionReceipt, DomainError]:
        """Execute stage pipeline for a demo identifier."""
        return self.run_pipeline(demo_id=demo_id, initial_seed=initial_seed or {})

    def execute_pilot(
        self,
        pilot: PilotAggregate,
    ) -> Result[PilotAggregate, DomainError]:
        """Run the stage pipeline for a PilotAggregate and return the updated aggregate."""
        res = self.run_for_pilot(pilot)
        if res.is_err:
            return Result.err(res.unwrap_err())
        receipt = res.unwrap()

        stages_count = StageNumber(max(1, min(STAGE_COUNT, len(receipt.completed_stages))))
        updated = replace(
            deepcopy(pilot),
            trial_status=TrialStatusVO("PASS" if receipt.all_stages_passed else "NOT_RUN"),
            evaluation_status=EvaluationStatusVO("NOT_RUN"),
            extracted_answer=None,
            response=None,
            completed_stages_count=stages_count,
            execution_receipt_evidence=(
                f"Pipeline executed {len(receipt.completed_stages)} stages; "
                "pilot answer acceptance was not evaluated"
            ),
        )
        return Result.ok(updated)

    def run_for_pilot(self, pilot: PilotAggregate) -> Result[PipelineExecutionReceipt, DomainError]:
        """Run the stage pipeline directly for a PilotAggregate."""
        if not isinstance(pilot, PilotAggregate):
            return Result.err(
                DomainError(
                    code=RefusalCode.TYPING_VIOLATION,
                    message=f"Expected PilotAggregate, received {type(pilot).__name__}",
                )
            )
        demo_id = getattr(pilot, "target", "") or pilot.pilot_id.value
        initial_seed = {
            "pilot_id": pilot.pilot_id.value,
            "seed_prompt": pilot.seed_prompt,
            "checker_id": pilot.checker_id.value,
        }
        return self.run_pipeline(demo_id=demo_id, initial_seed=initial_seed)

    def _execute_host_stage_5(
        self,
        demo_id: str,
        prior_responses: Dict[int, Dict[str, Any]],
    ) -> Result[Stage5Response, DomainError]:
        if self.host_verifier is None:
            return Result.err(
                DomainError(
                    code=RefusalCode.HOST_VERIFIER_UNAVAILABLE,
                    message="Stage 5 needs a host verifier; none was supplied.",
                    stage=5,
                )
            )
        try:
            verdict = self.host_verifier.verify(demo_id, prior_responses)
        except Exception as exc:
            return Result.err(
                DomainError(
                    code=RefusalCode.INFRASTRUCTURE_FAILURE,
                    message=f"Host verifier raised {type(exc).__name__}: {exc}",
                    stage=5,
                )
            )
        if type(verdict) is not Stage5Response or verdict.demo_id != demo_id:
            return Result.err(
                DomainError(
                    code=RefusalCode.SCHEMA_VIOLATION,
                    message="Host verifier did not return a Stage5Response for this demo.",
                    stage=5,
                )
            )
        if verdict.host_verdict != "PASS" or verdict.exact_checks_passed is not True:
            return Result.err(
                DomainError(
                    code=RefusalCode.HOST_CHECK_FAILED,
                    message=f"Host verdict {verdict.host_verdict!r}; exact checks did not pass.",
                    stage=5,
                )
            )
        return Result.ok(verdict)


class _EducationPipelineAdapter:
    """Bind education's validated responses and host verifier to runtime stages."""

    def __init__(self, owner, demo_id, seed, controller, modes=(), candidate_schema=None, mode_inputs=None):
        self.owner, self.demo_id, self.seed = owner, demo_id, seed
        self.controller, self.modes = controller, modes
        self.candidate_schema = deepcopy(candidate_schema)
        self.mode_artifacts = {}
        self.mode_inputs = deepcopy(mode_inputs or {})

    def native_staged_contracts(self, stages):
        """Refine the native frame ports with the current canonical stage files."""
        from ..domain.contracts.staged_operad import CONTROLLER_VERSION, json_digest

        if self.controller.version != CONTROLLER_VERSION:
            raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_CANONICAL_CONTRACT_REQUIRED")
        manifest = {"controller": json_digest(self.controller.model_dump(mode="json")), "stages": {}}
        refs = {ref.stage: ref for ref in self.controller.stages}
        for stage in stages:
            spec = self.owner.storage.load_stage_file(stage)
            ref = refs[stage]
            if (spec.stage != stage or spec.requires != ref.requires or spec.name != ref.name
                    or spec.executor != ref.executor or spec.seat != ref.seat
                    or spec.version != CONTROLLER_VERSION):
                raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_STAGE_CONTRACT_MISMATCH", stage)
            if stage == 5:
                contract = spec.input_contract
                if (not contract.preserve_original_seed or not contract.retain_stage_2_candidates
                        or contract.candidate_source_stage != 4 or not contract.independent_checker_required):
                    raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_HOST_CONTRACT_MISMATCH", stage)
            if spec.response_schema is not None:
                try:
                    Draft202012Validator.check_schema(spec.response_schema)
                except SchemaError as exc:
                    raise PfpPipelineFailure("SCHEMA_VIOLATION", "NATIVE_STAGED_RESPONSE_SCHEMA_INVALID", stage) from exc
            manifest["stages"][str(stage)] = json_digest(spec.model_dump(mode="json"))
        return manifest

    def prepare_modes(self):
        from .pfp_mode_checks import EXECUTABLE_MODES, execute_mode_check
        additional_modes = frozenset({9, 10, 11, 12, 16, 17, 18, 20})

        for mode_id in self.modes:
            mode = self.owner.storage.load_mode_file(mode_id)
            if mode.mode_id != mode_id:
                raise PfpPipelineFailure("UNKNOWN_MODE", "Mode identity mismatch")
            if mode_id not in EXECUTABLE_MODES | additional_modes | {2, 14}:
                raise PfpPipelineFailure(
                    "UNKNOWN_MODE", f"MODE_EXECUTOR_UNAVAILABLE: {mode_id:02d} {mode.verifier_contract.verifier_type}"
                )
            if mode_id in EXECUTABLE_MODES | additional_modes:
                if mode_id not in self.mode_inputs:
                    raise PfpPipelineFailure("HOST_VERIFIER_UNAVAILABLE", f"MODE_INPUT_REQUIRED: {mode_id:02d}")
                try:
                    if mode_id in additional_modes:
                        checker = getattr(self.owner.host_verifier, "verify_mode", None)
                        if checker is None:
                            raise PfpPipelineFailure("HOST_VERIFIER_UNAVAILABLE", "MODE_HOST_VERIFIER_REQUIRED")
                        self.mode_artifacts[str(mode_id)] = checker(mode_id, self.mode_inputs[mode_id])
                    else:
                        self.mode_artifacts[str(mode_id)] = execute_mode_check(mode_id, self.mode_inputs[mode_id])
                except (ValueError, TypeError, KeyError, OSError, ImportError, RuntimeError) as exc:
                    raise PfpPipelineFailure("HOST_CHECK_FAILED", f"MODE_{mode_id:02d}: {exc}") from exc
        if 2 in self.modes:
            envelope = PacketEnvelope(
                schema_id="pfp.numbered-stage-source.v1", task_data=self.seed,
                protected_boundary="original_seed", budget=0, candidate_payload={},
            )
            # Reading back exercises the actual verifier; hashes do not grade mathematics.
            self.mode_artifacts["2"] = PacketEnvelope.model_validate(
                envelope.model_dump(mode="json")
            ).model_dump(mode="json")
        if 14 in self.modes:
            verifier=getattr(self.owner.host_verifier,"verify_refusal",None)
            if verifier is None or 14 not in self.mode_inputs:
                raise PfpPipelineFailure("HOST_VERIFIER_UNAVAILABLE","MODE14_TYPED_PROBE_AND_REFUSAL_HANDLER_REQUIRED")
            try:
                self.mode_artifacts["14"] = verifier(self.demo_id,self.mode_inputs[14])
            except Exception as exc:
                raise PfpPipelineFailure("HOST_CHECK_FAILED",str(exc)) from exc

    @staticmethod
    def _step(result):
        if result.is_err:
            error = result.unwrap_err()
            raise PfpPipelineFailure(error.code.name, error.message, error.stage)
        response = result.unwrap()
        return PfpPipelineStep(response.model_dump(mode="json"), response.should_continue)

    def _stage_file(self, stage, prior_responses):
        stage_file = self.owner.storage.load_stage_file(stage)
        declared = self.controller.requires_by_stage()[stage]
        if (stage_file.stage != stage or stage_file.requires != declared
                or not set(declared) <= set(prior_responses)):
            raise PfpPipelineFailure("SCHEMA_VIOLATION", "STAGE_DEPENDENCY_MISMATCH", stage)
        return stage_file

    def execute_host_stage(self, stage, prior_responses):
        """Host stages. No model field is read as a verdict; stage 1 asks a model only to repair."""
        if stage not in HOST_STAGES:
            raise PfpPipelineFailure("UNKNOWN_STAGE", f"Stage {stage} is not a host stage", stage)
        stage_file = self._stage_file(stage, prior_responses)
        if stage == 1:
            declaration = self.seed.get("declaration")
            if declaration is None:
                repair, _ = self._model_turn(1, stage_file, prior_responses)
                data = admit_record(self.demo_id, None, repair)
            else:
                data = admit_record(self.demo_id, declaration)
            return PfpPipelineStep(data, data["status"] == "admit")
        if stage == 5:
            return self._step(self.owner._execute_host_stage_5(self.demo_id, prior_responses))
        if stage == 7:
            replay = self._replay(6, prior_responses[6]["challenges"], prior_responses)
            data = Stage7Response(
                demo_id=self.demo_id, host_replay=replay,
                obstruction_indices=list(replay.obstruction_indices),
                checked_count=replay.checked_count,
            ).model_dump(mode="json")
            return PfpPipelineStep(data, True)
        if stage == 8:
            return PfpPipelineStep(selection_record(self.demo_id, prior_responses), True)
        if stage == 9:
            return PfpPipelineStep(
                receipt_record(self.demo_id, prior_responses, stage_file.obligation_rules), True)
        return PfpPipelineStep(
            hand_off_record(self.demo_id, prior_responses[9], self.owner.storage.load_terminal_routing()), True)

    def execute_model_stage(self, stage, prior_responses):
        if stage in HOST_STAGES:
            raise PfpPipelineFailure("UNKNOWN_STAGE", f"Stage {stage} is a host stage", stage)
        parsed, should_continue = self._model_turn(stage, self._stage_file(stage, prior_responses), prior_responses)
        return PfpPipelineStep(parsed, should_continue)

    def _model_turn(self, stage, stage_file, prior_responses):
        schema = deepcopy(stage_file.response_schema)
        if not schema:
            raise PfpPipelineFailure("SCHEMA_VIOLATION", "STAGE_SCHEMA_UNAVAILABLE", stage)
        schema["properties"]["demo_id"] = {"const": self.demo_id}
        if stage == 6:
            schema["properties"]["challenges"]["items"]["properties"]["candidate_id"] = {
                "const": prior_responses[4]["candidate_id"],
                "description": "Reference the Stage 4 candidate, including for mutated negative controls; this is not a new challenge ID.",
            }
        if self.candidate_schema is not None:
            if stage == 4:
                schema["properties"]["candidate"] = deepcopy(self.candidate_schema)
            elif stage == 6:
                schema["properties"]["challenges"]["items"]["properties"]["witness"] = deepcopy(self.candidate_schema)
        context = dict(original_seed=self.seed, prior_artifacts=deepcopy(prior_responses),
                       stage_instruction=stage_file.user_prompt,
                       mode_artifacts=self.mode_artifacts)
        prompt = AssemblePfpStagePromptUseCase().execute(
            PfpStagePromptInput(
                (self.controller.system_prompt or "PFP source-bound stage execution") + "\n" +
                (stage_file.system_prompt or "") + "\nReturn exactly this JSON schema:\n" +
                json.dumps(schema, sort_keys=True),
                "{user_prompt}", {"user_prompt": json.dumps(context, sort_keys=True, ensure_ascii=False)}, schema,
            )
        )
        packet = PromptPacket(
            demo_id=self.demo_id, stage=stage, system=prompt.system, user=prompt.user,
            response_schema=prompt.response_schema,
            system_sha256=sha256(prompt.system.encode("utf-8")).hexdigest(),
            user_sha256=sha256(prompt.user.encode("utf-8")).hexdigest(),
            seed_sha256=sha256(json.dumps(self.seed, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
        )
        try:
            raw = self.owner.provider.generate_candidate(packet)
        except Exception as exc:
            raise PfpPipelineFailure("INFRASTRUCTURE_FAILURE",
                                     f"Stage provider raised {type(exc).__name__}", stage) from exc
        try:
            parsed = json.loads(raw, object_pairs_hook=_unique_pairs,
                                parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
            checker = validators.extend(Draft202012Validator, type_checker=
                Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _, v: type(v) is int))
            checker(schema).validate(parsed)
            self._check_references(stage, parsed, prior_responses)
            model = SCHEMA_RESPONSE_MODELS.get(stage)
            if model is not None:
                parsed = model.model_validate(parsed).model_dump(mode="json")
        except Exception as exc:
            raise PfpPipelineFailure("SCHEMA_VIOLATION", f"Canonical stage {stage} refused: {exc}", stage) from exc
        return parsed, parsed["should_continue"]

    def _replay(self, stage, items, prior_responses):
        """Stage 7: host replay of the stage 6 witnesses. The model never supplies `host_replay`."""
        if not items:
            return ChallengeReplay(demo_id=self.demo_id, stage=stage)
        verifier = getattr(self.owner.host_verifier, "verify_challenges", None)
        if verifier is None:
            raise PfpPipelineFailure("HOST_VERIFIER_UNAVAILABLE",
                                     f"Stage {stage} witnesses need independent host replay", 7)
        try:
            replay = verifier(self.demo_id, stage, deepcopy(items), deepcopy(prior_responses))
        except ValueError as exc:
            raise PfpPipelineFailure("HOST_CHECK_FAILED", f"Challenge host replay refused: {exc}", 7) from exc
        if (type(replay) is not ChallengeReplay or replay.demo_id != self.demo_id or replay.stage != stage
                or len(replay.witnesses) != len(items)
                or any(w.candidate_id != item["candidate_id"] or w.expected_accept is not item["expected_accept"]
                       for w, item in zip(replay.witnesses, items))):
            raise PfpPipelineFailure("HOST_CHECK_FAILED", "Challenge host replay does not bind the witnesses", 7)
        return replay

    def _check_references(self, stage, data, prior):
        if stage == 2:
            ids = [item["candidate_id"] for item in data["candidates"]]
            if len(set(ids)) != len(ids):
                raise ValueError("DUPLICATE_CANDIDATE_ID")
        elif stage == 3:
            ids = {item["candidate_id"] for item in prior[2]["candidates"]}
            audit_ids = [item["candidate_id"] for item in data["audits"]]
            if len(set(audit_ids)) != len(audit_ids) or not set(audit_ids).issubset(ids):
                raise ValueError("AUDIT_CANDIDATE_BINDING_MISMATCH")
        elif stage == 4:
            extractable = {item["candidate_id"] for item in prior[3]["audits"] if item["routing"] == "extract"}
            if data["candidate_id"] not in extractable or data["missing_fields"]:
                raise ValueError("EXTRACTED_CANDIDATE_NOT_ADMITTED_FOR_CHECK")
        elif stage == 6:
            for item in data["challenges"]:
                if item["candidate_id"] != prior[4]["candidate_id"]:
                    raise ValueError("CHALLENGE_CANDIDATE_BINDING_MISMATCH")


def _unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_JSON_FIELD")
        result[key] = value
    return result
