"""Deliberation turns and multi-perspective consensus protocols."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from .operad_colours import OperadColour


class ConsensusStatus(str, Enum):
    """Status of multi-agent deliberation over a paper artifact."""

    CONSENSUS_REACHED = "CONSENSUS_REACHED"
    DIALETHEIC_TENSION = "DIALETHEIC_TENSION"
    TERMINAL_REFUSAL = "TERMINAL_REFUSAL"


@dataclass(frozen=True)
class SwarmDeliberationTurn:
    """A single turn executed by a specialist persona during a deliberation bout."""

    persona_id: str
    turn_index: int
    input_colour: OperadColour
    output_colour: OperadColour
    passed_checks: bool
    findings: Tuple[str, ...]
    remediation_proposal: Optional[str] = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass(frozen=True)
class PeerReviewWitnessRecord:
    """Provenance record for a review screen; status states its evidence ceiling."""

    schema: str
    check_id: str
    obligation: str
    auditor_persona: str
    governing_skill: str
    source_colour: str
    target_colour: str
    paper_id: str
    snapshot_sha256: str
    timestamp_utc: str
    status: str
    findings: Tuple[str, ...]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "check_id": self.check_id,
            "obligation": self.obligation,
            "auditor_persona": self.auditor_persona,
            "governing_skill": self.governing_skill,
            "operad_morphism": {
                "source_colour": self.source_colour,
                "target_colour": self.target_colour,
            },
            "paper_id": self.paper_id,
            "snapshot_sha256": self.snapshot_sha256,
            "timestamp_utc": self.timestamp_utc,
            "status": self.status,
            "findings": list(self.findings),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class DeliberationBout:
    """A multi-turn deliberation bout among specialist personas."""

    bout_id: str
    paper_id: str
    turns: Tuple[SwarmDeliberationTurn, ...] = field(default_factory=tuple)
    status: ConsensusStatus = ConsensusStatus.DIALETHEIC_TENSION
    unresolved_objections: Tuple[str, ...] = field(default_factory=tuple)
    witness_records: Tuple[PeerReviewWitnessRecord, ...] = field(default_factory=tuple)
    #: The Adversary paper-review bout that closed the review ("" when none ran).
    routing_terminal: str = ""
    adversary_receipt_id: str = ""

    def is_unanimous_pass(self) -> bool:
        if not self.turns:
            return False
        return all(t.passed_checks for t in self.turns) and len(self.unresolved_objections) == 0

    def to_dict(self) -> dict:
        return {
            "bout_id": self.bout_id,
            "paper_id": self.paper_id,
            "status": self.status.value,
            "turns": [
                {
                    "persona_id": t.persona_id,
                    "turn_index": t.turn_index,
                    "input_colour": t.input_colour.value,
                    "output_colour": t.output_colour.value,
                    "passed_checks": t.passed_checks,
                    "findings": list(t.findings),
                    "remediation_proposal": t.remediation_proposal,
                    "authority_effect": t.authority_effect,
                }
                for t in self.turns
            ],
            "unresolved_objections": list(self.unresolved_objections),
            "witness_records": [w.to_dict() for w in self.witness_records],
            "routing_terminal": self.routing_terminal,
            "adversary_receipt_id": self.adversary_receipt_id,
        }
