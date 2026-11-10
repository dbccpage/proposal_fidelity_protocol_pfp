"""Hostile Checker Mutation Suite Verification for C014.

Verifies that 100% of injected corrupted decompositions, non-orthogonal flows,
harmonic-dimension errors, and invalid certificates are caught and rejected.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import pathlib

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)

MUT_DIR = pathlib.Path(__file__).parent / "mutations"


def test_mutation_suite_100_percent_kill_rate():
    mut_files = sorted(MUT_DIR.glob("mut_*.json"))
    assert len(mut_files) == 52, f"Expected 52 mutation files, found {len(mut_files)}"

    for mf in mut_files:
        with open(mf, "r", encoding="utf-8") as f:
            data = json.load(f)

        case_in = data["input_case"]
        corrupted = data["corrupted_output"]

        eval_res = evaluate_dual(case_in, corrupted)
        assert eval_res["verdict"] == "FAIL", (
            f"Checker mutation leak on {mf.name}: checkers failed to kill mutation! "
            f"eval_res={eval_res}"
        )


def test_mutation_payloads_are_pairwise_distinct():
    """Padding with copies overstated coverage (2026-09-29 correction removed them)."""
    payloads = [
        json.dumps([data["input_case"], data["corrupted_output"]], sort_keys=True)
        for data in (
            json.loads(p.read_text(encoding="utf-8")) for p in sorted(MUT_DIR.glob("mut_*.json"))
        )
    ]
    assert len(payloads) == len(set(payloads)) == 52
