"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    Any,
    CODE_CHANGE_ATTEMPT_SCHEMA,
    MAX_REFUSALS,
    Mapping,
    _fail,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_string,
    _string_tuple_from_wire,
    _validate_ordered_unique_strings,
    field,
)


@dataclass(frozen=True, slots=True)
class CodeChangeAttemptV1:
    """One attach/evaluate attempt against a proposal packet."""

    attempt_index: int
    candidate_id: str
    patch_id: str
    operation_count: int
    disposition: str
    refusal_codes: tuple[str, ...]
    schema_version: str = field(default=CODE_CHANGE_ATTEMPT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        if type(self.attempt_index) is not int or self.attempt_index < 0:
            _fail("attempt_index must be a nonnegative integer")
        _require_digest(self.candidate_id, "candidate_id")
        _require_digest(self.patch_id, "patch_id")
        _require_nonnegative_int(self.operation_count, "operation_count")
        _require_string(self.disposition, "attempt disposition", nonempty=True)
        if self.disposition not in {
            "AcceptedForGates",
            "BudgetExhausted",
            "Refused",
        }:
            _fail("attempt disposition is unsupported")
        codes = _validate_ordered_unique_strings(
            self.refusal_codes, "attempt refusal_codes", maximum=MAX_REFUSALS
        )
        object.__setattr__(self, "refusal_codes", codes)
        if self.disposition == "AcceptedForGates" and codes:
            _fail("accepted attempts cannot carry refusal codes")
        if self.disposition != "AcceptedForGates" and not codes:
            _fail("refused/budget attempts require refusal codes")
        if self.schema_version != CODE_CHANGE_ATTEMPT_SCHEMA:
            _fail("attempt schema version is unsupported")
        if self.authority_effect != "None":
            _fail("attempts must carry AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_index": self.attempt_index,
            "candidate_id": self.candidate_id,
            "patch_id": self.patch_id,
            "operation_count": self.operation_count,
            "disposition": self.disposition,
            "refusal_codes": list(self.refusal_codes),
            "authority_effect": self.authority_effect,
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CodeChangeAttemptV1":
        wire = _require_exact_dict(wire, "code-change attempt")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "attempt_index",
                    "candidate_id",
                    "patch_id",
                    "operation_count",
                    "disposition",
                    "refusal_codes",
                    "authority_effect",
                }
            ),
            "code-change attempt",
        )
        return cls(
            attempt_index=_require_nonnegative_int(
                wire["attempt_index"], "attempt_index"
            ),
            candidate_id=_require_digest(wire["candidate_id"], "candidate_id"),
            patch_id=_require_digest(wire["patch_id"], "patch_id"),
            operation_count=_require_nonnegative_int(
                wire["operation_count"], "operation_count"
            ),
            disposition=_require_string(
                wire["disposition"], "attempt disposition", nonempty=True
            ),
            refusal_codes=_string_tuple_from_wire(
                wire["refusal_codes"], "attempt refusal_codes", maximum=MAX_REFUSALS
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
