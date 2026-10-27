#!/usr/bin/env python3
"""Mirror selected skill packages across interactive host seats.

Hosts (repo-relative):
  .agents/skills   — Antigravity
  .claude/skills   — Claude Code
  .codex/skills    — Codex
  .grok/skills     — Grok

Canonical source defaults to operads/skills. Runtime Python modules for CODA
live under engine_py/ (not duplicated per host). This script only mirrors
skill packages (SKILL.md + references + optional skill-local scripts/tests).

Authority: None. Sync is a packaging operation, not skill admission.

THE ROSTER IS TRACKED, AND THAT IS LOAD-BEARING
-----------------------------------------------
`.gemini/skills` was removed from the roster on 2026-08-05 (operator: Gemini is
out). It is worth recording WHY its presence made this gate lie, because the
mechanism will recur with any host added carelessly.

`sync_skills` created a missing host root with `mkdir(parents=True)`. Nothing
tracked the result, so `.gemini/` existed on the machine that ran a sync and
nowhere else. `check_parity` then compared five host trees, found five, and
reported OK. Measured 2026-08-05:

    main checkout (has the untracked .gemini/)   224 OK,   0 FAIL, exit 0
    fresh worktree at the same commit              0 OK, 223 FAIL, exit 1

Same commit, opposite verdicts, and 223 of 223 failures were `.gemini`. The
green reading was produced by a directory that is not in the repository. A gate
whose result depends on untracked local state is not measuring the repository.

Two rules now enforce this and both are tested:

  1. A roster host root must ALREADY EXIST. `sync_skills` will not conjure one;
     adding a host is a deliberate, reviewable act, not a side effect of a sync.
  2. `--check` refuses when a roster host root is entirely untracked, rather
     than silently counting it as a peer.

Usage:
  python -m operations.use_cases.packaging.sync_cross_host_skills --check
  python -m operations.controllers.skill_mirror_cli --skills lib-coda-librarian,lib-encyclopedia-librarian
  python -m operations.use_cases.packaging.sync_cross_host_skills --package-hash --skills lib-coda-librarian
  python -m operations.controllers.skill_mirror_cli --all

Explicit --skills scopes sync/check to those packages and preserves unrelated
host-owned packages. --all and omitted --skills keep the whole-estate census.
Sync preflights every selected source and host root before writing. Cooperating
sync processes share an OS lock and retain exact destination rollback bytes;
restart restores a pending copy before a retry. Canonical edits are preserved.
--receipt only
reads the existing package bytes and reports their observed per-host digests.
Mutating commands use the controller, which supplies the production recovery
and locking factory. The use-case module permits read-only checks and receipts;
it refuses an unbound mutation instead of constructing an infrastructure adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from operations.domain.packaging.protocols import (
    MirrorRecoveryFactoryPort,
    MirrorRecoveryPort,
)

# The roster. Adding an entry here is the ONLY way to add a host, and the entry
# must be accompanied by a tracked host root -- see the docstring.
HOST_SKILL_ROOTS = (
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".grok/skills",
)

CANONICAL_SKILL_ROOT = "operads/skills"
DEFAULT_SOURCE_HOST = CANONICAL_SKILL_ROOT

DEFAULT_SKILLS = (
    "_shared",
    "lib-coda-librarian",
    "lib-encyclopedia-librarian",
    "lib-lean4-librarian",
    "governance-wdp",
    "lib-literature-lookup",
    "lib-hypothesis-tree",
    "lib-skill-admission-hygiene",
)

SKIP_DIR_NAMES = {"__pycache__", ".git"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".lean",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

RECEIPT_SCHEMA = "core.packaging.four-host-skill-receipt.v1"
TEXT_HASH_LAW = "newline_canonical_lf"
BINARY_HASH_LAW = "exact_bytes"
AUTHORITY_EFFECT = "None"
_DIGEST_HEX = re.compile(r"^[0-9a-f]{64}$")


class PackagingReceiptError(ValueError):
    """A packaging receipt failed its schema. AuthorityEffect: None."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True, slots=True)
