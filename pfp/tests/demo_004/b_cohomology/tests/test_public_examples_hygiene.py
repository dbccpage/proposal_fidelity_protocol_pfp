"""Public b_cohomology examples keep expected answers out of the input object.

Before the 2026-09-29 correction every example carried `expected_status`, and
four carried `expected_phi1`, inside the object that the runner hands to a solver
or a model. The expected values now live in examples/expected/<id>.json.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

THEME = (
    Path(
        importlib.import_module(
            "omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.runner"
        ).__file__
    )
    .resolve()
    .parent
)
EXAMPLES = sorted((THEME / "examples").glob("*.json"))


def test_examples_are_present() -> None:
    assert len(EXAMPLES) == 24


def test_no_example_input_carries_an_expected_answer() -> None:
    leaks = [
        (p.name, key)
        for p in EXAMPLES
        for key in json.loads(p.read_text(encoding="utf-8"))
        if key.startswith("expected")
    ]
    assert leaks == []


def test_expected_answers_are_kept_beside_the_inputs() -> None:
    for p in EXAMPLES:
        record = json.loads((THEME / "examples" / "expected" / p.name).read_text(encoding="utf-8"))
        assert record["id"] == json.loads(p.read_text(encoding="utf-8"))["id"]
        assert record["status"] in ("SOLVED", "OUT_OF_SCOPE")
