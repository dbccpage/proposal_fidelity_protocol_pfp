"""Versioned Rip-Papers machine policy for Paper Sweep (sole-input pilot).

Improver generates candidate + producer receipt only.
Adversary requires eligible I3 cross-model receipt to close.
Proof-signoff and release are NOT_ELIGIBLE under the sole-input rule
(cannot inspect Lean, ENC, companion ledgers, or external citations).

Boundary (strict):
- Internally generated stage projections are **eligibility records**, not
  actual improver/adversary/proof/release role receipts.
- Only externally supplied, hash-bound receipts may occupy role-receipt slots.
- Adversary acceptance alone must not yield StabilizedSurvivor while proof
  signoff is NOT_ELIGIBLE; workflow stays OpenObstruction / BLOCKED@proof.
- Proof signoff remains distinct from release.
- All terminal authority effects remain None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from omega_engine_pfp.domain.shared_kernel.research_digest import digest_payload

POLICY_VERSION = "omega.rip_papers.paper_sweep.policy.v1"
MAX_REPAIR_ATTEMPTS = 3


def _is_nonzero_lower_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value != "0" * 64
        and all(char in "0123456789abcdef" for char in value)
    )


class Role(str, Enum):
    IMPROVER = "improver"
    ADVERSARY = "adversary"
    PROOF_SIGNOFF = "proof_signoff"
    RELEASE = "release"


class StageEligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    PROVISIONAL = "PROVISIONAL"
    BLOCKED = "BLOCKED"


class ReceiptKind(str, Enum):
    """Distinguish projections from hash-bound external role receipts."""

    ELIGIBILITY_PROJECTION = "eligibility_projection"
    EXTERNAL_ROLE_RECEIPT = "external_role_receipt"


@dataclass(frozen=True)
class RoleReceipt:
    role: Role
    status: StageEligibility
    attempt: int
    notes: str
    i3_eligible: bool = False
    receipt_sha256_ref: Optional[str] = None
    authority_effect: str = "None"
    receipt_kind: ReceiptKind = ReceiptKind.ELIGIBILITY_PROJECTION

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "authority_effect": self.authority_effect,
            "i3_eligible": self.i3_eligible,
            "notes": self.notes,
            "receipt_kind": self.receipt_kind.value,
            "receipt_sha256_ref": self.receipt_sha256_ref,
            "role": self.role.value,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class AdversaryHandoff:
    """Always present; closed only by an eligible I3 receipt."""

    closed: bool
    required_independence: str
    workflow_state: str
    mathematical_terminal: str
    workflow_terminal: str
    reason: str
    producer_id: str
    adversary_id: str
    attempt: int
    authority_effect: str = "None"
    schema_version: str = "omega.adversary_handoff_packet.v1"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "adversary_id": self.adversary_id,
            "attempt": self.attempt,
            "authority_effect": self.authority_effect,
            "closed": self.closed,
            "mathematical_terminal": self.mathematical_terminal,
            "producer_id": self.producer_id,
            "reason": self.reason,
            "required_independence": self.required_independence,
            "schema_version": self.schema_version,
            "workflow_state": self.workflow_state,
            "workflow_terminal": self.workflow_terminal,
        }

    @property
    def packet_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


def evaluate_adversary_receipt(
    *,
    producer_id: str,
    adversary_id: str,
    adversary_model_id: Optional[str],
    producer_model_id: Optional[str],
    receipt: Optional[Mapping[str, Any]],
    frozen_carrier_sha256: str,
) -> tuple[bool, str]:
    """Return (eligible, reason). Valid I3 requires distinct models + bound hash.

    Only externally supplied, hash-bound receipts are considered. Missing or
    projection-only material is not I3-eligible.
    """
    if receipt is None:
        return False, "missing external adversary receipt"
    receipt_kind = receipt.get("receipt_kind")
    if (
        type(receipt_kind) is not str
        or receipt_kind != ReceiptKind.EXTERNAL_ROLE_RECEIPT.value
    ):
        return False, "receipt is not an external role receipt"
    if (
        type(producer_id) is not str
        or not producer_id
        or type(adversary_id) is not str
        or not adversary_id
        or adversary_id == producer_id
    ):
        return False, "adversary identity must differ from producer"
    if type(adversary_model_id) is not str or not adversary_model_id:
        return False, "adversary model id missing"
    if producer_model_id is not None and (
        type(producer_model_id) is not str or not producer_model_id
    ):
        return False, "producer model id malformed"
    if producer_model_id and adversary_model_id == producer_model_id:
        return False, "same-model adversary is not I3-eligible"
    bound = receipt.get("carrier_sha256") or receipt.get("frozen_carrier_sha256")
    if (
        not _is_nonzero_lower_sha256(bound)
        or not _is_nonzero_lower_sha256(frozen_carrier_sha256)
        or bound != frozen_carrier_sha256
    ):
        return False, "stale or mismatched carrier hash on adversary receipt"
    independence_class = receipt.get("independence_class")
    if type(independence_class) is not str or independence_class not in (
        "I3_CROSS_MODEL",
        "I3",
        "cross_model",
    ):
        return False, "malformed independence_class (require I3_CROSS_MODEL)"
    status = receipt.get("status")
    if type(status) is not str or status not in ("PASS", "ACCEPT", "ELIGIBLE"):
        return False, f"adversary status not accepting: {status}"
    # Fabricated closed I3 without binding fields is refused.
    if receipt.get("fabricated") is True:
        return False, "fabricated I3 receipt refused"
    return True, "eligible I3 cross-model external receipt"


def evaluate_proof_signoff_receipt(
    *,
    proof_receipt: Optional[Mapping[str, Any]],
    handoff_sha256: Optional[str] = None,
) -> tuple[bool, str]:
    """External, hash-bound proof return only. Never closes from pipeline_completed."""
    if proof_receipt is None:
        return False, "missing external proof return receipt"
    if proof_receipt.get("schema") != "omega.proof_candidate_receipt.v1":
        return False, "proof receipt must be omega.proof_candidate_receipt.v1"
    if proof_receipt.get("closes_proof_signoff") is True:
        return False, "proof return must not self-close proof signoff"
    if proof_receipt.get("pipeline_completed") and proof_receipt.get(
        "proof_status"
    ) in ("Proven", "Accepted", "Certified"):
        return False, "pipeline_completed must not lift to proof acceptance"
    if handoff_sha256 and proof_receipt.get("handoff_sha256") != handoff_sha256:
        return False, "proof return handoff_sha256 mismatch"
    if proof_receipt.get("authority_effect") not in (None, "None", "none"):
        return False, "proof return authority_effect must be None"
    status = proof_receipt.get("proof_status")
    if status not in (
        "CandidateGenerated",
        "ReplayVerified",
        "Refused",
        "OracleNeeded",
        "NotClaimed",
    ):
        return False, f"unsupported proof_status: {status}"
    # Even ReplayVerified evidence does not close signoff in this sole-input pilot.
    return False, (
        "external proof evidence may attach to a new attempt, but proof signoff "
        "remains NOT_ELIGIBLE until a separately verified signoff path exists"
    )


def run_rip_papers_policy(
    *,
    producer_id: str,
    adversary_id: str,
    producer_model_id: str = "local-structural-producer",
    adversary_model_id: Optional[str] = None,
    adversary_receipt: Optional[Mapping[str, Any]] = None,
    proof_return_receipt: Optional[Mapping[str, Any]] = None,
    frozen_carrier_sha256: str,
    attempt: int = 1,
) -> tuple[tuple[RoleReceipt, ...], AdversaryHandoff]:
    """Emit eligibility projections for one attempt (not external role receipts).

    Role-receipt *slots* for adversary/proof only gain EXTERNAL_ROLE_RECEIPT kind
    when a hash-bound external receipt is supplied. Internally generated rows
    remain eligibility projections.
    """
    if attempt < 1 or attempt > MAX_REPAIR_ATTEMPTS:
        raise ValueError(f"attempt must be in 1..{MAX_REPAIR_ATTEMPTS}")

    improver = RoleReceipt(
        role=Role.IMPROVER,
        status=StageEligibility.ELIGIBLE,
        attempt=attempt,
        notes=(
            "Eligibility projection: producer generated candidate copy only. "
            "Not an external improver role receipt."
        ),
        receipt_kind=ReceiptKind.ELIGIBILITY_PROJECTION,
    )

    eligible, reason = evaluate_adversary_receipt(
        producer_id=producer_id,
        adversary_id=adversary_id,
        adversary_model_id=adversary_model_id,
        producer_model_id=producer_model_id,
        receipt=adversary_receipt,
        frozen_carrier_sha256=frozen_carrier_sha256,
    )
    adversary = RoleReceipt(
        role=Role.ADVERSARY,
        status=StageEligibility.ELIGIBLE if eligible else StageEligibility.BLOCKED,
        attempt=attempt,
        notes=reason,
        i3_eligible=eligible,
        receipt_sha256_ref=(
            digest_payload(dict(adversary_receipt)) if adversary_receipt else None
        ),
        receipt_kind=(
            ReceiptKind.EXTERNAL_ROLE_RECEIPT
            if adversary_receipt is not None and eligible
            else ReceiptKind.ELIGIBILITY_PROJECTION
        ),
    )

    proof_ok, proof_reason = evaluate_proof_signoff_receipt(
        proof_receipt=proof_return_receipt,
    )
    proof = RoleReceipt(
        role=Role.PROOF_SIGNOFF,
        status=(
            StageEligibility.ELIGIBLE if proof_ok else StageEligibility.NOT_ELIGIBLE
        ),
        attempt=attempt,
        notes=proof_reason,
        receipt_sha256_ref=(
            digest_payload(dict(proof_return_receipt)) if proof_return_receipt else None
        ),
        receipt_kind=(
            ReceiptKind.EXTERNAL_ROLE_RECEIPT
            if proof_return_receipt is not None
            else ReceiptKind.ELIGIBILITY_PROJECTION
        ),
    )
    release = RoleReceipt(
        role=Role.RELEASE,
        status=StageEligibility.NOT_ELIGIBLE,
        attempt=attempt,
        notes=(
            "Release remains NOT_ELIGIBLE and distinct from proof signoff. "
            "Paper build, PDF/ZIP, upload, and promotion are outside this sweep."
        ),
        receipt_kind=ReceiptKind.ELIGIBILITY_PROJECTION,
    )

    # Adversary acceptance alone cannot yield StabilizedSurvivor while proof
    # signoff is NOT_ELIGIBLE.
    if eligible and proof.status == StageEligibility.NOT_ELIGIBLE:
        workflow_state = "BLOCKED@proof/OpenObstruction"
        workflow_terminal = "OracleNeeded"
        closed = False
        handoff_reason = (
            f"{reason}; adversary evidence retained but proof signoff remains "
            "NOT_ELIGIBLE — StabilizedSurvivor refused"
        )
    elif eligible and proof_ok:
        workflow_state = "BLOCKED@release/OpenObstruction"
        workflow_terminal = "OracleNeeded"
        closed = False
        handoff_reason = (
            "proof evidence may attach, but release is NOT_ELIGIBLE; "
            "StabilizedSurvivor refused without separate release path"
        )
    else:
        workflow_state = "BLOCKED@adversary/OracleNeeded"
        workflow_terminal = "OracleNeeded"
        closed = False
        handoff_reason = reason

    handoff = AdversaryHandoff(
        closed=closed,
        required_independence="I3_CROSS_MODEL",
        workflow_state=workflow_state,
        mathematical_terminal="OpenObstruction",
        workflow_terminal=workflow_terminal,
        reason=handoff_reason,
        producer_id=producer_id,
        adversary_id=adversary_id,
        attempt=attempt,
    )
    return (improver, adversary, proof, release), handoff


def policy_manifest() -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "max_repair_attempts": MAX_REPAIR_ATTEMPTS,
        "roles": [role.value for role in Role],
        "authority_effect": "None",
        "notes": (
            "Machine policy for Paper Sweep pilot; does not restore deleted "
            "paper_hygiene_standard.md. Skills remain separately versioned."
        ),
    }


__all__ = [
    "AdversaryHandoff",
    "MAX_REPAIR_ATTEMPTS",
    "POLICY_VERSION",
    "Role",
    "RoleReceipt",
    "StageEligibility",
    "evaluate_adversary_receipt",
    "policy_manifest",
    "run_rip_papers_policy",
]
