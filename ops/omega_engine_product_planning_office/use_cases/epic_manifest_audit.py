#!/usr/bin/env python3
"""Use case for fail-closed byte audit of the product planning epic manifest.

The manifest is a custody register, not a planning authority source. This
module validates its schema, recursive epic inventory, and every registered byte
sequence against domain rules.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

if __package__ is None or not __package__:
    _repo = Path(__file__).resolve().parents[2]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))

from omega_engine_product_planning_office.domain import (
    CONTENT_ENTRY_KEYS as CONTENT_ENTRY_KEYS,
)
from omega_engine_product_planning_office.domain import (
    EPIC_DIRECTORY,
    EPIC_FILENAME_RE,
    EXPECTED_EPIC_COUNT,
    EXPECTED_SOURCE_SNAPSHOT_COUNT,
    HASH_ALGORITHM,
    MANIFEST_PATH,
    SCHEMA_VERSION,
    SOURCE_SNAPSHOT_PATH,
    TOP_LEVEL_KEYS,
    EpicManifestAuditReport,
    EpicManifestError,
    compute_content_set_sha256,
    fail,
    line_profile,
    require_exact_keys,
    validate_entry_list,
    validate_nonnegative_int,
    validate_sha256,
    verify_epic_policy,
)
from omega_engine_product_planning_office.domain import (
    OIKONOMIA_STATUSES as OIKONOMIA_STATUSES,
)
from omega_engine_product_planning_office.domain import (
    SHA256_RE as SHA256_RE,
)
from omega_engine_product_planning_office.domain import (
    SOURCE_ENTRY_KEYS as SOURCE_ENTRY_KEYS,
)
from omega_engine_product_planning_office.domain import (
    require_exact_type as require_exact_type,
)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            fail("DUPLICATE_JSON_KEY", f"duplicate key {key!r}")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    fail("NONSTANDARD_JSON_CONSTANT", f"non-standard JSON value {value!r}")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail("MANIFEST_READ", f"cannot read {path}: {error}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        fail(
            "INVALID_JSON",
            f"{path}:{error.lineno}:{error.colno}: {error.msg}",
        )
    if not isinstance(value, dict):
        fail("TOP_LEVEL_TYPE", "manifest must be a JSON object")
    return value


def _resolve_registered_file(repo_root: Path, repo_path: str) -> Path:
    candidate = repo_root.joinpath(*PurePosixPath(repo_path).parts)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        fail("MISSING_REGISTERED_FILE", f"{repo_path}: {error}")
    resolved_root = repo_root.resolve(strict=True)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        fail("PATH_ESCAPE", f"{repo_path}: resolves outside repository")
    if candidate.is_symlink():
        fail("SYMLINK_FILE", f"{repo_path}: registered files must not be symlinks")
    if not resolved.is_file():
        fail("NOT_A_FILE", f"{repo_path}: expected a regular file")
    return resolved


def _resolve_manifest_path(repo_root: Path, manifest_path: Path) -> Path:
    """Resolve a manifest path without allowing the CLI to escape ``repo_root``.

    The audit accepts a caller-selected manifest so tests and review tooling can
    inspect a candidate packet, but that flexibility must not turn ``--write``
    into an arbitrary-file writer.  Treat a symlink as an escape too: a custody
    register is meaningful only when its bytes live in the reviewed tree.
    """

    candidate = manifest_path if manifest_path.is_absolute() else repo_root / manifest_path
    try:
        resolved_root = repo_root.resolve(strict=True)
        resolved = candidate.resolve(strict=False)
    except OSError as error:
        fail("MANIFEST_PATH", f"cannot resolve {candidate}: {error}")
    if resolved != resolved_root and resolved_root not in resolved.parents:
        fail("MANIFEST_PATH_ESCAPE", f"{manifest_path}: resolves outside repository")
    if candidate.is_symlink():
        fail("MANIFEST_SYMLINK", f"{manifest_path}: manifest must not be a symlink")
    return resolved


def _read_and_verify_entry(
    repo_root: Path, entry: Mapping[str, Any], *, source: bool
) -> bytes:
    path = str(entry["path"])
    resolved = _resolve_registered_file(repo_root, path)
    try:
        data = resolved.read_bytes()
    except OSError as error:
        fail("REGISTERED_FILE_READ", f"{path}: {error}")
    if len(data) != entry["bytes"]:
        fail(
            "BYTE_COUNT_MISMATCH",
            f"{path}: manifest={entry['bytes']}, observed={len(data)}",
        )
    observed_sha = hashlib.sha256(data).hexdigest()
    if observed_sha != entry["sha256"]:
        fail(
            "SHA256_MISMATCH",
            f"{path}: manifest={entry['sha256']}, observed={observed_sha}",
        )
    if source:
        observed_lines, observed_ending = line_profile(data)
        if observed_lines != entry["line_count"]:
            fail(
                "LINE_COUNT_MISMATCH",
                f"{path}: manifest={entry['line_count']}, observed={observed_lines}",
            )
        if observed_ending != entry["line_ending"]:
            fail(
                "LINE_ENDING_MISMATCH",
                f"{path}: manifest={entry['line_ending']}, observed={observed_ending}",
            )
    return data


def _direct_epic_inventory(repo_root: Path) -> list[str]:
    """Inventory every epic plan recursively; the legacy name is API-compatible.

    Research holds still need byte custody. READMEs, research drafts, registry
    YAML and placeholders are separate document classes, not epic plans.
    """
    directory = repo_root.joinpath(*PurePosixPath(EPIC_DIRECTORY).parts)
    if not directory.is_dir():
        fail("EPIC_DIRECTORY", f"missing directory {EPIC_DIRECTORY}")
    try:
        paths = sorted(
            child.relative_to(repo_root).as_posix()
            for child in directory.rglob("epic_*.md")
            if child.is_file() and EPIC_FILENAME_RE.fullmatch(child.name) is not None
        )
    except OSError as error:
        fail("EPIC_INVENTORY_READ", f"{EPIC_DIRECTORY}: {error}")
    if len(paths) != EXPECTED_EPIC_COUNT:
        fail(
            "EPIC_INVENTORY_COUNT",
            f"expected {EXPECTED_EPIC_COUNT} recursive epic plans, observed={len(paths)}: {paths!r}",
        )
    return paths


def audit_epic_manifest(
    repo_root: Path, manifest_path: Path | None = None
) -> EpicManifestAuditReport:
    """Validate the complete manifest packet or raise ``EpicManifestError``."""
    # strict=True raises FileNotFoundError for a path that does not exist, which
    # escaped this module untyped: `main` catches only EpicManifestError, so a
    # mistyped --repo-root produced a traceback rather than the REPO_ROOT
    # refusal declared three lines below. The docstring promises otherwise.
    try:
        repo_root = Path(repo_root).resolve(strict=True)
    except OSError as error:
        fail("REPO_ROOT", f"cannot resolve repository root: {error}")
    if not repo_root.is_dir():
        fail("REPO_ROOT", f"not a directory: {repo_root}")
    manifest_path = _resolve_manifest_path(
        repo_root,
        Path(manifest_path or Path(MANIFEST_PATH)),
    )
    manifest = _load_manifest(manifest_path)
    require_exact_keys(manifest, TOP_LEVEL_KEYS, "manifest")

    if manifest["schema_version"] != SCHEMA_VERSION:
        fail(
            "SCHEMA_VERSION",
            f"expected {SCHEMA_VERSION!r}, observed={manifest['schema_version']!r}",
        )
    if manifest["hash_algorithm"] != HASH_ALGORITHM:
        fail("HASH_ALGORITHM", "hash_algorithm must be 'sha256'")
    if manifest["authority_effect"] != "None":
        fail("AUTHORITY_EFFECT", "manifest authority_effect must be 'None'")
    if manifest["creates_execution_authority"] is not False:
        fail(
            "EXECUTION_AUTHORITY",
            "manifest creates_execution_authority must be false",
        )

    epic_count = validate_nonnegative_int(manifest["epic_count"], "epic_count")
    source_count = validate_nonnegative_int(
        manifest["source_snapshot_count"], "source_snapshot_count"
    )
    if epic_count != EXPECTED_EPIC_COUNT:
        fail("EPIC_COUNT", f"epic_count must be {EXPECTED_EPIC_COUNT}")
    if source_count != EXPECTED_SOURCE_SNAPSHOT_COUNT:
        fail(
            "SOURCE_SNAPSHOT_COUNT",
            f"source_snapshot_count must be {EXPECTED_SOURCE_SNAPSHOT_COUNT}",
        )

    epics = validate_entry_list(manifest["epics"], "epics", source=False)
    sources = validate_entry_list(
        manifest["source_snapshots"], "source_snapshots", source=True
    )
    if len(epics) != epic_count:
        fail(
            "EPIC_COUNT_MISMATCH",
            f"epic_count={epic_count}, entries={len(epics)}",
        )
    if len(sources) != source_count:
        fail(
            "SOURCE_COUNT_MISMATCH",
            f"source_snapshot_count={source_count}, entries={len(sources)}",
        )

    inventory = _direct_epic_inventory(repo_root)
    registered_epics = [str(entry["path"]) for entry in epics]
    if registered_epics != inventory:
        fail(
            "EPIC_INVENTORY_MISMATCH",
            f"registered={registered_epics!r}, observed={inventory!r}",
        )
    registered_sources = [str(entry["path"]) for entry in sources]
    expected_sources = [SOURCE_SNAPSHOT_PATH] if SOURCE_SNAPSHOT_PATH is not None else []
    if registered_sources != expected_sources:
        fail(
            "SOURCE_SNAPSHOT_PATH",
            f"expected {expected_sources!r}, observed={registered_sources!r}",
        )
    all_paths = registered_epics + registered_sources
    if len(all_paths) != len(set(all_paths)):
        fail("DUPLICATE_PATH", "a path appears in more than one content class")

    for entry in epics:
        data = _read_and_verify_entry(repo_root, entry, source=False)
        verify_epic_policy(str(entry["path"]), data)
    for entry in sources:
        _read_and_verify_entry(repo_root, entry, source=True)

    declared_aggregate = validate_sha256(
        manifest["content_set_sha256"], "content_set_sha256"
    )
    observed_aggregate = compute_content_set_sha256([*epics, *sources])
    if declared_aggregate != observed_aggregate:
        fail(
            "CONTENT_SET_SHA256_MISMATCH",
            f"manifest={declared_aggregate}, observed={observed_aggregate}",
        )

    try:
        rendered_manifest_path = manifest_path.resolve(strict=True).relative_to(
            repo_root
        ).as_posix()
    except (OSError, ValueError):
        rendered_manifest_path = str(manifest_path)
    return EpicManifestAuditReport(
        manifest_path=rendered_manifest_path,
        epic_count=epic_count,
        source_snapshot_count=source_count,
        content_set_sha256=observed_aggregate,
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _entry(repo_root: Path, repo_path: str, *, source: bool) -> dict[str, Any]:
    # Reuse the audit's regular-file and containment checks.  A regenerator
    # must not be able to certify a symlinked epic that the audit would reject.
    data = _resolve_registered_file(repo_root, repo_path).read_bytes()
    entry: dict[str, Any] = {
        "bytes": len(data),
        "path": repo_path,
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    if source:
        line_count, line_ending = line_profile(data)
        entry["line_count"] = line_count
        entry["line_ending"] = line_ending
    return entry


def rebuild_manifest(repo_root: Path) -> dict[str, Any]:
    """Recompute the manifest from the epics currently on disk.

    The audit is fail-closed on byte counts and hashes, so any legitimate edit
    to an epic invalidates it. Without a regenerator the only way to land such
    an edit is to hand-write sha256 values, which is both error-prone and
    exactly the kind of manual custody step a byte manifest exists to remove.
    """
    epics = [
        _entry(repo_root, path, source=False)
        for path in _direct_epic_inventory(repo_root)
    ]
    sources = (
        [_entry(repo_root, SOURCE_SNAPSHOT_PATH, source=True)]
        if SOURCE_SNAPSHOT_PATH is not None
        else []
    )
    return {
        "authority_effect": "None",
        "content_set_sha256": compute_content_set_sha256([*epics, *sources]),
        "creates_execution_authority": False,
        "epic_count": len(epics),
        "epics": epics,
        "hash_algorithm": HASH_ALGORITHM,
        "schema_version": SCHEMA_VERSION,
        "source_snapshot_count": len(sources),
        "source_snapshots": sources,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_default_repo_root())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(MANIFEST_PATH),
        help="repository-relative path unless absolute",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="recompute the manifest from disk, then audit the result",
    )
    args = parser.parse_args(argv)

    try:
        # Same reason as in audit_epic_manifest: this try catches only
        # EpicManifestError, so an unwrapped strict resolve turns a mistyped
        # --repo-root into a traceback instead of the REPO_ROOT refusal.
        try:
            repo_root = args.repo_root.resolve(strict=True)
        except OSError as error:
            fail("REPO_ROOT", f"cannot resolve repository root: {error}")
        target = _resolve_manifest_path(repo_root, args.manifest)
        canonical_target = (repo_root / MANIFEST_PATH).resolve(strict=False)
        if args.write:
            if target != canonical_target:
                fail(
                    "MANIFEST_WRITE_TARGET",
                    f"--write may update only {MANIFEST_PATH}, not {args.manifest}",
                )
            manifest = rebuild_manifest(repo_root)
            target.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(
                f"EPIC_MANIFEST_WRITTEN epics={manifest['epic_count']} "
                f"path={MANIFEST_PATH}"
            )
        report = audit_epic_manifest(repo_root, target)
    except EpicManifestError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(report.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
