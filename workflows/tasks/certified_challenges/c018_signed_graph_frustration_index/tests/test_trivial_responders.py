"""Trivial responders must fail the C018 judge; certified answers must pass.

Before the 2026-09-28 correction an UNKNOWN with trivial bounds (upper = the
identity switching's negative-edge count, lower = 0 or omitted) passed on 60 of
68 judge cases, and `int()` casts accepted 2.7 as 2 and True as 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from c018_signed_graph_frustration_index.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c018_signed_graph_frustration_index.reference_solver.solver import (
    solve,
)

CASES_DIR = Path(sys.modules[evaluate_dual.__module__].__file__).resolve().parents[1] / "cases"
JUDGE_CASES = sorted(CASES_DIR.rglob("*.json"))

K4_NEG = {
    "id": "k4",
    "vertices": ["0", "1", "2", "3"],
    "edges": [
        ["0", "1", -1],
        ["0", "2", -1],
        ["0", "3", -1],
        ["1", "2", -1],
        ["1", "3", -1],
        ["2", "3", -1],
    ],
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _trivial_bounds(case: dict, lower: object = "0") -> dict:
    negatives = sum(1 for e in case.get("edges", []) if len(e) > 2 and e[2] == -1)
    answer = {
        "id": case.get("id"),
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": str(negatives),
        "switching": {},
    }
    if lower is not None:
        answer["lower"] = lower
    return answer


def test_judge_cases_are_present() -> None:
    assert len(JUDGE_CASES) >= 40


def test_reference_answers_pass_every_judge_case() -> None:
    failures = [p.name for p in JUDGE_CASES if not evaluate_dual(_load(p), solve(_load(p))[0])[0]]
    assert failures == []


@pytest.mark.parametrize(
    "lower", ["0", None, -1], ids=["lower_zero", "lower_omitted", "lower_minus_one"]
)
def test_trivial_bounds_unknown_fails_on_every_judge_case(lower: object) -> None:
    """Counterexample: UNKNOWN with upper = #negative edges and lower 0 passed 60/68."""
    passes = [
        p.name for p in JUDGE_CASES if evaluate_dual(_load(p), _trivial_bounds(_load(p), lower))[0]
    ]
    assert passes == []


def test_unknown_is_inadmissible_for_small_graphs_even_with_a_valid_packing() -> None:
    answer = {
        "id": "k4",
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": "6",
        "lower": "1",
        "switching": {},
        "lower_bound": {"kind": "packing", "cycles": [["0", "1", "2"]]},
    }
    assert evaluate_dual(K4_NEG, answer)[0] is False


@pytest.mark.parametrize(
    "answer",
    [
        {},
        {"status": "SOLVED"},
        {"status": "OUT_OF_SCOPE", "witness": {"reason": "SELF_LOOP", "edge": ["0", "0"]}},
    ],
    ids=["empty_object", "bare_solved", "false_self_loop"],
)
def test_constant_responders_fail_on_in_scope_cases(answer: dict) -> None:
    in_scope = [p for p in JUDGE_CASES if not p.name.startswith("poison_")]
    passes = [p.name for p in in_scope if evaluate_dual(_load(p), dict(answer))[0]]
    assert passes == []


def test_float_count_is_rejected() -> None:
    """Counterexample: l = 2.7 passed through int() as 2."""
    good, _ = solve(K4_NEG)
    assert evaluate_dual(K4_NEG, good)[0] is True
    assert evaluate_dual(K4_NEG, {**good, "l": 2.7})[0] is False
    assert evaluate_dual(K4_NEG, {**good, "l": 2.0})[0] is False


def test_boolean_count_and_switching_are_rejected() -> None:
    tri = {
        "id": "t",
        "vertices": ["0", "1", "2"],
        "edges": [["0", "1", -1], ["1", "2", 1], ["2", "0", 1]],
    }
    good, _ = solve(tri)
    assert good["l"] == "1"
    assert evaluate_dual(tri, {**good, "l": True})[0] is False
    assert evaluate_dual(tri, {**good, "switching": {"0": True}})[0] is False


def test_unknown_on_large_graph_needs_a_maximal_packing() -> None:
    large = next(_load(p) for p in JUDGE_CASES if p.name.startswith("base_unknown_"))
    reference, _ = solve(large)
    assert reference["status"] == "UNKNOWN"
    assert evaluate_dual(large, reference)[0] is True
    empty_packing = {**reference, "lower": "0", "lower_bound": {"kind": "packing", "cycles": []}}
    assert evaluate_dual(large, empty_packing)[0] is False
    truncated = json.loads(json.dumps(reference))
    truncated["lower_bound"]["cycles"] = truncated["lower_bound"]["cycles"][:-1]
    truncated["lower"] = str(len(truncated["lower_bound"]["cycles"]))
    assert evaluate_dual(large, truncated)[0] is False


def test_self_loop_witness_must_cite_the_loop() -> None:
    case = {"id": "loop", "vertices": ["0", "1"], "edges": [["1", "1", 1], ["0", "1", 1]]}
    assert evaluate_dual(
        case,
        {
            "id": "loop",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "SELF_LOOP", "edge": ["1", "1"]},
        },
    )[0]
    assert not evaluate_dual(
        case,
        {
            "id": "loop",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "SELF_LOOP", "edge": ["0", "0"]},
        },
    )[0]
    assert not evaluate_dual(
        case, {"id": "loop", "status": "OUT_OF_SCOPE", "witness": {"reason": "INVALID_SIGN"}}
    )[0]


def _greedy_identity_responder(case: dict) -> dict:
    """Identity switching plus a greedy maximal packing: cheap, and far from tight."""
    from c018_signed_graph_frustration_index.reference_solver.graph_blocks import (
        find_negative_cycle_packing,
        parse_graph,
    )

    vertices, edges, _ = parse_graph(case)
    packing = find_negative_cycle_packing(vertices, edges)
    negatives = sum(1 for _, _, s in edges if s == -1)
    return {
        "id": case["id"],
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": str(negatives),
        "lower": str(len(packing)),
        "switching": {},
        "lower_bound": {"kind": "packing", "cycles": packing},
    }


def test_identity_switching_with_greedy_packing_fails_on_every_large_case() -> None:
    """Counterexample (review of e6fbc15cf): upper = the identity switching's count
    (47-80 against the reference's 26-44) passed both checkers on all 8 base_unknown cases."""
    large = [p for p in JUDGE_CASES if p.name.startswith("base_unknown_")]
    assert len(large) == 8
    passes = [
        p.name for p in large if evaluate_dual(_load(p), _greedy_identity_responder(_load(p)))[0]
    ]
    assert passes == []


@pytest.mark.parametrize("checker", ["frustration", "independent"])
def test_each_checker_requires_a_locally_optimal_switching(checker: str) -> None:
    from c018_signed_graph_frustration_index.judge_packet.checkers.frustration_checker import (
        check_frustration_certificate,
    )
    from c018_signed_graph_frustration_index.judge_packet.checkers.independent_checker import (
        check_independent_frustration,
    )

    check = (
        check_frustration_certificate if checker == "frustration" else check_independent_frustration
    )
    for path in JUDGE_CASES:
        if not path.name.startswith("base_unknown_"):
            continue
        case = _load(path)
        reference, _ = solve(case)
        assert check(case, reference)[0] is True, path.name
        assert check(case, _greedy_identity_responder(case))[0] is False, path.name
