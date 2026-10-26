"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .configuration import load_json
from .domain import (
    ARCHIVE_LOCK_PATH,
    DOC_ROOT,
    EDUCATION_LOCK_PATH,
    MAPPING_STATUSES,
    MIGRATION_MAP_PATH,
    Findings,
    absolute_repo_path,
    is_document_relative_path,
)
from .inventory import archive_entries, education_entries, sha256_file

REQUIRED_LEDGER_FIELDS = {
    "schema_version",
    "source_path",
    "source_root",
    "entry_type",
    "content_type",
    "source_sha256",
    "hash_status",
    "size_bytes",
    "git_state",
    "source_revision",
    "primary_disposition",
    "contribution",
    "destination_docs",
    "mapping_status",
    "claim_status",
    "authority_effect",
    "verification",
    "exemption_reason",
    "review_state",
}


@dataclass(frozen=True, slots=True)
class LedgerPolicy:
    allowed_dispositions: set[str]
    allowed_claims: set[str]
    controls: set[str]
    current: dict[str, dict[str, Any]]


def _index_ledger(rows: list[dict[str, Any]], findings: Findings) -> dict[str, dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        source_path = row.get("source_path")
        if not isinstance(source_path, str):
            findings.error("Ledger row lacks a string source_path")
            continue
        if source_path in by_path:
            findings.error(f"Duplicate ledger row for {source_path}")
        by_path[source_path] = row
    return by_path


def _check_coverage(
    by_path: dict[str, dict[str, Any]],
    current_by_path: dict[str, dict[str, Any]],
    findings: Findings,
) -> None:
    stable_current = {
        path: row
        for path, row in current_by_path.items()
        if row["git_state"] not in {"ignored", "access_blocked"}
    }
    missing = sorted(set(current_by_path) - set(by_path))
    if missing:
        findings.error(
            f"Ledger omits {len(missing)} discovered source path(s), first: {missing[0]}"
        )
    stale = sorted(set(stable_current) - set(by_path))
    if stale:
        findings.error(f"Ledger omits {len(stale)} stable source path(s), first: {stale[0]}")
    stale_rows = sorted(
        path
        for path, row in by_path.items()
        if path not in current_by_path and row.get("git_state") not in {"ignored", "access_blocked"}
    )
    if stale_rows:
        findings.error(f"Ledger has {len(stale_rows)} stale stable path(s), first: {stale_rows[0]}")


def _check_mapping(path: str, row: dict[str, Any], findings: Findings) -> None:
    destinations = row["destination_docs"]
    valid = isinstance(destinations, list) and all(
        isinstance(item, str) and item.strip() for item in destinations
    )
    if not valid:
        findings.error(f"destination_docs must be a string list for {path}")
        return
    reason = row["exemption_reason"]
    if not destinations and (not isinstance(reason, str) or not reason.strip()):
        findings.error(f"{path} has neither a destination nor an exemption rationale")
    elif not destinations and row["mapping_status"] != "exempt":
        findings.error(f"{path} has an exemption rationale but is not marked exempt")
    elif destinations and row["mapping_status"] == "exempt" and not str(reason).strip():
        findings.error(f"Exempt mapping for {path} lacks a rationale")


def _check_row_policy(
    path: str, row: dict[str, Any], policy: LedgerPolicy, findings: Findings
) -> None:
    if path in policy.controls:
        findings.error(f"Generated control artifact leaked into source ledger: {path}")
    if row["primary_disposition"] not in policy.allowed_dispositions:
        findings.error(f"Unknown disposition for {path}: {row['primary_disposition']}")
    if row["claim_status"] not in policy.allowed_claims:
        findings.error(f"Unknown claim status for {path}: {row['claim_status']}")
    if row["mapping_status"] not in MAPPING_STATUSES:
        findings.error(f"Unknown or unfinished mapping status for {path}: {row['mapping_status']}")
    if row["authority_effect"] != "None":
        findings.error(f"AuthorityEffect must remain None for {path}")
    for field in ("contribution", "verification"):
        if not isinstance(row[field], str) or not row[field].strip():
            findings.error(f"Missing {field} for {path}")


def _check_row_hash(
    path: str, row: dict[str, Any], policy: LedgerPolicy, findings: Findings
) -> None:
    if row["git_state"] in {"ignored", "access_blocked"} and row["source_sha256"] is not None:
        findings.error(f"Transient row {path} must not claim a payload hash")
    stable_file = row["entry_type"] == "file" and row["git_state"] not in {
        "ignored",
        "access_blocked",
    }
    if stable_file and not isinstance(row["source_sha256"], str):
        findings.error(f"Stable source row {path} lacks a SHA-256 hash")
    actual = policy.current.get(path)
    if (
        actual
        and actual["source_sha256"] is not None
        and row["source_sha256"] != actual["source_sha256"]
    ):
        findings.error(
            f"Source hash drift for {path}; rerun inventory after reviewing its destination"
        )


def _check_ledger_row(
    path: str, row: dict[str, Any], policy: LedgerPolicy, findings: Findings
) -> None:
    if missing := sorted(REQUIRED_LEDGER_FIELDS - set(row)):
        findings.error(f"Ledger row {path} lacks: {', '.join(missing)}")
        return
    _check_row_policy(path, row, policy, findings)
    _check_mapping(path, row, findings)
    _check_row_hash(path, row, policy, findings)


def check_ledger(
    rows: list[dict[str, Any]],
    current: list[dict[str, Any]],
    contract: dict[str, Any],
    findings: Findings,
) -> None:
    by_path = _index_ledger(rows, findings)
    current_by_path = {row["source_path"]: row for row in current}
    _check_coverage(by_path, current_by_path, findings)
    policy = LedgerPolicy(
        set(contract["allowed_dispositions"]),
        set(contract["allowed_claim_statuses"]),
        set(contract["generated_control_artifacts"]),
        current_by_path,
    )
    for path, row in by_path.items():
        _check_ledger_row(path, row, policy, findings)
    findings.checked(f"ledger coverage and field contract ({len(rows)} rows)")


def check_destination_targets(
    repo_root: Path, rows: list[dict[str, Any]], contract: dict[str, Any], findings: Findings
) -> None:
    """Require every non-exempt ledger destination to resolve to a real target file."""

    documentation_root = absolute_repo_path(repo_root, contract["documentation_root"]).resolve()
    checked = 0
    for row in rows:
        if row.get("mapping_status") == "exempt":
            continue
        source = row.get("source_path", "<unknown>")
        destinations = row.get("destination_docs")
        if not isinstance(destinations, list):
            continue
        for destination in destinations:
            if not isinstance(destination, str) or not is_document_relative_path(destination):
                findings.error(f"Unsafe documentation destination for {source}: {destination!r}")
                continue
            target = documentation_root.joinpath(*destination.split("/"))
            try:
                target.resolve().relative_to(documentation_root)
            except ValueError:
                findings.error(
                    f"Documentation destination escapes the target root for {source}: {destination}"
                )
                continue
            if not target.is_file():
                findings.error(f"Ledger destination does not exist for {source}: {destination}")
                continue
            checked += 1
    findings.checked(f"ledger destination existence ({checked} non-exempt target(s))")


def check_migration_map(rows: list[dict[str, Any]], findings: Findings) -> None:
    if not MIGRATION_MAP_PATH.exists():
        findings.error("Missing migration-map.json")
        return
    document = load_json(MIGRATION_MAP_PATH)
    entries = document.get("mappings")
    if not isinstance(entries, list):
        findings.error("migration-map.json lacks mappings")
        return
    mapping = {entry.get("source_path"): entry for entry in entries if isinstance(entry, dict)}
    for row in rows:
        entry = mapping.get(row["source_path"])
        if entry is None:
            findings.error(f"Migration map omits {row['source_path']}")
            continue
        for key in (
            "destination_docs",
            "mapping_status",
            "claim_status",
            "authority_effect",
            "exemption_reason",
        ):
            if entry.get(key) != row.get(key):
                findings.error(
                    f"Migration map disagrees with ledger for {row['source_path']} ({key})"
                )
    if len(mapping) != len(entries):
        findings.error("Migration map contains duplicate or invalid source paths")
    findings.checked(f"migration map ({len(entries)} entries)")


def check_archive_lock(
    current: list[dict[str, Any]], contract: dict[str, Any], findings: Findings
) -> None:
    if not ARCHIVE_LOCK_PATH.exists():
        findings.error("Missing archive-lock.json")
        return
    document = load_json(ARCHIVE_LOCK_PATH)
    entries = document.get("entries")
    if not isinstance(entries, list):
        findings.error("archive-lock.json lacks entries")
        return
    locked = {
        entry.get("source_path"): entry.get("source_sha256")
        for entry in entries
        if isinstance(entry, dict)
    }
    actual = {
        entry["source_path"]: entry["source_sha256"] for entry in archive_entries(current, contract)
    }
    if locked != actual:
        changed = sorted(set(locked) ^ set(actual))
        changed.extend(path for path in set(locked) & set(actual) if locked[path] != actual[path])
        findings.error(
            f"Raw archive lock mismatch ({len(set(changed))} path(s)); first: {sorted(set(changed))[0] if changed else 'unknown'}"
        )
    findings.checked(f"raw archive preservation ({len(actual)} files)")


@dataclass(slots=True)
class ArchiveCoverage:
    expected: dict[str, str | None]
    seen: dict[str, dict[str, Any]]
    documentation_root: str
    findings: Findings


def _archive_entry(number: int, line: str, coverage: ArchiveCoverage) -> None:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError as error:
        coverage.findings.error(f"Invalid archive record manifest at line {number}: {error}")
        return
    if not isinstance(entry, dict):
        coverage.findings.error(f"Archive record manifest line {number} is not an object")
        return
    raw_path, record_path, raw_hash = (
        entry.get(key) for key in ("raw_path", "record_path", "raw_sha256")
    )
    if not all(isinstance(value, str) for value in (raw_path, record_path, raw_hash)):
        coverage.findings.error(
            f"Archive record manifest line {number} lacks raw_path, raw_sha256, or record_path"
        )
        return
    source_path = f"{coverage.documentation_root}/{raw_path.lstrip('/')}"
    if source_path in coverage.seen:
        coverage.findings.error(f"Archive record manifest maps a raw source twice: {raw_path}")
        return
    coverage.seen[source_path] = entry
    if coverage.expected.get(source_path) != raw_hash:
        coverage.findings.error(f"Archive record hash does not match raw evidence: {raw_path}")
    record = DOC_ROOT.joinpath(*record_path.split("/"))
    try:
        record.resolve().relative_to(DOC_ROOT.resolve())
    except ValueError:
        coverage.findings.error(f"Archive record escapes documentation root: {record_path}")
        return
    if not record.is_file():
        coverage.findings.error(f"Archive record is missing: {record_path}")


def check_archive_record_coverage(
    current: list[dict[str, Any]], contract: dict[str, Any], findings: Findings, *, required: bool
) -> None:
    manifest = DOC_ROOT / "archive" / "records" / "manifest.jsonl"
    if not manifest.exists():
        message = "Archive record manifest is required for the final documentation stage"
        findings.error(message) if required else findings.warning(
            "Archive record manifest is pending during foundation stage"
        )
        return
    expected = {
        row["source_path"]: row["source_sha256"] for row in archive_entries(current, contract)
    }
    coverage = ArchiveCoverage(expected, {}, contract["documentation_root"].rstrip("/"), findings)
    try:
        lines = manifest.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        findings.error(f"Cannot read archive record manifest: {error}")
        return
    for number, line in enumerate(lines, start=1):
        if line.strip():
            _archive_entry(number, line, coverage)
    if set(coverage.seen) != set(expected):
        mismatch = sorted(set(expected) ^ set(coverage.seen))
        findings.error(
            f"Archive record coverage is not one-to-one; first mismatch: {mismatch[0] if mismatch else 'unknown'}"
        )
    findings.checked(f"archive reader-record coverage ({len(coverage.seen)} records)")


def _check_education_entry(
    repo_root: Path,
    source_path: str,
    expected: dict[str, Any],
    locked: dict[str, Any],
    findings: Findings,
) -> bool:
    for key in ("copy_set", "source_sha256", "destination_path"):
        if locked.get(key) != expected[key]:
            findings.error(f"Education source lock drift for {source_path} ({key})")
    target = absolute_repo_path(repo_root, expected["destination_path"])
    if not target.exists() or not target.is_file():
        if (
            locked.get("copy_status") != "pending_copy"
            or locked.get("destination_sha256") is not None
        ):
            findings.error(f"Education copy lock is inconsistent for pending source {source_path}")
        return True
    actual_hash = sha256_file(target)
    if actual_hash != expected["source_sha256"]:
        findings.error(f"Byte-copy mismatch for {source_path}")
    if locked.get("copy_status") != "verified" or locked.get("destination_sha256") != actual_hash:
        findings.error(f"Education copy lock needs refresh for {source_path}")
    return False


def check_education_lock(
    current: list[dict[str, Any]],
    repo_root: Path,
    contract: dict[str, Any],
    findings: Findings,
    *,
    require_copies: bool,
) -> None:
    if not EDUCATION_LOCK_PATH.exists():
        findings.error("Missing education-copy-lock.json")
        return
    document = load_json(EDUCATION_LOCK_PATH)
    entries = document.get("entries")
    if not isinstance(entries, list):
        findings.error("education-copy-lock.json lacks entries")
        return
    expected = education_entries(current, repo_root, contract)
    locked_by_source = {
        entry.get("source_path"): entry for entry in entries if isinstance(entry, dict)
    }
    expected_by_source = {entry["source_path"]: entry for entry in expected}
    if set(locked_by_source) != set(expected_by_source):
        findings.error(
            "Education copy lock does not cover exactly the declared curriculum copy sets"
        )
    pending = 0
    for source_path, expected_entry in expected_by_source.items():
        locked = locked_by_source.get(source_path)
        if locked is None:
            continue
        pending += _check_education_entry(repo_root, source_path, expected_entry, locked, findings)
    if require_copies and pending:
        findings.error(f"{pending} required education copy/copies are still pending")
    elif pending:
        findings.warning(
            f"{pending} education copies are intentionally pending during foundation stage"
        )
    findings.checked(f"education source lock ({len(expected)} source files)")
