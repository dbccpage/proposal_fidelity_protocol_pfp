#!/usr/bin/env python3
"""One-command verifier for the research paper deposit.

Deterministic, two-way verification:
1. Every file listed in SHA256SUMS exists and matches its recorded hash.
2. Sweep: no unrecorded non-excluded file is present in the deposit tree.
3. Fail-closed symlink rejection: rejects any unauthorized symlink.
4. Structural artifacts are present and non-empty.
5. Optional/Default named test files pass (--test).
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))
from deposit_paths import read_manifest, safe_path, walk_files

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "SHA256SUMS"

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
    "dev_rips",
    "rt",
    "target",
    "b",
    "scratch",
    "_support",
    "evidence",
    "reconstruction_v1",
}
EXCLUDED_NAMES = {
    "SHA256SUMS",
    ".coverage",
    ".env",
    "DEPOSIT_CHECKLIST.md",
    ".gitkeep",
}
EXCLUDED_SUFFIXES = {".zip", ".pyc", ".pyo", ".tmp", ".log"}

REQUIRED_PATTERNS = (
    "*_monograph.md",
    "*_change_log.md",
    "*_claim_ledger.md",
    "README.md",
    "LICENSE",
    "LICENSE-CODE",
    "pyproject.toml",
    "zenodo_metadata.json",
    "docs/descriptions.md",
    "docs/references.md",
    "code/deposit_paths.py",
)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifests() -> None:
    expected_files = walk_files(ROOT, EXCLUDED_DIRS, EXCLUDED_NAMES, EXCLUDED_SUFFIXES)
    lines = []
    for path in expected_files:
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256_of(path)
        lines.append(f"{digest}  {rel}")
    content = "\n".join(lines) + "\n"
    (ROOT / "SHA256SUMS").write_text(content, encoding="utf-8")
    (ROOT / "MANIFEST.sha256").write_text(content, encoding="utf-8")
    print(f"Wrote {len(lines)} entries to SHA256SUMS and MANIFEST.sha256.")


def check_manifest(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        excluded_names = set(EXCLUDED_NAMES)
        if manifest_path.name == "MANIFEST.sha256":
            excluded_names.add("MANIFEST.sha256")
        expected_files = walk_files(ROOT, EXCLUDED_DIRS, excluded_names, EXCLUDED_SUFFIXES)
        entries = read_manifest(ROOT, manifest_path)
        recorded = {relative for relative, _ in entries}
        for relative, digest in entries:
            path = safe_path(ROOT, relative)
            if not path.is_file():
                errors.append(f"Recorded file missing: {relative}")
            elif sha256_of(path) != digest:
                errors.append(f"Hash mismatch: {relative}")
        expected = {path.relative_to(ROOT).as_posix() for path in expected_files}
        for relative in sorted(expected - recorded):
            errors.append(f"Unrecorded deposit file: {relative}")
        for relative in sorted(recorded - expected):
            errors.append(f"Excluded file listed in manifest: {relative}")

        # Check required structural files/patterns
        for pattern in REQUIRED_PATTERNS:
            if "/" in pattern:
                target = ROOT / pattern
                if not target.is_file() or not target.stat().st_size:
                    errors.append(f"Required file missing or empty: {pattern}")
            else:
                matches = list(ROOT.glob(pattern))
                if pattern == "*_monograph.md" and not matches:
                    matches = list(ROOT.glob("paper.md"))
                if pattern == "*_change_log.md" and not matches:
                    matches = list(ROOT.glob("paper_change_log.md"))
                if pattern == "*_claim_ledger.md" and not matches:
                    matches = list(ROOT.glob("paper_claim_ledger.md"))
                if not matches or not any(m.stat().st_size > 0 for m in matches):
                    errors.append(f"Required file pattern missing or empty: {pattern}")
    except (OSError, ValueError) as error:
        errors.append(str(error))
    return errors


def check_tests(targets: list[str]) -> list[str]:
    if not targets:
        tests_dir = ROOT / "code" / "tests"
        if tests_dir.is_dir():
            targets = [p.relative_to(ROOT).as_posix() for p in tests_dir.glob("test_*.py")]
    if not targets:
        return ["No test files found in code/tests/"]
    errors: list[str] = []
    for target in targets:
        try:
            path = safe_path(ROOT, target)
            if not target.startswith("code/tests/test_") or path.suffix != ".py" or not path.is_file():
                raise ValueError(f"Invalid test target: {target}")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", target, "-q"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if result.returncode:
                errors.append(f"Pytest failure in {target}:\n{result.stdout}\n{result.stderr}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            errors.append(str(error))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify paper deposit package.")
    parser.add_argument("--write", action="store_true", help="Recompute and write SHA256SUMS and MANIFEST.sha256.")
    parser.add_argument("--test", action="append", default=[], help="Named test file; repeat as needed.")
    args = parser.parse_args()

    if args.write:
        write_manifests()
        return 0

    manifest_target = MANIFEST
    if not manifest_target.is_file() and (ROOT / "MANIFEST.sha256").is_file():
        manifest_target = ROOT / "MANIFEST.sha256"

    if not manifest_target.is_file():
        print("FAIL: Neither SHA256SUMS nor MANIFEST.sha256 found. Run with --write to generate.")
        return 1

    manifest_errors = check_manifest(manifest_target)
    if manifest_errors:
        print(f"FAIL: Manifest checks failed ({len(manifest_errors)} issues):")
        for err in manifest_errors:
            print(f"  - {err}")
        return 1
    else:
        print("OK: Manifest and two-way sweep checks passed.")

    if args.test:
        test_errors = check_tests(args.test)
        if test_errors:
            for error in test_errors:
                print(f"FAIL: {error}")
            return 1
        print("OK: Selected test files passed.")

    print("\nVerification PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
