"""Origin claim: one small workflow for IDE host steps and Python callbacks. AuthorityEffect: None.

Observations are reports from the bound executor, not checker certificates.
There is no provider discovery, tool execution, scheduler or background worker here.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from adversary.domain.checked_reuse import BoundReuseFile, CheckedReuseResult
from adversary.domain.ddc_program import DdcProgramBinding
from adversary.domain.native_gate_check import (
    NativeGateCheck,
    decode_native_json,
    native_gate_summary,
    validate_native_gate_receipt,
)
from adversary.use_cases.teamwork_schedule import PanelSchedule, seat_decision

CURRENT_TEAMWORK_VERSIONS = ("core.adversary.teamwork.v3", "core.adversary.teamwork.v4")

PANEL_ROLE_ORDER = (
    "syntax_prefilter", "scope_guard", "context_transport", "punchlist", "gauge_breaker", "bare_metal_anchor",
    "defect_hunter", "boundary_fuzzer", "overconfidence_probe", "anti_hype", "quarantine", "resilience",
    "custody", "covert_verifier", "pontius_integrity_auditor", "mark_hardware_constraint", "truth_repair",
    "primal_dual", "backdoor_auditor", "master", "adversary", "scar_chronicler",
)

PRESET_CONFIGURATIONS = {
    "all-anthropic": {
        "tier_frontier": "anthropic/claude-3.7-sonnet",
        "tier_reasoning": "anthropic/claude-3.7-sonnet:thinking",
        "tier_standard": "anthropic/claude-3.5-sonnet",
        "tier_fast": "anthropic/claude-3.5-haiku",
    },
    "cross-family": {
        "tier_frontier": "anthropic/claude-3.7-sonnet",
        "tier_reasoning": "openai/o3-mini",
        "tier_standard": "openai/gpt-4o",
        "tier_fast": "google/gemini-2.5-flash",
    },
    "cheap-falsifiers": {
        "tier_frontier": "anthropic/claude-3.5-sonnet",
        "tier_reasoning": "deepseek/deepseek-r1",
        "tier_standard": "openai/gpt-4o-mini",
        "tier_fast": "google/gemini-2.5-flash-lite",
    },
}


def load_panel_preset(name: str) -> dict[str, str]:
    """Load preset tier-to-model mapping from panel_presets.yaml or built-in dictionary."""
    try:
        from importlib.resources import files

        import yaml
        resource = files("adversary").joinpath("roles", "panel_presets.yaml")
        raw = resource.read_bytes()
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and "presets" in data and name in data["presets"]:
            return data["presets"][name]["tiers"]
    except Exception:
        pass
    if name in PRESET_CONFIGURATIONS:
        return PRESET_CONFIGURATIONS[name]
    raise ValueError(f"PRESET_UNKNOWN: {name}; declared: {sorted(PRESET_CONFIGURATIONS)}")


@dataclass
class FalsificationTicket:
    ticket_id: str
    seat_id: str = ""
    candidate_digest: str = ""
    claim_text: str = ""
    creator_role: str = ""
    defect_description: str = ""
    timestamp: float = 0.0
    status: str = "PENDING"  # PENDING, REPRODUCED, REFUTED_AS_FALSE_ALARM, STALE_PURGED

    def __post_init__(self) -> None:
        if not self.seat_id and self.creator_role:
            self.seat_id = self.creator_role
        elif not self.creator_role and self.seat_id:
            self.creator_role = self.seat_id
        if not self.claim_text and self.defect_description:
            self.claim_text = self.defect_description
        elif not self.defect_description and self.claim_text:
            self.defect_description = self.claim_text


class FalsificationQueue:
    """Digest-pinned falsification queue in the durable run ledger.

    Invariants:
    - Tickets referencing stale candidate digests are rejected with STALE_CANDIDATE_DIGEST.
    - Claims are admitted only on the active candidate digest.
    - Execution maintains FIFO ordering for active candidate evaluations.
    """

    def __init__(self, active_candidate_digest: str) -> None:
        self.active_candidate_digest = active_candidate_digest
        self.queue: list[FalsificationTicket] = []
        self.history: list[FalsificationTicket] = []

    def enqueue(self, ticket: FalsificationTicket) -> FalsificationTicket:
        if ticket.candidate_digest != self.active_candidate_digest:
            raise ValueError(
                f"STALE_CANDIDATE_DIGEST: claim references {ticket.candidate_digest}, active is {self.active_candidate_digest}"
            )
        self.queue.append(ticket)
        return ticket

    def submit(self, seat_id: str, candidate_digest: str, claim_text: str, timestamp: float = 0.0) -> FalsificationTicket:
        if candidate_digest != self.active_candidate_digest:
            raise ValueError(f"STALE_CANDIDATE_DIGEST: claim references {candidate_digest}, active is {self.active_candidate_digest}")
        for existing in self.queue:
            if existing.seat_id == seat_id and existing.candidate_digest == candidate_digest and existing.claim_text == claim_text:
                return existing
        ticket_id = hashlib.sha256(f"{seat_id}:{candidate_digest}:{claim_text}:{len(self.queue)}".encode("utf-8")).hexdigest()[:16]
        ticket = FalsificationTicket(
            ticket_id=ticket_id,
            seat_id=seat_id,
            candidate_digest=candidate_digest,
            claim_text=claim_text,
            timestamp=timestamp,
            status="PENDING",
        )
        self.queue.append(ticket)
        return ticket

    def pop_for_falsifier(self) -> FalsificationTicket | None:
        if not self.queue:
            return None
        return self.queue.pop(0)

    def size(self) -> int:
        return len(self.queue)

    def pending_tickets(self) -> list[str]:
        return [t.ticket_id for t in self.queue]

    def advance_candidate(self, new_candidate_digest: str) -> list[FalsificationTicket]:
        """Advance the active candidate digest; purges/stales remaining un-evaluated tickets."""
        self.active_candidate_digest = new_candidate_digest
        purged = list(self.queue)
        for ticket in self.queue:
            ticket.status = "STALE_PURGED"
            self.history.append(ticket)
        self.queue.clear()
        return purged

    def process_ticket(self, verifier_oracle: Callable[[str], bool]) -> FalsificationTicket | None:
        if not self.queue:
            return None
        ticket = self.queue.pop(0)
        is_reproduced = verifier_oracle(ticket.claim_text)
        ticket.status = "REPRODUCED" if is_reproduced else "REFUTED_AS_FALSE_ALARM"
        self.history.append(ticket)
        return ticket


class PanelStep(BaseModel):
    """One required contribution; a role name never authenticates a worker."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    role_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    cognitive_operator: str = Field(min_length=1)
    pipeline_acts: tuple[str, ...] = Field(min_length=1)
    model_tiers: tuple[str, ...] = Field(min_length=1)
    default_tier: str = Field(min_length=1)
    phase: Literal["intake", "build", "review", "learning"]
    kind: Literal["build", "review", "learn"]
    communication: Literal["pfp", "deterministic"] = "pfp"
    operation_binding: dict[str, Any] | None = None
    model: str | None = None

    @model_serializer(mode="wrap")
    def versioned_wire(self, handler):
        result = handler(self)
        if self.operation_binding is None:
            result.pop('operation_binding', None)
        if self.model is None:
            result.pop('model', None)
        return result


