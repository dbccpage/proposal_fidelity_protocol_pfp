#!/usr/bin/env python3
"""Verify custody and census coverage of the OEPFP v1.1RC audit artifacts.

This standard-library-only checker reads artifacts and their declared hashes.
It does not execute a pilot, test a mathematical claim, or certify a production
operad engine. AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import platform
import shlex
import subprocess
import sys
import zlib
from pathlib import Path, PurePosixPath
from typing import Any

EVIDENCE_DIRECTORY = Path("pfp/documentation/oepfp_v1_1_rc_evidence")
DEFAULT_MANIFEST = EVIDENCE_DIRECTORY / "source_manifest.json"
DEFAULT_CENSUS = EVIDENCE_DIRECTORY / "census.json"
MONOGRAPH = Path("pfp/documentation/oepfp_v1_1_rc_specification.md")
EXPECTED_ADVERSARY_MODULES = 308
GZIP_SCHEMA = "oepfp.forensic_extract.v1"


class IntegrityError(ValueError):
    """A missing, altered, ambiguous, or inconsistent audit artifact."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def _object(value: Any, label: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _reject_constant(value: str) -> None:
    raise IntegrityError(f"non-finite JSON constant is forbidden: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    _require(math.isfinite(number), f"non-finite JSON number is forbidden: {value}")
    return number


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _read_json(path: Path, *, compressed: bool = False) -> Any:
    try:
        if compressed:
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                text = stream.read()
        else:
            text = path.read_text(encoding="utf-8")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except (OSError, EOFError, UnicodeError, json.JSONDecodeError, zlib.error) as error:
        raise IntegrityError(
            f"cannot decode {'gzip JSON' if compressed else 'JSON'} {path}: {error}"
        ) from error


def _canonical_path(value: Any) -> PurePosixPath:
    _require(isinstance(value, str) and bool(value), "manifest path must be a nonempty string")
    try:
        value.encode("utf-8")
    except UnicodeError as error:
        raise IntegrityError("manifest path must be valid UTF-8") from error
    _require(
        "\\" not in value and not any(ord(character) < 32 for character in value),
        f"noncanonical manifest path: {value!r}",
    )
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and not any(part in (".", "..") for part in value.split("/"))
        and path.as_posix() == value
        and ":" not in path.parts[0],
        f"manifest path must be canonical and repository-relative: {value!r}",
    )
    return path


def _relative_file(root: Path, value: Any) -> Path:
    path = _canonical_path(value)
    candidate = root.joinpath(*path.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise IntegrityError(f"missing manifest file: {value}") from error
    _require(resolved.is_relative_to(root), f"manifest path escapes repository: {value}")
    _require(resolved.is_file(), f"manifest member is not a file: {value}")
    return resolved


class _PinnedSources:
    """Stream committed source blobs; never substitute current files on failure."""

    def __init__(self, root: Path, revision: str) -> None:
        self.revision = revision
        try:
            self.process = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            raise IntegrityError(f"cannot read pinned Git sources: {error}") from error

    def digest(self, path: str) -> str:
        source = self.process
        if source.stdin is None or source.stdout is None:
            raise IntegrityError("pinned Git source streams are unavailable")
        try:
            source.stdin.write(f"{self.revision}:{path}\n".encode("utf-8"))
            source.stdin.flush()
            header = source.stdout.readline().split()
            _require(
                len(header) == 3 and header[1] == b"blob" and header[2].isdigit(),
                f"missing pinned Git source blob: {path} at {self.revision}",
            )
            remaining = int(header[2])
            digest = hashlib.sha256()
            while remaining:
                block = source.stdout.read(min(remaining, 1024 * 1024))
                _require(bool(block), f"truncated pinned Git source: {path}")
                digest.update(block)
                remaining -= len(block)
            _require(source.stdout.read(1) == b"\n", f"invalid Git source framing: {path}")
            return digest.hexdigest()
        except OSError as error:
            raise IntegrityError(f"cannot read pinned Git source {path}: {error}") from error

    def close(self) -> None:
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                # A failed Git process can already have closed its input. Keep
                # the original typed verification failure during cleanup.
                self.process.stdin = None
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        for stream in (self.process.stdout, self.process.stderr):
            if stream is not None:
                stream.close()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise IntegrityError(f"cannot hash manifest member {path}: {error}") from error
    return digest.hexdigest()


def _is_hex(value: Any, lengths: tuple[int, ...]) -> bool:
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all(character in "0123456789abcdef" for character in value)
    )


