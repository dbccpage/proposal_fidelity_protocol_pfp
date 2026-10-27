"""Strict opt-in wires for the 22 existing primary native predicates.

Absent evidence is retained as absent (and may HOLD). Supplied known evidence is
typed. These models do not authenticate host observations, evaluate mathematics,
or replace the permissive historical refusal reader. Exact wire bytes remain the
native validator's input; serialization must use ``exclude_unset=True``.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Annotated, Generic, Literal, TypeVar, Union

from pydantic import (
    AfterValidator, BaseModel, BeforeValidator, ConfigDict, Discriminator,
    Field, JsonValue, StrictBool, StrictFloat, StrictInt, Tag, TypeAdapter,
    model_validator,
)

TYPED_GATE_CONTRACT_VERSION = "adversary.primary-gate-contracts.v1"


def _boolean(value):
    if type(value) is not bool:
        raise ValueError("require a JSON boolean")
    return value


def _integer(value):
    if type(value) is not int:
        raise ValueError("require a JSON integer")
    return value


def _exact_text(value: str) -> str:
    if not re.fullmatch(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?", value.strip()):
        raise ValueError("require an exact integer or rational string")
    return value


def _canonical(value: str) -> str:
    _exact_text(value)
    if str(Fraction(value)) != value:
        raise ValueError("require the native canonical rational spelling")
    return value


def _metric_text(value: str) -> str:
    # Mirror the owning stage decimal telemetry grammar without converting or
    # rounding the caller's wire spelling. Cochains use the narrower exact type.
    raw = value.strip()
    if "/" in raw:
        parts = raw.split("/")
        if len(parts) != 2 or any(not re.fullmatch(r"[+-]?[0-9]+", part.strip()) for part in parts):
            raise ValueError("invalid rational telemetry")
        if not parts[1].strip().lstrip("+-").strip("0"):
            raise ValueError("zero telemetry denominator")
    else:
        match = re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE]([+-]?[0-9]+))?", raw)
        if match is None:
            raise ValueError("invalid decimal telemetry")
        exponent_text = match.group(1) or "0"
        if len(exponent_text.lstrip("+-")) > 10:
            raise ValueError("telemetry exponent outside native bound")
        exponent = int(exponent_text)
        mantissa = re.split("[eE]", raw)[0]
        scale = len(mantissa.split(".", 1)[1]) if "." in mantissa else 0
        if not -2147483648 <= exponent <= 2147483647 or abs(scale - exponent) > 10000:
            raise ValueError("telemetry exponent outside native bound")
    return value


def _pair(value):
    if type(value) is not list or len(value) != 2:
        raise ValueError("require a two-element JSON array")
    return tuple(value)


def _finite_opaque(value):
    """Only genuinely opaque cell labels/invariant maps use this JSON carrier."""
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite JSON")
    if isinstance(value, dict):
        for item in value.values():
            _finite_opaque(item)
    elif isinstance(value, list):
        for item in value:
            _finite_opaque(item)
    return value


Text = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
BareSha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
UInt = Annotated[StrictInt, Field(ge=0)]
U64 = Annotated[UInt, Field(le=18446744073709551615)]
I64 = Annotated[StrictInt, Field(ge=-9223372036854775808, le=9223372036854775807)]
TrueFlag = Annotated[Literal[True], BeforeValidator(_boolean)]
FalseFlag = Annotated[Literal[False], BeforeValidator(_boolean)]
Zero = Annotated[Literal[0], BeforeValidator(_integer)]
Three = Annotated[Literal[3], BeforeValidator(_integer)]
ExactText = Annotated[str, AfterValidator(_exact_text)]
ExactScalar = StrictInt | ExactText
CanonicalQ = Annotated[str, AfterValidator(_canonical)]
Metric = StrictInt | StrictFloat | Annotated[str, AfterValidator(_metric_text)]
HexBytes = Annotated[str, Field(pattern=r"^(?:[0-9a-f]{2})*$", max_length=131072)]
PublicKeyHex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
SignatureHex = Annotated[str, Field(pattern=r"^[0-9a-f]{128}$")]
Vector = Annotated[list[ExactScalar], Field(max_length=128)]
Matrix = Annotated[list[Vector], Field(max_length=128)]
Pair = Annotated[tuple[Text, Text], BeforeValidator(_pair)]
HashPair = Annotated[tuple[Text, Sha256], BeforeValidator(_pair)]
AxiomPair = Annotated[tuple[Text, list[Text]], BeforeValidator(_pair)]
Opaque = Annotated[JsonValue, AfterValidator(_finite_opaque)]


class Wire(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)


class Scene(Wire):
    run_id: Text
    initial_task_id: Text
    action_id: Text
    workflow_version: Text
    stage: Text
    candidate_sha256: BareSha256
    objective_sha256: BareSha256
    artifacts_sha256: BareSha256
    plan_sha256: BareSha256
    check_source_id: Text
    check_source_paths_sha256: BareSha256
    source_reads_sha256: BareSha256
    native_gate_check_sha256: BareSha256
    host_observations_sha256: BareSha256
    prior_native_receipts_sha256: BareSha256
    gate_id: Text | None = None
    visit_index: UInt | None = None


class Payload(Wire):
    scene: Scene | None = Field(default=None, alias="_adversary_scene")


class Carrier(Wire):
    # The native complex uses these ordered arrays only for their cardinalities.
    vertices: Annotated[list[Opaque], Field(max_length=64)]
    edges: Annotated[list[Opaque], Field(max_length=128)]
    faces: Annotated[list[Opaque], Field(max_length=64)]


class CochainPayload(Payload):
    carrier: Carrier | None = None
    omega: Vector | None = None
    d0: Matrix | None = None
    d1: Matrix | None = None


class SyntaxPrefilterPayload(CochainPayload):
    packet_id: Text | None = None
    is_admitted: StrictBool | None = None
    candidate_content: Text | None = None


class GaugeBreakerPayload(Payload):
    round_number: UInt | None = None
    residual_history: Vector | None = None
    lift_requested: StrictBool | None = None


class ScopeGuardPayload(Payload):
    round_number: UInt | None = None
    vertex_count: UInt | None = None
    edge_count: UInt | None = None
    face_count: UInt | None = None
    estimated_cost_usd: Metric | None = None
    wire_packet_utf8: Text | None = None


class BackdoorAuditorPayload(CochainPayload):
    core_types: list[Text] | None = None
    random_seed_declared: StrictBool | None = None
    random_seed: UInt | None = None
    solver_method: Text | None = None


class TieBreakCertificate(Wire):
    upper: Vector
    lower: Vector
    prefix: Vector
    norm_multiplier: ExactScalar


class PrimalDualPayload(CochainPayload):
    alpha: Vector | None = None
    dual_witness: Vector | None = None
    ordered_basis: list[UInt] | None = None
    tie_break_certificates: list[TieBreakCertificate] | None = None
    phi1: ExactScalar | None = None
    gamma2: ExactScalar | None = None


class ProofExecution(Wire):
    exit_code: StrictInt
    artifact_sha256: Sha256
    claim_sha256: Sha256
    log_utf8: Text
    log_sha256: Sha256


class MasterLegacyPayload(Payload):
    claim_statement: Text | None = None
    has_mechanized_proof: StrictBool | None = None
    proof_kernel: Text | None = None
    proof_artifact_utf8: Text | None = None
    proof_artifact_sha256: Sha256 | None = None
    proof_execution: ProofExecution | None = None


class Scar(Wire):
    candidate_hash: Sha256
    obstruction_id: Text


class ScarChroniclerPayload(Payload):
    candidate_hash: Sha256 | None = None
    candidate_content: Text | None = None
    prior_scar_ledger: list[Scar] | None = None
    active_obstruction_id: Text | None = None
    repair_targets: list[Text] | None = None


class AntiHypePayload(Payload):
    candidate_prose: Text | None = None
    claim_tier: UInt | None = None
    receipt_attached: StrictBool | None = None
    receipt_utf8: Text | None = None
    receipt_sha256: Sha256 | None = None
    claim_scope: list[Text] | None = None
    evidence_scope: list[Text] | None = None


class Perturbation(Wire):
    edge_permutation: list[UInt]
    edge_signs: Vector
    omega: Vector
    d0: Matrix
    d1: Matrix


class BoundaryFuzzerPayload(PrimalDualPayload):
    fuzz_iterations: UInt | None = None
    perturbations: list[Perturbation] | None = None


class QuarantinePayload(Payload):
    agent_state: Text | None = None
    observed_behavior: Text | None = None
    cycle_count: UInt | None = None
    residual_descent_observed: StrictBool | None = None


class IntegrityAuditorPayload(Payload):
    pipeline_stage: UInt | None = None
    prior_stage_status: Text | None = None
    has_mock_injection: StrictBool | None = None
    skipped_checks: list[Text] | None = None
    suppressed_errors: list[Text] | None = None


class AdversaryPayload(PrimalDualPayload):
    packet_id: Text | None = None
    is_refused: StrictBool | None = None
    refusal_code: Text | None = None
    checker_receipt_hex: HexBytes | None = None
    checker_receipt_verdict: Text | None = None
    candidate_content: Text | None = None


class ContextTransportCommon(Payload):
    snapshot_id: Text | None = None
    origin_checksum: Sha256 | None = None
    payload_checksum: Sha256 | None = None
    origin_coordinates: list[Text] | None = None
    retained_coordinates: list[Text] | None = None
    dropped_coordinates: list[Text] | None = None
    serialization_profile: Text | None = None
    transport_scope: Text | None = None


class ContextTransportLegacyPayload(ContextTransportCommon):
    origin_payload_utf8: Text | None = None
    payload_utf8: Text | None = None


class ContextTransportPoolPayload(ContextTransportCommon):
    transport_profile: Literal["adversary.pfp-transport-pool.v2"]
    payload_pool_utf8: Annotated[list[Text], Field(min_length=1, max_length=2)] | None = None
    origin_payload_index: Zero | None = None
    payload_index: Annotated[UInt, Field(le=1)] | None = None

    @model_validator(mode="after")
    def pool_indices(self):
        pool = self.payload_pool_utf8
        if pool is not None:
            if len(set(pool)) != len(pool):
                raise ValueError("duplicate pool entries")
            if self.payload_index is not None and self.payload_index >= len(pool):
                raise ValueError("payload index outside retained pool")
            if len(pool) == 2 and self.payload_index == 0:
                raise ValueError("unreferenced extra pool entry")
        return self


class BareMetalAnchorLegacyPayload(Payload):
    candidate_id: Text | None = None
    has_executable_test: StrictBool | None = None
    runtime_exit_code: StrictInt | None = None
    abstract_bloat_score: Metric | None = None
    has_mock_injection: StrictBool | None = None
    executable_utf8: Text | None = None
    executable_sha256: Sha256 | None = None
    execution_log_utf8: Text | None = None
    execution_log_sha256: Sha256 | None = None
    observed_executable_sha256: Sha256 | None = None


class ResiliencePayload(Payload):
    crisis_severity: Text | None = None
    core_state_intact: StrictBool | None = None
    recovery_attempts: UInt | None = None
    recovery_budget: UInt | None = None
    core_before_utf8: Text | None = None
    core_before_sha256: Sha256 | None = None
    core_after_utf8: Text | None = None
    core_after_sha256: Sha256 | None = None
    fallback_utf8: Text | None = None
    fallback_sha256: Sha256 | None = None


class OverconfidenceProbePayload(Payload):
    candidate_id: Text | None = None
    self_confidence_score: Metric | None = None
    machine_receipt_present: StrictBool | None = None
    detected_circularities: list[Text] | None = None
    machine_receipt_utf8: Text | None = None
    machine_receipt_sha256: Sha256 | None = None


class Obligation(Wire):
    id: Text
    status: Text
    dependencies: list[Text]
    artifact_utf8: Text
    artifact_sha256: Sha256
    receipt_utf8: Text
    receipt_sha256: Sha256


class PunchlistPayload(Payload):
    task_list_id: Text | None = None
    open_obligations_count: UInt | None = None
    certified_receipts: list[Text] | None = None
    obligations: list[Obligation] | None = None


class ChainEntry(Wire):
    record_utf8: Text
    record_sha256: Sha256


class CitationArtifact(Wire):
    citation_id: Text
    content_utf8: Text
    content_sha256: Sha256


class LevyPayload(Payload):
    journal_chain_root: Sha256 | None = None
    observed_tip_hash: Sha256 | None = None
    citations: list[Text] | None = None
    chain_entries: list[ChainEntry] | None = None
    citation_artifacts: list[CitationArtifact] | None = None


class CovertVerifierLegacyPayload(Payload):
    task_id: Text | None = None
    reported_status: Text | None = None
    os_exit_code: StrictInt | None = None
    process_terminated: StrictBool | None = None
    log_output_utf8: Text | None = None
    log_output_hash: Sha256 | None = None


class TruthRepairPayload(Payload):
    candidate_id: Text | None = None
    detected_defect: Text | None = None
    proposed_repair: dict[str, Opaque] | None = None
    invariants_preserved: StrictBool | None = None
    sibling_invariants_before: dict[str, Opaque] | None = None
    sibling_invariants_after: dict[str, Opaque] | None = None
    original_fences: dict[str, Opaque] | None = None
    repaired_fences: dict[str, Opaque] | None = None
    checker_receipt_hex: HexBytes | None = None
    checker_receipt_verdict: Text | None = None
    candidate_content: Text | None = None


class HardwareConstraintLegacyPayload(Payload):
    task_pid: UInt | None = None
    elapsed_seconds: Metric | None = None
    timeout_ceiling_seconds: Metric | None = None
    resident_memory_bytes: UInt | None = None
    memory_limit_bytes: UInt | None = None


class EvidenceBinding(Wire):
    spec_id: Text
    scope: Text
    rule_digest: Sha256
    source_digest: Sha256
    subject_digest: Sha256
    context_digest: Sha256


class TrustedKey(Wire):
    issuer: Text
    key_id: Text
    public_key_hex: PublicKeyHex
    purposes: list[Literal["admission", "health", "observation"]]
    scopes: list[Text]
    not_before: U64
    not_after: U64
    max_lifetime_seconds: U64
    revoked: StrictBool
    observer_source_digest: Sha256 | None = None


class TrustPolicy(Wire):
    schema_version: Literal["core.eis.trust-policy.v1"]
    trust_domain: Text
    keys: list[TrustedKey]


class Attestation(Wire):
    schema_version: Literal["core.eis.signed-attestation.v1"]
    trust_domain: Text
    purpose: Literal["admission", "health", "observation"]
    issuer: Text
    key_id: Text
    event_id: Text
    binding: EvidenceBinding
    issued_at: U64
    expires_at: U64
    outcome: Text
    previous_event: Text | None
    evidence_digest: Sha256
    signature_hex: SignatureHex


class ObservedEvidence(Wire):
    schema_version: Literal["core.eis.observed-evidence.v1"]
    observer_id: Text
    run_id: Text
    subject_digest: Sha256
    source_digest: Sha256
    outcome: Text


def _decode_model(hex_text: str, model):
    # Reuse the strict retained-JSON decoder; never canonicalize signed bytes.
    from adversary.domain.native_gate_check import decode_native_json
    try:
        decoded = bytes.fromhex(hex_text).decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid retained UTF-8 record") from exc
    return model.model_validate(decode_native_json(decoded))


class SignedEvidence(Wire):
    attestation: Attestation
    evidence_hex: HexBytes

    @model_validator(mode="after")
    def observation_shape(self):
        _decode_model(self.evidence_hex, ObservedEvidence)
        return self


class ProcessExpected(Wire):
    run_id: Text
    task_id: Text
    action_id: Text
    source_digest: Sha256
    candidate_sha256: Sha256
    checker_id: Text
    requested_argv: list[str]
    argv: list[str]
    executable_path: Text
    executable_sha256: Sha256
    checker_source_paths: list[HashPair]
    artifacts: list[HashPair]
    observer_source_digest: Sha256


class ProcessRecord(ProcessExpected):
    schema_version: Literal["adversary.host-process.v1"]
    stdout_hex: HexBytes
    stdout_sha256: Sha256
    stderr_hex: HexBytes
    stderr_sha256: Sha256
    exit_code: I64
    direct_child_completed: StrictBool
    shell: StrictBool
    started_at_ms: U64
    completed_at_ms: U64
    authority_effect: Literal["None"]


class ProcessEnvelope(Wire):
    record_hex: HexBytes
    signed: SignedEvidence

    @model_validator(mode="after")
    def record_shape(self):
        _decode_model(self.record_hex, ProcessRecord)
        return self


class ProcessPayload(Payload):
    process_profile: Literal["adversary.host-process.v1"]
    process_observation: ProcessEnvelope | None = None
    process_expected: ProcessExpected | None = None
    process_trust_policy: TrustPolicy | None = None
    now: U64 | None = None


class KernelContext(Wire):
    run_id: Text
    task_id: Text
    action_id: Text
    source_digest: Sha256
    candidate_sha256: Sha256
    proof_artifact_path: Text
    proof_artifact_sha256: Sha256
    checker_id: Text
    required_declarations: list[Pair]
    axiom_policy: list[Text]
    toolchain_pin: Text
    lake_binary_path: Text
    lake_binary_sha256: Sha256


class LakeProcess(Wire):
    label: Text
    argv: list[str]
    cwd: Text
    exit_code: I64 | None
    stdout_hex: HexBytes | None
    stdout_sha256: Sha256 | None
    stderr_hex: HexBytes | None
    stderr_sha256: Sha256 | None
    started_at_ms: U64
    completed_at_ms: U64 | None
    direct_child_completed: StrictBool
    shell: StrictBool


class LeanReceipt(Wire):
    status: Text
    build_success: StrictBool
    harness_elaborated: StrictBool
    refusal_code: Text | None
    axioms: list[AxiomPair]


class LakeReceipt(Wire):
    schema_version: Literal["core.adversary.lake-check.v2"]
    authority_effect: Literal["None"]
    run_key: Text
    candidate_id: Text
    candidate_content_sha256: Sha256
    candidate_content_hex: HexBytes
    lean_source_sha256: Sha256
    lean_source_hex: HexBytes
    extraction_profile: Text
    objective_sha256: Sha256
    checker_id: Text
    toolchain_pin: Text
    lake_binary_path: Text
    lake_binary_sha256: Sha256
    required_declarations: list[Pair]
    axiom_policy: list[Text]
    package_manifest: list[HashPair]
    harness_source_hex: HexBytes
    harness_source_sha256: Sha256
    processes: list[LakeProcess]
    lean_receipt: LeanReceipt
    verdict: Text
    reason: Text


class KernelRecord(Wire):
    schema_version: Literal["adversary.host-lean.v1"]
    context: KernelContext
    lake_receipt_hex: HexBytes
    observer_source_digest: Sha256
    authority_effect: Literal["None"]

    @model_validator(mode="after")
    def receipt_shape(self):
        _decode_model(self.lake_receipt_hex, LakeReceipt)
        return self


class KernelEnvelope(Wire):
    record_hex: HexBytes
    signed: SignedEvidence

    @model_validator(mode="after")
    def record_shape(self):
        _decode_model(self.record_hex, KernelRecord)
        return self


class KernelPayload(Payload):
    kernel_profile: Literal["adversary.host-lean.v1"]
    kernel_observation: KernelEnvelope | None = None
    kernel_expected: KernelContext | None = None
    kernel_trust_policy: TrustPolicy | None = None
    now: U64 | None = None


class ResourceConfiguration(Wire):
    timeout_ms: U64
    memory_limit_bytes: U64
    schema_version: Literal["adversary.resource-check-config.v1"] | None = None
    sandbox_binary_path: Text | None = None
    sandbox_binary_sha256: BareSha256 | None = None
    max_output_bytes: U64 | None = None


class ResourceContext(Wire):
    run_id: Text
    task_id: Text
    source_digest: Text
    checker_id: Text
    candidate_sha256: Text
    configuration: ResourceConfiguration
    requested_argv: list[str] | None = None
    artifacts: dict[str, str] | None = None


class ResourceMeasurements(Wire):
    task_pid: U64 | None
    elapsed_ms: U64
    memory_metric: Text
    memory_bytes: U64 | None
    measurement_error: Text | None
    isolation_applied: StrictBool


class ResourceObservation(Wire):
    context: ResourceContext
    action_id: Text
    failure_code: Text | None
    native_outcome: Text | None
    measurements: ResourceMeasurements | None
    native_result_sha256: BareSha256 | None


class ResourcePayload(Payload):
    resource_profile: Literal["adversary.host-job-resources.v1"]
    resource_expected: ResourceContext | None = None
    resource_observation: ResourceObservation | None = None


def _profile_selector(field: str):
    def selected(value):
        return "profile" if (field in value if isinstance(value, dict) else hasattr(value, field)) else "legacy"
    return selected


MasterPayload = Annotated[Union[Annotated[MasterLegacyPayload, Tag("legacy")],
                                 Annotated[KernelPayload, Tag("profile")]], Discriminator(_profile_selector("kernel_profile"))]
BareMetalAnchorPayload = Annotated[Union[Annotated[BareMetalAnchorLegacyPayload, Tag("legacy")],
                                 Annotated[ProcessPayload, Tag("profile")]], Discriminator(_profile_selector("process_profile"))]
CovertVerifierPayload = Annotated[Union[Annotated[CovertVerifierLegacyPayload, Tag("legacy")],
                                   Annotated[ProcessPayload, Tag("profile")]], Discriminator(_profile_selector("process_profile"))]
ContextTransportPayload = Annotated[Union[Annotated[ContextTransportLegacyPayload, Tag("legacy")],
                                  Annotated[ContextTransportPoolPayload, Tag("profile")]], Discriminator(_profile_selector("transport_profile"))]
HardwareConstraintPayload = Annotated[Union[Annotated[HardwareConstraintLegacyPayload, Tag("legacy")],
                                    Annotated[ResourcePayload, Tag("profile")]], Discriminator(_profile_selector("resource_profile"))]


class SyntaxPrefilterWitness(Wire):
    admission_precedes_measurement: TrueFlag
    boundary_nilpotency_checked: TrueFlag


class DefectHunterWitness(Wire):
    gamma2: Literal["0"]
    checked_face_flux: list[CanonicalQ]


class GaugeBreakerWitness(Wire):
    stagnation_triggered: FalseFlag
    lift_applied: FalseFlag


class ScopeGuardWitness(Wire):
    estimated_cost_usd: CanonicalQ
    wire_bytes: UInt
    billed_cost_verified: FalseFlag


class BackdoorAuditorWitness(Wire):
    exact_values_checked: UInt


class PrimalDualWitness(Wire):
    phi1: CanonicalQ
    gamma2: CanonicalQ
    primal_dual_gap: Literal["0"]
    tier_verified: TrueFlag
    residual: list[CanonicalQ]


class KernelAudit(Wire):
    required_declarations: list[Pair]
    axiom_policy: list[Text]
    axioms: dict[str, list[Text]]
    proof_artifact_sha256: Sha256
    lean_source_sha256: Sha256
    toolchain_pin: Text
    lake_binary_sha256: Sha256
    completed_processes: Three


class KernelWitness(Wire):
    kernel_profile: Literal["adversary.host-lean.v1"]
    record_sha256: Sha256
    run_id: Text
    task_id: Text
    action_id: Text
    candidate_sha256: Sha256
    checker_id: Text
    audit: KernelAudit
    sandbox_verified: FalseFlag
    general_theorem_verified: FalseFlag


class ScarChroniclerWitness(Wire):
    known_candidate_replay: FalseFlag
    ledger_custody: Literal["owning_journal_port"]


class AntiHypeWitness(Wire):
    claim_tier_preserved: Literal["1", "2", "3", "4"]
    scope_relation_verified: TrueFlag
    natural_language_truth_verified: FalseFlag
    keyword_matches_alone_determine_tier: FalseFlag


class BoundaryFuzzerWitness(Wire):
    finite_perturbations_verified: UInt
    baseline_primal_dual: PrimalDualWitness
    scope: Literal["declared signed edge permutations"]


class QuarantineWitness(Wire):
    typed_state: Literal["ready", "stable", "running", "recovering", "halted"]
    ddc_letter_m_required: FalseFlag


class IntegrityAuditorWitness(Wire):
    upstream_success_preserved: TrueFlag


class AdversaryWitness(Wire):
    cochain_class: Literal["OpenObstruction", "StabilizedSurvivor", "Exact"]
    replayed_witnesses: PrimalDualWitness
    checker_authentication: Literal["owning_checker_port"]
    classification_is_not_execution_authority: TrueFlag


class ContextTransportLegacyWitness(Wire):
    lossless_bytes_verified: TrueFlag
    coordinates_verified: UInt


class ContextTransportPoolWitness(ContextTransportLegacyWitness):
    transport_profile: Literal["adversary.pfp-transport-pool.v2"]


ContextTransportWitness = Annotated[Union[Annotated[ContextTransportLegacyWitness, Tag("legacy")],
                                  Annotated[ContextTransportPoolWitness, Tag("profile")]], Discriminator(_profile_selector("transport_profile"))]


class ProcessWitness(Wire):
    process_profile: Literal["adversary.host-process.v1"]
    run_id: Text
    task_id: Text
    action_id: Text
    record_sha256: Sha256
    candidate_sha256: Sha256
    checker_id: Text
    executable_sha256: Sha256
    stdout_sha256: Sha256
    stderr_sha256: Sha256
    exit_code: Zero
    direct_child_completed: TrueFlag
    process_tree_verified: FalseFlag
    sandbox_verified: FalseFlag
    scope: Literal["configured owning host observed this exact waited command; no general program-safety or semantic-correctness proof"]


class ResilienceWitness(Wire):
    core_bytes_preserved: TrueFlag
    recovery_within_budget: TrueFlag


class OverconfidenceProbeWitness(Wire):
    confidence: CanonicalQ
    gauge_rotation_required: FalseFlag


class PunchlistWitness(Wire):
    closed_obligations: UInt
    dependency_order_verified: TrueFlag


class LevyWitness(Wire):
    verified_entries: UInt
    verified_tip: Sha256
    profile: Literal["raw-record-utf8-sha256-prev-field-v1"]
    tip_authentication: Literal["independently_retained_host_input"]


class TruthRepairWitness(Wire):
    declared_fences_preserved: TrueFlag
    declared_siblings_preserved: TrueFlag
    finite_repair_checker_bytes_bound: TrueFlag


class HardwareConstraintLegacyWitness(Wire):
    observed_resources_within_envelope: TrueFlag
    process_termination_owner: Literal["host_process_port"]


class ResourceWitness(Wire):
    resource_profile: Literal["adversary.host-job-resources.v1"]
    memory_metric: Literal["windows_job_peak_committed_bytes"]
    observed_resources_within_envelope: TrueFlag
    observation_authenticated: FalseFlag
    scope: Literal["finite host-captured Windows job measurements; not RSS or descendant termination attestation"]


HardwareConstraintWitness = Annotated[Union[Annotated[HardwareConstraintLegacyWitness, Tag("legacy")],
                                    Annotated[ResourceWitness, Tag("profile")]], Discriminator(_profile_selector("resource_profile"))]

P = TypeVar("P")
W = TypeVar("W")


class GateRequest(Wire, Generic[P]):
    operation: Literal["gate_evaluate"]
    payload: P
    history_edges: list[Text] = Field(default_factory=list)


class GateReceipt(Wire, Generic[W]):
    wire_schema: Literal["adversary.pfp.gate-receipt.v1"] = Field(alias="schema")
    status: Literal["PASS", "HOLD", "REFUSE"]
    refusal_code: Text | None
    diagnostics: Text
    witness: W | None
    input_sha256: Sha256
    input_digest_profile: Literal["python-sorted-spaced-ascii-json-v1"]
    specification_sha256: Sha256
    authority_effect: Literal["None"]
    can_authorize: FalseFlag
    observation_authentication: Literal["owning_host_ports", "configured_owning_host_signature", "not_admitted", "unsigned_host_capture"]
    general_theorem_verified: FalseFlag
    diagnostic_only: TrueFlag
    scope: Text

    @model_validator(mode="after")
    def outcome_shape(self):
        if self.status == "PASS":
            consistent = self.refusal_code is None and self.witness is not None
        elif self.status == "HOLD":
            consistent = self.refusal_code == "GATE_WITNESS_UNMEASURED" and self.witness is None
        else:
            consistent = self.refusal_code not in (None, "GATE_WITNESS_UNMEASURED") and self.witness is None
        if not consistent:
            raise ValueError("NATIVE_GATE_OUTCOME_CONTRADICTORY")
        profiles = [name for name in ("kernel_profile", "process_profile", "resource_profile") if name in self.model_fields_set]
        if any(getattr(self, name) is None for name in profiles):
            raise ValueError("NATIVE_GATE_PROFILE_UNSUPPORTED")
        authentication = "owning_host_ports"
        if profiles:
            authentication = "unsigned_host_capture" if profiles == ["resource_profile"] else (
                "configured_owning_host_signature" if self.status == "PASS" else "not_admitted")
        if self.observation_authentication != authentication:
            raise ValueError("NATIVE_GATE_AUTHENTICATION_PROFILE_MISMATCH")
        if self.status == "PASS" and self.witness is not None:
            for name in ("kernel_profile", "process_profile", "resource_profile"):
                if (name in profiles or hasattr(self.witness, name)) and (
                        getattr(self.witness, name, None) != getattr(self, name, None)):
                    raise ValueError("NATIVE_GATE_WITNESS_PROFILE_MISMATCH")
        return self


class SyntaxPrefilterRequest(GateRequest[SyntaxPrefilterPayload]):
    gate_id: Literal["PFP-01-SYNTAX-PREFILTER"]
class DefectHunterRequest(GateRequest[CochainPayload]):
    gate_id: Literal["PFP-02-DEFECT-HUNTER"]
class GaugeBreakerRequest(GateRequest[GaugeBreakerPayload]):
    gate_id: Literal["PFP-03-GAUGE-BREAKER"]
class ScopeGuardRequest(GateRequest[ScopeGuardPayload]):
    gate_id: Literal["PFP-04-SCOPE-GUARD"]
class BackdoorAuditorRequest(GateRequest[BackdoorAuditorPayload]):
    gate_id: Literal["PFP-05-BACKDOOR-AUDITOR"]
class PrimalDualRequest(GateRequest[PrimalDualPayload]):
    gate_id: Literal["PFP-06-PRIMAL-DUAL"]
class MasterRequest(GateRequest[MasterPayload]):
    gate_id: Literal["PFP-07-MANUSCRIPT-TRUTH"]
class ScarChroniclerRequest(GateRequest[ScarChroniclerPayload]):
    gate_id: Literal["PFP-08-SCAR-CHRONICLER"]
class AntiHypeRequest(GateRequest[AntiHypePayload]):
    gate_id: Literal["PFP-09-ANTI-HYPE"]
class BoundaryFuzzerRequest(GateRequest[BoundaryFuzzerPayload]):
    gate_id: Literal["PFP-10-BOUNDARY-FUZZER"]
class QuarantineRequest(GateRequest[QuarantinePayload]):
    gate_id: Literal["PFP-11-QUARANTINE"]
class IntegrityAuditorRequest(GateRequest[IntegrityAuditorPayload]):
    gate_id: Literal["PFP-12-INTEGRITY-AUDITOR"]
class AdversaryRequest(GateRequest[AdversaryPayload]):
    gate_id: Literal["PFP-13-REALITY-GATE"]
class ContextTransportRequest(GateRequest[ContextTransportPayload]):
    gate_id: Literal["PFP-14-CONTEXT-TRANSPORT"]
class BareMetalAnchorRequest(GateRequest[BareMetalAnchorPayload]):
    gate_id: Literal["PFP-15-BARE-METAL-ANCHOR"]
class ResilienceRequest(GateRequest[ResiliencePayload]):
    gate_id: Literal["PFP-16-RESILIENCE"]
class OverconfidenceProbeRequest(GateRequest[OverconfidenceProbePayload]):
    gate_id: Literal["PFP-17-OVERCONFIDENCE-PROBE"]
class PunchlistRequest(GateRequest[PunchlistPayload]):
    gate_id: Literal["PFP-18-PUNCHLIST"]
class LevyRequest(GateRequest[LevyPayload]):
    gate_id: Literal["PFP-19-CUSTODY"]
class CovertVerifierRequest(GateRequest[CovertVerifierPayload]):
    gate_id: Literal["PFP-20-COVERT-VERIFIER"]
class TruthRepairRequest(GateRequest[TruthRepairPayload]):
    gate_id: Literal["PFP-21-TRUTH-REPAIR"]
class HardwareConstraintRequest(GateRequest[HardwareConstraintPayload]):
    gate_id: Literal["PFP-22-HARDWARE-CONSTRAINT"]


class SyntaxPrefilterReceipt(GateReceipt[SyntaxPrefilterWitness]):
    gate_id: Literal["PFP-01-SYNTAX-PREFILTER"]
class DefectHunterReceipt(GateReceipt[DefectHunterWitness]):
    gate_id: Literal["PFP-02-DEFECT-HUNTER"]
class GaugeBreakerReceipt(GateReceipt[GaugeBreakerWitness]):
    gate_id: Literal["PFP-03-GAUGE-BREAKER"]
class ScopeGuardReceipt(GateReceipt[ScopeGuardWitness]):
    gate_id: Literal["PFP-04-SCOPE-GUARD"]
class BackdoorAuditorReceipt(GateReceipt[BackdoorAuditorWitness]):
    gate_id: Literal["PFP-05-BACKDOOR-AUDITOR"]
class PrimalDualReceipt(GateReceipt[PrimalDualWitness]):
    gate_id: Literal["PFP-06-PRIMAL-DUAL"]
class MasterReceipt(GateReceipt[KernelWitness]):
    gate_id: Literal["PFP-07-MANUSCRIPT-TRUTH"]
    kernel_profile: Literal["adversary.host-lean.v1"] | None = None
class ScarChroniclerReceipt(GateReceipt[ScarChroniclerWitness]):
    gate_id: Literal["PFP-08-SCAR-CHRONICLER"]
class AntiHypeReceipt(GateReceipt[AntiHypeWitness]):
    gate_id: Literal["PFP-09-ANTI-HYPE"]
class BoundaryFuzzerReceipt(GateReceipt[BoundaryFuzzerWitness]):
    gate_id: Literal["PFP-10-BOUNDARY-FUZZER"]
class QuarantineReceipt(GateReceipt[QuarantineWitness]):
    gate_id: Literal["PFP-11-QUARANTINE"]
class IntegrityAuditorReceipt(GateReceipt[IntegrityAuditorWitness]):
    gate_id: Literal["PFP-12-INTEGRITY-AUDITOR"]
class AdversaryReceipt(GateReceipt[AdversaryWitness]):
    gate_id: Literal["PFP-13-REALITY-GATE"]
class ContextTransportReceipt(GateReceipt[ContextTransportWitness]):
    gate_id: Literal["PFP-14-CONTEXT-TRANSPORT"]
class BareMetalAnchorReceipt(GateReceipt[ProcessWitness]):
    gate_id: Literal["PFP-15-BARE-METAL-ANCHOR"]
    process_profile: Literal["adversary.host-process.v1"] | None = None
class ResilienceReceipt(GateReceipt[ResilienceWitness]):
    gate_id: Literal["PFP-16-RESILIENCE"]
class OverconfidenceProbeReceipt(GateReceipt[OverconfidenceProbeWitness]):
    gate_id: Literal["PFP-17-OVERCONFIDENCE-PROBE"]
class PunchlistReceipt(GateReceipt[PunchlistWitness]):
    gate_id: Literal["PFP-18-PUNCHLIST"]
class LevyReceipt(GateReceipt[LevyWitness]):
    gate_id: Literal["PFP-19-CUSTODY"]
class CovertVerifierReceipt(GateReceipt[ProcessWitness]):
    gate_id: Literal["PFP-20-COVERT-VERIFIER"]
    process_profile: Literal["adversary.host-process.v1"] | None = None
class TruthRepairReceipt(GateReceipt[TruthRepairWitness]):
    gate_id: Literal["PFP-21-TRUTH-REPAIR"]
class HardwareConstraintReceipt(GateReceipt[HardwareConstraintWitness]):
    gate_id: Literal["PFP-22-HARDWARE-CONSTRAINT"]
    resource_profile: Literal["adversary.host-job-resources.v1"] | None = None


PrimaryGateRequest = Annotated[Union[
    SyntaxPrefilterRequest, DefectHunterRequest, GaugeBreakerRequest, ScopeGuardRequest, BackdoorAuditorRequest,
    PrimalDualRequest, MasterRequest, ScarChroniclerRequest, AntiHypeRequest, BoundaryFuzzerRequest,
    QuarantineRequest, IntegrityAuditorRequest, AdversaryRequest, ContextTransportRequest, BareMetalAnchorRequest,
    ResilienceRequest, OverconfidenceProbeRequest, PunchlistRequest, LevyRequest, CovertVerifierRequest,
    TruthRepairRequest, HardwareConstraintRequest,
], Field(discriminator="gate_id")]
PrimaryGateReceipt = Annotated[Union[
    SyntaxPrefilterReceipt, DefectHunterReceipt, GaugeBreakerReceipt, ScopeGuardReceipt, BackdoorAuditorReceipt,
    PrimalDualReceipt, MasterReceipt, ScarChroniclerReceipt, AntiHypeReceipt, BoundaryFuzzerReceipt,
    QuarantineReceipt, IntegrityAuditorReceipt, AdversaryReceipt, ContextTransportReceipt, BareMetalAnchorReceipt,
    ResilienceReceipt, OverconfidenceProbeReceipt, PunchlistReceipt, LevyReceipt, CovertVerifierReceipt,
    TruthRepairReceipt, HardwareConstraintReceipt,
], Field(discriminator="gate_id")]
_REQUEST = TypeAdapter(PrimaryGateRequest)
_RECEIPT = TypeAdapter(PrimaryGateReceipt)


def validate_typed_gate_request(value: object) -> PrimaryGateRequest:
    """Opt-in strict syntax; use the unchanged native predicate for its verdict."""
    return _REQUEST.validate_python(value)


def validate_typed_gate_receipt(value: object) -> PrimaryGateReceipt:
    """Parse a newly produced witness; this is not host authentication or replay."""
    return _RECEIPT.validate_python(value)


def typed_gate_contract_schema() -> dict:
    return {"schema_version": TYPED_GATE_CONTRACT_VERSION,
            "request": _REQUEST.json_schema(), "receipt": _RECEIPT.json_schema()}
