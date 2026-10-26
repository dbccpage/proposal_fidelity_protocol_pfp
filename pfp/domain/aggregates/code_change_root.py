"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    Any,
    CODE_CHANGE_RUN_ROOT_SCHEMA,
    MAX_ATTEMPTS,
    MAX_CANDIDATE_BUDGET,
    MAX_GATE_RECEIPTS,
    MAX_REFUSALS,
    MAX_REPAIRS,
    Mapping,
    OBSTRUCTION_VERIFIER_RECEIPT_REQUIRED,
    REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN,
    RUN_ROOT_DOMAIN,
    RUN_ROOT_TERMINAL_STATUSES,
    _fail,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_string,
    _string_tuple_from_wire,
    _validate_ordered_unique_strings,
    domain_digest,
    field,
)
from .code_change_attempt import CodeChangeAttemptV1
from .code_change_repair import CodeChangeRepairV1


@dataclass(frozen=True, slots=True)
class CodeChangeRunRootV1:
    """Complete proposal run root linking task, candidates, gates, and terminal."""

    task_packet_id: str
    task_packet_sha256: str
    candidate_ids: tuple[str, ...]
    patch_ids: tuple[str, ...]
    gate_receipt_ids: tuple[str, ...]
    attempts: tuple[CodeChangeAttemptV1, ...]
    repairs: tuple[CodeChangeRepairV1, ...]
    refusals: tuple[str, ...]
    terminal_status: str
    open_obstruction_ids: tuple[str, ...]
    schema_version: str = field(default=CODE_CHANGE_RUN_ROOT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_digest(self.task_packet_id, "task_packet_id")
        _require_digest(self.task_packet_sha256, "task_packet_sha256")
        candidates = _validate_ordered_unique_strings(
            self.candidate_ids, "candidate_ids", maximum=MAX_CANDIDATE_BUDGET
        )
        patches = _validate_ordered_unique_strings(
            self.patch_ids, "patch_ids", maximum=MAX_CANDIDATE_BUDGET
        )
        gate_ids = _validate_ordered_unique_strings(
            self.gate_receipt_ids, "gate_receipt_ids", maximum=MAX_GATE_RECEIPTS
        )
        object.__setattr__(self, "candidate_ids", candidates)
        object.__setattr__(self, "patch_ids", patches)
        object.__setattr__(self, "gate_receipt_ids", gate_ids)
        if type(self.attempts) is not tuple or any(
            not isinstance(item, CodeChangeAttemptV1) for item in self.attempts
        ):
            _fail("attempts must be a tuple of CodeChangeAttemptV1")
        if len(self.attempts) > MAX_ATTEMPTS:
            _fail("attempts exceed the resource limit")
        for index, attempt in enumerate(self.attempts):
            if attempt.attempt_index != index:
                _fail("attempts must be contiguous and zero-indexed")
        if type(self.repairs) is not tuple or any(
            not isinstance(item, CodeChangeRepairV1) for item in self.repairs
        ):
            _fail("repairs must be a tuple of CodeChangeRepairV1")
        if len(self.repairs) > MAX_REPAIRS:
            _fail("repairs exceed the resource limit")
        for index, repair in enumerate(self.repairs):
            if repair.repair_index != index:
                _fail("repairs must be contiguous and zero-indexed")
        refusals = _validate_ordered_unique_strings(
            self.refusals, "refusals", maximum=MAX_REFUSALS
        )
        object.__setattr__(self, "refusals", refusals)
        _require_string(self.terminal_status, "terminal_status", nonempty=True)
        if self.terminal_status == "VerifiedProposal":
            _fail(REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN)
        if self.terminal_status not in RUN_ROOT_TERMINAL_STATUSES:
            _fail("terminal_status is unsupported")
        open_ids = _validate_ordered_unique_strings(
            self.open_obstruction_ids,
            "open_obstruction_ids",
            maximum=MAX_REFUSALS,
        )
        object.__setattr__(self, "open_obstruction_ids", open_ids)
        if self.terminal_status in {"TransportValidated", "DeclaredUnverified"}:
            if not candidates or not patches or not self.attempts:
                _fail(
                    "TransportValidated/DeclaredUnverified requires candidates, "
                    "patches, and attempts"
                )
            if refusals:
                _fail(
                    "TransportValidated/DeclaredUnverified cannot retain refusals"
                )
        if self.terminal_status == "DeclaredUnverified":
            if OBSTRUCTION_VERIFIER_RECEIPT_REQUIRED not in open_ids:
                _fail(
                    "DeclaredUnverified requires VERIFIER_RECEIPT_REQUIRED obstruction"
                )
        if self.terminal_status == "TransportValidated" and open_ids:
            _fail("TransportValidated cannot retain open obstructions")
        if self.terminal_status == "TypedRefusal" and not refusals:
            _fail("TypedRefusal requires at least one refusal code")
        if self.schema_version != CODE_CHANGE_RUN_ROOT_SCHEMA:
            _fail("code-change run root schema version is unsupported")
        if self.authority_effect != "None":
            _fail("code-change run roots must carry AuthorityEffect None")

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_packet_id": self.task_packet_id,
            "task_packet_sha256": self.task_packet_sha256,
            "candidate_ids": list(self.candidate_ids),
            "patch_ids": list(self.patch_ids),
            "gate_receipt_ids": list(self.gate_receipt_ids),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "repairs": [repair.to_dict() for repair in self.repairs],
            "refusals": list(self.refusals),
            "terminal_status": self.terminal_status,
            "open_obstruction_ids": list(self.open_obstruction_ids),
            "authority_effect": self.authority_effect,
        }


    @property
    def task_id(self) -> str:
        if self.explicit_task_id is not None:
            return self.explicit_task_id
        return self.task_packet_id

    @property
    def payload(self) -> Any:
        return self.explicit_payload

    @property
    def run_root_id(self) -> str:
        return domain_digest(RUN_ROOT_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_root_id": self.run_root_id,
            **self.identity_fields(),
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CodeChangeRunRootV1":
        wire = _require_exact_dict(wire, "code-change run root")
        if "passed" in wire or "promotion_eligible" in wire or "verified" in wire:
            _fail("run root carries forbidden authority-bearing fields")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "run_root_id",
                    "task_packet_id",
                    "task_packet_sha256",
                    "candidate_ids",
                    "patch_ids",
                    "gate_receipt_ids",
                    "attempts",
                    "repairs",
                    "refusals",
                    "terminal_status",
                    "open_obstruction_ids",
                    "authority_effect",
                }
            ),
            "code-change run root",
        )
        expected = _require_digest(wire["run_root_id"], "run_root_id")
        raw_attempts = wire["attempts"]
        raw_repairs = wire["repairs"]
        if type(raw_attempts) is not list or len(raw_attempts) > MAX_ATTEMPTS:
            _fail("attempts must be a bounded array")
        if type(raw_repairs) is not list or len(raw_repairs) > MAX_REPAIRS:
            _fail("repairs must be a bounded array")
        root = cls(
            task_packet_id=_require_digest(wire["task_packet_id"], "task_packet_id"),
            task_packet_sha256=_require_digest(
                wire["task_packet_sha256"], "task_packet_sha256"
            ),
            candidate_ids=_string_tuple_from_wire(
                wire["candidate_ids"],
                "candidate_ids",
                maximum=MAX_CANDIDATE_BUDGET,
            ),
            patch_ids=_string_tuple_from_wire(
                wire["patch_ids"], "patch_ids", maximum=MAX_CANDIDATE_BUDGET
            ),
            gate_receipt_ids=_string_tuple_from_wire(
                wire["gate_receipt_ids"],
                "gate_receipt_ids",
                maximum=MAX_GATE_RECEIPTS,
            ),
            attempts=tuple(
                CodeChangeAttemptV1.from_dict(item) for item in raw_attempts
            ),
            repairs=tuple(CodeChangeRepairV1.from_dict(item) for item in raw_repairs),
            refusals=_string_tuple_from_wire(
                wire["refusals"], "refusals", maximum=MAX_REFUSALS
            ),
            terminal_status=_require_string(
                wire["terminal_status"], "terminal_status", nonempty=True
            ),
            open_obstruction_ids=_string_tuple_from_wire(
                wire["open_obstruction_ids"],
                "open_obstruction_ids",
                maximum=MAX_REFUSALS,
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
        if expected != root.run_root_id:
            _fail("run_root_id does not match canonical wire content")
        return root
