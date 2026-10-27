"""Executable anti-skill domain contracts.

Prompt Civilization owns these pure, closed types.  They describe detection
and admission evidence only: no object in this module repairs a subject,
activates itself, or grants authority.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, cast

from .canonical import canonical_id
from .constants import AUTHORITY_EFFECT_NONE, DIGEST_PATTERN, IDENTIFIER_PATTERN

MAX_ANTI_SKILL_ITEMS = 64
MAX_ANTI_SKILL_TEXT_BYTES = 4096
MAX_PREDICATE_ATOMS = 16

SUBJECT_SCHEMA_V1 = "core.antiskill.subject.v1"
PREDICATE_ATOM_SCHEMA_V1 = "core.antiskill.predicate-atom.v1"
PREDICATE_EXPRESSION_SCHEMA_V1 = "core.antiskill.predicate-expression.v1"
SPEC_SCHEMA_V2 = "core.antiskill.spec.v2"
FIXTURE_CASE_SCHEMA_V1 = "core.antiskill.fixture-case.v1"
FIXTURE_BANK_SCHEMA_V1 = "core.antiskill.fixture-bank.v1"
CASE_RESULT_SCHEMA_V1 = "core.antiskill.case-result.v1"
EVALUATION_RECEIPT_SCHEMA_V2 = "core.antiskill.evaluation-receipt.v2"
HUMAN_DECISION_SCHEMA_V1 = "core.antiskill.human-admission-decision.v1"
VERIFIED_REGISTRY_SCHEMA_V1 = "core.antiskill.verified-registry.v1"
ACTIVATION_PROFILE_SCHEMA_V1 = "core.antiskill.activation-profile.v1"
HIT_SCHEMA_V1 = "core.antiskill.hit.v1"

CLAIM_MODES = frozenset({"PROPOSAL", "BOUNDED", "UNRESTRICTED", "SELF_CERTIFIED"})
REQUESTED_EFFECTS = frozenset(
    {
        "NONE",
        "FINDING",
        "HOLD",
        "REFUSE",
        "ACTION_LICENSE",
        "ENGINE_TRANSITION",
        "MERGE",
        "PUBLISH",
    }
)
HIT_DISPOSITIONS = frozenset({"FINDING", "HOLD", "REFUSE"})
PREDICATE_OPERATORS = frozenset(
    {"EQUAL_FIELDS", "NOT_SUBSET_FIELDS", "VALUE_IN", "IS_EMPTY"}
)
PREDICATE_MODES = frozenset({"ALL", "ANY"})
SUBJECT_FIELDS = frozenset(
    {
        "claim_scope",
        "evidence_scope",
        "producer_identity",
        "verifier_identity",
        "claim_mode",
        "requested_effect",
        "approval_reference",
        "nonclaims",
    }
)
COLLECTION_FIELDS = frozenset({"claim_scope", "evidence_scope", "nonclaims"})
SCALAR_FIELDS = SUBJECT_FIELDS - COLLECTION_FIELDS


def _exact_object(value: Any, fields: frozenset[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ValueError(f"{label} must be an exact string-keyed object")
    wire = cast(dict[str, Any], value)
    missing = fields - set(wire)
    unknown = set(wire) - fields
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{label} unknown fields: {', '.join(sorted(unknown))}")
    return wire


def _text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be an exact string")
    if len(value.encode("utf-8")) > MAX_ANTI_SKILL_TEXT_BYTES:
        raise ValueError(f"{label} exceeds the text limit")
    if not allow_empty and (not value or value.strip() != value):
        raise ValueError(f"{label} must be a normalized nonempty string")
    if allow_empty and value and value.strip() != value:
        raise ValueError(f"{label} must be normalized")
    return value


def _identifier(value: Any, label: str) -> str:
    result = _text(value, label)
    if IDENTIFIER_PATTERN.fullmatch(result) is None:
        raise ValueError(f"{label} must be a canonical identifier")
    return result


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase sha256 digest")
    return value


def _exact_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be an exact boolean")
    return value


def _string_tuple(
    value: Any,
    label: str,
    *,
    identifiers: bool = False,
    digests: bool = False,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{label} must be an exact tuple")
    if len(value) > MAX_ANTI_SKILL_ITEMS:
        raise ValueError(f"{label} exceeds the item limit")
    parsed: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if identifiers:
            parsed.append(_identifier(item, item_label))
        elif digests:
            parsed.append(_digest(item, item_label))
        else:
            parsed.append(_text(item, item_label, allow_empty=allow_empty))
    if len(parsed) != len(set(parsed)):
        raise ValueError(f"{label} must not contain duplicates")
    return tuple(parsed)


def _wire_tuple(
    value: Any,
    label: str,
    *,
    identifiers: bool = False,
    digests: bool = False,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be an exact JSON array")
    return _string_tuple(
        tuple(value),
        label,
        identifiers=identifiers,
        digests=digests,
        allow_empty=allow_empty,
    )


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise TypeError("canonical JSON input must be an exact dictionary")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _semantic_id(schema: str, payload: Mapping[str, Any]) -> str:
    return cast(str, canonical_id(schema, dict(payload)))


@dataclass(frozen=True, slots=True)
class AntiSkillSubjectV1:
    claim_scope: tuple[str, ...]
    evidence_scope: tuple[str, ...]
    producer_identity: str
    verifier_identity: str
    claim_mode: str
    requested_effect: str
    approval_reference: str = ""
    nonclaims: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = SUBJECT_SCHEMA_V1
    subject_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claim_scope",
            _string_tuple(self.claim_scope, "claim_scope", identifiers=True),
        )
        object.__setattr__(
            self,
            "evidence_scope",
            _string_tuple(self.evidence_scope, "evidence_scope", identifiers=True),
        )
        if not self.claim_scope:
            raise ValueError("claim_scope must not be empty")
        _identifier(self.producer_identity, "producer_identity")
        _identifier(self.verifier_identity, "verifier_identity")
        if self.claim_mode not in CLAIM_MODES:
            raise ValueError("claim_mode is not closed")
        if self.requested_effect not in REQUESTED_EFFECTS:
            raise ValueError("requested_effect is not closed")
        if self.approval_reference:
            _digest(self.approval_reference, "approval_reference")
        object.__setattr__(
            self,
            "nonclaims",
            _string_tuple(self.nonclaims, "nonclaims"),
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("anti-skill subject authority_effect must be None")
        if self.schema_version != SUBJECT_SCHEMA_V1:
            raise ValueError("unsupported anti-skill subject schema")
        expected = _semantic_id(SUBJECT_SCHEMA_V1, self._payload())
        if self.subject_id and self.subject_id != expected:
            raise ValueError("subject_id does not match canonical content")
        object.__setattr__(self, "subject_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "claim_scope": list(self.claim_scope),
            "evidence_scope": list(self.evidence_scope),
            "producer_identity": self.producer_identity,
            "verifier_identity": self.verifier_identity,
            "claim_mode": self.claim_mode,
            "requested_effect": self.requested_effect,
            "approval_reference": self.approval_reference,
            "nonclaims": list(self.nonclaims),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "subject_id": self.subject_id}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillSubjectV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "claim_scope",
                    "evidence_scope",
                    "producer_identity",
                    "verifier_identity",
                    "claim_mode",
                    "requested_effect",
                    "approval_reference",
                    "nonclaims",
                    "authority_effect",
                    "schema_version",
                    "subject_id",
                }
            ),
            "anti-skill subject",
        )
        return cls(
            claim_scope=_wire_tuple(
                wire["claim_scope"], "claim_scope", identifiers=True
            ),
            evidence_scope=_wire_tuple(
                wire["evidence_scope"], "evidence_scope", identifiers=True
            ),
            producer_identity=_identifier(
                wire["producer_identity"], "producer_identity"
            ),
            verifier_identity=_identifier(
                wire["verifier_identity"], "verifier_identity"
            ),
            claim_mode=_text(wire["claim_mode"], "claim_mode"),
            requested_effect=_text(wire["requested_effect"], "requested_effect"),
            approval_reference=_text(
                wire["approval_reference"], "approval_reference", allow_empty=True
            ),
            nonclaims=_wire_tuple(wire["nonclaims"], "nonclaims"),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            subject_id=_digest(wire["subject_id"], "subject_id"),
        )


@dataclass(frozen=True, slots=True)
class PredicateAtomV1:
    operator: str
    fields: tuple[str, ...]
    values: tuple[str, ...] = ()
    schema_version: str = PREDICATE_ATOM_SCHEMA_V1

    def __post_init__(self) -> None:
        if self.operator not in PREDICATE_OPERATORS:
            raise ValueError("predicate operator is not closed")
        object.__setattr__(
            self, "fields", _string_tuple(self.fields, "fields", identifiers=True)
        )
        object.__setattr__(self, "values", _string_tuple(self.values, "values"))
        if not self.fields or any(field not in SUBJECT_FIELDS for field in self.fields):
            raise ValueError("predicate references an unknown subject field")
        if self.operator == "EQUAL_FIELDS":
            if len(self.fields) != 2 or self.values:
                raise ValueError(
                    "EQUAL_FIELDS requires exactly two fields and no values"
                )
            both_collection = all(field in COLLECTION_FIELDS for field in self.fields)
            both_scalar = all(field in SCALAR_FIELDS for field in self.fields)
            if not (both_collection or both_scalar):
                raise ValueError("EQUAL_FIELDS requires fields of the same kind")
        elif self.operator == "NOT_SUBSET_FIELDS":
            if len(self.fields) != 2 or self.values:
                raise ValueError(
                    "NOT_SUBSET_FIELDS requires exactly two collection fields and no values"
                )
            if any(field not in COLLECTION_FIELDS for field in self.fields):
                raise ValueError("NOT_SUBSET_FIELDS requires collection fields")
        elif self.operator == "VALUE_IN":
            if (
                len(self.fields) != 1
                or self.fields[0] not in SCALAR_FIELDS
                or not self.values
            ):
                raise ValueError(
                    "VALUE_IN requires one scalar field and at least one value"
                )
        elif self.operator == "IS_EMPTY":
            if len(self.fields) != 1 or self.values:
                raise ValueError("IS_EMPTY requires one field and no values")
        if self.schema_version != PREDICATE_ATOM_SCHEMA_V1:
            raise ValueError("unsupported predicate atom schema")

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": self.operator,
            "fields": list(self.fields),
            "values": list(self.values),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "PredicateAtomV1":
        wire = _exact_object(
            value,
            frozenset({"operator", "fields", "values", "schema_version"}),
            "predicate atom",
        )
        return cls(
            operator=_text(wire["operator"], "operator"),
            fields=_wire_tuple(wire["fields"], "fields", identifiers=True),
            values=_wire_tuple(wire["values"], "values"),
            schema_version=_text(wire["schema_version"], "schema_version"),
        )

    def matches(self, subject: AntiSkillSubjectV1) -> bool:
        if type(subject) is not AntiSkillSubjectV1:
            raise TypeError("predicate subject must be exact AntiSkillSubjectV1")
        left = getattr(subject, self.fields[0])
        if self.operator == "EQUAL_FIELDS":
            return left == getattr(subject, self.fields[1])
        if self.operator == "NOT_SUBSET_FIELDS":
            return not set(left).issubset(set(getattr(subject, self.fields[1])))
        if self.operator == "VALUE_IN":
            return left in self.values
        if self.operator == "IS_EMPTY":
            return not left
        raise AssertionError("unreachable predicate operator")


@dataclass(frozen=True, slots=True)
class PredicateExpressionV1:
    mode: str
    atoms: tuple[PredicateAtomV1, ...]
    schema_version: str = PREDICATE_EXPRESSION_SCHEMA_V1

    def __post_init__(self) -> None:
        if self.mode not in PREDICATE_MODES:
            raise ValueError("predicate mode is not closed")
        if type(self.atoms) is not tuple or not self.atoms:
            raise TypeError("predicate atoms must be a nonempty exact tuple")
        if len(self.atoms) > MAX_PREDICATE_ATOMS:
            raise ValueError("predicate expression exceeds the atom limit")
        if any(type(atom) is not PredicateAtomV1 for atom in self.atoms):
            raise TypeError("predicate expression contains a non-exact atom")
        if self.schema_version != PREDICATE_EXPRESSION_SCHEMA_V1:
            raise ValueError("unsupported predicate expression schema")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "atoms": [atom.to_dict() for atom in self.atoms],
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "PredicateExpressionV1":
        wire = _exact_object(
            value,
            frozenset({"mode", "atoms", "schema_version"}),
            "predicate expression",
        )
        if type(wire["atoms"]) is not list:
            raise ValueError("predicate atoms must be an exact JSON array")
        return cls(
            mode=_text(wire["mode"], "mode"),
            atoms=tuple(PredicateAtomV1.from_dict(atom) for atom in wire["atoms"]),
            schema_version=_text(wire["schema_version"], "schema_version"),
        )

    def matches(self, subject: AntiSkillSubjectV1) -> bool:
        results = tuple(atom.matches(subject) for atom in self.atoms)
        return all(results) if self.mode == "ALL" else any(results)


@dataclass(frozen=True, slots=True)
class AntiSkillSpecV2:
    spec_id: str = ""
    version: int = 1
    failure_code: str = "UNSPECIFIED_FAILURE"
    predicate: PredicateExpressionV1 | None = None
    disposition: str = "FINDING"
    protected_fields: tuple[str, ...] = ("claim_scope",)
    evidence_refs: tuple[str, ...] = ("ref_1",)
    counterexamples: tuple[str, ...] = ("ex_1",)
    implementation_digest: str = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    subject_schema: str = SUBJECT_SCHEMA_V1
    status: str = "PROPOSED"
    runtime_enforcement: bool = False
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = SPEC_SCHEMA_V2
    spec_digest: str = ""
    skill_id: str = ""

    def __post_init__(self) -> None:
        if self.status != "PROPOSED":
            raise ValueError("PROPOSED_STATUS_REQUIRED: anti-skill spec status must be PROPOSED")
        if type(self.runtime_enforcement) is not bool or self.runtime_enforcement:
            raise ValueError("RUNTIME_ENFORCEMENT_MUST_BE_FALSE: proposed anti-skill runtime_enforcement must be false")
        if self.skill_id and not self.spec_id:
            object.__setattr__(self, "spec_id", self.skill_id)
        if not self.skill_id and self.spec_id:
            object.__setattr__(self, "skill_id", self.spec_id)
        if self.predicate is None:
            object.__setattr__(
                self,
                "predicate",
                PredicateExpressionV1(
                    mode="ALL",
                    atoms=(
                        PredicateAtomV1(
                            operator="VALUE_IN",
                            fields=("claim_mode",),
                            values=("SELF_CERTIFIED",),
                        ),
                    ),
                ),
            )
        _identifier(self.spec_id, "spec_id")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("version must be an exact positive integer")
        _identifier(self.failure_code, "failure_code")
        if type(self.predicate) is not PredicateExpressionV1:
            raise TypeError("predicate must be exact PredicateExpressionV1")
        if self.disposition not in HIT_DISPOSITIONS:
            raise ValueError("disposition is not closed")
        object.__setattr__(
            self,
            "protected_fields",
            _string_tuple(self.protected_fields, "protected_fields", identifiers=True),
        )
        if not self.protected_fields or any(
            field not in SUBJECT_FIELDS for field in self.protected_fields
        ):
            raise ValueError("protected_fields must name subject fields")
        object.__setattr__(
            self, "evidence_refs", _string_tuple(self.evidence_refs, "evidence_refs")
        )
        object.__setattr__(
            self,
            "counterexamples",
            _string_tuple(self.counterexamples, "counterexamples"),
        )
        if not self.evidence_refs or not self.counterexamples:
            raise ValueError("spec requires evidence and counterexamples")
        _digest(self.implementation_digest, "implementation_digest")
        if self.subject_schema != SUBJECT_SCHEMA_V1:
            raise ValueError("spec subject schema is not supported")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("anti-skill spec authority_effect must be None")
        if self.schema_version != SPEC_SCHEMA_V2:
            raise ValueError("unsupported anti-skill spec schema")
        expected = _semantic_id(SPEC_SCHEMA_V2, self._payload())
        if self.spec_digest and self.spec_digest != expected:
            raise ValueError("spec_digest does not match canonical content")
        object.__setattr__(self, "spec_digest", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "version": self.version,
            "failure_code": self.failure_code,
            "predicate": self.predicate.to_dict(),
            "disposition": self.disposition,
            "protected_fields": list(self.protected_fields),
            "evidence_refs": list(self.evidence_refs),
            "counterexamples": list(self.counterexamples),
            "implementation_digest": self.implementation_digest,
            "subject_schema": self.subject_schema,
            "status": self.status,
            "runtime_enforcement": self.runtime_enforcement,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "spec_digest": self.spec_digest}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillSpecV2":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "spec_id",
                    "version",
                    "failure_code",
                    "predicate",
                    "disposition",
                    "protected_fields",
                    "evidence_refs",
                    "counterexamples",
                    "implementation_digest",
                    "subject_schema",
                    "status",
                    "runtime_enforcement",
                    "authority_effect",
                    "schema_version",
                    "spec_digest",
                }
            ),
            "anti-skill spec v2",
        )
        if type(wire["version"]) is not int:
            raise ValueError("version must be an exact integer")
        return cls(
            spec_id=_identifier(wire["spec_id"], "spec_id"),
            version=wire["version"],
            failure_code=_identifier(wire["failure_code"], "failure_code"),
            predicate=PredicateExpressionV1.from_dict(wire["predicate"]),
            disposition=_text(wire["disposition"], "disposition"),
            protected_fields=_wire_tuple(
                wire["protected_fields"], "protected_fields", identifiers=True
            ),
            evidence_refs=_wire_tuple(wire["evidence_refs"], "evidence_refs"),
            counterexamples=_wire_tuple(wire["counterexamples"], "counterexamples"),
            implementation_digest=_digest(
                wire["implementation_digest"], "implementation_digest"
            ),
            subject_schema=_text(wire["subject_schema"], "subject_schema"),
            status=_text(wire["status"], "status"),
            runtime_enforcement=_exact_bool(
                wire["runtime_enforcement"], "runtime_enforcement"
            ),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            spec_digest=_digest(wire["spec_digest"], "spec_digest"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillFixtureCaseV1:
    case_id: str
    spec_id: str
    context_key: str
    subject: AntiSkillSubjectV1
    expected_hit: bool
    negative_control: bool
    schema_version: str = FIXTURE_CASE_SCHEMA_V1
    case_digest: str = ""

    def __post_init__(self) -> None:
        _identifier(self.case_id, "case_id")
        _identifier(self.spec_id, "spec_id")
        _identifier(self.context_key, "context_key")
        if type(self.subject) is not AntiSkillSubjectV1:
            raise TypeError("fixture subject must be exact AntiSkillSubjectV1")
        _exact_bool(self.expected_hit, "expected_hit")
        _exact_bool(self.negative_control, "negative_control")
        if self.negative_control and self.expected_hit:
            raise ValueError("a negative control cannot expect a hit")
        if self.schema_version != FIXTURE_CASE_SCHEMA_V1:
            raise ValueError("unsupported fixture case schema")
        expected = _semantic_id(FIXTURE_CASE_SCHEMA_V1, self._payload())
        if self.case_digest and self.case_digest != expected:
            raise ValueError("case_digest does not match canonical content")
        object.__setattr__(self, "case_digest", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "spec_id": self.spec_id,
            "context_key": self.context_key,
            "subject": self.subject.to_dict(),
            "expected_hit": self.expected_hit,
            "negative_control": self.negative_control,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "case_digest": self.case_digest}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillFixtureCaseV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "case_id",
                    "spec_id",
                    "context_key",
                    "subject",
                    "expected_hit",
                    "negative_control",
                    "schema_version",
                    "case_digest",
                }
            ),
            "anti-skill fixture case",
        )
        return cls(
            case_id=_identifier(wire["case_id"], "case_id"),
            spec_id=_identifier(wire["spec_id"], "spec_id"),
            context_key=_identifier(wire["context_key"], "context_key"),
            subject=AntiSkillSubjectV1.from_dict(wire["subject"]),
            expected_hit=_exact_bool(wire["expected_hit"], "expected_hit"),
            negative_control=_exact_bool(wire["negative_control"], "negative_control"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            case_digest=_digest(wire["case_digest"], "case_digest"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillFixtureBankV1:
    cases: tuple[AntiSkillFixtureCaseV1, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = FIXTURE_BANK_SCHEMA_V1
    bank_id: str = ""

    def __post_init__(self) -> None:
        if type(self.cases) is not tuple or not self.cases:
            raise TypeError("fixture bank cases must be a nonempty exact tuple")
        if len(self.cases) > MAX_ANTI_SKILL_ITEMS:
            raise ValueError("fixture bank exceeds the case limit")
        if any(type(case) is not AntiSkillFixtureCaseV1 for case in self.cases):
            raise TypeError("fixture bank contains a non-exact case")
        if tuple(sorted(self.cases, key=lambda item: item.case_id)) != self.cases:
            raise ValueError("fixture cases must be sorted by case_id")
        case_ids = tuple(case.case_id for case in self.cases)
        subject_ids = tuple(case.subject.subject_id for case in self.cases)
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("fixture case ids must be unique")
        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError("copied fixture subjects are forbidden")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("fixture bank authority_effect must be None")
        if self.schema_version != FIXTURE_BANK_SCHEMA_V1:
            raise ValueError("unsupported fixture bank schema")
        expected = _semantic_id(FIXTURE_BANK_SCHEMA_V1, self._payload())
        if self.bank_id and self.bank_id != expected:
            raise ValueError("bank_id does not match canonical content")
        object.__setattr__(self, "bank_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "cases": [case.to_dict() for case in self.cases],
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "bank_id": self.bank_id}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillFixtureBankV1":
        wire = _exact_object(
            value,
            frozenset({"cases", "authority_effect", "schema_version", "bank_id"}),
            "anti-skill fixture bank",
        )
        if type(wire["cases"]) is not list:
            raise ValueError("fixture cases must be an exact JSON array")
        return cls(
            cases=tuple(
                AntiSkillFixtureCaseV1.from_dict(case) for case in wire["cases"]
            ),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            bank_id=_digest(wire["bank_id"], "bank_id"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillCaseResultV1:
    case_id: str
    case_digest: str
    expected_hit: bool
    observed_hit: bool
    negative_control: bool
    passed: bool
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = CASE_RESULT_SCHEMA_V1
    result_id: str = ""

    def __post_init__(self) -> None:
        _identifier(self.case_id, "case_id")
        _digest(self.case_digest, "case_digest")
        for field in ("expected_hit", "observed_hit", "negative_control", "passed"):
            _exact_bool(getattr(self, field), field)
        computed = self.expected_hit == self.observed_hit
        if self.negative_control:
            computed = computed and not self.observed_hit
        if self.passed != computed:
            raise ValueError("case result passed is not independently derived")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("case result authority_effect must be None")
        if self.schema_version != CASE_RESULT_SCHEMA_V1:
            raise ValueError("unsupported case result schema")
        expected = _semantic_id(CASE_RESULT_SCHEMA_V1, self._payload())
        if self.result_id and self.result_id != expected:
            raise ValueError("result_id does not match canonical content")
        object.__setattr__(self, "result_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_digest": self.case_digest,
            "expected_hit": self.expected_hit,
            "observed_hit": self.observed_hit,
            "negative_control": self.negative_control,
            "passed": self.passed,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "result_id": self.result_id}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillCaseResultV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "case_id",
                    "case_digest",
                    "expected_hit",
                    "observed_hit",
                    "negative_control",
                    "passed",
                    "authority_effect",
                    "schema_version",
                    "result_id",
                }
            ),
            "anti-skill case result",
        )
        return cls(
            case_id=_identifier(wire["case_id"], "case_id"),
            case_digest=_digest(wire["case_digest"], "case_digest"),
            expected_hit=_exact_bool(wire["expected_hit"], "expected_hit"),
            observed_hit=_exact_bool(wire["observed_hit"], "observed_hit"),
            negative_control=_exact_bool(wire["negative_control"], "negative_control"),
            passed=_exact_bool(wire["passed"], "passed"),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            result_id=_digest(wire["result_id"], "result_id"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillEvaluationReceiptV2:
    spec_digest: str
    fixture_bank_id: str
    implementation_digest: str
    case_results: tuple[AntiSkillCaseResultV1, ...]
    context_keys: tuple[str, ...]
    outcome: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = EVALUATION_RECEIPT_SCHEMA_V2
    receipt_id: str = ""

    def __post_init__(self) -> None:
        _digest(self.spec_digest, "spec_digest")
        _digest(self.fixture_bank_id, "fixture_bank_id")
        _digest(self.implementation_digest, "implementation_digest")
        if type(self.case_results) is not tuple or not self.case_results:
            raise TypeError("evaluation receipt requires exact case results")
        if any(
            type(result) is not AntiSkillCaseResultV1 for result in self.case_results
        ):
            raise TypeError("evaluation receipt contains a non-exact case result")
        if (
            tuple(sorted(self.case_results, key=lambda item: item.case_id))
            != self.case_results
        ):
            raise ValueError("case results must be sorted by case_id")
        if len({result.case_id for result in self.case_results}) != len(
            self.case_results
        ):
            raise ValueError("case result ids must be unique")
        object.__setattr__(
            self,
            "context_keys",
            _string_tuple(self.context_keys, "context_keys", identifiers=True),
        )
        if len(self.context_keys) < 2:
            raise ValueError("evaluation requires independent fixture contexts")
        computed_outcome = (
            "COMPUTED_PASS"
            if all(result.passed for result in self.case_results)
            else "COMPUTED_FAIL"
        )
        if self.outcome != computed_outcome:
            raise ValueError("evaluation outcome is not independently derived")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("evaluation receipt authority_effect must be None")
        if self.schema_version != EVALUATION_RECEIPT_SCHEMA_V2:
            raise ValueError("unsupported evaluation receipt schema")
        expected = _semantic_id(EVALUATION_RECEIPT_SCHEMA_V2, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "spec_digest": self.spec_digest,
            "fixture_bank_id": self.fixture_bank_id,
            "implementation_digest": self.implementation_digest,
            "case_results": [result.to_dict() for result in self.case_results],
            "context_keys": list(self.context_keys),
            "outcome": self.outcome,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillEvaluationReceiptV2":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "spec_digest",
                    "fixture_bank_id",
                    "implementation_digest",
                    "case_results",
                    "context_keys",
                    "outcome",
                    "authority_effect",
                    "schema_version",
                    "receipt_id",
                }
            ),
            "anti-skill evaluation receipt v2",
        )
        if type(wire["case_results"]) is not list:
            raise ValueError("case_results must be an exact JSON array")
        return cls(
            spec_digest=_digest(wire["spec_digest"], "spec_digest"),
            fixture_bank_id=_digest(wire["fixture_bank_id"], "fixture_bank_id"),
            implementation_digest=_digest(
                wire["implementation_digest"], "implementation_digest"
            ),
            case_results=tuple(
                AntiSkillCaseResultV1.from_dict(item) for item in wire["case_results"]
            ),
            context_keys=_wire_tuple(
                wire["context_keys"], "context_keys", identifiers=True
            ),
            outcome=_text(wire["outcome"], "outcome"),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            receipt_id=_digest(wire["receipt_id"], "receipt_id"),
        )


@dataclass(frozen=True, slots=True)
class HumanAntiSkillAdmissionDecisionV1:
    reviewer_identity: str
    spec_digest: str
    evaluation_receipt_id: str
    decision: str
    approval_reference: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = HUMAN_DECISION_SCHEMA_V1
    decision_id: str = ""

    def __post_init__(self) -> None:
        _identifier(self.reviewer_identity, "reviewer_identity")
        _digest(self.spec_digest, "spec_digest")
        _digest(self.evaluation_receipt_id, "evaluation_receipt_id")
        if self.decision not in {"APPROVE", "REJECT"}:
            raise ValueError("human admission decision is not closed")
        _digest(self.approval_reference, "approval_reference")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("human admission decision authority_effect must be None")
        if self.schema_version != HUMAN_DECISION_SCHEMA_V1:
            raise ValueError("unsupported human admission decision schema")
        expected = _semantic_id(HUMAN_DECISION_SCHEMA_V1, self._payload())
        if self.decision_id and self.decision_id != expected:
            raise ValueError("decision_id does not match canonical content")
        object.__setattr__(self, "decision_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "reviewer_identity": self.reviewer_identity,
            "spec_digest": self.spec_digest,
            "evaluation_receipt_id": self.evaluation_receipt_id,
            "decision": self.decision,
            "approval_reference": self.approval_reference,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "decision_id": self.decision_id}

    @classmethod
    def from_dict(cls, value: Any) -> "HumanAntiSkillAdmissionDecisionV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "reviewer_identity",
                    "spec_digest",
                    "evaluation_receipt_id",
                    "decision",
                    "approval_reference",
                    "authority_effect",
                    "schema_version",
                    "decision_id",
                }
            ),
            "human anti-skill admission decision",
        )
        return cls(
            reviewer_identity=_identifier(
                wire["reviewer_identity"], "reviewer_identity"
            ),
            spec_digest=_digest(wire["spec_digest"], "spec_digest"),
            evaluation_receipt_id=_digest(
                wire["evaluation_receipt_id"], "evaluation_receipt_id"
            ),
            decision=_text(wire["decision"], "decision"),
            approval_reference=_digest(
                wire["approval_reference"], "approval_reference"
            ),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            decision_id=_digest(wire["decision_id"], "decision_id"),
        )


@dataclass(frozen=True, slots=True)
class VerifiedAntiSkillRegistryV1:
    specs: tuple[AntiSkillSpecV2, ...]
    evaluation_receipts: tuple[AntiSkillEvaluationReceiptV2, ...]
    admission_decisions: tuple[HumanAntiSkillAdmissionDecisionV1, ...]
    verifier_implementation_digest: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = VERIFIED_REGISTRY_SCHEMA_V1
    registry_id: str = ""

    def __post_init__(self) -> None:
        for label, values, expected_type in (
            ("specs", self.specs, AntiSkillSpecV2),
            (
                "evaluation_receipts",
                self.evaluation_receipts,
                AntiSkillEvaluationReceiptV2,
            ),
            (
                "admission_decisions",
                self.admission_decisions,
                HumanAntiSkillAdmissionDecisionV1,
            ),
        ):
            if type(values) is not tuple or any(
                type(item) is not expected_type for item in values
            ):
                raise TypeError(f"{label} must be an exact typed tuple")
            if len(values) > MAX_ANTI_SKILL_ITEMS:
                raise ValueError(f"{label} exceeds the item limit")
        if tuple(sorted(self.specs, key=lambda item: item.spec_id)) != self.specs:
            raise ValueError("verified registry specs must be sorted")
        if not (
            len(self.specs)
            == len(self.evaluation_receipts)
            == len(self.admission_decisions)
        ):
            raise ValueError("verified registry evidence is not one-to-one")
        receipts_by_spec = {
            receipt.spec_digest: receipt for receipt in self.evaluation_receipts
        }
        decisions_by_spec = {
            decision.spec_digest: decision for decision in self.admission_decisions
        }
        if len(receipts_by_spec) != len(self.evaluation_receipts):
            raise ValueError("verified registry duplicates an evaluation spec digest")
        if len(decisions_by_spec) != len(self.admission_decisions):
            raise ValueError("verified registry duplicates a decision spec digest")
        for spec in self.specs:
            receipt = receipts_by_spec.get(spec.spec_digest)
            decision = decisions_by_spec.get(spec.spec_digest)
            if receipt is None or decision is None:
                raise ValueError("verified registry omits spec evidence")
            if receipt.outcome != "COMPUTED_PASS":
                raise ValueError(
                    "verified registry contains failed evaluation evidence"
                )
            if decision.decision != "APPROVE":
                raise ValueError("verified registry contains a non-approval decision")
            if decision.evaluation_receipt_id != receipt.receipt_id:
                raise ValueError("verified registry decision and receipt differ")
        _digest(self.verifier_implementation_digest, "verifier_implementation_digest")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("verified registry authority_effect must be None")
        if self.schema_version != VERIFIED_REGISTRY_SCHEMA_V1:
            raise ValueError("unsupported verified registry schema")
        expected = _semantic_id(VERIFIED_REGISTRY_SCHEMA_V1, self._payload())
        if self.registry_id and self.registry_id != expected:
            raise ValueError("registry_id does not match canonical content")
        object.__setattr__(self, "registry_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "specs": [spec.to_dict() for spec in self.specs],
            "evaluation_receipts": [
                receipt.to_dict() for receipt in self.evaluation_receipts
            ],
            "admission_decisions": [
                decision.to_dict() for decision in self.admission_decisions
            ],
            "verifier_implementation_digest": self.verifier_implementation_digest,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "registry_id": self.registry_id}

    @classmethod
    def from_dict(cls, value: Any) -> "VerifiedAntiSkillRegistryV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "specs",
                    "evaluation_receipts",
                    "admission_decisions",
                    "verifier_implementation_digest",
                    "authority_effect",
                    "schema_version",
                    "registry_id",
                }
            ),
            "verified anti-skill registry",
        )
        for field in ("specs", "evaluation_receipts", "admission_decisions"):
            if type(wire[field]) is not list:
                raise ValueError(f"{field} must be an exact JSON array")
        return cls(
            specs=tuple(AntiSkillSpecV2.from_dict(item) for item in wire["specs"]),
            evaluation_receipts=tuple(
                AntiSkillEvaluationReceiptV2.from_dict(item)
                for item in wire["evaluation_receipts"]
            ),
            admission_decisions=tuple(
                HumanAntiSkillAdmissionDecisionV1.from_dict(item)
                for item in wire["admission_decisions"]
            ),
            verifier_implementation_digest=_digest(
                wire["verifier_implementation_digest"],
                "verifier_implementation_digest",
            ),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            registry_id=_digest(wire["registry_id"], "registry_id"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillActivationProfileV1:
    profile_id: str
    registry_id: str
    active_spec_ids: tuple[str, ...]
    subject_scopes: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = ACTIVATION_PROFILE_SCHEMA_V1
    profile_digest: str = ""

    def __post_init__(self) -> None:
        _identifier(self.profile_id, "profile_id")
        _digest(self.registry_id, "registry_id")
        object.__setattr__(
            self,
            "active_spec_ids",
            _string_tuple(self.active_spec_ids, "active_spec_ids", identifiers=True),
        )
        object.__setattr__(
            self,
            "subject_scopes",
            _string_tuple(self.subject_scopes, "subject_scopes", identifiers=True),
        )
        if not self.active_spec_ids or not self.subject_scopes:
            raise ValueError("activation profile requires specs and subject scopes")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("activation profile authority_effect must be None")
        if self.schema_version != ACTIVATION_PROFILE_SCHEMA_V1:
            raise ValueError("unsupported activation profile schema")
        expected = _semantic_id(ACTIVATION_PROFILE_SCHEMA_V1, self._payload())
        if self.profile_digest and self.profile_digest != expected:
            raise ValueError("profile_digest does not match canonical content")
        object.__setattr__(self, "profile_digest", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "registry_id": self.registry_id,
            "active_spec_ids": list(self.active_spec_ids),
            "subject_scopes": list(self.subject_scopes),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "profile_digest": self.profile_digest}

    @classmethod
    def from_dict(cls, value: Any) -> "AntiSkillActivationProfileV1":
        wire = _exact_object(
            value,
            frozenset(
                {
                    "profile_id",
                    "registry_id",
                    "active_spec_ids",
                    "subject_scopes",
                    "authority_effect",
                    "schema_version",
                    "profile_digest",
                }
            ),
            "anti-skill activation profile",
        )
        return cls(
            profile_id=_identifier(wire["profile_id"], "profile_id"),
            registry_id=_digest(wire["registry_id"], "registry_id"),
            active_spec_ids=_wire_tuple(
                wire["active_spec_ids"], "active_spec_ids", identifiers=True
            ),
            subject_scopes=_wire_tuple(
                wire["subject_scopes"], "subject_scopes", identifiers=True
            ),
            authority_effect=_text(wire["authority_effect"], "authority_effect"),
            schema_version=_text(wire["schema_version"], "schema_version"),
            profile_digest=_digest(wire["profile_digest"], "profile_digest"),
        )


@dataclass(frozen=True, slots=True)
class AntiSkillHitV1:
    spec_id: str
    failure_code: str
    disposition: str
    subject_id: str
    protected_fields: tuple[str, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = HIT_SCHEMA_V1
    hit_id: str = ""

    def __post_init__(self) -> None:
        _identifier(self.spec_id, "spec_id")
        _identifier(self.failure_code, "failure_code")
        if self.disposition not in HIT_DISPOSITIONS:
            raise ValueError("hit disposition is not closed")
        _digest(self.subject_id, "subject_id")
        object.__setattr__(
            self,
            "protected_fields",
            _string_tuple(self.protected_fields, "protected_fields", identifiers=True),
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("anti-skill hit authority_effect must be None")
        if self.schema_version != HIT_SCHEMA_V1:
            raise ValueError("unsupported anti-skill hit schema")
        expected = _semantic_id(HIT_SCHEMA_V1, self._payload())
        if self.hit_id and self.hit_id != expected:
            raise ValueError("hit_id does not match canonical content")
        object.__setattr__(self, "hit_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "spec_id": self.spec_id,
            "failure_code": self.failure_code,
            "disposition": self.disposition,
            "subject_id": self.subject_id,
            "protected_fields": list(self.protected_fields),
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "hit_id": self.hit_id}


__all__ = [
    "ACTIVATION_PROFILE_SCHEMA_V1",
    "AntiSkillActivationProfileV1",
    "AntiSkillCaseResultV1",
    "AntiSkillEvaluationReceiptV2",
    "AntiSkillFixtureBankV1",
    "AntiSkillFixtureCaseV1",
    "AntiSkillHitV1",
    "AntiSkillSpecV2",
    "AntiSkillSubjectV1",
    "HumanAntiSkillAdmissionDecisionV1",
    "PredicateAtomV1",
    "PredicateExpressionV1",
    "SUBJECT_SCHEMA_V1",
    "VerifiedAntiSkillRegistryV1",
    "canonical_json_bytes",
]