class SkillHostDigestRow:
    """One skill's full per-host package digests. Truncated prefixes are not digests."""

    skill: str
    host_digests: tuple[tuple[str, str | None], ...]
    digests_agree: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SkillHostDigestRow)
        return (
            self.skill == other.skill
            and self.host_digests == other.host_digests
            and self.digests_agree is other.digests_agree
        )

    def __hash__(self) -> int:
        return hash((type(self), self.skill, self.host_digests, self.digests_agree))


@dataclass(frozen=True, slots=True)
class FourHostPackagingReceipt:
    """Schema-checked record of per-host package digests.

    Text digests are newline-canonical. Binary digests are exact bytes.
    Emitting this record admits nothing.
    """

    schema_version: str
    authority_effect: str
    source_host: str
    hosts: tuple[str, ...]
    text_hash_law: str
    binary_hash_law: str
    skill_rows: tuple[SkillHostDigestRow, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, FourHostPackagingReceipt)
        return (
            self.schema_version == other.schema_version
            and self.authority_effect == other.authority_effect
            and self.source_host == other.source_host
            and self.hosts == other.hosts
            and self.text_hash_law == other.text_hash_law
            and self.binary_hash_law == other.binary_hash_law
            and self.skill_rows == other.skill_rows
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.schema_version,
                self.authority_effect,
                self.source_host,
                self.hosts,
                self.text_hash_law,
                self.binary_hash_law,
                self.skill_rows,
            )
        )

    def all_agree(self) -> bool:
        """True only when every named skill has one shared full digest."""
        if not self.skill_rows:
            return False
        return all(row.digests_agree for row in self.skill_rows)

    def as_dict(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "binary_hash_law": self.binary_hash_law,
            "hosts": list(self.hosts),
            "schema_version": self.schema_version,
            "skills": [
                {
                    "digests_agree": row.digests_agree,
                    "host_digests": {
                        host: digest for host, digest in row.host_digests
                    },
                    "skill": row.skill,
                }
                for row in self.skill_rows
            ],
            "source_host": self.source_host,
            "text_hash_law": self.text_hash_law,
        }

    def validate(self) -> FourHostPackagingReceipt:
        """Refuse a receipt that is not the four-host digest schema."""
        self._validate_header()
        seen: set[str] = set()
        for row in self.skill_rows:
            self._validate_row(row, seen)
            seen.add(row.skill)
        return self

    def _validate_header(self) -> None:
        if self.schema_version != RECEIPT_SCHEMA:
            raise PackagingReceiptError("SCHEMA", self.schema_version)
        if type(self.authority_effect) is not str or self.authority_effect != AUTHORITY_EFFECT:
            raise PackagingReceiptError("AUTHORITY", repr(self.authority_effect))
        if self.text_hash_law != TEXT_HASH_LAW:
            raise PackagingReceiptError("TEXT_LAW", self.text_hash_law)
        if self.binary_hash_law != BINARY_HASH_LAW:
            raise PackagingReceiptError("BINARY_LAW", self.binary_hash_law)
        if (
            type(self.hosts) is not tuple
            or not self.hosts
            or len(set(self.hosts)) != len(self.hosts)
            or any(type(host) is not str or not host for host in self.hosts)
        ):
            raise PackagingReceiptError("HOSTS", repr(self.hosts))
        if self.source_host not in self.hosts:
            raise PackagingReceiptError("SOURCE_HOST", self.source_host)

    def _validate_row(self, row: SkillHostDigestRow, seen: set[str]) -> None:
        if type(row) is not SkillHostDigestRow:
            raise PackagingReceiptError("SKILL_ROW", type(row).__name__)
        if type(row.skill) is not str or not row.skill or row.skill in seen:
            raise PackagingReceiptError("SKILL_ROW", repr(row.skill))
        if type(row.digests_agree) is not bool:
            raise PackagingReceiptError("AGREEMENT", repr(row.digests_agree))
        hosts = tuple(host for host, _digest in row.host_digests)
        if hosts != self.hosts:
            raise PackagingReceiptError("HOSTS", repr(hosts))
        digests = [digest for _host, digest in row.host_digests]
        if any(
            digest is not None
            and (type(digest) is not str or _DIGEST_HEX.fullmatch(digest) is None)
            for digest in digests
        ):
            raise PackagingReceiptError("DIGEST", repr(digests))
        expected = all(item is not None for item in digests) and len(set(digests)) == 1
        if row.digests_agree is not expected:
            raise PackagingReceiptError(
                "AGREEMENT",
                f"{row.skill}: declared {row.digests_agree} but digests say {expected}",
            )


