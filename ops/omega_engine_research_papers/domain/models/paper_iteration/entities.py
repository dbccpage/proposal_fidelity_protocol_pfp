#!/usr/bin/env python3
"""Domain Entities and Aggregate Roots for the paper_iteration Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from .enums import (
    AuthorityEffect,
    GateVerdict,
    LedgerLane,
    ResearchGate,
    ResearchMode,
    ResearchTerminal,
)
from .errors import (
    AuthorityFirewallViolationError,
    StrictProposerEvaluatorCollisionError,
)
from .value_objects import GateReceipt

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest_canonical_dict(payload: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 over key-sorted JSON without floats."""
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class ResearchEvaluation:
    """Aggregate root representing an atomic multi-gate evaluation of a research packet."""

    packet_sha256: str
    proposal_sha256: str
    proposer_id: str
    evaluator_id: str
    mode: ResearchMode
    gates: tuple[GateReceipt, ...]
    refutation_candidate: bool = False
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    schema_version: str = "omega.research_evaluation.v1"

    def __post_init__(self) -> None:
        for label, value in (
            ("packet_sha256", self.packet_sha256),
            ("proposal_sha256", self.proposal_sha256),
        ):
            if _SHA256.fullmatch(value) is None:
                raise ValueError(f"{label} must be a lowercase SHA-256 digest")
        if not self.proposer_id or not self.evaluator_id:
            raise ValueError("proposer and evaluator identities must be explicit")
        if self.mode is ResearchMode.STRICT and self.proposer_id == self.evaluator_id:
            raise StrictProposerEvaluatorCollisionError(self.proposer_id)
        names = [receipt.gate for receipt in self.gates]
        if len(names) != len(ResearchGate) or set(names) != set(ResearchGate):
            raise ValueError("evaluation must contain each research gate exactly once")
        if self.authority_effect is not AuthorityEffect.NONE and self.authority_effect != AuthorityEffect.NONE.value:
            raise AuthorityFirewallViolationError(str(self.authority_effect))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ResearchEvaluation)
        return (
            self.packet_sha256 == other.packet_sha256
            and self.proposal_sha256 == other.proposal_sha256
            and self.proposer_id == other.proposer_id
            and self.evaluator_id == other.evaluator_id
            and self.mode == other.mode
            and self.gates == other.gates
            and self.refutation_candidate == other.refutation_candidate
            and self.authority_effect == other.authority_effect
            and self.schema_version == other.schema_version
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.packet_sha256,
                self.proposal_sha256,
                self.proposer_id,
                self.evaluator_id,
                self.mode,
                self.gates,
                self.refutation_candidate,
                self.authority_effect,
                self.schema_version,
            )
        )

    @property
    def terminal(self) -> ResearchTerminal:
        verdicts = {receipt.verdict for receipt in self.gates}
        if GateVerdict.INFRASTRUCTURE_FAILURE in verdicts:
            return ResearchTerminal.PROCESS_OBSTRUCTION
        if GateVerdict.REFUSE in verdicts:
            return ResearchTerminal.REFUSED
        if GateVerdict.FAIL in verdicts:
            return ResearchTerminal.REPAIR_REQUIRED
        if GateVerdict.OPEN in verdicts:
            return ResearchTerminal.ORACLE_NEEDED
        if self.refutation_candidate:
            return ResearchTerminal.THEORY_REFUTATION_CANDIDATE
        if self.mode is ResearchMode.FAST:
            return ResearchTerminal.EXPLORATORY_CANDIDATE
        return ResearchTerminal.READY_FOR_HUMAN_REVIEW

    @property
    def lane(self) -> LedgerLane:
        if self.terminal is ResearchTerminal.READY_FOR_HUMAN_REVIEW:
            return LedgerLane.HUMAN_REVIEW
        if self.terminal in {
            ResearchTerminal.EXPLORATORY_CANDIDATE,
            ResearchTerminal.THEORY_REFUTATION_CANDIDATE,
        }:
            return LedgerLane.EXPLORATORY
        if self.terminal is ResearchTerminal.ORACLE_NEEDED:
            return LedgerLane.OBLIGATIONS
        return LedgerLane.FAILURE_ATLAS

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_sha256": self.packet_sha256,
            "proposal_sha256": self.proposal_sha256,
            "proposer_id": self.proposer_id,
            "evaluator_id": self.evaluator_id,
            "mode": self.mode.value,
            "gates": [receipt.canonical_payload() for receipt in self.gates],
            "refutation_candidate": self.refutation_candidate,
            "terminal": self.terminal.value,
            "lane": self.lane.value,
            "authority_effect": self.authority_effect.value if hasattr(self.authority_effect, "value") else str(self.authority_effect),
        }

    @property
    def evaluation_sha256(self) -> str:
        return _digest_canonical_dict(self.canonical_payload())

    @property
    def focus_codes(self) -> tuple[str, ...]:
        return tuple(
            receipt.reason_code
            for receipt in self.gates
            if receipt.verdict is not GateVerdict.PASS
        )
