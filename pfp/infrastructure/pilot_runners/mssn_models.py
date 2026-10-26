"""models.py — Typed Algebraic and Pydantic Domain Models for MSS-N Demos.

AuthorityEffect: None.
Reference: Minimal Symbol System N (MSS-N) and S(n) Cochain Foundations.
Enforces strict algebraic types, runtime contracts, and immutable schemas.
"""

from __future__ import annotations

from enum import Enum
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from omega_engine_woland.infrastructure.providers.openai_compat import OPENROUTER_BASE_URL

# ==============================================================================
# PFP PROTOCOL ENUMS AND STAGES
# ==============================================================================


class PfpStageStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    STOPPED = "STOPPED"
    SKIPPED = "SKIPPED"


class ProposalStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    NON_DESCENT = "NON_DESCENT"
    TYPED_REFUSAL = "TYPED_REFUSAL"
    OBSTRUCTION_FOUND = "OBSTRUCTION_FOUND"


class PfpStageVerdicts(BaseModel):
    stage_1_compression_gate: PfpStageStatus = PfpStageStatus.PASS
    stage_2_ideation: PfpStageStatus = PfpStageStatus.STOPPED
    stage_3_audit: PfpStageStatus = PfpStageStatus.STOPPED
    stage_4_l2_extraction: PfpStageStatus = PfpStageStatus.PASS
    stage_5_evaluation: PfpStageStatus = PfpStageStatus.PASS
    stage_6_adversarial: PfpStageStatus = PfpStageStatus.STOPPED
    stage_7_countermodel: PfpStageStatus = PfpStageStatus.STOPPED
    stage_8_evidence_plan: PfpStageStatus = PfpStageStatus.STOPPED


# ==============================================================================
# ALGEBRAIC & MATHEMATICAL VALUE OBJECTS
# ==============================================================================


class ExactRational(BaseModel):
    """Exact rational scalar p/q."""

    num: int
    den: int = 1

    @field_validator("den")
    @classmethod
    def denominator_nonzero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Denominator must be non-zero.")
        return v

    def to_fraction(self) -> Fraction:
        return Fraction(self.num, self.den)

    @classmethod
    def from_fraction(cls, f: Fraction) -> ExactRational:
        return cls(num=f.numerator, den=f.denominator)


class ExactRationalVector(BaseModel):
    """Ordered vector over Q."""

    dimension: int
    elements: List[ExactRational]

    @model_validator(mode="after")
    def validate_dimension(self) -> ExactRationalVector:
        if len(self.elements) != self.dimension:
            raise ValueError(
                f"Dimension mismatch: expected {self.dimension}, got {len(self.elements)}"
            )
        return self


class SimplicialCarrier(BaseModel):
    """Abstract oriented simplicial complex without ambient metric assumptions."""

    vertices: List[str]
    edges: List[Tuple[str, str]]
    faces: List[Tuple[str, str, str]] = Field(default_factory=list)
    has_metric_data: bool = False


class CochainRepairProblem(BaseModel):
    """Degree-k cochain with allowed coboundary repairs."""

    degree: int
    cochain: List[int]
    differential_matrix: List[List[int]]
    allowed_repair_space: str
    target_residual: List[int] = Field(default_factory=lambda: [0, 0])


class CohomologicalObstructionWitness(BaseModel):
    """Exact certificate of non-exactness via cycle pairing."""

    cycle_name: str
    cycle_chain: List[int]
    pairing_value: int
    is_obstructed: bool

    @model_validator(mode="after")
    def check_obstruction(self) -> CohomologicalObstructionWitness:
        if self.pairing_value != 0 and not self.is_obstructed:
            raise ValueError("Non-zero pairing must be flagged as obstructed.")
        return self


# ==============================================================================
# DEMO PAYLOAD MODELS
# ==============================================================================


