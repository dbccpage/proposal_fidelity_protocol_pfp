"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    Any,
    CODE_CHANGE_REPAIR_SCHEMA,
    Mapping,
    _fail,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_string,
    field,
)


@dataclass(frozen=True, slots=True)
class CodeChangeRepairV1:
    """One repair link after a refused or failed evaluation attempt."""

    repair_index: int
    prior_candidate_id: str
    repaired_candidate_id: str
    reason: str
    schema_version: str = field(default=CODE_CHANGE_REPAIR_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        if type(self.repair_index) is not int or self.repair_index < 0:
            _fail("repair_index must be a nonnegative integer")
        _require_digest(self.prior_candidate_id, "prior_candidate_id")
        _require_digest(self.repaired_candidate_id, "repaired_candidate_id")
        _require_string(self.reason, "repair reason", nonempty=True)
        if self.schema_version != CODE_CHANGE_REPAIR_SCHEMA:
            _fail("repair schema version is unsupported")
        if self.authority_effect != "None":
            _fail("repairs must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repair_index": self.repair_index,
            "prior_candidate_id": self.prior_candidate_id,
            "repaired_candidate_id": self.repaired_candidate_id,
            "reason": self.reason,
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CodeChangeRepairV1":
        wire = _require_exact_dict(wire, "code-change repair")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "repair_index",
                    "prior_candidate_id",
                    "repaired_candidate_id",
                    "reason",
                    "authority_effect",
                }
            ),
            "code-change repair",
        )
        return cls(
            repair_index=_require_nonnegative_int(
                wire["repair_index"], "repair_index"
            ),
            prior_candidate_id=_require_digest(
                wire["prior_candidate_id"], "prior_candidate_id"
            ),
            repaired_candidate_id=_require_digest(
                wire["repaired_candidate_id"], "repaired_candidate_id"
            ),
            reason=_require_string(wire["reason"], "repair reason", nonempty=True),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
