"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    Any,
    GATE_DISPOSITIONS,
    GATE_RECEIPT_DOMAIN,
    GATE_RECEIPT_SCHEMA,
    MAX_REFUSALS,
    Mapping,
    REQUIRED_GATE_IDS,
    _fail,
    _require_bool,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_optional_bool,
    _require_stable_id,
    _require_string,
    _string_tuple_from_wire,
    _validate_ordered_unique_strings,
    domain_digest,
    field,
)


@dataclass(frozen=True, slots=True)
class GateReceiptV1:
    """Independent gate receipt. Model-authored ``passed`` is never trusted."""

    gate_id: str
    packet_id: str
    candidate_id: str
    evaluator_id: str
    disposition: str
    model_claimed_passed: bool | None
    evidence_sha256: str
    evidence_byte_count: int
    refusal_codes: tuple[str, ...]
    schema_version: str = field(default=GATE_RECEIPT_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_stable_id(self.gate_id, "gate_id")
        if self.gate_id not in REQUIRED_GATE_IDS:
            _fail("gate_id is unsupported")
        _require_digest(self.packet_id, "packet_id")
        _require_digest(self.candidate_id, "candidate_id")
        _require_stable_id(self.evaluator_id, "evaluator_id")
        _require_string(self.disposition, "disposition", nonempty=True)
        if self.disposition not in GATE_DISPOSITIONS:
            _fail("gate disposition is unsupported")
        if self.model_claimed_passed is not None:
            _require_bool(self.model_claimed_passed, "model_claimed_passed")
        _require_digest(self.evidence_sha256, "evidence_sha256")
        _require_nonnegative_int(self.evidence_byte_count, "evidence_byte_count")
        codes = _validate_ordered_unique_strings(
            self.refusal_codes, "refusal_codes", maximum=MAX_REFUSALS
        )
        object.__setattr__(self, "refusal_codes", codes)
        if self.disposition == "PASS" and codes:
            _fail("PASS gate receipts cannot carry refusal codes")
        if self.disposition in {"FAIL", "REFUSED"} and not codes:
            _fail("FAIL/REFUSED gate receipts require refusal codes")
        if self.schema_version != GATE_RECEIPT_SCHEMA:
            _fail("gate receipt schema version is unsupported")
        if self.authority_effect != "None":
            _fail("gate receipts must carry AuthorityEffect None")

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "packet_id": self.packet_id,
            "candidate_id": self.candidate_id,
            "evaluator_id": self.evaluator_id,
            "disposition": self.disposition,
            "model_claimed_passed": self.model_claimed_passed,
            "evidence_sha256": self.evidence_sha256,
            "evidence_byte_count": self.evidence_byte_count,
            "refusal_codes": list(self.refusal_codes),
            "authority_effect": self.authority_effect,
        }

    @property
    def receipt_id(self) -> str:
        return domain_digest(GATE_RECEIPT_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            **self.identity_fields(),
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "GateReceiptV1":
        wire = _require_exact_dict(wire, "gate receipt")
        if "passed" in wire:
            _fail(
                "gate receipt field 'passed' is untrusted; use host disposition only"
            )
        if "promotion_eligible" in wire or "verified" in wire or "trusted" in wire:
            _fail("gate receipt carries forbidden authority-bearing fields")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "receipt_id",
                    "gate_id",
                    "packet_id",
                    "candidate_id",
                    "evaluator_id",
                    "disposition",
                    "model_claimed_passed",
                    "evidence_sha256",
                    "evidence_byte_count",
                    "refusal_codes",
                    "authority_effect",
                }
            ),
            "gate receipt",
        )
        expected = _require_digest(wire["receipt_id"], "receipt_id")
        receipt = cls(
            gate_id=_require_stable_id(wire["gate_id"], "gate_id"),
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            candidate_id=_require_digest(wire["candidate_id"], "candidate_id"),
            evaluator_id=_require_stable_id(wire["evaluator_id"], "evaluator_id"),
            disposition=_require_string(
                wire["disposition"], "disposition", nonempty=True
            ),
            model_claimed_passed=_require_optional_bool(
                wire["model_claimed_passed"], "model_claimed_passed"
            ),
            evidence_sha256=_require_digest(
                wire["evidence_sha256"], "evidence_sha256"
            ),
            evidence_byte_count=_require_nonnegative_int(
                wire["evidence_byte_count"], "evidence_byte_count"
            ),
            refusal_codes=_string_tuple_from_wire(
                wire["refusal_codes"], "refusal_codes", maximum=MAX_REFUSALS
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
        if expected != receipt.receipt_id:
            _fail("receipt_id does not match canonical wire content")
        return receipt
