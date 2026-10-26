"""Receipt-shaped domain models and witness certificates for Woland Swarm Engines.

Unifies the CODA 9-layer calculus, LGGR gluing defect diagnostics, and Woland
retinue deliberation into immutable research evidence envelopes.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional


def fraction_to_str(frac: Fraction) -> str:
    """Format Fraction as exact numerator/denominator string."""
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def str_to_fraction(val: str) -> Fraction:
    """Parse exact rational from string."""
    if "/" in val:
        num, den = val.split("/", 1)
        return Fraction(int(num.strip()), int(den.strip()))
    return Fraction(int(val.strip()), 1)


@dataclass(frozen=True)
class DualWitnessCertificate:
    """Verified Primal-Dual witness certificate representation.

    Cross-verified with Lean 4 substrate Simplex.AutoP.Kernel.DualWitnessCertificate
    and Rust PTIR auto_p/compiler/ptir.rs.
    """

    name: str
    divergence_free: bool
    linf_bounded: bool
    pairing_saturated: bool

    def is_valid(self) -> bool:
        """Certificate is valid iff all mathematical sub-conditions hold exactly."""
        return self.divergence_free and self.linf_bounded and self.pairing_saturated

    def canonical_receipt_string(self) -> str:
        """Canonical receipt string representation matching Lean 4 and Rust PTIR."""
        df_str = "true" if self.divergence_free else "false"
        lb_str = "true" if self.linf_bounded else "false"
        ps_str = "true" if self.pairing_saturated else "false"
        return f"DualWitnessCertificate:{self.name}:{df_str}:{lb_str}:{ps_str}"

    def receipt_hash(self) -> str:
        """Compute 32-byte Blake3 cryptographic digest matching Rust PTIR."""
        try:
            import blake3

            hasher = blake3.blake3()
            hasher.update(b"AUTOP_DUAL_WITNESS_V1:")
            hasher.update(self.canonical_receipt_string().encode("utf-8"))
            return hasher.hexdigest()
        except ImportError:
            hasher = hashlib.sha256()
            hasher.update(b"AUTOP_DUAL_WITNESS_V1:")
            hasher.update(self.canonical_receipt_string().encode("utf-8"))
            return hasher.hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "divergence_free": self.divergence_free,
            "linf_bounded": self.linf_bounded,
            "pairing_saturated": self.pairing_saturated,
            "is_valid": self.is_valid(),
            "canonical_receipt_string": self.canonical_receipt_string(),
            "receipt_hash": self.receipt_hash(),
        }


@dataclass(frozen=True)
class ResearchTaskContractV1:
    """Immutable research problem specification binding carrier and verification scope."""

    task_id: str
    objective: str
    carrier_type: str  # "cochain", "path_kernel", "graph", "simplicial"
    declared_regime: str  # "Reading_L", "Reading_F", "Simplicial"
    budget_max_steps: int
    created_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def contract_digest(self) -> str:
        raw = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CodaEvaluationResult:
    """Exact quotient diagnostic and dual-witness receipt across the 9-layer CODA stack."""

    phi1: Fraction
    gamma2: Fraction
    grade: str  # "ExactSolution", "CoherentResidual", "NonclosedDefect"
    dual_witness_vector: List[Fraction]
    dual_witness_linfty: Fraction
    dual_witness_pairing: Fraction
    layer_records: List[Dict[str, Any]]
    terminal_kind: str  # "Authorized", "ClosedResidual", "Refused"
    firewall_decision: str
    evidence_digest: str
    dual_witness_certificate: Optional[DualWitnessCertificate] = None
    native_evidence: Optional[Dict[str, Any]] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, CodaEvaluationResult):
            return False
        return (
            self.phi1 == other.phi1
            and self.gamma2 == other.gamma2
            and self.grade == other.grade
            and self.dual_witness_vector == other.dual_witness_vector
            and self.dual_witness_linfty == other.dual_witness_linfty
            and self.dual_witness_pairing == other.dual_witness_pairing
            and self.layer_records == other.layer_records
            and self.terminal_kind == other.terminal_kind
            and self.firewall_decision == other.firewall_decision
            and self.evidence_digest == other.evidence_digest
            and self.dual_witness_certificate == other.dual_witness_certificate
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.phi1,
            self.gamma2,
            self.grade,
            tuple(self.dual_witness_vector),
            self.dual_witness_linfty,
            self.dual_witness_pairing,
            self.terminal_kind,
            self.firewall_decision,
            self.evidence_digest,
            self.dual_witness_certificate,
        ))

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "phi1": fraction_to_str(self.phi1),
            "gamma2": fraction_to_str(self.gamma2),
            "grade": self.grade,
            "dual_witness_vector": [fraction_to_str(f) for f in self.dual_witness_vector],
            "dual_witness_linfty": fraction_to_str(self.dual_witness_linfty),
            "dual_witness_pairing": fraction_to_str(self.dual_witness_pairing),
            "layer_records": self.layer_records,
            "terminal_kind": self.terminal_kind,
            "firewall_decision": self.firewall_decision,
            "evidence_digest": self.evidence_digest,
        }
        if self.dual_witness_certificate:
            res["dual_witness_certificate"] = self.dual_witness_certificate.to_dict()
        if self.native_evidence is not None:
            res["native_evidence"] = self.native_evidence
        return res


@dataclass(frozen=True)
class JointKernelVerdictV1:
    """The native LGGR V verdict on a carrier difference D and observer quotient Q.

    `sound` is rank(Q·D) == rank(D), decided by `lggr_v::check_soundness`. When
    unsound, `witness` is a vector v with D·v != 0 and Q·D·v == 0, replayed by
    the adapter before this value is built. AuthorityEffect: None.
    """

    sound: bool
    d_rank: int
    qd_rank: int
    witness: Optional[tuple[Fraction, ...]]
    decision: str

    def __post_init__(self) -> None:
        if type(self.sound) is not bool or type(self.d_rank) is not int or type(self.qd_rank) is not int:
            raise TypeError("JOINT_KERNEL_VERDICT_TYPES")
        if not 0 <= self.qd_rank <= self.d_rank:
            raise ValueError("JOINT_KERNEL_RANKS_INCONSISTENT")
        if self.sound != (self.qd_rank == self.d_rank) or self.sound != (self.witness is None):
            raise ValueError("JOINT_KERNEL_VERDICT_INCONSISTENT")
        if self.witness is not None and any(type(entry) is not Fraction for entry in self.witness):
            raise TypeError("JOINT_KERNEL_WITNESS_NOT_EXACT")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, JointKernelVerdictV1):
            return False
        return (self.sound, self.d_rank, self.qd_rank, self.witness, self.decision) == (
            other.sound, other.d_rank, other.qd_rank, other.witness, other.decision)

    def __hash__(self) -> int:
        return hash((type(self), self.sound, self.d_rank, self.qd_rank, self.witness, self.decision))

    def to_dict(self) -> Dict[str, Any]:
        return {"sound": self.sound, "d_rank": self.d_rank, "qd_rank": self.qd_rank,
                "witness": None if self.witness is None else [fraction_to_str(v) for v in self.witness],
                "decision": self.decision}


@dataclass(frozen=True)
class LggrGluingResult:
    """Local Green Global Red gluing defect and detector adequacy analysis."""

    local_evaluators: Dict[str, int]
    global_evaluator: int
    local_product: int
    gluing_defect_delta: int  # -1 (NGD), 0 (ZDR), +1 (PGD)
    verdict_name: str  # "NegativeGluingDefect_LocalGreenGlobalRed", "ZeroDefectResidual", "PositiveGluingDefect"
    detector_adequacy_certified: bool
    adequacy_failures: List[str]
    null_space_soundness_satisfied: bool  # whether im(D) \cap K == {0}
    interpretation: str
    native_evidence: Optional[Dict[str, Any]] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, LggrGluingResult):
            return False
        return (
            self.local_evaluators == other.local_evaluators
            and self.global_evaluator == other.global_evaluator
            and self.local_product == other.local_product
            and self.gluing_defect_delta == other.gluing_defect_delta
            and self.verdict_name == other.verdict_name
            and self.detector_adequacy_certified == other.detector_adequacy_certified
            and self.adequacy_failures == other.adequacy_failures
            and self.null_space_soundness_satisfied == other.null_space_soundness_satisfied
            and self.interpretation == other.interpretation
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            tuple(sorted(self.local_evaluators.items())),
            self.global_evaluator,
            self.local_product,
            self.gluing_defect_delta,
            self.verdict_name,
            self.detector_adequacy_certified,
            tuple(self.adequacy_failures),
            self.null_space_soundness_satisfied,
            self.interpretation,
        ))

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.native_evidence is None:
            result.pop("native_evidence", None)
        return result


@dataclass(frozen=True)
class WolandSwarmDeliberation:
    """Cognitive deliberation, 9-dot gauge break, and fireproof audit record."""

    scene_id: str
    characters_invoked: List[str]
    divergent_proposals: List[Dict[str, Any]]
    nocebo_plunge_critique: Optional[str]
    surprise_gauge_break: Optional[str]
    old_man_fireproof_findings: List[Dict[str, Any]]
    terminal_verdict: str  # "PASS_TO_MASTER", "REFUSE", "OPEN_RESIDUAL"
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, WolandSwarmDeliberation):
            return False
        return (
            self.scene_id == other.scene_id
            and self.characters_invoked == other.characters_invoked
            and self.divergent_proposals == other.divergent_proposals
            and self.nocebo_plunge_critique == other.nocebo_plunge_critique
            and self.surprise_gauge_break == other.surprise_gauge_break
            and self.old_man_fireproof_findings == other.old_man_fireproof_findings
            and self.terminal_verdict == other.terminal_verdict
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.scene_id,
            tuple(self.characters_invoked),
            self.nocebo_plunge_critique,
            self.surprise_gauge_break,
            self.terminal_verdict,
            self.authority_effect,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchEvidenceEnvelopeV1:
    """Consolidated cryptographic research evidence envelope binding all research receipts."""

    envelope_id: str
    contract: ResearchTaskContractV1
    coda_evaluation: CodaEvaluationResult
    lggr_gluing: LggrGluingResult
    woland_deliberation: WolandSwarmDeliberation
    envelope_digest: str
    persisted_path: Optional[str] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ResearchEvidenceEnvelopeV1):
            return False
        return (
            self.envelope_id == other.envelope_id
            and self.contract == other.contract
            and self.coda_evaluation == other.coda_evaluation
            and self.lggr_gluing == other.lggr_gluing
            and self.woland_deliberation == other.woland_deliberation
            and self.envelope_digest == other.envelope_digest
            and self.persisted_path == other.persisted_path
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.envelope_id,
            self.contract,
            self.coda_evaluation,
            self.lggr_gluing,
            self.woland_deliberation,
            self.envelope_digest,
            self.persisted_path,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "omega.research_swarm.evidence_envelope.v1",
            "authority_effect": "None",
            "envelope_id": self.envelope_id,
            "contract": self.contract.to_dict(),
            "coda_evaluation": self.coda_evaluation.to_dict(),
            "lggr_gluing": self.lggr_gluing.to_dict(),
            "woland_deliberation": self.woland_deliberation.to_dict(),
            "envelope_digest": self.envelope_digest,
            "persisted_path": self.persisted_path,
        }
