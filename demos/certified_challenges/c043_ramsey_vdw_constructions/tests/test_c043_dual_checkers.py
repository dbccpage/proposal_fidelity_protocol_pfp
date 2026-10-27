# AuthorityEffect: None.
"""Tests for Exact and Independent Dual Checkers in C043 Ramsey & Van der Waerden."""

import json
from pathlib import Path

from c043_ramsey_vdw_constructions.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c043_ramsey_vdw_constructions.reference_solver.solver import (
    solve,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def test_public_examples_reference_solver():
    """All 10 public examples must be solved by reference solver and accepted by dual checkers."""
    examples_dir = BASE_DIR / "participant_packet" / "examples"
    example_files = sorted(examples_dir.glob("c043_pub_*.json"))
    assert len(example_files) == 10

    for f in example_files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok is True, f"Failed on {f.name}: {msg}"
        assert receipt["checkers_agree"] is True


def test_dual_evaluator_rejects_monochromatic_clique():
    """Checker must reject a graph colouring containing a monochromatic K_3."""
    case = {
        "case_id": "test_k3",
        "family": "RAMSEY",
        "n_vertices": 3,
        "k_clique": 3,
        "n_colours": 2,
        "target": "AVOID_MONOCHROMATIC_CLIQUE",
    }
    # All 3 edges coloured 0 -> monochromatic triangle!
    ans = {
        "case_id": "test_k3",
        "status": "WITNESS_FOUND",
        "certificate_type": "EDGE_COLOURING",
        "certificate": {
            "num_vertices": 3,
            "edges": [{"u": 0, "v": 1, "c": 0}, {"u": 0, "v": 2, "c": 0}, {"u": 1, "v": 2, "c": 0}],
        },
    }
    ok, msg, receipt = evaluate_dual(case, ans)
    assert ok is False
    assert receipt["checkers_agree"] is True


def test_dual_evaluator_rejects_monochromatic_ap():
    """Checker must reject a progression containing a monochromatic 3-AP."""
    case = {
        "case_id": "test_ap3",
        "family": "VAN_DER_WAERDEN",
        "length": 5,
        "k_ap": 3,
        "n_colours": 2,
        "target": "AVOID_MONOCHROMATIC_AP",
    }
    # [0, 0, 0, 1, 1] contains 3-AP at indices 0, 1, 2 all colour 0
    ans = {
        "case_id": "test_ap3",
        "status": "WITNESS_FOUND",
        "certificate_type": "SEQUENCE_COLOURING",
        "certificate": {"length": 5, "colouring": [0, 0, 0, 1, 1]},
    }
    ok, msg, receipt = evaluate_dual(case, ans)
    assert ok is False
    assert receipt["checkers_agree"] is True


def test_mutation_suite_rejection():
    """All 48 hostile mutations in the judge packet must be rejected."""
    mut_dir = BASE_DIR / "judge_packet" / "mutation_suite"
    mut_files = sorted(mut_dir.glob("c043_mut_*.json"))
    assert len(mut_files) == 48

    for f in mut_files:
        with open(f, "r", encoding="utf-8") as stream:
            payload = json.load(stream)
        case = payload["case"]
        corrupted_ans = payload["answer"]
        ok, msg, receipt = evaluate_dual(case, corrupted_ans)
        assert ok is False, f"Hostile mutation {f.name} was falsely accepted: {msg}"
