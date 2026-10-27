"""C046: a submitted completion must follow from the input equations.

Counterexamples named by these tests (reported by review; all passed the dual evaluator):
- central_projector with {p(x) -> x, q(x) -> 0};
- absorb_ring_zero with {times(x, y) -> 0};
- nilpotent_order_2 with {sq(x) -> 0, mul(x, y) -> 0};
- centralizer_idempotent with {c(x) -> d(x), d(x) -> x}.
Each set is LPO-decreasing, locally confluent and joins the input equations, but proves
equations the input does not imply. Both checkers now require every submitted rule to be an
equational consequence of the input (checker 2 by its own completion).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c046_knuth_bendix_completion.judge_packet.checkers import (
    independent_checker,
)
from c046_knuth_bendix_completion.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from c046_knuth_bendix_completion.judge_packet.checkers.exact_checker import (
    check_exact,
)
from c046_knuth_bendix_completion.judge_packet.checkers.independent_checker import (
    check_independent,
)
from c046_knuth_bendix_completion.reference_solver.solver import (
    solve,
)

PKG = Path(__file__).resolve().parent.parent
HIDDEN = {
    c["case_id"]: c
    for c in json.loads(
        (PKG / "judge_packet" / "hidden_cases" / "c046_hidden_cases_64.json").read_text(
            encoding="utf-8"
        )
    )
}

UNSOUND = {
    "c046_base_complete_05_central_projector": [["p(x)", "x"], ["q(x)", "0"]],
    "c046_base_complete_10_absorb_ring_zero": [["times(x, y)", "0"]],
    "c046_base_complete_04_nilpotent_order_2": [["sq(x)", "0"], ["mul(x, y)", "0"]],
    "c046_base_complete_09_centralizer_idempotent": [["c(x)", "d(x)"], ["d(x)", "x"]],
}


def _answer(case_id: str, rules: list[list[str]]) -> dict:
    return {
        "case_id": case_id,
        "status": "SOLVED",
        "task": "COMPLETE",
        "converged": True,
        "rules_count": len(rules),
        "rules": [{"lhs": a, "rhs": b} for a, b in rules],
        "joinability_certificates_count": 0,
    }


@pytest.mark.parametrize("case_id", sorted(UNSOUND))
def test_unsound_completion_is_rejected_by_both_checkers(case_id: str) -> None:
    case = HIDDEN[case_id]
    ans = _answer(case_id, UNSOUND[case_id])
    ok1, msg1 = check_exact(case, ans)
    ok2, msg2 = check_independent(case, ans)
    assert ok1 is False, msg1
    assert ok2 is False, msg2
    assert "consequence" in msg1 and "consequence" in msg2
    assert evaluate_dual(case, ans)[0] is False


@pytest.mark.parametrize("case_id", sorted(UNSOUND))
def test_reference_completion_still_passes(case_id: str) -> None:
    case = HIDDEN[case_id]
    ok, msg, _receipt = evaluate_dual(case, solve(case))
    assert ok is True, msg


def test_independent_completion_of_group_axioms_has_ten_rules() -> None:
    parse = independent_checker.parse
    equations = [
        (parse("mul(e, x)"), parse("x")),
        (parse("mul(inv(x), x)"), parse("e")),
        (parse("mul(mul(x, y), z)"), parse("mul(x, mul(y, z))")),
    ]
    rules = independent_checker.complete_equations(equations, {"inv": 100, "mul": 50, "e": 10})
    assert rules is not None and len(rules) == 10


def test_independent_completion_refuses_unorientable_input() -> None:
    parse = independent_checker.parse
    unorientable = [(parse("mul(x, y)"), parse("mul(y, x)"))]
    assert independent_checker.complete_equations(unorientable, {"mul": 50}) is None


def test_checker_one_soundness_uses_its_own_completion() -> None:
    """Checker 1 must not reach the reference completion or checker 2 (import boundary)."""
    import inspect

    from c046_knuth_bendix_completion.judge_packet.checkers import (
        exact_checker,
        judge_completion,
    )

    exact_source = inspect.getsource(exact_checker)
    assert "reference_solver.completion" not in exact_source
    assert "independent_checker" not in exact_source
    own_source = inspect.getsource(judge_completion)
    assert "reference_solver" not in own_source
    assert "independent_checker" not in own_source


@pytest.mark.parametrize("case_id", sorted(UNSOUND))
def test_judge_completion_decides_the_four_unsound_sets(case_id: str) -> None:
    from c046_knuth_bendix_completion.judge_packet.checkers.judge_completion import (
        follows_from,
    )

    case = HIDDEN[case_id]
    equations = [(a, b) for a, b in case["equations"]]
    sound, detail = follows_from(
        equations, case.get("precedence"), [tuple(r) for r in UNSOUND[case_id]]
    )
    assert sound is False, detail
    reference_rules = [(r["lhs"], r["rhs"]) for r in solve(case)["rules"]]
    assert follows_from(equations, case.get("precedence"), reference_rules)[0] is True
