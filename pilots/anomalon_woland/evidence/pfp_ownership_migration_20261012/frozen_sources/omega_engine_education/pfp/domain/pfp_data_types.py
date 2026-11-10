"""Proposal Fidelity Protocol (PFP) - Canonical Data Types (Pydantic V2).

AuthorityEffect: None.

Comprehensive fully-typed data model catalog governing:
1. Pilot Specifications & Ingress Coordinates (spec.yaml)
2. Model Responses, Sanitization Reports & Evaluation Receipts (response.yaml)
3. Universal Prompt Templates, P* Trees, Lineage & Guidance Defense Slots (prompt_template.yaml, p_star.yaml)
4. System Prompt Policy Manifest, Typing Rules & Claim Hygiene
5. Seed Prompts & Oracle Ground Truth Expectations (seed.yaml)
6. Cycle Balance Quartet: Carrier, Cell Bounds, Matrices, Problem, Candidate, Verifier, Receipt
7. Fixtures & Long-Horizon Task Packet Envelopes (fable_long_horizon_task_packet_v2.yaml)
8. Modes Catalog & Specifications: 20 Play Modes & 5 Clusters (modes/)
9. Normal Forms Domain Index & Extended Form Contracts (normal_forms/)
10. Prompt Rewriting & Wire Topologies: mss-boundary-v1, Partitions, Symbol Codebook (rewriting/)
11. Schema Registry & Envelope Envelopes: Draft 2020-12 & Grammar Schemas (schemas/)
12. Stages & Execution Controllers: 8 Numbered Pipeline Stages (stages/)
13. Type Register Metrics & Invariants: Census & World Definitions (type_register/)
"""

from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

# =============================================================================
# BASE MODEL & SERIALIZATION MIXIN
# =============================================================================

class PfpBaseModel(BaseModel):
    """Base Pydantic model with strict defaults and lossless YAML helpers."""

    model_config = ConfigDict(
        extra="ignore",
        strict=False,
        validate_assignment=True,
    )

    @classmethod
    def from_yaml(cls, path_or_str: str | Path):
        p = Path(path_or_str)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8")
        else:
            content = str(path_or_str)
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError(f"YAML payload for {cls.__name__} must be a mapping, got {type(data).__name__}")
        return cls.model_validate(data)

    def to_yaml(self) -> str:
        data = self.model_dump(mode="json", exclude_none=True)
        return yaml.dump(data, sort_keys=False, default_flow_style=False)


# =============================================================================
# PRIMITIVES & ENUMS
# =============================================================================

class PfpAuthorityEffect(str, Enum):
    NONE = "None"


AuthorityEffect = PfpAuthorityEffect


class TaskFamily(str, Enum):
    LINEAR_ALGEBRA = "linear_algebra"
    GRAPH_FACTS = "graph_facts"
    GRAPH_REPAIR = "graph_repair"
    REFUSAL = "refusal"
    COCHAIN_DEFECT = "cochain_defect"
    MAGMA_ASSOCIATIVITY = "magma_associativity"


class ExecutionMode(str, Enum):
    OFFLINE_FIXTURE = "offline_fixture"
    LIVE_MANUAL_DISPATCH = "live_manual_dispatch"
    LIVE_GATEWAY_DISPATCH = "live_gateway_dispatch"


class TrialStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUSED = "REFUSED"


class EvaluationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    FALSE_CERTAINTY = "FALSE_CERTAINTY"
    MALFORMED = "MALFORMED"
    NOT_RUN = "NOT_RUN"
    REFUSED = "REFUSED"


class ConstraintType(str, Enum):
    PROJECT_OUT = "ProjectOut"
    RESTRAIN = "Restrain"
    ENFORCE = "Enforce"
    REJECT_MALFORMED_OR_FAKE_REFUSALS = "RejectMalformedOrFakeRefusals"


class Operatorizability(str, Enum):
    REPAIRABLE = "repairable"
    FATAL = "fatal"


class RuntimeAction(str, Enum):
    REPAIR = "repair"
    ABORT = "abort"
    REFUSE = "refuse"


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# =============================================================================
# 1. PILOT SPECIFICATION (spec.yaml)
# =============================================================================