class PanelPlan(BaseModel):
    """Frozen governed roster and order carried by every new orchestrated run."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["core.adversary.panel-plan.v1", "core.adversary.panel-plan.v2"] = "core.adversary.panel-plan.v1"
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_version: str = Field(min_length=1)
    steps: tuple[PanelStep, ...]
    # Optional declared schedule; absent means the full scene-by-scene Panel.
    schedule: PanelSchedule | None = None
    preset: str | None = None

    @model_serializer(mode="wrap")
    def versioned_wire(self, handler):
        result = handler(self)
        if self.schedule is None:
            result.pop("schedule", None)  # Plans without a schedule keep their original hash.
        if self.preset is None:
            result.pop("preset", None)  # Plans without a preset keep their original hash.
        return result

    @model_validator(mode="after")
    def validate_totality(self):
        _require_panel_order(self)
        for index, step in enumerate(self.steps):
            _validate_panel_step(self, index, step)
        return self

    @property
    def plan_sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.model_dump(mode="json"), sort_keys=True,
            separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _role_ids(steps) -> tuple:
    return tuple(step.role_id for step in steps)


def _seat_ids(schedule) -> tuple:
    return tuple(seat.role_id for seat in schedule.seats)


def _require_panel_order(plan: PanelPlan) -> None:
    if _role_ids(plan.steps) != PANEL_ROLE_ORDER:
        raise ValueError("PANEL_TOTALITY_REQUIRED: retain the versioned 22-role order")
    if plan.schedule is None:
        return
    if _seat_ids(plan.schedule) != PANEL_ROLE_ORDER:
        raise ValueError("SCHEDULE_ROSTER_MISMATCH: a schedule names every role in roster order")


def _panel_stage(index: int) -> tuple[str, str]:
    if index < 5:
        return ("intake", "review")
    if index == 5:
        return ("build", "build")
    if index == 21:
        return ("learning", "learn")
    return ("review", "review")


def _operation_lookup(inventory):
    found = {}
    for skill in inventory.skills:
        for op in skill.ops:
            found[op.op_id] = op
    return found


def _validate_bound_operation(step: PanelStep) -> None:
    from operads.skill_operad.skill_compiler.op_inventory import (
        OpInventory,
        Wire,
        wire_term,
    )
    binding = step.operation_binding
    if binding.get("role_id") != step.role_id:
        raise ValueError("OPERATION_ROLE_MISMATCH")
    inventory = OpInventory.model_validate(binding["inventory"])
    term = wire_term(Wire.model_validate(binding["op_term"]), _operation_lookup(inventory))
    if term.op.target_color != "State":
        raise ValueError("OPERATION_STAGE_OUTPUT_MISMATCH")


def _validate_operation_binding(plan: PanelPlan, step: PanelStep) -> None:
    bound = step.operation_binding is not None
    if plan.schema_version.endswith(".v2") != bound:
        raise ValueError("PANEL_OPERATION_BINDING_REQUIRED")
    if step.operation_binding is None:
        return
    _validate_bound_operation(step)


def _validate_panel_communication(step: PanelStep) -> None:
    if step.role_id == "syntax_prefilter":
        if step.communication != "deterministic" or step.model_tiers != ("no_llm",):
            raise ValueError("SYNTAX_PREFILTER_MUST_BE_DETERMINISTIC")
        return
    if step.communication != "pfp" or "no_llm" in step.model_tiers:
        raise ValueError("PANEL_PFP_REQUIRED")


def _validate_panel_step(plan: PanelPlan, index: int, step: PanelStep) -> None:
    _validate_operation_binding(plan, step)
    if (step.phase, step.kind) != _panel_stage(index):
        raise ValueError("PANEL_STAGE_MISMATCH")
    if step.default_tier not in step.model_tiers:
        raise ValueError("PANEL_TIER_MISMATCH")
    _validate_panel_communication(step)


def _panel_role_id(member: dict) -> str:
    sketch = member.get("sketch", "")
    if not isinstance(sketch, str) or not sketch.startswith("adversary_panel/") or not sketch.endswith(".md"):
        raise ValueError("PANEL_SKETCH_INVALID")
    return sketch.removeprefix("adversary_panel/").removesuffix(".md")


def _panel_members(roster: list[dict]) -> dict:
    members = {}
    for member in roster:
        role_id = _panel_role_id(member)
        if role_id in members:
            raise ValueError("PANEL_DUPLICATE_ROLE")
        members[role_id] = member
    if set(members) != set(PANEL_ROLE_ORDER):
        raise ValueError("PANEL_TOTALITY_REQUIRED: governed roster must contain exactly 22 members")
    return members


def _compiled_step(index: int, role_id: str, member: dict) -> PanelStep:
    phase, kind = _panel_stage(index)
    communication = "pfp"
    if role_id == "syntax_prefilter":
        communication = "deterministic"
    return PanelStep(role_id=role_id, name=member["name"], role=member["role"],
        cognitive_operator=member["cognitive_operator"], pipeline_acts=member["pipeline_acts"],
        model_tiers=member["model_tiers"], default_tier=member["default_tier"],
        phase=phase, kind=kind, communication=communication)


def _compiled_steps(members: dict) -> tuple:
    steps = []
    for index, role_id in enumerate(PANEL_ROLE_ORDER):
        steps.append(_compiled_step(index, role_id, members[role_id]))
    return tuple(steps)


def build_panel_plan(roster: list[dict], *, source_sha256: str,
                      source_version: str) -> PanelPlan:
    """Compile supplied governed YAML data; loading bytes belongs to the host."""
    return PanelPlan(source_sha256=source_sha256, source_version=source_version,
        steps=_compiled_steps(_panel_members(roster)))


class TeamworkObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_id: str = Field(min_length=1)
    worker: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    content: str = ""
    findings: tuple[str, ...] = ()
    artifacts: dict[str, str] = Field(default_factory=dict)
    blocked: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    intelligence: IntelligenceRead | None = None
    check: TaskCheck | None = None
    ddc_program: TeamworkDdcProgram | None = None

    @model_serializer(mode="wrap")
    def retained_wire(self, handler):
        result = handler(self)
        if self.ddc_program is None:
            result.pop("ddc_program", None)
        return result


class TeamworkHostObservation(BaseModel):
    """Captured pre-learning facts, not provider authorization or an invoice."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["core.adversary.host-observation.v1"] = "core.adversary.host-observation.v1"
    observations_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    observation_count: int = Field(ge=0)
    executor: Literal["ide", "openrouter", "anthropic"]
    provider_attempt_count: int = Field(ge=0)
    known_cost_attempt_count: int = Field(ge=0)
    unknown_cost_attempt_count: int = Field(ge=0)
    known_cost_usd: str = Field(pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")
    billing_status: Literal["UNOBSERVED", "KNOWN_COST", "UNKNOWN_COST"]
    stopped_status: Literal["", "partial", "blocked"] = ""
    stopped_reason: str = ""


class TeamworkDdcProgram(BaseModel):
    """Host readback of the existing retained procedure, never task acceptance."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    binding: DdcProgramBinding
    run_path: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    steps: tuple[dict[str, Any], ...] = Field(min_length=1)
    premises: dict[str, Any]
    fresh_checker_required: Literal[True] = True
    mathematical_acceptance: Literal["UNVERIFIED"] = "UNVERIFIED"
    authority_effect: Literal["None"] = "None"
    learning_reply_binding: dict[str, str] | None = None
    host_observation: TeamworkHostObservation | None = None

    @model_serializer(mode="wrap")
    def retained_wire(self, handler):
        result = handler(self)
        if self.learning_reply_binding is None:
            result.pop("learning_reply_binding", None)
        if self.host_observation is None:
            result.pop("host_observation", None)
        return result

    @model_validator(mode="after")
    def validate_learning_reply_binding(self):
        if self.learning_reply_binding is not None and self.learning_reply_binding != {
                "consumed_ddc_root": self.binding.semantic_ddc_root,
                "consumed_procedure_sha256": self.procedure_sha256}:
            raise ValueError("DDC_CONSUMPTION_BINDING_MISMATCH: supply the host-computed program identity")
        return self

    @field_validator("binding", mode="before")
    @classmethod
    def parse_binding(cls, value):
        return DdcProgramBinding.model_validate_json(json.dumps(value)) if type(value) is dict else value

    @property
    def procedure_sha256(self) -> str:
        return hashlib.sha256(json.dumps(self.binding.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")).hexdigest()


class IntelligenceRead(BaseModel):
    """Host readback, not admission or a lifecycle certificate."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    initial_task_id: str
    source_id: str
    source_locator: str
    parent_source_id: str | None = None
    findings: tuple[str, ...] = ()
    coverage_gaps: tuple[str, ...] = ()


class TaskCheck(BaseModel):
    """Host operation observation; command names the operation, not a subprocess.

    Syntax Prefilter runs in process. Original-task acceptance can run the bound command.
    Editable observations authenticate neither host execution nor operator trust.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    initial_task_id: str
    source_id: str
    checker_id: str = Field(min_length=1)
    command: tuple[str, ...] = Field(min_length=1)
    exit_status: int = Field(strict=True)
    output_sha256: str
    artifacts: dict[str, str]


class HostAcceptanceRequirement(BaseModel):
    """Operator-bound independent acceptance, separate from model role review."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    checker_id: str = Field(min_length=1)
    operation: tuple[str, ...] = Field(min_length=1)
    check_source_paths: dict[str, str] = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def retained_wire(self, handler):
        result = handler(self)
        if not self.check_source_paths:
            result.pop("check_source_paths", None)
        return result


class TeamworkContinuation(BaseModel):
    """Explicit operator resumption; the old observations and limits remain."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    after_observations: int = Field(ge=0, strict=True)
    reason: str = Field(min_length=1)
    parent_state_path: str = Field(min_length=1)
    parent_state_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    additional_repairs: int = Field(default=0, ge=0, le=3, strict=True)
    additional_actions: int = Field(default=0, ge=0, strict=True)
    acceptance_successor: HostAcceptanceRequirement | None = None

    @model_serializer(mode="wrap")
    def retained_wire(self, handler):
        result = handler(self)
        if self.acceptance_successor is None:
            result.pop("acceptance_successor", None)
        return result


class AttachedOperad(BaseModel):
    """Reviewed self-digestion guidance for named seats; text bound to its catalogue digest."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    skill_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    seats: tuple[str, ...] = Field(min_length=1)
    instruction_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    guidance: str = Field(min_length=1, max_length=4096)

    @model_validator(mode="after")
    def guidance_matches_digest(self):
        if hashlib.sha256(self.guidance.encode("utf-8")).hexdigest() != self.instruction_sha256:
            raise ValueError("ATTACHED_OPERAD_DIGEST_MISMATCH")
        return self


class TeamworkBrief(BaseModel):
    """Task guidance and preferred workers, never a substitute for required roles."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    deliverable: str = ""
    constraints: tuple[str, ...] = ()
    acceptance: tuple[str, ...] = ()
    builder: str = "Scope Guard"
    reviewer: str = "Defect Hunter"
    repairer: str = "Primal Dual"
    scene: str = ""
    skills: tuple[str, ...] = ()
    anti_skills: tuple[str, ...] = ()
    response_profile: Literal["legacy-v1", "compact-v1", "compact-v2"] = "legacy-v1"
    context_profile: Literal["legacy-v1", "bounded-v1"] = "legacy-v1"
    clarification_policy: Literal["strict-query-v1"] | None = None
    artifact_schema: dict[str, Any] | None = None
    checked_reuse_registry: BoundReuseFile | None = None
    checked_reuse_result: CheckedReuseResult | None = None
    checked_reuse_candidate: str | None = None
    task_premises: dict[str, Any] | None = None
    density_dimension: int | None = Field(default=None, ge=28, le=1024, strict=True)
    forge_organization: bool | None = Field(default=None, strict=True)
    forge_preparation: dict[str, Any] | None = None
    operads: tuple[AttachedOperad, ...] = ()

    @model_serializer(mode="wrap")
    def retain_optional_profile(self, handler):
        result = handler(self)
        # Old prompts/action digests keep their original wire representation.
        if self.response_profile == "legacy-v1":
            result.pop("response_profile", None)
        if self.context_profile == "legacy-v1":
            result.pop("context_profile", None)
        if self.artifact_schema is None:
            result.pop("artifact_schema", None)
        for key in ("checked_reuse_registry", "checked_reuse_result", "checked_reuse_candidate", "task_premises", "clarification_policy", "density_dimension", "forge_organization", "forge_preparation"):
            if result.get(key) is None:
                result.pop(key, None)
        if not self.operads:
            result.pop("operads", None)
        return result

    @model_validator(mode="after")
    def validate_artifact_schema(self):
        _validate_checked_reuse(self)
        _validate_closed_schema(self)
        _validate_clarification_policy(self)
        return self


class OptionalToolRoute(BaseModel):
    """An optional host tool alternative for the same required contribution."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    tool: str = Field(min_length=1)
    alternative: str = Field(min_length=1)
    operator: str = ""
    scene: str = ""
    skills: tuple[str, ...] = ()


class TeamworkAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_id: str
    run_id: str = ""
    kind: Literal["build", "review", "repair", "recheck", "digest", "learn", "ddc_store", "ddc_complete", "native_gates"]
    objective: str
    instructions: str
    candidate: str = ""
    findings: tuple[str, ...] = ()
    artifacts: dict[str, str] = Field(default_factory=dict)
    intelligence: IntelligenceRead | None = None
    initial_task_id: str = ""
    checker_id: str = ""
    check_command: tuple[str, ...] = ()
    source_reads: tuple[IntelligenceRead, ...] = ()
    role_id: str = ""
    phase: str = ""
    communication: Literal["pfp", "deterministic", "host"] = "pfp"
    workflow_version: str = "core.adversary.teamwork.v1"
    plan_sha256: str = ""
    role_contributions: tuple[dict[str, Any], ...] = ()
    check_source_id: str = ""
    check_source_paths: dict[str, str] = Field(default_factory=dict)
    ddc_program: TeamworkDdcProgram | None = None
    acceptance_predecessors: tuple[HostAcceptanceRequirement, ...] = ()
    stopped_reason: str = ""
    stopped_status: Literal["", "partial", "blocked"] = ""
    evaluations_used: int = Field(default=0, ge=0, strict=True)
    evaluation_limit: int = Field(default=10, ge=1, le=10, strict=True)
    brief: TeamworkBrief | None = None
    operator: str = ""
    route: OptionalToolRoute | None = None
    feedback_policy: Literal["semantic_digestion_v1", "semantic_digestion_v2"] | None = None
    learning_context: dict[str, Any] | None = None
    clarification_context: dict[str, Any] | None = None
    native_gate_check: NativeGateCheck | None = None
    native_gate_batches: tuple[dict[str, Any], ...] = ()
    native_host_observations: tuple[dict[str, Any], ...] = ()
    operation_binding: dict[str, Any] | None = None
    operation_required: bool = False
    model_tier: str = ""
    assigned_model: str = ""
    assigned_family: str = ""

    @model_serializer(mode="wrap")
    def versioned_wire(self, handler):
        result = handler(self)
        _pop_absent_binding(self, result)
        _pop_blank_fields(result, ("model_tier", "assigned_model", "assigned_family"))
        _pop_blank_fields(result, ("brief", "operator", "route", "feedback_policy", "learning_context", "clarification_context"))
        _pop_historical_action_fields(self, result)
        return result


class TeamworkRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["core.adversary.teamwork.v1", "core.adversary.teamwork.v2", "core.adversary.teamwork.v3", "core.adversary.teamwork.v4"] = "core.adversary.teamwork.v1"
    run_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    executor: Literal["ide", "openrouter", "anthropic"] = "ide"
    max_repairs: int = Field(default=1, ge=0, le=3, strict=True)
    max_actions: int = Field(default=32, ge=1, strict=True)
    learn_after_run: bool = Field(default=False, strict=True)
    provider_binding: dict[str, Any] | None = None
    continuations: tuple[TeamworkContinuation, ...] = ()
    observations: tuple[TeamworkObservation, ...] = ()
    pending_prompt: dict[str, Any] | None = None
    intelligence: IntelligenceRead | None = None
    checker_id: str = ""
    check_command: tuple[str, ...] = ()
    panel_plan: PanelPlan | None = None
    acceptance_check: HostAcceptanceRequirement | None = None
    max_evaluations: int = Field(default=10, ge=1, le=10, strict=True)
    episode_binding: dict[str, Any] | None = None
    brief: TeamworkBrief | None = None
    feedback_policy: Literal["semantic_digestion_v1", "semantic_digestion_v2"] | None = None
    native_gate_check: NativeGateCheck | None = None

    @model_serializer(mode="wrap")
    def versioned_wire(self, handler):
        result = handler(self)
        if self.pending_prompt is None:
            result.pop("pending_prompt", None)
        if self.brief is None:
            result.pop("brief", None)
        if self.feedback_policy is None:
            result.pop("feedback_policy", None)
        if self.schema_version != "core.adversary.teamwork.v4":
            result.pop("native_gate_check", None)
        if self.schema_version not in CURRENT_TEAMWORK_VERSIONS:
            result.pop("max_evaluations", None)
            result.pop("episode_binding", None)
            if result.get("acceptance_check"):
                result["acceptance_check"].pop("check_source_paths", None)
        return result

    @model_validator(mode="after")
    def validate_workflow(self):
        _validate_clarification_acceptance(self)
        _validate_feedback_policy_version(self)
        if self.schema_version in ("core.adversary.teamwork.v2", *CURRENT_TEAMWORK_VERSIONS):
            _validate_panel_workflow(self)
        elif self.panel_plan is not None or self.acceptance_check is not None:
            raise ValueError("LEGACY_PANEL_BACKDATE_FORBIDDEN")
        _reject_legacy_native_gate(self)
        return self

    @property
    def work_status(self) -> str:
        stage, _producer = _course(self)
        if self.schema_version in CURRENT_TEAMWORK_VERSIONS:
            stopped = _trace_v3(self)[8]["stopped_status"]
            if stopped:
                return stopped
        return "pending_host" if stage in _INSTRUCTIONS else stage

    @property
    def evidence_verdict(self) -> str:
        return "OPEN_RESIDUAL"

    @property
    def native_gate_coverage(self) -> dict[str, Any]:
        if self.schema_version != "core.adversary.teamwork.v4":
            return {"status": "LEGACY_UNMEASURED", "authority_effect": "None"}
        _trace(self)
        receipt = next((item.metadata.get("native_gate_receipt") for item in reversed(self.observations)
                        if item.metadata.get("native_gate_receipt")), None)
        return native_gate_summary(receipt)

    @property
    def panel_coverage(self) -> dict[str, Any]:
        """Observed role contributions, never independent-agent or correctness claims."""
        if self.panel_plan is None:
            return {"status": "LEGACY_UNMEASURED", "required": [], "observed": [],
                    "missing": [], "complete": False}
        return _measured_panel_coverage(self)

    @property
    def continuation_status(self) -> dict[str, Any]:
        trace = _trace(self)
        stage, _producer, spent, limits, reason, pending, findings = trace[:7]
        return _continuation_record(self, trace, stage, spent, limits, reason, pending, findings)


POST_RUN_LEARNING_INSTRUCTIONS = (
    "Use /auto-oe-autop once in its scoped post-run mode in the current IDE session; "
    "its finish invokes /auto-learn once. Read relevant existing skills, rules and "
    "source-bound lessons first. Inspect "
    "this run's actual work and failures, choose a supported useful correction, and apply it "
    "to the existing owning skill, rule, prompt or code file. Reuse the current catalog; "
    "do not create another framework or a report-only substitute. Inspect the changed bytes "
    "and recheck the original task with the relevant focused check. Return actual changed "
    "paths in metadata.changed_paths and observed checks in metadata.verification, or a "
    "justified metadata.no_change_reason when existing guidance already covers the lesson "
    "or evidence does not support a repair. Put unresolved defects of the original work in "
    "findings so the existing repair path handles them. Keep the original deliverable; "
    "do not replace it with the learning summary. No recursive Adversary run, concurrency, "
    "broad repository sweep or new receipt is required. A text-only provider can propose "
    "lessons, but must mark metadata.proposed_only true and cannot claim installed changes "
    "or executed IDE skills."
)


_INSTRUCTIONS = {
    "native_gates": "Execute the bound native primary, intergate and empirical predicates at this workflow checkpoint. Retain actual witness/source/binary/spec/candidate bindings and residuals. Native diagnostics never replace independent original-task acceptance.",
    "build": (
        "Scope Guard/build: recall task-relevant existing rules, skills and source-bound learned "
        "guidance before planning; read the useful existing owners rather than the whole "
        "catalog. Inspect the task, make a short practical plan and produce the requested "
        "artifact with your actual tools. For edits, carry a short checklist of the original "
        "public API and invariants that must survive into each worker brief. Attach useful "
        "existing skills when needed. Return "
        "what you did, candidate content, actual artifact hashes and checks. Identify the real "
        "worker; role names alone do not mean independent agents ran."
    ),
    "review": (
        "Defect Hunter/review: inspect the actual artifact and acceptance requirements. For edits, "
        "review the complete diff against the original baseline and retained APIs/invariants "
        "as well as the repaired failure; narrow green checks do not cover omitted behavior. Report only "
        "actionable findings with evidence; an empty findings list means this focused review "
        "found none. Do not invent test execution or checker acceptance."
    ),
    "repair": (
        "Primal Dual/repair: recover the original requirements and, for edits, reread the "
        "relevant original source and invariant checklist alongside the latest failure. "
        "Repair the recorded findings with the "
        "smallest useful change, preserve unaffected behavior, then run the "
        "focused check that decides them. Keep the same objective, permissions and executor. "
        "Return changed content, actual artifact hashes and observed checks."
    ),
    "recheck": (
        "Recheck the original task and every affected descendant against current artifact "
        "bytes using the actual host checker. Retain command, output and checker identity. "
        "A proposed repair or an admitted candidate alone does not close work."
    ),
    "digest": (
        "Digest the intelligence of this work, including the digester's own findings and "
        "wrong lessons. Read the actual resulting report through the existing extractor. "
        "New obstruction returns to repair under the same initial task. An administrative "
        "receipt alone is not new semantic work. Record complete coverage and actual bytes."
    ),
    "learn": POST_RUN_LEARNING_INSTRUCTIONS,
    "ddc_store": "Store the actual observed DDC procedure and read back its sealed native bundle before Scar Chronicler. No retained verdict accepts the original task.",
    "ddc_complete": "Verify Scar Chronicler's actual checked procedure consumption; store and read back final work and learning, retaining every stopped reason and open finding. Original-task acceptance remains independent.",
}


def _pop_blank_fields(result: dict, names: tuple[str, ...]) -> None:
    for name in names:
        if not result.get(name):
            result.pop(name, None)


def _pop_named(result: dict, names: tuple[str, ...]) -> None:
    for name in names:
        result.pop(name, None)


def _pop_absent_binding(action: TeamworkAction, result: dict) -> None:
    if action.operation_binding is None:
        result.pop("operation_binding", None)
    if not action.operation_required:
        result.pop("operation_required", None)
    if not action.acceptance_predecessors:
        result.pop("acceptance_predecessors", None)


def _pop_historical_action_fields(action: TeamworkAction, result: dict) -> None:
    if action.workflow_version != "core.adversary.teamwork.v4":
        _pop_named(result, ("native_gate_check", "native_gate_batches", "native_host_observations"))
    if action.workflow_version not in CURRENT_TEAMWORK_VERSIONS:
        _pop_named(result, ("run_id", "check_source_paths", "ddc_program", "stopped_reason",
                            "stopped_status", "evaluations_used", "evaluation_limit"))


def _reuse_selected(brief: TeamworkBrief):
    return (brief.checked_reuse_registry, brief.checked_reuse_result, brief.checked_reuse_candidate)


def _any_present(items) -> bool:
    for item in items:
        if item is not None:
            return True
    return False


def _any_missing(items) -> bool:
    for item in items:
        if item is None:
            return True
    return False


def _reuse_binding_broken(brief: TeamworkBrief, selected) -> bool:
    if _any_missing(selected):
        return True
    if brief.response_profile not in ("compact-v1", "compact-v2"):
        return True
    if brief.artifact_schema is not None:
        return True
    digest = hashlib.sha256(brief.checked_reuse_candidate.encode("utf-8")).hexdigest()
    if digest != brief.checked_reuse_result.target_candidate_sha256:
        return True
    return brief.checked_reuse_registry.sha256 != brief.checked_reuse_result.registry_sha256


def _validate_checked_reuse(brief: TeamworkBrief) -> None:
    selected = _reuse_selected(brief)
    if not _any_present(selected):
        return
    if _reuse_binding_broken(brief, selected):
        raise ValueError("CHECKED_REUSE_BRIEF_BINDING_MISMATCH")


def _non_string_key(required) -> bool:
    for key in required:
        if type(key) is not str:
            return True
    return False


def _closed_artifact_schema(schema: dict) -> bool:
    required = schema.get("required")
    properties = schema.get("properties")
    if schema.get("type") != "object":
        return False
    if schema.get("additionalProperties") is not False:
        return False
    if not isinstance(properties, dict) or not properties:
        return False
    if type(required) is not list or _non_string_key(required):
        return False
    if len(set(required)) != len(required):
        return False
    return set(required) == set(properties)


def _validate_closed_schema(brief: TeamworkBrief) -> None:
    if brief.artifact_schema is None:
        return
    if brief.response_profile not in ("compact-v1", "compact-v2"):
        raise ValueError("ARTIFACT_SCHEMA_PROFILE_REQUIRED")
    if not _closed_artifact_schema(brief.artifact_schema):
        raise ValueError("CLOSED_ARTIFACT_SCHEMA_REQUIRED")


def _clarification_unbound(brief: TeamworkBrief) -> bool:
    return brief.artifact_schema is None and brief.checked_reuse_result is None


def _validate_clarification_policy(brief: TeamworkBrief) -> None:
    if not brief.clarification_policy:
        return
    if brief.response_profile != "compact-v2" or brief.task_premises is None or _clarification_unbound(brief):
        raise ValueError("CLARIFICATION_POLICY_BINDING_REQUIRED")


def _validate_clarification_acceptance(run: TeamworkRun) -> None:
    if not run.brief or not run.brief.clarification_policy:
        return
    if (run.schema_version not in CURRENT_TEAMWORK_VERSIONS or run.acceptance_check is None
            or not run.acceptance_check.check_source_paths):
        raise ValueError("CLARIFICATION_ACCEPTANCE_BINDING_REQUIRED")


def _validate_feedback_policy_version(run: TeamworkRun) -> None:
    if run.feedback_policy and run.schema_version not in CURRENT_TEAMWORK_VERSIONS:
        raise ValueError("FEEDBACK_POLICY_WORKFLOW_MISMATCH: historical workflows cannot gain current obligations")


def _validate_v2_acceptance(run: TeamworkRun) -> None:
    if run.schema_version == "core.adversary.teamwork.v2" and run.intelligence and run.acceptance_check:
        raise ValueError("ACCEPTANCE_BINDING_CONFLICT: intelligence already binds original acceptance")


def _validate_current_allowance(run: TeamworkRun) -> None:
    if run.acceptance_check is None and not (run.intelligence and run.checker_id.strip() and run.check_command):
        raise ValueError("ACCEPTANCE_BINDING_REQUIRED: select the original independent host check")
    if run.max_actions < 3:
        raise ValueError("FINISH_ALLOWANCE_REQUIRED: reserve DDC storage, Scar Chronicler and final readback")
    if not run.feedback_policy:
        return
    floor = 4
    if run.schema_version == "core.adversary.teamwork.v4":
        floor = 5
    if run.max_actions < floor:
        raise ValueError("FINISH_ALLOWANCE_REQUIRED: reserve native intake, learning, digestion and final readback")


def _validate_v4_workflow(run: TeamworkRun) -> None:
    if run.schema_version != "core.adversary.teamwork.v4":
        return
    if run.native_gate_check is None:
        raise ValueError("NATIVE_GATE_CHECK_REQUIRED")
    if run.max_actions < 4:
        raise ValueError("FINISH_ALLOWANCE_REQUIRED: reserve DDC storage,Scar Chronicler,native final diagnostics and final readback")


def _validate_panel_workflow(run: TeamworkRun) -> None:
    if run.panel_plan is None:
        raise ValueError("PANEL_PLAN_REQUIRED")
    if not run.learn_after_run:
        raise ValueError("PANEL_LEARNING_REQUIRED")
    _validate_v2_acceptance(run)
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        _validate_current_allowance(run)
    _validate_v4_workflow(run)


def _reject_legacy_native_gate(run: TeamworkRun) -> None:
    if run.schema_version != "core.adversary.teamwork.v4" and run.native_gate_check is not None:
        raise ValueError("LEGACY_NATIVE_GATE_BACKDATE_FORBIDDEN")


def _required_role_ids(run: TeamworkRun) -> list[str]:
    return [step.role_id for step in run.panel_plan.steps]


def _observed_role_ids(run: TeamworkRun) -> set:
    found = set()
    for item in run.observations:
        if not item.blocked:
            found.add(item.metadata.get("role_id"))
    return found


def _schedule_skips(run: TeamworkRun, trace: tuple) -> list:
    if run.panel_plan.schedule is None or len(trace) <= 8:
        return []
    return trace[8].get("schedule_skips", [])


def _skipped_role_ids(skips: list, observed: set) -> set:
    return {item["role_id"] for item in skips} - observed


def _missing_role_ids(required: list[str], observed: set, skipped: set) -> list[str]:
    missing = []
    for role in required:
        if role not in observed and role not in skipped:
            missing.append(role)
    return missing


def _roles_in(required: list[str], chosen: set) -> list[str]:
    return [role for role in required if role in chosen]


_APPROVAL_WORDS = ("none", "no failure found", "clean", "ok", "lgtm")


def _reviewer_finding_set(run: TeamworkRun, required: list[str]) -> set:
    reviewer_ids = set(required[6:20])
    found = set()
    for obs in run.observations:
        if obs.metadata.get("role_id") not in reviewer_ids or obs.blocked or obs.metadata.get("approval"):
            continue
        for finding in obs.findings:
            if finding and str(finding).strip().lower() not in _APPROVAL_WORDS:
                found.add(finding.strip())
    return found


def _host_observations(run: TeamworkRun) -> list:
    rows = []
    for obs in run.observations:
        kind = obs.metadata.get("execution_kind")
        if kind == "host" or obs.metadata.get("role_id") == "host_acceptance":
            rows.append(obs)
    return rows


def _host_finding_set(host_obs: list) -> set:
    found = set()
    for obs in host_obs:
        for finding in obs.findings:
            if finding:
                found.add(finding.strip())
    return found


def _host_check_failed(host_obs: list) -> bool:
    for obs in host_obs:
        if obs.check and obs.check.exit_status != 0:
            return True
    return False


def _observation_faults(rev_findings: set, host_obs: list, host_findings: set) -> tuple[int, int]:
    if not host_obs:
        return 0, 0
    if _host_check_failed(host_obs) or host_findings:
        if host_findings:
            return len(rev_findings & host_findings), len(rev_findings - host_findings)
        return len(rev_findings), 0
    return 0, len(rev_findings)


def _trace_fault_pair(trace: tuple) -> tuple[int, int]:
    if len(trace) <= 8:
        return 0, 0
    return int(trace[8].get("failures_reproduced", 0)), int(trace[8].get("false_alarms", 0))


def _coverage_base(run: TeamworkRun, required, observed, missing, failures, alarms, skipped) -> dict:
    return {"status": "OBSERVED" if not missing else "INCOMPLETE",
            "required": required, "observed": _roles_in(required, observed),
            "missing": missing, "complete": not missing,
            "plan_sha256": run.panel_plan.plan_sha256,
            "declared": len(required), "scheduled": len(required) - len(skipped),
            "contributed": len(_roles_in(required, observed)),
            "failures_reproduced": failures, "false_alarms": alarms}


def _attach_schedule_coverage(coverage: dict, run: TeamworkRun, required, skipped, skips) -> None:
    schedule = run.panel_plan.schedule
    if schedule is None:
        return
    coverage.update(schedule=schedule.name,
        skipped_by_schedule=_roles_in(required, skipped),
        schedule_skips=[dict(item) for item in skips])


def _measured_panel_coverage(run: TeamworkRun) -> dict[str, Any]:
    trace = _trace(run)  # Saved observations must pass the same action/PFP replay as live intake.
    required = _required_role_ids(run)
    observed = _observed_role_ids(run)
    skips = _schedule_skips(run, trace)
    skipped = _skipped_role_ids(skips, observed)
    missing = _missing_role_ids(required, observed, skipped)
    trace_failures, trace_alarms = _trace_fault_pair(trace)
    host_obs = _host_observations(run)
    host_findings = _host_finding_set(host_obs)
    obs_failures, obs_alarms = _observation_faults(
        _reviewer_finding_set(run, required), host_obs, host_findings)
    coverage = _coverage_base(run, required, observed, missing,
        max(trace_failures, obs_failures), max(trace_alarms, obs_alarms), skipped)
    _attach_schedule_coverage(coverage, run, required, skipped, skips)
    if run.panel_plan.preset:
        coverage["preset"] = run.panel_plan.preset
    return coverage


def _task_identity(run: TeamworkRun) -> str:
    if run.intelligence:
        return run.intelligence.initial_task_id
    return run.run_id


def _open_findings(stage: str, findings, clarification) -> list:
    if stage != "completed" or clarification is not None:
        return list(findings)
    return []


def _gap_sources(run: TeamworkRun) -> list:
    sources = []
    if run.intelligence:
        sources.append(run.intelligence)
    for item in run.observations:
        if item.intelligence:
            sources.append(item.intelligence)
    return sources


def _coverage_gap_names(run: TeamworkRun) -> list:
    gaps = set()
    for source in _gap_sources(run):
        for gap in source.coverage_gaps:
            gaps.add(gap)
    return sorted(gaps)


def _finish_pending(trace: tuple, stage: str) -> bool:
    if stage in ("ddc_store", "learn", "ddc_complete"):
        return True
    return stage in ("digest", "native_gates") and bool(trace[8]["stopped_status"])


def _attach_current_continuation(record: dict, run: TeamworkRun, trace: tuple, stage: str) -> None:
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        record["evaluations_used"] = trace[8]["evaluations_used"]
        record["evaluation_limit"] = run.max_evaluations
        record["finish_pending"] = _finish_pending(trace, stage)
    if run.schema_version == "core.adversary.teamwork.v4":
        record["native_gates"] = run.native_gate_coverage
    if run.feedback_policy == "semantic_digestion_v2":
        record["semantic_review_pending"] = trace[8]["semantic_review_pending"]


def _continuation_record(run, trace, stage, spent, limits, reason, pending, findings) -> dict:
    clarification = None
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        clarification = trace[8].get("clarification_context")
    record = {
        "reason": reason,
        "pending_stage": pending if run.work_status in ("blocked", "partial") else None,
        "initial_task_id": _task_identity(run),
        "executor": run.executor,
        "actions_used": len(run.observations),
        "action_allowance": limits[1],
        "remaining_actions": max(0, limits[1] - len(run.observations)),
        "repairs_used": spent,
        "repair_allowance": limits[0],
        "remaining_repairs": max(0, limits[0] - spent),
        "open_findings": _open_findings(stage, findings, clarification),
        "coverage_gaps": _coverage_gap_names(run),
        "panel": run.panel_coverage,
    }
    if clarification is not None:
        record["clarification_context"] = clarification
    _attach_current_continuation(record, run, trace, stage)
    return record


def _course(run: TeamworkRun) -> tuple[str, TeamworkObservation | None]:
    stage, producer, *_rest = _trace(run)
    return stage, producer


def intelligence_sources(run: TeamworkRun) -> tuple[IntelligenceRead, ...]:
    """Original source followed by actual observed intake/digestion descendants."""
    return tuple(source for source in (
        run.intelligence, *(item.intelligence for item in run.observations)
    ) if source is not None)


def _optional_route(result: TeamworkObservation) -> OptionalToolRoute | None:
    if not result.blocked or result.metadata.get("failure_code") != "OPTIONAL_TOOL_UNAVAILABLE":
        return None
    checked = result.metadata.get("pfp")
    if checked and (not checked.get("schema_valid") or checked.get("failure_class") != "NONE"):
        return None
    route = result.metadata.get("optional_route")
    return OptionalToolRoute.model_validate(route) if route else None


def _f0_list(value) -> list:
    return list(value or ())


def _f0_two_args(args):
    if isinstance(args[0], (list, tuple)):
        findings_raw, host_verdict = args
        return "", "", _f0_list(findings_raw), host_verdict
    candidate_id, host_verdict = args
    return candidate_id, "", [], host_verdict


def _f0_from_args(args):
    candidate_id, candidate_digest, findings, host_verdict = "", "", [], set()
    if len(args) == 4:
        candidate_id, candidate_digest, findings_raw, host_verdict = args
        findings = _f0_list(findings_raw)
    elif len(args) == 2:
        candidate_id, candidate_digest, findings, host_verdict = _f0_two_args(args)
    elif len(args) == 3:
        candidate_id, candidate_digest, findings_raw = args
        findings = _f0_list(findings_raw)
    return candidate_id, candidate_digest, findings, host_verdict


def _f0_kwargs_findings(kwargs, findings):
    if "findings" in kwargs:
        return _f0_list(kwargs["findings"])
    if "reviewer_findings" in kwargs:
        return _f0_list(kwargs["reviewer_findings"])
    return findings


def _f0_kwargs_verdict(kwargs, host_verdict):
    if "host_verdict" in kwargs:
        return kwargs["host_verdict"]
    if "host_planted_faults" in kwargs:
        return kwargs["host_planted_faults"]
    return host_verdict


def _f0_from_kwargs(kwargs, candidate_id, candidate_digest, findings, host_verdict):
    if "candidate_id" in kwargs:
        candidate_id = kwargs["candidate_id"]
    if "candidate_digest" in kwargs:
        candidate_digest = kwargs["candidate_digest"]
    return (candidate_id, candidate_digest, _f0_kwargs_findings(kwargs, findings),
            _f0_kwargs_verdict(kwargs, host_verdict))


def _f0_require_active(kwargs, candidate_digest) -> None:
    active = kwargs.get("active_candidate_digest") or kwargs.get("active_digest")
    if active and candidate_digest and candidate_digest != active:
        raise ValueError(f"STALE_CANDIDATE_DIGEST: claim references {candidate_digest}, active is {active}")


def _f0_dict_faults(host_verdict) -> set:
    planted = host_verdict.get("planted_faults")
    if planted:
        return set(planted)
    faults = host_verdict.get("faults")
    if faults:
        return set(faults)
    return set(host_verdict.get("planted") or ())


def _f0_host_faults(host_verdict) -> set:
    if isinstance(host_verdict, (set, frozenset)):
        return set(host_verdict)
    if isinstance(host_verdict, (list, tuple)):
        return set(host_verdict)
    if isinstance(host_verdict, dict):
        return _f0_dict_faults(host_verdict)
    if host_verdict is None:
        return set()
    return {str(host_verdict)}


def _f0_text(item, key: str) -> str:
    return str(item.get(key) or "")


def _f0_approval(item) -> bool:
    if item.get("approval") is True:
        return True
    return _f0_text(item, "text").strip().lower() in _APPROVAL_WORDS


def _f0_reproduced(item, host_planted_faults) -> bool:
    claim_id = _f0_text(item, "claim_id")
    finding_text = _f0_text(item, "text")
    if claim_id and claim_id in host_planted_faults:
        return True
    return bool(finding_text and finding_text in host_planted_faults)


def _f0_row(item, status: str) -> dict[str, Any]:
    return {"seat_id": _f0_text(item, "seat_id"), "claim_id": _f0_text(item, "claim_id"),
            "text": _f0_text(item, "text"), "status": status}


def _f0_split_findings(findings, host_planted_faults):
    reproduced, alarms = [], []
    for item in findings:
        if _f0_approval(item):
            continue
        if _f0_reproduced(item, host_planted_faults):
            reproduced.append(_f0_row(item, "REPRODUCED_BY_HOST"))
        else:
            alarms.append(_f0_row(item, "FALSE_ALARM"))
    return reproduced, alarms


def _f0_flagged(reproduced) -> set:
    flagged = set()
    for item in reproduced:
        if item["claim_id"]:
            flagged.add(item["claim_id"])
        if item["text"]:
            flagged.add(item["text"])
    return flagged


def _f0_result(candidate_id, candidate_digest, reproduced, alarms, host_planted_faults) -> dict[str, Any]:
    caught = host_planted_faults.issubset(_f0_flagged(reproduced))
    if not host_planted_faults:
        caught = True
    return {
        "candidate_id": candidate_id,
        "candidate_digest": candidate_digest,
        "failures_reproduced": len(reproduced),
        "false_alarms": len(alarms),
        "reproduced_details": reproduced,
        "false_alarm_details": alarms,
        "host_clearance": caught and len(reproduced) >= len(host_planted_faults),
        "approval_weight": 0,
    }


def evaluate_f0_submission(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Authoritative F0 Failure-First Currency evaluator.

    Invariants:
    1. Approvals ("no failure found", "clean", or empty findings) carry exactly 0 acceptance weight.
    2. A claimed failure counts as a reproduced failure IF AND ONLY IF confirmed by the host checker.
    3. Unreproduced claims are retained with false-alarm credit.
    4. Clearance is granted ONLY if all planted/host defects were reproduced and no unresolved defects remain.
    """
    candidate_id, candidate_digest, findings, host_verdict = _f0_from_kwargs(
        kwargs, *_f0_from_args(args))
    _f0_require_active(kwargs, candidate_digest)
    host_planted_faults = _f0_host_faults(host_verdict)
    reproduced, alarms = _f0_split_findings(findings, host_planted_faults)
    return _f0_result(candidate_id, candidate_digest, reproduced, alarms, host_planted_faults)


def _trace(run: TeamworkRun) -> tuple:
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        return _trace_v3(run)
    if run.schema_version == "core.adversary.teamwork.v2":
        return _trace_panel(run)[:7]
    return _trace_legacy(run)


def _indexed_points(run: TeamworkRun) -> dict:
    return {point.after_observations: point for point in run.continuations}


def _continuation_past_end(run: TeamworkRun, points: dict) -> bool:
    for index in points:
        if index > len(run.observations):
            return True
    return False


def _require_continuation_positions(run: TeamworkRun, points: dict) -> None:
    if len(points) != len(run.continuations) or _continuation_past_end(run, points):
        raise ValueError("CONTINUATION_POSITION_INVALID")


def _intake_frontier(run: TeamworkRun) -> tuple:
    if run.intelligence:
        return tuple(sorted(set(run.intelligence.findings)))
    return ()


class _Legacy:
    def __init__(self, run: TeamworkRun) -> None:
        self.repair_limit = run.max_repairs
        self.action_limit = run.max_actions
        self.stage = "build"
        self.repairs = 0
        self.learning_applied = False
        self.producer = None
        self.reason = ""
        self.resume_stage = None
        self.frontier = _intake_frontier(run)
        self.artifacts: dict[str, str] = {}
        self.repair_frontier = ()
        self.repair_before: dict = {}
        self.points = _indexed_points(run)


def _legacy_cap(state: _Legacy, index: int) -> None:
    if state.stage in _INSTRUCTIONS and index >= state.action_limit:
        state.stage, state.resume_stage, state.reason = "partial", state.stage, "ACTION_ALLOWANCE_EXHAUSTED"
    if state.stage == "repair" and state.repairs >= state.repair_limit:
        state.stage, state.resume_stage, state.reason = "partial", "repair", "REPAIR_ALLOWANCE_EXHAUSTED"


def _legacy_resume(state: _Legacy, index: int) -> None:
    if index not in state.points:
        return
    point = state.points[index]
    if state.stage not in ("blocked", "partial") or state.resume_stage is None:
        raise ValueError("CONTINUATION_POSITION_INVALID: only stopped work can resume")
    state.repair_limit += point.additional_repairs
    state.action_limit += point.additional_actions
    state.stage, state.reason = state.resume_stage, ""


def _legacy_block(state: _Legacy, result: TeamworkObservation, attempted: str) -> None:
    stripped = []
    for finding in result.findings:
        stripped.append(finding.strip())
    state.frontier = tuple(sorted({*state.frontier, *stripped}))
    state.stage, state.resume_stage = "blocked", attempted
    state.reason = str(result.metadata.get("failure_code", "REQUIRED_ACTION_UNAVAILABLE"))


def _legacy_findings(state: _Legacy, result: TeamworkObservation) -> None:
    stripped = {finding.strip() for finding in result.findings}
    state.frontier = tuple(sorted(stripped))
    state.resume_stage = "repair"
    if state.repair_frontier == state.frontier and state.artifacts == state.repair_before:
        state.stage, state.reason = "partial", "NO_PROGRESS"
        return
    if state.repairs >= state.repair_limit:
        state.stage, state.reason = "partial", "REPAIR_ALLOWANCE_EXHAUSTED"
        return
    state.stage = "repair"


def _legacy_review_stage(run: TeamworkRun) -> str:
    if run.intelligence:
        return "recheck"
    if run.learn_after_run:
        return "learn"
    return "completed"


def _legacy_digest_stage(run: TeamworkRun, state: _Legacy) -> str:
    if run.learn_after_run and not state.learning_applied:
        return "learn"
    return "completed"


def _legacy_learn_changed(result: TeamworkObservation, previous: dict) -> bool:
    if result.metadata.get("changed_paths"):
        return True
    return bool(result.artifacts) and result.artifacts != previous


def _legacy_clear_stage(run: TeamworkRun, state: _Legacy, result: TeamworkObservation, previous: dict) -> None:
    if state.stage == "review":
        state.stage = _legacy_review_stage(run)
        return
    if state.stage == "recheck":
        state.stage, state.frontier = "digest", ()
        return
    if state.stage == "digest":
        state.stage, state.frontier = _legacy_digest_stage(run, state), ()
        return
    changed = _legacy_learn_changed(result, previous)
    state.learning_applied = bool(run.intelligence and changed)
    state.stage, state.frontier = ("recheck" if state.learning_applied else "completed"), ()


def _legacy_checked(run: TeamworkRun, state: _Legacy, result: TeamworkObservation, previous: dict) -> None:
    if result.findings:
        _legacy_findings(state, result)
        return
    _legacy_clear_stage(run, state, result, previous)


def _legacy_apply(run: TeamworkRun, state: _Legacy, index: int) -> None:
    result = run.observations[index]
    attempted = state.stage
    previous = dict(state.artifacts)
    if state.stage == "repair":
        state.repairs += 1  # A failed/unavailable attempt also spends allowance.
        state.repair_frontier, state.repair_before = state.frontier, dict(state.artifacts)
    state.artifacts.update(result.artifacts)
    if result.blocked:
        _legacy_block(state, result, attempted)
        return
    if state.stage in ("review", "recheck", "digest", "learn"):
        _legacy_checked(run, state, result, previous)
        return
    state.learning_applied = False  # A new build/repair needs its own learning review.
    state.producer = result
    state.stage = "review"


def _legacy_step(run: TeamworkRun, state: _Legacy, index: int) -> bool:
    _legacy_cap(state, index)
    _legacy_resume(state, index)
    _legacy_cap(state, index)
    if index == len(run.observations):
        return True
    if state.stage not in _INSTRUCTIONS:
        raise ValueError("TERMINAL_RUN: observations after completion")
    _legacy_apply(run, state, index)
    return False


def _legacy_intake_block(run: TeamworkRun, state: _Legacy):
    if not run.intelligence or not run.intelligence.coverage_gaps:
        return None
    return ("blocked", None, 0, (state.repair_limit, state.action_limit), "INTAKE_COVERAGE_OPEN", "build",
            tuple(run.intelligence.findings))


def _trace_legacy(run: TeamworkRun) -> tuple:
    """Replay sequential observations and explicit resumption points, never reset."""
    state = _Legacy(run)
    blocked = _legacy_intake_block(run, state)
    if blocked is not None:
        return blocked
    _require_continuation_positions(run, state.points)
    for index in range(len(run.observations) + 1):
        if _legacy_step(run, state, index):
            break
    return (state.stage, state.producer, state.repairs, (state.repair_limit, state.action_limit),
            state.reason, state.resume_stage, state.frontier)


def _observation_prefix(run: TeamworkRun, index: int) -> TeamworkRun:
    kept = []
    for point in run.continuations:
        if point.after_observations <= index:
            kept.append(point)
    return run.model_copy(update={"observations": run.observations[:index], "continuations": tuple(kept)})


class _Panel:
    def __init__(self, run: TeamworkRun, plan: PanelPlan) -> None:
        self.plan = plan
        self.repair_limit = run.max_repairs
        self.action_limit = run.max_actions
        self.mode = "plan"
        self.cursor = 0
        self.repairs = 0
        self.producer = None
        self.reason = ""
        self.stopped = False
        self.resume_stage = None
        self.frontier = _intake_frontier(run)
        self.initial_findings = self.frontier
        self.artifacts: dict[str, str] = {}
        self.repair_frontier = ()
        self.repair_before: dict = {}
        self.repair_candidate = ""
        self.learning_applied = False
        self.points = _indexed_points(run)
        self.stage = ""
        self.descriptor = ("", "", "host")

    def pending(self):
        if self.mode in ("plan", "review_repair"):
            step = self.plan.steps[self.cursor]
            return step.kind, (step.role_id, step.phase, step.communication)
        if self.mode == "repair":
            return "repair", ("primal_dual", "repair", "pfp")
        if self.mode in ("recheck", "digest"):
            role = "host_digestion"
            if self.mode == "recheck":
                role = "host_acceptance"
            return self.mode, (role, self.mode, "host")
        return self.mode, ("", "", "host")


def _panel_cap(state: _Panel, index: int) -> None:
    if state.stopped or state.stage not in _INSTRUCTIONS:
        return
    if index >= state.action_limit:
        state.stage, state.reason, state.stopped = "partial", "ACTION_ALLOWANCE_EXHAUSTED", True
    elif state.stage == "repair" and state.repairs >= state.repair_limit:
        state.stage, state.reason, state.stopped = "partial", "REPAIR_ALLOWANCE_EXHAUSTED", True
    if state.stopped:
        state.resume_stage = state.pending()[0]


def _panel_resume_reason(state: _Panel, index: int) -> str:
    if index >= state.action_limit:
        return "ACTION_ALLOWANCE_EXHAUSTED"
    return "REPAIR_ALLOWANCE_EXHAUSTED"


def _panel_resume(state: _Panel, index: int) -> None:
    if index not in state.points:
        return
    point = state.points[index]
    if not state.stopped or state.resume_stage is None:
        raise ValueError("CONTINUATION_POSITION_INVALID: only stopped work can resume")
    state.repair_limit += point.additional_repairs
    state.action_limit += point.additional_actions
    state.stage, state.descriptor = state.pending()
    state.reason, state.stopped = "", False
    repair_capped = state.stage == "repair" and state.repairs >= state.repair_limit
    if index >= state.action_limit or repair_capped:
        state.stage, state.stopped = "partial", True
        state.reason = _panel_resume_reason(state, index)


def _panel_bind(run: TeamworkRun, state: _Panel, index: int):
    prefix = _observation_prefix(run, index)
    action = _make_action(prefix, state.stage, state.producer, state.frontier, state.descriptor)
    result = run.observations[index]
    _validate_panel_observation(action, result)
    _validate_action_result(run, action, result)
    return result, dict(state.artifacts)


def _panel_block(state: _Panel, result: TeamworkObservation) -> None:
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    state.resume_stage = state.stage
    state.stage, state.stopped = "blocked", True
    state.reason = str(result.metadata.get("failure_code", "REQUIRED_ACTION_UNAVAILABLE"))


def _panel_produced(state: _Panel, result: TeamworkObservation) -> None:
    state.producer = result
    state.learning_applied = False
    # Intake/source findings are build requirements, not evidence that
    # the resulting artifact still fails. Every reviewer receives those
    # retained contributions and reports any unresolved defect afresh.
    state.frontier = ()
    state.mode, state.cursor = ("review_repair", 6)
    if state.stage == "build":
        state.mode, state.cursor = ("plan", 6)


def _panel_reviewed(state: _Panel, result: TeamworkObservation) -> bool:
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    state.cursor += 1
    return state.cursor < 21


def _panel_clear_recheck(run: TeamworkRun, state: _Panel) -> None:
    state.cursor = 21
    if run.intelligence:
        state.mode = "digest"
        return
    state.mode = "plan"
    if state.learning_applied:
        state.mode = "completed"


def _panel_clear_learn(run: TeamworkRun, state: _Panel, result: TeamworkObservation, previous: dict) -> None:
    changed = _legacy_learn_changed(result, previous)
    state.learning_applied = bool((run.intelligence or run.acceptance_check) and changed)
    state.mode = "completed"
    if state.learning_applied:
        state.mode = "recheck"


def _panel_clear_checked(run: TeamworkRun, state: _Panel, result: TeamworkObservation, previous: dict) -> None:
    if state.stage == "recheck":
        _panel_clear_recheck(run, state)
        return
    if state.stage == "digest":
        state.mode, state.cursor = ("plan", 21)
        if state.learning_applied:
            state.mode, state.cursor = ("completed", 21)
        return
    _panel_clear_learn(run, state, result, previous)


def _panel_checked(run: TeamworkRun, state: _Panel, result: TeamworkObservation, previous: dict) -> bool:
    state.frontier = tuple(sorted(set(result.findings)))
    if state.frontier:
        return False
    _panel_clear_checked(run, state, result, previous)
    return True


def _panel_progress(run: TeamworkRun, state: _Panel, result: TeamworkObservation, previous: dict) -> bool:
    if state.stage in ("build", "repair"):
        _panel_produced(state, result)
        return True
    if state.stage == "review":
        return _panel_reviewed(state, result)
    if state.stage in ("recheck", "digest", "learn"):
        return _panel_checked(run, state, result, previous)
    return False


def _panel_same_repair(state: _Panel) -> bool:
    if state.repair_frontier != state.frontier or state.artifacts != state.repair_before:
        return False
    current = ""
    if state.producer:
        current = state.producer.content
    return current == state.repair_candidate


def _panel_frontier_gate(run: TeamworkRun, state: _Panel) -> None:
    if not state.frontier:
        state.mode, state.cursor = ("plan", 21)
        if run.intelligence or run.acceptance_check:
            state.mode, state.cursor = ("recheck", 21)
        return
    state.mode = "repair"
    state.resume_stage = "repair"
    if _panel_same_repair(state):
        state.stage, state.reason, state.stopped = "partial", "NO_PROGRESS", True
        return
    if state.repairs >= state.repair_limit:
        state.stage, state.reason, state.stopped = "partial", "REPAIR_ALLOWANCE_EXHAUSTED", True


def _panel_apply(run: TeamworkRun, state: _Panel, index: int) -> None:
    result, previous = _panel_bind(run, state, index)
    if state.stage == "repair":
        state.repairs += 1
        state.repair_frontier, state.repair_before = state.frontier, dict(state.artifacts)
        state.repair_candidate = ""
        if state.producer:
            state.repair_candidate = state.producer.content
    state.artifacts.update(result.artifacts)
    if result.blocked:
        _panel_block(state, result)
        return
    if _panel_progress(run, state, result, previous):
        return
    _panel_frontier_gate(run, state)


def _panel_step(run: TeamworkRun, state: _Panel, index: int) -> bool:
    if not state.stopped:
        state.stage, state.descriptor = state.pending()
    _panel_cap(state, index)
    _panel_resume(state, index)
    if index == len(run.observations):
        return True
    if state.stopped or state.stage not in _INSTRUCTIONS:
        raise ValueError("TERMINAL_RUN: observations after stopped or completed work")
    _panel_apply(run, state, index)
    return False


def _panel_result(state: _Panel) -> tuple:
    return (state.stage, state.producer, state.repairs, (state.repair_limit, state.action_limit),
            state.reason, state.resume_stage, state.frontier, state.descriptor)


def _panel_intake_block(run: TeamworkRun, state: _Panel):
    if not run.intelligence or not run.intelligence.coverage_gaps:
        return None
    return ("blocked", None, 0, (state.repair_limit, state.action_limit), "INTAKE_COVERAGE_OPEN",
            "review", state.initial_findings, ("syntax_prefilter", "intake", "deterministic"))


def _trace_panel(run: TeamworkRun) -> tuple:
    """Replay the governed plan, every raw role reply, and additive resumptions."""
    plan = run.panel_plan
    if plan is None:
        raise ValueError("PANEL_PLAN_REQUIRED")
    plan.validate_totality()
    state = _Panel(run, plan)
    _require_continuation_positions(run, state.points)
    blocked = _panel_intake_block(run, state)
    if blocked is not None:
        return blocked
    state.stage, state.descriptor = state.pending()
    for index in range(len(run.observations) + 1):
        if _panel_step(run, state, index):
            break
    return _panel_result(state)


def _query_shape(run, producer) -> bool:
    if not run.brief or run.brief.clarification_policy != "strict-query-v1":
        return False
    if producer is None or len(producer.artifacts) != 1:
        return False
    return True


def _artifact_digest_matches(producer, raw: bytes) -> bool:
    digest = hashlib.sha256(raw).hexdigest()
    for value in producer.artifacts.values():
        if digest == value.removeprefix("sha256:"):
            return True
    return False


def _decode_query_candidate(run, producer, premises, check_clarification):
    if type(premises) is not dict or set(premises) != {"required_fields", "supplied_fields"}:
        return None
    raw = producer.content.encode("utf-8")
    if len(raw) > 65_536 or not _artifact_digest_matches(producer, raw):
        return None
    candidate = decode_native_json(raw)
    checked = check_clarification(candidate, seed=run.objective,
        required_fields=tuple(premises["required_fields"]), supplied_fields=premises["supplied_fields"])
    if checked.is_err:
        return None
    return candidate


def _query_candidate(run, producer):
    """A strict query can request an original check, never admit itself."""
    if not _query_shape(run, producer):
        return None
    from pfp.use_cases.clarification import check_clarification

    try:
        return _decode_query_candidate(run, producer, run.brief.task_premises, check_clarification)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return None


_CAPTURE_KEYS = {"schema_version", "stdout_hex", "stderr_hex", "exit_code", "command",
                 "authority_effect", "authenticated"}


def _query_host_check(action, result, candidate) -> bool:
    check = result.check
    if candidate is None or result.blocked or result.metadata.get("execution_kind") != "host":
        return False
    if check is None or check.exit_status != 0 or check.initial_task_id != action.initial_task_id:
        return False
    return True


def _query_check_binding(action, result, producer) -> bool:
    check = result.check
    if check.source_id != action.check_source_id or check.checker_id != action.checker_id:
        return False
    if check.command != action.check_command or check.artifacts != action.artifacts:
        return False
    return producer.artifacts == action.artifacts and bool(action.check_source_paths)


def _query_capture_meta(action, capture) -> bool:
    if type(capture) is not dict or set(capture) != _CAPTURE_KEYS:
        return False
    if capture.get("schema_version") != "adversary.unsigned-checker-capture.v1":
        return False
    if type(capture.get("exit_code")) is not int or capture["exit_code"] != 0:
        return False
    if capture.get("command") != list(action.check_command):
        return False
    return capture.get("authority_effect") == "None" and capture.get("authenticated") is False


def _query_capture_shape(action, result, producer, candidate) -> bool:
    if not _query_host_check(action, result, candidate):
        return False
    if not _query_check_binding(action, result, producer):
        return False
    return _query_capture_meta(action, result.metadata.get("checker_capture"))


def _capture_byte(capture, key: str):
    if type(capture[key]) is not str or len(capture[key]) > 131_072:
        return None
    value = bytes.fromhex(capture[key])
    if value.hex() != capture[key]:
        return None
    return value


def _capture_bytes(capture):
    raw = []
    for key in ("stdout_hex", "stderr_hex"):
        value = _capture_byte(capture, key)
        if value is None:
            return None
        raw.append(value)
    return raw


def _capture_streams_match(result, raw) -> bool:
    for key, value in zip(("stdout", "stderr"), raw, strict=True):
        if key in result.metadata and result.metadata[key] != value.decode("utf-8", errors="replace"):
            return False
    return True


def _query_output_head(output) -> bool:
    if type(output) is not dict or output.get("accepted") is not True:
        return False
    if output.get("outcome") != "QUERY_USER_MORE_INFO":
        return False
    return output.get("mathematical_acceptance") == "NOT_SOLVED"


def _query_output_binding(run, action, producer, candidate, output) -> bool:
    if output.get("checker_id") != action.checker_id:
        return False
    candidate_sha = hashlib.sha256(producer.content.encode("utf-8")).hexdigest()
    if output.get("candidate_sha256") != candidate_sha:
        return False
    seed = hashlib.sha256(action.objective.encode("utf-8")).hexdigest()
    if output.get("seed_sha256") != seed:
        return False
    from .prompt_family_replay import _program_digest
    if output.get("premises_sha256") != _program_digest(run.brief.task_premises):
        return False
    if output.get("missing_fields") != candidate["missing_fields"]:
        return False
    return output.get("questions") == candidate["questions"]


def _query_output_matches(run, action, result, producer, candidate, raw) -> bool:
    digest = hashlib.sha256(raw[0] + b"\n--- stderr ---\n" + raw[1]).hexdigest()
    if digest != result.check.output_sha256:
        return False
    if not _capture_streams_match(result, raw):
        return False
    output = decode_native_json(raw[0])
    if not _query_output_head(output):
        return False
    return _query_output_binding(run, action, producer, candidate, output)


def _query_disposition_record(action, result, producer, candidate, raw) -> dict:
    check = result.check
    candidate_sha = hashlib.sha256(producer.content.encode("utf-8")).hexdigest()
    return {"policy": "strict-query-v1", "outcome": "QUERY_USER_MORE_INFO",
        "mathematical_acceptance": "NOT_SOLVED", "candidate_sha256": candidate_sha,
        "checker_id": check.checker_id, "check_source_id": check.source_id,
        "checker_output_sha256": check.output_sha256, "checker_stdout_sha256": hashlib.sha256(raw[0]).hexdigest(),
        "missing_fields": candidate["missing_fields"], "questions": candidate["questions"],
        "findings_disposition": "ADVISORY_UNRESOLVED", "authority_effect": "None"}


def _checked_query_body(run, action, result, producer, candidate):
    raw = _capture_bytes(result.metadata.get("checker_capture"))
    if raw is None:
        return None
    if not _query_output_matches(run, action, result, producer, candidate, raw):
        return None
    return _query_disposition_record(action, result, producer, candidate, raw)


def _checked_query_disposition(run, action, result, producer):
    """Recognize an exact bound original-check capture, not a role's query claim."""
    candidate = _query_candidate(run, producer)
    if not _query_capture_shape(action, result, producer, candidate):
        return None
    try:
        return _checked_query_body(run, action, result, producer, candidate)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return None


def _v3_final_diagnostics(run: TeamworkRun) -> str:
    if run.schema_version == "core.adversary.teamwork.v4":
        return "native_finish"
    return "finish_complete"


def _v3_semantic_finish(run: TeamworkRun, final_diagnostics: str) -> str:
    if run.feedback_policy:
        return "finish_digest"
    return final_diagnostics


def _pending_plan(state):
    step = state.plan.steps[state.cursor]
    return step.kind, (step.role_id, step.phase, step.communication)


def _pending_repair(state):
    return "repair", ("primal_dual", "repair", "pfp")


def _pending_recheck(state):
    return "recheck", ("host_acceptance", "recheck", "host")


def _pending_digest(state):
    return "digest", ("host_digestion", "digest", "host")


def _pending_learning_review(state):
    return "review", ("defect_hunter", "learning_review", "pfp")


def _pending_store(state):
    return "ddc_store", ("host_ddc_store", "ddc_store", "host")


def _pending_learn(state):
    phase = "learning"
    if state.mode == "learning_correction":
        phase = "learning_correction"
    return "learn", ("scar_chronicler", phase, "pfp")


def _pending_complete(state):
    return "ddc_complete", ("host_ddc_complete", "ddc_complete", "host")


_V3_PENDING = {
    "plan": _pending_plan,
    "review_repair": _pending_plan,
    "repair": _pending_repair,
    "recheck": _pending_recheck,
    "learn_recheck": _pending_recheck,
    "digest": _pending_digest,
    "learn_digest": _pending_digest,
    "finish_digest": _pending_digest,
    "learning_review": _pending_learning_review,
    "corrected_learning_review": _pending_learning_review,
    "finish_store": _pending_store,
    "learning_correction_store": _pending_store,
    "finish_learn": _pending_learn,
    "learning_correction": _pending_learn,
    "finish_complete": _pending_complete,
}


def _v3_pending(state):
    chosen = _V3_PENDING.get(state.mode)
    if chosen is not None:
        return chosen(state)
    if state.mode.startswith("native_"):
        return "native_gates", ("host_native_gates", state.mode, "host")
    if state.stopped_status:
        return state.stopped_status, ("", "", "host")
    return "completed", ("", "", "host")


def _v3_after_learning(state) -> str:
    if state.mode == "native_finish":
        return "finish_complete"
    if state.mode == "finish_digest":
        return state.final_diagnostics
    return state.semantic_finish


def _v3_stopped_mode(state, finish: bool) -> str:
    if not finish:
        return "terminal"
    if not state.learning_done:
        return "finish_store"
    return _v3_after_learning(state)


class _V3:
    def __init__(self, run: TeamworkRun, plan: PanelPlan) -> None:
        self.plan = plan
        self.repair_limit = run.max_repairs
        self.action_limit = run.max_actions
        self.mode = "plan"
        self.cursor = 0
        self.repairs = 0
        self.evaluations = 0
        self.producer = None
        self.program = None
        self.learning_done = False
        self.review_learning = run.feedback_policy == "semantic_digestion_v2"
        self.semantic_review_pending = self.review_learning
        self.correction_pending = False
        self.reuse_native = False
        self.query_disposition = None
        self.advisory_frontier: tuple[str, ...] = ()
        self.final_diagnostics = _v3_final_diagnostics(run)
        self.semantic_finish = _v3_semantic_finish(run, self.final_diagnostics)
        self.source_bound = run.intelligence is not None
        self.reason = ""
        self.stopped_status = ""
        self.resume_stage = None
        self.resume_mode = "plan"
        self.resume_cursor = 0
        self.retrying_learning_handoff = False
        self.handoff_markers: set[str] = set()
        self.frontier = _intake_frontier(run)
        self.artifacts: dict[str, str] = {}
        self.repair_frontier = ()
        self.repair_before: dict = {}
        self.repair_candidate = ""
        self.attempted_routes: set[str] = set()
        self.schedule = plan.schedule
        self.clean_streak = 0
        self.cohort_index = 0
        self.cohort_finders: set[str] = set()
        self.prior_finders: frozenset[str] = frozenset()
        self.in_repair_cohort = False
        self.schedule_skips: list[dict[str, Any]] = []
        self.failures_reproduced = 0
        self.false_alarms = 0
        self.candidate_reviewer_claims: list[str] = []
        self.points = _indexed_points(run)
        self.stage = ""
        self.descriptor = ("", "", "host")

    def pending(self):
        return _v3_pending(self)

    def stop(self, code, status="partial", *, finish=True) -> None:
        if not self.stopped_status:
            self.resume_mode, self.resume_cursor = self.mode, self.cursor
            self.resume_stage = self.pending()[0]
            self.reason, self.stopped_status = code, status
        self.mode = _v3_stopped_mode(self, finish)

    def advance(self, position: int) -> int:
        """Move past seats the schedule skips here, recording each skip and its reason."""
        while self.schedule is not None and position < 21:
            role = self.plan.steps[position].role_id
            why = seat_decision(self.schedule, role, clean_streak=self.clean_streak,
                cohort_has_findings=bool(self.frontier), repair_cohort=self.in_repair_cohort,
                prior_finders=self.prior_finders)
            if why is None:
                break
            self.schedule_skips.append({"role_id": role, "reason": why, "cohort": self.cohort_index})
            position += 1
        return position


_V3_EVAL_MODES = ("plan", "review_repair", "repair", "recheck", "digest",
                  "native_intake", "native_pre", "native_post")
_V3_LEARN_MODES = ("learn_recheck", "learn_digest", "native_learn_pre", "native_learn_post",
                   "learning_review", "corrected_learning_review", "learning_correction_store",
                   "learning_correction")


def _v3_eval_finish_actions(state: _V3, run: TeamworkRun) -> int:
    finish_actions = 1
    if run.schema_version == "core.adversary.teamwork.v4":
        finish_actions = 2
    finish_actions += bool(run.feedback_policy)
    if not state.learning_done:
        finish_actions += 2
    return finish_actions


def _v3_allow_eval(state: _V3, run: TeamworkRun, index: int) -> None:
    finish_actions = _v3_eval_finish_actions(state, run)
    if index >= state.action_limit - finish_actions:
        state.stop("ACTION_ALLOWANCE_EXHAUSTED")
        return
    if state.stage == "repair" and state.repairs >= state.repair_limit:
        state.stop("REPAIR_ALLOWANCE_EXHAUSTED")
        return
    if state.stage == "recheck" and state.evaluations >= run.max_evaluations:
        state.stop("EVALUATION_ALLOWANCE_EXHAUSTED")


def _v3_learn_finish_actions(state: _V3, run: TeamworkRun) -> int:
    finish_actions = 1
    if run.schema_version == "core.adversary.teamwork.v4":
        finish_actions = 2
    if run.feedback_policy:
        finish_actions += 1
    if state.mode == "learning_correction_store":
        finish_actions += 1
    return finish_actions


def _v3_learn_action_stop(state: _V3, run: TeamworkRun) -> None:
    if run.feedback_policy or run.schema_version == "core.adversary.teamwork.v4":
        state.stop("ACTION_ALLOWANCE_EXHAUSTED")
        return
    state.stop("ACTION_ALLOWANCE_EXHAUSTED", finish=False)
    state.mode = "finish_complete"


def _v3_learn_eval_stop(state: _V3, run: TeamworkRun) -> None:
    if run.feedback_policy:
        state.stop("EVALUATION_ALLOWANCE_EXHAUSTED")
        return
    state.stop("EVALUATION_ALLOWANCE_EXHAUSTED", finish=False)
    state.mode = state.final_diagnostics


def _v3_allow_learn(state: _V3, run: TeamworkRun, index: int) -> None:
    finish_actions = _v3_learn_finish_actions(state, run)
    if index >= state.action_limit - finish_actions:
        _v3_learn_action_stop(state, run)
        return
    if state.stage == "recheck" and state.evaluations >= run.max_evaluations:
        _v3_learn_eval_stop(state, run)
        return
    if state.mode == "learning_correction_store" and state.repairs >= state.repair_limit:
        state.stop("REPAIR_ALLOWANCE_EXHAUSTED")


def _v3_allowance(state: _V3, run: TeamworkRun, index: int) -> None:
    if state.mode in _V3_EVAL_MODES:
        _v3_allow_eval(state, run, index)
        return
    if state.mode in _V3_LEARN_MODES:
        _v3_allow_learn(state, run, index)


def _v3_resume_learning(state: _V3) -> None:
    if state.mode in ("finish_learn", "learning_correction"):
        if state.mode == "learning_correction":
            state.mode = "learning_correction_store"
        else:
            state.mode = "finish_store"
        state.program = None
        return
    if state.review_learning and state.learning_done:
        return
    state.program = None
    state.learning_done = False


def _v3_resume_point(state: _V3, index: int) -> None:
    if index not in state.points:
        return
    point = state.points[index]
    if state.mode != "terminal" or not state.stopped_status or state.resume_stage is None:
        raise ValueError("CONTINUATION_POSITION_INVALID: finish stopped work before resuming")
    state.repair_limit += point.additional_repairs
    state.action_limit += point.additional_actions
    state.mode, state.cursor = state.resume_mode, state.resume_cursor
    state.retrying_learning_handoff = (
        state.mode in ("finish_learn", "learning_correction") and state.reason == "HOST_ARTIFACTS_REQUIRED")
    state.reason, state.stopped_status = "", ""
    _v3_resume_learning(state)


def _v3_context(state: _V3) -> dict:
    context = {"stopped_status": state.stopped_status, "evaluations_used": state.evaluations,
               "ddc_program": state.program, "semantic_review_pending": state.semantic_review_pending,
               "stopped_reason": state.reason}
    if state.query_disposition is not None:
        context["clarification_context"] = {
            **state.query_disposition, "advisory_findings": list(state.advisory_frontier)}
    return context


def _v3_bind(state: _V3, run: TeamworkRun, index: int):
    prefix = _observation_prefix(run, index)
    action = _make_action(prefix, state.stage, state.producer, state.frontier, state.descriptor,
        v3_context=_v3_context(state))
    result = run.observations[index]
    _validate_panel_observation(action, result)
    _validate_action_result(run, action, result)
    return action, result, dict(state.artifacts)


def _v3_spend(state: _V3) -> None:
    if state.stage == "recheck":
        state.evaluations += 1  # Failed and unavailable host evaluations are episodes too.
    if state.stage == "repair":
        state.repairs += 1
        state.repair_frontier, state.repair_before = state.frontier, dict(state.artifacts)
        state.repair_candidate = state.producer.content if state.producer else ""
    if state.mode == "learning_correction":
        state.repairs += 1  # Prose correction shares the original repair allowance.


def _v3_route(action: TeamworkAction, stage: str, result: TeamworkObservation):
    if action.communication != "pfp" or stage not in ("build", "review", "repair"):
        return None
    if action.phase == "learning_review":
        return None
    return _optional_route(result)


def _v3_take_route(state: _V3, action: TeamworkAction, result: TeamworkObservation) -> bool:
    route = _v3_route(action, state.stage, result)
    if not route:
        return False
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    route_key = route.model_dump_json()
    if route_key in state.attempted_routes:
        state.stop("NO_PROGRESS")
    else:
        state.attempted_routes.add(route_key)
    return True


def _v3_blocked_destination(state: _V3) -> str:
    if state.mode == "finish_digest":
        return state.final_diagnostics
    return "finish_complete"


def _v3_on_blocked(state: _V3, result: TeamworkObservation) -> None:
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    code = str(result.metadata.get("failure_code", "REQUIRED_ACTION_UNAVAILABLE"))
    if state.mode in ("finish_learn", "learning_correction"):
        state.handoff_markers.clear()
        if not state.stopped_status:
            state.stop(code, "blocked", finish=False)
        state.mode = state.semantic_finish
        return
    if state.mode in ("finish_store", "learning_correction_store", "finish_complete"):
        state.stop(code, "blocked", finish=False)
        return
    if state.mode in ("finish_digest", "native_finish"):
        destination = _v3_blocked_destination(state)
        state.stop(code, "blocked", finish=False)
        state.mode = destination
        return
    state.stop(code, "blocked")


def _v3_produced(state: _V3, result: TeamworkObservation) -> None:
    state.producer = result
    state.frontier = ()
    state.query_disposition, state.advisory_frontier = None, ()
    state.mode, state.cursor = ("review_repair", 6)
    if state.stage == "build":
        state.mode, state.cursor = ("plan", 6)
    # Narrow a repair cohort only when reviewers raised the findings it answers; a repair
    # after a failed host check or learning findings reruns every scheduled reviewer.
    state.in_repair_cohort = state.stage == "repair" and bool(state.cohort_finders)
    state.prior_finders = frozenset(state.cohort_finders) if state.in_repair_cohort else frozenset()
    state.cohort_finders, state.clean_streak = set(), 0
    state.cohort_index += 1
    state.cursor = state.advance(state.cursor)


def _v3_after_build(state: _V3, run: TeamworkRun, action, result, previous):
    _v3_produced(state, result)
    return None


def _v3_corrected_mode(state: _V3, run: TeamworkRun) -> str:
    if state.reuse_native:
        return "learn_recheck"
    if run.schema_version == "core.adversary.teamwork.v4":
        return "native_learn_pre"
    return "learn_recheck"


def _v3_learning_review(state: _V3, run: TeamworkRun, result: TeamworkObservation) -> None:
    if state.query_disposition is not None:
        # This opt-in disposition closes the checked question workflow,
        # not its external inputs or disputed learning claims.
        state.advisory_frontier = tuple(sorted({*state.advisory_frontier, *state.frontier, *result.findings}))
        state.frontier = state.advisory_frontier
        state.semantic_review_pending = bool(state.advisory_frontier)
        state.mode = "finish_complete"
        return
    # Only an actual review can discharge findings about learning.
    # Original-task acceptance cannot erase these advisory findings.
    state.frontier = tuple(sorted(set(result.findings)))
    state.semantic_review_pending = bool(state.frontier)
    if state.frontier:
        state.correction_pending = True
        state.mode = "learning_correction_store"
        if state.repairs >= state.repair_limit:
            state.stop("REPAIR_ALLOWANCE_EXHAUSTED")
        return
    if state.mode == "corrected_learning_review":
        state.semantic_review_pending = True  # Review the resulting digestion too.
        state.mode = _v3_corrected_mode(state, run)
        return
    state.mode = "finish_complete"


def _v3_check_claim_digest(state: _V3, result: TeamworkObservation) -> None:
    claimed_digest = result.metadata.get("candidate_digest")
    if claimed_digest is None:
        return
    active_digest = hashlib.sha256((state.producer.content if state.producer else "").encode("utf-8")).hexdigest()
    if claimed_digest != active_digest:
        raise ValueError(
            f"STALE_CANDIDATE_DIGEST: claim references {claimed_digest}, active is {active_digest}"
        )


def _cohort_clean_findings(result: TeamworkObservation) -> list[str]:
    if result.metadata.get("approval"):
        return []
    cleaned = []
    for finding in result.findings:
        text = finding.strip()
        if text.lower() not in _APPROVAL_WORDS:
            cleaned.append(text)
    return cleaned


def _v3_note_clean(state: _V3, result: TeamworkObservation, clean: list[str]) -> None:
    state.frontier = tuple(sorted({*state.frontier, *clean}))
    state.cursor += 1
    if not clean:
        state.clean_streak += 1
        return
    state.clean_streak = 0
    state.cohort_finders.add(str(result.metadata.get("role_id", "")))
    state.candidate_reviewer_claims.extend(clean)


def _v3_same_repair(state: _V3) -> bool:
    if state.repair_frontier != state.frontier or state.artifacts != state.repair_before:
        return False
    current = state.producer.content if state.producer else ""
    return current == state.repair_candidate


def _v3_cohort_done(state: _V3, run: TeamworkRun) -> None:
    if not state.frontier or _query_candidate(run, state.producer) is not None:
        state.mode = "recheck"
        if run.schema_version == "core.adversary.teamwork.v4":
            state.mode = "native_pre"
        return
    state.mode = "repair"
    if _v3_same_repair(state):
        state.stop("NO_PROGRESS")
        return
    if state.repairs >= state.repair_limit:
        state.stop("REPAIR_ALLOWANCE_EXHAUSTED")


def _v3_after_cohort_review(state: _V3, run: TeamworkRun, result: TeamworkObservation):
    _v3_check_claim_digest(state, result)
    _v3_note_clean(state, result, _cohort_clean_findings(result))
    if run.schema_version == "core.adversary.teamwork.v4" and state.cursor == 1:
        state.mode = "native_intake"
        return "continue"
    state.cursor = state.advance(state.cursor)
    if state.cursor < 21:
        return "continue"
    _v3_cohort_done(state, run)
    return None


def _v3_after_review(state: _V3, run: TeamworkRun, action, result, previous):
    if state.mode in ("learning_review", "corrected_learning_review"):
        _v3_learning_review(state, run, result)
        return "continue"
    return _v3_after_cohort_review(state, run, result)


def _claim_overlaps(claim: str, host_finding_set: set) -> bool:
    if claim in host_finding_set:
        return True
    for finding in host_finding_set:
        if claim in finding:
            return True
    return False


def _matching_claims(claims: list[str], host_finding_set: set) -> set:
    if not host_finding_set:
        return set(claims)
    matched = set()
    for claim in claims:
        if _claim_overlaps(claim, host_finding_set):
            matched.add(claim)
    return matched


def _v3_account_host_failed(state: _V3, result: TeamworkObservation) -> None:
    if not state.candidate_reviewer_claims:
        return
    matching = _matching_claims(state.candidate_reviewer_claims, set(result.findings))
    state.failures_reproduced += len(matching)
    state.false_alarms += len(set(state.candidate_reviewer_claims) - matching)
    state.candidate_reviewer_claims.clear()


def _v3_host_failed(result: TeamworkObservation) -> bool:
    if result.findings:
        return True
    return result.check is not None and result.check.exit_status != 0


def _v3_account_recheck(state: _V3, result: TeamworkObservation) -> None:
    if _v3_host_failed(result):
        _v3_account_host_failed(state, result)
        return
    if not state.candidate_reviewer_claims:
        return
    state.false_alarms += len(set(state.candidate_reviewer_claims))
    state.candidate_reviewer_claims.clear()


def _handoff_entry(finding: str):
    entry, _, code = finding.partition(":residual:")
    if code != "HOST_ARTIFACTS_REQUIRED":
        return None
    if not entry.startswith("digestion.blocked[") or not entry.endswith("]"):
        return None
    if not entry[len("digestion.blocked["):-1].isdigit():
        return None
    return entry


def _other_residual(result: TeamworkObservation, entry: str, finding: str) -> bool:
    prefix = entry + ":residual:"
    for item in result.findings:
        if item.startswith(prefix) and item != finding:
            return True
    return False


def _collect_handoff(state: _V3, result: TeamworkObservation) -> None:
    for finding in result.findings:
        entry = _handoff_entry(finding)
        if entry is None:
            continue
        state.handoff_markers.add(finding)
        state_marker = entry + ":state:blocked"
        if state_marker in result.findings and not _other_residual(result, entry, finding):
            state.handoff_markers.add(state_marker)


def _v3_finish_digest(state: _V3, result: TeamworkObservation) -> None:
    if (state.reason == "HOST_ARTIFACTS_REQUIRED"
            and state.resume_mode in ("finish_learn", "learning_correction")):
        # Remember only this stopped finish's host-derived handoff
        # markers. Other residuals and later model findings stay open.
        _collect_handoff(state, result)
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    if state.query_disposition is not None:
        state.advisory_frontier = state.frontier
    state.mode = state.final_diagnostics


def _v3_merge_advisory(state: _V3, result: TeamworkObservation) -> None:
    state.advisory_frontier = tuple(sorted({*state.advisory_frontier, *state.frontier, *result.findings}))
    state.frontier = state.advisory_frontier


def _v3_keep_digest_query(state: _V3, previous: dict) -> bool:
    if state.query_disposition is None or state.stage != "digest":
        return False
    return state.artifacts == previous


def _v3_apply_checked(state: _V3, result: TeamworkObservation, checked) -> None:
    state.query_disposition = checked
    _v3_merge_advisory(state, result)


def _v3_reject_unchecked_query(state: _V3, result: TeamworkObservation) -> None:
    # An empty success summary or forged capture cannot use the
    # preliminary query route to discard the review frontier.
    state.query_disposition = None
    state.frontier = tuple(sorted({*state.frontier, *result.findings,
        "Strict query disposition requires the bound original checker capture."}))


def _v3_apply_query(state: _V3, run: TeamworkRun, action, result, previous) -> bool:
    after_learning = state.mode in ("learn_recheck", "learn_digest")
    checked = None
    if state.stage == "recheck":
        checked = _checked_query_disposition(run, action, result, state.producer)
    if checked is not None:
        _v3_apply_checked(state, result, checked)
        return after_learning
    if _v3_keep_digest_query(state, previous):
        _v3_merge_advisory(state, result)
        return after_learning
    if state.stage == "recheck" and _query_candidate(run, state.producer) is not None:
        _v3_reject_unchecked_query(state, result)
        return after_learning
    state.query_disposition = None
    state.frontier = tuple(sorted(set(result.findings)))
    return after_learning


def _v3_store_or_review(state: _V3, after_learning: bool) -> str:
    if after_learning or state.learning_done:
        if state.review_learning:
            return "learning_review"
        return "finish_complete"
    return "finish_store"


def _v3_enter_repair(state: _V3) -> None:
    state.mode = "repair"
    if state.repairs >= state.repair_limit:
        state.stop("REPAIR_ALLOWANCE_EXHAUSTED")


def _v3_native_recheck_mode(after_learning: bool) -> str:
    if after_learning:
        return "native_learn_post"
    return "native_post"


def _v3_source_recheck_mode(after_learning: bool) -> str:
    if after_learning:
        return "learn_digest"
    return "digest"


def _v3_after_recheck_mode(state: _V3, run: TeamworkRun, after_learning: bool) -> None:
    if run.schema_version == "core.adversary.teamwork.v4" and not (after_learning and state.reuse_native):
        state.mode = _v3_native_recheck_mode(after_learning)
        return
    if state.source_bound:
        state.mode = _v3_source_recheck_mode(after_learning)
        return
    state.mode = _v3_store_or_review(state, after_learning)


def _v3_after_query(state: _V3, run: TeamworkRun, after_learning: bool) -> None:
    if state.frontier and state.query_disposition is None:
        _v3_enter_repair(state)
        return
    if state.stage != "recheck":
        state.mode = _v3_store_or_review(state, after_learning)
        return
    _v3_after_recheck_mode(state, run, after_learning)


def _v3_after_recheck_or_digest(state: _V3, run: TeamworkRun, action, result, previous):
    if state.stage == "recheck":
        _v3_account_recheck(state, result)
    if state.mode == "finish_digest":
        _v3_finish_digest(state, result)
        return "continue"
    _v3_after_query(state, run, _v3_apply_query(state, run, action, result, previous))
    return None


def _v3_store_mode(state: _V3) -> None:
    if state.mode == "learning_correction_store":
        state.mode = "learning_correction"
        return
    state.mode = "finish_learn"


def _v3_after_store(state: _V3, run: TeamworkRun, action, result, previous):
    state.program = result.ddc_program
    if result.intelligence:
        state.source_bound = True
        if result.intelligence.coverage_gaps and not state.stopped_status:
            state.reason, state.stopped_status = "INTAKE_COVERAGE_OPEN", "blocked"
            state.resume_stage = "digest"
    _v3_store_mode(state)
    return None


def _v3_clear_handoff(state: _V3, result: TeamworkObservation) -> None:
    if state.retrying_learning_handoff and result.metadata.get("host_artifacts_checked") is True:
        state.frontier = tuple(item for item in state.frontier if item not in state.handoff_markers)
    state.retrying_learning_handoff = False


def _v3_learn_query(state: _V3, changed: bool) -> None:
    if state.query_disposition is None:
        return
    if changed:
        state.query_disposition = None
        return
    state.advisory_frontier = tuple(sorted({*state.advisory_frontier, *state.frontier}))


def _v3_learn_follow(run: TeamworkRun, changed: bool) -> str:
    follow = bool(changed or run.feedback_policy)
    if run.schema_version != "core.adversary.teamwork.v4":
        if follow:
            return "learn_recheck"
        return "finish_complete"
    if follow:
        return "native_learn_pre"
    return "native_finish"


def _v3_learn_next(state: _V3, run: TeamworkRun, changed: bool) -> None:
    if state.stopped_status:
        state.mode = state.semantic_finish
        return
    if state.mode == "learning_correction":
        # Keep the prior finding until Defect Hunter actually reads this reply.
        # Unchanged candidates retain their independently checked native scope.
        state.reuse_native = not changed
        state.correction_pending = False
        state.mode = "corrected_learning_review"
        return
    if state.frontier and state.query_disposition is None:
        state.mode = "repair"
        if state.repairs >= state.repair_limit:
            state.stop("REPAIR_ALLOWANCE_EXHAUSTED")
        return
    state.reuse_native = False
    state.mode = _v3_learn_follow(run, changed)


def _v3_after_learn(state: _V3, run: TeamworkRun, action, result, previous):
    state.learning_done = True
    _v3_clear_handoff(state, result)
    state.frontier = tuple(sorted({*state.frontier, *result.findings}))
    changed = bool(result.metadata.get("changed_paths")) or state.artifacts != previous
    _v3_learn_query(state, changed)
    _v3_learn_next(state, run, changed)
    return None


def _v3_native_post(state: _V3) -> str:
    if state.source_bound:
        return "digest"
    return "finish_store"


def _v3_native_learn_post(state: _V3) -> str:
    if state.source_bound:
        return "learn_digest"
    if state.review_learning:
        return "learning_review"
    return "finish_complete"


def _v3_native_plan(state: _V3) -> str:
    return "plan"


def _v3_native_recheck(state: _V3) -> str:
    return "recheck"


def _v3_native_learn_recheck(state: _V3) -> str:
    return "learn_recheck"


def _v3_native_finish(state: _V3) -> str:
    return "finish_complete"


_V3_NATIVE = {
    "native_intake": _v3_native_plan,
    "native_pre": _v3_native_recheck,
    "native_learn_pre": _v3_native_learn_recheck,
    "native_post": _v3_native_post,
    "native_learn_post": _v3_native_learn_post,
    "native_finish": _v3_native_finish,
}


def _v3_after_native(state: _V3, run: TeamworkRun, action, result, previous):
    chosen = _V3_NATIVE.get(state.mode)
    if chosen is not None:
        state.mode = chosen(state)
    return None


def _v3_after_complete(state: _V3, run: TeamworkRun, action, result, previous):
    state.mode = "terminal"
    return None


_V3_STAGE = {
    "build": _v3_after_build,
    "repair": _v3_after_build,
    "review": _v3_after_review,
    "recheck": _v3_after_recheck_or_digest,
    "digest": _v3_after_recheck_or_digest,
    "ddc_store": _v3_after_store,
    "learn": _v3_after_learn,
    "native_gates": _v3_after_native,
    "ddc_complete": _v3_after_complete,
}


def _v3_apply_stage(state: _V3, run: TeamworkRun, action, result, previous):
    handler = _V3_STAGE.get(state.stage)
    if handler is None:
        return None
    return handler(state, run, action, result, previous)


def _v3_observe(state: _V3, run: TeamworkRun, index: int):
    action, result, previous = _v3_bind(state, run, index)
    _v3_spend(state)
    state.artifacts.update(result.artifacts)
    if _v3_take_route(state, action, result):
        return None
    if result.blocked:
        _v3_on_blocked(state, result)
        return None
    state.attempted_routes.clear()
    return _v3_apply_stage(state, run, action, result, previous)


def _v3_step(state: _V3, run: TeamworkRun, index: int) -> bool:
    _v3_resume_point(state, index)
    state.stage, state.descriptor = state.pending()
    _v3_allowance(state, run, index)
    state.stage, state.descriptor = state.pending()
    if index == len(run.observations):
        return True
    if state.mode == "terminal" or index >= state.action_limit:
        raise ValueError("TERMINAL_RUN: no observations beyond the retained cap or finish")
    _v3_observe(state, run, index)
    return False


def _v3_result(state: _V3) -> tuple:
    extra = {"stopped_status": state.stopped_status,
        "evaluations_used": state.evaluations, "ddc_program": state.program,
        "semantic_review_pending": state.semantic_review_pending or state.correction_pending,
        "failures_reproduced": state.failures_reproduced,
        "false_alarms": state.false_alarms}
    if state.query_disposition is not None:
        extra["clarification_context"] = {
            **state.query_disposition, "advisory_findings": list(state.advisory_frontier)}
    if state.schedule is not None:
        extra["schedule_skips"] = list(state.schedule_skips)
    return (state.stage, state.producer, state.repairs, (state.repair_limit, state.action_limit),
            state.reason, state.resume_stage, state.frontier, state.descriptor, extra)


def _trace_v3(run: TeamworkRun) -> tuple:
    """Replay actual evaluation episodes and a reserved, required finish sequence."""
    plan = run.panel_plan
    if plan is None:
        raise ValueError("PANEL_PLAN_REQUIRED")
    plan.validate_totality()
    state = _V3(run, plan)
    _require_continuation_positions(run, state.points)
    if run.intelligence and run.intelligence.coverage_gaps:
        state.stop("INTAKE_COVERAGE_OPEN", "blocked")
    for index in range(len(run.observations) + 1):
        if _v3_step(state, run, index):
            break
    return _v3_result(state)


def _validate_panel_observation(action: TeamworkAction, result: TeamworkObservation) -> None:
    if result.action_id != action.action_id:
        raise ValueError("ACTION_MISMATCH: result does not bind the pending task and candidate")
    if result.metadata.get("role_id") != action.role_id:
        raise ValueError("PANEL_ROLE_MISMATCH: bind the actual pending role")
    from .teamwork_pfp import validate_teamwork_observation

    _validate_retained_role_bytes(
        json.dumps(action.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False),
        json.dumps(result.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False),
        validate_teamwork_observation)


@lru_cache(maxsize=128)
def _validate_retained_role_bytes(action_json: str, result_json: str, validator: Callable) -> None:
    """Memoize only a pure exact-byte check, never host readback or execution.

    Nested mutable metadata is serialized on every call, so changing any retained
    byte or action binding invokes the validator again. A replaced validator has
    a different key. The bounded cache makes repeated state replay practical.
    """
    validator(TeamworkAction.model_validate_json(action_json),
              TeamworkObservation.model_validate_json(result_json))


def _require_acceptance_binding(acceptance_check, intelligence, checker_id, check_command) -> None:
    if acceptance_check is None and not (intelligence and checker_id.strip() and check_command):
        raise ValueError("ACCEPTANCE_BINDING_REQUIRED: select the original independent host check before work")


def _require_start_plan(panel_plan) -> None:
    if panel_plan is None:
        raise ValueError("PANEL_PLAN_REQUIRED: bind the governed 22-member plan at composition")


def _reject_unbound_explicit_checks(checker_id, check_command, intelligence, acceptance_check) -> None:
    if (checker_id or check_command) and intelligence is None and acceptance_check is None:
        raise ValueError("ACCEPTANCE_BINDING_REQUIRED: explicit checks need source-bound acceptance")


def _require_checker_command(intelligence, checker_id, check_command) -> None:
    if intelligence and (not checker_id.strip() or not check_command):
        raise ValueError("CHECKER_REQUIRED: bind the original acceptance command at intake")


def _teamwork_schema(native_gate_check) -> str:
    if native_gate_check is not None:
        return "core.adversary.teamwork.v4"
    return "core.adversary.teamwork.v3"


def _teamwork_run_id(run_id: str | None) -> str:
    if run_id:
        return run_id
    return uuid.uuid4().hex


def _teamwork_objective(objective: str, brief) -> str:
    if brief and brief.density_dimension is not None:
        return objective
    return objective.strip()


def start_teamwork(
    objective: str, *, executor: Literal["ide", "openrouter", "anthropic"] = "ide",
    max_repairs: int = 1, run_id: str | None = None,
    intelligence: IntelligenceRead | None = None,
    checker_id: str = "", check_command: tuple[str, ...] = (),
    max_actions: int = 48,
    learn_after_run: bool = True,
    panel_plan: PanelPlan | None = None,
    acceptance_check: HostAcceptanceRequirement | None = None,
    max_evaluations: int = 10,
    brief: TeamworkBrief | None = None,
    native_gate_check: NativeGateCheck | None = None,
) -> TeamworkRun:
    _require_acceptance_binding(acceptance_check, intelligence, checker_id, check_command)
    _require_start_plan(panel_plan)
    _reject_unbound_explicit_checks(checker_id, check_command, intelligence, acceptance_check)
    _require_checker_command(intelligence, checker_id, check_command)
    return TeamworkRun(
        schema_version=_teamwork_schema(native_gate_check),
        native_gate_check=native_gate_check, panel_plan=panel_plan,
        acceptance_check=acceptance_check,
        run_id=_teamwork_run_id(run_id),
        objective=_teamwork_objective(objective, brief),
        executor=executor, max_repairs=max_repairs, intelligence=intelligence,
        checker_id=checker_id, check_command=check_command,
        max_actions=max_actions, learn_after_run=learn_after_run, max_evaluations=max_evaluations,
        brief=brief, feedback_policy="semantic_digestion_v2",
    )


def next_action(run: TeamworkRun) -> TeamworkAction | None:
    trace = _trace_v3(run) if run.schema_version in CURRENT_TEAMWORK_VERSIONS else (
        _trace_panel(run) if run.schema_version == "core.adversary.teamwork.v2" else _trace_legacy(run))
    stage, producer, _spent, _limits, _reason, _resume_stage, frontier = trace[:7]
    if stage not in _INSTRUCTIONS:
        return None
    descriptor = trace[7] if run.panel_plan is not None else ("", "", "pfp")
    return _make_action(run, stage, producer, frontier, descriptor,
        v3_context={**trace[8], "stopped_reason": trace[4]} if len(trace) > 8 else None)


def effective_acceptance(run: TeamworkRun) -> HostAcceptanceRequirement | None:
    """Select an explicit wrapper successor without replacing original obligations.

    The host still validates source bytes and exact immutable parent history.
    Prefix replay sees only the continuation markers effective at that prefix.
    """
    selected = run.acceptance_check
    for point in run.continuations:
        successor = point.acceptance_successor
        if successor is None or point.after_observations > len(run.observations):
            continue
        if (selected is None or successor.checker_id != selected.checker_id
                or successor.source_id == selected.source_id
                or any(successor.check_source_paths.get(path) != digest
                       for path, digest in selected.check_source_paths.items())
                or successor.check_source_paths.get(point.parent_state_path) != point.parent_state_sha256):
            raise ValueError("CONTINUATION_ACCEPTANCE_MISMATCH: retain checker, sources and parent")
        selected = successor
    return selected


def _schedule_of(run: TeamworkRun):
    if run.panel_plan is None:
        return None
    return run.panel_plan.schedule


def _seat_id_set(schedule) -> set[str]:
    found = set()
    for seat in schedule.seats:
        found.add(seat.role_id)
    return found


def _blind_review(run: TeamworkRun, phase: str, role_id: str) -> bool:
    schedule = _schedule_of(run)
    if schedule is None or phase != "review":
        return False
    if role_id not in _seat_id_set(schedule):
        return False
    return schedule.policy(role_id).view == "blind"


def _strip_action_state(run: TeamworkRun, state: dict) -> None:
    # Provider custody is outside the semantic task; replay keeps the original action ID.
    state.pop("provider_binding")
    state.pop("episode_binding", None)
    if run.panel_plan is None:
        state.pop("panel_plan")  # Never backdate the new workflow into historical action IDs.
        state.pop("acceptance_check")
    if not run.learn_after_run:
        state.pop("learn_after_run")  # Preserve pending action IDs from legacy state files.


def _producer_index(run: TeamworkRun, producer_action_id) -> int:
    for idx, obs in enumerate(run.observations):
        if obs.action_id == producer_action_id:
            return idx
    return -1


def _intake_build_ids(run: TeamworkRun) -> set[str]:
    found = set()
    for step in run.panel_plan.steps:
        if step.phase in ("intake", "build"):
            found.add(step.role_id)
    return found


def _keep_intake_build(run: TeamworkRun, state: dict) -> None:
    roles = _intake_build_ids(run)
    kept = []
    for obs in state["observations"]:
        if obs.get("metadata", {}).get("role_id") in roles:
            kept.append(obs)
    state["observations"] = kept


def _trim_blind_observations(run: TeamworkRun, state: dict, producer, role_id: str) -> None:
    state["_blind_role_id"] = role_id
    producer_action_id = None
    if producer:
        producer_action_id = producer.action_id
    producer_idx = _producer_index(run, producer_action_id)
    if producer_idx >= 0:
        state["observations"] = state["observations"][:producer_idx + 1]
        return
    if run.panel_plan is not None:
        _keep_intake_build(run, state)


def _action_wire(run: TeamworkRun, producer, role_id: str, phase: str) -> tuple[str, bool]:
    from adversary.infrastructure.prompt_geometry import discard_geometry_diagnostics

    state = run.model_dump(mode="json")
    discard_geometry_diagnostics(state)
    _strip_action_state(run, state)
    blind = _blind_review(run, phase, role_id)
    if blind and phase == "review":
        _trim_blind_observations(run, state, producer, role_id)
    wire = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return wire, blind


def _read_sources(run: TeamworkRun, source, source_reads: list, findings):
    artifacts: dict[str, str] = {}
    for item in run.observations:
        artifacts.update(item.artifacts)
        if item.intelligence:
            source = item.intelligence
            source_reads.append(source)
    if source and not run.observations:
        findings = source.findings
    return findings, source, source_reads, artifacts


def _merged_artifacts(run: TeamworkRun) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for item in run.observations:
        artifacts.update(item.artifacts)
    return artifacts


def _collect_materials(run: TeamworkRun, producer, frontier):
    findings = frontier
    source = run.intelligence
    source_reads = []
    if source:
        source_reads = [source]
    if source or (run.panel_plan is not None and run.feedback_policy):
        return _read_sources(run, source, source_reads, findings)
    if run.panel_plan is not None:
        return findings, source, source_reads, _merged_artifacts(run)
    artifacts: dict[str, str] = {}
    if producer:
        artifacts = producer.artifacts
    return findings, source, source_reads, artifacts


def _role_step(run: TeamworkRun, role_id: str):
    if run.panel_plan is None:
        return None
    for item in run.panel_plan.steps:
        if item.role_id == role_id:
            return item
    return None


def _assigned_model(run: TeamworkRun, step, model_tier: str) -> str:
    if step.model:
        return step.model
    if not run.panel_plan.preset:
        return ""
    return load_panel_preset(run.panel_plan.preset).get(model_tier, "")


def _assigned_family(role_id: str, model_tier: str, assigned_model: str) -> str:
    if model_tier == "no_llm" or role_id == "syntax_prefilter":
        return "deterministic"
    if "/" in assigned_model:
        return assigned_model.split("/")[0]
    if assigned_model:
        return "native"
    return ""


def _role_assignment(run: TeamworkRun, step, role_id: str):
    operation = step.operation_binding
    model_tier = step.default_tier
    assigned_model = _assigned_model(run, step, model_tier)
    assigned_family = _assigned_family(role_id, model_tier, assigned_model)
    if run.panel_plan.schema_version.endswith(".v2") and operation is None:
        raise ValueError("PANEL_OPERATION_BINDING_REQUIRED")
    return operation, model_tier, assigned_model, assigned_family


_INTAKE_TEXT = (
    "Inspect the original need, relevant existing owners and the declared constraints. "
    "Return a concise concrete contribution from this role's perspective and only "
    "actionable findings. Before a candidate exists, review the plan and prerequisites. "
    "Do not claim an artifact was built or a checker ran. "
)
_ROLE_TAIL = (
    " This is a mandatory role contribution, not proof of an independent agent. "
    "Use PFP for any model communication. Persona agreement cannot certify task correctness."
)
_BLIND_REVIEW_TEXT = (
    " Review the current candidate independently against the original need and intake. "
    "Other reviewers' contributions are withheld on purpose; report the defects you find yourself."
)
_OPEN_REVIEW_TEXT = (
    " Inspect prior role contributions, original intake findings and the current candidate; "
    "report unresolved defects after the build rather than repeating already repaired concerns."
)
_SYNTAX_PREFILTER_TEXT = (
    "Syntax Prefilter: run the bound deterministic syntax/intake checker without any LLM. "
    "Return the actual command, exit status, output digest and checked artifact bindings. "
    "No tool availability or success may be inferred from the role name."
)
_BACKDOOR_AUDITOR_TEXT = " Review retention and stale outputs only; this role never authorizes deletion."
_MASTER_TEXT = (
    " Review existing mechanization evidence and a bounded formalization plan. "
    "Do not schedule new formal execution before a separately admitted PASS_TO_MASTER."
)


def _role_preamble(step, phase: str, instructions: str) -> str:
    return (
        f"{step.name}/{phase}: {step.role}. Cognitive perspective: {step.cognitive_operator}. "
        f"Governed acts: {', '.join(step.pipeline_acts)}. " + instructions + _ROLE_TAIL
    )


def _review_suffix(phase: str, blind: bool) -> str:
    if phase != "review":
        return ""
    if blind:
        return _BLIND_REVIEW_TEXT
    return _OPEN_REVIEW_TEXT


def _named_role_text(instructions: str, role_id: str) -> str:
    if role_id == "syntax_prefilter":
        return _SYNTAX_PREFILTER_TEXT
    if role_id == "backdoor_auditor":
        return instructions + _BACKDOOR_AUDITOR_TEXT
    if role_id == "master":
        return instructions + _MASTER_TEXT
    return instructions


def _role_text(step, phase: str, stage: str, blind: bool, role_id: str, instructions: str) -> str:
    if stage in ("build", "review", "repair"):
        instructions = instructions.split(": ", 1)[-1]
    if phase == "intake":
        instructions = _INTAKE_TEXT
    return _named_role_text(_role_preamble(step, phase, instructions) + _review_suffix(phase, blind), role_id)


def _with_role(run: TeamworkRun, stage: str, role_id: str, phase: str, blind: bool, instructions: str):
    step = _role_step(run, role_id)
    if step is None:
        return None, "", "", "", instructions
    operation, tier, model, family = _role_assignment(run, step, role_id)
    return operation, tier, model, family, _role_text(step, phase, stage, blind, role_id, instructions)


_LEARN_CONSUME = (
    " Consume the host-read retained DDC program in this action. Bind its exact semantic root "
    "and canonical procedure digest in consumed_ddc_root and consumed_procedure_sha256. "
    "Retain the original candidate and all open findings. A partial run remains partial; "
    "the learning outcome never supplies acceptance of the original task."
)
_LEARN_BINDING = (
    " Copy consumed_ddc_root and consumed_procedure_sha256 exactly from "
    "ddc_program.learning_reply_binding in this action; these host-calculated values "
    "identify the readback. Do not substitute the roster plan digest or compute a new digest."
)
_LEARN_HOST = (
    " Use ddc_program.host_observation for captured accounting and stop facts through "
    "its observation_count only, before this learning reply. Task text and earlier role "
    "summaries are not observations of provider costs or dispatch status. KNOWN_COST "
    "does not support an unknown-cost halt; UNKNOWN_COST names captured provider "
    "attempts with unavailable costs. UNOBSERVED billing for IDE or native work is "
    "not provider UnknownCost and is not evidence of free usage. State an actual halt "
    "only from the observed stopped_status and stopped_reason; distinguish hypothetical "
    "policy advice. This context does not authorize dispatch, change an allowance, or "
    "settle future or missing provider costs."
)


def _context_program(v3_context):
    if not v3_context:
        return None
    return v3_context.get("ddc_program")


def _learn_instructions(run: TeamworkRun, stage: str, instructions: str, v3_context) -> str:
    if run.schema_version not in CURRENT_TEAMWORK_VERSIONS or stage != "learn":
        return instructions
    instructions += _LEARN_CONSUME
    program = _context_program(v3_context)
    if program is not None and program.learning_reply_binding is not None:
        instructions += _LEARN_BINDING
    if program is not None and program.host_observation is not None:
        instructions += _LEARN_HOST
    return instructions


def _latest_match(run: TeamworkRun, predicate):
    for item in reversed(run.observations):
        if predicate(item):
            return item
    return None


def _is_scar_chronicler_learn(item: TeamworkObservation) -> bool:
    if item.metadata.get("learning_stage") != "learn":
        return False
    if item.metadata.get("role_id") != "scar_chronicler":
        return False
    return not item.blocked


def _is_host_digestion(item: TeamworkObservation) -> bool:
    return item.metadata.get("role_id") == "host_digestion" and not item.blocked


def _model_dump_or_none(value):
    if value is None:
        return None
    return value.model_dump(mode="json")


def _host_observation_dump(program):
    if not program or not program.host_observation:
        return None
    return program.host_observation.model_dump(mode="json")


def _semantic_learning_context(run: TeamworkRun, v3_context, clarification_context) -> dict:
    learned = _latest_match(run, _is_scar_chronicler_learn)
    digested = _latest_match(run, _is_host_digestion)
    context = {
        "learning": _model_dump_or_none(learned),
        "digestion": _model_dump_or_none(digested),
        "host_observation": _host_observation_dump(_context_program(v3_context)),
    }
    if clarification_context is not None:
        context["clarification_context"] = clarification_context
    return context


_LEARNING_REVIEW_TEXT = (
    " Review the actual latest learned reply and digestion in learning_context, including "
    "lessons, observed stop/billing claims and their evidence. Distinguish current facts "
    "from hypothetical advice, old failures and future reuse requirements. Report concrete "
    "unsupported or contradictory claims even when the original artifact checker passed. "
    "Inspect every pending learning finding against this appended correction; return only "
    "remaining findings. A clean review is advisory evidence, not a semantic proof or "
    "authority to install guidance. Do not modify the original deliverable."
)
_LEARNING_CORRECTION_TEXT = (
    " Append a corrected learned reply addressing the pending learning-review findings. "
    "Preserve the original deliverable and prior raw reply; a prose error is not a request "
    "to rewrite the task artifact. Use the current native readback binding. State actual "
    "changed files only if a justified owning-file repair was applied; otherwise give a "
    "specific no_change_reason. Your reply will itself be reviewed before closure."
)


def _learning_phase_text(phase: str) -> str:
    if phase == "learning_review":
        return _LEARNING_REVIEW_TEXT
    return _LEARNING_CORRECTION_TEXT


def _clarification_from(v3_context):
    if not v3_context:
        return None
    return v3_context.get("clarification_context")


def _learning_bundle(run: TeamworkRun, phase: str, v3_context, instructions: str):
    clarification_context = _clarification_from(v3_context)
    if run.feedback_policy != "semantic_digestion_v2" or phase not in ("learning_review", "learning_correction"):
        return None, clarification_context, instructions
    context = _semantic_learning_context(run, v3_context, clarification_context)
    return context, clarification_context, instructions + _learning_phase_text(phase)


def _brief_operator(brief: TeamworkBrief, communication: str, stage: str) -> str:
    if communication != "pfp":
        return ""
    return {"build": brief.builder, "review": brief.reviewer, "repair": brief.repairer}.get(stage, "")


def _visible_brief(brief: TeamworkBrief) -> str:
    if brief.forge_preparation is not None:
        return brief.model_dump_json(exclude={"forge_preparation"})
    return brief.model_dump_json()


_CLARIFICATION_PERMIT = (
    " This task explicitly permits a strict QUERY_USER_MORE_INFO residual for genuinely missing "
    "declared inputs. Only the bound original checker can confirm it. Retain questions and "
    "advisory findings; do not invent premises or call a checked question mathematically solved."
)
_CLARIFICATION_CONTEXT = (
    " clarification_context is the checked current query disposition, still NOT_SOLVED. "
    "Missing external inputs are retained advisory obligations; learning review must report "
    "its real findings without asking mathematical repair to invent those inputs."
)


def _with_brief(run: TeamworkRun, instructions: str, communication: str, stage: str, clarification_context):
    if not run.brief:
        return instructions, ""
    operator = _brief_operator(run.brief, communication, stage)
    instructions += ("\nTask brief (guidance only; preferred workers do not replace the mandatory role, "
        "permissions or independent acceptance): " + _visible_brief(run.brief))
    if not run.brief.clarification_policy:
        return instructions, operator
    instructions += _CLARIFICATION_PERMIT
    if clarification_context is not None:
        instructions += _CLARIFICATION_CONTEXT
    return instructions, operator


def _pending_route(run: TeamworkRun, communication: str, stage: str, role_id: str):
    if communication != "pfp" or stage not in ("build", "review", "repair") or not run.observations:
        return None
    last = run.observations[-1]
    if last.metadata.get("role_id") != role_id:
        return None
    return _optional_route(last)


def _with_route(run: TeamworkRun, communication: str, stage: str, role_id: str, operator: str, instructions: str):
    route = _pending_route(run, communication, stage, role_id)
    if not route:
        return operator, None, instructions
    if route.operator:
        operator = route.operator
    instructions += ("\nOptional tool unavailable: " + route.tool + ". Use this declared alternative "
        "for the same required role: " + route.alternative + ". Retain all findings, permissions "
        "and required checks. Route guidance: " + route.model_dump_json())
    return operator, route, instructions


def _acceptance_chain(run: TeamworkRun):
    acceptance = effective_acceptance(run)
    predecessors = []
    previous = run.acceptance_check
    for point in run.continuations:
        if point.acceptance_successor is None or point.after_observations > len(run.observations):
            continue
        if previous is not None:
            predecessors.append(previous)
        previous = point.acceptance_successor
    return acceptance, predecessors


def _contribution_visible(item, producer, blind: bool, intake_ids: set[str]) -> bool:
    if not blind:
        return True
    if item is producer:
        return True
    return item.metadata["role_id"] in intake_ids


def _role_contributions(run: TeamworkRun, producer, blind: bool) -> tuple:
    intake_ids: set[str] = set()
    if blind:
        intake_ids = _intake_build_ids(run)
    rows = []
    for item in run.observations:
        if "role_id" not in item.metadata or item.blocked:
            continue
        if not _contribution_visible(item, producer, blind, intake_ids):
            continue
        rows.append({"role_id": item.metadata["role_id"], "worker": item.worker,
            "summary": item.summary, "findings": list(item.findings)})
    return tuple(rows)


def _current_run_id(run: TeamworkRun) -> str:
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        return run.run_id
    return ""


def _candidate_text(producer) -> str:
    if producer:
        return producer.content
    return ""


def _plan_sha(run: TeamworkRun) -> str:
    if run.panel_plan:
        return run.panel_plan.plan_sha256
    return ""


def _acceptance_fields(run: TeamworkRun, acceptance):
    if not acceptance:
        return run.checker_id, run.check_command, "", {}
    return acceptance.checker_id, acceptance.operation, acceptance.source_id, acceptance.check_source_paths


def _native_gate_batches(run: TeamworkRun) -> tuple:
    rows = []
    for item in run.observations:
        if "native_gate_receipt" in item.metadata:
            rows.append(item.metadata["native_gate_receipt"])
    return tuple(rows)


_HOST_CAPTURE_KEYS = ("process_observations", "process_capture", "checker_capture",
                      "kernel_observations", "kernel_capture", "resource_capture")


def _host_observation_row(item: TeamworkObservation) -> dict:
    row = {"check": item.check.model_dump(mode="json") if item.check else None,
           "stdout": item.metadata.get("stdout", ""), "stderr": item.metadata.get("stderr", "")}
    for name in _HOST_CAPTURE_KEYS:
        if name in item.metadata:
            row[name] = item.metadata[name]
    row["action_id"] = item.action_id
    return row


def _host_capture_present(item: TeamworkObservation) -> bool:
    if item.check is not None:
        return True
    for name in ("process_capture", "kernel_capture", "resource_capture"):
        if name in item.metadata:
            return True
    return False


def _host_execution(item: TeamworkObservation) -> bool:
    if not _host_capture_present(item):
        return False
    return item.metadata.get("execution_kind") == "host"


def _native_host_observations(run: TeamworkRun) -> tuple:
    rows = []
    for item in run.observations:
        if _host_execution(item):
            rows.append(_host_observation_row(item))
    return tuple(rows)


def _context_value(v3_context, name: str, default=None):
    if not v3_context:
        return default
    return v3_context.get(name, default)


def _assemble_action(run, stage, producer, wire, role_id, phase, communication, pack, v3_context,
                     acceptance, predecessors) -> TeamworkAction:
    checker_id, check_command, check_source_id, check_source_paths = _acceptance_fields(run, acceptance)
    return TeamworkAction(
        action_id=hashlib.sha256(wire.encode("utf-8")).hexdigest(), kind=stage,
        run_id=_current_run_id(run),
        objective=run.objective, instructions=pack["instructions"],
        operation_binding=pack["operation"],
        operation_required=pack["operation"] is not None,
        candidate=_candidate_text(producer), findings=pack["findings"],
        artifacts=pack["artifacts"], intelligence=pack["source"],
        initial_task_id=_task_identity(run),
        checker_id=checker_id, check_command=check_command,
        source_reads=tuple(pack["source_reads"]),
        role_id=role_id, phase=phase, communication=communication,
        workflow_version=run.schema_version, plan_sha256=_plan_sha(run),
        role_contributions=_role_contributions(run, producer, pack["blind"]),
        check_source_id=check_source_id, check_source_paths=check_source_paths,
        acceptance_predecessors=tuple(predecessors),
        ddc_program=_context_value(v3_context, "ddc_program"),
        stopped_reason=_context_value(v3_context, "stopped_reason", ""),
        stopped_status=_context_value(v3_context, "stopped_status", ""),
        evaluations_used=_context_value(v3_context, "evaluations_used", 0),
        evaluation_limit=run.max_evaluations,
        brief=run.brief, operator=pack["operator"], route=pack["route"],
        feedback_policy=run.feedback_policy,
        learning_context=pack["learning_context"], clarification_context=pack["clarification_context"],
        native_gate_check=run.native_gate_check,
        native_gate_batches=_native_gate_batches(run),
        native_host_observations=_native_host_observations(run),
        model_tier=pack["model_tier"], assigned_model=pack["assigned_model"],
        assigned_family=pack["assigned_family"],
    )


def _make_action(run: TeamworkRun, stage: str, producer: TeamworkObservation | None,
                 frontier: tuple[str, ...], descriptor: tuple[str, str, str],
                 *, v3_context: dict | None = None) -> TeamworkAction:
    role_id, phase, communication = descriptor
    wire, blind = _action_wire(run, producer, role_id, phase)
    findings, source, source_reads, artifacts = _collect_materials(run, producer, frontier)
    if blind:
        findings = ()  # A blind reviewer does not see the cohort's findings so far.
    instructions = _INSTRUCTIONS[stage]
    operation, model_tier, assigned_model, assigned_family, instructions = _with_role(
        run, stage, role_id, phase, blind, instructions)
    instructions = _learn_instructions(run, stage, instructions, v3_context)
    learning_context, clarification_context, instructions = _learning_bundle(
        run, phase, v3_context, instructions)
    instructions, operator = _with_brief(run, instructions, communication, stage, clarification_context)
    operator, route, instructions = _with_route(run, communication, stage, role_id, operator, instructions)
    acceptance, predecessors = _acceptance_chain(run)
    pack = {"instructions": instructions, "operation": operation, "model_tier": model_tier,
            "assigned_model": assigned_model, "assigned_family": assigned_family,
            "findings": findings, "source": source, "source_reads": source_reads,
            "artifacts": artifacts, "blind": blind, "operator": operator, "route": route,
            "learning_context": learning_context, "clarification_context": clarification_context}
    return _assemble_action(run, stage, producer, wire, role_id, phase, communication, pack,
                            v3_context, acceptance, predecessors)


def _require_pending_refusal(run: TeamworkRun) -> TeamworkAction:
    action = next_action(run)
    if action is None:
        raise ValueError("TERMINAL_RUN: required refusals cannot be routed around")
    return action


def _require_tool_failure_text(tool: str, reason: str) -> None:
    if not tool.strip() or not reason.strip():
        raise ValueError("TOOL_FAILURE_REQUIRED")


def _reject_illegal_alternative(action: TeamworkAction, optional: bool, alternative: str) -> None:
    if alternative and (not optional or action.communication != "pfp"
            or action.kind not in ("build", "review", "repair") or action.phase == "learning_review"):
        raise ValueError("OPTIONAL_ROUTE_REQUIRED: required checks and finish operations cannot be skipped")


def _optional_tool_route(tool: str, optional: bool, alternative: str, operator: str, scene: str,
                         skills: tuple[str, ...]):
    if optional and alternative:
        return OptionalToolRoute(tool=tool.strip(), alternative=alternative.strip(),
            operator=operator, scene=scene, skills=skills)
    return None


def _tool_failure_metadata(action: TeamworkAction, tool: str, optional: bool, route) -> dict:
    code = "REQUIRED_ACTION_UNAVAILABLE"
    if optional:
        code = "OPTIONAL_TOOL_UNAVAILABLE"
    metadata = {"failure_code": code, "role_id": action.role_id, "tool": tool,
        "host_tools_executed": False, "host_reported_tool_failure": True}
    if route:
        metadata["optional_route"] = route.model_dump(mode="json")
    return metadata


def tool_unavailable(
    run: TeamworkRun, *, tool: str, reason: str, optional: bool = False,
    alternative: str = "", operator: str = "", scene: str = "", skills: tuple[str, ...] = (),
    worker: str = "current IDE session",
) -> TeamworkRun:
    """Record an actual host tool failure; never substitute a required contribution."""
    action = _require_pending_refusal(run)
    _require_tool_failure_text(tool, reason)
    _reject_illegal_alternative(action, optional, alternative)
    route = _optional_tool_route(tool, optional, alternative, operator, scene, skills)
    metadata = _tool_failure_metadata(action, tool, optional, route)
    return observe(run, TeamworkObservation(action_id=action.action_id, worker=worker,
        summary=reason, blocked=True, metadata=metadata))


def _reject_legacy_observe(run: TeamworkRun) -> None:
    if run.schema_version not in CURRENT_TEAMWORK_VERSIONS:
        raise ValueError("LEGACY_WORKFLOW_READ_ONLY: historical states cannot start new role execution")
    if run.feedback_policy is None:
        raise ValueError("LEGACY_FEEDBACK_READ_ONLY: retain the historical run and start current governed work")


def _require_matching_action(run: TeamworkRun, result: TeamworkObservation) -> TeamworkAction:
    action = next_action(run)
    if action is None:
        raise ValueError("TERMINAL_RUN: no action is pending")
    if result.action_id != action.action_id:
        raise ValueError("ACTION_MISMATCH: result does not bind the pending task and candidate")
    return action


def _stamp_assigned_field(metadata: dict, present, key: str, value) -> None:
    if present and key not in metadata:
        metadata[key] = value


def _stamp_assignment(action: TeamworkAction, result: TeamworkObservation) -> None:
    _stamp_assigned_field(result.metadata, action.model_tier, "tier", action.model_tier)
    _stamp_assigned_field(result.metadata, action.assigned_model, "model", action.assigned_model)
    _stamp_assigned_field(result.metadata, action.assigned_family, "model_family", action.assigned_family)


def observe(run: TeamworkRun, result: TeamworkObservation) -> TeamworkRun:
    _reject_legacy_observe(run)
    action = _require_matching_action(run, result)
    if run.panel_plan is not None:
        _validate_panel_observation(action, result)
    result = _validate_action_result(run, action, result)
    _stamp_assignment(action, result)
    return run.model_copy(update={"observations": (*run.observations, result), "pending_prompt": None})


def _validate_review_digest(action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind != "review" or result.blocked:
        return
    claimed_digest = result.metadata.get("candidate_digest")
    if claimed_digest is None:
        return
    active_digest = hashlib.sha256(action.candidate.encode("utf-8")).hexdigest()
    if claimed_digest != active_digest:
        raise ValueError(
            f"STALE_CANDIDATE_DIGEST: claim references {claimed_digest}, active is {active_digest}"
        )


def _route_context_changed(result: TeamworkObservation, action: TeamworkAction) -> bool:
    if result.intelligence is not None:
        return True
    if result.check is not None:
        return True
    if result.ddc_program is not None:
        return True
    return bool(result.artifacts and result.artifacts != action.artifacts)


def _validate_optional_route_context(action: TeamworkAction, result: TeamworkObservation) -> None:
    if _optional_route(result) is None:
        return
    if action.communication != "pfp":
        return
    if action.kind not in ("build", "review", "repair"):
        return
    if action.phase == "learning_review":
        raise ValueError("REQUIRED_REVIEW_UNAVAILABLE: learning review cannot be skipped")
    if _route_context_changed(result, action):
        raise ValueError("OPTIONAL_ROUTE_CONTEXT_CHANGED: a tool failure cannot rebind retained evidence")


def _native_should_stop(action: TeamworkAction, summary: dict) -> bool:
    if not summary["coverage_complete"]:
        return True
    return action.native_gate_check.policy == "require_pass" and not summary["all_pass"]


def _validate_native_receipt(action: TeamworkAction, result: TeamworkObservation, receipt) -> None:
    validate_native_gate_receipt(action, receipt)
    summary = native_gate_summary(receipt)
    should_stop = _native_should_stop(action, summary)
    if result.blocked != should_stop or result.metadata.get("native_gate_summary") != summary:
        raise ValueError("NATIVE_GATE_POLICY_MISMATCH")


def _validate_native_gate_action(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if run.schema_version != "core.adversary.teamwork.v4" or action.kind != "native_gates":
        return
    receipt = result.metadata.get("native_gate_receipt")
    if receipt is not None:
        _validate_native_receipt(action, result, receipt)
        return
    if not result.blocked:
        raise ValueError("NATIVE_GATE_RECEIPT_REQUIRED")


def _ddc_prompt_digest(objective: str) -> str:
    return hashlib.sha256(objective.encode("utf-8")).hexdigest()


def _ddc_premises_digest(premises) -> str:
    payload = json.dumps(premises, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _ddc_binding_broken(run: TeamworkRun, program) -> bool:
    if program.binding.prompt_sha256 != _ddc_prompt_digest(run.objective):
        return True
    if program.binding.family_id != "adversary-teamwork-" + run.schema_version.rsplit(".", 1)[1]:
        return True
    return program.binding.template_version != run.schema_version


def _ddc_readback_broken(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation, program) -> bool:
    if program is None:
        return True
    if result.metadata.get("execution_kind") != "host":
        return True
    if _ddc_binding_broken(run, program):
        return True
    if program.premises != ddc_task_premises(action):
        return True
    return program.binding.premises_sha256 != _ddc_premises_digest(program.premises)


def _run_intake_broken(action: TeamworkAction, program, source) -> bool:
    if source is None:
        return True
    if source.initial_task_id != action.initial_task_id:
        return True
    if source.parent_source_id is not None:
        return True
    if source.source_locator != program.run_path:
        return True
    return source.source_id != program.source_id


def _validate_stored_intake(run: TeamworkRun, action: TeamworkAction, program, result: TeamworkObservation) -> None:
    if not run.feedback_policy or action.kind != "ddc_store" or action.intelligence is not None:
        return
    if _run_intake_broken(action, program, result.intelligence):
        raise ValueError("RUN_INTAKE_REQUIRED: read the actual native retained context before learning")


def _validate_ddc_readback(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind not in ("ddc_store", "ddc_complete"):
        return
    program = result.ddc_program
    if _ddc_readback_broken(run, action, result, program):
        raise ValueError("DDC_READBACK_REQUIRED: retain the current task's sealed procedure")
    if result.findings:
        raise ValueError("DDC_READBACK_OPEN: storage cannot discharge task findings")
    _validate_stored_intake(run, action, program, result)


def _stopped_artifact_changed(action: TeamworkAction, result: TeamworkObservation) -> bool:
    for path, digest in action.artifacts.items():
        if result.artifacts.get(path, digest) != digest:
            return True
    return False


def _stopped_candidate_changed(action: TeamworkAction, result: TeamworkObservation) -> bool:
    if not action.stopped_status:
        return False
    return _stopped_artifact_changed(action, result)


def _learn_consumption_broken(action: TeamworkAction, result: TeamworkObservation) -> bool:
    if result.metadata.get("consumed_ddc_root") != action.ddc_program.binding.semantic_ddc_root:
        return True
    return result.metadata.get("consumed_procedure_sha256") != action.ddc_program.procedure_sha256


def _validate_learn_consumption(action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind != "learn":
        return
    if action.ddc_program is None:
        raise ValueError("DDC_READBACK_REQUIRED: learning must consume the stored procedure")
    if _learn_consumption_broken(action, result):
        raise ValueError("DDC_CONSUMPTION_REQUIRED: bind the actual checked Scar Chronicler reply")
    if _stopped_candidate_changed(action, result):
        raise ValueError("STOPPED_CANDIDATE_CHANGED: preserve original stopped artifacts")


def _validate_host_intelligence_intake(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if run.feedback_policy and result.intelligence and action.kind not in ("ddc_store", "digest"):
        raise ValueError("INTELLIGENCE_HOST_INTAKE_REQUIRED: only native intake or digestion may bind a source")


def _validate_current_contracts(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if run.schema_version not in CURRENT_TEAMWORK_VERSIONS or result.blocked:
        return
    _validate_host_intelligence_intake(run, action, result)
    _validate_ddc_readback(run, action, result)
    _validate_learn_consumption(action, result)


def _learning_paths_apply(action: TeamworkAction, result: TeamworkObservation) -> bool:
    return action.kind == "learn" and bool(result.metadata.get("changed_paths"))


def _artifacts_rebound(action: TeamworkAction, result: TeamworkObservation) -> bool:
    for path, digest in action.artifacts.items():
        if result.artifacts.get(path) != digest:
            return True
    return False


def _require_retained_keys(action: TeamworkAction, result: TeamworkObservation) -> None:
    if not action.artifacts.keys() <= result.artifacts.keys():
        raise ValueError("APPLICATION_REQUIRED: retain all original and descendant artifacts")


def _validate_digest_bindings(action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind == "digest" and result.findings:
        if _artifacts_rebound(action, result):
            raise ValueError("ARTIFACT_REBINDING: digestion must retain original output bindings")
        return
    if result.artifacts and result.artifacts != action.artifacts:
        raise ValueError("ARTIFACT_REBINDING: only application may change current output bindings")


def _validate_panel_artifacts(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if run.panel_plan is None or result.blocked:
        return
    if action.kind in ("build", "repair") or _learning_paths_apply(action, result):
        _require_retained_keys(action, result)
        return
    _validate_digest_bindings(action, result)


def _acceptance_identity_unbound(action: TeamworkAction, check) -> bool:
    if check.initial_task_id != action.initial_task_id:
        return True
    if check.source_id != action.check_source_id:
        return True
    if check.checker_id != action.checker_id:
        return True
    return check.command != action.check_command


def _acceptance_check_unbound(action: TeamworkAction, check) -> bool:
    if check is None:
        return True
    if _acceptance_identity_unbound(action, check):
        return True
    if check.artifacts != action.artifacts:
        return True
    return not check.artifacts


def _validate_acceptance_recheck(run: TeamworkRun, action: TeamworkAction, result: TeamworkObservation) -> None:
    if not run.acceptance_check or action.kind != "recheck" or result.blocked:
        return
    check = result.check
    if _acceptance_check_unbound(action, check):
        raise ValueError("CHECK_BINDING_MISMATCH: bind independent acceptance to the current candidate")
    if check.exit_status != 0 and not result.findings:
        raise ValueError("FAILED_CHECK: a failed independent judge cannot close work")


def _path_text_changed(paths) -> bool:
    for path in paths:
        if not isinstance(path, str) or not path.strip():
            return False
    return True


def _paths_changed(paths) -> bool:
    if not isinstance(paths, (list, tuple)) or not paths:
        return False
    return _path_text_changed(paths)


def _reason_present(reason) -> bool:
    return isinstance(reason, str) and bool(reason.strip())


def _require_learning_outcome(result: TeamworkObservation) -> None:
    paths = result.metadata.get("changed_paths", [])
    reason = result.metadata.get("no_change_reason", "")
    if not _paths_changed(paths) and not _reason_present(reason):
        raise ValueError("LEARNING_OUTCOME_REQUIRED: report changed paths or justified no-change")


def _stamp_learning_stage(result: TeamworkObservation, stage: str) -> TeamworkObservation:
    return result.model_copy(update={"metadata": {**result.metadata, "learning_stage": stage}})


def _validate_learning_outcome(run: TeamworkRun, action: TeamworkAction,
                               result: TeamworkObservation) -> TeamworkObservation:
    if action.kind != "learn" or result.blocked:
        return result
    if run.executor != "ide":
        if result.metadata.get("proposed_only") is not True:
            raise ValueError("PROPOSED_ONLY_REQUIRED: a text provider cannot install learning")
    elif not result.findings:
        _require_learning_outcome(result)
    return _stamp_learning_stage(result, "learn")


def _stamp_learning_review(action: TeamworkAction, result: TeamworkObservation) -> TeamworkObservation:
    if action.phase != "learning_review":
        return result
    return _stamp_learning_stage(result, "review")


def _bound_learning_applies(action: TeamworkAction, result: TeamworkObservation) -> bool:
    if action.kind != "learn":
        return False
    if result.metadata.get("changed_paths"):
        return True
    return bool(result.artifacts)


def _missing_learning_output(result: TeamworkObservation) -> bool:
    for path in result.metadata.get("changed_paths", []):
        if path not in result.artifacts:
            return True
    return False


def _require_bound_application(action: TeamworkAction, result: TeamworkObservation, applies: bool) -> None:
    if action.kind not in ("build", "repair") and not applies:
        return
    if not result.artifacts or not action.artifacts.keys() <= result.artifacts.keys():
        raise ValueError("APPLICATION_REQUIRED: retain all original and descendant artifacts")
    if applies and _missing_learning_output(result):
        raise ValueError("APPLICATION_REQUIRED: bind every learning output for recheck")


def _bound_source_id(action: TeamworkAction) -> str:
    if action.check_source_id:
        return action.check_source_id
    return action.intelligence.source_id


def _bound_recheck_identity(action: TeamworkAction, check) -> bool:
    if check.initial_task_id != action.initial_task_id:
        return True
    if check.source_id != _bound_source_id(action):
        return True
    if check.checker_id != action.checker_id:
        return True
    return check.command != action.check_command


def _bound_recheck_unbound(action: TeamworkAction, check) -> bool:
    if check is None:
        return True
    if _bound_recheck_identity(action, check):
        return True
    if check.artifacts != action.artifacts:
        return True
    return not check.artifacts


def _validate_bound_recheck(action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind != "recheck":
        return
    check = result.check
    if _bound_recheck_unbound(action, check):
        raise ValueError("CHECK_BINDING_MISMATCH: recheck must bind the original task and current outputs")
    if check.exit_status != 0 and not result.findings:
        raise ValueError("FAILED_CHECK: nonzero outcome cannot close the task")


def _digestion_ancestry_broken(action: TeamworkAction, source) -> bool:
    if source is None:
        return True
    if source.initial_task_id != action.initial_task_id:
        return True
    return source.parent_source_id != action.intelligence.source_id


def _validate_bound_digest(action: TeamworkAction, result: TeamworkObservation) -> None:
    if action.kind != "digest":
        return
    source = result.intelligence
    if _digestion_ancestry_broken(action, source):
        raise ValueError("DIGESTION_ANCESTRY_MISMATCH: retain initial task and parent source")
    if source.coverage_gaps:
        raise ValueError("DIGESTION_COVERAGE_OPEN: unreadable/unsupported input cannot close")
    if result.findings != source.findings:
        raise ValueError("DIGESTION_FINDINGS_MISMATCH: preserve the actual extracted findings")


def _validate_bound_intelligence(action: TeamworkAction, result: TeamworkObservation) -> None:
    if not action.intelligence or result.blocked:
        return
    applies = _bound_learning_applies(action, result)
    _require_bound_application(action, result, applies)
    _validate_bound_recheck(action, result)
    _validate_bound_digest(action, result)


def _validate_action_result(run: TeamworkRun, action: TeamworkAction,
                            result: TeamworkObservation) -> TeamworkObservation:
    """Apply the same retained source/check/learning contracts during replay."""
    _validate_review_digest(action, result)
    _validate_optional_route_context(action, result)
    _validate_native_gate_action(run, action, result)
    _validate_current_contracts(run, action, result)
    _validate_panel_artifacts(run, action, result)
    _validate_acceptance_recheck(run, action, result)
    result = _validate_learning_outcome(run, action, result)
    result = _stamp_learning_review(action, result)
    _validate_bound_intelligence(action, result)
    return result


def ddc_task_premises(action: TeamworkAction) -> dict:
    """Exact task, checker and candidate scope of the existing DDC program."""
    premises = {"initial_task_id": action.initial_task_id,
        "workflow_version": action.workflow_version, "plan_sha256": action.plan_sha256,
        "checker_id": action.checker_id, "check_command": list(action.check_command),
        "check_source_id": action.check_source_id, "check_source_paths": action.check_source_paths,
        "artifacts": dict(action.artifacts),
        "source_reads": [source.model_dump(mode="json") for source in action.source_reads],
        **({"native_gate_check": action.native_gate_check.model_dump(mode="json"),
            "native_gate_receipts": [{key: receipt[key] for key in ("path", "sha256", "receipt_sha256")}
                                     for receipt in action.native_gate_batches]}
           if action.workflow_version == "core.adversary.teamwork.v4" else {})}
    if action.feedback_policy:
        premises["feedback_policy"] = action.feedback_policy
    if action.brief and action.brief.task_premises is not None:
        premises["task_premises"] = action.brief.task_premises
    return premises


def _reject_legacy_resume(run: TeamworkRun) -> None:
    if run.schema_version not in CURRENT_TEAMWORK_VERSIONS:
        raise ValueError("LEGACY_WORKFLOW_READ_ONLY: start a new governed run and retain this history")
    if run.feedback_policy is None:
        raise ValueError("LEGACY_FEEDBACK_READ_ONLY: retain historical feedback semantics")


def _reject_open_intake(run: TeamworkRun) -> None:
    if run.intelligence and run.intelligence.coverage_gaps:
        raise ValueError("INTAKE_COVERAGE_OPEN: repaired source requires explicit new intake")


def _observation_coverage_open(result: TeamworkObservation) -> bool:
    return bool(result.intelligence and result.intelligence.coverage_gaps)


def _reject_open_sources(run: TeamworkRun) -> None:
    for result in run.observations:
        if _observation_coverage_open(result):
            raise ValueError("SOURCE_COVERAGE_OPEN: preserve the unreadable descendant; resumption cannot erase its gaps")


def _reject_unstopped_resume(run: TeamworkRun) -> None:
    if run.work_status not in ("blocked", "partial"):
        raise ValueError("RUN_NOT_STOPPED: continue the pending action or retain completed work")
    if next_action(run) is not None:
        raise ValueError("FINISH_REQUIRED: retain DDC and Scar Chronicler before resuming stopped work")


def _require_continuation_allowance(continued: TeamworkRun) -> None:
    continued_trace = _trace_v3(continued)
    if continued_trace[8]["stopped_status"]:
        raise ValueError("CONTINUATION_ALLOWANCE_REQUIRED: " + continued_trace[4])
    if next_action(continued) is None:
        raise ValueError("CONTINUATION_ALLOWANCE_REQUIRED: grant only the explicit additional work needed")


def resume_teamwork(
    run: TeamworkRun, *, parent_state_path: str, parent_state_sha256: str, reason: str,
    additional_repairs: int = 0, additional_actions: int = 0,
    acceptance_successor: HostAcceptanceRequirement | None = None,
) -> TeamworkRun:
    """Retry stopped work with retained history and only explicit additive grants.

    Host callers must preserve/read back the parent file. This pure transition
    neither finds a provider nor recreates a financial budget/gateway.
    """
    _reject_legacy_resume(run)
    _reject_open_intake(run)
    _reject_open_sources(run)
    _reject_unstopped_resume(run)
    point = TeamworkContinuation(after_observations=len(run.observations), reason=reason.strip(),
        parent_state_path=parent_state_path, parent_state_sha256=parent_state_sha256,
        additional_repairs=additional_repairs, additional_actions=additional_actions,
        acceptance_successor=acceptance_successor)
    continued = run.model_copy(update={"continuations": (*run.continuations, point)})
    effective_acceptance(continued)
    _require_continuation_allowance(continued)
    return continued


def _automatic_density_checkpoint(checkpoint, run: TeamworkRun):
    return checkpoint is None and run.brief and run.brief.density_dimension is not None


def _density_checkpoint(run: TeamworkRun):
    from ..infrastructure.teamwork_state import default_state_path, save_teamwork_state

    state_path = default_state_path(run)

    def checkpoint(updated):
        report = save_teamwork_state(state_path, updated)
        if report["status"] == "REPORTING_FAILED":
            import warnings
            warnings.warn("Adversary reporting failed; state retained: " + report["detail"], RuntimeWarning)

    return checkpoint


def _drive_executor_gate(run: TeamworkRun, executor) -> None:
    if run.schema_version not in CURRENT_TEAMWORK_VERSIONS:
        raise ValueError("LEGACY_WORKFLOW_READ_ONLY: historical states cannot dispatch workers")
    if run.feedback_policy is None:
        raise ValueError("LEGACY_FEEDBACK_READ_ONLY: historical states cannot dispatch workers")
    if getattr(executor, "execution_mode", "ide") != run.executor:
        raise ValueError("EXECUTOR_MISMATCH: bound executor differs from the selected run mode")


def _executor_failure(run: TeamworkRun, action: TeamworkAction, exc: Exception) -> TeamworkObservation:
    return TeamworkObservation(
        action_id=action.action_id, worker=f"bound {run.executor} executor", blocked=True,
        summary=f"EXECUTOR_FAILED: {type(exc).__name__}",
        metadata={"role_id": action.role_id, "failure_code": "EXECUTOR_FAILED",
                  "error_message": str(exc)[:500]},
    )


def _drive_one(run: TeamworkRun, executor, action: TeamworkAction, checkpoint) -> TeamworkRun:
    try:
        result = executor(action)
    except Exception as exc:
        result = _executor_failure(run, action, exc)
    run = observe(run, result)
    if checkpoint is not None:
        checkpoint(run)
    return run


def drive_teamwork(
    run: TeamworkRun,
    executor: Callable[[TeamworkAction], TeamworkObservation] | None = None,
    *, checkpoint: Callable[[TeamworkRun], None] | None = None,
) -> TeamworkRun:
    """Run a bound callback, or leave a genuinely unbound IDE action pending.

    The host selects the executor once. An unmarked callable is the IDE binding.
    It cannot satisfy an openrouter run. No credentials, remote fallback or imports
    from strings are used to acquire an IDE conversation.
    """
    automatic_checkpoint = _automatic_density_checkpoint(checkpoint, run)
    if automatic_checkpoint:
        checkpoint = _density_checkpoint(run)
    if executor is None:
        if automatic_checkpoint:
            checkpoint(run)
        return run
    _drive_executor_gate(run, executor)
    if automatic_checkpoint:
        checkpoint(run)
    while (action := next_action(run)) is not None:
        run = _drive_one(run, executor, action, checkpoint)
    return run


def ref_parallel_blind_cohort_dispatch(
    pre_cohort_state: dict[str, Any],
    cohort_roles: list[str],
    reviewer_functions: dict[str, Callable[[dict[str, Any]], list[str]]],
    closed_roster: tuple[str, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute parallel blind cohort dispatch against reference dictionary state.

    Invariants:
    1. Every reviewer in the cohort binds strictly to pre_cohort_state (prior peer findings withheld).
    2. Observations are recorded in deterministic closed roster order, not completion order.
    """
    raw_results: dict[str, list[str]] = {}
    for role in cohort_roles:
        fn = reviewer_functions.get(role, lambda state: [])
        findings = fn(dict(pre_cohort_state))
        raw_results[role] = findings

    ordered_observations: list[dict[str, Any]] = []
    for role in closed_roster:
        if role in raw_results:
            state_bytes = json.dumps(pre_cohort_state, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            ordered_observations.append({
                "role_id": role,
                "view": "blind",
                "findings": raw_results[role],
                "bound_state_digest": hashlib.sha256(state_bytes).hexdigest(),
            })

    combined_findings = [f for obs in ordered_observations for f in obs["findings"]]
    post_cohort_state = {
        **pre_cohort_state,
        "cohort_findings": combined_findings,
        "cohort_clean": len(combined_findings) == 0,
    }
    return post_cohort_state, ordered_observations


def _cohort_schedule(run: TeamworkRun):
    if run.panel_plan is None or run.panel_plan.schedule is None:
        return None
    return run.panel_plan.schedule


def _cohort_first_action(run: TeamworkRun):
    action = next_action(run)
    if action is None or action.kind != "review":
        return None
    return action


def _cohort_producer_match(obs: TeamworkObservation, candidate: str) -> bool:
    if obs.content != candidate:
        return False
    if obs.content:
        return True
    return obs.metadata.get("role_id") in {"bare_metal_anchor", "primal_dual"}


def _cohort_producer(run: TeamworkRun, candidate: str):
    for obs in reversed(run.observations):
        if _cohort_producer_match(obs, candidate):
            return obs
    return None


def _cohort_trace_producer(run: TeamworkRun):
    if run.schema_version in CURRENT_TEAMWORK_VERSIONS:
        trace = _trace_v3(run)
    else:
        trace = _trace_panel(run)
    return trace[1]


def _cohort_step_closed(step, schedule) -> bool:
    if step.phase != "review":
        return True
    return schedule.policy(step.role_id).view != "blind"


def _collect_blind_actions(run: TeamworkRun, schedule, first_action, producer) -> list:
    actions = []
    collecting = False
    for step in run.panel_plan.steps:
        if step.role_id == first_action.role_id:
            collecting = True
        if collecting and _cohort_step_closed(step, schedule):
            break
        if collecting:
            actions.append(_make_action(run, "review", producer, (),
                (step.role_id, step.phase, step.communication)))
    return actions


def _run_cohort(futures, actions, executor, max_workers) -> dict:
    results = {}
    with futures.ThreadPoolExecutor(max_workers=max_workers or len(actions)) as pool:
        future_map = {}
        for act in actions:
            future_map[pool.submit(executor, act)] = act.role_id
        for future in futures.as_completed(future_map):
            role_id = future_map[future]
            results[role_id] = future.result()
    return results


def _merge_cohort_seat(run: TeamworkRun, results: dict, role_id: str):
    if role_id not in results:
        return run, False
    pending = next_action(run)
    if pending is None or pending.kind != "review":
        return run, True
    if pending.role_id == role_id:
        run = observe(run, results[role_id])
    return run, False


def _merge_cohort(run: TeamworkRun, results: dict) -> TeamworkRun:
    for role_id in PANEL_ROLE_ORDER:
        run, stop = _merge_cohort_seat(run, results, role_id)
        if stop:
            break
    return run


def parallel_blind_cohort_dispatch(
    run: TeamworkRun,
    executor: Callable[[TeamworkAction], TeamworkObservation],
    *,
    max_workers: int | None = None,
) -> TeamworkRun:
    """Dispatch a cohort of blind reviewers concurrently and observe in deterministic roster order.

    Invariants:
    1. Every reviewer binds strictly to the pre-cohort state.
    2. Reviewers execute concurrently without observing peer findings.
    3. Observations are merged into the run in declared roster sequence (PANEL_ROLE_ORDER).
    4. Remaining cohort seats skipped by schedule (e.g. quorum reached) are bypassed safely.
    """
    import concurrent.futures

    schedule = _cohort_schedule(run)
    if schedule is None:
        return run
    first_action = _cohort_first_action(run)
    if first_action is None:
        return run
    if schedule.policy(first_action.role_id).view != "blind":
        return run
    producer = _cohort_producer(run, first_action.candidate)
    if producer is None:
        producer = _cohort_trace_producer(run)
    actions = _collect_blind_actions(run, schedule, first_action, producer)
    if not actions:
        return run
    results = _run_cohort(concurrent.futures, actions, executor, max_workers)
    return _merge_cohort(run, results)


def apply_preset_to_run(run: TeamworkRun, preset_name: str) -> TeamworkRun:
    """Attach preset to panel plan and validate tier mappings."""
    if run.panel_plan is None:
        return run
    load_panel_preset(preset_name)
    updated_plan = run.panel_plan.model_copy(update={"preset": preset_name})
    return run.model_copy(update={"panel_plan": updated_plan})


def pack_run_bundle(
    run: TeamworkRun,
    preset_name: str,
    prompt_family_versions: dict[str, str],
    checker_ids: list[str],
    turns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from adversary.use_cases.yardstick import compute_bundle_digest

    b_digest = compute_bundle_digest(preset_name, prompt_family_versions, checker_ids)
    return {
        "schema_version": "core.adversary.run-bundle.v1",
        "bundle_digest": b_digest,
        "preset": preset_name,
        "prompt_family_versions": prompt_family_versions,
        "checker_ids": sorted(checker_ids),
        "run_id": run.run_id,
        "objective": run.objective,
        "panel_coverage": run.panel_coverage,
        "turns": turns or [],
    }


def verify_run_bundle(bundle_data: dict[str, Any]) -> bool:
    from adversary.use_cases.yardstick import compute_bundle_digest

    expected = compute_bundle_digest(
        bundle_data["preset"],
        bundle_data["prompt_family_versions"],
        bundle_data["checker_ids"],
    )
    return bundle_data.get("bundle_digest") == expected


def replay_run_bundle(
    bundle_data: dict[str, Any],
    *,
    initial_run: TeamworkRun | None = None,
) -> TeamworkRun:
    """Replay recorded turns deterministically offline with zero external provider calls."""
    if not verify_run_bundle(bundle_data):
        raise ValueError("BUNDLE_DIGEST_MISMATCH: run bundle failed integrity verification")

    run = initial_run
    if run is None:
        raise ValueError("INITIAL_RUN_REQUIRED: provide initial run for replay")

    turns = bundle_data.get("turns", [])
    for turn in turns:
        action = next_action(run)
        if action is None:
            raise ValueError("RUN_TERMINATED_EARLY: run terminated before all bundle turns replayed")
        if action.action_id != turn["action_id"]:
            raise ValueError(f"REPLAY_ACTION_MISMATCH: expected {turn['action_id']}, got {action.action_id}")
        obs_data = turn["observation"]
        obs = TeamworkObservation.model_validate(obs_data)
        run = observe(run, obs)
    return run

