"""End-to-end integration test for C017."""

from __future__ import annotations

import json
import pathlib

from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)

C017_DIR = pathlib.Path(__file__).parent.parent
MANIFEST_PATH = C017_DIR / "judge_packet" / "manifest.json"


def test_manifest_integrity():
    assert MANIFEST_PATH.is_file()
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = data["files"]
    assert len(files) == data["file_count"]
    keys = list(files.keys())
    sorted_keys = sorted(keys, key=lambda s: s.encode("utf-8"))
    assert keys == sorted_keys, "Manifest keys are not strictly sorted by ordinal UTF-8 byte order"


def test_full_pipeline_verdict():
    receipt = run_provisional_evaluation()
    assert receipt["provisional_verdict"]["verdict"] != "PASS_TO_MASTER"
    assert receipt["provisional_verdict"]["details"]["commit_reveal_enforced"] is False