class PilotCoordinates(PfpBaseModel):
    task_family: TaskFamily
    difficulty_rung: int = Field(ge=1, le=5)
    representation_rewrite: str
    rewrite_count: int = Field(ge=0)
    legend_present: bool
    mode: str
    stage_count: int = Field(ge=1)
    pass_count: int = Field(ge=1)
    single_shot: bool
    antibody_active: bool
    antibody_ids: list[str] = Field(default_factory=list)
    model_class: str
    model_id: str
    temperature: float = Field(ge=0.0, le=2.0)
    target_spend_usd: float = Field(ge=0.0)


class PilotIngress(PfpBaseModel):
    task_mode_fidelity: str
    variable_identifier_permutation: str
    floating_point_approximation_risk: str
    arm_template: str
    missing_premise: str
    cohomology_defect_class: str
    magma_associativity_type: str


class PilotHostGate(PfpBaseModel):
    checker_id: str
    response_schema: str
    residual_logging: bool
    structure_delta_metric: str
    expected_outcome: str


class PilotSpec(PfpBaseModel):
    schema_: Literal["pfp.pilot-spec.v1"] = Field(default="pfp.pilot-spec.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str
    prompt_id: str
    parent_prompt_id: str | None = None
    generation_id: int = 0
    phase: str
    split: str
    coordinates: PilotCoordinates
    ingress: PilotIngress
    host_gate: PilotHostGate

    @property
    def schema_version(self) -> str:
        return self.schema_


# =============================================================================
# 2. PILOT RESPONSE & EVALUATION (response.yaml)
# =============================================================================

class ResponseSummaryPayload(PfpBaseModel):
    narrowest_defensible_thesis: str
    evidence_scope: str
    next_concrete_test: str


class ProcessIntegrityPayload(PfpBaseModel):
    seed_allows_theory_refutation: bool
    detected_prompt_biases: list[str] = Field(default_factory=list)
    should_continue: bool


class PromptResponsePayload(PfpBaseModel):
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    summary: ResponseSummaryPayload
    process_integrity: ProcessIntegrityPayload
    sections: list[dict[str, Any]] = Field(default_factory=list)


class SanitizationReport(PfpBaseModel):
    fence_stripped: bool
    is_valid_json: bool
    structure_leakage_debt_chars: int = Field(ge=0)


class EvaluationReport(PfpBaseModel):
    checker_id: str
    expected: Any
    received: Any
    status: EvaluationStatus


class ExecutionReceipt(PfpBaseModel):
    provider: str | None = None
    dispatch_kind: str | None = None
    cost_microusd: int = Field(ge=0, default=0)
    evidence: str
    timestamp_utc: str | None = None
    provider_calls: int | None = None


class PilotResponse(PfpBaseModel):
    schema_: Literal["pfp.pilot-response.v1"] = Field(default="pfp.pilot-response.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str
    request_id: str
    execution_mode: ExecutionMode
    model_id: str | None = None
    trial_status: TrialStatus
    raw_reply: str | None = None
    parsed_response: PromptResponsePayload | None = None
    parsed_json: dict[str, Any] | None = None
    extracted_answer: Any | None = None
    sanitization: SanitizationReport
    evaluation: EvaluationReport
    receipt: ExecutionReceipt

    @property
    def schema_version(self) -> str:
        return self.schema_


# =============================================================================
# 3. PROMPT TEMPLATE, P* TREE, LINEAGE & GUIDANCE
# =============================================================================

class PromptLineageSlot(PfpBaseModel):
    """First-class provenance and mutation ancestry slots for prompt trees."""
    prompt_id: str
    generation_id: Any
    family_id: str
    parent_id: str | None = None
    mutation_kind: str | None = None
    mutation_notes: str | None = None


class RuleSlot(PfpBaseModel):
    """Sovereign governance rule binding."""
    rule_id: str
    name: str | None = None
    statement: str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class AntibodySlot(PfpBaseModel):
    """Active immune antibody record adhering to .agents/antibodies schema."""
    antibody_id: str
    failure_class: str
    target_pattern: str
    constraint_type: str = "Restrain"
    operatorizability: str = "repairable"
    action: str = "repair"
    severity: str = "P2"
    description: str
    negative_fixture: str | None = None
    positive_fixture: str | None = None
    times_seen: int | None = 0
    evidence_sha256: str | None = None
    pharmacy_status: str | None = "candidate"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class AntipatternSlot(PfpBaseModel):
    """Known anti-pattern signature to be projected out."""
    antipattern_id: str
    name: str
    description: str
    target_pattern: str | None = None


class HelpfulPatternSlot(PfpBaseModel):
    """Positive behavioral pattern or recommended structural idiom."""
    pattern_id: str
    name: str
    description: str
    enforcement: str | None = None


class GuidanceSlot(PfpBaseModel):
    """Active defense and behavioral guidance slots."""
    rules: list[RuleSlot] = Field(default_factory=list)
    antibodies: list[Any] = Field(default_factory=list)
    antipatterns: list[AntipatternSlot] = Field(default_factory=list)
    helpful_patterns: list[HelpfulPatternSlot] = Field(default_factory=list)


class PromptTemplate(PfpBaseModel):
    """Universal prompt template carrying lineage, guidance, and system manifest."""
    lineage: PromptLineageSlot
    guidance: GuidanceSlot
    system_prompt: str
    user_prompt: str
    response_schema: str

    def parse_system_manifest(self) -> SystemPromptManifest:
        clean = self.system_prompt.strip()
        if clean.startswith("```yaml"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("\n", 1)[0]
        data = yaml.safe_load(clean)
        return SystemPromptManifest.model_validate(data)

    def parse_response_schema(self) -> dict[str, Any]:
        clean = self.response_schema.strip()
        if clean.startswith("```yaml"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("\n", 1)[0]
        data = yaml.safe_load(clean)
        return data if isinstance(data, dict) else {}


class PStarPrompt(PfpBaseModel):
    """Concrete P* instance with ground truth prompt stimulus injected."""
    lineage: PromptLineageSlot
    guidance: GuidanceSlot
    system_prompt: str
    user_prompt: str
    response_schema: str


# =============================================================================
# 4. SYSTEM PROMPT MANIFEST (Internal System Prompt Structure)
# =============================================================================

class PfpSemanticPolicyManifest(PfpBaseModel):
    policy_id: Literal["SPK-001"] = "SPK-001"
    required_stamp: Literal["derived_under_policy: SPK-001"] = "derived_under_policy: SPK-001"


class PfpMss0GrammarConstraint(PfpBaseModel):
    system_name: Literal["SYM SYS"] = "SYM SYS"
    atomic_glyph_count: Literal[38] = 38
    node_labels: Literal["a..z"] = "a..z"
    numeric_labels: Literal["0..9"] = "0..9"
    delimiters: list[str]
    pair_note: str
    numeric_license_rule: str
    derived_patterns_note: str


class PfpOpSemantics(PfpBaseModel):
    default_layer: int = 1
    default_meaning: str = "syntactic_binary_operator"
    forbidden_unlicensed_interpretations: list[str] = Field(default_factory=list)
    license_required_for: list[str] = Field(default_factory=list)


class PfpMss0Level(PfpBaseModel):
    level: int
    code: str
    name: str
    meaning: str


class PfpMss0TypingRules(PfpBaseModel):
    preamble: str
    levels: list[PfpMss0Level]


class PfpEvaluatorBinding(PfpBaseModel):
    evaluator: str
    promotes: str
    does_not_promote: str | None = None


class PfpEvaluatorScopeRule(PfpBaseModel):
    principle: str
    bindings: list[PfpEvaluatorBinding]


class PfpEvidenceLevel(PfpBaseModel):
    code: str
    meaning: str


class ReplacementDefault(PfpBaseModel):
    from_: str = Field(alias="from")
    to: str


class PfpClaimHygiene(PfpBaseModel):
    discipline: str | None = None
    forbidden_words: list[str] = Field(default_factory=list)
    forbidden_word_exceptions: str | None = None
    replacement_defaults: list[ReplacementDefault] = Field(default_factory=list)
    default_posture: str | None = None
    what_it_supports: str | None = None
    what_it_does_not_support: str | None = None
    next_test_needed: str | None = None


class RoleManifest(PfpBaseModel):
    persona: str
    goal: str | None = None


class SystemPromptManifest(PfpBaseModel):
    semantic_policy_manifest: PfpSemanticPolicyManifest
    mss0_grammar_constraint: PfpMss0GrammarConstraint
    op_semantics: PfpOpSemantics
    import_boundary: str
    mss0_typing_rules: PfpMss0TypingRules
    evaluator_scope_rule: PfpEvaluatorScopeRule
    evidence_levels: list[PfpEvidenceLevel]
    claim_hygiene: PfpClaimHygiene
    role: RoleManifest
    antibody_injections: list[Any] = Field(default_factory=list)


# =============================================================================
# 5. SEED PROMPT (seed.yaml)
# =============================================================================

class ExpectedOutcome(PfpBaseModel):
    answer: Any
    status: str = "ACCEPTED"


class SeedPrompt(PfpBaseModel):
    schema_: Literal["pfp.seed-prompt.v1"] = Field(default="pfp.seed-prompt.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str
    task_family: str
    difficulty_rung: int = Field(ge=1, le=5)
    request_id: str
    seed_prompt: str
    expected_outcome: ExpectedOutcome

    @property
    def schema_version(self) -> str:
        return self.schema_


# =============================================================================
# 6. CYCLE BALANCE QUARTET (cycle_balance/)
# =============================================================================

class PfpArithmeticDomain(str, Enum):
    EXACT_INTEGER = "EXACT_INTEGER"


class PfpClaimedMove(str, Enum):
    ATTACH_2CELL = "ATTACH_2CELL"


class PfpVerificationRule(str, Enum):
    STATIC_CELL_BOUNDS_CHECK = "STATIC_CELL_BOUNDS_CHECK"
    CHAIN_COMPLEX_NILPOTENCY_CHECK = "CHAIN_COMPLEX_NILPOTENCY_CHECK"
    INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE = "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE"


class PfpVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"


class PfpStaticCellBounds(PfpBaseModel):
    max_vertices: int = Field(ge=0)
    max_edges: int = Field(ge=0)
    max_faces: int = Field(ge=0)


class PfpEdge(PfpBaseModel):
    id: str = Field(min_length=1)
    source: int
    target: int


class PfpFace(PfpBaseModel):
    id: str = Field(min_length=1)
    boundary_edges: list[str] = Field(default_factory=list)


class PfpCarrier(PfpBaseModel):
    name: str = Field(min_length=1)
    vertices: list[int] = Field(default_factory=list)
    edges: list[PfpEdge] = Field(default_factory=list)
    faces: list[PfpFace] = Field(default_factory=list)
    static_cell_bounds: PfpStaticCellBounds

    @model_validator(mode="after")
    def _validate_carrier(self) -> PfpCarrier:
        b = self.static_cell_bounds
        if len(self.vertices) > b.max_vertices:
            raise ValueError("vertex count exceeds static_cell_bounds.max_vertices")
        if len(self.edges) > b.max_edges:
            raise ValueError("edge count exceeds static_cell_bounds.max_edges")
        if len(self.faces) > b.max_faces:
            raise ValueError("face count exceeds static_cell_bounds.max_faces")
        return self


class PfpBoundaryMatrices(PfpBaseModel):
    d1: list[list[int]] = Field(default_factory=list)
    d2: list[list[int]] = Field(default_factory=list)


class PfpActiveObstruction(PfpBaseModel):
    cycle_z: list[int] = Field(default_factory=list)
    cycle_edges: list[str] = Field(default_factory=list)
    d1_z: list[int] = Field(default_factory=list)
    homology_status: PfpVerificationStatus


class PfpCycleBalanceProblem(PfpBaseModel):
    schema_version: Literal["omega.symbol_game.cycle_balance.problem.v1"] = "omega.symbol_game.cycle_balance.problem.v1"
    problem_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    carrier: PfpCarrier
    boundary_matrices: PfpBoundaryMatrices
    active_obstruction: PfpActiveObstruction


class PfpCycleBalanceCandidate(PfpBaseModel):
    schema_version: Literal["omega.symbol_game.cycle_balance.candidate.v1"] = "omega.symbol_game.cycle_balance.candidate.v1"
    candidate_id: str = Field(min_length=1)
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    claimed_move: PfpClaimedMove = PfpClaimedMove.ATTACH_2CELL
    repair_face_name: str = Field(min_length=1)
    constituent_edges: list[str] = Field(default_factory=list)
    repair_boundary_column: list[int] = Field(default_factory=list)
    preserves_chain_law: bool
    claimed_integer_preimage_c: list[int] = Field(default_factory=list)
    claimed_h1_status: str = Field(min_length=1)


class PfpCycleBalanceVerifier(PfpBaseModel):
    schema_version: Literal["omega.symbol_game.cycle_balance.verifier.v1"] = "omega.symbol_game.cycle_balance.verifier.v1"
    verifier_id: str = Field(min_length=1)
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verification_rules: list[PfpVerificationRule] = Field(min_length=1)
    static_bounds: PfpStaticCellBounds


class PfpCycleBalanceReceipt(PfpBaseModel):
    schema_version: Literal["omega.symbol_game.cycle_balance.receipt.v1"] = "omega.symbol_game.cycle_balance.receipt.v1"
    receipt_id: str = Field(min_length=1)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verification_status: PfpVerificationStatus
    terminal_status: str | None = None
    residuals: Any | None = None
    exact_witness: Any | None = None
    claim_hygiene: PfpClaimHygiene
    receipt_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


def object_digest(obj: object) -> str:
    """sha256 of sorted-key compact UTF-8 JSON."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PfpCycleBalanceQuartet(PfpBaseModel):
    problem: PfpCycleBalanceProblem
    candidate: PfpCycleBalanceCandidate
    verifier: PfpCycleBalanceVerifier
    receipt: PfpCycleBalanceReceipt

    def check_digest_bindings(self, raw: dict[str, dict[str, Any]]) -> bool:
        pd = object_digest(raw["problem"])
        cd = object_digest(raw["candidate"])
        vd = object_digest(raw["verifier"])
        receipt_raw = dict(raw["receipt"])
        receipt_raw["receipt_digest"] = ""
        return (
            self.candidate.problem_digest == pd
            and self.verifier.problem_digest == pd
            and self.receipt.problem_digest == pd
            and self.receipt.candidate_digest == cd
            and self.receipt.verifier_digest == vd
            and self.receipt.receipt_digest == object_digest(receipt_raw)
        )


# =============================================================================
# 7. FIXTURES & TASK PACKET ENVELOPES (fixtures/ & schemas/)
# =============================================================================

class PfpAllowedTransform(str, Enum):
    EDIT_SCOPED_PATHS = "edit_scoped_paths"
    EMIT_CONTENT_ADDRESSED_ARTIFACT = "emit_content_addressed_artifact"
    EMIT_DDA_RECEIPT = "emit_dda_receipt"
    RENDER_PROSE_FROM_ROOT = "render_prose_from_root"
    TEST = "test"


class PfpFramingMode(str, Enum):
    STRICT = "strict"
    PERMISSIVE = "permissive"


class PfpEvidenceCeiling(str, Enum):
    REPLAYABLE_LAB_EVIDENCE = "ReplayableLabEvidence"
    MACHINE_CHECKED_PROOF = "MachineCheckedProof"
    THEORETICAL_CONJECTURE = "TheoreticalConjecture"


class PfpOraclePolicy(str, Enum):
    INDEPENDENT_GATE_RECEIPTS_REQUIRED = "IndependentGateReceiptsRequired"
    INDEPENDENT_GATE_RECEIPTS_AND_EXTERNAL_PROMOTION_REQUIRED = "IndependentGateReceiptsAndExternalPromotionRequired"


class PfpPacketKind(str, Enum):
    PROBLEM = "problem"
    CANDIDATE = "candidate"
    EVALUATION = "evaluation"
    RECEIPT = "receipt"


class PfpNextWorkItem(PfpBaseModel):
    order: int
    target: str
    work_id: str


class PfpFableLongHorizonTaskPacket(PfpBaseModel):
    schema_version: str = Field(default="omega.symbol-game.packet-envelope.v2")
    task_id: str
    packet_id: str
    packet_family: str
    packet_kind: PfpPacketKind
    parent_event_id: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    evidence_ceiling: PfpEvidenceCeiling
    oracle_policy: PfpOraclePolicy
    framing_mode: PfpFramingMode
    carrier_id: str
    initial_state_hash: str
    source_digest: str
    step_budget: int = Field(ge=1)
    terminal_target: str
    allowed_transforms: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    protected_boundaries: list[str] = Field(default_factory=list)
    payload: list[Any] = Field(default_factory=list)


# =============================================================================
# 8. MODES CATALOG & SPECIFICATIONS (modes/)
# =============================================================================

class PfpModeCluster(str, Enum):
    CARRIER_REPRESENTATION = "Cluster I: Carrier & Representation"
    INTERNAL_STEERING = "Cluster II: Internal Steering"
    GROUP_COCHAIN_STRUCTURE = "Cluster III: Group & Cochain Structure"
    DIALECTICAL_ADVERSARIAL = "Cluster IV: Dialectical & Adversarial"
    FOUNDATIONAL_MECHANIZATION = "Cluster V: Foundational Mechanization"


class PfpModeCatalogEntry(PfpBaseModel):
    mode_id: int = Field(ge=1, le=20)
    name: str = Field(min_length=1)
    cluster: PfpModeCluster
    contract_path: str = Field(pattern=r"^mode_\d{2}_[a-z0-9_]+/contract\.yaml$")
    extra_specs: list[str] = Field(default_factory=list)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpModeCatalog(PfpBaseModel):
    entries: list[PfpModeCatalogEntry] = Field(min_length=20, max_length=20)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpVerifierContract(PfpBaseModel):
    verifier_type: str = Field(min_length=1)
    fail_closed: bool


class PfpModeFile(PfpBaseModel):
    mode_id: int = Field(ge=1, le=20)
    name: str = Field(min_length=1)
    cluster: PfpModeCluster
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    core_mechanism: str = Field(min_length=1)
    substrate: str = Field(min_length=1)
    paper_reference: str = Field(min_length=1)
    rules: list[str] = Field(default_factory=list)
    entry_preconditions: list[str] = Field(default_factory=list)
    winning_condition: str = Field(min_length=1)
    failure_modes: list[str] = Field(default_factory=list)
    verifier_contract: PfpVerifierContract


class PfpClusterEntry(PfpBaseModel):
    name: str
    modes: list[int] = Field(default_factory=list)


class PfpClusterIndex(PfpBaseModel):
    cluster_1_carrier_representation: PfpClusterEntry
    cluster_2_internal_steering: PfpClusterEntry
    cluster_3_group_cochain_structure: PfpClusterEntry
    cluster_4_dialectical_adversarial: PfpClusterEntry
    cluster_5_foundational_mechanization: PfpClusterEntry


class PfpManifestMode(PfpBaseModel):
    id: int = Field(ge=1, le=20)
    file: str = Field(min_length=1)


# =============================================================================
# 9. NORMAL FORMS DOMAIN INDEX & CONTRACTS (normal_forms/)
# =============================================================================

class PfpNfFamily(str, Enum):
    CODA = "coda"
    EPISTEMIC = "epistemic"
    CHANGE = "change"
    COMPILATION = "compilation"
    REPRESENTATION = "representation"
    EVIDENCE = "evidence"
    EXPERIMENTAL = "experimental"


class PfpNfIndexEntry(PfpBaseModel):
    nf_id: str = Field(pattern=r"^nf\.[a-z]+\.[a-z_]+$")
    short_name: str = Field(min_length=1)
    name: str = Field(min_length=1)
    family: PfpNfFamily
    form_category: Literal["Extended Form Contract"] = "Extended Form Contract"
    qualifies_as_true_normal_form: Literal[False] = False
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNfDomainIndex(PfpBaseModel):
    contracts: list[PfpNfIndexEntry] = Field(min_length=9, max_length=9)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNormalFormContractIdentity(PfpBaseModel):
    id: str
    name: str
    short_name: str
    version: str
    theory_status: str
    contract_status: str
    verification_status: str
    family: str


class PfpNormalFormClassification(PfpBaseModel):
    hierarchy_level: str
    subject_kind: list[str] = Field(default_factory=list)
    data_posture: str
    mathematical_posture: str


class PfpNormalFormContract(PfpBaseModel):
    schema_version: str = "smplx.nf.contract_schema.v1"
    contract_kind: str
    identity: PfpNormalFormContractIdentity
    classification: PfpNormalFormClassification
    purpose: Any
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


# =============================================================================
# 10. PROMPT REWRITING & WIRE TOPOLOGY (rewriting/rewriting_types.yaml)
# =============================================================================

class PfpSpanRole(str, Enum):
    TASK = "task"
    CONSTRAINT = "constraint"
    CONTEXT = "context"
    OUTPUT = "output"
    UNRESOLVED = "unresolved"


class PfpByteSpan(PfpBaseModel):
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    role: PfpSpanRole

    @model_validator(mode="after")
    def _validate_interval(self) -> PfpByteSpan:
        if self.end_byte <= self.start_byte:
            raise ValueError(f"end_byte ({self.end_byte}) must be strictly greater than start_byte ({self.start_byte})")
        return self


class PfpSpanPartition(PfpBaseModel):
    prompt_byte_length: int = Field(ge=1)
    spans: list[PfpByteSpan] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_cover(self) -> PfpSpanPartition:
        cursor = 0
        for span in self.spans:
            if span.start_byte != cursor:
                raise ValueError(f"Gap or overlap at byte {cursor}: next span starts at {span.start_byte}")
            cursor = span.end_byte
        if cursor != self.prompt_byte_length:
            raise ValueError(f"Spans end at byte {cursor}, but prompt_byte_length is {self.prompt_byte_length}")
        return self


class PfpBoundaryWire(PfpBaseModel):
    profile: Literal["mss-boundary-v1"] = "mss-boundary-v1"
    term: str = Field(min_length=1)


class PfpSymbolMapping(PfpBaseModel):
    symbol_token: str = Field(pattern=r"^s[0-9]+$")
    start_byte: int = Field(ge=0)
    end_byte: int = Field(ge=0)
    text: str


class PfpRewritingContract(PfpBaseModel):
    schema_id: Literal["omega.pfp.rewriting.types.v1"] = "omega.pfp.rewriting.types.v1"
    title: str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    source: str
    span_roles: list[str] = Field(default_factory=list)
    partition_rules: list[str] = Field(default_factory=list)
    wire_profile: dict[str, Any]
    receipt_guarantees_checked_by_model: list[str] = Field(default_factory=list)
    example: dict[str, Any]


# =============================================================================
# 11. SCHEMA REGISTER & ENVELOPES (schemas/)
# =============================================================================

class PfpEnvelopeSchemaEntry(PfpBaseModel):
    file: str = Field(pattern=r"^[a-z0-9_]+\.schema\.yaml$")
    dialect: Literal["https://json-schema.org/draft/2020-12/schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema_dollar_id: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpGrammarSchemaEntry(PfpBaseModel):
    file: str = Field(pattern=r"^[a-z0-9_]+_schema\.yaml$")
    schema_id: str = Field(pattern=r"^[A-Z0-9]+(-[A-Z0-9]+)*-v\d+\.\d+$")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpSchemaRegister(PfpBaseModel):
    envelope_schemas: list[PfpEnvelopeSchemaEntry] = Field(min_length=9, max_length=9)
    grammar_schemas: list[PfpGrammarSchemaEntry] = Field(min_length=4, max_length=4)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


# =============================================================================
# 12. STAGES & EXECUTION CONTROLLER (stages/)
# =============================================================================

class PfpStageName(str, Enum):
    COMPRESSION_GATE = "compression_gate"
    IDEATION = "ideation"
    AUDIT = "audit"
    L2_EXTRACTION = "l2_extraction"
    EVALUATION = "evaluation"
    ADVERSARIAL = "adversarial"
    COUNTERMODEL = "countermodel"
    EVIDENCE_PLAN = "evidence_plan"


class PfpStageExecutor(str, Enum):
    MODEL = "model"
    HOST = "host"


class PfpStageInputContract(PfpBaseModel):
    preserve_original_seed: bool
    retain_stage_2_candidates: bool
    candidate_source_stage: int
    independent_checker_required: bool


class PfpStageFile(PfpBaseModel):
    stage: int = Field(ge=1, le=8)
    name: PfpStageName
    executor: PfpStageExecutor
    requires: list[int] = Field(default_factory=list)
    version: str
    derived_under_policy: Literal["SPK-001"] = "SPK-001"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    source_template: str
    system_prompt: str
    user_prompt: str
    response_schema: dict[str, Any] | None = None
    input_contract: PfpStageInputContract | None = None


class PfpStageReference(PfpBaseModel):
    stage: int = Field(ge=1, le=8)
    name: PfpStageName
    executor: PfpStageExecutor
    requires: list[int] = Field(default_factory=list)


class PfpStageController(PfpBaseModel):
    policy_id: Literal["SPK-001"] = "SPK-001"
    version: str
    public_stage_count: Literal[8] = 8
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    system_prompt: str
    worked_example: str
    stages: list[PfpStageReference] = Field(min_length=8, max_length=8)


# =============================================================================
# 13. TYPE REGISTER METRICS & INVARIANTS (type_register/)
# =============================================================================

class PfpModuleWorld(str, Enum):
    COLOCATED = "colocated"
    RUNTIME = "runtime"
    GENERATED = "generated"


class PfpModuleSource(str, Enum):
    PYDANTIC = "pydantic"
    YAML = "yaml"
    BOTH_PARITY_TESTED = "both_parity_tested"
    BOTH_UNCHECKED = "both_unchecked"


class PfpYamlRole(str, Enum):
    JSON_SCHEMA = "json_schema"
    GENERATED_JSON_SCHEMA = "generated_json_schema"
    CUSTOM_SCHEMA = "custom_schema"
    DATA = "data"


class PfpModuleStatus(str, Enum):
    CANONICAL = "canonical"
    REVIEW = "review"


class PfpYamlRef(PfpBaseModel):
    path: str = Field(min_length=1)
    role: PfpYamlRole


class PfpModuleRow(PfpBaseModel):
    path: str = Field(pattern=r"^[a-z0-9_/]+\.py$")
    world: PfpModuleWorld
    source: PfpModuleSource
    yaml: list[PfpYamlRef] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    status: PfpModuleStatus
    note: str | None = None


class PfpTypeRegister(PfpBaseModel):
    schema_: Literal["pfp.type-register.v1"] = Field(default="pfp.type-register.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    modules: list[PfpModuleRow]
    name_collisions: list[dict[str, Any]] = Field(default_factory=list)
    overlaps: list[dict[str, Any]] = Field(default_factory=list)
    derived: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# CANONICAL ERGONOMIC ALIASES (Non-colliding AST Assignments)
# =============================================================================

ArithmeticDomain = PfpArithmeticDomain
ClaimedMove = PfpClaimedMove
VerificationRule = PfpVerificationRule
VerificationStatus = PfpVerificationStatus
StaticCellBounds = PfpStaticCellBounds
Edge = PfpEdge
Face = PfpFace
Carrier = PfpCarrier
BoundaryMatrices = PfpBoundaryMatrices
ActiveObstruction = PfpActiveObstruction
CycleBalanceProblem = PfpCycleBalanceProblem
CycleBalanceCandidate = PfpCycleBalanceCandidate
CycleBalanceVerifier = PfpCycleBalanceVerifier
CycleBalanceReceipt = PfpCycleBalanceReceipt
CycleBalanceQuartet = PfpCycleBalanceQuartet

AllowedTransform = PfpAllowedTransform
FramingMode = PfpFramingMode
EvidenceCeiling = PfpEvidenceCeiling
OraclePolicy = PfpOraclePolicy
PacketKind = PfpPacketKind
NextWorkItem = PfpNextWorkItem
FableLongHorizonTaskPacket = PfpFableLongHorizonTaskPacket

ModeCluster = PfpModeCluster
ModeCatalogEntry = PfpModeCatalogEntry
ModeCatalog = PfpModeCatalog
VerifierContract = PfpVerifierContract
ModeFile = PfpModeFile
ClusterEntry = PfpClusterEntry
ClusterIndex = PfpClusterIndex
ManifestMode = PfpManifestMode

NfFamily = PfpNfFamily
NfIndexEntry = PfpNfIndexEntry
NfDomainIndex = PfpNfDomainIndex
NormalFormContractIdentity = PfpNormalFormContractIdentity
NormalFormClassification = PfpNormalFormClassification
NormalFormContract = PfpNormalFormContract

SpanRole = PfpSpanRole
ByteSpan = PfpByteSpan
SpanPartition = PfpSpanPartition
BoundaryWire = PfpBoundaryWire
SymbolMapping = PfpSymbolMapping
RewritingContract = PfpRewritingContract

EnvelopeSchemaEntry = PfpEnvelopeSchemaEntry
GrammarSchemaEntry = PfpGrammarSchemaEntry
SchemaRegister = PfpSchemaRegister

StageName = PfpStageName
StageExecutor = PfpStageExecutor
StageInputContract = PfpStageInputContract
StageFile = PfpStageFile
StageReference = PfpStageReference
StageController = PfpStageController

ModuleWorld = PfpModuleWorld
ModuleSource = PfpModuleSource
YamlRole = PfpYamlRole
ModuleStatus = PfpModuleStatus
YamlRef = PfpYamlRef
ModuleRow = PfpModuleRow
TypeRegister = PfpTypeRegister

SemanticPolicyManifest = PfpSemanticPolicyManifest
Mss0GrammarConstraint = PfpMss0GrammarConstraint
OpSemantics = PfpOpSemantics
Mss0Level = PfpMss0Level
Mss0TypingRules = PfpMss0TypingRules
EvaluatorBinding = PfpEvaluatorBinding
EvaluatorScopeRule = PfpEvaluatorScopeRule
EvidenceLevel = PfpEvidenceLevel
ClaimHygiene = PfpClaimHygiene
