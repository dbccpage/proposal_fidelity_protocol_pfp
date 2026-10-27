"""Strict, authority-null K0 bootstrap records and their canonical codec.

The records in this module bind propositions to exact bytes.  They do not
grant permission, authorize execution, waive policy, or perform an external
effect.  Parsing is deliberately stricter than ordinary JSON: accepted input
must already be the unique canonical representation of the validated record.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, Literal, NoReturn, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

_DEVIATION_SCHEMA = "core.swarm.bootstrap_deviation_spec.v1"
_ADOPTION_SCHEMA = "core.swarm.operator_policy_adoption_receipt.v1"
_DEVIATION_DOMAIN = b"engine/BootstrapDeviationSpecV1/v1\0"
_ADOPTION_DOMAIN = b"engine/OperatorPolicyAdoptionReceiptV1/v1\0"
_SAFE_INTEGER_LIMIT = (1 << 53) - 1
_LOWER_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LOWER_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_UTC_SECONDS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_LOCATOR_RE = re.compile(r"^(?P<scheme>[a-z][a-z0-9+.-]*):(?P<body>.+)$")
_T0_CONTROL_IDS = tuple(f"T0-{number:02d}" for number in range(1, 16))
_MAX_CANONICAL_BYTES = 262_144
_MAX_JSON_DEPTH = 64
_MAX_JSON_NODES = 10_000


class BootstrapContractError(ValueError):
    """A bootstrap codec or binding refusal with a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
    )


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty without edge whitespace")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{field} must contain only Unicode scalar values")
    try:
        normalized = unicodedata.normalize("NFC", value)
    except UnicodeError as error:
        raise ValueError(f"{field} could not be normalized") from error
    if normalized != value:
        raise ValueError(f"{field} must be NFC-normalized")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise ValueError(f"{field} must not contain control characters")
    return value


