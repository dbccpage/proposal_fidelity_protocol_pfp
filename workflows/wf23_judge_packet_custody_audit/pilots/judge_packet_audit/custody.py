"""Custody replay: do recorded digests bind the bytes in the checkout?

For every digest a package records (judge manifests, commitment records,
freeze records, scoring receipts, reality-gate receipts), the harness
recomputes SHA-256 over two canonical byte forms of the named file: LF line
endings and CRLF line endings. A digest that matches neither names bytes that
are not in the checkout.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")
RECORD_GLOBS = ("commitments/*.json", "commit_reveal/*.json", "reality_gate_receipt.json")


def lf_crlf_digests(data: bytes) -> tuple[str, str]:
    lf = data.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return hashlib.sha256(lf).hexdigest(), hashlib.sha256(crlf).hexdigest()


def classify(digest: str, data: bytes | None) -> str:
    if data is None:
        return "FILE_MISSING"
    lf, crlf = lf_crlf_digests(data)
    if digest == lf and digest == crlf:
        return "LF_AND_CRLF"
    if digest == lf:
        return "LF"
    if digest == crlf:
        return "CRLF"
    return "NEITHER"


def _read(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def manifest_replay(pkg_dir: Path) -> dict[str, Any] | None:
    """Replays ``judge_packet/manifest.json`` (or a package-root ``manifest.json``)."""
    candidates = [pkg_dir / "judge_packet" / "manifest.json", pkg_dir / "manifest.json"]
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        return None
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {"path": path.relative_to(pkg_dir).as_posix(), "parse_error": True}
    entries = _manifest_entries(data)
    counts = {"LF": 0, "CRLF": 0, "LF_AND_CRLF": 0, "NEITHER": 0, "FILE_MISSING": 0}
    per_entry = []
    listed = set()
    for rel, digest in entries:
        target = _resolve(pkg_dir, path.parent, rel)
        klass = classify(digest, _read(target) if target else None)
        counts[klass] += 1
        if target is not None:
            listed.add(target.resolve())
        per_entry.append({"path": rel, "class": klass})
    judge_files = [
        p
        for p in (pkg_dir / "judge_packet").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != "manifest.json"
    ]
    unlisted = sorted(
        p.relative_to(pkg_dir).as_posix() for p in judge_files if p.resolve() not in listed
    )
    lf, crlf = lf_crlf_digests(raw)
    return {
        "path": path.relative_to(pkg_dir).as_posix(),
        "declared_files_count": data.get("files_count") if isinstance(data, dict) else None,
        "entries": len(entries),
        "counts": counts,
        "non_lf_entries": [e for e in per_entry if e["class"] != "LF"],
        "judge_files_not_listed": unlisted,
        "manifest_sha256_lf": lf,
        "manifest_sha256_crlf": crlf,
        "raw_has_cr": b"\r" in raw,
    }


def _manifest_entries(data: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(data, dict):
        items = data.get("manifest") or data.get("files") or data.get("entries")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    rel = item.get("path") or item.get("file")
                    digest = item.get("sha256") or item.get("digest")
                    if isinstance(rel, str) and isinstance(digest, str) and HEX64.match(digest):
                        out.append((rel, digest))
        elif isinstance(items, dict):
            for rel, value in items.items():
                digest = (
                    value.get("sha256") or value.get("digest") if isinstance(value, dict) else value
                )
                if isinstance(digest, str) and HEX64.match(digest):
                    out.append((rel, digest))
    return out


def _resolve(pkg_dir: Path, manifest_dir: Path, rel: str) -> Path | None:
    for base in (pkg_dir, manifest_dir):
        candidate = base / rel
        if candidate.is_file():
            return candidate
    return None


def record_replay(pkg_dir: Path, manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Checks every 64-hex digest in commitment and receipt records."""
    index: dict[str, list[str]] = {}
    for path in pkg_dir.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        lf, crlf = lf_crlf_digests(path.read_bytes())
        rel = path.relative_to(pkg_dir).as_posix()
        index.setdefault(lf, []).append(f"{rel}@LF")
        if crlf != lf:
            index.setdefault(crlf, []).append(f"{rel}@CRLF")
    out = []
    for pattern in RECORD_GLOBS:
        for path in sorted(pkg_dir.glob(pattern)):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, UnicodeDecodeError):
                out.append({"record": path.relative_to(pkg_dir).as_posix(), "parse_error": True})
                continue
            fields = []
            for key_path, digest in _digests(data, "$"):
                matches = sorted(index.get(digest, []))
                klass = "MATCHES_FILE" if matches else "NO_FILE_MATCH"
                if key_path.endswith("manifest_sha256") and manifest is not None:
                    if digest == manifest["manifest_sha256_lf"]:
                        klass = "MANIFEST_LF"
                    elif digest == manifest["manifest_sha256_crlf"]:
                        klass = "MANIFEST_CRLF"
                    else:
                        klass = "MANIFEST_NEITHER"
                fields.append({"field": key_path, "class": klass, "matches": matches[:4]})
            out.append(
                {
                    "record": path.relative_to(pkg_dir).as_posix(),
                    "verdict": _verdict(data),
                    "digest_fields": fields,
                }
            )
    return out


