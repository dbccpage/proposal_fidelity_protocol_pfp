"""Pydantic v2 models for PFP Stages (Stages 1 through 11).

Defines StageController, StageFile, StageName, Executor, and all Stage Response contracts.
AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator
from pydantic.functional_validators import BeforeValidator


class AuthorityEffect(str, Enum):
    NONE = "None"


class StageName(str, Enum):
    ADMIT = "admit"
    IDEATION = "ideation"
    AUDIT = "audit"
    L2_EXTRACTION = "l2_extraction"
    EVALUATION = "evaluation"
    ADVERSARIAL = "adversarial"
    CHALLENGE_REPLAY = "challenge_replay"
    SELECTION = "selection"
    RECEIPT = "receipt"
    HAND_OFF = "hand_off"
    EVIDENCE_PLAN = "evidence_plan"


class Executor(str, Enum):
    MODEL = "model"
    HOST = "host"


STAGE_NAMES_BY_INDEX: Tuple[StageName, ...] = tuple(StageName)
STAGE_COUNT = len(STAGE_NAMES_BY_INDEX)

# Host stages never dispatch a model turn, except that stage 1 (admit) asks a model to
# repair a missing declaration. Every other stage is a model turn.
HOST_STAGES: frozenset[int] = frozenset({1, 5, 7, 8, 9, 10})

# The core retinue seat that owns each stage. Stages without a seat are host plumbing.
# The seats are the first five `core_required` entries of
# omega_engine/crates_rs/omega_woland/src/council_layout_v1.json.
SEAT_BY_STAGE: Dict[int, str] = {
    2: "seat_begemot",
    3: "seat_koroviev",
    4: "seat_begemot",
    5: "seat_woland",
    6: "seat_margarita",
    8: "seat_the_master",
}

# The closed set of obligations a stage 9 receipt can carry. The stage 9 file maps each
# to its kill-condition refusal-map key.
OBLIGATION_CODES: Tuple[str, ...] = ("ADVERSARY_CHECKED_NOTHING", "DECLARATION_FROM_MODEL_REPAIR")

# Stages whose outputs the pipeline code reads, by consuming stage. The host stage 5 reads
# the stage 2 candidates and the stage 4 candidate; stage 6 binds to the stage 4 candidate
# id and runs after the stage 5 verdict; stage 7 replays the stage 6 witnesses against the
# stage 4 candidate; stage 8 selects from the stage 5 survivors less the stage 7
# obstructions; stage 9 reads the admission, the verdict and the replay; stages 10 and 11
# read the receipt. A declared `requires` list must contain these.
MINIMUM_STAGE_INPUTS: Dict[int, Tuple[int, ...]] = {
    5: (2, 4), 6: (4, 5), 7: (4, 5, 6), 8: (5, 7), 9: (1, 5, 7), 10: (9,), 11: (9,),
}


def stage_identity_problem(stage: int, name: StageName, executor: Executor,
                           seat: Optional[str]) -> Optional[str]:
    """Why a stage's name, executor or seat is wrong for its number, or None."""
    expected_name = STAGE_NAMES_BY_INDEX[stage - 1]
    if name != expected_name:
        return f"Stage {stage} name must be {expected_name}, got {name}"
    expected_exec = Executor.HOST if stage in HOST_STAGES else Executor.MODEL
    if executor != expected_exec:
        return f"Stage {stage} executor must be {expected_exec}, got {executor}"
    if seat != SEAT_BY_STAGE.get(stage):
        return f"Stage {stage} seat must be {SEAT_BY_STAGE.get(stage)}, got {seat}"
    return None


def requires_problem(stage: int, requires: List[int]) -> Optional[str]:
    """Why a `requires` list is not a valid dependency list for `stage`, or None."""
    if any(type(r) is not int for r in requires):
        return f"Stage {stage} requires must be integers"
    if requires != sorted(set(requires)):
        return f"Stage {stage} requires must be sorted and distinct"
    if any(not 1 <= r < stage for r in requires):
        return f"Stage {stage} requires must name earlier stages only"
    if stage > 1 and not requires:
        return f"Stage {stage} must require at least one earlier stage"
    missing = sorted(set(MINIMUM_STAGE_INPUTS.get(stage, ())) - set(requires))
    if missing:
        return f"Stage {stage} requires must include {missing}"
    return None


def stage_subset_problem(stages: Tuple[int, ...], requires: Dict[int, List[int]]) -> Optional[str]:
    """Why `stages` is not a runnable subset under `requires`, or None.

    A runnable subset is strictly increasing, starts with stage 1, and contains every stage
    that each of its members requires.
    """
    if not stages or any(type(s) is not int or s not in requires for s in stages):
        return "Stages must be known stage numbers"
    if list(stages) != sorted(set(stages)) or stages[0] != 1:
        return "Stages must be strictly increasing and start with stage 1"
    chosen = set(stages)
    for stage in stages:
        missing = sorted(set(requires[stage]) - chosen)
        if missing:
            return f"Stage {stage} requires stages {missing}"
    return None


