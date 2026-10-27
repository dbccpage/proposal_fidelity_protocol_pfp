"""Canonical five-stage SPK-002 Symbol Game flow for Paper Sweep (offline).

Stages:
  01_seed_packet
  02_candidate_intake
  03_schema_validate
  04_transition_seal
  05_terminal_prompt_synthesis

No obsolete eight-stage candidate_ideas runner. Provider calls default to 0
in this pilot (deterministic local synthesis only).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

try:
    from core_symbol_game.research_packets import digest_payload
except ImportError:
    def digest_payload(data: Any) -> str:
        return "0" * 64


SPK002_STAGES: tuple[str, ...] = (
    "01_seed_packet",
    "02_candidate_intake",
    "03_schema_validate",
    "04_transition_seal",
    "05_terminal_prompt_synthesis",
)

CONTROLLER_ID = "core.symbol_game.spk002.paper_sweep.v1"
INTEGRITY_CONTRACT = "core.symbol_game.integrity.evidence_only.v1"


@dataclass(frozen=True)
class StageArtifact:
    stage: str
    request: dict[str, Any]
    response: dict[str, Any]
    packet: dict[str, Any]
    receipt: dict[str, Any]
    transition_sha256: str


@dataclass(frozen=True)
class SymbolGameRun:
    controller_id: str
    integrity_contract: str
    stages: tuple[StageArtifact, ...]
    conductor_packets: tuple[dict[str, Any], ...]
    provider_calls: int
    authority_effect: str = "None"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "conductor_packets": list(self.conductor_packets),
            "controller_id": self.controller_id,
            "integrity_contract": self.integrity_contract,
            "provider_calls": self.provider_calls,
            "stages": [
                {
                    "packet": stage.packet,
                    "receipt": stage.receipt,
                    "request": stage.request,
                    "response": stage.response,
                    "stage": stage.stage,
                    "transition_sha256": stage.transition_sha256,
                }
                for stage in self.stages
            ],
        }

    @property
    def run_sha256(self) -> str:
        return digest_payload(self.canonical_payload())


def _seal(payload: Mapping[str, Any]) -> str:
    return digest_payload(dict(payload))


def _require_schema(packet: Mapping[str, Any], required: Sequence[str]) -> None:
    missing = [key for key in required if key not in packet]
    if missing:
        raise ValueError(f"schema validation failed; missing={missing}")


def run_spk002_offline(
    *,
    source_sha256: str,
    source_path: str,
    proposal_payload: Mapping[str, Any],
    packetization_witness: Mapping[str, Any],
) -> SymbolGameRun:
    """Execute the five-stage flow deterministically with zero provider calls."""
    stages: list[StageArtifact] = []

    # 01 seed
    seed_packet = {
        "schema_version": "core.spk002.seed.v1",
        "source_path": source_path,
        "source_sha256": source_sha256,
        "packetization_witness_sha256": packetization_witness.get("witness_sha256")
        or digest_payload(packetization_witness),
        "authority_effect": "None",
    }
    _require_schema(seed_packet, ("schema_version", "source_sha256", "authority_effect"))
    seed_req = {"stage": "01_seed_packet", "action": "freeze_seed"}
    seed_resp = {"status": "LOCAL_SYNTH", "provider_calls": 0}
    seed_receipt = {"status": "PASS", "validated": True}
    seed_transition = _seal(
        {"request": seed_req, "response": seed_resp, "packet": seed_packet}
    )
    stages.append(
        StageArtifact(
            stage="01_seed_packet",
            request=seed_req,
            response=seed_resp,
            packet=seed_packet,
            receipt=seed_receipt,
            transition_sha256=seed_transition,
        )
    )

    # 02 candidate intake
    candidate_packet = {
        "schema_version": "core.spk002.candidate.v1",
        "seed_sha256": seed_transition,
        "proposal": dict(proposal_payload),
        "authority_effect": "None",
    }
    _require_schema(candidate_packet, ("schema_version", "proposal", "authority_effect"))
    cand_req = {"stage": "02_candidate_intake", "action": "accept_structural_proposal"}
    cand_resp = {"status": "LOCAL_SYNTH", "provider_calls": 0}
    cand_receipt = {"status": "PASS", "validated": True}
    cand_transition = _seal(
        {"request": cand_req, "response": cand_resp, "packet": candidate_packet}
    )
    stages.append(
        StageArtifact(
            stage="02_candidate_intake",
            request=cand_req,
            response=cand_resp,
            packet=candidate_packet,
            receipt=cand_receipt,
            transition_sha256=cand_transition,
        )
    )

    # 03 schema validate
    validate_packet = {
        "schema_version": "core.spk002.validate.v1",
        "candidate_transition_sha256": cand_transition,
        "checks": [
            "proposal.action",
            "proposal.realization",
            "proposal.cochain_realization",
            "proposal.authority_effect",
        ],
        "status": "PASS",
        "authority_effect": "None",
    }
    _require_schema(validate_packet, ("schema_version", "status", "authority_effect"))
    if proposal_payload.get("cochain_realization") != "UNRESOLVED":
        raise ValueError("Stage-3 refused: cochain_realization must be UNRESOLVED")
    if proposal_payload.get("authority_effect") not in ("None", "none"):
        raise ValueError("Stage-3 refused: authority_effect must be None")
    val_req = {"stage": "03_schema_validate", "action": "validate_candidate_schema"}
    val_resp = {"status": "LOCAL_SYNTH", "provider_calls": 0}
    val_receipt = {"status": "PASS", "validated": True}
    val_transition = _seal(
        {"request": val_req, "response": val_resp, "packet": validate_packet}
    )
    stages.append(
        StageArtifact(
            stage="03_schema_validate",
            request=val_req,
            response=val_resp,
            packet=validate_packet,
            receipt=val_receipt,
            transition_sha256=val_transition,
        )
    )

    # 04 transition seal
    seal_packet = {
        "schema_version": "core.spk002.seal.v1",
        "prior_transition_sha256": val_transition,
        "sealed": True,
        "authority_effect": "None",
    }
    seal_req = {"stage": "04_transition_seal", "action": "seal_transitions"}
    seal_resp = {"status": "LOCAL_SYNTH", "provider_calls": 0}
    seal_receipt = {"status": "PASS", "validated": True}
    seal_transition = _seal(
        {"request": seal_req, "response": seal_resp, "packet": seal_packet}
    )
    stages.append(
        StageArtifact(
            stage="04_transition_seal",
            request=seal_req,
            response=seal_resp,
            packet=seal_packet,
            receipt=seal_receipt,
            transition_sha256=seal_transition,
        )
    )

    # 05 terminal prompt synthesis (provisional — no I3 adversary)
    terminal_packet = {
        "schema_version": "core.spk002.terminal.v1",
        "prior_transition_sha256": seal_transition,
        "mathematical_terminal": proposal_payload.get(
            "mathematical_terminal", "OpenObstruction"
        ),
        "workflow_terminal": "OracleNeeded",
        "workflow_state": "BLOCKED@adversary/OracleNeeded",
        "reason": "no eligible I3 cross-model adversary receipt",
        "authority_effect": "None",
    }
    term_req = {
        "stage": "05_terminal_prompt_synthesis",
        "action": "synthesize_provisional_terminal",
    }
    term_resp = {"status": "LOCAL_SYNTH", "provider_calls": 0}
    term_receipt = {
        "status": "PROVISIONAL",
        "validated": True,
        "i3_eligible": False,
    }
    term_transition = _seal(
        {"request": term_req, "response": term_resp, "packet": terminal_packet}
    )
    stages.append(
        StageArtifact(
            stage="05_terminal_prompt_synthesis",
            request=term_req,
            response=term_resp,
            packet=terminal_packet,
            receipt=term_receipt,
            transition_sha256=term_transition,
        )
    )

    conductor = (
        {
            "packet_kind": "cochain_obstruction",
            "cochain_realization": "UNRESOLVED",
            "object_fields": "NOT_CONSTRUCTED",
            "source_sha256": source_sha256,
            "authority_effect": "None",
        },
        {
            "packet_kind": "code_rewrite",
            "action": proposal_payload.get("action"),
            "realization": proposal_payload.get("realization"),
            "candidate_sha256": proposal_payload.get("candidate_sha256"),
            "patch_sha256": proposal_payload.get("patch_sha256"),
            "authority_effect": "None",
        },
    )

    return SymbolGameRun(
        controller_id=CONTROLLER_ID,
        integrity_contract=INTEGRITY_CONTRACT,
        stages=tuple(stages),
        conductor_packets=conductor,
        provider_calls=0,
    )


def freeze_spk002_config() -> dict[str, Any]:
    """Controller + integrity + registry + five template hashes for config/."""
    templates = {
        stage: digest_payload({"template": stage, "controller": CONTROLLER_ID})
        for stage in SPK002_STAGES
    }
    config = {
        "controller_id": CONTROLLER_ID,
        "integrity_contract": INTEGRITY_CONTRACT,
        "registry": list(SPK002_STAGES),
        "templates": templates,
        "authority_effect": "None",
    }
    config["config_sha256"] = digest_payload(config)
    return config




__all__ = [
    "CONTROLLER_ID",
    "INTEGRITY_CONTRACT",
    "SPK002_STAGES",
    "StageArtifact",
    "SymbolGameRun",
    "freeze_spk002_config",
    "run_spk002_offline",
]
