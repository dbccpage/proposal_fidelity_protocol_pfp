"""Identity Links V1 Aggregate and Functions (1 class).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, replace
from typing import Any

from .authority_effect_v1 import AuthorityEffectV1
from .decision_status_v1 import DecisionStatusV1
from .identity_contract_error import IdentityContractError
from .identity_domain_v1 import IdentityDomainV1
from .identity_ref_v1 import IdentityRefV1
from .identity_slot_v1 import IdentitySlotV1
from .not_yet_created import NotYetCreated

IDENTITY_LINKS_SCHEMA_V1 = "omega.identity_links.v1"
MAX_IDENTITY_LINKS_BYTES = 4096
MAX_IDENTITY_SCHEMA_CHARS = 64
_REF_DIGEST_PREFIX = b"omega.identity_ref.v1\0"
_LINK_DIGEST_PREFIX = b"omega.identity_links.v1\0"
_SCHEMA_RE = re.compile(r"^[a-z0-9_.-]{1,64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ZERO_DIGEST = "0" * 64

APPLICATION_NOT_YET_CREATED = NotYetCreated(IdentitySlotV1.APPLICATION)
DECISION_NOT_YET_CREATED = NotYetCreated(IdentitySlotV1.DECISION)
EVIDENCE_NOT_YET_CREATED = NotYetCreated(IdentitySlotV1.EVIDENCE)
EXECUTION_NOT_YET_CREATED = NotYetCreated(IdentitySlotV1.EXECUTION)


def _require_exact_enum(value: object, enum_cls: type, code: str) -> None:
    if type(value) is not enum_cls:
        raise IdentityContractError(code)


def _require_ref_for_slot(
    value: object, domain: IdentityDomainV1, slot: IdentitySlotV1
) -> None:
    if type(value) is not IdentityRefV1:
        raise IdentityContractError(f"SLOT_{slot.name}_REQUIRES_REF")
    if value.domain is not domain:
        raise IdentityContractError(f"SLOT_{slot.name}_DOMAIN_MISMATCH")
    value.__post_init__()


def _require_ref_or_uncreated(
    value: object, domain: IdentityDomainV1, slot: IdentitySlotV1
) -> None:
    if type(value) is NotYetCreated:
        if value.slot is not slot:
            raise IdentityContractError(f"UNCREATED_SLOT_{slot.name}_MISMATCH")
        value.__post_init__()
        return
    _require_ref_for_slot(value, domain, slot)


@dataclass(frozen=True, slots=True)
class IdentityLinksV1:
    problem: IdentityRefV1
    presentation: IdentityRefV1
    execution: IdentityRefV1 | NotYetCreated = EXECUTION_NOT_YET_CREATED
    evidence: IdentityRefV1 | NotYetCreated = EVIDENCE_NOT_YET_CREATED
    decision: NotYetCreated = DECISION_NOT_YET_CREATED
    application: NotYetCreated = APPLICATION_NOT_YET_CREATED
    authority_effect: AuthorityEffectV1 = AuthorityEffectV1.NONE

    def __post_init__(self) -> None:
        _require_ref_for_slot(
            self.problem, IdentityDomainV1.PROBLEM, IdentitySlotV1.PROBLEM
        )
        _require_ref_for_slot(
            self.presentation,
            IdentityDomainV1.PRESENTATION,
            IdentitySlotV1.PRESENTATION,
        )
        _require_ref_or_uncreated(
            self.execution, IdentityDomainV1.EXECUTION, IdentitySlotV1.EXECUTION
        )
        _require_ref_or_uncreated(
            self.evidence, IdentityDomainV1.EVIDENCE, IdentitySlotV1.EVIDENCE
        )
        if type(self.decision) is not NotYetCreated:
            raise IdentityContractError("DECISION_MUST_BE_NOT_YET_CREATED")
        if self.decision.slot is not IdentitySlotV1.DECISION:
            raise IdentityContractError("DECISION_SLOT_MISMATCH")
        if type(self.application) is not NotYetCreated:
            raise IdentityContractError("APPLICATION_MUST_BE_NOT_YET_CREATED")
        if self.application.slot is not IdentitySlotV1.APPLICATION:
            raise IdentityContractError("APPLICATION_SLOT_MISMATCH")
        _require_exact_enum(
            self.authority_effect,
            AuthorityEffectV1,
            "AUTHORITY_EFFECT_TYPE_REFUSED",
        )
        if self.authority_effect is not AuthorityEffectV1.NONE:
            raise IdentityContractError("AUTHORITY_EFFECT_MUST_BE_NONE")

    def with_execution(self, execution: IdentityRefV1) -> IdentityLinksV1:
        self.__post_init__()
        if type(self.execution) is not NotYetCreated:
            raise IdentityContractError("EXECUTION_IDENTITY_ALREADY_CREATED")
        _require_ref_for_slot(
            execution, IdentityDomainV1.EXECUTION, IdentitySlotV1.EXECUTION
        )
        return replace(self, execution=execution)

    def with_evidence(self, evidence: IdentityRefV1) -> IdentityLinksV1:
        self.__post_init__()
        if type(self.execution) is not IdentityRefV1:
            raise IdentityContractError("EVIDENCE_PRECEDES_EXECUTION")
        if type(self.evidence) is not NotYetCreated:
            raise IdentityContractError("EVIDENCE_IDENTITY_ALREADY_CREATED")
        _require_ref_for_slot(
            evidence, IdentityDomainV1.EVIDENCE, IdentitySlotV1.EVIDENCE
        )
        return replace(self, evidence=evidence)


def _ref_wire(value: IdentityRefV1) -> dict[str, str]:
    value.__post_init__()
    return {
        "digest": value.digest,
        "domain": value.domain.value,
        "schema": value.schema,
    }


def _uncreated_wire(value: NotYetCreated) -> dict[str, str]:
    value.__post_init__()
    status = (
        DecisionStatusV1.NOT_YET_CREATED.value
        if value.slot is IdentitySlotV1.DECISION
        else "NOT_YET_CREATED"
    )
    return {"slot": value.slot.value, "status": status}


def _slot_wire(value: IdentityRefV1 | NotYetCreated) -> dict[str, str]:
    if type(value) is IdentityRefV1:
        return _ref_wire(value)
    if type(value) is NotYetCreated:
        return _uncreated_wire(value)
    raise IdentityContractError("IDENTITY_SLOT_TYPE_REFUSED")


def canonical_identity_links_bytes(links: IdentityLinksV1) -> bytes:
    if type(links) is not IdentityLinksV1:
        raise IdentityContractError("IDENTITY_LINKS_TYPE_REFUSED")
    links.__post_init__()
    wire = {
        "application": _uncreated_wire(links.application),
        "decision": _uncreated_wire(links.decision),
        "evidence": _slot_wire(links.evidence),
        "execution": _slot_wire(links.execution),
        "presentation": _ref_wire(links.presentation),
        "problem": _ref_wire(links.problem),
        "schema": IDENTITY_LINKS_SCHEMA_V1,
    }
    return json.dumps(
        wire,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def identity_links_sha256(links: IdentityLinksV1) -> str:
    return hashlib.sha256(
        _LINK_DIGEST_PREFIX + canonical_identity_links_bytes(links)
    ).hexdigest()


def identity_ref_from_bytes(
    domain: IdentityDomainV1, schema: str, payload: bytes
) -> IdentityRefV1:
    _require_exact_enum(domain, IdentityDomainV1, "IDENTITY_DOMAIN_TYPE_REFUSED")
    if (
        type(schema) is not str
        or len(schema) > MAX_IDENTITY_SCHEMA_CHARS
        or _SCHEMA_RE.fullmatch(schema) is None
    ):
        raise IdentityContractError("IDENTITY_SCHEMA_REFUSED")
    if type(payload) is not bytes:
        raise IdentityContractError("IDENTITY_PAYLOAD_BYTES_REQUIRED")
    frame = json.dumps(
        {"domain": domain.value, "schema": schema},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    digest = hashlib.sha256(_REF_DIGEST_PREFIX + frame + b"\0" + payload).hexdigest()
    return IdentityRefV1(domain=domain, schema=schema, digest=digest)


def _reject_number(_: str) -> None:
    raise IdentityContractError("JSON_NUMBER_REFUSED")


def _reject_constant(_: str) -> None:
    raise IdentityContractError("JSON_CONSTANT_REFUSED")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IdentityContractError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _exact_keys(raw: object, keys: frozenset[str], code: str) -> dict[str, Any]:
    if type(raw) is not dict or frozenset(raw) != keys:
        raise IdentityContractError(code)
    return raw


def _parse_ref(raw: object, expected: IdentityDomainV1) -> IdentityRefV1:
    value = _exact_keys(
        raw, frozenset({"digest", "domain", "schema"}), "IDENTITY_REF_WIRE_REFUSED"
    )
    if value["domain"] != expected.value:
        raise IdentityContractError("IDENTITY_DOMAIN_MISMATCH")
    return IdentityRefV1(expected, value["schema"], value["digest"])


def _parse_uncreated(raw: object, expected: IdentitySlotV1) -> NotYetCreated:
    value = _exact_keys(
        raw, frozenset({"slot", "status"}), "NOT_YET_CREATED_WIRE_REFUSED"
    )
    if value["slot"] != expected.value:
        raise IdentityContractError("NOT_YET_CREATED_SLOT_MISMATCH")
    expected_status = (
        DecisionStatusV1.NOT_YET_CREATED.value
        if expected is IdentitySlotV1.DECISION
        else "NOT_YET_CREATED"
    )
    if value["status"] != expected_status:
        raise IdentityContractError("FUTURE_IDENTITY_STATUS_REFUSED")
    return NotYetCreated(expected)


def _parse_optional_ref(
    raw: object, domain: IdentityDomainV1, slot: IdentitySlotV1
) -> IdentityRefV1 | NotYetCreated:
    if type(raw) is dict and frozenset(raw) == frozenset({"slot", "status"}):
        return _parse_uncreated(raw, slot)
    return _parse_ref(raw, domain)


def parse_identity_links_v1(data: bytes) -> IdentityLinksV1:
    if type(data) is not bytes:
        raise IdentityContractError("IDENTITY_LINKS_BYTES_REQUIRED")
    if not data or len(data) > MAX_IDENTITY_LINKS_BYTES:
        raise IdentityContractError("IDENTITY_LINKS_SIZE_REFUSED")
    try:
        text = data.decode("utf-8", errors="strict")
        raw = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_constant,
        )
    except IdentityContractError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise IdentityContractError("IDENTITY_LINKS_JSON_REFUSED") from exc

    root = _exact_keys(
        raw,
        frozenset(
            {
                "application",
                "decision",
                "evidence",
                "execution",
                "presentation",
                "problem",
                "schema",
            }
        ),
        "IDENTITY_LINKS_FIELDS_REFUSED",
    )
    if root["schema"] != IDENTITY_LINKS_SCHEMA_V1:
        raise IdentityContractError("IDENTITY_LINKS_SCHEMA_REFUSED")
    links = IdentityLinksV1(
        problem=_parse_ref(root["problem"], IdentityDomainV1.PROBLEM),
        presentation=_parse_ref(root["presentation"], IdentityDomainV1.PRESENTATION),
        execution=_parse_optional_ref(
            root["execution"], IdentityDomainV1.EXECUTION, IdentitySlotV1.EXECUTION
        ),
        evidence=_parse_optional_ref(
            root["evidence"], IdentityDomainV1.EVIDENCE, IdentitySlotV1.EVIDENCE
        ),
        decision=_parse_uncreated(root["decision"], IdentitySlotV1.DECISION),
        application=_parse_uncreated(root["application"], IdentitySlotV1.APPLICATION),
    )
    if canonical_identity_links_bytes(links) != data:
        raise IdentityContractError("NONCANONICAL_IDENTITY_LINKS_BYTES")
    return links


def verify_identity_links_v1(data: bytes, expected_sha256: str) -> IdentityLinksV1:
    if (
        type(expected_sha256) is not str
        or _DIGEST_RE.fullmatch(expected_sha256) is None
        or expected_sha256 == _ZERO_DIGEST
    ):
        raise IdentityContractError("EXPECTED_LINK_DIGEST_REFUSED")
    links = parse_identity_links_v1(data)
    observed = identity_links_sha256(links)
    if not hmac.compare_digest(observed, expected_sha256):
        raise IdentityContractError("IDENTITY_LINK_DIGEST_MISMATCH")
    return links
