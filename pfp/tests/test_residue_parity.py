"""Both sides of the seam agree what `mod` means. This is the Python side.

The hazard, restated because it is easy to under-rate: `mod` here is the least
non-negative residue, so `-17 mod 5 = 3`. Rust, C, C++, Java and Go compute
`-2` -- the sign follows the dividend, not the divisor. A Rust re-derivation of
a row Python already re-derived would therefore disagree, and the disagreement
would surface as a **CONTRADICTED row**: the producer blamed for a difference
between two hosts.

The vectors live in governance, not here, and neither side transcribes them.
The Rust integration test reads the same file, so the two independently
implemented hosts are pinned to one shared seam convention.

Why the wrong answers are in the file too
-----------------------------------------

Each case carries `truncated_remainder` as well, and the tests below assert the
decider **contradicts** it. A test that only checks the correct value passes on
a host that has never been asked the question -- and this whole file exists
because a plausible implementation returns the other number.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_engine_pfp.domain.calculus_receipt import RowOutcome
from omega_engine_pfp.domain.row_rederivation import rederive_statement

VECTORS_PATH = (
    Path(__file__).resolve().parents[2]
    / "omega_engine_governance"
    / "contracts"
    / "pinned"
    / "modular_residue_vectors.json"
)

_BODY = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
CASES = _BODY["cases"]
DISAGREEING = [case for case in CASES if not case["conventions_agree"]]


def _label(case: dict) -> str:
    return f"{case['lhs']}mod{case['modulus']}"


def test_the_vectors_file_is_the_one_this_estate_pins() -> None:
    assert _BODY["schema"] == "omega.modular_residue_vectors.v1"
    assert _BODY["authority_effect"] == "None"


def test_the_vector_set_contains_cases_that_actually_discriminate() -> None:
    """Guards the fixture.

    If every case were one the two conventions agree about, the whole file
    would pass on a host using the wrong `%` and would establish nothing.
    """
    assert DISAGREEING, "no case distinguishes the two conventions"
    assert len(DISAGREEING) >= 5, f"only {len(DISAGREEING)} discriminating cases"


def test_the_vector_set_also_contains_agreeing_cases() -> None:
    # The other half: a file of only disagreements would pass a host that
    # handled negatives correctly and returned garbage for positives.
    assert [case for case in CASES if case["conventions_agree"]]


@pytest.mark.parametrize("case", CASES, ids=_label)
def test_the_decider_computes_the_least_non_negative_residue(case: dict) -> None:
    statement = (
        f"REDUCE {case['lhs']} mod {case['modulus']} "
        f"= {case['least_non_negative_residue']}"
    )
    derivation = rederive_statement(statement)
    assert derivation.outcome is RowOutcome.REDERIVED, (
        f"{statement!r} should re-derive; host said {derivation.host_value}"
    )
    assert derivation.host_value == case["least_non_negative_residue"]


@pytest.mark.parametrize("case", DISAGREEING, ids=_label)
def test_the_truncating_answer_is_contradicted(case: dict) -> None:
    """The assertion that would fail on a Rust-style `%`.

    Without this, the suite passes on a host returning `-2` for `-17 mod 5`
    provided nobody ever asks it that question.
    """
    statement = (
        f"REDUCE {case['lhs']} mod {case['modulus']} "
        f"= {case['truncated_remainder']}"
    )
    derivation = rederive_statement(statement)
    assert derivation.outcome is RowOutcome.CONTRADICTED, (
        f"{statement!r} is the C-family answer and must be contradicted"
    )
    assert derivation.host_value == case["least_non_negative_residue"]


@pytest.mark.parametrize("case", CASES, ids=_label)
def test_every_residue_is_in_range(case: dict) -> None:
    residue = int(case["least_non_negative_residue"])
    assert 0 <= residue < int(case["modulus"])