class MssnDemoBasePayload(BaseModel):
    """Base payload schema for all 50 MSS-N demos."""

    status: ProposalStatus
    pfp_stage_verdicts: PfpStageVerdicts
    carrier_evidence: Union[Dict[str, Any], List[Any], str, None] = Field(default_factory=dict)
    mathematical_witness: Union[Dict[str, Any], List[Any], str, None] = Field(default_factory=dict)
    narrowest_defensible_claim: Union[str, List[str]]
    justification: Union[str, List[str]]

    @field_validator("narrowest_defensible_claim", "justification", mode="before")
    @classmethod
    def coerce_to_string(cls, v: Any) -> str:
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        return str(v)

    @field_validator("narrowest_defensible_claim", "justification")
    @classmethod
    def validate_claim_hygiene(cls, text: str) -> str:
        forbidden = [
            "proves",
            "guarantees",
            "mathematically verifies",
            "fundamentally",
            "true intelligence",
            "impossible",
            "universal",
            "flawless",
            "perfectly",
            "clearly",
            "obviously",
            "simply",
            "merely",
            "weaponized",
        ]
        text_lower = text.lower()
        import re

        for word in forbidden:
            if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
                raise ValueError(
                    f"Claim Hygiene Violation: forbidden word '{word}' found in response."
                )
        return text


# ==============================================================================
# YAML PROMPT PACKET AND FIXTURE MODELS
# ==============================================================================


class PromptPacket(BaseModel):
    """Layer 2 typed prompt packet schema for prompt.yaml."""

    schema_version: str = "pfp.prompt.v1"
    authority_effect: str = "None"
    seed_id: str
    number: int
    title: str
    mss_regimes: List[str]
    modes: List[str]
    focus_stages: List[int]
    system_prompt: str
    response_schema: str
    user_prompt: str

    @field_validator("authority_effect")
    @classmethod
    def validate_authority(cls, v: str) -> str:
        if v != "None":
            raise ValueError("authority_effect must strictly be 'None'")
        return v


class ExpectedFixture(MssnDemoBasePayload):
    """Layer 2 expected ground truth fixture schema for expected.yaml."""

    pass


# ==============================================================================
# ADVANCED ALGEBRAIC STRUCTURES & INVARIANT CHECKERS
# ==============================================================================


class NilpotentBoundaryOperator(BaseModel):
    """Boundary operators d_k and d_{k-1} satisfying d_{k-1} * d_k = 0."""

    d_k: List[List[int]]
    d_k_minus_1: List[List[int]]

    @model_validator(mode="after")
    def verify_nilpotence(self) -> NilpotentBoundaryOperator:
        if not self.d_k or not self.d_k_minus_1:
            return self
        m = len(self.d_k_minus_1)
        k = len(self.d_k)
        n = len(self.d_k[0]) if k > 0 else 0
        if len(self.d_k_minus_1[0]) != k:
            raise ValueError(
                f"Matrix dimension mismatch for composition: ({m}x{len(self.d_k_minus_1[0])}) vs ({k}x{n})"
            )
        # Check d_{k-1} * d_k == 0
        for i in range(m):
            for j in range(n):
                val = sum(self.d_k_minus_1[i][p] * self.d_k[p][j] for p in range(k))
                if val != 0:
                    raise ValueError(
                        f"Nilpotence violated at ({i}, {j}): composition is {val} != 0"
                    )
        return self


class QuantumStabilizerCheck(BaseModel):
    """CSS code parity-check matrices satisfying H_X * H_Z^T = 0 mod 2."""

    h_x: List[List[int]]
    h_z: List[List[int]]

    @model_validator(mode="after")
    def verify_orthogonality(self) -> QuantumStabilizerCheck:
        if not self.h_x or not self.h_z:
            return self
        n_x = len(self.h_x[0])
        n_z = len(self.h_z[0])
        if n_x != n_z:
            raise ValueError(f"Qubit count mismatch: H_X has {n_x} cols, H_Z has {n_z} cols")
        for i, row_x in enumerate(self.h_x):
            for j, row_z in enumerate(self.h_z):
                comm = sum(a * b for a, b in zip(row_x, row_z)) % 2
                if comm != 0:
                    raise ValueError(
                        f"Stabilizer commutativity violated between X-row {i} and Z-row {j}: {comm} != 0 mod 2"
                    )
        return self


# ==============================================================================
# CRYPTOGRAPHIC RECEIPT MODEL & EXECUTION HONESTY GATE
# ==============================================================================


