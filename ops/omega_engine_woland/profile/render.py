"""Deterministic human UNS and authoritative JSONL rendering."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, cast

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.stage.domain.canonical import (
    AUTHORITY_EFFECT_NONE,
    canonical_json_bytes,
    exact_object,
    strict_json_loads,
)

from .models import WolandSealPacketV1


@dataclass(frozen=True, slots=True)
class RenderedWolandSealV1:
    uns_text: str
    uns_sha256: str
    jsonl_bytes: bytes
    jsonl_sha256: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        if type(self.uns_text) is not str or not self.uns_text:
            raise TypeError("UNS must be nonempty exact text")
        if type(self.jsonl_bytes) is not bytes or not self.jsonl_bytes:
            raise TypeError("JSONL must be nonempty exact bytes")
        expected_uns = (
            "sha256:" + hashlib.sha256(self.uns_text.encode("utf-8")).hexdigest()
        )
        expected_jsonl = "sha256:" + hashlib.sha256(self.jsonl_bytes).hexdigest()
        if self.uns_sha256 != expected_uns or self.jsonl_sha256 != expected_jsonl:
            raise ValueError("rendered Woland digest does not match exact bytes")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("rendered seal authority_effect must be None")


def _line(sequence: int, record_type: str, payload: dict[str, Any]) -> bytes:
    return cast(
        bytes,
        canonical_json_bytes(
            {
                "authority_effect": AUTHORITY_EFFECT_NONE,
                "payload": payload,
                "record_type": record_type,
                "sequence": sequence,
            },
        ),
    )


def render_woland_seal_packet(packet: WolandSealPacketV1) -> RenderedWolandSealV1:
    if type(packet) is not WolandSealPacketV1:
        raise TypeError("packet must be exact WolandSealPacketV1")
    uns_lines = [
        "# Woland Engineering Factory — Universal Narrative Service",
        "",
        f"Packet: {packet.packet_id}",
        f"Run receipt: {packet.run_receipt_id}",
        f"Selection proposal: {packet.selection_proposal_id}",
        f"Artifacts: {len(packet.artifact_refs)}",
        f"Findings retained: {len(packet.finding_refs)}",
        f"Valuations: {len(packet.valuation_receipt_ids)}",
        f"Anti-skill gates: {len(packet.anti_skill_gate_receipt_ids)}",
        f"Inert mined proposals: {len(packet.mined_proposals)}",
        "",
        "## Draft PR text",
        "",
        packet.draft_pr_text,
        "",
        "## Nonclaims",
        "",
        *(f"- {item}" for item in packet.nonclaims),
        "",
        "No hidden chain-of-thought is recorded. AuthorityEffect: None.",
        "",
    ]
    uns = "\n".join(uns_lines)
    records = [_line(0, "WOLAND_SEAL_PACKET", packet.to_dict())]
    records.extend(
        _line(index, "INERT_MINED_PROPOSAL", proposal.to_dict())
        for index, proposal in enumerate(packet.mined_proposals, start=1)
    )
    jsonl = b"\n".join(records) + b"\n"
    return RenderedWolandSealV1(
        uns_text=uns,
        uns_sha256="sha256:" + hashlib.sha256(uns.encode("utf-8")).hexdigest(),
        jsonl_bytes=jsonl,
        jsonl_sha256="sha256:" + hashlib.sha256(jsonl).hexdigest(),
    )


def verify_rendered_woland_seal(
    *,
    packet: WolandSealPacketV1,
    uns_bytes: bytes,
    jsonl_bytes: bytes,
) -> Result[RenderedWolandSealV1, Refusal]:
    """Strictly reparse and independently reproduce both durable streams."""

    try:
        if type(packet) is not WolandSealPacketV1:
            raise TypeError("packet must be exact WolandSealPacketV1")
        if type(uns_bytes) is not bytes or type(jsonl_bytes) is not bytes:
            raise TypeError("rendered streams must be exact bytes")
        uns_text = uns_bytes.decode("utf-8", errors="strict")
        raw_lines = jsonl_bytes.splitlines()
        if not raw_lines or jsonl_bytes != b"\n".join(raw_lines) + b"\n":
            raise ValueError("JSONL must be nonempty and end with one LF")
        parsed = tuple(strict_json_loads(line) for line in raw_lines)
        envelopes = tuple(
            exact_object(
                item,
                frozenset({"authority_effect", "payload", "record_type", "sequence"}),
                "Woland JSONL envelope",
            )
            for item in parsed
        )
        if tuple(item["sequence"] for item in envelopes) != tuple(
            range(len(envelopes))
        ):
            raise ValueError("Woland JSONL sequence is not canonical")
        if envelopes[0]["record_type"] != "WOLAND_SEAL_PACKET":
            raise ValueError("Woland JSONL omits the seal packet head")
        if envelopes[0]["payload"] != packet.to_dict():
            raise ValueError("Woland JSONL packet payload differs")
        if any(item["authority_effect"] != AUTHORITY_EFFECT_NONE for item in envelopes):
            raise ValueError("Woland JSONL authority_effect differs")
        proposals = packet.mined_proposals
        if len(envelopes) != len(proposals) + 1:
            raise ValueError("Woland JSONL mined proposal coverage differs")
        for envelope, proposal in zip(envelopes[1:], proposals, strict=True):
            if envelope["record_type"] != "INERT_MINED_PROPOSAL":
                raise ValueError("Woland JSONL proposal record type differs")
            if envelope["payload"] != proposal.to_dict():
                raise ValueError("Woland JSONL mined proposal payload differs")
        reproduced = render_woland_seal_packet(packet)
        if reproduced.uns_text != uns_text or reproduced.jsonl_bytes != jsonl_bytes:
            raise ValueError("rendered Woland streams do not reproduce")
        return Ok(reproduced)
    except (
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        return Err(Refusal("WOLAND_SEAL_REPLAY_REFUSED", str(exc), "seal-and-mine"))


__all__ = [
    "RenderedWolandSealV1",
    "render_woland_seal_packet",
    "verify_rendered_woland_seal",
]
