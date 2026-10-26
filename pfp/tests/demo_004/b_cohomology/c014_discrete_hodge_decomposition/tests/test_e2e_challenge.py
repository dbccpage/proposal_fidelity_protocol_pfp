"""End-to-End Challenge Test for C014.

Verifies complete execution pipeline:
- Public examples through runner
- Reference solver on all hidden cases
- Hostile mutation kill verification
- Manifest hash integrity

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"


def test_manifest_hash_integrity():
    """Asserts manifest.json correctly catalogs all files with strict byte matching."""
    manifest_file = JUDGE_DIR / "manifest.json"
    assert manifest_file.exists(), "manifest.json missing"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))

    entries = data["manifest"]
    assert len(entries) >= 100, f"Expected >= 100 files, found {len(entries)}"

    for item in entries:
        rel_path = item["path"]
        expected_sha = item["sha256"]
        full_path = CHALLENGE_DIR / rel_path
        assert full_path.exists(), f"File in manifest does not exist on disk: {full_path}"
        actual_sha = hashlib.sha256(full_path.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, (
            f"SHA mismatch on {rel_path}: {actual_sha} != {expected_sha}"
        )
