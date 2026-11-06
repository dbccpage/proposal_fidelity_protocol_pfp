"""Byte-preserved source-copy custody; historical files are inert evidence.

This module verifies files and provenance, not the truth of imported receipts.
It has no repository imports and is usable after extracting the paper archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath

SCHEMA = "paper011.source-copy-manifest.v1"
MANIFEST_PATH = "docs/source_copy_manifest.json"
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
HEX256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_OID = re.compile(r"[0-9a-f]{40}\Z")


class CustodyError(ValueError):
    """An absent, redirected, malformed, or modified source copy."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ordinal(value: str) -> bytes:
    return value.encode("utf-8")


def _relative(value: object) -> str:
    if type(value) is not str or not value or "\\" in value or ":" in value:
        raise CustodyError("noncanonical relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {".", "..", ""} for part in value.split("/")):
        raise CustodyError("unsafe relative path")
    if path.as_posix() != value:
        raise CustodyError("noncanonical relative path")
    return value


def _regular(path: Path, *, directory: bool = False) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise CustodyError(f"missing or unreadable entry: {path.name}") from exc
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & reparse:
        raise CustodyError(f"redirected entry: {path.name}")
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode):
        raise CustodyError(f"nonregular entry: {path.name}")
    return info


def _safe_file(root: Path, relative: str) -> Path:
    for ancestor in (root, *root.parents):
        _regular(ancestor, directory=True)
    parts = _relative(relative).split("/")
    current = root
    for part in parts[:-1]:
        current /= part
        _regular(current, directory=True)
    current /= parts[-1]
    _regular(current)
    return current


