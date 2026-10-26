"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .configuration import (
    active_route_destinations,
    archive_record_destinations,
    load_exemptions,
    load_json,
    write_json_atomic,
    write_text_atomic,
)
from .domain import (
    ARCHIVE_LOCK_PATH,
    EDUCATION_LOCK_PATH,
    LEDGER_PATH,
    MIGRATION_MAP_PATH,
    SHA256_CHUNK_SIZE,
    IntegrityError,
    absolute_repo_path,
    copy_set_for_path,
    extension_kind,
    is_control_artifact,
    planned_asset_destination,
    root_for_path,
    source_root_paths,
)
from .git_adapter import git, git_index_blobs, git_revision, git_tracked_paths


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(SHA256_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_with_size(path: Path) -> tuple[str, int]:
    """Hash an immutable read snapshot and return its observed byte length."""

    return sha256_file(path), path.stat().st_size


def hash_stable_paths(
    repo_root: Path, paths: Iterable[str]
) -> dict[str, tuple[str | None, int | None]]:
    """Hash the large evidence corpus concurrently without weakening the lock.

    The raw archive has many small files; serial file-open overhead dominates its
    validation time on Windows.  Hashing independent files in a bounded pool
    keeps the same SHA-256 evidence while making the foundation check practical.
    """

    values = list(paths)
    if not values:
        return {}
    workers = min(32, max(4, (os.cpu_count() or 4) * 2))
    results: dict[str, tuple[str | None, int | None]] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_paths = {
            executor.submit(
                sha256_file_with_size, absolute_repo_path(repo_root, source_path)
            ): source_path
            for source_path in values
        }
        for future in as_completed(future_paths):
            source_path = future_paths[future]
            try:
                results[source_path] = future.result()
            except OSError:
                results[source_path] = (None, None)
    return results


def _porcelain_entries(
    records: list[bytes], roots: list[str], contract: dict[str, Any], repo_root: Path
) -> tuple[dict[str, str], dict[str, str]]:
    files: dict[str, str] = {}
    directories: dict[str, str] = {}
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        state = record[:2].decode("ascii", errors="replace")
        source_path = record[3:].decode("utf-8", errors="surrogateescape")
        if "R" in state or "C" in state:
            index += 1
        if not any(source_path == root or source_path.startswith(root + "/") for root in roots):
            continue
        if is_control_artifact(contract, source_path):
            continue
        git_state = (
            "ignored" if state == "!!" else "untracked" if state == "??" else "tracked_modified"
        )
        target = directories if absolute_repo_path(repo_root, source_path).is_dir() else files
        target[source_path.rstrip("/") + "/" if target is directories else source_path] = git_state
    return files, directories


def _inaccessible_paths(stderr: bytes, roots: list[str]) -> set[str]:
    inaccessible: set[str] = set()
    for match in re.finditer(
        r"could not open directory '([^']+)'", stderr.decode("utf-8", errors="replace")
    ):
        candidate = match.group(1).replace("\\", "/").rstrip("/")
        if any(candidate == root or candidate.startswith(root + "/") for root in roots):
            inaccessible.add(candidate + "/")
    return inaccessible


def git_discovered_paths(
    repo_root: Path, contract: dict[str, Any]
) -> tuple[dict[str, str], dict[str, str], set[str]]:
    """Discover untracked and ignored material through Git's fast path walker.

    A Python ``os.walk`` of this estate is disproportionately expensive because
    archive rewrites and Python caches contain tens of thousands of small files.
    Git already owns an optimized worktree walker and is also the authority for
    ignored status, so use its porcelain output as the discovery record.  The
    returned directory entries preserve ignored cache directories without
    needlessly reading their payloads.
    """

    roots = source_root_paths(contract)
    result = git(
        repo_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored", "--", *roots],
    )
    if result.returncode:
        raise IntegrityError(result.stderr.decode("utf-8", errors="replace").strip())
    records = [record for record in result.stdout.split(b"\0") if record]
    files, directories = _porcelain_entries(records, roots, contract, repo_root)
    return files, directories, _inaccessible_paths(result.stderr, roots)


@dataclass(frozen=True, slots=True)
class ClassificationContext:
    contract: dict[str, Any]
    exemptions: dict[str, dict[str, Any]]
    archive_destinations: dict[str, str]
    active_routes: dict[str, str]
    source_path: str
    source_root: dict[str, Any]
    git_state: str
    entry_type: str

    @property
    def relative(self) -> str:
        root_path = self.source_root["path"].rstrip("/")
        return self.source_path[len(root_path) :].lstrip("/")


VERIFY = "python -m omega_engine_pfp.scripts.docs_integrity validate"


def _classification(
    disposition: str, contribution: str, destinations: list[str], status: str, claim: str
) -> dict[str, Any]:
    return {
        "primary_disposition": disposition,
        "contribution": contribution,
        "destination_docs": destinations,
        "mapping_status": status,
        "claim_status": claim,
        "verification": VERIFY,
        "exemption_reason": "",
    }


def _transient_classification(context: ClassificationContext) -> dict[str, Any] | None:
    if context.entry_type == "inaccessible_directory":
        value = _classification(
            "access_blocked",
            "Inaccessible generated or cache directory recorded without payload review.",
            [],
            "exempt",
            "transient",
        )
        value["exemption_reason"] = (
            "Filesystem access prevented enumeration; this is a recorded transient exception."
        )
        return value
    if context.git_state == "ignored":
        value = _classification(
            "generated_exclude",
            "Ignored generated or cache artifact recorded without payload review.",
            [],
            "exempt",
            "transient",
        )
        value["exemption_reason"] = (
            "Ignored generated material is intentionally excluded from documentation content."
        )
        return value
    return None


def _override_classification(context: ClassificationContext) -> dict[str, Any] | None:
    override = context.exemptions.get(context.source_path)
    if override is None:
        return None
    destinations = override.get("destination_docs", [])
    if not isinstance(destinations, list) or not all(
        isinstance(item, str) for item in destinations
    ):
        raise IntegrityError(
            f"Invalid destination_docs in source exemption for {context.source_path}"
        )
    value = _classification(
        override.get("primary_disposition", "curate_and_synthesize"),
        override.get(
            "contribution", "Explicitly exempted source with a recorded review rationale."
        ),
        destinations,
        "exempt",
        override.get("claim_status", "unverified"),
    )
    value.update(
        verification=override.get("verification", VERIFY), exemption_reason=override["reason"]
    )
    return value


def _archive_classification(context: ClassificationContext) -> dict[str, Any]:
    relative = context.relative.removeprefix("_archive/")
    destination = context.archive_destinations.get(context.source_path)
    status = "mapped" if destination else "planned"
    if not destination and extension_kind(context.source_path) == "markdown":
        destination = f"archive/{relative}"
    elif not destination:
        category = relative.split("/", 1)[0] if relative else "root"
        destination = f"archive/catalogs/{category}.md"
    value = _classification(
        "historical_archive",
        "Immutable historical source retained as evidence for a reader-facing rewrite or catalogue.",
        [destination],
        status,
        "historical",
    )
    value["verification"] += " --check-archive"
    return value


def _documentation_classification(context: ClassificationContext) -> dict[str, Any]:
    relative = context.relative
    if (
        relative.startswith(("_meta/", "scripts/", "migration/"))
        or relative == "archive/records/manifest.jsonl"
    ):
        value = _classification(
            "documentation_control",
            "Documentation provenance, migration, or validation control artifact.",
            [],
            "exempt",
            "configuration",
        )
        value["exemption_reason"] = (
            "Control artefact; it governs documentation rather than serving as reader-facing content."
        )
        return value
    if relative.startswith("learning-copies/"):
        value = _classification(
            "curriculum_source",
            "Byte-preserved learning-copy artifact retained at its exact destination for source-locked study.",
            [relative],
            "mapped",
            "educational",
        )
        value["verification"] += " --require-education-copies"
        return value
    if relative.startswith("_archive/"):
        return _archive_classification(context)
    destination = context.active_routes.get(relative)
    if destination or extension_kind(context.source_path) == "markdown":
        value = _classification(
            "canonical_source",
            "Current documentation source retained at its canonical route.",
            [destination or relative],
            "mapped",
            "authored",
        )
        value["verification"] += " --content-scope governed"
        return value
    return _documentation_asset_classification(context)


def _documentation_asset_classification(context: ClassificationContext) -> dict[str, Any]:
    relative = context.relative
    content_type = extension_kind(context.source_path)
    if relative.endswith(".mmd"):
        destination = f"{relative[:-4]}.md"
    else:
        destination = planned_asset_destination(relative)
    if relative.endswith(".mmd") or content_type in {"asset", "diagram_source"}:
        value = _classification(
            "retain_as_asset",
            "Visual or diagram asset retained with an adjacent textual description in its owning page.",
            [destination],
            "mapped",
            "asset",
        )
        value["verification"] += " --strict-content"
        return value
    return _classification(
        "curate_and_synthesize",
        "Current supporting documentation material to be synthesized into a canonical page.",
        [destination],
        "mapped",
        "configuration",
    )


def _copy_classification(context: ClassificationContext) -> dict[str, Any] | None:
    copy_set = copy_set_for_path(context.contract, context.source_path)
    if copy_set is None:
        return None
    suffix = context.source_path[len(copy_set["source_prefix"].rstrip("/")) :].lstrip("/")
    destination = f"{copy_set['destination_prefix'].rstrip('/')}/{suffix}"
    root = context.contract["documentation_root"].rstrip("/")
    value = _classification(
        "curriculum_source",
        "Byte-preserved curriculum source required for the learning-copy estate.",
        [destination[len(root) :].lstrip("/")],
        "mapped",
        "educational",
    )
    value["verification"] += " --check-education-lock"
    return value


def _implementation_classification(context: ClassificationContext) -> dict[str, Any] | None:
    root_id = context.source_root["id"]
    if root_id == "education":
        disposition = (
            "structural_placeholder"
            if extension_kind(context.source_path) == "placeholder"
            else "curriculum_source"
        )
        return _classification(
            disposition,
            "Curriculum, exercise, support code, or asset indexed by the learning-copy guide.",
            ["learning/README.md"],
            "mapped",
            "educational",
        )
    pages = {
        "python_symbol_game": "reference/python-integration.md",
        "rust_native_host": "reference/native-rust-host.md",
        "rust_runtime": "reference/runtime-actions.md",
        "rust_epics": "reference/experimental-epics.md",
    }
    if root_id not in pages:
        return None
    destinations = [pages[root_id]]
    if "/tests/" in context.source_path or "/fixtures/" in context.source_path:
        destinations.append("operations/verification-and-evidence.md")
    value = _classification(
        "executable_evidence" if len(destinations) > 1 else "curate_and_synthesize",
        "Implementation or executable evidence for the Symbol Game reference.",
        destinations,
        "mapped",
        "tested" if len(destinations) > 1 else "implementation",
    )
    value["verification"] = (
        "python -m pytest omega_engine_pfp/tests"
        if root_id == "python_symbol_game"
        else f"cargo test -p {'omega_symbol_game_runtime' if root_id == 'rust_runtime' else 'omega_symbol_game'}"
    )
    return value


def classify_source(context: ClassificationContext) -> dict[str, Any]:
    """Produce an explicit contribution and future reader-facing destination."""

    value = _transient_classification(context) or _override_classification(context)
    if value is not None:
        return value
    if context.source_root["id"] == "documentation":
        return _documentation_classification(context)
    value = _copy_classification(context) or _implementation_classification(context)
    if value is not None:
        return value
    result = _classification(
        "untracked_review_required",
        "Source is within the declared documentation estate but needs a classification review.",
        [],
        "exempt",
        "unverified",
    )
    result["exemption_reason"] = "Unrecognized source root requires an explicit classification."
    return result


@dataclass(frozen=True, slots=True)
class InventoryContext:
    repo_root: Path
    contract: dict[str, Any]
    exemptions: dict[str, dict[str, Any]]
    archive_destinations: dict[str, str]
    active_routes: dict[str, str]
    blobs: dict[str, str]
    revision: str

    def classify(self, path: str, root: dict[str, Any], state: str, kind: str) -> dict[str, Any]:
        return classify_source(
            ClassificationContext(
                self.contract,
                self.exemptions,
                self.archive_destinations,
                self.active_routes,
                path,
                root,
                state,
                kind,
            )
        )


def _base_row(context: InventoryContext, path: str, root: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "symbol-game-source-ledger/v1",
        "source_path": path,
        "source_root": root["id"],
        "source_revision": context.revision,
        "authority_effect": "None",
        "review_state": "inventory",
    }


def _file_row(
    context: InventoryContext,
    source_path: str,
    git_state: str,
    stable_hash: tuple[str | None, int | None],
) -> dict[str, Any]:
    root = root_for_path(context.contract, source_path)
    source_hash, size = stable_hash
    if git_state == "ignored":
        source_hash = None
        size = absolute_repo_path(context.repo_root, source_path).stat().st_size
    elif source_hash is None:
        git_state = "access_blocked"
    row = _base_row(context, source_path, root)
    row.update(
        entry_type="file",
        content_type=extension_kind(source_path),
        source_sha256=source_hash,
        hash_status="not_hashed_transient"
        if git_state == "ignored"
        else "sha256"
        if source_hash
        else "unavailable",
        size_bytes=size,
        git_state=git_state,
        git_blob=context.blobs.get(source_path),
    )
    row.update(context.classify(source_path, root, git_state, "file"))
    return row


def _directory_row(
    context: InventoryContext, pseudo_path: str, state: str, entry_type: str
) -> dict[str, Any] | None:
    path = pseudo_path.rstrip("/")
    if is_control_artifact(context.contract, path):
        return None
    try:
        root = root_for_path(context.contract, path)
    except IntegrityError:
        return None
    row = _base_row(context, pseudo_path, root)
    inaccessible = entry_type == "inaccessible_directory"
    row.update(
        entry_type=entry_type,
        content_type="unavailable" if inaccessible else "directory",
        source_sha256=None,
        hash_status="unavailable" if inaccessible else "not_hashed_transient",
        size_bytes=None,
        git_state=state,
        git_blob=None,
    )
    row.update(context.classify(path, root, state, entry_type))
    return row


def collect_inventory(repo_root: Path, contract: dict[str, Any]) -> list[dict[str, Any]]:
    tracked = git_tracked_paths(repo_root, contract)
    files, directories, inaccessible = git_discovered_paths(repo_root, contract)
    expected = (tracked | set(files)) - set(contract["generated_control_artifacts"])
    ignored = {path for path, state in files.items() if state == "ignored"}
    hashes = hash_stable_paths(repo_root, (path for path in expected if path not in ignored))
    context = InventoryContext(
        repo_root,
        contract,
        load_exemptions(),
        archive_record_destinations(contract),
        active_route_destinations(),
        git_index_blobs(repo_root, contract),
        git_revision(repo_root),
    )
    rows = []
    for path in sorted(expected):
        state = files.get(path, "tracked" if path in tracked else "untracked")
        try:
            stable_hash = hashes.get(path, (None, None))
            rows.append(_file_row(context, path, state, stable_hash))
        except OSError:
            rows.append(_file_row(context, path, "access_blocked", (None, None)))
    for path, state in sorted(directories.items()):
        if row := _directory_row(context, path, state, "generated_directory"):
            rows.append(row)
    for path in sorted(inaccessible):
        if row := _directory_row(context, path, "access_blocked", "inaccessible_directory"):
            rows.append(row)
    return sorted(rows, key=lambda row: row["source_path"])


def archive_entries(
    rows: Iterable[dict[str, Any]], contract: dict[str, Any]
) -> list[dict[str, Any]]:
    prefix = contract["raw_archive_prefix"].rstrip("/") + "/"
    return [
        {
            "source_path": row["source_path"],
            "source_sha256": row["source_sha256"],
            "size_bytes": row["size_bytes"],
        }
        for row in rows
        if row["source_path"].startswith(prefix) and row["entry_type"] == "file"
    ]


def education_entries(
    rows: Iterable[dict[str, Any]], repo_root: Path, contract: dict[str, Any]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for copy_set in contract["education_copy_sets"]:
        source_prefix = copy_set["source_prefix"].rstrip("/") + "/"
        destination_prefix = copy_set["destination_prefix"].rstrip("/") + "/"
        for row in rows:
            source_path = row["source_path"]
            if (
                row["entry_type"] != "file"
                or row["hash_status"] != "sha256"
                or not source_path.startswith(source_prefix)
            ):
                continue
            suffix = source_path[len(source_prefix) :]
            destination_path = destination_prefix + suffix
            target = absolute_repo_path(repo_root, destination_path)
            if target.exists() and target.is_file():
                destination_hash = sha256_file(target)
                copy_status = "verified" if destination_hash == row["source_sha256"] else "mismatch"
            else:
                destination_hash = None
                copy_status = "pending_copy"
            entries.append(
                {
                    "copy_set": copy_set["id"],
                    "source_path": source_path,
                    "source_sha256": row["source_sha256"],
                    "destination_path": destination_path,
                    "destination_sha256": destination_hash,
                    "copy_status": copy_status,
                }
            )
    return sorted(entries, key=lambda entry: entry["source_path"])


@dataclass(frozen=True, slots=True)
class LockPolicy:
    existing_path: Path
    refresh: bool
    label: str
    source_field: str = "source_path"
    hash_field: str = "source_sha256"


def require_lock_stability(policy: LockPolicy, current_entries: list[dict[str, Any]]) -> None:
    if not policy.existing_path.exists() or policy.refresh:
        return
    old_document = load_json(policy.existing_path)
    old_entries = old_document.get("entries", [])
    if not isinstance(old_entries, list):
        raise IntegrityError(f"{policy.existing_path} must contain an entries list")
    old_map = {
        entry[policy.source_field]: entry.get(policy.hash_field)
        for entry in old_entries
        if isinstance(entry, dict)
    }
    new_map = {
        entry[policy.source_field]: entry.get(policy.hash_field) for entry in current_entries
    }
    if old_map != new_map:
        changed = sorted(set(old_map) ^ set(new_map))
        changed.extend(
            path for path in set(old_map) & set(new_map) if old_map[path] != new_map[path]
        )
        preview = ", ".join(sorted(set(changed))[:5])
        raise IntegrityError(
            f"{policy.label} lock would change ({preview}). Use the explicit refresh flag only for an approved source change."
        )


def _mapping_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = (
        "source_path",
        "source_root",
        "destination_docs",
        "mapping_status",
        "claim_status",
        "authority_effect",
        "exemption_reason",
    )
    return [{key: row[key] for key in keys} for row in rows]


def _write_inventory_documents(
    repo_root: Path,
    contract: dict[str, Any],
    rows: list[dict[str, Any]],
    archive: list[dict[str, Any]],
    education: list[dict[str, Any]],
) -> None:
    revision = git_revision(repo_root)
    write_text_atomic(
        LEDGER_PATH,
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
    )
    write_json_atomic(
        MIGRATION_MAP_PATH,
        {
            "schema_version": "symbol-game-migration-map/v1",
            "documentation_stage": contract.get("documentation_stage", "foundation"),
            "source_revision": revision,
            "mappings": _mapping_entries(rows),
        },
    )
    write_json_atomic(
        ARCHIVE_LOCK_PATH,
        {
            "schema_version": "symbol-game-raw-archive-lock/v1",
            "algorithm": "sha256",
            "raw_archive_prefix": contract["raw_archive_prefix"],
            "source_revision": revision,
            "entries": archive,
        },
    )
    write_json_atomic(
        EDUCATION_LOCK_PATH,
        {
            "schema_version": "symbol-game-education-copy-lock/v1",
            "algorithm": "sha256",
            "source_revision": revision,
            "entries": education,
        },
    )


def write_inventory(
    repo_root: Path, contract: dict[str, Any], args: argparse.Namespace
) -> list[dict[str, Any]]:
    rows = collect_inventory(repo_root, contract)
    archive = archive_entries(rows, contract)
    education = education_entries(rows, repo_root, contract)
    require_lock_stability(
        LockPolicy(ARCHIVE_LOCK_PATH, args.refresh_archive_lock, "Raw archive"), archive
    )
    require_lock_stability(
        LockPolicy(EDUCATION_LOCK_PATH, args.refresh_education_lock, "Education source"), education
    )
    _write_inventory_documents(repo_root, contract, rows, archive, education)
    return rows
