#!/usr/bin/env python3
"""Verify the tracked packaging roster and shared manifest parity.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from operations.use_cases.packaging.sync_cross_host_skills import (  # noqa: E402
    HOST_SKILL_ROOTS,
)

ACTIVE_HOST_ROOTS = [root.split("/")[0] for root in HOST_SKILL_ROOTS]


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check_host_seat_presence_and_parity(repo_root: Path) -> list[str]:
    violations = []
    # 1. Check directory presence for active host roots
    for host in ACTIVE_HOST_ROOTS:
        host_skills = repo_root / host / "skills"
        if not host_skills.is_dir():
            violations.append(f"Host seat missing or uninitialized: {host_skills}")
        tracked = subprocess.run(
            ["git", "ls-files", "--", f"{host}/skills"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode or not tracked.stdout.strip():
            violations.append(f"Host seat is not tracked: {host}")

    # 2. Check byte parity for shared governance manifests across active hosts
    canon_root = repo_root / "operads"
    manifests_to_check = [
        Path("skills/_shared/family_registry.md"),
        Path("registry/capabilities.yaml"),
        Path("registry/lifecycle.yaml"),
    ]

    for rel_path in manifests_to_check:
        canon_file = canon_root / rel_path
        if not canon_file.is_file():
            violations.append(f"Canonical manifest missing in OEOP: {rel_path}")
            continue
        canon_digest = hash_file(canon_file)

        for mirror_host in ACTIVE_HOST_ROOTS:
            mirror_file = repo_root / mirror_host / rel_path
            if not mirror_file.is_file():
                violations.append(f"Mirror file missing in {mirror_host}: {rel_path}")
            else:
                mirror_digest = hash_file(mirror_file)
                if mirror_digest != canon_digest:
                    violations.append(
                        f"Byte divergence between OEOP and {mirror_host} for {rel_path} "
                        f"({canon_digest[:8]} != {mirror_digest[:8]})"
                    )

    return violations


def main() -> int:
    repo_root = Path.cwd()
    violations = check_host_seat_presence_and_parity(repo_root)
    if violations:
        for v in violations:
            print(f"[FAIL] {v}", file=sys.stderr)
        return 1
    print("PASS: The tracked packaging roster is present and shared manifests have byte parity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
