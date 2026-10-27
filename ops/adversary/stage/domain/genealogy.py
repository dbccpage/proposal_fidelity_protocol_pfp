"""Pure value objects for Cemetery, Antibodies, and Lineage Genealogy in Adversary stage.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    digest,
    exact_object,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
    wire_tuple,
)


@dataclass(frozen=True, slots=True)
class CemeteryHeadstoneV1:
    """Record for a killed candidate in the cemetery (the failure gold seam)."""

    candidate_id: str
    run_key: str
    scene_id: str
    cause_of_death: str
    killing_seat_id: str
    evidence_refs: tuple[str, ...]
    candidate_payload_sha256: str
    round_index: int = 0

    def __post_init__(self) -> None:
        identifier(self.candidate_id, "candidate_id")
        identifier(self.run_key, "run_key")
        identifier(self.scene_id, "scene_id")
        text(self.cause_of_death, "cause_of_death")
        identifier(self.killing_seat_id, "killing_seat_id")
        object.__setattr__(
            self,
            "evidence_refs",
            string_tuple(self.evidence_refs, "evidence_refs", allow_empty=True),
        )
        digest(self.candidate_payload_sha256, "candidate_payload_sha256")
        integer(self.round_index, "round_index", minimum=0)

    @property
    def headstone_id(self) -> str:
        return semantic_id(
            "core.oeas.headstone.v1",
            {
                "run_key": self.run_key,
                "scene_id": self.scene_id,
                "candidate_id": self.candidate_id,
                "cause_of_death": self.cause_of_death,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "headstone_id": self.headstone_id,
            "candidate_id": self.candidate_id,
            "run_key": self.run_key,
            "scene_id": self.scene_id,
            "cause_of_death": self.cause_of_death,
            "killing_seat_id": self.killing_seat_id,
            "evidence_refs": list(self.evidence_refs),
            "candidate_payload_sha256": self.candidate_payload_sha256,
            "round_index": self.round_index,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "CemeteryHeadstoneV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "headstone_id",
                    "candidate_id",
                    "run_key",
                    "scene_id",
                    "cause_of_death",
                    "killing_seat_id",
                    "evidence_refs",
                    "candidate_payload_sha256",
                    "round_index",
                }
            ),
            "cemetery headstone",
        )
        parsed = cls(
            candidate_id=identifier(wire["candidate_id"], "candidate_id"),
            run_key=identifier(wire["run_key"], "run_key"),
            scene_id=identifier(wire["scene_id"], "scene_id"),
            cause_of_death=text(wire["cause_of_death"], "cause_of_death"),
            killing_seat_id=identifier(wire["killing_seat_id"], "killing_seat_id"),
            evidence_refs=wire_tuple(wire["evidence_refs"], "evidence_refs"),
            candidate_payload_sha256=digest(
                wire["candidate_payload_sha256"], "candidate_payload_sha256"
            ),
            round_index=integer(wire.get("round_index", 0), "round_index"),
        )
        if digest(wire["headstone_id"], "headstone_id") != parsed.headstone_id:
            raise ValueError("cemetery headstone identity does not match its payload")
        return parsed


@dataclass(frozen=True, slots=True)
class AntibodyEntryV1:
    """Active negative constraint entry accumulated from recurring failures."""

    antibody_id: str
    failure_pattern: str
    occurrences: int
    constraint_rule: str
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        identifier(self.antibody_id, "antibody_id")
        text(self.failure_pattern, "failure_pattern")
        integer(self.occurrences, "occurrences", minimum=1)
        text(self.constraint_rule, "constraint_rule")
        identifier(self.status, "status")

    def to_dict(self) -> dict[str, Any]:
        return {
            "antibody_id": self.antibody_id,
            "failure_pattern": self.failure_pattern,
            "occurrences": self.occurrences,
            "constraint_rule": self.constraint_rule,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "AntibodyEntryV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "antibody_id",
                    "failure_pattern",
                    "occurrences",
                    "constraint_rule",
                    "status",
                }
            ),
            "antibody entry",
        )
        return cls(
            antibody_id=identifier(wire["antibody_id"], "antibody_id"),
            failure_pattern=text(wire["failure_pattern"], "failure_pattern"),
            occurrences=integer(wire["occurrences"], "occurrences"),
            constraint_rule=text(wire["constraint_rule"], "constraint_rule"),
            status=identifier(wire["status"], "status"),
        )


@dataclass(frozen=True, slots=True)
class GenealogyEntryV1:
    """Re-entry lineage link recording parent->child mutation details."""

    parent_run_key: str
    child_run_key: str
    structural_deficiencies: tuple[str, ...]
    concrete_fixes: tuple[str, ...]
    next_run_guidance: str
    re_entry_reason: str = "COMPOST_GUIDED_MUTATION"

    def __post_init__(self) -> None:
        identifier(self.parent_run_key, "parent_run_key")
        identifier(self.child_run_key, "child_run_key")
        object.__setattr__(
            self,
            "structural_deficiencies",
            string_tuple(
                self.structural_deficiencies, "structural_deficiencies"
            ),
        )
        object.__setattr__(
            self,
            "concrete_fixes",
            string_tuple(self.concrete_fixes, "concrete_fixes"),
        )
        text(self.next_run_guidance, "next_run_guidance")
        identifier(self.re_entry_reason, "re_entry_reason")

    @property
    def lineage_id(self) -> str:
        return semantic_id(
            "core.oeas.genealogy.v1",
            {
                "parent_run_key": self.parent_run_key,
                "child_run_key": self.child_run_key,
                "re_entry_reason": self.re_entry_reason,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "parent_run_key": self.parent_run_key,
            "child_run_key": self.child_run_key,
            "structural_deficiencies": list(self.structural_deficiencies),
            "concrete_fixes": list(self.concrete_fixes),
            "next_run_guidance": self.next_run_guidance,
            "re_entry_reason": self.re_entry_reason,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "GenealogyEntryV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "lineage_id",
                    "parent_run_key",
                    "child_run_key",
                    "structural_deficiencies",
                    "concrete_fixes",
                    "next_run_guidance",
                    "re_entry_reason",
                }
            ),
            "genealogy entry",
        )
        parsed = cls(
            parent_run_key=identifier(wire["parent_run_key"], "parent_run_key"),
            child_run_key=identifier(wire["child_run_key"], "child_run_key"),
            structural_deficiencies=wire_tuple(
                wire["structural_deficiencies"], "structural_deficiencies"
            ),
            concrete_fixes=wire_tuple(wire["concrete_fixes"], "concrete_fixes"),
            next_run_guidance=text(
                wire["next_run_guidance"], "next_run_guidance"
            ),
            re_entry_reason=identifier(wire["re_entry_reason"], "re_entry_reason"),
        )
        if digest(wire["lineage_id"], "lineage_id") != parsed.lineage_id:
            raise ValueError("genealogy identity does not match its payload")
        return parsed


__all__ = [
    "AntibodyEntryV1",
    "CemeteryHeadstoneV1",
    "GenealogyEntryV1",
]