class ExecutionAttestationMode(str, Enum):
    LIVE_PROVIDER = "LIVE_PROVIDER"
    FIXTURE_REPLAY = "FIXTURE_REPLAY"


class ExecutionMetadata(BaseModel):
    attestation_mode: ExecutionAttestationMode = ExecutionAttestationMode.FIXTURE_REPLAY
    dry_run: bool
    model_requested: str
    model: str
    generation_id: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: float = 0.0
    latency_ms: Optional[float] = None
    raw_usage: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def gate_execution_honesty(self) -> ExecutionMetadata:
        """GATE_EXECUTION_HONESTY_001: Prevent mocked or dry-run execution from claiming live status."""
        if self.attestation_mode == ExecutionAttestationMode.LIVE_PROVIDER:
            if self.dry_run:
                raise ValueError(
                    "Gate Refusal [GATE_EXECUTION_HONESTY_001]: dry_run must be False when attestation_mode is LIVE_PROVIDER."
                )
            if self.model.startswith("dry-run:") or "fixture" in self.model.lower():
                raise ValueError(
                    f"Gate Refusal [GATE_EXECUTION_HONESTY_001]: model name '{self.model}' indicates mock/dry-run, not live provider."
                )
            if not self.generation_id or self.generation_id.startswith("dry-run-"):
                raise ValueError(
                    f"Gate Refusal [GATE_EXECUTION_HONESTY_001]: generation_id '{self.generation_id}' is invalid or synthetic."
                )
            if self.prompt_tokens is None or self.prompt_tokens <= 0:
                raise ValueError(
                    "Gate Refusal [GATE_EXECUTION_HONESTY_001]: prompt_tokens must be positive on live provider execution."
                )
            if self.completion_tokens is None or self.completion_tokens <= 0:
                raise ValueError(
                    "Gate Refusal [GATE_EXECUTION_HONESTY_001]: completion_tokens must be positive on live provider execution."
                )
        elif self.attestation_mode == ExecutionAttestationMode.FIXTURE_REPLAY:
            if not self.dry_run:
                raise ValueError(
                    "Gate Refusal [GATE_EXECUTION_HONESTY_001]: dry_run must be True when attestation_mode is FIXTURE_REPLAY."
                )
            if not self.model.startswith("dry-run:"):
                self.model = f"dry-run:{self.model}"
        return self


class LayerHashes(BaseModel):
    layer_1_seed_sha256: str
    layer_2_prompt_sha256: str
    layer_3_response_sha256: str


class GateVerificationResult(BaseModel):
    demo_id: str
    passed: bool
    verdicts: Dict[str, bool] = Field(default_factory=dict)
    failure_reasons: List[str] = Field(default_factory=list)
    computed_evidence: Dict[str, Any] = Field(default_factory=dict)


class PfpDemoReceipt(BaseModel):
    schema_version: str = "pfp.receipt.v1"
    authority_effect: str = "None"
    demo_id: str
    number: int
    title: str
    mss_regimes: List[str]
    modes: List[str]
    focus_stages: List[int]
    timestamp_utc: str
    execution: ExecutionMetadata
    layers: LayerHashes
    verification: GateVerificationResult


# ==============================================================================
# COMMON BUILD PROPERTIES (.NET Directory.Build.props EQUIVALENT)
# ==============================================================================


class CommonBuildProps(BaseModel):
    """Common build properties for the MSS-N / S(n) demonstration suite.

    Analogous to .NET Directory.Build.props, centralizing all project-wide
    constants, execution policies, schema versions, and resource fences.
    """

    authority_effect: str = "None"
    prompt_schema_version: str = "pfp.prompt.v1"
    receipt_schema_version: str = "pfp.receipt.v1"
    default_model: str = "deepseek/deepseek-chat"
    max_session_cost_usd: float = 0.010
    max_tokens: int = 2048
    temperature: float = 0.0
    total_demos_count: int = 50
    default_attestation_mode: ExecutionAttestationMode = ExecutionAttestationMode.LIVE_PROVIDER
    fallback_attestation_mode: ExecutionAttestationMode = ExecutionAttestationMode.FIXTURE_REPLAY
    openrouter_endpoint: str = OPENROUTER_BASE_URL + "/chat/completions"
    python_pinned_version: str = "3.12"
