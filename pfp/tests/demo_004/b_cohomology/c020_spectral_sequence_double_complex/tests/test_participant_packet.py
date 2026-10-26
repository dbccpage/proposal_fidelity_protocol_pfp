"""Test participant packet for C020."""

from __future__ import annotations

from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.participant_packet.runner import (
    run_public_examples,
)

PARTICIPANT_DIR = Path(__file__).resolve().parent.parent / "participant_packet"


def test_participant_packet_structure():
    assert (PARTICIPANT_DIR / "TASK.md").exists()
    assert (PARTICIPANT_DIR / "accounting.json").exists()
    assert (PARTICIPANT_DIR / "runner.py").exists()

    examples = list((PARTICIPANT_DIR / "examples").glob("*.json"))
    assert len(examples) == 16


def test_runner_execution():
    res = run_public_examples()
    assert res["total_examples"] == 16
    assert len(res["results"]) == 16
    for r in res["results"]:
        assert r["status"] in ("SOLVED", "OUT_OF_SCOPE")
