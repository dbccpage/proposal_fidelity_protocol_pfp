"""C051 corrections: the participant runner's refusal escape and a checker crash.

Counterexamples from the 2026-09-28 audit:

- ``participant_packet/runner.py`` accepted any OUT_OF_SCOPE reply, so a solver
  that refused everything scored 14/14 on the public examples;
- the independent checker raised TypeError on a case with a non-numeric entry.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from c051_exact_lp_solver_with_duals.judge_packet import (
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
JUDGE_DIR = PACKAGE_DIR / "judge_packet"
EXAMPLES = sorted((PACKAGE_DIR / "participant_packet" / "examples").glob("*.json"))
CASES = [
    json.loads(p.read_text(encoding="utf-8")) for p in sorted((JUDGE_DIR / "cases").glob("*.json"))
]
CHECKERS = (
    ("exact", exact_checker.check_solution),
    ("independent", independent_checker.check_solution),
)


def _participant_runner():
    name = "c051_participant_runner_under_test"
    spec = importlib.util.spec_from_file_location(
        name, PACKAGE_DIR / "participant_packet" / "runner.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _refuse_all(case):
    return {
        "case_id": case.get("case_id"),
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "REFUSED"},
    }


def test_always_out_of_scope_solver_scores_only_the_malformed_examples():
    runner = _participant_runner()
    assert len(EXAMPLES) == 14
    assert runner.score(_refuse_all, EXAMPLES) == 2


def test_empty_and_unknown_solvers_score_zero():
    runner = _participant_runner()
    assert runner.score(lambda case: {}, EXAMPLES) == 0
    assert (
        runner.score(lambda case: {"case_id": case.get("case_id"), "status": "UNKNOWN"}, EXAMPLES)
        == 0
    )
    assert runner.score(lambda case: [], EXAMPLES) == 0


def test_reference_solver_scores_all_examples():
    from c051_exact_lp_solver_with_duals.reference_solver import (
        solve,
    )

    assert _participant_runner().score(solve, EXAMPLES) == 14


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("entry", ["abc", 1.5, True, None, "1/0", [1]])
def test_non_numeric_case_entry_is_out_of_scope_not_a_crash(name, checker, entry):
    case = {"case_id": "bad", "A": [["1", entry]], "b": ["1"], "c": ["1", "1"]}
    solved = {
        "case_id": "bad",
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "x": ["0", "0"],
        "y": ["1"],
        "value": "0",
    }
    ok, msg = checker(case, solved)
    assert ok is False and isinstance(msg, str), (name, msg)
    assert (
        checker(
            case, {"case_id": "bad", "status": "OUT_OF_SCOPE", "witness": {"reason": "BAD_ENTRY"}}
        )[0]
        is True
    )


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("value", [" 2", "2 ", "+2", "02", "2/1", "4/2", "-0", "2.0", 2])
def test_non_canonical_answer_strings_are_rejected(name, checker, value):
    case = {"case_id": "t", "A": [["1"]], "b": ["2"], "c": ["1"]}
    good = {
        "case_id": "t",
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "x": ["2"],
        "y": ["1"],
        "value": "2",
    }
    assert checker(case, good)[0] is True
    assert checker(case, {**good, "value": value})[0] is False, (name, value)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_refuse_all_responder_fails_on_every_in_scope_judge_case(name, checker):
    in_scope = [c for c in CASES if not exact_checker.is_malformed_case(c)[0]]
    assert len(in_scope) == len(CASES) == 64
    for case in in_scope:
        assert checker(case, _refuse_all(case))[0] is False, (name, case["case_id"])
        assert checker(case, {})[0] is False


def test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers():
    from c051_exact_lp_solver_with_duals.reference_solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, case["case_id"])
    for path in sorted((JUDGE_DIR / "hostile_mutations").glob("*.json")):
        mutation = json.loads(path.read_text(encoding="utf-8"))
        for name, checker in CHECKERS:
            assert checker(mutation["case"], mutation["corrupted_result"])[0] is False, (
                name,
                path.name,
            )
