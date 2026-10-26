"""Infrastructure serialization and canonical JSON encoding for local_ci Bounded Context."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any, NoReturn

from pydantic import BaseModel

from omega_engine_operations.domain.cicd import (
    CanonicalCandidateManifestV1,
    GateResult,
    LocalCiExecutionReceiptV3,
    LocalCiInvocationV1,
    LocalCiVerificationInputsV1,
    ResolvedGateInvocationV1,
)
from omega_engine_operations.domain.cicd.catalog import GATE_CATALOG_V3
from omega_engine_operations.domain.cicd.constants import (
    _CATALOG_DOMAIN,
    _MANIFEST_DOMAIN,
    _MAX_CANONICAL_BYTES,
    _MAX_INTEGER_LEXEME_DIGITS,
    _MAX_JSON_DEPTH,
    _MAX_JSON_NODES,
    _RECEIPT_SCHEMA,
    _RESULTS_DOMAIN,
    _SAFE_INTEGER_LIMIT,
)
from omega_engine_operations.domain.cicd.digests import (
    resolved_invocation_digest as domain_resolved_invocation_digest,
)
from omega_engine_operations.domain.cicd.errors import (
    LocalCiReceiptError,
    LocalCiReceiptErrorCode,
)


def _validate_unicode_scalar_string(value: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.NON_SCALAR_UNICODE,
            "strings must contain Unicode scalar values",
        )
    if not unicodedata.is_normalized("NFC", value):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.NON_NFC_STRING,
            "all strings must be NFC-normalized",
        )


def _walk_canonical_value(value: Any) -> None:
    stack: list[tuple[Any, int]] = [(value, 1)]
    nodes = 0
    max_nodes = _MAX_JSON_NODES
    max_depth = _MAX_JSON_DEPTH
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.JSON_NODE_LIMIT,
                "JSON value exceeds the node ceiling",
            )
        if depth > max_depth:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.JSON_DEPTH_LIMIT,
                "JSON value exceeds the depth ceiling",
            )
        _validate_and_expand_node(current, depth=depth, stack=stack)


def _validate_and_expand_node(
    current: Any,
    *,
    depth: int,
    stack: list[tuple[Any, int]],
) -> None:
    if current is None or isinstance(current, (str, bool)):
        if isinstance(current, str):
            _validate_unicode_scalar_string(current)
        return
    if type(current) is int:
        if not -_SAFE_INTEGER_LIMIT <= current <= _SAFE_INTEGER_LIMIT:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.INVALID_RECORD,
                "integer exceeds the interoperable safe range",
            )
        return
    if isinstance(current, float):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.FLOAT_FORBIDDEN,
            "floats are not canonical",
        )
    if isinstance(current, Mapping):
        _expand_mapping(current, depth=depth, stack=stack)
        return
    if isinstance(current, (list, tuple)):
        stack.extend((child, depth + 1) for child in current)
        return
    raise LocalCiReceiptError(
        LocalCiReceiptErrorCode.INVALID_RECORD,
        f"unsupported canonical type {type(current).__name__}",
    )


def _expand_mapping(
    current: Mapping[Any, Any],
    *,
    depth: int,
    stack: list[tuple[Any, int]],
) -> None:
    for key, child in current.items():
        if not isinstance(key, str):
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.INVALID_RECORD,
                "JSON object keys must be strings",
            )
        stack.append((child, depth + 1))
        stack.append((key, depth + 1))


def _duplicate_refusing_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LocalCiReceiptError(
                LocalCiReceiptErrorCode.DUPLICATE_KEY,
                f"duplicate JSON key {key!r}",
            )
        result[key] = value
    return result


def _parse_integer(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    if len(digits) > _MAX_INTEGER_LEXEME_DIGITS:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INTEGER_LEXEME_TOO_LONG,
            "integer lexeme exceeds the canonical digit ceiling",
        )
    try:
        value = int(token)
    except (ValueError, RuntimeError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_JSON,
            "integer lexeme cannot be converted safely",
        ) from error
    if not -_SAFE_INTEGER_LIMIT <= value <= _SAFE_INTEGER_LIMIT:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "integer exceeds the interoperable safe range",
        )
    return value


def _refuse_float(_: str) -> NoReturn:
    raise LocalCiReceiptError(
        LocalCiReceiptErrorCode.FLOAT_FORBIDDEN, "floats are not canonical"
    )


def _refuse_constant(_: str) -> NoReturn:
    raise LocalCiReceiptError(
        LocalCiReceiptErrorCode.NONFINITE_FORBIDDEN,
        "non-finite values are not JSON",
    )


def _unquoted_structure(text: str) -> list[str]:
    structure: list[str] = []
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
        elif character == '"':
            in_string = True
        elif character in "[]{}":
            structure.append(character)
    return structure


def _preflight_depth(text: str) -> None:
    depth = 0
    for character in _unquoted_structure(text):
        if character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise LocalCiReceiptError(
                    LocalCiReceiptErrorCode.JSON_DEPTH_LIMIT,
                    "JSON input exceeds the depth ceiling",
                )
        else:
            depth -= 1
            if depth < 0:
                raise LocalCiReceiptError(
                    LocalCiReceiptErrorCode.INVALID_JSON,
                    "unbalanced JSON structure",
                )


def _load_json_value(data: bytes) -> dict[str, Any]:
    if type(data) is not bytes:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.BYTES_REQUIRED,
            "canonical receipt input must be bytes",
        )
    if len(data) > _MAX_CANONICAL_BYTES:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INPUT_TOO_LARGE,
            "receipt exceeds the byte ceiling",
        )
    if data.startswith(b"\xef\xbb\xbf"):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.UTF8_BOM_FORBIDDEN,
            "UTF-8 BOM is forbidden",
        )
    if b"\r" in data:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.CARRIAGE_RETURN_FORBIDDEN,
            "canonical bytes must not contain CR",
        )
    try:
        text = data.decode("utf-8", errors="strict")
    except (UnicodeDecodeError, ValueError, RuntimeError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_UTF8, "receipt is not UTF-8"
        ) from error
    _preflight_depth(text)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_refusing_object,
            parse_int=_parse_integer,
            parse_float=_refuse_float,
            parse_constant=_refuse_constant,
        )
    except LocalCiReceiptError:
        raise
    except (
        json.JSONDecodeError,
        RecursionError,
        UnicodeError,
        ValueError,
        RuntimeError,
    ) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_JSON,
            "receipt is not one bounded JSON value",
        ) from error
    if not isinstance(value, dict):
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "receipt must be a JSON object",
        )
    _walk_canonical_value(value)
    return value


def _model_value(record: BaseModel) -> dict[str, Any]:
    return record.model_dump(mode="json", by_alias=True)


def _canonical_value_bytes(value: Any) -> bytes:
    _walk_canonical_value(value)
    try:
        encoded = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )
    except (RecursionError, UnicodeError, ValueError, TypeError, OverflowError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "record cannot be canonically serialized",
        ) from error
    if len(encoded) > _MAX_CANONICAL_BYTES:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INPUT_TOO_LARGE,
            "canonical record exceeds the byte ceiling",
        )
    return encoded


def canonical_local_ci_json_bytes(record: BaseModel) -> bytes:
    """Return compact sorted NFC UTF-8 bytes with exactly one trailing LF."""
    from omega_engine_operations.use_cases.cicd.gate_resolution import (
        _rehydrate_invocation,
        _rehydrate_manifest,
        _rehydrate_receipt,
        _rehydrate_result,
        _rehydrate_verification_inputs,
        _strict_declared_rehydrate,
    )

    if type(record) is CanonicalCandidateManifestV1:
        validated: BaseModel = _rehydrate_manifest(record)
    elif type(record) is GateResult:
        validated = _rehydrate_result(record)
    elif type(record) is LocalCiInvocationV1:
        validated = _rehydrate_invocation(record)
    elif type(record) is LocalCiExecutionReceiptV3:
        validated = _rehydrate_receipt(record)
    elif type(record) is LocalCiVerificationInputsV1:
        validated = _rehydrate_verification_inputs(record)
    elif type(record) is ResolvedGateInvocationV1:
        validated = _strict_declared_rehydrate(
            record,
            ResolvedGateInvocationV1,
            label="resolved gate invocation",
        )
    else:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.UNSUPPORTED_RECORD,
            "record is not an exact local-CI protocol model",
        )
    return _canonical_value_bytes(_model_value(validated))


@lru_cache(maxsize=1)
def canonical_gate_catalog_sha256() -> str:
    """Digest only immutable catalog bytes, never candidate-derived arguments."""
    from omega_engine_operations.infrastructure.cicd.gate_catalog_loader import (
        ensure_gate_catalog,
    )
    from omega_engine_operations.use_cases.cicd.gate_resolution import _rehydrate_gate_spec

    ensure_gate_catalog()
    value = [_model_value(_rehydrate_gate_spec(gate)) for gate in GATE_CATALOG_V3]
    return hashlib.sha256(_CATALOG_DOMAIN + _canonical_value_bytes(value)).hexdigest()


def canonical_candidate_manifest_sha256(
    manifest: CanonicalCandidateManifestV1,
) -> str:
    """Return the domain-separated digest of one exact candidate manifest."""
    from omega_engine_operations.use_cases.cicd.gate_resolution import _rehydrate_manifest

    manifest = _rehydrate_manifest(manifest)
    return hashlib.sha256(
        _MANIFEST_DOMAIN + _canonical_value_bytes(_model_value(manifest))
    ).hexdigest()


def canonical_gate_results_sha256(results: Sequence[GateResult]) -> str:
    """Bind the ordered, strictly rehydrated measured result sequence."""
    from omega_engine_operations.use_cases.cicd.gate_resolution import _rehydrate_results

    exact_results = _rehydrate_results(results)
    if not exact_results:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.EMPTY_RESULTS,
            "cannot digest an empty active gate result sequence",
        )
    value = [_model_value(result) for result in exact_results]
    return hashlib.sha256(_RESULTS_DOMAIN + _canonical_value_bytes(value)).hexdigest()


def _resolved_invocation_digest(
    gate_id: str, resolved_argv: tuple[str, ...], resolved_inputs: tuple[str, ...]
) -> str:
    return domain_resolved_invocation_digest(
        gate_id,
        resolved_argv,
        resolved_inputs,
    )


def parse_local_ci_receipt(data: bytes) -> LocalCiExecutionReceiptV3:
    """Parse only the exact canonical bytes of a strict v3 receipt."""
    from pydantic import ValidationError

    from omega_engine_operations.use_cases.cicd.gate_resolution import _rehydrate_receipt

    value = _load_json_value(data)
    if value.get("schema") != _RECEIPT_SCHEMA:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            f"receipt schema must be {_RECEIPT_SCHEMA!r}",
        )
    try:
        parsed = LocalCiExecutionReceiptV3.model_validate_json(data, strict=True)
        receipt = _rehydrate_receipt(parsed)
    except (TypeError, ValueError, RuntimeError, ValidationError) as error:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.INVALID_RECORD,
            "receipt violates its strict v3 schema",
        ) from error
    if canonical_local_ci_json_bytes(receipt) != data:
        raise LocalCiReceiptError(
            LocalCiReceiptErrorCode.NON_CANONICAL_BYTES,
            "receipt bytes are not the unique canonical encoding",
        )
    return receipt


def parse_local_ci_receipt_bytes(data: bytes) -> LocalCiExecutionReceiptV3:
    """Parse one already-captured receipt buffer without reopening its path."""
    return parse_local_ci_receipt(data)


def resolved_invocation_digest(
    gate_id: str, resolved_argv: tuple[str, ...], resolved_inputs: tuple[str, ...]
) -> str:
    """Compute the domain-separated digest of a resolved gate invocation."""
    return _resolved_invocation_digest(gate_id, resolved_argv, resolved_inputs)


class LocalCiSerializer:
    """Canonical serialization and digest generator implementing LocalCiSerializerProtocol."""

    def canonical_gate_catalog_sha256(self) -> str:
        return canonical_gate_catalog_sha256()

    def canonical_gate_results_sha256(self, results: Sequence[GateResult]) -> str:
        return canonical_gate_results_sha256(results)

    def resolved_invocation_digest(
        self,
        gate_id: str,
        resolved_argv: tuple[str, ...],
        resolved_inputs: tuple[str, ...],
    ) -> str:
        return _resolved_invocation_digest(gate_id, resolved_argv, resolved_inputs)

    def canonical_candidate_manifest_sha256(
        self, manifest: CanonicalCandidateManifestV1
    ) -> str:
        return canonical_candidate_manifest_sha256(manifest)

    def canonical_local_ci_json_bytes(self, record: BaseModel) -> bytes:
        return canonical_local_ci_json_bytes(record)

    def parse_local_ci_receipt(self, data: bytes) -> LocalCiExecutionReceiptV3:
        return parse_local_ci_receipt(data)


from omega_engine_operations.domain.cicd.protocols import (
    register_local_ci_serializer,
)

_default_local_ci_serializer = LocalCiSerializer()
register_local_ci_serializer(_default_local_ci_serializer)