class InputContract(BaseModel):
    """Host-stage input requirements (stage 5)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preserve_original_seed: StrictBool = True
    retain_stage_2_candidates: StrictBool = True
    candidate_source_stage: StrictInt = 4
    independent_checker_required: StrictBool = True


class ControllerStageRef(BaseModel):
    """Stage reference in controller.yaml."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    stage: StrictInt = Field(ge=1, le=STAGE_COUNT)
    name: StageName
    file: Optional[StrictStr] = None
    executor: Executor
    requires: List[StrictInt]
    seat: Optional[StrictStr] = None

    @model_validator(mode="after")
    def validate_identity(self) -> ControllerStageRef:
        problem = (stage_identity_problem(self.stage, self.name, self.executor, self.seat)
                   or requires_problem(self.stage, self.requires))
        if problem is not None:
            raise ValueError(problem)
        return self


class StageFile(BaseModel):
    """Canonical stage specification (stages/stage_N_*.yaml)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    stage: StrictInt = Field(ge=1, le=STAGE_COUNT)
    name: StageName
    executor: Executor
    requires: List[StrictInt]
    seat: Optional[StrictStr] = None
    version: StrictStr = Field(min_length=1)
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    claim_hygiene_profile: StrictStr = Field(default="claim_hygiene_strict_v1")
    description: StrictStr = Field(default="")
    source_template: Optional[StrictStr] = None
    system_prompt: Optional[StrictStr] = None
    user_prompt: Optional[StrictStr] = None
    input_contract: Optional[InputContract] = None
    response_schema: Optional[Dict[str, Any]] = None
    obligation_rules: Optional[Dict[StrictStr, StrictStr]] = None

    @model_validator(mode="after")
    def validate_stage_contract(self) -> StageFile:
        problem = (stage_identity_problem(self.stage, self.name, self.executor, self.seat)
                   or requires_problem(self.stage, self.requires))
        if problem is not None:
            raise ValueError(problem)
        # Stage 5 carries its input contract; model stages and the stage 1 repair turn carry a
        # response schema; stage 9 carries its obligation rules; the other host stages carry none.
        present = {key for key in ("input_contract", "response_schema", "obligation_rules")
                   if getattr(self, key) is not None}
        if self.stage == 5:
            expected = {"input_contract"}
        elif self.stage == 9:
            expected = {"obligation_rules"}
        elif self.stage == 1 or self.executor == Executor.MODEL:
            expected = {"response_schema"}
        else:
            expected = set()
        if present != expected:
            raise ValueError(f"Stage {self.stage} must carry exactly {sorted(expected)}, got {sorted(present)}")
        if self.stage == 9 and sorted(self.obligation_rules) != sorted(OBLIGATION_CODES):
            raise ValueError(f"Stage 9 obligation_rules must cover exactly {list(OBLIGATION_CODES)}")
        return self


class StageTransition(BaseModel):
    """Transition rule between stages in controller.yaml."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    from_stage: StrictInt = Field(ge=1, le=STAGE_COUNT)
    to_stage: StrictInt = Field(ge=1, le=STAGE_COUNT)
    on_success: StrictStr = Field(default="proceed")
    on_failure: StrictStr = Field(default="abort")


class StageController(BaseModel):
    """Controller configuration (stages/controller.yaml)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    version: StrictStr = Field(min_length=1)
    policy_id: StrictStr = "SPK-001"
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    public_stage_count: StrictInt = STAGE_COUNT
    system_prompt: Optional[StrictStr] = None
    worked_example: Optional[StrictStr] = None
    source_golden_sha256: Optional[StrictStr] = None
    stages: List[ControllerStageRef]

    @model_validator(mode="after")
    def validate_stage_set(self) -> StageController:
        if self.public_stage_count != STAGE_COUNT:
            raise ValueError(f"public_stage_count must be {STAGE_COUNT}")
        stages_present = [s.stage for s in self.stages]
        if stages_present != list(range(1, STAGE_COUNT + 1)):
            raise ValueError(f"Controller must declare stages 1 through {STAGE_COUNT} in order")
        return self

    def requires_by_stage(self) -> Dict[int, List[int]]:
        return {ref.stage: list(ref.requires) for ref in self.stages}

    def seat_by_stage(self) -> Dict[int, str]:
        """The seat that owns each stage, for the stages that have one."""
        return {ref.stage: ref.seat for ref in self.stages if ref.seat is not None}

    def stages_for_seat(self, seat: str) -> Tuple[int, ...]:
        """The stages one core retinue seat owns, in order; empty for an unknown seat."""
        return tuple(ref.stage for ref in self.stages if ref.seat == seat)


# --- Stage Response Models for Model & Host Turns ---

class BaseStageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    stage: StrictInt
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    authority_effect: Literal["None"] = "None"
    demo_id: StrictStr
    should_continue: StrictBool


class AdmissionProposal(BaseModel):
    """Stage 1 repair object from stage_1_admit.yaml. AuthorityEffect: None."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["admit", "refuse", "needs_declaration"]
    grammar: StrictStr
    equality_test: StrictStr
    coefficient_profile: StrictStr
    missing_declarations: List[StrictStr]
    reason: StrictStr


