"""Finite counterexamples and executable worksheet for Companion 007."""

from __future__ import annotations

import re
from fractions import Fraction as Q
from pathlib import Path

from test_007_pedagogical_transmission import evaluate_headless_notebook_grade

PACKAGE = Path(__file__).resolve().parents[2]


def test_wrong_sign_passes_sum_checks_but_fails_coordinate_prediction() -> None:
    edges = (("a", "b"), ("b", "c"), ("c", "a"))
    heights = {"a": Q(0), "b": Q(1, 3), "c": Q(2, 3)}
    wrong = tuple(heights[s] - heights[t] for s, t in edges)
    residual = tuple(Q(1, 3) - delta for delta in wrong)
    assert sum(wrong, Q(0)) == 0
    assert sum(residual, Q(0)) == 1
    assert wrong != (Q(1, 3), Q(1, 3), Q(-2, 3))
    assert residual == (Q(2, 3), Q(2, 3), Q(-1, 3))


def test_legacy_status_grade_counts_non_assertions_without_execution() -> None:
    cells = [
        {"cell_type": "code", "source": "# assert example", "execution_status": "ok"},
        {"cell_type": "code", "source": 'print("assert")', "execution_status": "ok"},
        {"cell_type": "code", "source": "assert False", "execution_status": "error"},
    ]
    assert evaluate_headless_notebook_grade(cells) == Q(2, 3)


def test_study_guide_worksheet_runs_exactly_as_printed() -> None:
    text = (PACKAGE / "_lev_landau_theoretical_minimum_quiz/study_guide.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.S)
    assert len(blocks) == 1
    exec(compile(blocks[0], "study_guide.md#exact-worksheet", "exec"), {})


def test_unfamiliar_four_cycle_has_declared_residual() -> None:
    edges = (("p", "q"), ("q", "r"), ("r", "s"), ("s", "p"))
    h = (Q(1, 2), Q(-1, 3), Q(3, 4), Q(1, 6))
    f = {"p": Q(0), "q": Q(1, 2), "r": Q(1, 6), "s": Q(11, 12)}
    df = tuple(f[t] - f[s] for s, t in edges)
    residual = tuple(claim - delta for claim, delta in zip(h, df))
    assert df == (Q(1, 2), Q(-1, 3), Q(3, 4), Q(-11, 12))
    assert residual == (Q(0), Q(0), Q(0), Q(13, 12))
    assert sum(h, Q(0)) == sum(residual, Q(0)) == Q(13, 12)
    assert (*h[:3], -sum(h[:3], Q(0))) == df