def _manifest_members(
    root: Path, manifest: dict[str, Any], *, pinned_sources: bool = False
) -> dict[str, Path]:
    members: dict[str, Path] = {}
    reader = _PinnedSources(root, manifest["base_commit"]) if pinned_sources else None
    try:
        return _check_manifest_members(root, manifest, members, reader)
    finally:
        if reader is not None:
            reader.close()


def _check_manifest_members(
    root: Path,
    manifest: dict[str, Any],
    members: dict[str, Path],
    reader: _PinnedSources | None,
) -> dict[str, Path]:
    for group in ("sources", "artifacts"):
        entries = manifest.get(group)
        _require(
            isinstance(entries, list) and bool(entries), f"manifest {group} must be a nonempty list"
        )
        paths = []
        for entry in entries:
            item = _object(entry, f"manifest {group} entry")
            value = item.get("path")
            path = _canonical_path(value)
            historical = group == "sources" and reader is not None
            file = root.joinpath(*path.parts) if historical else _relative_file(root, value)
            _require(value not in members, f"duplicate manifest path: {value}")
            expected = item.get("sha256")
            _require(_is_hex(expected, (64,)), f"invalid SHA-256 for {value}")
            observed = reader.digest(value) if historical else _digest(file)
            _require(observed == expected, f"SHA-256 mismatch: {value}")
            members[value] = file
            paths.append(value)
        _require(
            paths == sorted(paths, key=lambda path: path.encode("utf-8")),
            f"manifest {group} paths must be sorted in UTF-8 order",
        )
    return members


def _execution_outputs(receipt: dict[str, Any], artifacts: dict[str, str]) -> int:
    """Every named execution output must be shipped and bound by the manifest."""
    count = 0
    pending: list[Any] = [receipt]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "output_artifact" in value:
                path = value["output_artifact"]
                _canonical_path(path)
                _require(path in artifacts, f"execution output omitted from manifest: {path}")
                _require(
                    value.get("output_sha256") == artifacts[path],
                    f"execution output digest mismatch: {path}",
                )
                count += 1
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return count


def _coverage(
    rows: Any, expected: set[Any], label: str, *, integer_ids: bool = False
) -> list[dict[str, Any]]:
    _require(isinstance(rows, list), f"census {label} must be a list")
    identifiers = []
    for row in rows:
        item = _object(row, f"census {label} row")
        identifier = item.get("id")
        if integer_ids:
            _require(
                isinstance(identifier, int) and not isinstance(identifier, bool),
                f"census {label} id must be an integer",
            )
        else:
            _require(isinstance(identifier, str), f"census {label} id must be a string")
        identifiers.append(identifier)
    _require(len(set(identifiers)) == len(identifiers), f"duplicate census {label} id")
    _require(
        set(identifiers) == expected, f"census {label} IDs do not cover the exact required set"
    )
    return rows


