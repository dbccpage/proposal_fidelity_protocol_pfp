"""Hostile Mutation Suite Tests for C016 Checkers.

Asserts 100% kill rate across every hostile mutation of cohomology cup product certificates.
"""

from __future__ import annotations

import json
import pathlib

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)

MUT_DIR = pathlib.Path(__file__).parent / "mutations"


def test_mutation_suite_100_percent_kill_rate():
    mut_files = sorted(list(MUT_DIR.glob("mut_*.json")))
    assert len(mut_files) == 23, f"Expected 23 mutation files, found {len(mut_files)}"

    killed = 0
    survived = []

    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted = data["corrupted_result"]
        ok, reason, details = evaluate_dual(case, corrupted)
        if not ok:
            killed += 1
        else:
            survived.append((mf.name, data["description"]))

    assert len(survived) == 0, f"Hostile mutations survived: {survived}"
    assert killed == 23, f"Kill rate {killed}/23 != 100%"


def test_mutation_payloads_are_pairwise_distinct():
    """Padding with copies overstated coverage (2026-09-29 correction removed them)."""
    payloads = [
        json.dumps([data["case"], data["corrupted_result"]], sort_keys=True)
        for data in (
            json.loads(p.read_text(encoding="utf-8")) for p in sorted(MUT_DIR.glob("mut_*.json"))
        )
    ]
    assert len(payloads) == len(set(payloads)) == 23