def _digests(value: Any, path: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key in sorted(value):
            out.extend(_digests(value[key], f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.extend(_digests(item, f"{path}[{index}]"))
    elif isinstance(value, str) and HEX64.match(value):
        out.append((path, value))
    return out


def _verdict(data: Any) -> str | None:
    if isinstance(data, dict):
        for key in ("verdict", "terminal_verdict", "gate_verdict", "final_verdict"):
            value = data.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict) and isinstance(value.get("verdict"), str):
                return value["verdict"]
    return None


@dataclass(frozen=True)
class GitRef:
    """A repository and a revision in it, for read-only history queries.

    The audited tree may be a working tree of ``repo`` at ``rev`` or an export
    of ``rev`` (``git archive``) that has no repository of its own.
    """

    repo: Path
    rev: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return (self.repo, self.rev) == (other.repo, other.rev)  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash((type(self), self.repo, self.rev))


def git_first_added(git: GitRef, rel_path: str) -> dict[str, str] | None:
    """The commit (and committer date) in the history of ``git.rev`` that first added ``rel_path``."""
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(git.repo),
            "log",
            git.rev,
            "--diff-filter=A",
            "--format=%H %cI",
            "--",
            rel_path,
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    lines = [ln for ln in proc.stdout.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    if not lines:
        return None
    commit, _, date = lines[-1].partition(" ")
    return {"commit": commit, "date": date}


def commitment_timing(repo_root: Path, pkg_dir: Path, git: GitRef) -> dict[str, Any]:
    """Whether a judge commitment was committed to git before the scoring record."""
    rel_pkg = pkg_dir.relative_to(repo_root).as_posix()
    commitments = sorted(
        p
        for pattern in (
            "commitments/*judge_commitment*.json",
            "commit_reveal/*judge_commitment*.json",
        )
        for p in pkg_dir.glob(pattern)
    )
    receipts = sorted(
        p
        for pattern in (
            "commitments/*scoring_receipt*.json",
            "commit_reveal/*scoring_receipt*.json",
            "reality_gate_receipt.json",
        )
        for p in pkg_dir.glob(pattern)
    )
    out: dict[str, Any] = {"judge_commitment_files": [], "receipt_files": []}
    for path in commitments:
        rel = path.relative_to(pkg_dir).as_posix()
        out["judge_commitment_files"].append(
            {"path": rel, "first_added": git_first_added(git, f"{rel_pkg}/{rel}")}
        )
    for path in receipts:
        rel = path.relative_to(pkg_dir).as_posix()
        out["receipt_files"].append(
            {"path": rel, "first_added": git_first_added(git, f"{rel_pkg}/{rel}")}
        )
    commit_ids = {
        c["first_added"]["commit"] for c in out["judge_commitment_files"] if c["first_added"]
    }
    receipt_ids = {r["first_added"]["commit"] for r in out["receipt_files"] if r["first_added"]}
    if not commitments:
        out["class"] = "NO_JUDGE_COMMITMENT_RECORD"
    elif commit_ids and receipt_ids and commit_ids & receipt_ids:
        out["class"] = "COMMITMENT_ADDED_WITH_RECEIPT"
    elif commit_ids and not receipt_ids:
        out["class"] = "COMMITMENT_WITHOUT_RECEIPT"
    else:
        out["class"] = "COMMITMENT_ADDED_SEPARATELY"
    return out
