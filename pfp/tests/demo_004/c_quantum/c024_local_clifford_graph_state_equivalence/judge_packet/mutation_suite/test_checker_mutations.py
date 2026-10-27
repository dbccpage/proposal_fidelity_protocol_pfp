"""Hostile Mutation Test Suite for C024 (Local Clifford Graph State Equivalence).

Asserts 100% kill rate across all hostile mutations.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)

MUTATIONS_DIR = Path(__file__).resolve().parent / "mutations"
MUTATION_FILES = sorted(MUTATIONS_DIR.glob("mut_*.json"))


def test_mutation_count():
    assert len(MUTATION_FILES) == 39, f"Expected 39 mutations, got {len(MUTATION_FILES)}"


@pytest.mark.parametrize("mut_path", MUTATION_FILES, ids=lambda p: p.stem)
def test_hostile_mutation_killed(mut_path: Path):
    with open(mut_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    case = data["case"]
    candidate = data["candidate"]
    desc = data.get("desc", mut_path.stem)

    passed, detail, meta = evaluate_dual(case, candidate)
    assert not passed, f"Hostile mutation survived! [{desc}] Detail: {detail}"


def test_mutation_payloads_are_pairwise_distinct():
    """Padding with copies overstated coverage (2026-09-29 correction removed them)."""
    payloads = [
        json.dumps([data["case"], data["candidate"]], sort_keys=True)
        for data in (
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(MUTATIONS_DIR.glob("mut_*.json"))
        )
    ]
    assert len(payloads) == len(set(payloads)) == 39
