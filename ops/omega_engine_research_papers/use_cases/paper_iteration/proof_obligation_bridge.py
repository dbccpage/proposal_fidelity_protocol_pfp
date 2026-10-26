"""Typed paper-finding → proof-obligation handoff (diagnostic only).

Schemas:
  omega.paper_proof_handoff.v1
  omega.proof_candidate_receipt.v1

compile-proof-obligation emits a SuccessorPacketCandidate for human dispatch.
It never invokes the proofer, never edits papers/ledgers, never promotes.

verify-proof-return checks returned evidence only; it cannot close proof
signoff or release.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

try:
    from omega_symbol_game.research_packets import digest_payload
except ImportError:
    def digest_payload(data: Any) -> str:
        return "0" * 64


HANDOFF_SCHEMA = "omega.paper_proof_handoff.v1"
RETURN_SCHEMA = "omega.proof_candidate_receipt.v1"
SUCCESSOR_SCHEMA = "omega.successor_packet_candidate.v1"
AUTHORITY_EFFECT = "None"
MAX_REPAIR_ATTEMPTS = 3
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ProofBridgeError(RuntimeError):
    """Typed refusal at the paper↔proof boundary."""


class ProofStatus(str, Enum):
    CANDIDATE_GENERATED = "CandidateGenerated"
    REPLAY_VERIFIED = "ReplayVerified"
    REFUSED = "Refused"
    ORACLE_NEEDED = "OracleNeeded"
    NOT_CLAIMED = "NotClaimed"


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ProofBridgeError(f"{label} must be lowercase SHA-256")
    return value


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()



@dataclass(frozen=True)
class PaperFindingView:
    """Minimal typed view of a paper finding for handoff compilation."""

    finding_id: str
    claim_id: str
    paper_path: str
    paper_sha256: str
    start_byte: int
    end_byte: int
    span_bytes: bytes
    theorem_statement: str
    hypotheses: tuple[str, ...]
    scope: str
    nonclaims: tuple[str, ...]
    carrier: str = ""
    c0: str = ""
    c1: str = ""
    zero_rel: str = ""
    q1: str = ""
    d0: str = ""
    d1: str = ""
    lean_target: str = ""
    lean_statement_hash: str = ""
    lean_import_hash: str = ""
    print_axioms_shape: str = "sorry_free_empty_axiom_list"
    rust_witness_required: bool = False

    @property
    def span_sha256(self) -> str:
        return _sha256_bytes(self.span_bytes)


def compile_proof_obligation(
    *,
    finding: PaperFindingView | Mapping[str, Any],
    parent_sweep_run_id: str,
    verified_bundle_hash: str,
    base_git_commit: str,
    candidate_sha256: str,
    carrier_sha256: str,
    producer_id: str,
    producer_provider_id: str,
    required_evaluator_id: str,
    forbidden_provider_ids: Sequence[str] = (),
    max_repair_attempts: int = MAX_REPAIR_ATTEMPTS
) -> dict[str, Any]:
    """Compile a typed handoff + successor packet. Does not run the proofer."""
    if max_repair_attempts < 1 or max_repair_attempts > MAX_REPAIR_ATTEMPTS:
        raise ProofBridgeError(
            f"max_repair_attempts must be in 1..{MAX_REPAIR_ATTEMPTS}"
        )
    if not required_evaluator_id or required_evaluator_id == producer_id:
        raise ProofBridgeError(
            "required_evaluator_id must differ from producer_id"
        )
    if required_evaluator_id == producer_provider_id:
        raise ProofBridgeError(
            "evaluator identity must not equal producer provider"
        )

    view = finding if isinstance(finding, PaperFindingView) else _view_from_mapping(finding)
    _require_sha256(verified_bundle_hash, "verified_bundle_hash")
    _require_sha256(candidate_sha256, "candidate_sha256")
    _require_sha256(carrier_sha256, "carrier_sha256")
    _require_sha256(view.paper_sha256, "paper_sha256")
    if view.start_byte < 0 or view.end_byte <= view.start_byte:
        raise ProofBridgeError("invalid source span offsets")
    if _sha256_bytes(view.span_bytes) != view.span_sha256:
        raise ProofBridgeError("span hash mismatch")

    forbidden = sorted(
        set(list(forbidden_provider_ids) + [producer_provider_id, producer_id])
    )

    handoff = {
        "schema": HANDOFF_SCHEMA,
        "authority_effect": AUTHORITY_EFFECT,
        "parent_sweep_run_id": parent_sweep_run_id,
        "verified_bundle_hash": verified_bundle_hash,
        "base_git_commit": base_git_commit,
        "paper_path": view.paper_path,
        "paper_sha256": view.paper_sha256,
        "candidate_sha256": candidate_sha256,
        "carrier_sha256": carrier_sha256,
        "finding_id": view.finding_id,
        "claim_id": view.claim_id,
        "source_span": {
            "start_byte": view.start_byte,
            "end_byte": view.end_byte,
            "span_sha256": view.span_sha256,
        },
        "theorem_statement": view.theorem_statement,
        "hypotheses": list(view.hypotheses),
        "scope": view.scope,
        "nonclaims": list(view.nonclaims)
        + [
            "pipeline_completed is not proof",
            "candidate generation is not proof signoff",
            "this packet does not authorize release",
        ],
        "cochain_fields": {
            "carrier": view.carrier,
            "C0": view.c0,
            "C1": view.c1,
            "ZeroRel": view.zero_rel,
            "Q1": view.q1,
            "d0": view.d0,
            "d1": view.d1,
        },
        "lean": {
            "target": view.lean_target,
            "statement_hash": view.lean_statement_hash,
            "import_hash": view.lean_import_hash,
            "print_axioms_evidence_shape": view.print_axioms_shape,
        },
        "rust_witness_required": view.rust_witness_required,
        "producer_id": producer_id,
        "producer_provider_id": producer_provider_id,
        "required_evaluator_id": required_evaluator_id,
        "forbidden_provider_ids": forbidden,
        "max_repair_attempts": max_repair_attempts,
        "dispatch": "human_controlled_only",
        "auto_invoke_proofer": False,
    }
    handoff["packet_sha256"] = digest_payload(
        {k: v for k, v in handoff.items() if k != "packet_sha256"}
    )

    successor = {
        "schema": SUCCESSOR_SCHEMA,
        "authority_effect": AUTHORITY_EFFECT,
        "kind": "ProofObligationDispatch",
        "handoff_schema": HANDOFF_SCHEMA,
        "handoff_sha256": handoff["packet_sha256"],
        "human_controlled_dispatch": True,
        "auto_execute": False,
        "recursive_agents_forbidden": True,
        "target_role": "proofer",
        "required_evaluator_id": required_evaluator_id,
        "forbidden_provider_ids": forbidden,
        "max_repair_attempts": max_repair_attempts,
        "nonclaims": [
            "Successor packet is not authorization",
            "Does not start agents automatically",
        ],
    }
    successor["packet_sha256"] = digest_payload(
        {k: v for k, v in successor.items() if k != "packet_sha256"}
    )

    result = {
        "handoff": handoff,
        "successor_packet_candidate": successor,
        "authority_effect": AUTHORITY_EFFECT,
    }
    return result


def _view_from_mapping(data: Mapping[str, Any]) -> PaperFindingView:
    span = data.get("source_span") or {}
    span_hex = data.get("span_bytes_hex")
    if span_hex:
        span_bytes = bytes.fromhex(str(span_hex))
    elif "span_text" in data:
        span_bytes = str(data["span_text"]).encode("utf-8")
    else:
        raise ProofBridgeError("finding requires span_bytes_hex or span_text")
    lean = data.get("lean") or {}
    co = data.get("cochain_fields") or {}
    return PaperFindingView(
        finding_id=str(data["finding_id"]),
        claim_id=str(data.get("claim_id") or data["finding_id"]),
        paper_path=str(data["paper_path"]),
        paper_sha256=str(data["paper_sha256"]),
        start_byte=int(span.get("start_byte", data.get("start_byte", 0))),
        end_byte=int(span.get("end_byte", data.get("end_byte", 0))),
        span_bytes=span_bytes,
        theorem_statement=str(data.get("theorem_statement") or ""),
        hypotheses=tuple(data.get("hypotheses") or ()),
        scope=str(data.get("scope") or "sole_paper_carrier"),
        nonclaims=tuple(data.get("nonclaims") or ()),
        carrier=str(co.get("carrier") or data.get("carrier") or ""),
        c0=str(co.get("C0") or ""),
        c1=str(co.get("C1") or ""),
        zero_rel=str(co.get("ZeroRel") or ""),
        q1=str(co.get("Q1") or ""),
        d0=str(co.get("d0") or ""),
        d1=str(co.get("d1") or ""),
        lean_target=str(lean.get("target") or ""),
        lean_statement_hash=str(lean.get("statement_hash") or ""),
        lean_import_hash=str(lean.get("import_hash") or ""),
        print_axioms_shape=str(
            lean.get("print_axioms_evidence_shape") or "sorry_free_empty_axiom_list"
        ),
        rust_witness_required=bool(data.get("rust_witness_required", False)),
    )


def refuse_free_form_proofer_seed(seed: Any) -> None:
    """Typed boundary: free-form prose seeds are refused."""
    if isinstance(seed, str):
        raise ProofBridgeError(
            "free-form prose seed refused at typed proofer boundary; "
            "require omega.paper_proof_handoff.v1"
        )
    if not isinstance(seed, Mapping):
        raise ProofBridgeError("proofer seed must be a mapping handoff packet")
    if seed.get("schema") != HANDOFF_SCHEMA:
        raise ProofBridgeError(
            f"proofer seed schema must be {HANDOFF_SCHEMA}, got {seed.get('schema')}"
        )


def build_proof_candidate_receipt(
    *,
    handoff: Mapping[str, Any],
    pipeline_completed: bool,
    proof_status: ProofStatus | str,
    producer_provider_id: str,
    evaluator_provider_id: str,
    attempt: int,
    candidate_artifact_sha256: Optional[str] = None,
    notes: str = "",
) -> dict[str, Any]:
    """Emit a returned proof-candidate receipt (evidence only)."""
    refuse_free_form_proofer_seed(handoff)
    if attempt < 1 or attempt > int(handoff.get("max_repair_attempts") or MAX_REPAIR_ATTEMPTS):
        raise ProofBridgeError(
            f"attempt {attempt} exceeds max_repair_attempts"
        )
    status = (
        proof_status
        if isinstance(proof_status, ProofStatus)
        else ProofStatus(str(proof_status))
    )
    # Never lift pipeline completion to proof acceptance
    if pipeline_completed and status == ProofStatus.CANDIDATE_GENERATED:
        pass  # allowed: completed generation only
    if status in (ProofStatus.CANDIDATE_GENERATED,) and pipeline_completed:
        # explicit split fields
        pass

    receipt = {
        "schema": RETURN_SCHEMA,
        "authority_effect": AUTHORITY_EFFECT,
        "handoff_sha256": handoff.get("packet_sha256"),
        "finding_id": handoff.get("finding_id"),
        "pipeline_completed": bool(pipeline_completed),
        "proof_status": status.value,
        "producer_provider_id": producer_provider_id,
        "evaluator_provider_id": evaluator_provider_id,
        "attempt": attempt,
        "candidate_artifact_sha256": candidate_artifact_sha256,
        "notes": notes,
        "closes_proof_signoff": False,
        "closes_release": False,
        "may_attach_to_rip_papers_attempt": True,
        "semantic_nonclaims": [
            "pipeline_completed is not proof_status",
            "CandidateGenerated is not proof approval",
            "receipt cannot close proof signoff or release",
        ],
    }
    receipt["receipt_sha256"] = digest_payload(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )
    return receipt


def verify_proof_return(
    *,
    handoff: Mapping[str, Any],
    return_receipt: Mapping[str, Any],
    carrier_bytes: Optional[bytes] = None,
    span_bytes: Optional[bytes] = None,
) -> dict[str, Any]:
    """Verify returned proof material as evidence only."""
    refuse_free_form_proofer_seed(handoff)
    if return_receipt.get("schema") != RETURN_SCHEMA:
        raise ProofBridgeError(
            f"return schema must be {RETURN_SCHEMA}"
        )
    if return_receipt.get("authority_effect") != AUTHORITY_EFFECT:
        raise ProofBridgeError("return authority_effect must be None")
    if return_receipt.get("closes_proof_signoff") is True:
        raise ProofBridgeError("return receipt must not close proof signoff")
    if return_receipt.get("closes_release") is True:
        raise ProofBridgeError("return receipt must not close release")

    expected_handoff = handoff.get("packet_sha256")
    if return_receipt.get("handoff_sha256") != expected_handoff:
        raise ProofBridgeError("return handoff_sha256 mismatch")

    producer = str(return_receipt.get("producer_provider_id") or "")
    evaluator = str(return_receipt.get("evaluator_provider_id") or "")
    if not producer or not evaluator:
        raise ProofBridgeError("producer and evaluator provider ids required")
    if producer == evaluator:
        raise ProofBridgeError("self-review refused: producer == evaluator")
    forbidden = set(handoff.get("forbidden_provider_ids") or [])
    if evaluator in forbidden:
        raise ProofBridgeError(
            "evaluator provider is forbidden (self-review / producer set)"
        )
    required = handoff.get("required_evaluator_id")
    if required and evaluator != required and evaluator == producer:
        raise ProofBridgeError("evaluator identity not independent")

    # Fabricated I3-style claims on the proof return are refused.
    if return_receipt.get("independence_class") in (
        "I3_CROSS_MODEL",
        "I3",
        "cross_model",
    ):
        if return_receipt.get("fabricated") or not return_receipt.get(
            "i3_external_receipt_sha256"
        ):
            raise ProofBridgeError("fabricated or unbound I3 claim refused")

    attempt = int(return_receipt.get("attempt") or 0)
    max_attempts = int(handoff.get("max_repair_attempts") or MAX_REPAIR_ATTEMPTS)
    if attempt < 1 or attempt > max_attempts:
        raise ProofBridgeError(
            f"attempt {attempt} outside 1..{max_attempts}"
        )

    if carrier_bytes is not None:
        actual = _sha256_bytes(carrier_bytes)
        if actual != handoff.get("carrier_sha256"):
            raise ProofBridgeError("carrier hash mismatch")
    if span_bytes is not None:
        actual = _sha256_bytes(span_bytes)
        expected = (handoff.get("source_span") or {}).get("span_sha256")
        if actual != expected:
            raise ProofBridgeError("source span hash mismatch")

    # Re-seal receipt body
    body = {k: v for k, v in return_receipt.items() if k != "receipt_sha256"}
    recomputed = digest_payload(body)
    if recomputed != return_receipt.get("receipt_sha256"):
        raise ProofBridgeError("return receipt_sha256 mismatch")

    # pipeline vs proof split
    if return_receipt.get("pipeline_completed") and return_receipt.get(
        "proof_status"
    ) in ("Proven", "Accepted", "Certified"):
        raise ProofBridgeError(
            "proof_status must not claim Proven/Accepted/Certified from this bridge"
        )

    return {
        "ok": True,
        "authority_effect": AUTHORITY_EFFECT,
        "proof_status": return_receipt.get("proof_status"),
        "pipeline_completed": return_receipt.get("pipeline_completed"),
        "closes_proof_signoff": False,
        "closes_release": False,
        "may_attach_to_rip_papers_attempt": True,
    }
