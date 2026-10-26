"""End-to-end challenge integration test."""

from __future__ import annotations

import pathlib

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c019_h2_obstruction_extension.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)

C019_DIR = pathlib.Path(__file__).parent.parent


def test_e2e_full_challenge_pipeline():
    receipt = run_provisional_evaluation()
    assert receipt["integrity_snapshot"]["solver_sha256"]
    assert receipt["evaluation"]["total_cases"] == 58  # duplicates removed 2026-09-29
    assert receipt["evaluation"]["passed_cases"] == 58
    assert receipt["evaluation"]["mutation_kill_rate"] == 1.0
    assert receipt["provisional_verdict"]["verdict"] == "REFUSE"