class IdeationCandidate(BaseModel):
    """One stage 2 candidate object from stage_2_ideation.yaml."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: StrictStr = Field(min_length=1)
    kind: Literal["construction", "refutation", "weakening"]
    statement: StrictStr = Field(min_length=1)
    assumptions: List[StrictStr]
    check_without_llm: StrictBool


class AuditItem(BaseModel):
    """One stage 3 audit object from stage_3_audit.yaml."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: StrictStr
    routing: Literal["extract", "hold", "reject"]
    reasons: List[StrictStr]
    source_quotes: List[StrictStr]
    imported_assumptions: List[StrictStr]


class ProposalObject(BaseModel):
    """Default `{proposal: string}` object in the stage 4 and stage 6 YAML schemas."""

    model_config = ConfigDict(extra="forbid")

    proposal: StrictStr


def _stage_object(value: Any) -> Any:
    """Keep the YAML proposal object. Any other object is one the runner's bound schema accepted."""
    if type(value) is not dict:
        raise ValueError("STAGE_OBJECT_REQUIRED")
    if set(value) == {"proposal"}:
        return ProposalObject.model_validate(value)
    return dict(value)


StageObject = Annotated[Union[ProposalObject, Dict[str, Any]], BeforeValidator(_stage_object)]


class Stage1Response(BaseStageResponse):
    """Stage 1 model repair turn. The host admission record is a different object."""

    stage: Literal[1] = 1
    admission_proposal: AdmissionProposal


class Stage2Response(BaseStageResponse):
    stage: Literal[2] = 2
    candidates: List[IdeationCandidate] = Field(min_length=5, max_length=7)


class Stage3Response(BaseStageResponse):
    stage: Literal[3] = 3
    audits: List[AuditItem] = Field(min_length=1)


class Stage4Response(BaseStageResponse):
    stage: Literal[4] = 4
    candidate_id: StrictStr
    coefficient_profile: StrictStr
    source_quotes: List[StrictStr]
    missing_fields: List[StrictStr]
    candidate: StageObject


class Stage5Response(BaseStageResponse):
    stage: Literal[5] = 5
    # No defaults: a host verdict that was never computed must not read as a pass.
    host_verdict: StrictStr
    exact_checks_passed: StrictBool
    surviving_candidates: List[StrictStr] = Field(default_factory=list)