@dataclass(frozen=True, slots=True)
class FourHostSkillMirror:
    """Copy and compare skill packages across the host roster.

    Comparison uses newline-canonical text bytes and exact binary bytes.
    The receipt records the full per-host digests. It does not delete stray
    files and it does not admit a skill.
    """

    root: Path
    source_host: str = DEFAULT_SOURCE_HOST
    hosts: tuple[str, ...] = HOST_SKILL_ROOTS

    def _package_path(self, skill: str, host: str) -> Path:
        name = _package_name(skill)
        if host not in self.hosts and host != CANONICAL_SKILL_ROOT:
            raise PackagingReceiptError("HOST_NOT_ON_ROSTER", host)
        root = self.root.resolve()
        host_root = root / host
        _contained_package_path(host_root, root)
        package = host_root / name
        _contained_package_path(package, host_root)
        return package

    def copy_package(self, skill: str, dest_host: str) -> list[str]:
        """Copy one contained package. Destination-only files stay on disk."""
        if dest_host not in self.hosts:
            raise PackagingReceiptError("HOST_NOT_ON_ROSTER", dest_host)
        dest = self._package_path(skill, dest_host)
        if dest_host == self.source_host:
            raise PackagingReceiptError("SOURCE_IS_NOT_A_DESTINATION", dest_host)
        if not dest.parent.is_dir():
            raise PackagingReceiptError(
                "HOST_ROOT_MISSING",
                f"{dest_host} does not exist; a mirror must not create a host root",
            )
        source = self._package_path(skill, self.source_host)
        if not source.is_dir():
            raise PackagingReceiptError("SOURCE_PACKAGE_MISSING", str(source))
        return mirror_skill(source, dest)

    def compare_package(self, skill: str, dest_host: str) -> list[str]:
        """Mismatch messages; an absent package never counts as agreement."""
        source = self._package_path(skill, self.source_host)
        dest = self._package_path(skill, dest_host)
        missing = [f"package missing: {path}" for path in (source, dest) if not path.is_dir()]
        if missing:
            return missing
        return compare_skill_trees(source, dest)

    def receipt(self, skill_names: Sequence[str]) -> FourHostPackagingReceipt:
        """Compare canonical source and projections in the existing digest format."""
        rows: list[SkillHostDigestRow] = []
        roots = (self.source_host, *(host for host in self.hosts if host != self.source_host))
        for name in skill_names:
            pairs: list[tuple[str, str | None]] = []
            for host in roots:
                path = self._package_path(name, host)
                digest = package_tree_hash(path) if path.is_dir() else None
                pairs.append((host, digest))
            present = [digest for _host, digest in pairs]
            agree = all(item is not None for item in present) and len(set(present)) == 1
            rows.append(SkillHostDigestRow(name, tuple(pairs), agree))
        receipt = FourHostPackagingReceipt(
            schema_version=RECEIPT_SCHEMA,
            authority_effect=AUTHORITY_EFFECT,
            source_host=self.source_host,
            hosts=roots,
            text_hash_law=TEXT_HASH_LAW,
            binary_hash_law=BINARY_HASH_LAW,
            skill_rows=tuple(rows),
        )
        return receipt.validate()



def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "engine").is_dir():
            return candidate
    raise SystemExit("could not locate repo root (expected .git + engine)")


