"""Pure domain models and constraints for code-change proposal packets.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from pfp.domain.shared_kernel.path import is_normalized_relative_posix
from pfp.domain.shared_kernel.canonical import (
    CanonicalizationError,
    domain_digest,
    thaw,
)
from pfp.domain.validation import (
    MAX_ARRAY_LENGTH,
    MAX_ID_LENGTH,
    MAX_STRING_LENGTH,
    _fail,
    _require_bool,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_optional_bool,
    _require_optional_digest,
    _require_positive_int,
    _require_stable_id,
    _require_string,
)

CODE_CHANGE_PROPOSAL_SCHEMA = "core.symbol-game.code-change-proposal.v1"
CODE_CHANGE_PATCH_SCHEMA = "core.symbol-game.code-change-patch.v1"
GATE_RECEIPT_SCHEMA = "core.symbol-game.gate-receipt.v1"
CODE_CHANGE_RUN_ROOT_SCHEMA = "core.symbol-game.code-change-run-root.v1"
CODE_CHANGE_ATTEMPT_SCHEMA = "core.symbol-game.code-change-attempt.v1"
CODE_CHANGE_REPAIR_SCHEMA = "core.symbol-game.code-change-repair.v1"

REFUSAL_PROTECTED_FILE_PATCHED = "REFUSAL_PROTECTED_FILE_PATCHED"
REFUSAL_TOUCHED_OUTSIDE_OWNED = "REFUSAL_TOUCHED_OUTSIDE_OWNED"
REFUSAL_MISSING_REQUIRED_GATE = "REFUSAL_MISSING_REQUIRED_GATE"
REFUSAL_GATE_FAILED = "REFUSAL_GATE_FAILED"
REFUSAL_MISSING_REQUIRED_REPLY_FIELDS = "REFUSAL_MISSING_REQUIRED_REPLY_FIELDS"
REFUSAL_INHERITED_MEANING = "REFUSAL_INHERITED_MEANING"
REFUSAL_UNKNOWN_FIELDS = "REFUSAL_UNKNOWN_FIELDS"
REFUSAL_BUDGET_EXHAUSTED = "REFUSAL_BUDGET_EXHAUSTED"

CODE_CHANGE_PACKET_FAMILY = "code_change_proposal_v1"
CODE_CHANGE_FAMILY = "code_change_proposal"

PATH_MANIFEST_DOMAIN = "core.symbol-game.code-change-path-manifest.v1"
PAYLOAD_DOMAIN = "core.symbol-game.code-change-proposal-payload.v1"
PATCH_DOMAIN = "core.symbol-game.code-change-patch.v1"
GATE_RECEIPT_DOMAIN = "core.symbol-game.gate-receipt.v1"
RUN_ROOT_DOMAIN = "core.symbol-game.code-change-run-root.v1"

CODE_CHANGE_TERMINAL_TARGET = "TransportValidatedOrTypedRefusal"
CODE_CHANGE_EVIDENCE_CEILING = "ReplayableLabEvidence"
CODE_CHANGE_ORACLE_POLICY = "IndependentGateReceiptsAndExternalPromotionRequired"

CODE_CHANGE_ENVELOPE_CONSTRAINTS = (
    "authority_effect_none",
    "owned_paths_bound",
    "protected_paths_fenced",
    "independent_gate_receipts_required",
    "model_verdicts_untrusted",
)

ALLOWED_TRANSFORMS = frozenset(
    {
        "edit",
        "emit_evidence",
        "test",
    }
)
REQUIRED_GATE_IDS = frozenset({"focused_tests", "lint", "replay", "gate_syntax", "gate_ownership", "gate_contract"})
GATE_DISPOSITIONS = frozenset({"FAIL", "PASS", "REFUSED", "SKIPPED"})
PATCH_ENCODINGS = frozenset({"file-set-v1", "unified-diff-utf8-lf-v1"})
RUN_ROOT_TERMINAL_STATUSES = frozenset(
    {
        "BudgetExhausted",
        "DeclaredUnverified",
        "InvalidPacket",
        "OpenEvaluation",
        "TransportValidated",
        "TypedRefusal",
    }
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_REVISION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./+@:-]*$")
MAX_PATH_LENGTH = 2048
MAX_PATHS = 256
MAX_CANDIDATE_BUDGET = 32
MAX_OPERATION_BUDGET = 4096
MAX_CANONICAL_PAYLOAD_BYTES = 256 * 1024
MAX_PATCH_BYTES = 8 * 1024 * 1024
MAX_REFUSALS = 256
MAX_ATTEMPTS = 64
MAX_REPAIRS = 64
MAX_GATE_RECEIPTS = 64

# Host-derived refusal codes.
REFUSAL_OWNED_PATH_EMPTY = "OWNED_PATH_EMPTY"
REFUSAL_PROTECTED_PATH_COLLISION = "PROTECTED_PATH_COLLISION"
REFUSAL_TOUCHED_PATH_OUTSIDE_OWNED = "TOUCHED_PATH_OUTSIDE_OWNED"
REFUSAL_TOUCHED_PATH_PROTECTED = "TOUCHED_PATH_PROTECTED"
REFUSAL_REQUIRED_GATE_MISSING = "REQUIRED_GATE_MISSING"
REFUSAL_GATE_FAILED = "GATE_FAILED"
REFUSAL_GATE_REFUSED = "GATE_REFUSED"
REFUSAL_CANDIDATE_BUDGET_EXCEEDED = "CANDIDATE_BUDGET_EXCEEDED"
REFUSAL_OPERATION_BUDGET_EXCEEDED = "OPERATION_BUDGET_EXCEEDED"
REFUSAL_PATCH_DIGEST_MISMATCH = "PATCH_DIGEST_MISMATCH"
REFUSAL_PATCH_BYTES_ABSENT = "PATCH_BYTES_ABSENT"
REFUSAL_TOUCHED_PATH_DECLARED_MISMATCH = "TOUCHED_PATH_DECLARED_MISMATCH"
REFUSAL_MODEL_VERDICT_UNTRUSTED = "MODEL_VERDICT_UNTRUSTED"
REFUSAL_MARKDOWN_CLAIM_INJECTION = "MARKDOWN_CLAIM_INJECTION"
REFUSAL_REFUSAL_ERASURE = "REFUSAL_ERASURE"
REFUSAL_AUTHORITY_NON_NONE = "AUTHORITY_EFFECT_NON_NONE"
REFUSAL_TERMINAL_NOT_DERIVED = "TERMINAL_NOT_DERIVED_FROM_EVIDENCE"
REFUSAL_VERIFIED_PROPOSAL_FORBIDDEN = "VERIFIED_PROPOSAL_FORBIDDEN"
REFUSAL_CANDIDATE_PATCH_MISBIND = "CANDIDATE_PATCH_MISBIND"
REFUSAL_ATTEMPT_ID_MISBIND = "ATTEMPT_ID_MISBIND"
REFUSAL_POSITIVE_TERMINAL_NEEDS_REPLAY = "POSITIVE_TERMINAL_NEEDS_EVIDENCE_REPLAY"
OBSTRUCTION_VERIFIER_RECEIPT_REQUIRED = "VERIFIER_RECEIPT_REQUIRED"
OBSTRUCTION_BUDGET_HOST_STATE_ABSENT = "BUDGET_HOST_STATE_ABSENT"
OBSTRUCTION_SOURCE_REVISION_UNBOUND = "SOURCE_REVISION_UNBOUND"
POSITIVE_TERMINALS = frozenset({"TransportValidated", "DeclaredUnverified"})


def _canonical_json_size(value: Any) -> int:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CanonicalizationError("value is not strict JSON data") from exc
    return len(encoded)


def _validate_ordered_unique_strings(
    value: Any, label: str, *, maximum: int = MAX_ARRAY_LENGTH
) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        _fail(f"{label} must be an exact tuple of strings")
    if len(value) > maximum:
        _fail(f"{label} exceeds the array resource limit")
    for index, item in enumerate(value):
        _require_string(item, f"{label}[{index}]", nonempty=True)
    if tuple(sorted(value)) != value or len(value) != len(set(value)):
        _fail(f"{label} must be unique and sorted")
    return value


def _string_tuple_from_wire(
    value: Any, label: str, *, maximum: int = MAX_ARRAY_LENGTH
) -> tuple[str, ...]:
    if type(value) is not list:
        _fail(f"{label} must be an array")
    if len(value) > maximum:
        _fail(f"{label} exceeds the array resource limit")
    result = tuple(
        _require_string(item, f"{label}[{index}]", nonempty=True)
        for index, item in enumerate(value)
    )
    return _validate_ordered_unique_strings(result, label, maximum=maximum)


def _validate_repo_relative_path(value: Any, label: str) -> str:
    value = _require_string(value, label, nonempty=True)
    if len(value) > MAX_PATH_LENGTH or "\\" in value or "\x00" in value:
        _fail(f"{label} must be a normalized relative POSIX path")
    if not is_normalized_relative_posix(value):
        _fail(f"{label} must be a normalized relative POSIX path")
    return value


def _path_tuple_from_wire(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail(f"{label} must be an array")
    if len(value) > MAX_PATHS:
        _fail(f"{label} exceeds the path resource limit")
    result = tuple(
        _validate_repo_relative_path(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if tuple(sorted(result)) != result or len(result) != len(set(result)):
        _fail(f"{label} must be unique and sorted")
    return result


def _validate_path_tuple(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        _fail(f"{label} must be an exact tuple of paths")
    if len(value) > MAX_PATHS:
        _fail(f"{label} exceeds the path resource limit")
    normalized = tuple(
        _validate_repo_relative_path(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )
    if tuple(sorted(normalized)) != normalized or len(normalized) != len(
        set(normalized)
    ):
        _fail(f"{label} must be unique and sorted")
    return normalized


def _require_revision(value: Any, label: str) -> str:
    value = _require_string(value, label, nonempty=True)
    if len(value) > MAX_ID_LENGTH or _REVISION.fullmatch(value) is None:
        _fail(f"{label} must be a stable source revision identifier")
    return value


def _path_manifest_root(
    owned_paths: tuple[str, ...], protected_paths: tuple[str, ...]
) -> str:
    return domain_digest(
        PATH_MANIFEST_DOMAIN,
        {
            "owned_paths": list(owned_paths),
            "protected_paths": list(protected_paths),
        },
    )