def _validate_census(census: dict[str, Any]) -> dict[str, int]:
    _require(
        census.get("audit_mode") == "static_source_and_record_audit",
        "census audit_mode must describe the frozen static audit",
    )
    curriculum = _coverage(census.get("curriculum"), {f"{i:03}" for i in range(13)}, "curriculum")
    pilots = _coverage(census.get("pilots"), set(range(1, 76)), "pilots", integer_ids=True)
    antibodies = _coverage(
        census.get("antibodies"), {f"AB-{i:03}" for i in range(1, 20)}, "antibodies"
    )
    modules = census.get("adversary_modules")
    _require(
        isinstance(modules, list) and len(modules) == EXPECTED_ADVERSARY_MODULES,
        f"census must contain exactly {EXPECTED_ADVERSARY_MODULES} Adversary modules",
    )
    paths = []
    for row in modules:
        item = _object(row, "Adversary module")
        path = item.get("path")
        _require(isinstance(path, str) and bool(path), "Adversary module path must be a string")
        paths.append(path)
        _validate_module_status(item)
        _require(not item["executed_now"], "static audit cannot claim a module executed now")
    _require(len(set(paths)) == len(paths), "duplicate Adversary module path")
    for row in pilots:
        _validate_pilot_status(row)
        _require(not row["executed_now"], "static audit cannot claim a pilot executed now")
    return {
        "curriculum": len(curriculum),
        "pilots": len(pilots),
        "antibodies": len(antibodies),
        "adversary_modules": len(modules),
    }


def _validate_pilot_status(row: dict[str, Any]) -> None:
    # A normalized status contract is deliberately separate from mathematical
    # correctness: these fields describe this audit's evidence provenance.
    materialization = row.get("materialization")
    evidence = row.get("evidence_status")
    executed = row.get("executed_now")
    _require(
        isinstance(materialization, str) and materialization in {"present", "absent", "planned"},
        f"pilot {row['id']} has invalid materialization",
    )
    _require(
        isinstance(evidence, str)
        and evidence in {"absent", "planned", "source_only", "recorded", "executed_now"},
        f"pilot {row['id']} has invalid evidence_status",
    )
    _require(isinstance(executed, bool), f"pilot {row['id']} executed_now must be boolean")
    if "empirical_verified" in row:
        _require(
            isinstance(row["empirical_verified"], bool),
            f"pilot {row['id']} empirical_verified must be boolean",
        )
    if materialization in {"absent", "planned"}:
        _require(
            evidence in {"absent", "planned", "source_only"}
            and not executed
            and row.get("empirical_verified") is not True,
            f"absent/planned pilot {row['id']} cannot be empirically verified or executed",
        )
    _require(
        executed == (evidence == "executed_now"),
        f"pilot {row['id']} execution status contradicts evidence_status",
    )


def _validate_module_status(row: dict[str, Any]) -> None:
    provenance = row.get("provenance")
    executed = row.get("executed_now")
    _require(
        isinstance(provenance, str) and provenance in {"source_only", "recorded", "executed_now"},
        f"Adversary module {row['path']} has invalid provenance",
    )
    _require(
        isinstance(executed, bool), f"Adversary module {row['path']} executed_now must be boolean"
    )
    _require(
        executed == (provenance == "executed_now"),
        f"source-only/recorded module {row['path']} cannot be labelled executed now",
    )


def _validate_gzip_metadata(value: Any, path: str, base_commit: str) -> None:
    envelope = _object(value, f"gzip artifact {path}")
    _require(
        envelope.get("schema_version") == GZIP_SCHEMA,
        f"gzip artifact {path} schema_version mismatch",
    )
    _require(
        envelope.get("base_commit") == base_commit, f"gzip artifact {path} base_commit mismatch"
    )
    _require(
        envelope.get("audit_mode") == "static_source_and_record_audit",
        f"gzip artifact {path} audit_mode mismatch",
    )
    _require(
        isinstance(envelope.get("records"), (list, dict)),
        f"gzip artifact {path} records must be an array or object",
    )