def _should_skip(path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    return False


def _package_name(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or any(character in value for character in "/\\:\0")
    ):
        raise PackagingReceiptError("INVALID_SKILL_NAME", repr(value))
    return value


def _contained_package_path(path: Path, boundary: Path) -> None:
    """Refuse escapes and filesystem links before traversing or copying them."""
    try:
        relative = path.relative_to(boundary)
        inside = path.resolve().is_relative_to(boundary.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        raise PackagingReceiptError("PACKAGE_PATH_ESCAPE", str(path)) from exc
    if not relative.parts or not inside:
        raise PackagingReceiptError("PACKAGE_PATH_ESCAPE", str(path))
    current = boundary
    for part in relative.parts:
        current /= part
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise PackagingReceiptError("PACKAGE_LINK", str(current))


def iter_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    if not skill_dir.is_dir():
        return files
    _contained_package_path(skill_dir, skill_dir.parent)
    for path in skill_dir.rglob("*"):
        _contained_package_path(path, skill_dir)
        if path.is_file() and not _should_skip(path.relative_to(skill_dir)):
            if path.stat().st_nlink != 1:
                raise PackagingReceiptError("PACKAGE_HARD_LINK", str(path))
            files.append(path)
    return sorted(files, key=lambda path: path.as_posix())


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def canonical_file_bytes(path: Path) -> bytes:
    """Return semantic bytes for parity while preserving binary payloads.

    Git may materialize text with host-specific newlines. Those bytes are not a
    skill semantic difference. Binary files and unknown suffixes remain exact.
    """
    raw = path.read_bytes()
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return raw
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def package_tree_hash(skill_dir: Path) -> str:
    """Deterministic hash of relative path + content for the whole package tree."""
    h = hashlib.sha256()
    for path in iter_files(skill_dir):
        rel = path.relative_to(skill_dir).as_posix().encode("utf-8")
        h.update(b"PATH\0")
        h.update(rel)
        h.update(b"\0DATA\0")
        h.update(canonical_file_bytes(path))
        h.update(b"\0")
    return h.hexdigest()


def mirror_skill(source_skill: Path, dest_skill: Path) -> list[str]:
    """Copy a source package in place without deleting the destination tree.

    Skill mirrors can be writeable while denying delete on Windows. Deleting the
    whole package also exposes a partially missing tree if a later host fails.
    Refuse unexpected destination-only files and overwrite only named source
    files.
    """
    source_files = {path.relative_to(source_skill).as_posix() for path in iter_files(source_skill)}
    dest_files = (
        {path.relative_to(dest_skill).as_posix() for path in iter_files(dest_skill)}
        if dest_skill.is_dir()
        else set()
    )
    extra = sorted(dest_files - source_files)
    if extra:
        raise RuntimeError(
            f"destination has files absent from canonical source {dest_skill}: {extra}"
        )
    dest_skill.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for src in iter_files(source_skill):
        rel = src.relative_to(source_skill)
        dst = dest_skill / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        written.append(rel.as_posix())
    return written


def compare_skill_trees(a: Path, b: Path) -> list[str]:
    """Return human-readable mismatch messages."""
    msgs: list[str] = []
    if not a.is_dir() and not b.is_dir():
        return msgs
    if a.is_dir() != b.is_dir():
        return [f"presence mismatch: {a} vs {b}"]
    files_a = {p.relative_to(a).as_posix(): p for p in iter_files(a)}
    files_b = {p.relative_to(b).as_posix(): p for p in iter_files(b)}
    only_a = sorted(set(files_a) - set(files_b))
    only_b = sorted(set(files_b) - set(files_a))
    for rel in only_a:
        msgs.append(f"only in {a}: {rel}")
    for rel in only_b:
        msgs.append(f"only in {b}: {rel}")
    for rel in sorted(set(files_a) & set(files_b)):
        if canonical_file_bytes(files_a[rel]) != canonical_file_bytes(files_b[rel]):
            msgs.append(
                f"content mismatch {rel}: "
                f"{hashlib.sha256(canonical_file_bytes(files_a[rel])).hexdigest()[:12]} "
                f"vs {hashlib.sha256(canonical_file_bytes(files_b[rel])).hexdigest()[:12]}"
            )
    return msgs


def host_root_is_tracked(root: Path, host: str) -> bool:
    """Does git track anything under this host root?"""
    git_dir = root / ".git"
    if not git_dir.exists():
        return False
    proc = subprocess.run(
        [
            "git",
            "--git-dir",
            str(git_dir),
            "--work-tree",
            str(root),
            "ls-files",
            "--",
            host,
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(root),
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(root / ".gitconfig-none")},
    )
    return proc.returncode == 0 and proc.stdout.strip() != ""


def git_tracked_relpaths(root: Path, host: str) -> list[str] | None:
    """Tracked paths under a host, as git stores them (case-preserving).

    ``Path.rglob`` on a case-insensitive host folds ``ARCHITECTURE.md`` into
    ``architecture.md``. The index does not. ``None`` means git could not
    answer (throwaway fixtures that are not a repository).

    ``--git-dir`` is pinned so a fixture cannot walk up into the real checkout.
    """
    git_dir = root / ".git"
    if not git_dir.exists():
        return None
    proc = subprocess.run(
        [
            "git",
            "--git-dir",
            str(git_dir),
            "--work-tree",
            str(root),
            "ls-files",
            "--full-name",
            "-z",
            "--",
            host,
        ],
        cwd=str(root),
        capture_output=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(root / ".gitconfig-none")},
    )
    if proc.returncode != 0:
        return None
    prefix = host.replace("\\", "/").rstrip("/") + "/"
    rels: list[str] = []
    for line in proc.stdout.decode("utf-8", "replace").split("\0"):
        if not line:
            continue
        path = line.replace("\\", "/")
        if path.startswith(prefix):
            rels.append(path[len(prefix):])
    return rels


def assert_roster_hosts(root: Path) -> list[str]:
    """Roster hosts must exist and be tracked. Returns the complaints."""
    problems = []
    for host in HOST_SKILL_ROOTS:
        path = root / host
        if not path.is_dir():
            problems.append(
                f"roster host root missing: {host}. Adding a host is a reviewable "
                f"act -- create and commit it, do not let a sync conjure it."
            )
        elif not host_root_is_tracked(root, host):
            n = sum(1 for _ in path.rglob("*") if _.is_dir())
            problems.append(
                f"roster host root is entirely UNTRACKED: {host} ({n} directories on "
                f"disk, 0 tracked by git). Parity against it measures this machine, "
                f"not the repository. Commit it or drop it from HOST_SKILL_ROOTS."
            )
    return problems


def find_destination_only_packages(root: Path, source_host: str = DEFAULT_SOURCE_HOST) -> list[str]:
    """Packages present in a mirror host but absent from the canonical host.

    Parity was checked by walking the names discovered under the canonical
    host and comparing each across the roster. A package that exists ONLY in a
    mirror is not in that list, so nothing ever looked at it: delete a skill
    from `.agents/skills` without syncing, or add one directly to a mirror, and
    the gate still reported every name it knew about as identical.

    The direction matters. `compare_skill_trees` already refuses a
    destination-only FILE inside a package it is comparing; this is the same
    rule one level up, for a whole package that comparison never reaches.
    """
    source_names = {
        d.name
        for d in (root / source_host).iterdir()
        if d.is_dir() and not d.name.startswith(".")
    } if (root / source_host).is_dir() else set()

    strays: list[str] = []
    for host in HOST_SKILL_ROOTS:
        if host == source_host:
            continue
        host_dir = root / host
        if not host_dir.is_dir():
            continue
        for d in sorted(host_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if d.name not in source_names:
                strays.append(
                    f"{host}/{d.name} exists but {source_host}/{d.name} does not. "
                    f"A mirror may not hold a package the canonical host has never "
                    f"declared; delete it, or promote it into {source_host}."
                )
    return strays


def _tracked_paths_for_scope(
    paths: list[str] | None, skill_names: Sequence[str], full_estate: bool
) -> list[str] | None:
    if paths is None or full_estate:
        return paths
    selected = set(skill_names)
    return [path for path in paths if path.partition("/")[0] in selected]


def check_parity(
    root: Path,
    skill_names: Sequence[str],
    source_host: str = DEFAULT_SOURCE_HOST,
    *,
    full_estate: bool = True,
) -> int:
    """Compare selected packages; direct callers retain the global census by default."""
    host_names = (source_host, *(host for host in HOST_SKILL_ROOTS if host != source_host))
    hosts = [root / host for host in host_names]
    errors = 0
    for problem in assert_roster_hosts(root):
        print(f"FAIL roster: {problem}")
        errors += 1
    errors += _check_tracked_path_parity(root, skill_names, source_host, full_estate)
    if full_estate:
        for stray in find_destination_only_packages(root, source_host=source_host):
            print(f"FAIL stray: {stray}")
            errors += 1
    for name in skill_names:
        errors += _check_package_parity(name, [host / name for host in hosts])
    return errors


def _check_tracked_path_parity(
    root: Path,
    skill_names: Sequence[str],
    source_host: str,
    full_estate: bool,
) -> int:
    canonical = _tracked_paths_for_scope(
        git_tracked_relpaths(root, source_host), skill_names, full_estate
    )
    if canonical is None:
        return 0
    errors = 0
    for host in HOST_SKILL_ROOTS:
        if host == source_host:
            continue
        other = _tracked_paths_for_scope(git_tracked_relpaths(root, host), skill_names, full_estate)
        if other is None:
            continue
        only_canonical = sorted(set(canonical) - set(other))
        only_other = sorted(set(other) - set(canonical))
        if only_canonical or only_other:
            errors += _report_tracked_path_split(source_host, host, only_canonical, only_other)
    return errors


def _report_tracked_path_split(
    source_host: str,
    host: str,
    only_canonical: list[str],
    only_other: list[str],
) -> int:
    print(
        f"FAIL tracked-path case/name split: {source_host} vs {host} "
        "(git ls-files, case-sensitive; Windows pathlib folding is not a pass)"
    )
    for relative in only_canonical[:20]:
        print(f"  only in {source_host}: {relative}")
    for relative in only_other[:20]:
        print(f"  only in {host}: {relative}")
    return 1


def _check_package_parity(name: str, paths: list[Path]) -> int:
    missing = [str(path) for path in paths if not path.is_dir()]
    if missing:
        print(f"FAIL {name}: missing dirs: {missing}")
        return 1
    base = paths[0]
    base_hash = package_tree_hash(base)
    errors = sum(_report_package_difference(name, base, base_hash, other) for other in paths[1:])
    if errors == 0:
        print(
            f"OK   {name}: {len(iter_files(base))} files identical across {len(paths)} source/host roots "
            f"(package_sha256={base_hash[:16]}…)"
        )
    return errors


def _report_package_difference(name: str, base: Path, base_hash: str, other: Path) -> int:
    messages = compare_skill_trees(base, other)
    other_hash = package_tree_hash(other)
    if not messages and other_hash == base_hash:
        return 0
    print(f"FAIL {name}:")
    if other_hash != base_hash:
        print(f"  package hash {base}={base_hash[:16]} vs {other}={other_hash[:16]}")
    for message in messages:
        print(f"  {message}")
    return 1


def _preflight_sync(mirror: FourHostSkillMirror, skill_names: Sequence[str]) -> None:
    for host in mirror.hosts:
        host_root = mirror.root / host
        _contained_package_path(host_root, mirror.root)
        if not host_root.is_dir():
            raise PackagingReceiptError("HOST_ROOT_MISSING", str(host_root))
    for name in skill_names:
        source = mirror._package_path(name, mirror.source_host)
        if not source.is_dir():
            raise PackagingReceiptError("SOURCE_PACKAGE_MISSING", str(source))
        iter_files(source)
        source_files = {p.relative_to(source).as_posix() for p in iter_files(source)}
        for host in mirror.hosts:
            if host == mirror.source_host:
                continue
            destination = mirror._package_path(name, host)
            extra = {p.relative_to(destination).as_posix() for p in iter_files(destination)} - source_files
            if extra:
                raise PackagingReceiptError(
                    "DESTINATION_ONLY_FILES",
                    f"destination has files absent from canonical source {destination}: {sorted(extra)}",
                )


def sync_skills(
    root: Path,
    skill_names: Sequence[str],
    source_host: str,
    *,
    full_estate: bool = True,
    recovery_factory: MirrorRecoveryFactoryPort,
) -> int:
    mirror = FourHostSkillMirror(root=root, source_host=source_host, hosts=HOST_SKILL_ROOTS)
    try:
        if not skill_names or source_host not in (*HOST_SKILL_ROOTS, CANONICAL_SKILL_ROOT):
            raise PackagingReceiptError("SYNC_SCOPE", "selected skills and a roster source required")
        for name in skill_names:
            _package_name(name)
        recovery = recovery_factory.create(mirror, list(skill_names))
        if not recovery.pending.exists():
            _preflight_sync(mirror, skill_names)
        with recovery.lock:
            return _sync_under_lock(
                root,
                skill_names,
                source_host,
                full_estate,
                mirror,
                recovery,
            )
    except (OSError, RuntimeError, ValueError) as err:
        print(f"REFUSE sync: {err}", file=sys.stderr)
        return 2
    return 0


def _sync_under_lock(
    root: Path,
    skill_names: Sequence[str],
    source_host: str,
    full_estate: bool,
    mirror: FourHostSkillMirror,
    recovery: MirrorRecoveryPort,
) -> int:
    if recovery.recover():
        print("RECOVERED destinations; canonical edits preserved. Retry sync.", file=sys.stderr)
        return 2
    _preflight_sync(mirror, skill_names)
    recovery.begin()
    try:
        for name in skill_names:
            _copy_skill_to_destinations(mirror, name, source_host)
        errors = check_parity(
            root,
            skill_names,
            source_host=source_host,
            full_estate=full_estate,
        )
        if errors:
            recovery.recover()
            return errors
        recovery.finish()
        return 0
    except (OSError, RuntimeError, ValueError):
        recovery.recover()
        raise


def _copy_skill_to_destinations(
    mirror: FourHostSkillMirror,
    name: str,
    source_host: str,
) -> None:
    for host in mirror.hosts:
        if host != source_host:
            written = mirror.copy_package(name, host)
            print(f"SYNC {name} -> {host} ({len(written)} files)")


def emit_package_hashes(root: Path, skill_names: Sequence[str]) -> int:
    try:
        receipt = FourHostSkillMirror(root=root, hosts=HOST_SKILL_ROOTS).receipt(skill_names)
    except PackagingReceiptError as exc:
        print(f"REFUSE receipt: {exc}", file=sys.stderr)
        return 2
    errors = 0
    for row in receipt.skill_rows:
        host_hashes = dict(row.host_digests)
        errors += sum(digest is None for digest in host_hashes.values())
        print(json.dumps(
            {"skill": row.skill, "ok": row.digests_agree, "hashes": host_hashes},
            sort_keys=True,
        ))
    return errors or int(not receipt.all_agree())

def discover_all_skills(root: Path, source_host: str = DEFAULT_SOURCE_HOST) -> list[str]:
    src_dir = root / source_host
    if not src_dir.is_dir():
        return list(DEFAULT_SKILLS)
    return sorted([
        d.name for d in src_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])


def main(
    argv: Sequence[str] | None = None,
    *,
    recovery_factory: MirrorRecoveryFactoryPort | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repo root (default: auto)")
    parser.add_argument(
        "--source-host",
        default=DEFAULT_SOURCE_HOST,
        choices=[CANONICAL_SKILL_ROOT, *HOST_SKILL_ROOTS],
        help="skill source root (default: operads/skills)",
    )
    parser.add_argument(
        "--skills",
        default=None,
        help="comma-separated names; scopes sync/check to those packages (default: whole estate)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="explicitly discover and replicate ALL skills in source host",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only verify parity; do not copy",
    )
    parser.add_argument(
        "--package-hash",
        action="store_true",
        help="emit per-host package-tree hashes for the selected skills",
    )
    parser.add_argument(
        "--receipt",
        action="store_true",
        help="emit one schema-validated receipt of full per-host package digests",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else repo_root_from()
    if args.all or args.skills is None:
        skills = discover_all_skills(root, args.source_host)
    else:
        skills = [s.strip() for s in args.skills.split(",") if s.strip()]
    if args.receipt:
        mirror = FourHostSkillMirror(
            root=root,
            source_host=args.source_host,
            hosts=HOST_SKILL_ROOTS,
        )
        try:
            receipt = mirror.receipt(skills)
        except PackagingReceiptError as exc:
            print(f"REFUSE receipt: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(receipt.as_dict(), sort_keys=True))
        return 0 if receipt.all_agree() else 1
    if args.package_hash:
        return 1 if emit_package_hashes(root, skills) else 0
    full_estate = args.all or args.skills is None
    if args.check:
        errors = check_parity(root, skills, source_host=args.source_host, full_estate=full_estate)
        return 1 if errors else 0
    if recovery_factory is None:
        print(
            "REFUSE sync: MIRROR_RECOVERY_FACTORY_UNBOUND; invoke the packaging controller",
            file=sys.stderr,
        )
        return 2
    return 1 if sync_skills(
        root,
        skills,
        args.source_host,
        full_estate=full_estate,
        recovery_factory=recovery_factory,
    ) else 0


if __name__ == "__main__":
    raise SystemExit(main())
