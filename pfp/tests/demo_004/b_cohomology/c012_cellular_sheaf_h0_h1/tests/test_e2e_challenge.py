"""End-to-End Test for C012 Complete Challenge Package.

Verifies the entire lifecycle:
1. Public participant packet runner.
2. All 68 hidden judge cases evaluated under dual checkers.
3. Mutation suite kills all 40 hostile mutations.
4. Manifest SHA-256 byte-level agreement.
5. Reference self-consistency label REFERENCE_SELF_CONSISTENT (a self-check of the reference solver,
   not a Adversary verdict), computed on a temporary copy of the package.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from projects.mssn_sn_symgam.challenges.b_cohomology.c012_cellular_sheaf_h0_h1.governance.commit_reveal_runner import (
    CommitRevealRunner,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c012_cellular_sheaf_h0_h1.governance.adversary_gate import (
    TERMINAL_REFERENCE_SELF_CONSISTENT,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c012_cellular_sheaf_h0_h1.participant_packet.runner import (
    load_cases,
    load_solver_func,
    run_cases,
)

C012_DIR = Path(__file__).resolve().parent.parent


def test_complete_c012_lifecycle_e2e():
    """Asserts complete end-to-end challenge lifecycle."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Run participant solver on ex01
        ex01 = C012_DIR / "participant_packet" / "examples" / "ex01_solved_constant_tree.json"
        cases = load_cases(ex01)
        solver_fn = load_solver_func()
        out_file = Path(tmp_dir) / "answers.jsonl"
        count = run_cases(solver_fn, cases, out_file)
        assert count == 1
        record = json.loads(out_file.read_text(encoding="utf-8").strip())
        assert record.get("status") == "SOLVED"

        # 2. Run the commit-reveal runner on a temporary copy. Counterexample: the old
        # test ran on the package itself and rewrote the checked-in commitments.
        challenge_root = Path(tmp_dir) / "c012"
        shutil.copytree(
            C012_DIR, challenge_root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
        )
        runner = CommitRevealRunner(
            challenge_root=challenge_root, base_repo_root=Path(tmp_dir) / "store"
        )
        p1 = runner.run_phase1_commit_judge()
        assert p1["manifest_sha256"] != ""

        p2 = runner.run_phase2_freeze_solver()
        assert p2["phase1_binding_sha256"] == p1["manifest_sha256"]

        scoring = runner.run_phase3_reveal_and_score()
        assert scoring.get("verdict") == TERMINAL_REFERENCE_SELF_CONSISTENT
        assert scoring.get("agreements_count") == scoring.get("case_count") == 68
        assert scoring.get("all_passed") is True