def _read_regular(root: Path, relative: str) -> bytes:
    path = _safe_file(root, relative)
    before = path.lstat()
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise CustodyError(f"unreadable entry: {relative}") from exc
    after = _regular(path)
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
        after.st_size,
        after.st_mtime_ns,
        after.st_ino,
    ):
        raise CustodyError(f"entry changed during read: {relative}")
    return data


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CustodyError(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def _json(data: bytes) -> dict:
    if len(data) > MAX_MANIFEST_BYTES or data.startswith(b"\xef\xbb\xbf"):
        raise CustodyError("invalid manifest encoding or size")
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(CustodyError("nonfinite JSON")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustodyError("malformed manifest") from exc
    if type(value) is not dict:
        raise CustodyError("manifest must be an object")
    return value


def _inventory(root: Path, relative: str) -> list[str]:
    base = root / _relative(relative)
    for ancestor in (root, *root.parents):
        _regular(ancestor, directory=True)
    current = root
    for part in relative.split("/"):
        current /= part
        _regular(current, directory=True)
    found: list[str] = []
    casing: dict[str, str] = {}

    def visit(folder: Path) -> None:
        _regular(folder, directory=True)
        try:
            children = list(folder.iterdir())
        except OSError as exc:
            raise CustodyError(f"inventory traversal failed: {folder.name}") from exc
        for child in children:
            child_relative = child.relative_to(root).as_posix()
            folded = child_relative.casefold()
            if folded in casing and casing[folded] != child_relative:
                raise CustodyError("case-colliding inventory")
            casing[folded] = child_relative
            info = child.lstat()
            if stat.S_ISDIR(info.st_mode):
                _regular(child, directory=True)
                visit(child)
            else:
                _regular(child)
                found.append(child_relative)

    visit(base)
    return sorted(found, key=_ordinal)


def _git(repo: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def tracked_sources(
    repo: Path, source_head: str, source_roots: list[str]
) -> dict[str, tuple[str, str]]:
    """Read the complete pinned Git tree inventory, never an ambient glob."""
    if not GIT_OID.fullmatch(source_head):
        raise CustodyError("invalid pinned Git head")
    raw = _git(repo, "ls-tree", "-r", "-z", "--full-tree", source_head, "--", *source_roots)
    result: dict[str, tuple[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split(" ")
        path = _relative(path_bytes.decode("utf-8"))
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise CustodyError("source tree includes a redirected or nonregular entry")
        result[path] = (mode, oid)
    return result


def _manifest_shape(manifest: dict) -> tuple[list[dict], list[dict]]:
    keys = {
        "schema_version",
        "paper_id",
        "authority_effect",
        "source_git_head",
        "captured_at_utc",
        "inventory_policy",
        "excluded_scope",
        "source_roots",
        "file_count",
        "total_bytes",
        "entries",
    }
    if set(manifest) != keys or manifest["schema_version"] != SCHEMA:
        raise CustodyError("unsupported manifest schema")
    if manifest["paper_id"] != "PAPER_011" or manifest["authority_effect"] != "None":
        raise CustodyError("invalid paper or authority declaration")
    if not GIT_OID.fullmatch(str(manifest["source_git_head"])):
        raise CustodyError("invalid source Git head")
    if manifest["inventory_policy"] != "ALL_GIT_TRACKED_FILES_UNDER_DECLARED_ROOTS":
        raise CustodyError("invalid source inventory policy")
    if manifest["excluded_scope"] != "UNTRACKED_LOCAL_STATE_ONLY":
        raise CustodyError("invalid exclusion policy")
    roots, entries = manifest["source_roots"], manifest["entries"]
    if type(roots) is not list or not roots or type(entries) is not list or not entries:
        raise CustodyError("missing source inventory")
    for root in roots:
        if type(root) is not dict or set(root) != {
            "source_root",
            "copy_root",
            "file_count",
            "total_bytes",
        }:
            raise CustodyError("invalid source root")
        _relative(root["source_root"])
        _relative(root["copy_root"])
        if not root["copy_root"].startswith("docs/source_archive/"):
            raise CustodyError("source copy outside archive")
    if [root["source_root"] for root in roots] != sorted(
        {root["source_root"] for root in roots}, key=_ordinal
    ):
        raise CustodyError("source roots must be unique and ordinal sorted")
    copy_roots = [root["copy_root"] for root in roots]
    if len(set(copy_roots)) != len(copy_roots):
        raise CustodyError("duplicate copy root")
    for root in roots:
        for other in roots:
            if root is not other and (
                root["source_root"].startswith(other["source_root"] + "/")
                or root["copy_root"].startswith(other["copy_root"] + "/")
            ):
                raise CustodyError("overlapping source roots")
    previous = b""
    seen_source: set[str] = set()
    seen_copy: set[str] = set()
    casing: dict[str, str] = {}
    for entry in entries:
        entry_keys = {
            "source_path",
            "copy_path",
            "captured_source_sha256",
            "current_copy_sha256",
            "size_bytes",
            "git_blob_oid",
            "git_mode",
        }
        if type(entry) is not dict or set(entry) != entry_keys:
            raise CustodyError("invalid source entry")
        source, copy = _relative(entry["source_path"]), _relative(entry["copy_path"])
        if _ordinal(copy) <= previous or source in seen_source or copy in seen_copy:
            raise CustodyError("inventory must be bijective and ordinal sorted")
        previous = _ordinal(copy)
        seen_source.add(source)
        seen_copy.add(copy)
        for name in (source, copy):
            parts = name.split("/")
            for end in range(1, len(parts) + 1):
                component = "/".join(parts[:end])
                folded = component.casefold()
                if folded in casing and casing[folded] != component:
                    raise CustodyError("case-colliding manifest")
                casing[folded] = component
        if type(entry["size_bytes"]) is not int or entry["size_bytes"] < 0:
            raise CustodyError("invalid file size")
        for key in ("captured_source_sha256", "current_copy_sha256"):
            if type(entry[key]) is not str or not HEX256.fullmatch(entry[key]):
                raise CustodyError("invalid source hash")
        if entry["captured_source_sha256"] != entry["current_copy_sha256"]:
            raise CustodyError("archival copy differs from captured source")
        if not GIT_OID.fullmatch(str(entry["git_blob_oid"])) or entry["git_mode"] not in {
            "100644",
            "100755",
        }:
            raise CustodyError("invalid source Git record")
        matches = [root for root in roots if source.startswith(root["source_root"] + "/")]
        if len(matches) != 1:
            raise CustodyError("source outside declared roots")
        selected = matches[0]
        suffix = source[len(selected["source_root"]) :]
        if copy != selected["copy_root"] + suffix:
            raise CustodyError("source/copy subtree mismatch")
    for root in roots:
        selected = [
            entry for entry in entries if entry["copy_path"].startswith(root["copy_root"] + "/")
        ]
        for key, actual in (
            ("file_count", len(selected)),
            ("total_bytes", sum(entry["size_bytes"] for entry in selected)),
        ):
            if type(root[key]) is not int or root[key] != actual:
                raise CustodyError("source root census mismatch")
    if type(manifest["file_count"]) is not int or manifest["file_count"] != len(entries):
        raise CustodyError("file census mismatch")
    if type(manifest["total_bytes"]) is not int or manifest["total_bytes"] != sum(
        entry["size_bytes"] for entry in entries
    ):
        raise CustodyError("byte census mismatch")
    return roots, entries


def verify_source_copies(
    paper_root: Path,
    *,
    expected_manifest_sha256: str | None = None,
    source_repo: Path | None = None,
) -> dict:
    """Verify the deposited copy inventory; optionally audit the original sources.

    A caller-supplied digest pins the inventory. Without that pin, the paper's
    release checksum verifier must authenticate the manifest separately.
    """
    paper_root = paper_root.absolute()
    manifest_bytes = _read_regular(paper_root, MANIFEST_PATH)
    if expected_manifest_sha256 is not None:
        if (
            not HEX256.fullmatch(expected_manifest_sha256)
            or sha256(manifest_bytes) != expected_manifest_sha256
        ):
            raise CustodyError("manifest pin mismatch")
    manifest = _json(manifest_bytes)
    roots, entries = _manifest_shape(manifest)
    if source_repo is not None:
        source_repo = source_repo.absolute()
        pinned = tracked_sources(
            source_repo, manifest["source_git_head"], [root["source_root"] for root in roots]
        )
        actual_records = {
            entry["source_path"]: (entry["git_mode"], entry["git_blob_oid"]) for entry in entries
        }
        if pinned != actual_records:
            raise CustodyError("pinned source Git inventory mismatch")
    # Replay every copy after the mutable Git subprocess, including all siblings
    # of the declared copy roots: an extra archive subtree cannot escape custody.
    found = _inventory(paper_root, "docs/source_archive")
    expected = [entry["copy_path"] for entry in entries]
    if found != expected:
        raise CustodyError("copy inventory mismatch")
    for entry in entries:
        data = _read_regular(paper_root, entry["copy_path"])
        if len(data) != entry["size_bytes"] or sha256(data) != entry["current_copy_sha256"]:
            raise CustodyError(f"copy bytes changed: {entry['copy_path']}")
    if source_repo is not None:
        for entry in entries:
            data = _read_regular(source_repo, entry["source_path"])
            if len(data) != entry["size_bytes"] or sha256(data) != entry["captured_source_sha256"]:
                raise CustodyError(f"source bytes changed: {entry['source_path']}")
    # Rehash after optional mutable subprocesses and all source/copy reads.
    if _read_regular(paper_root, MANIFEST_PATH) != manifest_bytes:
        raise CustodyError("manifest changed during verification")
    return {
        "schema_version": "paper011.source-copy-verification.v1",
        "status": "VERIFIED_BYTE_COPIES",
        "authority_effect": "None",
        "manifest_sha256": sha256(manifest_bytes),
        "source_git_head": manifest["source_git_head"],
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
        "source_inventory_checked": source_repo is not None,
        "execution_claim": "NONE_ARCHIVAL_CUSTODY_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--source-repo", type=Path)
    args = parser.parse_args()
    try:
        result = verify_source_copies(
            args.paper_root,
            expected_manifest_sha256=args.manifest_sha256,
            source_repo=args.source_repo,
        )
    except (CustodyError, OSError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                {"status": "REFUSED", "reason": str(exc), "authority_effect": "None"},
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
