#!/usr/bin/env python3
"""Domain models, value objects, and schema specifications for product planning epic manifests.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping, NoReturn

SCHEMA_VERSION = "core.product_planning.epic_bytes_manifest.v1"
HASH_ALGORITHM = "sha256"
EPIC_DIRECTORY = "product_planning_office/plans/epics"
MANIFEST_PATH = f"{EPIC_DIRECTORY}/epic_manifest.json"
SOURCE_SNAPSHOT_PATH: str | None = None
# RIS was retired by ef13b5cf1a; its bytes remain in that commit's parent.
# Four superseded Adversary plans were coalesced into their one residual owner.
# OEPFP 000-009 were consolidated into 010.
EXPECTED_EPIC_COUNT = 20
EXPECTED_SOURCE_SNAPSHOT_COUNT = 0

TOP_LEVEL_KEYS = frozenset(
    {
        "authority_effect",
        "content_set_sha256",
        "creates_execution_authority",
        "epic_count",
        "epics",
        "hash_algorithm",
        "schema_version",
        "source_snapshot_count",
        "source_snapshots",
    }
)
CONTENT_ENTRY_KEYS = frozenset({"bytes", "path", "sha256"})
SOURCE_ENTRY_KEYS = frozenset(
    {"bytes", "line_count", "line_ending", "path", "sha256"}
)
OIKONOMIA_STATUSES = frozenset(
    {
        "LIVE",
        "ORPHAN",
        "RESEARCH_HOLD",
        "BLOCKED",
        "SPEC_ONLY",
        "SUNSET",
        "PROTOTYPE",
        "IMPLEMENTED, TESTED",
        "NOT_IMPLEMENTED",
    }
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
EPIC_FILENAME_RE = re.compile(r"epic_oe_[a-z0-9_]+_plan\.md\Z")


class EpicManifestError(ValueError):
    """A deterministic, user-facing manifest audit failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"EPIC_MANIFEST_ERROR[{code}]: {detail}")


@dataclass(frozen=True)
class EpicManifestAuditReport:
    manifest_path: str
    epic_count: int
    source_snapshot_count: int
    content_set_sha256: str

    def render(self) -> str:
        return (
            "EPIC_MANIFEST_OK "
            f"manifest={self.manifest_path} "
            f"epics={self.epic_count} "
            f"source_snapshots={self.source_snapshot_count} "
            f"content_set_sha256={self.content_set_sha256} "
            "AuthorityEffect=None"
        )


def fail(code: str, detail: str) -> NoReturn:
    raise EpicManifestError(code, detail)


def require_exact_keys(
    value: Mapping[str, Any], expected: frozenset[str], locus: str
) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing or unknown:
        fail(
            "SCHEMA_KEYS",
            f"{locus}: missing={missing!r}, unknown={unknown!r}",
        )


def require_exact_type(value: Any, expected: type, locus: str) -> None:
    if type(value) is not expected:
        fail(
            "SCHEMA_TYPE",
            f"{locus}: expected {expected.__name__}, got {type(value).__name__}",
        )


def validate_repo_path(raw: Any, locus: str) -> str:
    require_exact_type(raw, str, locus)
    path = PurePosixPath(raw)
    if (
        not raw
        or "\\" in raw
        or raw != path.as_posix()
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        fail("NONCANONICAL_PATH", f"{locus}: {raw!r}")
    try:
        raw.encode("ascii")
    except UnicodeEncodeError:
        fail("NONASCII_PATH", f"{locus}: {raw!r}")
    return raw


def validate_sha256(raw: Any, locus: str) -> str:
    require_exact_type(raw, str, locus)
    if SHA256_RE.fullmatch(raw) is None:
        fail("INVALID_SHA256", f"{locus}: expected 64 lowercase hexadecimal digits")
    return raw


def validate_nonnegative_int(raw: Any, locus: str) -> int:
    require_exact_type(raw, int, locus)
    if raw < 0:
        fail("NEGATIVE_INTEGER", f"{locus}: {raw}")
    return raw


def validate_entry(raw: Any, locus: str, *, source: bool) -> dict[str, Any]:
    if not isinstance(raw, dict):
        fail("SCHEMA_TYPE", f"{locus}: expected object, got {type(raw).__name__}")
    require_exact_keys(raw, SOURCE_ENTRY_KEYS if source else CONTENT_ENTRY_KEYS, locus)
    entry = {
        "bytes": validate_nonnegative_int(raw["bytes"], f"{locus}.bytes"),
        "path": validate_repo_path(raw["path"], f"{locus}.path"),
        "sha256": validate_sha256(raw["sha256"], f"{locus}.sha256"),
    }
    if source:
        entry["line_count"] = validate_nonnegative_int(
            raw["line_count"], f"{locus}.line_count"
        )
        require_exact_type(raw["line_ending"], str, f"{locus}.line_ending")
        if raw["line_ending"] not in {"CRLF", "LF", "CR", "NONE"}:
            fail(
                "INVALID_LINE_ENDING",
                f"{locus}.line_ending: {raw['line_ending']!r}",
            )
        entry["line_ending"] = raw["line_ending"]
    return entry


def validate_entry_list(raw: Any, locus: str, *, source: bool) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        fail("SCHEMA_TYPE", f"{locus}: expected array, got {type(raw).__name__}")
    entries = [
        validate_entry(item, f"{locus}[{index}]", source=source)
        for index, item in enumerate(raw)
    ]
    paths = [entry["path"] for entry in entries]
    if paths != sorted(paths):
        fail("ENTRY_ORDER", f"{locus}: entries must be ordered lexically by path")
    if len(paths) != len(set(paths)):
        fail("DUPLICATE_PATH", f"{locus}: repeated path")
    return entries
