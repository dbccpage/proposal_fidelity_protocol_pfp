"""Domain-shaped records and strict decoding helpers for intelligence digestion."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARCHIVE_MANIFEST_SCHEMA = "core.intelligence.archive-manifest.v2"
ARCHIVE_JOURNAL_SCHEMA = "core.intelligence.archive-journal.v1"
SOURCE_SCHEMA = "core.intelligence.source-registration.v1"
CORPORA_MANIFEST_SCHEMA = "core.intelligence.corpora-archive-manifest.v1"
HARVEST_DIGESTION_RECEIPT_SCHEMA = "core.intelligence.harvest-digestion-receipt.v1"
EXTRACTOR_VERSION = "core.intelligence-digestion.python.v4"
CHECKER_VERSION = "core_intelligence.v1"
_NATIVE_BUNDLE_DIGESTS = {
    "novella.md": "novella_sha256",
    "ddc.jsonl": "ddc_sha256",
    "summary.json": "summary_sha256",
}
# Run folders written before 2026-10-16 also carry this byte copy of ddc.jsonl.
_LEGACY_DDA_TAPE = ("dda_actions.jsonl", "dda_actions_sha256")
_NATIVE_BUNDLE_FILES = tuple((*_NATIVE_BUNDLE_DIGESTS, "receipt.json"))


class ArchiveManifestUnreadable(RuntimeError):
    """The existing archive projection is evidence and must not be replaced."""


class ArchiveJournalUnreadable(RuntimeError):
    """A journal corruption blocks new archival until its bytes are retained and repaired."""


@dataclass
class DigestionRecord:
    run_id: str
    source_id: str
    source_queue: str
    original_path: str
    archive_path: str
    archived_at_utc: str
    evidence_sha256: str
    defects_count: int
    defects_extracted: list[str]
    digestion_state: str
    storage_state: str
    certificate_id: str | None = None
    status: str = "ABSORBED"
    authority_effect: str = "None"


@dataclass
class BlockedDigestion:
    run_id: str
    source_queue: str
    source_id: str | None
    state: str
    residuals: list[str]


@dataclass
class DigestionReceipt:
    receipt_id: str
    timestamp_utc: str
    authority_effect: str
    total_runs_examined: int
    total_runs_archived: int
    records: list[DigestionRecord] = field(default_factory=list)
    blocked: list[BlockedDigestion] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Extraction:
    findings: list[str]
    coverage_gaps: list[str]
    parse_residuals: list[str]


@dataclass(frozen=True)
class _SourceWork:
    run_path: Path
    source_queue: str
    producer_id: str | None = None
    work_keys: tuple[str, ...] = ()
    locator: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value!r}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _read_object(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    value = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    if type(value) is not dict:
        raise ValueError("JSON root must be an object")
    return value


def _sha256_reference(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _matches_digest(claimed: object, raw: bytes) -> bool:
    if type(claimed) is not str:
        return False
    actual = hashlib.sha256(raw).hexdigest()
    return claimed.removeprefix("sha256:") == actual


def _safe_component(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")[:80]
    return stem or "source"
