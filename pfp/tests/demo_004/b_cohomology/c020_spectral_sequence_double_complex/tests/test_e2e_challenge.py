"""End-to-end challenge integration test for C020."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)


def test_e2e_full_challenge_pipeline():
    receipt = run_provisional_evaluation()
    assert receipt["integrity_snapshot"]["solver_sha256"]
    assert receipt["evaluation"]["total_cases"] == 46  # duplicates removed 2026-09-29
    assert receipt["evaluation"]["passed_cases"] == 46
    assert receipt["evaluation"]["mutation_kill_rate"] == 1.0
    assert receipt["provisional_verdict"]["verdict"] == "REFUSE"
