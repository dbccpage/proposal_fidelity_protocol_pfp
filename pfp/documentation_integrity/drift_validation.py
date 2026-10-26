"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .configuration import load_exemptions
from .domain import LEDGER_PATH, Findings, repo_relative
from .git_adapter import git_changed_paths, git_show


def load_base_ledger(repo_root: Path, base: str) -> dict[str, dict[str, Any]]:
    relative = repo_relative(repo_root, LEDGER_PATH)
    text = git_show(repo_root, base, relative)
    if text is None:
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict) and isinstance(value.get("source_path"), str):
                rows[value["source_path"]] = value
    return rows


def check_changed_raw_archive(
    repo_root: Path, contract: dict[str, Any], base: str, findings: Findings
) -> None:
    changed = git_changed_paths(repo_root, base)
    prefix = contract["raw_archive_prefix"].rstrip("/") + "/"
    raw_changes = sorted(path for path in changed if path.startswith(prefix))
    if raw_changes:
        findings.error(f"Raw archive is immutable; changed path: {raw_changes[0]}")
    findings.checked("raw archive diff guard")


def check_changed_education_source(
    repo_root: Path, contract: dict[str, Any], base: str, findings: Findings
) -> None:
    """Keep the curriculum source immutable; only its byte copies belong here."""

    education_root = next(
        entry["path"].rstrip("/") + "/"
        for entry in contract["source_roots"]
        if entry["id"] == "education"
    )
    changed = git_changed_paths(repo_root, base)
    source_changes = sorted(path for path in changed if path.startswith(education_root))
    if source_changes:
        findings.error(
            f"Education source is immutable in this documentation estate; changed path: {source_changes[0]}"
        )
    findings.checked("education source diff guard")


def check_source_drift(
    repo_root: Path,
    rows: list[dict[str, Any]],
    contract: dict[str, Any],
    base: str,
    findings: Findings,
) -> None:
    changed = git_changed_paths(repo_root, base)
    drift_roots = tuple(root.rstrip("/") + "/" for root in contract["source_drift_roots"])
    source_changes = sorted(path for path in changed if path.startswith(drift_roots))
    if not source_changes:
        findings.checked("source-to-documentation drift guard (no source changes)")
        return
    current = {row["source_path"]: row for row in rows}
    previous = load_base_ledger(repo_root, base)
    documentation_root = contract["documentation_root"].rstrip("/") + "/"
    document_changes = {
        path[len(documentation_root) :] for path in changed if path.startswith(documentation_root)
    }
    exemptions = load_exemptions()
    for source_path in source_changes:
        row = current.get(source_path) or previous.get(source_path)
        if row is None:
            findings.error(f"Changed source lacks a documentation ledger entry: {source_path}")
            continue
        exemption = exemptions.get(source_path)
        if exemption is not None and exemption.get("reason"):
            continue
        destinations = row.get("destination_docs", [])
        if not isinstance(destinations, list):
            findings.error(f"Changed source has invalid destination map: {source_path}")
            continue
        document_updated = any(destination in document_changes for destination in destinations)
        previous_row = previous.get(source_path, {})
        mapping_updated = any(
            row.get(key) != previous_row.get(key)
            for key in ("destination_docs", "mapping_status", "exemption_reason")
        )
        if not document_updated and not mapping_updated:
            findings.error(
                f"Changed source {source_path} needs an affected documentation page change, a mapping update, or a checked-in exemption."
            )
    findings.checked(f"source-to-documentation drift guard ({len(source_changes)} source changes)")
