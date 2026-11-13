"""
Runs the offline worksheet printed in the guide (paper.md, Section 3) and checks
the Section 2 argument it illustrates. Pure exact arithmetic; no native calculator.
"""

import re
from fractions import Fraction
from pathlib import Path

PAPER = Path(__file__).resolve().parents[2] / "paper.md"
WEIGHTS = (Fraction(1), Fraction(2), Fraction(3))


def _worksheet_source() -> str:
    blocks = re.findall(r"```python\n(.*?)```", PAPER.read_text(encoding="utf-8"), flags=re.S)
    matching = [block for block in blocks if "edge_differences" in block]
    assert len(matching) == 1, f"expected one worksheet block in {PAPER.name}, found {len(matching)}"
    return matching[0]


def _weighted_discrepancy(claims, potential) -> Fraction:
    a, b, c = potential
    differences = (b - a, c - b, a - c)
    return sum((w * abs(x - d) for w, x, d in zip(WEIGHTS, claims, differences)), Fraction(0))


def test_printed_worksheet_runs_and_matches_section_2():
    namespace: dict = {}
    exec(compile(_worksheet_source(), f"{PAPER.name}:worksheet", "exec"), namespace)
    q = Fraction
    if namespace["edge_differences"] != (q(-2), q(1), q(1)):
        raise AssertionError("edge differences differ from Section 2")
    if namespace["residual"] != (q(3), q(0), q(0)):
        raise AssertionError("residual differs from Section 2")


def test_lower_bound_is_attained_and_replacement_is_consistent():
    claims = (Fraction(1), Fraction(1), Fraction(1))
    potential = (Fraction(0), Fraction(-2), Fraction(-1))
    # Section 2: D_c(f) >= min(w) * |sum(c)| = 3, attained at f = (0, -2, -1).
    assert min(WEIGHTS) * abs(sum(claims)) == 3
    assert _weighted_discrepancy(claims, potential) == 3
    # The all-zero potential scores 6 with weights (1,2,3): a score, not the minimum.
    assert _weighted_discrepancy(claims, (Fraction(0),) * 3) == 6
    # Replacing the claims by (-2, 1, 1) gives a consistent instance.
    replacement = (Fraction(-2), Fraction(1), Fraction(1))
    assert sum(replacement) == 0
    assert _weighted_discrepancy(replacement, potential) == 0