def verify(
    repository_root: Path,
    manifest_path: Path | None = None,
    census_path: Path | None = None,
    *,
    pinned_sources: bool = False,
) -> dict[str, Any]:
    """Read the complete manifest and fail on any custody/coverage inconsistency."""
    root = repository_root.resolve()
    manifest_file = root / (manifest_path or DEFAULT_MANIFEST)
    census_file = root / (census_path or DEFAULT_CENSUS)
    manifest = _object(_read_json(manifest_file), "source manifest")
    base_commit = manifest.get("base_commit")
    _require(
        _is_hex(base_commit, (40, 64)), "manifest base_commit must be a lowercase Git object id"
    )
    members = _manifest_members(root, manifest, pinned_sources=pinned_sources)
    try:
        manifest_relative = manifest_file.resolve().relative_to(root).as_posix()
        census_relative = census_file.resolve().relative_to(root).as_posix()
    except ValueError as error:
        raise IntegrityError("manifest and census must be inside the repository") from error
    _require(manifest_relative not in members, "source manifest must not hash itself")
    receipt_relative = (
        (manifest_file.parent / "execution_receipt.json").relative_to(root).as_posix()
    )
    _require(
        receipt_relative not in members, "execution receipt must be excluded from source_manifest"
    )
    _require(census_relative in members, "census must be covered by source_manifest")
    _require(MONOGRAPH.as_posix() in members, "main monograph must be covered by source_manifest")
    census = _object(_read_json(census_file), "census")
    _require(census.get("base_commit") == base_commit, "census base_commit mismatch")
    counts = _validate_census(census)
    for row in census["adversary_modules"]:
        _require(
            row["path"] in members, f"Adversary module omitted from source_manifest: {row['path']}"
        )
    gzip_paths = sorted(
        item["path"] for item in manifest["artifacts"] if item["path"].endswith(".json.gz")
    )
    for path in gzip_paths:
        _validate_gzip_metadata(_read_json(members[path], compressed=True), path, base_commit)
    for file in manifest_file.parent.rglob("*.json.gz"):
        relative = file.relative_to(root).as_posix()
        _require(relative in members, f"gzip artifact is omitted from manifest: {relative}")
    execution_outputs = 0
    receipt_file = root / receipt_relative
    if receipt_file.exists():
        execution_outputs = _execution_outputs(
            _object(_read_json(receipt_file), "execution receipt"),
            {item["path"]: item["sha256"] for item in manifest["artifacts"]},
        )
    return {
        "schema": "oepfp.v1_1_rc.artifact-integrity.v1",
        "status": "PASS",
        "authority_effect": "None",
        "scope": "artifact custody and census coverage only; no mathematical or runtime certification",
        "base_commit": base_commit,
        "source_binding": "pinned_git_revision" if pinned_sources else "working_tree",
        "working_tree_sources_verified": not pinned_sources,
        "source_files_checked": len(manifest["sources"]),
        "artifact_files_checked": len(manifest["artifacts"]),
        "gzip_json_files_checked": len(gzip_paths),
        "execution_output_artifacts_checked": execution_outputs,
        "census_counts": counts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--census", type=Path)
    parser.add_argument(
        "--pinned-sources",
        action="store_true",
        help="verify frozen source blobs at manifest base_commit; artifacts remain current",
    )
    args = parser.parse_args(argv)
    invocation = (
        [sys.executable, *sys.argv]
        if argv is None
        else [sys.executable, str(Path(__file__).resolve()), *argv]
    )
    root = args.repository_root.resolve()
    context = {
        "command": shlex.join(invocation),
        "argv": invocation,
        "working_directory": str(Path.cwd()),
        "invocation_kind": "process" if argv is None else "programmatic_main",
        "tool_version": f"Python {platform.python_version()}; oepfp.v1_1_rc.artifact-integrity.v1",
        "tested_scope": {
            "repository_root": str(root),
            "manifest": str(root / (args.manifest or DEFAULT_MANIFEST)),
            "census": str(root / (args.census or DEFAULT_CENSUS)),
            "checks": "manifest custody, exact census coverage, evidence provenance and gzip metadata",
            "excluded": "mathematical correctness, pilot execution, model calls and production runtime certification",
        },
    }
    try:
        receipt = verify(
            args.repository_root, args.manifest, args.census, pinned_sources=args.pinned_sources
        )
    except IntegrityError as error:
        receipt = {
            "schema": "oepfp.v1_1_rc.artifact-integrity.v1",
            "status": "FAIL",
            "authority_effect": "None",
            "error": str(error),
        }
        exit_code = 1
    else:
        exit_code = 0
    receipt.update(context)
    receipt["exit_code"] = exit_code
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
