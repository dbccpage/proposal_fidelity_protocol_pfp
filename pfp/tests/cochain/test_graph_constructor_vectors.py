"""Finite constructor vectors shared with the actual Rust typed constructor.

Rust's fixture decoder rejects values not representable by usize/BigRational;
those rows must not be reported as production Rust constructor refusals.
"""

import json
from fractions import Fraction
from pathlib import Path

import pytest

from omega_engine_pfp.domain.cochain import PromptCellComplex

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "omega_engine/crates_rs/tests/omega_symbol_game_runtime/fixtures/cochain_constructor_vectors.json").read_text(encoding="utf-8"))


def _coefficient(value):
    # Decode only explicit exact fixture values. Malformed primitives reach the
    # real Python constructor unchanged, rather than being refused by this helper.
    return Fraction(*value["rational"]) if isinstance(value, dict) else value


def _expected(matrix):
    return tuple(tuple(Fraction(value) for value in row) for row in matrix)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_shared_constructor_vector(case):
    faces = case["faces"]
    if faces is not None:
        faces = [[(index, _coefficient(coefficient)) for index, coefficient in face] for face in faces]
    if case["python"] == "refused":
        with pytest.raises(ValueError):
            PromptCellComplex.from_oriented_graph(case["vertices"], case["edges"], faces)
        return
    result = PromptCellComplex.from_oriented_graph(case["vertices"], case["edges"], faces)
    assert result.d0_matrix == _expected(case["d0"])
    assert result.d1_matrix == _expected(case["d1"])
    assert (result.v_count, result.e_count, result.f_count) == (
        len(case["vertices"]), len(case["edges"]), len(faces or ()),
    )
