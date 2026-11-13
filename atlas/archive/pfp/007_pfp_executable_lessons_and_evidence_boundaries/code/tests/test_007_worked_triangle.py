"""Checks for the worked triangle lesson in Section 3 of Companion 007.

The first tests use Python fractions only. The notebook test reads the stored
companion notebook as JSON and does not execute it. The last test runs the
Section 3 code blocks exactly as printed against the repository's cochain
implementation; it needs the full repository checkout and is skipped, with that
reason, when the implementation is absent.
"""

from __future__ import annotations

import ast
import json
import re
from fractions import Fraction as Q
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2]
PAPER = PACKAGE / "paper.md"
NOTEBOOK = PACKAGE / "jupyter_notebooks" / "007_moving_a_discrepancy.ipynb"
COCHAINS = Path("pfp", "domain", "ddc", "cochains.py")

EDGES = (("a", "b"), ("b", "c"), ("c", "a"))
CLAIMS = {edge: Q(1, 3) for edge in EDGES}
HEIGHTS = {"a": Q(0), "b": Q(1, 3), "c": Q(2, 3)}


def d0(heights: dict[str, Q]) -> dict[tuple[str, str], Q]:
    """Difference on each directed edge: target height minus source height."""
    return {(s, t): heights[t] - heights[s] for (s, t) in EDGES}


def cycle_sum(values: dict[tuple[str, str], Q]) -> Q:
    return sum((values[edge] for edge in EDGES), Q(0))


def test_potential_adjustment_moves_the_residual() -> None:
    df = d0(HEIGHTS)
    residual = {edge: CLAIMS[edge] - df[edge] for edge in EDGES}
    assert [df[edge] for edge in EDGES] == [Q(1, 3), Q(1, 3), Q(-2, 3)]
    assert [residual[edge] for edge in EDGES] == [Q(0), Q(0), Q(1)]
    assert cycle_sum(CLAIMS) == cycle_sum(residual) == 1
    assert cycle_sum(df) == 0


def test_constant_shift_leaves_differences_unchanged() -> None:
    shifted = {vertex: height + Q(7, 5) for vertex, height in HEIGHTS.items()}
    assert d0(shifted) == d0(HEIGHTS)


def test_negated_claims_have_residual_sum_minus_one() -> None:
    df = d0(HEIGHTS)
    assert cycle_sum({edge: -CLAIMS[edge] - df[edge] for edge in EDGES}) == -1


def test_missing_third_claim_is_minus_two_thirds() -> None:
    third = -(CLAIMS[("a", "b")] + CLAIMS[("b", "c")])
    assert third == Q(-2, 3)
    assert cycle_sum({**CLAIMS, ("c", "a"): third}) == 0


def test_differences_cancel_around_the_cycle_for_other_heights() -> None:
    for heights in (
        {"a": Q(0), "b": Q(0), "c": Q(0)},
        {"a": Q(5), "b": Q(-2, 7), "c": Q(3, 11)},
        {"a": Q(-1, 2), "b": Q(9, 4), "c": Q(-13, 6)},
    ):
        assert cycle_sum(d0(heights)) == 0


def test_companion_notebook_stores_the_section3_values() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert [cell["execution_count"] for cell in code] == [1, 2, 3, 4, 5, 6]
    stdout = "".join(
        "".join(output["text"])
        for cell in code
        for output in cell["outputs"]
        if output.get("output_type") == "stream" and output.get("name") == "stdout"
    )
    for expected in (
        "claims h = (1/3, 1/3, 1/3); cycle sum = 1",
        "df = (1/3, 1/3, -2/3); cycle sum = 0",
        "h - df = (0, 0, 1); cycle sum = 1",
        "d0(shifted) = (1/3, 1/3, -2/3)",
        "-h - df = (-2/3, -2/3, 1/3); cycle sum = -1",
        "third claim = -2/3",
        "wrong-sign df = (-1/3, -1/3, 2/3); residual = (2/3, 2/3, -1/3)",
        "weak cycle-sum check passes; predicted-coordinate check rejects",
    ):
        assert expected in stdout
    imported = set()
    for cell in code:
        for node in ast.walk(ast.parse("".join(cell["source"]))):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
    assert imported == {"fractions"}


def _repository_root() -> Path | None:
    return next((p for p in PACKAGE.parents if (p / COCHAINS).is_file()), None)


REPOSITORY = _repository_root()


@pytest.mark.skipif(
    REPOSITORY is None,
    reason=(
        "needs the full repository checkout: "
        + COCHAINS.as_posix()
        + " was not found four levels above this package"
    ),
)
def test_section3_code_blocks_run_as_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    assert REPOSITORY is not None
    text = PAPER.read_text(encoding="utf-8")
    section = text.split("\n## 3.", 1)[1].split("\n## 4.", 1)[0]
    blocks = re.findall(r"```python\n(.*?)```", section, flags=re.S)
    assert len(blocks) == 3
    monkeypatch.syspath_prepend(str(REPOSITORY))
    namespace: dict[str, object] = {"__name__": "companion_007_section_3"}
    for index, block in enumerate(blocks, 1):
        exec(compile(block, f"paper.md#section-3-block-{index}", "exec"), namespace)
    assert namespace["residual"].values[("c", "a")] == 1
