#!/usr/bin/env python3
"""Build deterministic release manifests and ZIP bundle for PO-001.

Authority status: None. Packaging bytes is not evidence for any claim.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects.zip"
ARCHIVE_PREFIX = "001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects"
ZIP_DATE = (2026, 10, 2, 12, 0, 0)

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    ".lake",
    "dist",
    "build",
    "htmlcov",
    "scratch",
}
EXCLUDED_NAMES = {".coverage", "cov.json", "coverage.xml", "covering_edge_descent.aux", "covering_edge_descent.log"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".out"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def enumerate_payload(root: Path) -> list[str]:
    """Enumerate relative POSIX paths of all payload files in UTF-8 ordinal order."""
    payload: list[str] = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in EXCLUDED_DIRS or part.endswith((".egg-info", ".dist-info")) for part in rel.parts):
            continue
        if p.is_symlink():
            raise ValueError(f"symlink is not a release payload: {rel}")
        if not p.is_file():
            continue
        if p.name in EXCLUDED_NAMES or p.suffix in EXCLUDED_SUFFIXES:
            continue
        rel_posix = rel.as_posix()
        if rel_posix in ("SHA256SUMS", "MANIFEST.sha256") or rel_posix.endswith(".zip"):
            continue
        payload.append(rel_posix)
    payload.sort(key=lambda s: s.encode("utf-8"))
    return payload


def generate_manifests(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    payload = enumerate_payload(root)

    # 1. MANIFEST.sha256 covers exactly the payload files
    manifest_entries = {rel: sha256_of(root / rel) for rel in payload}
    manifest_lines = [
        f"{digest}  {rel}"
        for rel, digest in sorted(manifest_entries.items(), key=lambda pair: pair[0].encode("utf-8"))
    ]
    manifest_bytes = ("\n".join(manifest_lines) + "\n").encode("utf-8")
    (root / "MANIFEST.sha256").write_bytes(manifest_bytes)

    # 2. SHA256SUMS covers payload files PLUS MANIFEST.sha256
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    sums_entries = dict(manifest_entries)
    sums_entries["MANIFEST.sha256"] = manifest_sha
    sums_lines = [
        f"{digest}  {rel}"
        for rel, digest in sorted(sums_entries.items(), key=lambda pair: pair[0].encode("utf-8"))
    ]
    sums_bytes = ("\n".join(sums_lines) + "\n").encode("utf-8")
    (root / "SHA256SUMS").write_bytes(sums_bytes)

    return manifest_entries, sums_entries


def build_archive(root: Path, archive_path: Path) -> None:
    payload = enumerate_payload(root)
    all_members = sorted(
        [*payload, "MANIFEST.sha256", "SHA256SUMS"],
        key=lambda s: s.encode("utf-8"),
    )

    seen: set[str] = set()
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for rel in all_members:
            key = rel.casefold()
            if key in seen:
                raise ValueError(f"duplicate archive member: {rel}")
            seen.add(key)
            member_name = f"{ARCHIVE_PREFIX}/{rel}"
            info = zipfile.ZipInfo(filename=member_name, date_time=ZIP_DATE)
            info.create_system = 3  # Unix
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            data = (root / rel).read_bytes()
            archive.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Verify without modifying")
    args = parser.parse_args()

    root = PACKAGE_ROOT
    archive_path = root / ARCHIVE_NAME

    if not args.check_only:
        print("1. Generating MANIFEST.sha256 and SHA256SUMS...")
        generate_manifests(root)
        print("2. Building deterministic release ZIP archive...")
        build_archive(root, archive_path)
        print(f"   Built: {archive_path.name} ({archive_path.stat().st_size:,} bytes)")

    print("3. Verifying release...")
    manifest_lines = (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    sums_lines = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    print(f"   MANIFEST.sha256 entries: {len(manifest_lines)}")
    print(f"   SHA256SUMS entries: {len(sums_lines)}")

    with zipfile.ZipFile(archive_path, "r") as archive:
        infos = archive.infolist()
        print(f"   ZIP members: {len(infos)}")
        for info in infos:
            assert info.create_system == 3, f"Non-unix create_system: {info.create_system}"
            assert (info.external_attr >> 16) == 0o100644, f"Bad external_attr: {oct(info.external_attr >> 16)}"
    print("Release verified successfully.")


if __name__ == "__main__":
    main()