class ChallengeItem(BaseModel):
    """One stage 6 challenge from stage_6_adversarial.yaml."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: StrictStr
    claim: StrictStr
    witness: StageObject
    expected_accept: StrictBool
    required_check: StrictStr


class Stage6Response(BaseStageResponse):
    """Stage 6. `expected_accept` is a hypothesis. No field is a host verdict."""

    stage: Literal[6] = 6
    challenges: List[ChallengeItem]


class ReceiptObligation(BaseModel):
    """One stage 9 obligation. AuthorityEffect: None."""

    model_config = ConfigDict(extra="forbid")

    code: StrictStr
    refusal_map_key: StrictStr


class Stage9Response(BaseStageResponse):
    """Stage 9 receipt. should_continue is required and has no pass default."""

    stage: Literal[9]
    terminal: StrictStr
    remaining_obligations: List[ReceiptObligation]
    diagnostic_only: StrictBool


class Stage10Response(BaseStageResponse):
    """Stage 10 hand-off. authorized_by stays null."""

    stage: Literal[10]
    terminal: StrictStr
    routing_terminal: StrictStr
    remaining_obligations: List[ReceiptObligation]
    authorized_by: Literal[None]


class Stage11Response(BaseStageResponse):
    """Stage 11 evidence plan. Required fields match the stage 11 response schema."""

    stage: Literal[11]
    scoped_summary: StrictStr
    remaining_obligations: List[StrictStr]
    next_seed: StrictStr
    proposed_tests: List[StrictStr]


class ReplayOutcome(str, Enum):
    """Host grading of one adversarial witness. AuthorityEffect: None.

    OPEN_OBSTRUCTION: the host checker accepted a witness that is not the stage 4
    candidate. The witness is an undischarged challenge to the acceptance claim,
    whatever the adversary predicted.
    CONTROL: the adversary predicted rejection and the host rejected the witness.
    DISCARDED: the host rejected a witness the adversary predicted it would accept
    (a failed attack), or the witness is the stage 4 candidate itself.
    """

    OPEN_OBSTRUCTION = "OPEN_OBSTRUCTION"
    CONTROL = "CONTROL"
    DISCARDED = "DISCARDED"


def replay_outcome(expected_accept: bool, host_accepted: bool, same_as_candidate: bool) -> ReplayOutcome:
    if same_as_candidate:
        return ReplayOutcome.DISCARDED
    if host_accepted:
        return ReplayOutcome.OPEN_OBSTRUCTION
    return ReplayOutcome.CONTROL if not expected_accept else ReplayOutcome.DISCARDED


class WitnessReplay(BaseModel):
    """One stage 6 witness as the stage 7 host replay graded it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: StrictInt = Field(ge=0)
    candidate_id: StrictStr = Field(min_length=1)
    expected_accept: StrictBool
    host_accepted: StrictBool
    same_as_candidate: StrictBool
    outcome: ReplayOutcome
    failure_reasons: Tuple[StrictStr, ...] = ()

    @property
    def prediction_matched(self) -> bool:
        return self.expected_accept is self.host_accepted

    @model_validator(mode="after")
    def outcome_follows_host_facts(self) -> WitnessReplay:
        if self.outcome is not replay_outcome(self.expected_accept, self.host_accepted, self.same_as_candidate):
            raise ValueError("REPLAY_OUTCOME_MISMATCH")
        return self


class ChallengeReplay(BaseModel):
    """Host replay (stage 7) of every witness the adversarial stage 6 proposed.

    `stage` names the stage whose witnesses were replayed. AuthorityEffect: None.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    demo_id: StrictStr = Field(min_length=1)
    stage: Literal[6]
    authority_effect: Literal["None"] = "None"
    witnesses: Tuple[WitnessReplay, ...] = ()

    @model_validator(mode="after")
    def indices_are_dense(self) -> ChallengeReplay:
        if tuple(item.index for item in self.witnesses) != tuple(range(len(self.witnesses))):
            raise ValueError("REPLAY_INDEX_MISMATCH")
        return self

    @property
    def obstruction_indices(self) -> Tuple[int, ...]:
        return tuple(w.index for w in self.witnesses if w.outcome is ReplayOutcome.OPEN_OBSTRUCTION)

    @property
    def checked_count(self) -> int:
        """Witnesses the host checked that differ from the candidate."""
        return sum(1 for w in self.witnesses if not w.same_as_candidate)


class Stage7Response(BaseModel):
    """Host stage 7 record. The model does not supply `host_replay`."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    stage: Literal[7] = 7
    demo_id: StrictStr = Field(min_length=1)
    authority_effect: Literal["None"] = "None"
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    host_replay: ChallengeReplay
    obstruction_indices: List[StrictInt]
    checked_count: StrictInt = Field(ge=0)


class Stage8Response(BaseModel):
    """Host stage 8 selection record. One survivor is SELECT; none is REJECT."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    stage: Literal[8] = 8
    demo_id: StrictStr = Field(min_length=1)
    authority_effect: Literal["None"] = "None"
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    seat: Literal["seat_the_master"] = "seat_the_master"
    disposition: Literal["SELECT", "REJECT"]
    selected_candidate_id: Optional[StrictStr]
    survivors: List[StrictStr]
    rule: Literal["STAGE5_SURVIVORS_LESS_STAGE7_OBSTRUCTIONS"]

    @model_validator(mode="after")
    def selection_agrees(self) -> Stage8Response:
        selected = [self.selected_candidate_id] if self.disposition == "SELECT" else []
        if self.survivors != selected or (self.disposition == "REJECT" and self.selected_candidate_id is not None):
            raise ValueError("SELECTION_RECORD_MISMATCH")
        return self


# Stages whose reply the runner checks against the stage YAML response_schema.
SCHEMA_RESPONSE_MODELS: Dict[int, type[BaseModel]] = {
    1: Stage1Response,
    2: Stage2Response,
    3: Stage3Response,
    4: Stage4Response,
    6: Stage6Response,
    11: Stage11Response,
}


ResponseModel = Union[
    Stage1Response,
    Stage2Response,
    Stage3Response,
    Stage4Response,
    Stage5Response,
    Stage6Response,
    Stage7Response,
    Stage8Response,
    Stage9Response,
    Stage10Response,
    Stage11Response,
]
