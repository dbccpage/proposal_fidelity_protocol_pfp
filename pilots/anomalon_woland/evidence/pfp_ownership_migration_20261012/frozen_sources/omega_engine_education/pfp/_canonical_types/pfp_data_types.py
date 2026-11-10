"""Proposal Fidelity Protocol (PFP) - Canonical Data Types (Pydantic V2).

AuthorityEffect: None.

Comprehensive fully-typed data model catalog governing all PFP artifacts and registers under
`omega_engine_education/pfp/infrastructure/yaml/`:
1. Pilot Specifications & Ingress Coordinates (spec.yaml)
2. Model Responses, Sanitization Reports & Evaluation Receipts (response.yaml)
3. Universal Prompt Templates, P* Trees, Lineage & Guidance Defense Slots (prompt_template.yaml, p_star.yaml)
4. System Prompt Policy Manifest, Typing Rules & Claim Hygiene
5. Seed Prompts & Oracle Ground Truth Expectations (seed.yaml)
6. Cycle Balance Quartet: Carrier, Cell Bounds, Matrices, Problem, Candidate, Verifier, Receipt (cycle_balance/)
7. Fixtures & Long-Horizon Task Packet Envelopes (fixtures/fable_long_horizon_task_packet_v2.yaml)
8. Modes Catalog & Specifications: 20 Play Modes & 5 Clusters (modes/)
9. Normal Forms Domain Index & Extended Form Contracts (nf/)
10. Prompt Rewriting & Wire Topologies: mss-boundary-v1, Partitions, Symbol Codebook (rewriting/)
11. Schema Registry & Envelope Envelopes: Draft 2020-12 & Grammar Schemas (schemas/)
12. Stages & Execution Controllers: 8 Numbered Pipeline Stages (stages/)
13. Type Register Metrics & Invariants: Census & World Definitions (type_register/)
14. Retinue, Intergate & Empirical Benchmark Gates (gates/)
15. Cartesian Matrix Space Product Model (cartesian_matrix/)
16. Task Families & Open Dynamic Registry (task_families/)
17. Symbolic Wire Syntax Profiles: Tier-D & Tier-H Profiles (wires/)
18. Stage Transition & Retraction Invariance Contracts (contracts/)
19. Algebraic Domains & Operational Taxonomy Enums (taxonomy/)
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Callable, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
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


class TaskModeFidelity(str, Enum):
    LITERAL_EXTRACTION = "literal_extraction"
    FINITE_DEDUCTION = "finite_deduction"


class VariableIdentifierPermutation(str, Enum):
    CANONICAL = "canonical"
    PERMUTED = "permuted"


class FloatingPointRisk(str, Enum):
    EXACT_MODULAR = "exact_modular"
    FLOAT_APPROXIMATED = "float_approximated"


class ArmTemplate(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"


class MissingPremise(str, Enum):
    ANSWERABLE = "answerable"
    UNANSWERABLE = "unanswerable"


class CohomologyDefectClass(str, Enum):
    NONE = "none"
    EXACT_BOUNDARY = "exact_boundary"
    CLOSED_NON_EXACT = "closed_non_exact"
    CURVATURE_DEFECT = "curvature_defect"


class MagmaAssociativityType(str, Enum):
    NONE = "none"
    ASSOCIATIVE_SEMIGROUP = "associative_semigroup"
    NON_ASSOCIATIVE_MAGMA = "non_associative_magma"


class CheckerId(str, Enum):
    EXACT_LINALG = "PFP-01-EXACT-LINALG"
    GRAPH_FACTS = "PFP-02-GRAPH-FACTS"
    GRAPH_REPAIR = "PFP-03-GRAPH-REPAIR"
    TYPED_REFUSAL = "PFP-14-TYPED-REFUSAL"
    COCHAIN_DEFECT = "PFP-52-COCHAIN-DEFECT"
    MAGMA_ASSOC = "PFP-55-MAGMA-ASSOC"


class StructureDeltaMetric(str, Enum):
    EXACT_RATIONAL_DELTA = "exact_rational_delta"
    GATE_BOOLEAN = "gate_boolean"
    COCHAIN_NORM = "cochain_norm"
    RANK_CHANGE = "rank_change"


class RepresentationRewrite(str, Enum):
    RAW_PROSE = "raw_prose"
    STRUCTURED_SPANS = "structured_spans"
    MSS_BOUNDARY_V1 = "mss_boundary_v1"
    SN_WIRE_V2 = "sn_wire_v2"
    EBNF_WIRE_V1 = "ebnf_wire_v1"
    HIEROGLYPHIC_GLYPHS = "hieroglyphic_glyphs"


class ModelClass(str, Enum):
    CLASS_8B = "8B"
    CLASS_70B = "70B"
    CLASS_500B_PLUS = "500B_plus"


# =============================================================================
# 1. PILOT SPECIFICATION (spec.yaml)
# =============================================================================

class PilotCoordinates(PfpBaseModel):
    task_family: TaskFamily | str
    difficulty_rung: int = Field(ge=1, le=5)
    representation_rewrite: RepresentationRewrite | str
    rewrite_count: int = Field(ge=0)
    legend_present: bool
    mode: str
    stage_count: int = Field(ge=1)
    pass_count: int = Field(ge=1)
    single_shot: bool
    antibody_active: bool
    antibody_ids: list[str] = Field(default_factory=list)
    model_class: ModelClass | str
    model_id: str
    temperature: float = Field(ge=0.0, le=2.0)
    target_spend_usd: float = Field(ge=0.0)


class PilotIngress(PfpBaseModel):
    task_mode_fidelity: TaskModeFidelity | str
    variable_identifier_permutation: VariableIdentifierPermutation | str
    floating_point_approximation_risk: FloatingPointRisk | str
    arm_template: ArmTemplate | str
    missing_premise: MissingPremise | str
    cohomology_defect_class: CohomologyDefectClass | str
    magma_associativity_type: MagmaAssociativityType | str


class PilotHostGate(PfpBaseModel):
    checker_id: CheckerId | str
    response_schema: str
    residual_logging: bool
    structure_delta_metric: StructureDeltaMetric | str
    expected_outcome: str


class PilotSpec(PfpBaseModel):
    schema_: Literal["pfp.pilot-spec.v1"] = Field(default="pfp.pilot-spec.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str = Field(pattern=r"^pilot_\d{5}$")
    execution_mode: ExecutionMode
    coordinates: PilotCoordinates
    ingress: PilotIngress
    host_gate: PilotHostGate
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    trial_status: TrialStatus = TrialStatus.NOT_RUN


# =============================================================================
# 2. PILOT RESPONSE & EVALUATION RECEIPTS (response.yaml)
# =============================================================================

class PromptResponsePayload(PfpBaseModel):
    raw_response: str
    model_id: str
    finish_reason: str
    latency_ms: int = Field(ge=0)
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)


class SanitizationReport(PfpBaseModel):
    clean: bool
    stripped_tokens: list[str] = Field(default_factory=list)
    detected_delimiters: list[str] = Field(default_factory=list)
    encoding_normalized: bool = True


class EvaluationReceipt(PfpBaseModel):
    checker_id: CheckerId | str
    status: EvaluationStatus
    structure_delta: float
    residual_norm: float | None = None
    witness_hash: str | None = None
    checked_at: str
    pass_rule: bool


class PilotResponse(PfpBaseModel):
    schema_: Literal["pfp.pilot-response.v1"] = Field(default="pfp.pilot-response.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    pilot_id: str = Field(pattern=r"^pilot_\d{5}$")
    response: PromptResponsePayload
    sanitization: SanitizationReport
    evaluation: EvaluationReceipt


# =============================================================================
# 3. PROMPT TEMPLATES, P* TREES & DEFENSES (prompt_template.yaml, p_star.yaml)
# =============================================================================

class GuidanceSlot(PfpBaseModel):
    slot_id: str
    role: str
    text: str
    priority: int = 1


class RuleSlot(PfpBaseModel):
    rule_id: str
    rule_type: ConstraintType
    predicate: str
    severity: Severity = Severity.P1


class AntibodySlot(PfpBaseModel):
    antibody_id: str
    target_failure_pattern: str
    inoculation_payload: str
    provenance_pilot: str | None = None


class AntipatternSlot(PfpBaseModel):
    pattern_id: str
    prohibited_phrase_or_structure: str
    remediation_hint: str


class HelpfulPatternSlot(PfpBaseModel):
    pattern_id: str
    encouraged_structure: str
    exemplar: str


class PromptLineageSlot(PfpBaseModel):
    parent_prompt_hash: str | None = None
    mutation_history: list[str] = Field(default_factory=list)
    generation_method: str = "direct"
    seed_provenance: str | None = None


class NegativeMutationFixture(PfpBaseModel):
    fixture_id: str
    checker_id: CheckerId | str
    mutation_kind: str
    description: str
    expected_status: EvaluationStatus = EvaluationStatus.WRONG_ANSWER
    expected_refusal_code: str | None = None


class PromptTemplate(PfpBaseModel):
    schema_: Literal["pfp.prompt-template.v1"] = Field(default="pfp.prompt-template.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    template_id: str
    task_family: TaskFamily | str
    difficulty_rung: int = Field(ge=1, le=5)
    base_stimulus: str
    guidance_slots: list[GuidanceSlot] = Field(default_factory=list)
    rule_slots: list[RuleSlot] = Field(default_factory=list)
    antibodies: list[AntibodySlot] = Field(default_factory=list)
    negative_mutations: list[NegativeMutationFixture] = Field(default_factory=list)
    lineage: PromptLineageSlot = Field(default_factory=lambda: PromptLineageSlot())


class PStarPrompt(PfpBaseModel):
    schema_: Literal["pfp.p-star.v1"] = Field(default="pfp.p-star.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    p_star_id: str
    assembled_prompt_text: str
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    active_guidance: list[GuidanceSlot] = Field(default_factory=list)
    active_antibodies: list[AntibodySlot] = Field(default_factory=list)
    active_antipatterns: list[AntipatternSlot] = Field(default_factory=list)
    active_helpful_patterns: list[HelpfulPatternSlot] = Field(default_factory=list)


# =============================================================================
# 4. SYSTEM PROMPT POLICY MANIFEST, TYPING & CLAIM HYGIENE
# =============================================================================

class PfpMss0GrammarConstraint(PfpBaseModel):
    non_terminal: str
    expansion_pattern: str


class PfpOpSemantics(PfpBaseModel):
    operator: str
    arity: int
    axioms: list[str] = Field(default_factory=list)


class PfpMss0Level(PfpBaseModel):
    level: int
    name: str
    grammar: list[PfpMss0GrammarConstraint] = Field(default_factory=list)
    operations: list[PfpOpSemantics] = Field(default_factory=list)


class PfpMss0TypingRules(PfpBaseModel):
    soundness_postulate: str
    levels: list[PfpMss0Level] = Field(default_factory=list)


class PfpEvaluatorBinding(PfpBaseModel):
    binding_id: str
    checker_id: CheckerId | str
    executable_path: str


class PfpEvaluatorScopeRule(PfpBaseModel):
    rule_name: str
    forbidden_claims: list[str] = Field(default_factory=list)
    admitted_claims: list[str] = Field(default_factory=list)


class PfpEvidenceLevel(str, Enum):
    TOY_SETTING = "toy_setting"
    EMPIRICAL_BENCHMARK = "empirical_benchmark"
    EXACT_VERIFIED = "exact_verified"


class PfpClaimHygiene(PfpBaseModel):
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    forbidden_verbs: list[str] = Field(default_factory=list)
    replacement_defaults: dict[str, str] = Field(default_factory=dict)
    mandatory_fields_in_artifact_summary: list[str] = Field(default_factory=list)


class PfpSemanticPolicyManifest(PfpBaseModel):
    schema_: Literal["pfp.system-prompt-manifest.v1"] = Field(
        default="pfp.system-prompt-manifest.v1", alias="schema"
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    mss0_typing: PfpMss0TypingRules
    evaluator_bindings: list[PfpEvaluatorBinding] = Field(default_factory=list)
    evaluator_scope: list[PfpEvaluatorScopeRule] = Field(default_factory=list)
    claim_hygiene: PfpClaimHygiene


SystemPromptManifest = PfpSemanticPolicyManifest


# =============================================================================
# 5. SEED PROMPT (seed.yaml)
# =============================================================================

class ExpectedOutcome(PfpBaseModel):
    checker_id: CheckerId | str
    status: EvaluationStatus
    solution_oracle: str | None = None
    refusal_oracle: str | None = None


class SeedPrompt(PfpBaseModel):
    schema_: Literal["pfp.seed-prompt.v1"] = Field(default="pfp.seed-prompt.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    seed_id: str
    task_family: TaskFamily | str
    difficulty_rung: int = Field(ge=1, le=5)
    prompt_text: str
    expected_outcome: ExpectedOutcome


# =============================================================================
# 6. CYCLE BALANCE QUARTET (cycle_balance/)
# =============================================================================

class PfpArithmeticDomain(str, Enum):
    EXACT_INTEGER = "EXACT_INTEGER"
    EXACT_RATIONAL = "EXACT_RATIONAL"
    FINITE_FIELD_GF2 = "FINITE_FIELD_GF2"
    MODULAR_RING_ZN = "MODULAR_RING_ZN"
    BOOLEAN_ALGEBRA = "BOOLEAN_ALGEBRA"


class PfpClaimedMove(str, Enum):
    ATTACH_2CELL = "ATTACH_2CELL"
    REMOVE_1CELL = "REMOVE_1CELL"
    CONTRACT_EDGE = "CONTRACT_EDGE"
    GAUGE_TRANSFORM = "GAUGE_TRANSFORM"
    LIFT_CARRIER = "LIFT_CARRIER"
    REFUSE_DESCENT = "REFUSE_DESCENT"
    REWRITE_EXPRESSION = "REWRITE_EXPRESSION"
    SCALE_DESCENT = "SCALE_DESCENT"
    EXACT_REPAIR = "EXACT_REPAIR"
    STRUCTURAL_LIFT = "STRUCTURAL_LIFT"
    TYPED_REFUSAL = "TYPED_REFUSAL"


class PfpVerificationRule(str, Enum):
    STATIC_CELL_BOUNDS_CHECK = "STATIC_CELL_BOUNDS_CHECK"
    CHAIN_COMPLEX_NILPOTENCY_CHECK = "CHAIN_COMPLEX_NILPOTENCY_CHECK"
    INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE = "INTEGER_SMITH_NORMAL_FORM_CYCLE_BALANCE"
    EXACT_SCALAR_SUBSTITUTION = "EXACT_SCALAR_SUBSTITUTION"
    DUAL_CIRCULATION_FEASIBILITY = "DUAL_CIRCULATION_FEASIBILITY"
    ACYCLIC_POTENTIAL_GRADIENT = "ACYCLIC_POTENTIAL_GRADIENT"
    ASSOCIATIVITY_DIVERGENCE_VERIFIER = "ASSOCIATIVITY_DIVERGENCE_VERIFIER"
    BOOLEAN_SATISFIABILITY_VERIFIER = "BOOLEAN_SATISFIABILITY_VERIFIER"
    LEAN4_KERNEL_ELABORATION = "LEAN4_KERNEL_ELABORATION"
    RATIONAL_COCHAIN_DEFECT_ZERO = "RATIONAL_COCHAIN_DEFECT_ZERO"
    REFUSAL_PAYLOAD_VALIDITY = "REFUSAL_PAYLOAD_VALIDITY"


class PfpVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class PfpStaticCellBounds(PfpBaseModel):
    max_vertices: int = Field(ge=0)
    max_edges: int = Field(ge=0)
    max_faces: int = Field(ge=0)


class PfpEdge(PfpBaseModel):
    id: str = Field(min_length=1)
    source: int = Field(ge=0)
    target: int = Field(ge=0)


class PfpFace(PfpBaseModel):
    id: str = Field(min_length=1)
    boundary_cycle: list[int] = Field(min_length=3)


class PfpCarrier(PfpBaseModel):
    carrier_id: str = Field(min_length=1)
    vertices: list[int] = Field(default_factory=list)
    edges: list[PfpEdge] = Field(default_factory=list)
    faces: list[PfpFace] = Field(default_factory=list)


class PfpBoundaryMatrices(PfpBaseModel):
    d0: list[list[int]] = Field(default_factory=list)
    d1: list[list[int]] = Field(default_factory=list)


class PfpActiveObstruction(PfpBaseModel):
    dimension: int = Field(ge=0)
    cycle: list[int] = Field(default_factory=list)
    weight: int = 1


class PfpCycleBalanceProblem(PfpBaseModel):
    schema_: Literal["pfp.cycle-balance-problem.v1"] = Field(
        default="pfp.cycle-balance-problem.v1", alias="schema"
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    problem_id: str = Field(min_length=1)
    problem_kind: Literal["CYCLE_BALANCE_CHORD_REPAIR"] = "CYCLE_BALANCE_CHORD_REPAIR"
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    static_cell_bounds: PfpStaticCellBounds
    carrier: PfpCarrier
    boundary_matrices: PfpBoundaryMatrices
    active_obstruction: PfpActiveObstruction
    step_budget: int = Field(ge=1)


class PfpCycleBalanceCandidate(PfpBaseModel):
    schema_: Literal["pfp.cycle-balance-candidate.v1"] = Field(
        default="pfp.cycle-balance-candidate.v1", alias="schema"
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    candidate_id: str = Field(min_length=1)
    target_problem_id: str = Field(min_length=1)
    proposed_move: PfpClaimedMove
    move_payload: dict[str, Any]
    steps_taken: int = Field(ge=1)


class PfpCycleBalanceVerifier(PfpBaseModel):
    schema_: Literal["pfp.cycle-balance-verifier.v1"] = Field(
        default="pfp.cycle-balance-verifier.v1", alias="schema"
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    verifier_id: str = Field(min_length=1)
    target_problem_id: str = Field(min_length=1)
    target_candidate_id: str = Field(min_length=1)
    arithmetic_domain: PfpArithmeticDomain = PfpArithmeticDomain.EXACT_INTEGER
    rules: list[PfpVerificationRule] = Field(min_length=1)
    fail_closed: bool = True


class PfpCycleBalanceReceipt(PfpBaseModel):
    schema_: Literal["pfp.cycle-balance-receipt.v1"] = Field(
        default="pfp.cycle-balance-receipt.v1", alias="schema"
    )
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    receipt_id: str = Field(min_length=1)
    target_problem_id: str = Field(min_length=1)
    target_candidate_id: str = Field(min_length=1)
    target_verifier_id: str = Field(min_length=1)
    problem_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verification_status: PfpVerificationStatus
    rules_applied: list[PfpVerificationRule]
    diagnostics: list[str] = Field(default_factory=list)


def _canonical_json_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_hexdigest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class PfpCycleBalanceQuartet(PfpBaseModel):
    problem: PfpCycleBalanceProblem
    candidate: PfpCycleBalanceCandidate
    verifier: PfpCycleBalanceVerifier
    receipt: PfpCycleBalanceReceipt

    def check_digest_bindings(self, raw_dict: dict[str, dict[str, Any]]) -> bool:
        p_dig = _sha256_hexdigest(_canonical_json_bytes(raw_dict["problem"]))
        c_dig = _sha256_hexdigest(_canonical_json_bytes(raw_dict["candidate"]))
        v_dig = _sha256_hexdigest(_canonical_json_bytes(raw_dict["verifier"]))

        return (
            self.receipt.problem_digest == p_dig
            and self.receipt.candidate_digest == c_dig
            and self.receipt.verifier_digest == v_dig
            and self.candidate.target_problem_id == self.problem.problem_id
            and self.verifier.target_problem_id == self.problem.problem_id
            and self.verifier.target_candidate_id == self.candidate.candidate_id
            and self.receipt.target_problem_id == self.problem.problem_id
            and self.receipt.target_candidate_id == self.candidate.candidate_id
            and self.receipt.target_verifier_id == self.verifier.verifier_id
        )


# =============================================================================
# 7. FIXTURES & LONG-HORIZON TASK PACKETS (fixtures/)
# =============================================================================

class PfpAllowedTransform(str, Enum):
    SWAP_ROWS = "swap_rows"
    ADD_MULTIPLE = "add_multiple"
    TRANSPOSE = "transpose"
    ATTACH_CELL = "attach_cell"
    SCALE_DESCENT = "scale_descent"
    EXACT_REPAIR = "exact_repair"


class PfpFramingMode(str, Enum):
    BARE_MATH = "bare_math"
    FABLE = "fable"
    PSEUDOCODE = "pseudocode"


class PfpEvidenceCeiling(str, Enum):
    TOY_SETTING = "toy_setting"
    EMPIRICAL_BENCHMARK = "empirical_benchmark"
    EXACT_VERIFIED = "exact_verified"


class PfpOraclePolicy(PfpBaseModel):
    verification_mode: Literal["fail_closed"] = "fail_closed"
    evidence_ceiling: PfpEvidenceCeiling = PfpEvidenceCeiling.TOY_SETTING
    prohibited_hype_verbs: list[str] = Field(default_factory=list)


class PfpPacketKind(str, Enum):
    LONG_HORIZON_TASK_PACKET = "LONG_HORIZON_TASK_PACKET"


class PfpNextWorkItem(PfpBaseModel):
    step_index: int = Field(ge=0)
    instruction: str
    target_slot: str


class PfpFableLongHorizonTaskPacket(PfpBaseModel):
    schema_: Literal["pfp.fixtures.v1"] = Field(default="pfp.fixtures.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    packet_id: str
    packet_kind: PfpPacketKind = PfpPacketKind.LONG_HORIZON_TASK_PACKET
    target_mode: str
    framing: PfpFramingMode
    oracle_policy: PfpOraclePolicy
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
    clusters: list[PfpClusterEntry] = Field(default_factory=list)


class PfpManifestMode(PfpBaseModel):
    id: int = Field(ge=1, le=20)
    file: str = Field(min_length=1)


# =============================================================================
# 9. NORMAL FORMS DOMAIN INDEX & CONTRACTS (nf/)
# =============================================================================

class PfpNfFamily(str, Enum):
    CODA = "coda"
    EPISTEMIC = "epistemic"
    CHANGE = "change"
    COMPILATION = "compilation"
    REPRESENTATION = "representation"
    EVIDENCE = "evidence"
    EXPERIMENTAL = "experimental"
    BRIDGE = "bridge"
    MSSN = "mssn"
    GENESIS = "genesis"
    WDP = "wdp"


class PfpNfIndexEntry(PfpBaseModel):
    nf_id: str = Field(pattern=r"^nf\.[a-z0-9_]+\.[a-z0-9_.]+$")
    short_name: str = Field(min_length=1)
    name: str = Field(min_length=1)
    family: PfpNfFamily | str
    form_category: str = "Extended Form Contract"
    qualifies_as_true_normal_form: bool = False
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNfDomainIndex(PfpBaseModel):
    contracts: list[PfpNfIndexEntry] = Field(default_factory=list)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNormalFormContractIdentity(PfpBaseModel):
    id: str | None = None
    name: str
    short_name: str | None = None
    version: str | None = None
    theory_status: str | None = None
    contract_status: str | None = None
    verification_status: str | None = None
    family: str | None = None
    canonical_form: str | None = None
    extended_normal_form_kind: str | None = None


class PfpNormalFormClassification(PfpBaseModel):
    hierarchy_level: str | None = None
    subject_kind: list[str] = Field(default_factory=list)
    data_posture: str | None = None
    mathematical_posture: str | None = None


class PfpNormalFormContract(PfpBaseModel):
    schema_version: str | None = None
    schema_ref: str | None = None
    contract_kind: str | None = None
    contract_type: str | None = None
    identity: PfpNormalFormContractIdentity
    classification: PfpNormalFormClassification | None = None
    purpose: Any = None
    quadrilateral: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


# =============================================================================
# 10. REWRITING & WIRE TOPOLOGIES (rewriting/)
# =============================================================================

class PfpSpanRole(str, Enum):
    TASK_STIMULUS = "TASK_STIMULUS"
    REASONING_TRACE = "REASONING_TRACE"
    CANDIDATE_SOLUTION = "CANDIDATE_SOLUTION"
    CHAIN_OF_THOUGHT = "CHAIN_OF_THOUGHT"
    INOCULATION_SHIELD = "INOCULATION_SHIELD"
    CANONICAL_CLOSURE = "CANONICAL_CLOSURE"


class PfpByteSpan(PfpBaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    role: PfpSpanRole


class PfpSpanPartition(PfpBaseModel):
    spans: list[PfpByteSpan]
    source_len: int = Field(ge=0)

    @field_validator("spans")
    @classmethod
    def check_monotonic_disjoint(cls, spans: list[PfpByteSpan]) -> list[PfpByteSpan]:
        cur = 0
        for s in spans:
            if s.start < cur:
                raise ValueError("Spans must be non-overlapping and sorted")
            if s.end <= s.start:
                raise ValueError("Span length must be positive")
            cur = s.end
        return spans


class PfpBoundaryWire(PfpBaseModel):
    wire_id: str
    wire_format: Literal["mss_boundary_v1", "sn_wire_v2", "ebnf_wire_v1"]
    token_legend: dict[str, str] = Field(default_factory=dict)


class PfpSymbolMapping(PfpBaseModel):
    original: str
    rewritten: str


class PfpRewritingContract(PfpBaseModel):
    schema_: Literal["pfp.rewriting.v1"] = Field(default="pfp.rewriting.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    contract_id: str
    rewrite_rules: list[str] = Field(default_factory=list)
    symbol_table: list[PfpSymbolMapping] = Field(default_factory=list)
    boundary_wires: list[PfpBoundaryWire] = Field(default_factory=list)


# =============================================================================
# 11. SCHEMA REGISTRY (schemas/)
# =============================================================================

class PfpEnvelopeSchemaEntry(PfpBaseModel):
    schema_id: str
    schema_uri: str
    file_path: str
    version: str = "2020-12"


class PfpGrammarSchemaEntry(PfpBaseModel):
    grammar_id: str
    file_path: str
    format: str = "ebnf"


class PfpSchemaRegister(PfpBaseModel):
    schema_: Literal["pfp.schema-register.v1"] = Field(default="pfp.schema-register.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    envelopes: list[PfpEnvelopeSchemaEntry] = Field(default_factory=list)
    grammars: list[PfpGrammarSchemaEntry] = Field(default_factory=list)


# =============================================================================
# 12. STAGES & EXECUTION CONTROLLERS (stages/)
# =============================================================================

class PfpStageName(str, Enum):
    STAGE_1 = "stage_1_compression_gate"
    STAGE_2 = "stage_2_prompt_expansion"
    STAGE_3 = "stage_3_candidate_admission"
    STAGE_4 = "stage_4_cycle_balance"
    STAGE_5 = "stage_5_defect_measurement"
    STAGE_6 = "stage_6_descent_execution"
    STAGE_7 = "stage_7_normal_form_chase"
    STAGE_8 = "stage_8_terminal_witness"


class PfpStageExecutor(PfpBaseModel):
    executor_name: str
    module_path: str


class PfpStageInputContract(PfpBaseModel):
    required_keys: list[str] = Field(default_factory=list)
    allowed_types: list[str] = Field(default_factory=list)


class PfpStageFile(PfpBaseModel):
    stage_id: int = Field(ge=1, le=8)
    name: PfpStageName | str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    executor: PfpStageExecutor
    input_contract: PfpStageInputContract
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)


class PfpStageReference(PfpBaseModel):
    stage_id: int = Field(ge=1, le=8)
    file: str = Field(pattern=r"^stage_\d_[a-z0-9_]+\.yaml$")


class PfpStageController(PfpBaseModel):
    schema_: Literal["pfp.stage-controller.v1"] = Field(default="pfp.stage-controller.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    stages: list[PfpStageReference] = Field(min_length=8, max_length=8)
    fail_closed: bool = True


# =============================================================================
# 13. TYPE REGISTER METRICS & INVARIANTS (type_register/)
# =============================================================================

class PfpModuleWorld(str, Enum):
    DOCS = "docs"
    CORE = "core"
    BOTH = "both"


class PfpModuleSource(str, Enum):
    DOCS_LEAD = "docs_lead"
    CORE_LEAD = "core_lead"
    SHADOW = "shadow"
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
# 14. RETINUE, INTERGATE & EMPIRICAL BENCHMARK GATES (gates/)
# =============================================================================

class ComparisonOperator(str, Enum):
    """Comparison operators used by empirical benchmark gates."""
    LT = "LT"
    GTE = "GTE"
    EQ = "EQ"


_GATE_REF_PATTERN = r"^PFP-(0[1-9]|1[0-9]|2[0-2])-[A-Z]+(-[A-Z]+)*$"


def gate_ordinal(gate_ref: str) -> int:
    """Return the two-digit ordinal of a ``PFP-NN-...`` reference."""
    return int(gate_ref.split("-")[1])


class PrimaryGate(PfpBaseModel):
    """One of the 22 primary retinue verification gates."""
    gate_id: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    name: StrictStr = Field(min_length=1)
    character: StrictStr = Field(min_length=1)
    file: StrictStr = Field(pattern=r"^\d{2}_[a-z0-9_]+\.yaml$")
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _file_prefix_matches_id(self) -> PrimaryGate:
        if int(self.file[:2]) != gate_ordinal(self.gate_id):
            raise ValueError("file number prefix must equal gate ordinal")
        return self


class Intergate(PfpBaseModel):
    """A transition register entry between two primary gates."""
    intergate_id: StrictStr = Field(pattern=r"^PFP-IG-\d{2}-[A-Z]+(-[A-Z]+)*$")
    file: StrictStr = Field(pattern=r"^intergates/\d{2}_[a-z0-9_]+\.yaml$")
    transition_from: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    transition_to: StrictStr = Field(pattern=_GATE_REF_PATTERN)
    cognitive_vector: StrictStr = Field(min_length=1)
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _edge_is_not_a_loop(self) -> Intergate:
        if gate_ordinal(self.transition_from) == gate_ordinal(self.transition_to):
            raise ValueError("an intergate must join two distinct primary gates")
        return self


class EmpiricalGate(PfpBaseModel):
    """A quantitative empirical benchmark gate."""
    gate_id: StrictStr = Field(pattern=r"^PFP-EMP-GATE-\d{3}$")
    kind: Literal["EmpiricalBenchmarkGate"]
    suite_id: StrictStr = Field(min_length=1)
    comparison_operator: ComparisonOperator
    file: StrictStr = Field(pattern=r"^empirical/\d{2}_[a-z0-9_]+\.yaml$")
    authority_effect: Literal["None"] = "None"


class GateRegister(PfpBaseModel):
    """Complete register: 22 primary gates, 10 intergates, 3 empirical gates."""
    primary_gates: list[PrimaryGate]
    intergates: list[Intergate]
    empirical_gates: list[EmpiricalGate]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _counts_and_edges(self) -> GateRegister:
        ords = sorted(gate_ordinal(g.gate_id) for g in self.primary_gates)
        if ords != list(range(1, 23)):
            raise ValueError("primary gates must be ordinals 1..22 exactly once")
        if len(self.intergates) != 10:
            raise ValueError("intergate register must hold exactly 10 entries")
        if len(self.empirical_gates) != 3:
            raise ValueError("empirical register must hold exactly 3 entries")
        return self


_PRIMARY_KEYS = ("gate_id", "name", "character", "authority_effect")
_INTER_KEYS = (
    "intergate_id",
    "transition_from",
    "transition_to",
    "cognitive_vector",
    "authority_effect",
)
_EMP_KEYS = ("gate_id", "kind", "suite_id", "comparison_operator", "authority_effect")


def _head(path: Path, keys: tuple[str, ...], rel: str) -> dict[str, object]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    out = {k: raw[k] for k in keys}
    out["file"] = rel
    return out


def load_register_from_files(gates_dir: Path) -> dict[str, list[dict[str, object]]]:
    """Collect identity headers from the on-disk gate files as register data."""
    return {
        "primary_gates": [
            _head(p, _PRIMARY_KEYS, p.name) for p in sorted(gates_dir.glob("[0-9][0-9]_*.yaml"))
        ],
        "intergates": [
            _head(p, _INTER_KEYS, f"intergates/{p.name}")
            for p in sorted((gates_dir / "intergates").glob("*.yaml"))
        ],
        "empirical_gates": [
            _head(p, _EMP_KEYS, f"empirical/{p.name}")
            for p in sorted((gates_dir / "empirical").glob("*.yaml"))
        ],
    }


# =============================================================================
# 15. CARTESIAN MATRIX SPACE (cartesian_matrix/)
# =============================================================================

class DimensionDefinition(PfpBaseModel):
    """Specification of an orthogonal coordinate dimension in the Cartesian product."""
    dimension_id: str
    display_name: str
    type: str
    cardinality_baseline: int
    levels: list[Any]
    note: str = ""


class CartesianCoordinate(PfpBaseModel):
    """A single concrete point in the PFP Cartesian Product space."""
    task_family: str
    difficulty_rung: int = Field(ge=1)
    prompt_representation: str
    operational_mode: str
    stage_pipeline: str = Field(default="single_pass")
    rewrite_strategy: str = Field(default="none")
    gate_profile: str = Field(default="canonical_exact_rational")
    inoculation_status: str = Field(default="none")
    model_tier: str = Field(default="class_8b")
    decoding_control: str = Field(default="deterministic_t0")
    execution_channel: str = Field(default="offline_fixture")

    def coordinate_vector(self) -> tuple[str, int, str, str, str, str, str, str, str, str, str]:
        return (
            self.task_family,
            self.difficulty_rung,
            self.prompt_representation,
            self.operational_mode,
            self.stage_pipeline,
            self.rewrite_strategy,
            self.gate_profile,
            self.inoculation_status,
            self.model_tier,
            self.decoding_control,
            self.execution_channel,
        )


class SamplingSlice(PfpBaseModel):
    """Definition of an empirical sampling projection over the Cartesian space."""
    slice_id: str
    name: str
    pilot_count: int
    pilot_range: str = ""
    focus: str = ""
    constraints: dict[str, Any] = Field(default_factory=dict)


class CartesianMatrixSpace:
    """Manager and calculator for the PFP Cartesian Product matrix space."""

    _instance: CartesianMatrixSpace | None = None

    def __init__(self, register_path: Path | None = None) -> None:
        self._dimensions: dict[str, DimensionDefinition] = {}
        self._slices: dict[str, SamplingSlice] = {}
        self._register_path = register_path
        self._load_register()

    @classmethod
    def get_instance(cls, register_path: Path | None = None) -> CartesianMatrixSpace:
        if cls._instance is None:
            cls._instance = CartesianMatrixSpace(register_path=register_path)
        return cls._instance

    def _load_register(self) -> None:
        reg_file = self._register_path
        if reg_file is None:
            # Try multiple candidate locations
            candidates = [
                Path(__file__).parent.parent / "infrastructure" / "yaml" / "cartesian_matrix" / "cartesian_matrix_register.yaml",
                Path(__file__).parent.parent / "infrastructure" / "yaml_data" / "cartesian_matrix" / "cartesian_matrix_register.yaml",
                Path(__file__).parent / "cartesian_matrix_register.yaml",
            ]
            for c in candidates:
                if c.is_file():
                    reg_file = c
                    break
        if reg_file and reg_file.is_file():
            data = yaml.safe_load(reg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for d in data.get("dimensions", []):
                    try:
                        defn = DimensionDefinition.model_validate(d)
                        self._dimensions[defn.dimension_id] = defn
                    except Exception:
                        pass
                for s in data.get("sampling_slices", []):
                    try:
                        sl = SamplingSlice.model_validate(s)
                        self._slices[sl.slice_id] = sl
                    except Exception:
                        pass

    def compute_total_volume(self, custom_family_count: int | None = None) -> int:
        volume = 1
        for dim_id, dim in self._dimensions.items():
            if dim_id == "task_family" and custom_family_count is not None:
                volume *= custom_family_count
            else:
                volume *= max(1, len(dim.levels))
        return volume

    def dimension_names(self) -> list[str]:
        return list(self._dimensions.keys())

    def get_dimension(self, dim_id: str) -> DimensionDefinition | None:
        return self._dimensions.get(dim_id)

    def get_slice(self, slice_id: str) -> SamplingSlice | None:
        return self._slices.get(slice_id)

    def validate_coordinate(self, coord: CartesianCoordinate) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for dim_id, value in coord.model_dump().items():
            dim = self._dimensions.get(dim_id)
            if dim is None:
                continue
            if dim_id == "task_family":
                if not isinstance(value, str) or not value:
                    errors.append(f"task_family must be non-empty string, got {value!r}")
            elif dim_id == "difficulty_rung":
                if not isinstance(value, int) or value < 1:
                    errors.append(f"difficulty_rung must be positive int, got {value!r}")
            else:
                if value not in dim.levels:
                    errors.append(f"Invalid {dim_id}: {value!r}. Must be one of {dim.levels}")
        return len(errors) == 0, errors


# =============================================================================
# 16. TASK FAMILIES & OPEN DYNAMIC REGISTRY (task_families/)
# =============================================================================

class DomainCategory(str, Enum):
    SYMBOLIC_MATHEMATICS = "symbolic_mathematics"
    DISCRETE_STRUCTURES = "discrete_structures"
    FORMAL_LOGIC = "formal_logic"
    ALGORITHMIC_SEARCH = "algorithmic_search"
    PROGRAM_SYNTHESIS = "program_synthesis"
    NATURAL_LANGUAGE_REASONING = "natural_language_reasoning"
    CONSTRAINT_SATISFACTION = "constraint_satisfaction"
    DISCRETE_PHYSICS = "discrete_physics"
    PROTOCOL_VERIFICATION = "protocol_verification"
    EXTENSIONAL_PROMPT_DOMAIN = "extensional_prompt_domain"


class InputModality(str, Enum):
    PLAIN_PROSE = "plain_prose"
    MATHEMATICAL_NOTATION = "mathematical_notation"
    GRAPH_ADJACENCY = "graph_adjacency"
    RELATIONAL_TABLES = "relational_tables"
    FORMAL_CODE_AST = "formal_code_ast"
    SYMBOLIC_WIRE_PACKET = "symbolic_wire_packet"
    JSON_KV_RECORD = "json_kv_record"
    HIEROGLYPHIC_SEQUENCE = "hieroglyphic_sequence"
    CUSTOM_TEXT_PROMPT = "custom_text_prompt"


class SolutionModality(str, Enum):
    SCALAR_RATIONAL = "scalar_rational"
    DISCRETE_VECTOR_MATRIX = "discrete_vector_matrix"
    STRUCTURAL_GRAPH = "structural_graph"
    BOOLEAN_DECISION = "boolean_decision"
    REFUSAL_DECLARATION = "refusal_declaration"
    TYPED_SCHEMA_RECORD = "typed_schema_record"
    CODE_PATCH = "code_patch"
    LEAN4_PROOF_TERM = "lean4_proof_term"
    COCHAIN_POTENTIAL = "cochain_potential"
    ARBITRARY_MATCH = "arbitrary_match"


class EvaluationStrategy(str, Enum):
    EXACT_SCALAR_MATCH = "exact_scalar_match"
    DUAL_WITNESS_CIRCULATION = "dual_witness_circulation"
    ACYCLIC_POTENTIAL_GRADIENT = "acyclic_potential_gradient"
    ASSOCIATIVITY_COUNTEREXAMPLE = "associativity_counterexample"
    REFUSAL_TRUTH_TABLE = "refusal_truth_table"
    ORACLE_EXECUTION = "oracle_execution"
    LEAN4_KERNEL_ELABORATION = "lean4_kernel_elaboration"
    PROPERTY_TEST_SUITE = "property_test_suite"
    CUSTOM_PREDICATE = "custom_predicate"


class TaskFamilyDefinition(PfpBaseModel):
    family_id: str = Field(description="Unique slug identifier")
    display_name: str = Field(description="Human-readable title")
    domain_category: DomainCategory | str = Field(default=DomainCategory.EXTENSIONAL_PROMPT_DOMAIN)
    input_modality: InputModality | str = Field(default=InputModality.CUSTOM_TEXT_PROMPT)
    solution_modality: SolutionModality | str = Field(default=SolutionModality.TYPED_SCHEMA_RECORD)
    evaluation_strategy: EvaluationStrategy | str = Field(default=EvaluationStrategy.ORACLE_EXECUTION)
    checker_contract_id: str = Field(description="Identifier for verification oracle")
    supports_refusal: bool = Field(default=False)
    difficulty_metric: str = Field(default="order_or_size")
    default_rungs: dict[int, dict[str, Any]] = Field(default_factory=dict)
    is_extensional: bool = Field(default=True)
    description: str = Field(default="")

    @field_validator("family_id")
    @classmethod
    def validate_family_id(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]{1,63}$", v):
            raise ValueError(f"Invalid family_id: {v!r}. Must match '^[a-z][a-z0-9_]{{1,63}}$'")
        return v

    @field_validator("checker_contract_id")
    @classmethod
    def validate_checker_id(cls, v: str) -> str:
        if not re.match(r"^PFP-[0-9A-Z_-]+$", v):
            raise ValueError(f"Invalid checker_contract_id: {v!r}. Must match '^PFP-[0-9A-Z_-]+$'")
        return v


class TaskFamilyRegister(PfpBaseModel):
    schema_uri: str = Field(default="pfp.task-family-register.v1", alias="schema")
    authority_effect: str = Field(default="None")
    families: list[TaskFamilyDefinition] = Field(default_factory=list)


GroundTruthProvider = Callable[[int], dict[str, Any]]


class TaskFamilyRegistry:
    """Thread-safe catalog of bedrock and dynamically registered task families."""

    _instance: TaskFamilyRegistry | None = None

    def __init__(self, register_path: Path | None = None) -> None:
        self._families: dict[str, TaskFamilyDefinition] = {}
        self._ground_truth_providers: dict[str, GroundTruthProvider] = {}
        self._register_path = register_path
        self._load_canonical_register()

    @classmethod
    def get_instance(cls, register_path: Path | None = None) -> TaskFamilyRegistry:
        if cls._instance is None:
            cls._instance = TaskFamilyRegistry(register_path=register_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _load_canonical_register(self) -> None:
        reg_file = self._register_path
        if reg_file is None:
            candidates = [
                Path(__file__).parent.parent / "infrastructure" / "yaml" / "task_families" / "task_family_register.yaml",
                Path(__file__).parent.parent / "infrastructure" / "yaml_data" / "task_families" / "task_family_register.yaml",
                Path(__file__).parent / "task_family_register.yaml",
            ]
            for c in candidates:
                if c.is_file():
                    reg_file = c
                    break
        if reg_file and reg_file.is_file():
            data = yaml.safe_load(reg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "families" in data:
                for fam in data["families"]:
                    try:
                        defn = TaskFamilyDefinition.model_validate(fam)
                        self._families[defn.family_id] = defn
                    except Exception:
                        pass

    def register(self, definition: TaskFamilyDefinition) -> None:
        self._families[definition.family_id] = definition

    def register_simple(
        self,
        family_id: str,
        display_name: str,
        domain_category: str = "extensional_prompt_domain",
        checker_contract_id: str | None = None,
        supports_refusal: bool = False,
        description: str = "",
        ground_truth_provider: GroundTruthProvider | None = None,
    ) -> TaskFamilyDefinition:
        checker_id = checker_contract_id or f"PFP-EXT-{family_id.upper()}"
        defn = TaskFamilyDefinition(
            family_id=family_id,
            display_name=display_name,
            domain_category=domain_category,
            checker_contract_id=checker_id,
            supports_refusal=supports_refusal,
            is_extensional=True,
            description=description,
        )
        self.register(defn)
        if ground_truth_provider is not None:
            self.register_ground_truth_provider(family_id, ground_truth_provider)
        return defn

    def register_ground_truth_provider(
        self,
        family_id: str,
        provider: GroundTruthProvider,
    ) -> None:
        self._ground_truth_providers[family_id] = provider

    def get_ground_truth(self, family_id: str, difficulty_rung: int = 1) -> dict[str, Any] | None:
        provider = self._ground_truth_providers.get(family_id)
        if provider is not None:
            return provider(difficulty_rung)
        return None

    def get(self, family_id: str) -> TaskFamilyDefinition | None:
        return self._families.get(family_id)

    def is_valid_family(self, family_id: str) -> bool:
        return family_id in self._families

    def all_family_ids(self) -> frozenset[str]:
        return frozenset(self._families.keys())

    def list_families(self) -> list[TaskFamilyDefinition]:
        return list(self._families.values())


# =============================================================================
# 17. SYMBOLIC WIRE SYNTAX PROFILES (wires/)
# =============================================================================

class TokenLegend(PfpBaseModel):
    profile_name: str = Field(min_length=1)
    tokens: dict[str, str] = Field(default_factory=dict)
    delimiters: dict[str, str] = Field(default_factory=dict)


class WireSyntaxProfile(PfpBaseModel):
    profile_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: str = "1.0.0"
    tier: str = Field(min_length=1)
    allowed_tokens: list[str] = Field(default_factory=list)
    max_expression_depth: int = Field(ge=1)
    max_tokens_count: int = Field(ge=1)
    token_legend: TokenLegend


SyntaxProfile = WireSyntaxProfile


# =============================================================================
# 18. STAGE TRANSITION & RETRACTION CONTRACTS (contracts/)
# =============================================================================

class ContractPrecondition(PfpBaseModel):
    name: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    description: str = ""


class ContractPostcondition(PfpBaseModel):
    name: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    description: str = ""


class StageTransitionContract(PfpBaseModel):
    contract_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    version: str = "1.0.0"
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    entry_preconditions: list[ContractPrecondition] = Field(default_factory=list)
    exit_postconditions: list[ContractPostcondition] = Field(default_factory=list)
    invariants: list[str] = Field(default_factory=list)
    winning_condition: str = ""
    failure_modes: list[str] = Field(default_factory=list)


# =============================================================================
# 19. EXTENDED QUADRILATERAL NORMAL FORMS (nf/)
# =============================================================================

class QuadrilateralBlock(PfpBaseModel):
    contract: str = Field(default="")
    properties: dict[str, Any] = Field(default_factory=dict)
    invariants: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)


class ExtendedNormalFormContract(PfpBaseModel):
    schema_ref: str = Field(default="standard.yaml")
    contract_type: str = Field(default="extended_normal_form_contract")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    identity: PfpNormalFormContractIdentity
    quadrilateral: QuadrilateralBlock = Field(default_factory=lambda: QuadrilateralBlock())
    extensions: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# CANONICAL ERGONOMIC ALIASES
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

__all__ = [
    "PfpBaseModel",
    "PfpAuthorityEffect",
    "AuthorityEffect",
    "TaskFamily",
    "ExecutionMode",
    "TrialStatus",
    "EvaluationStatus",
    "ConstraintType",
    "Operatorizability",
    "RuntimeAction",
    "Severity",
    "TaskModeFidelity",
    "VariableIdentifierPermutation",
    "FloatingPointRisk",
    "ArmTemplate",
    "MissingPremise",
    "CohomologyDefectClass",
    "MagmaAssociativityType",
    "CheckerId",
    "StructureDeltaMetric",
    "RepresentationRewrite",
    "ModelClass",
    "PilotCoordinates",
    "PilotIngress",
    "PilotHostGate",
    "PilotSpec",
    "PromptResponsePayload",
    "SanitizationReport",
    "EvaluationReceipt",
    "PilotResponse",
    "GuidanceSlot",
    "RuleSlot",
    "AntibodySlot",
    "AntipatternSlot",
    "HelpfulPatternSlot",
    "PromptLineageSlot",
    "NegativeMutationFixture",
    "PromptTemplate",
    "PStarPrompt",
    "PfpMss0GrammarConstraint",
    "PfpOpSemantics",
    "PfpMss0Level",
    "PfpMss0TypingRules",
    "PfpEvaluatorBinding",
    "PfpEvaluatorScopeRule",
    "PfpEvidenceLevel",
    "PfpClaimHygiene",
    "PfpSemanticPolicyManifest",
    "SystemPromptManifest",
    "ExpectedOutcome",
    "SeedPrompt",
    "PfpArithmeticDomain",
    "ArithmeticDomain",
    "PfpClaimedMove",
    "ClaimedMove",
    "PfpVerificationRule",
    "VerificationRule",
    "PfpVerificationStatus",
    "VerificationStatus",
    "PfpStaticCellBounds",
    "StaticCellBounds",
    "PfpEdge",
    "Edge",
    "PfpFace",
    "Face",
    "PfpCarrier",
    "Carrier",
    "PfpBoundaryMatrices",
    "BoundaryMatrices",
    "PfpActiveObstruction",
    "ActiveObstruction",
    "PfpCycleBalanceProblem",
    "CycleBalanceProblem",
    "PfpCycleBalanceCandidate",
    "CycleBalanceCandidate",
    "PfpCycleBalanceVerifier",
    "CycleBalanceVerifier",
    "PfpCycleBalanceReceipt",
    "CycleBalanceReceipt",
    "PfpCycleBalanceQuartet",
    "CycleBalanceQuartet",
    "PfpAllowedTransform",
    "AllowedTransform",
    "PfpFramingMode",
    "FramingMode",
    "PfpEvidenceCeiling",
    "EvidenceCeiling",
    "PfpOraclePolicy",
    "OraclePolicy",
    "PfpPacketKind",
    "PacketKind",
    "PfpNextWorkItem",
    "NextWorkItem",
    "PfpFableLongHorizonTaskPacket",
    "FableLongHorizonTaskPacket",
    "PfpModeCluster",
    "ModeCluster",
    "PfpModeCatalogEntry",
    "ModeCatalogEntry",
    "PfpModeCatalog",
    "ModeCatalog",
    "PfpVerifierContract",
    "VerifierContract",
    "PfpModeFile",
    "ModeFile",
    "PfpClusterEntry",
    "ClusterEntry",
    "PfpClusterIndex",
    "ClusterIndex",
    "PfpManifestMode",
    "ManifestMode",
    "PfpNfFamily",
    "NfFamily",
    "PfpNfIndexEntry",
    "NfIndexEntry",
    "PfpNfDomainIndex",
    "NfDomainIndex",
    "PfpNormalFormContractIdentity",
    "NormalFormContractIdentity",
    "PfpNormalFormClassification",
    "NormalFormClassification",
    "PfpNormalFormContract",
    "NormalFormContract",
    "PfpSpanRole",
    "SpanRole",
    "PfpByteSpan",
    "ByteSpan",
    "PfpSpanPartition",
    "SpanPartition",
    "PfpBoundaryWire",
    "BoundaryWire",
    "PfpSymbolMapping",
    "SymbolMapping",
    "PfpRewritingContract",
    "RewritingContract",
    "PfpEnvelopeSchemaEntry",
    "EnvelopeSchemaEntry",
    "PfpGrammarSchemaEntry",
    "GrammarSchemaEntry",
    "PfpSchemaRegister",
    "SchemaRegister",
    "PfpStageName",
    "StageName",
    "PfpStageExecutor",
    "StageExecutor",
    "PfpStageInputContract",
    "StageInputContract",
    "PfpStageFile",
    "StageFile",
    "PfpStageReference",
    "StageReference",
    "PfpStageController",
    "StageController",
    "PfpModuleWorld",
    "ModuleWorld",
    "PfpModuleSource",
    "ModuleSource",
    "PfpYamlRole",
    "YamlRole",
    "PfpModuleStatus",
    "ModuleStatus",
    "PfpYamlRef",
    "YamlRef",
    "PfpModuleRow",
    "ModuleRow",
    "PfpTypeRegister",
    "TypeRegister",
    "ComparisonOperator",
    "PrimaryGate",
    "Intergate",
    "EmpiricalGate",
    "GateRegister",
    "gate_ordinal",
    "load_register_from_files",
    "DimensionDefinition",
    "CartesianCoordinate",
    "SamplingSlice",
    "CartesianMatrixSpace",
    "DomainCategory",
    "InputModality",
    "SolutionModality",
    "EvaluationStrategy",
    "TaskFamilyDefinition",
    "TaskFamilyRegister",
    "TaskFamilyRegistry",
    "GroundTruthProvider",
    "TokenLegend",
    "WireSyntaxProfile",
    "SyntaxProfile",
    "ContractPrecondition",
    "ContractPostcondition",
    "StageTransitionContract",
    "QuadrilateralBlock",
    "ExtendedNormalFormContract",
]