def _identifier(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if _IDENTIFIER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a stable identifier")
    return text


def _repository(value: Any) -> str:
    text = _text(value, field="repository")
    if _REPOSITORY_RE.fullmatch(text) is None:
        raise ValueError("repository must use owner/name form")
    owner, name = text.split("/", maxsplit=1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise ValueError("repository owner and name must not be dot components")
    return text


def _lower_hex(value: Any, *, field: str, pattern: re.Pattern[str]) -> str:
    text = _text(value, field=field)
    if pattern.fullmatch(text) is None:
        raise ValueError(f"{field} must be canonical lowercase hexadecimal")
    return text


def _timestamp(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if _UTC_SECONDS_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise ValueError(f"{field} is not a real UTC timestamp") from error
    return text


def _as_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _require_sorted_unique(
    values: Sequence[str], *, field: str, casefold_unique: bool = False
) -> tuple[str, ...]:
    canonical = tuple(values)
    if tuple(sorted(canonical, key=lambda item: item.encode("utf-8"))) != canonical:
        raise ValueError(f"{field} must be sorted by UTF-8 ordinal bytes")
    if len(set(canonical)) != len(canonical):
        raise ValueError(f"{field} must be unique")
    if casefold_unique and len({item.casefold() for item in canonical}) != len(
        canonical
    ):
        raise ValueError(f"{field} must be casefold collision-free")
    return canonical


def _relative_posix_path(value: Any) -> str:
    text = _text(value, field="scope path")
    if text == "." or "\\" in text or ":" in text or text.startswith("/"):
        raise ValueError("scope paths must be relative POSIX paths")
    path = PurePosixPath(text)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("scope paths must not contain empty, dot, or parent parts")
    if str(path) != text:
        raise ValueError("scope paths must already be normalized")
    return text


def _locator(value: Any) -> str:
    text = _text(value, field="external evidence locator")
    match = _LOCATOR_RE.fullmatch(text)
    if match is None:
        raise ValueError("external evidence locator must be a stable URI-like value")
    scheme = match.group("scheme")
    body = match.group("body")
    if scheme == "file" or len(scheme) == 1 or "\\" in body:
        raise ValueError("external evidence locator must not be a host path")
    if any(character.isspace() for character in text):
        raise ValueError("external evidence locator must not contain whitespace")
    return text


class MissingAutomationV1(_StrictFrozenModel):
    """One bootstrap automation that is explicitly not yet present."""

    automation_id: str
    description: str

    @field_validator("automation_id", mode="before")
    @classmethod
    def _validate_automation_id(cls, value: Any) -> str:
        return _identifier(value, field="automation_id")

    @field_validator("description", mode="before")
    @classmethod
    def _validate_description(cls, value: Any) -> str:
        return _text(value, field="description")


class CompensatingControlV1(_StrictFrozenModel):
    """One non-waivable manual control covering declared missing automation."""

    control_id: str
    description: str
    covers_automation_ids: tuple[str, ...]
    non_waivable: Literal[True] = True

    @field_validator("control_id", mode="before")
    @classmethod
    def _validate_control_id(cls, value: Any) -> str:
        return _identifier(value, field="control_id")

    @field_validator("description", mode="before")
    @classmethod
    def _validate_description(cls, value: Any) -> str:
        return _text(value, field="description")

    @field_validator("non_waivable", mode="before")
    @classmethod
    def _validate_non_waivable(cls, value: Any) -> bool:
        if type(value) is not bool or not value:
            raise ValueError("non_waivable must be the exact boolean true")
        return value

    @field_validator("covers_automation_ids")
    @classmethod
    def _validate_coverage(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("covers_automation_ids must not be empty")
        identifiers = tuple(
            _identifier(item, field="covers_automation_ids") for item in value
        )
        return _require_sorted_unique(identifiers, field="covers_automation_ids")


class ExternalEvidenceBindingV1(_StrictFrozenModel):
    """A stable external locator bound to the exact observed evidence bytes."""

    locator: str
    sha256: str

    @field_validator("locator", mode="before")
    @classmethod
    def _validate_locator(cls, value: Any) -> str:
        return _locator(value)

    @field_validator("sha256", mode="before")
    @classmethod
    def _validate_sha256(cls, value: Any) -> str:
        return _lower_hex(value, field="sha256", pattern=_LOWER_SHA256_RE)


class BootstrapDeviationSpecV1(_StrictFrozenModel):
    """An inert, finite declaration of K0's missing automation and controls."""

    schema_id: Literal["core.swarm.bootstrap_deviation_spec.v1"] = Field(
        default=_DEVIATION_SCHEMA, alias="schema"
    )
    authority_effect: Literal[None] = None
    creates_execution_authority: Literal[False] = False
    repository: str
    base_oid: str
    proposed_policy_sha256: str
    proposed_t0_sha256: str
    scope_paths: tuple[str, ...]
    missing_automation: tuple[MissingAutomationV1, ...]
    compensating_controls: tuple[CompensatingControlV1, ...]
    maximum_repository_writers: Literal[1] = 1
    issued_at: str
    expires_at: str
    retirement_condition: str
    residual_status: Literal["OPEN"] = "OPEN"

    @field_validator("repository", mode="before")
    @classmethod
    def _validate_repository(cls, value: Any) -> str:
        return _repository(value)

    @field_validator("creates_execution_authority", mode="before")
    @classmethod
    def _validate_execution_authority(cls, value: Any) -> bool:
        if type(value) is not bool or value:
            raise ValueError(
                "creates_execution_authority must be the exact boolean false"
            )
        return value

    @field_validator("maximum_repository_writers", mode="before")
    @classmethod
    def _validate_maximum_repository_writers(cls, value: Any) -> int:
        if type(value) is not int or value != 1:
            raise ValueError("maximum_repository_writers must be the exact integer 1")
        return value

    @field_validator("base_oid", mode="before")
    @classmethod
    def _validate_base_oid(cls, value: Any) -> str:
        return _lower_hex(value, field="base_oid", pattern=_LOWER_GIT_OID_RE)

    @field_validator("proposed_policy_sha256", "proposed_t0_sha256", mode="before")
    @classmethod
    def _validate_digest(cls, value: Any, info: ValidationInfo) -> str:
        return _lower_hex(value, field=info.field_name, pattern=_LOWER_SHA256_RE)

    @field_validator("scope_paths")
    @classmethod
    def _validate_scope_paths(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("scope_paths must not be empty")
        paths = tuple(_relative_posix_path(item) for item in value)
        return _require_sorted_unique(paths, field="scope_paths", casefold_unique=True)

    @field_validator("issued_at", "expires_at", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: Any, info: ValidationInfo) -> str:
        return _timestamp(value, field=info.field_name)

    @field_validator("retirement_condition", mode="before")
    @classmethod
    def _validate_retirement_condition(cls, value: Any) -> str:
        return _text(value, field="retirement_condition")

    @model_validator(mode="after")
    def _validate_deviation(self) -> BootstrapDeviationSpecV1:
        if _as_datetime(self.issued_at) >= _as_datetime(self.expires_at):
            raise ValueError("issued_at must precede expires_at")
        if not self.missing_automation:
            raise ValueError("missing_automation must not be empty")
        if not self.compensating_controls:
            raise ValueError("compensating_controls must not be empty")
        missing_ids = tuple(item.automation_id for item in self.missing_automation)
        control_ids = tuple(item.control_id for item in self.compensating_controls)
        _require_sorted_unique(missing_ids, field="missing_automation")
        _require_sorted_unique(control_ids, field="compensating_controls")
        missing_set = set(missing_ids)
        covered: set[str] = set()
        for control in self.compensating_controls:
            control_coverage = set(control.covers_automation_ids)
            if not control_coverage <= missing_set:
                raise ValueError(
                    "compensating controls may cover only declared missing automation"
                )
            covered.update(control_coverage)
        if covered != missing_set:
            raise ValueError("every missing automation must be covered")
        return self


class OperatorPolicyAdoptionReceiptV1(_StrictFrozenModel):
    """An inert record of an externally stated, independently observed adoption."""

    schema_id: Literal["core.swarm.operator_policy_adoption_receipt.v1"] = Field(
        default=_ADOPTION_SCHEMA, alias="schema"
    )
    authority_effect: Literal[None] = None
    creates_execution_authority: Literal[False] = False
    repository: str
    adopted_base_oid: str
    policy_sha256: str
    t0_sha256: str
    schema_bundle_sha256: str
    deviation_sha256: str
    external_evidence: ExternalEvidenceBindingV1
    adopter: str
    proposed_landing_operator: str
    adopted_t0_control_ids: tuple[str, ...]
    issued_at: str
    expires_at: str
    independent_observer: str

    @field_validator("repository", mode="before")
    @classmethod
    def _validate_repository(cls, value: Any) -> str:
        return _repository(value)

    @field_validator("creates_execution_authority", mode="before")
    @classmethod
    def _validate_execution_authority(cls, value: Any) -> bool:
        if type(value) is not bool or value:
            raise ValueError(
                "creates_execution_authority must be the exact boolean false"
            )
        return value

    @field_validator("adopted_base_oid", mode="before")
    @classmethod
    def _validate_base_oid(cls, value: Any) -> str:
        return _lower_hex(value, field="adopted_base_oid", pattern=_LOWER_GIT_OID_RE)

    @field_validator(
        "policy_sha256",
        "t0_sha256",
        "schema_bundle_sha256",
        "deviation_sha256",
        mode="before",
    )
    @classmethod
    def _validate_digest(cls, value: Any, info: ValidationInfo) -> str:
        return _lower_hex(value, field=info.field_name, pattern=_LOWER_SHA256_RE)

    @field_validator(
        "adopter",
        "proposed_landing_operator",
        "independent_observer",
        mode="before",
    )
    @classmethod
    def _validate_actor(cls, value: Any, info: ValidationInfo) -> str:
        text = _text(value, field=info.field_name)
        if any(character.isspace() for character in text):
            raise ValueError(f"{info.field_name} must be one stable actor identifier")
        return text

    @field_validator("adopted_t0_control_ids")
    @classmethod
    def _validate_t0_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        identifiers = tuple(
            _identifier(item, field="adopted_t0_control_ids") for item in value
        )
        _require_sorted_unique(identifiers, field="adopted_t0_control_ids")
        if identifiers != _T0_CONTROL_IDS:
            raise ValueError(
                "adopted_t0_control_ids must be exactly T0-01 through T0-15"
            )
        return identifiers

    @field_validator("issued_at", "expires_at", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: Any, info: ValidationInfo) -> str:
        return _timestamp(value, field=info.field_name)

    @model_validator(mode="after")
    def _validate_adoption(self) -> OperatorPolicyAdoptionReceiptV1:
        if _as_datetime(self.issued_at) >= _as_datetime(self.expires_at):
            raise ValueError("issued_at must precede expires_at")
        actors = (
            self.adopter,
            self.proposed_landing_operator,
            self.independent_observer,
        )
        if len({actor.casefold() for actor in actors}) != len(actors):
            raise ValueError(
                "adopter, landing operator, and observer must be pairwise distinct"
            )
        return self


BootstrapRecordV1: TypeAlias = (
    BootstrapDeviationSpecV1 | OperatorPolicyAdoptionReceiptV1
)


def _validate_unicode_scalar_string(value: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise BootstrapContractError(
            "NON_SCALAR_UNICODE", "strings must contain only Unicode scalar values"
        )
    try:
        normalized = unicodedata.normalize("NFC", value)
    except UnicodeError as error:
        raise BootstrapContractError(
            "INVALID_UNICODE", "string normalization failed"
        ) from error
    if normalized != value:
        raise BootstrapContractError("NON_NFC_STRING", "all strings must be NFC")
    if "\r" in value:
        raise BootstrapContractError(
            "CARRIAGE_RETURN_FORBIDDEN", "strings must not contain CR"
        )


def _walk_canonical_value(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    node_count = 0
    while stack:
        current, depth = stack.pop()
        node_count += 1
        if node_count > _MAX_JSON_NODES:
            raise BootstrapContractError(
                "JSON_NODE_LIMIT", "JSON value exceeds the canonical node ceiling"
            )
        if depth > _MAX_JSON_DEPTH:
            raise BootstrapContractError(
                "JSON_DEPTH_LIMIT", "JSON value exceeds the canonical depth ceiling"
            )
        if current is None or isinstance(current, (str, bool)):
            if isinstance(current, str):
                _validate_unicode_scalar_string(current)
            continue
        if isinstance(current, int):
            if not -_SAFE_INTEGER_LIMIT <= current <= _SAFE_INTEGER_LIMIT:
                raise BootstrapContractError(
                    "INTEGER_OUT_OF_RANGE",
                    "integer exceeds the interoperable safe range",
                )
            continue
        if isinstance(current, float):
            raise BootstrapContractError("FLOAT_FORBIDDEN", "floats are not canonical")
        if isinstance(current, Mapping):
            for key, child in current.items():
                if not isinstance(key, str):
                    raise BootstrapContractError(
                        "NON_STRING_KEY", "JSON keys must be strings"
                    )
                stack.append((child, depth + 1))
                stack.append((key, depth + 1))
            continue
        if isinstance(current, (list, tuple)):
            stack.extend((child, depth + 1) for child in current)
            continue
        raise BootstrapContractError(
            "UNSUPPORTED_JSON_TYPE",
            f"unsupported canonical value {type(current).__name__}",
        )


def canonical_bootstrap_json_bytes(record: BootstrapRecordV1) -> bytes:
    """Return the one compact, sorted, NFC UTF-8 representation plus one LF."""

    if type(record) not in {
        BootstrapDeviationSpecV1,
        OperatorPolicyAdoptionReceiptV1,
    }:
        raise BootstrapContractError(
            "UNSUPPORTED_RECORD", "record must be one frozen bootstrap v1 model"
        )
    try:
        value = record.model_dump(mode="python", by_alias=True)
        validated = type(record).model_validate(value, strict=True)
        value = validated.model_dump(mode="python", by_alias=True)
    except (RecursionError, UnicodeError) as error:
        raise BootstrapContractError(
            "STRUCTURE_LIMIT", "record serialization exceeded a safe host limit"
        ) from error
    except ValidationError as error:
        raise BootstrapContractError(
            "INVALID_RECORD", "record no longer satisfies its frozen schema"
        ) from error
    _walk_canonical_value(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        encoded = text.encode("utf-8") + b"\n"
    except (RecursionError, UnicodeError) as error:
        raise BootstrapContractError(
            "STRUCTURE_LIMIT", "record serialization exceeded a safe host limit"
        ) from error
    if len(encoded) > _MAX_CANONICAL_BYTES:
        raise BootstrapContractError(
            "INPUT_TOO_LARGE", "canonical record exceeds the byte ceiling"
        )
    return encoded


def bootstrap_record_sha256(record: BootstrapRecordV1) -> str:
    """Return the version- and contract-domain-separated record digest."""

    record_type = type(record)
    if record_type is BootstrapDeviationSpecV1:
        domain = _DEVIATION_DOMAIN
    elif record_type is OperatorPolicyAdoptionReceiptV1:
        domain = _ADOPTION_DOMAIN
    else:
        raise BootstrapContractError("UNSUPPORTED_RECORD", "unknown record contract")
    return hashlib.sha256(domain + canonical_bootstrap_json_bytes(record)).hexdigest()


def _duplicate_refusing_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BootstrapContractError(
                "DUPLICATE_KEY", f"duplicate JSON object key {key!r}"
            )
        result[key] = value
    return result


def _parse_safe_integer(token: str) -> int:
    value = int(token)
    if not -_SAFE_INTEGER_LIMIT <= value <= _SAFE_INTEGER_LIMIT:
        raise BootstrapContractError(
            "INTEGER_OUT_OF_RANGE", "integer exceeds the interoperable safe range"
        )
    return value


def _refuse_float(_: str) -> NoReturn:
    raise BootstrapContractError("FLOAT_FORBIDDEN", "floats are not canonical")


def _refuse_constant(_: str) -> NoReturn:
    raise BootstrapContractError("NONFINITE_FORBIDDEN", "non-finite values are invalid")


def _preflight_json_structure(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise BootstrapContractError(
                    "JSON_DEPTH_LIMIT", "JSON input exceeds the canonical depth ceiling"
                )
        elif character in "]}":
            depth -= 1


def _load_canonical_json(data: bytes) -> dict[str, Any]:
    if not isinstance(data, bytes):
        raise BootstrapContractError("BYTES_REQUIRED", "canonical input must be bytes")
    if data.startswith(b"\xef\xbb\xbf"):
        raise BootstrapContractError("UTF8_BOM_FORBIDDEN", "UTF-8 BOM is forbidden")
    if b"\r" in data:
        raise BootstrapContractError(
            "CARRIAGE_RETURN_FORBIDDEN", "canonical bytes must not contain CR"
        )
    if len(data) > _MAX_CANONICAL_BYTES:
        raise BootstrapContractError(
            "INPUT_TOO_LARGE", "canonical input exceeds the byte ceiling"
        )
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise BootstrapContractError("INVALID_UTF8", "input is not UTF-8") from error
    _preflight_json_structure(text)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_refusing_object,
            parse_int=_parse_safe_integer,
            parse_float=_refuse_float,
            parse_constant=_refuse_constant,
        )
    except BootstrapContractError:
        raise
    except RecursionError as error:
        raise BootstrapContractError(
            "JSON_DEPTH_LIMIT", "JSON decoder exceeded the canonical depth ceiling"
        ) from error
    except UnicodeError as error:
        raise BootstrapContractError(
            "INVALID_UNICODE", "JSON decoder encountered invalid Unicode"
        ) from error
    except json.JSONDecodeError as error:
        raise BootstrapContractError(
            "INVALID_JSON", "input is not one JSON value"
        ) from error
    if not isinstance(value, dict):
        raise BootstrapContractError("OBJECT_REQUIRED", "record must be a JSON object")
    _walk_canonical_value(value)
    return value


def _tuple_if_list(value: Any) -> Any:
    return tuple(value) if isinstance(value, list) else value


def _prepare_deviation(value: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(value)
    prepared["scope_paths"] = _tuple_if_list(prepared.get("scope_paths"))
    missing = prepared.get("missing_automation")
    if isinstance(missing, list):
        prepared["missing_automation"] = tuple(
            MissingAutomationV1.model_validate(item, strict=True) for item in missing
        )
    controls = prepared.get("compensating_controls")
    if isinstance(controls, list):
        nested: list[CompensatingControlV1] = []
        for item in controls:
            if isinstance(item, dict):
                item = dict(item)
                item["covers_automation_ids"] = _tuple_if_list(
                    item.get("covers_automation_ids")
                )
            nested.append(CompensatingControlV1.model_validate(item, strict=True))
        prepared["compensating_controls"] = tuple(nested)
    return prepared


def _prepare_adoption(value: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(value)
    prepared["adopted_t0_control_ids"] = _tuple_if_list(
        prepared.get("adopted_t0_control_ids")
    )
    evidence = prepared.get("external_evidence")
    if isinstance(evidence, dict):
        prepared["external_evidence"] = ExternalEvidenceBindingV1.model_validate(
            evidence, strict=True
        )
    return prepared


def _parse_record(
    data: bytes,
    *,
    expected_schema: str,
) -> BootstrapRecordV1:
    value = _load_canonical_json(data)
    if value.get("schema") != expected_schema:
        raise BootstrapContractError(
            "SCHEMA_MISMATCH", f"expected schema {expected_schema!r}"
        )
    try:
        if expected_schema == _DEVIATION_SCHEMA:
            record: BootstrapRecordV1 = BootstrapDeviationSpecV1.model_validate(
                _prepare_deviation(value), strict=True
            )
        else:
            record = OperatorPolicyAdoptionReceiptV1.model_validate(
                _prepare_adoption(value), strict=True
            )
    except BootstrapContractError:
        raise
    except RecursionError as error:
        raise BootstrapContractError(
            "STRUCTURE_LIMIT", "record validation exceeded a safe host limit"
        ) from error
    except UnicodeError as error:
        raise BootstrapContractError(
            "INVALID_UNICODE", "record validation encountered invalid Unicode"
        ) from error
    except (TypeError, ValueError) as error:
        raise BootstrapContractError(
            "INVALID_RECORD", "record violates its strict schema"
        ) from error
    if canonical_bootstrap_json_bytes(record) != data:
        raise BootstrapContractError(
            "NON_CANONICAL_BYTES", "input does not exactly match canonical bytes"
        )
    return record


def parse_bootstrap_deviation_spec_v1(data: bytes) -> BootstrapDeviationSpecV1:
    """Parse only exact canonical deviation bytes; expiry is checked separately."""

    record = _parse_record(data, expected_schema=_DEVIATION_SCHEMA)
    if type(record) is not BootstrapDeviationSpecV1:
        raise BootstrapContractError("SCHEMA_MISMATCH", "not a deviation record")
    return record


def parse_operator_policy_adoption_receipt_v1(
    data: bytes,
) -> OperatorPolicyAdoptionReceiptV1:
    """Parse only exact canonical adoption bytes; expiry is checked separately."""

    record = _parse_record(data, expected_schema=_ADOPTION_SCHEMA)
    if type(record) is not OperatorPolicyAdoptionReceiptV1:
        raise BootstrapContractError("SCHEMA_MISMATCH", "not an adoption record")
    return record


def validate_bootstrap_record_currency(
    record: BootstrapRecordV1, *, now: datetime
) -> None:
    """Refuse a record outside its issue/expiry interval using an injected clock."""

    if type(record) not in {
        BootstrapDeviationSpecV1,
        OperatorPolicyAdoptionReceiptV1,
    }:
        raise BootstrapContractError(
            "UNSUPPORTED_RECORD", "currency applies only to bootstrap v1 records"
        )
    if not isinstance(now, datetime):
        raise BootstrapContractError("INVALID_CLOCK", "now must be a datetime")
    if now.tzinfo is None or now.utcoffset() != UTC.utcoffset(now):
        raise BootstrapContractError("INVALID_CLOCK", "now must be UTC-aware")
    issued_at = _as_datetime(record.issued_at)
    expires_at = _as_datetime(record.expires_at)
    if now < issued_at:
        raise BootstrapContractError("NOT_YET_CURRENT", "record is not yet current")
    if now >= expires_at:
        raise BootstrapContractError("RECORD_EXPIRED", "record has expired")


def _sha256(data: bytes, *, field: str) -> str:
    if not isinstance(data, bytes):
        raise BootstrapContractError("BYTES_REQUIRED", f"{field} must be exact bytes")
    return hashlib.sha256(data).hexdigest()


def _expect(actual: str, expected: str, *, field: str) -> None:
    if actual != expected:
        raise BootstrapContractError(
            "BINDING_MISMATCH", f"{field} does not match the supplied exact value"
        )


def verify_operator_policy_adoption_binding(
    receipt_bytes: bytes,
    *,
    deviation_bytes: bytes,
    policy_bytes: bytes,
    t0_bytes: bytes,
    schema_bundle_bytes: bytes,
    external_evidence_locator: str,
    external_evidence_bytes: bytes,
    expected_repository: str,
    expected_base_oid: str,
    expected_adopter: str,
    expected_landing_operator: str,
    expected_observer: str,
    now: datetime,
) -> OperatorPolicyAdoptionReceiptV1:
    """Verify one receipt against every exact externally supplied binding.

    The result is validated evidence only.  A successful return has no
    authority effect and does not execute or authorize a repository action.
    """

    deviation = parse_bootstrap_deviation_spec_v1(deviation_bytes)
    receipt = parse_operator_policy_adoption_receipt_v1(receipt_bytes)

    policy_sha256 = _sha256(policy_bytes, field="policy_bytes")
    t0_sha256 = _sha256(t0_bytes, field="t0_bytes")
    schema_bundle_sha256 = _sha256(schema_bundle_bytes, field="schema_bundle_bytes")
    external_evidence_sha256 = _sha256(
        external_evidence_bytes, field="external_evidence_bytes"
    )

    _expect(deviation.repository, expected_repository, field="deviation.repository")
    _expect(deviation.base_oid, expected_base_oid, field="deviation.base_oid")
    _expect(
        deviation.proposed_policy_sha256,
        policy_sha256,
        field="deviation.proposed_policy_sha256",
    )
    _expect(
        deviation.proposed_t0_sha256,
        t0_sha256,
        field="deviation.proposed_t0_sha256",
    )

    _expect(receipt.repository, expected_repository, field="receipt.repository")
    _expect(
        receipt.adopted_base_oid, expected_base_oid, field="receipt.adopted_base_oid"
    )
    _expect(receipt.policy_sha256, policy_sha256, field="receipt.policy_sha256")
    _expect(receipt.t0_sha256, t0_sha256, field="receipt.t0_sha256")
    _expect(
        receipt.schema_bundle_sha256,
        schema_bundle_sha256,
        field="receipt.schema_bundle_sha256",
    )
    _expect(
        receipt.deviation_sha256,
        bootstrap_record_sha256(deviation),
        field="receipt.deviation_sha256",
    )
    try:
        canonical_evidence_locator = _locator(external_evidence_locator)
    except ValueError as error:
        raise BootstrapContractError(
            "INVALID_LOCATOR", "external evidence locator is not canonical"
        ) from error
    _expect(
        receipt.external_evidence.locator,
        canonical_evidence_locator,
        field="receipt.external_evidence.locator",
    )
    _expect(
        receipt.external_evidence.sha256,
        external_evidence_sha256,
        field="receipt.external_evidence.sha256",
    )
    _expect(receipt.adopter, expected_adopter, field="receipt.adopter")
    _expect(
        receipt.proposed_landing_operator,
        expected_landing_operator,
        field="receipt.proposed_landing_operator",
    )
    _expect(
        receipt.independent_observer,
        expected_observer,
        field="receipt.independent_observer",
    )

    validate_bootstrap_record_currency(deviation, now=now)
    validate_bootstrap_record_currency(receipt, now=now)
    return receipt


__all__ = (
    "BootstrapContractError",
    "BootstrapDeviationSpecV1",
    "CompensatingControlV1",
    "ExternalEvidenceBindingV1",
    "MissingAutomationV1",
    "OperatorPolicyAdoptionReceiptV1",
    "bootstrap_record_sha256",
    "canonical_bootstrap_json_bytes",
    "parse_bootstrap_deviation_spec_v1",
    "parse_operator_policy_adoption_receipt_v1",
    "validate_bootstrap_record_currency",
    "verify_operator_policy_adoption_binding",
)
