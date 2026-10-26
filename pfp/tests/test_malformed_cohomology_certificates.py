"""Regressions for malformed witnesses observed in the bounded C013/C016 run."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from omega_engine_pfp.tests.demo_004.b_cohomology.c013_integral_homology_torsion.judge_packet.checkers import (
    snf_algebraic_checker,
)
from omega_engine_pfp.tests.demo_004.b_cohomology.c013_integral_homology_torsion.judge_packet.checkers.dual_evaluator import (
    evaluate_dual as evaluate_snf,
)
from omega_engine_pfp.tests.demo_004.b_cohomology.c013_integral_homology_torsion.reference_solver.solver import (
    solve as solve_snf,
)
from omega_engine_pfp.tests.demo_004.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers import (
    algebraic_cup_checker,
)
from omega_engine_pfp.tests.demo_004.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.dual_evaluator import (
    evaluate_dual as evaluate_cup,
)
from omega_engine_pfp.tests.demo_004.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
    solve as solve_cup,
)


@pytest.mark.parametrize("parent,missing", [
    ([[42]], []),  # Actual retained C013 model witness.
    ([42, {}], [42]),
    ([42, "c_1"], [42]),
    ([42, "²"], [42]),
    ([42, 43], [[42]]),
    ([42, 43], [True]),
    ([42, 43], [42.5]),
])
def test_snf_dual_rejects_malformed_face_witness_without_crashing(parent, missing):
    case = {"id": "case_base_01", "simplices": [[42]]}
    candidate = {
        "id": case["id"], "status": "OUT_OF_SCOPE",
        "witness": {"of_simplex": parent, "missing_face": missing},
    }
    original = deepcopy((case, candidate))

    checked = evaluate_snf(case, candidate)

    assert checked["verdict"] == "FAIL"
    assert checked["agreement"]
    assert not checked["checker1"]["valid"]
    assert not checked["checker2"]["valid"]
    assert (case, candidate) == original


@pytest.mark.parametrize("string_vertices", [False, True])
def test_snf_dual_keeps_valid_missing_face_witness(string_vertices):
    case = {"id": "missing_face", "simplices": [[42, 43], [42]]}
    witness = {"of_simplex": [42, 43], "missing_face": [43]}
    if string_vertices:
        witness = {key: list(map(str, value)) for key, value in witness.items()}
    checked = evaluate_snf(case, {"status": "OUT_OF_SCOPE", "witness": witness})
    assert checked["verdict"] == "PASS", checked


def test_snf_original_single_point_certificate_still_passes():
    root = Path(snf_algebraic_checker.__file__).parents[1] / "cases/base"
    case = json.loads((root / "case_base_01.json").read_bytes())
    checked = evaluate_snf(case, solve_snf(case))
    assert checked["verdict"] == "PASS", checked


@pytest.fixture(scope="module")
def cup_source_certificate():
    root = Path(algebraic_cup_checker.__file__).parents[1] / "cases/base"
    case = json.loads((root / "base_01.json").read_bytes())
    certificate, _ = solve_cup(case)
    return case, certificate


def test_cup_rejects_actual_symbolic_model_coefficients(cup_source_certificate):
    case, _ = cup_source_certificate
    candidate = {
        "id": case["id"], "status": "SOLVED", "verdict": "DISTINGUISHED",
        "X": {
            "rank": "2", "basis_p": [{"[0, 1]": "c_1"}],
            "basis_q": [{"[0, 1]": "c_2"}],
            "nonzero": [
                {"i": "1", "j": "1", "cycle": {"[0, 1, 2]": "c_3"}, "value": "1"},
                {"i": "1", "j": "2", "cycle": {"[0, 1, 2]": "c_4"}, "value": "1"},
            ], "primitives": [],
        },
        "Y": {
            "rank": "1", "basis_p": [{"[0, 1]": "d_1"}],
            "basis_q": [{"[0, 1]": "d_2"}], "nonzero": [], "primitives": [],
        },
    }
    original = deepcopy(candidate)
    accepted, reason, details = evaluate_cup(case, candidate)
    assert not accepted
    assert not details["algebraic_checker"]["passed"]
    assert "malformed" in reason.lower()
    assert candidate == original


@pytest.mark.parametrize("location", ["basis_p", "basis_q", "cycle", "gamma"])
@pytest.mark.parametrize("coefficient", ["c_1", "1/0"])
def test_cup_rejects_bad_coefficients_at_each_chain_boundary(
    cup_source_certificate, location, coefficient,
):
    case, source = cup_source_certificate
    candidate = deepcopy(source)
    side = candidate["X"]
    if location in ("basis_p", "basis_q"):
        chain = side[location][0]
    elif location == "cycle":
        chain = side["nonzero"][0]["cycle"]
    else:
        side["primitives"] = [{"i": "0", "j": "0", "gamma": {"[0, 1]": "1"}}]
        chain = side["primitives"][0]["gamma"]
    chain[next(iter(chain))] = coefficient

    accepted, reason = algebraic_cup_checker.check_algebraic_cup_certificate(case, candidate)
    assert not accepted
    assert "malformed" in reason.lower()


@pytest.mark.parametrize("bad_chain", [None, [], {7: "1"}, {"[0, nope]": "1"}])
def test_cup_rejects_malformed_chain_shape(cup_source_certificate, bad_chain):
    case, source = cup_source_certificate
    candidate = deepcopy(source)
    candidate["X"]["basis_p"] = [bad_chain]
    accepted, reason = algebraic_cup_checker.check_algebraic_cup_certificate(case, candidate)
    assert not accepted
    assert "malformed" in reason.lower()


@pytest.mark.parametrize("bad_index", ["999", "-1", "c_1"])
def test_cup_rejects_malformed_witness_basis_index(cup_source_certificate, bad_index):
    case, source = cup_source_certificate
    candidate = deepcopy(source)
    candidate["X"]["nonzero"][0]["i"] = bad_index
    accepted, _ = algebraic_cup_checker.check_algebraic_cup_certificate(case, candidate)
    assert not accepted


def test_cup_original_certificate_passes_both_independent_judges(cup_source_certificate):
    case, candidate = cup_source_certificate
    accepted, reason, _ = evaluate_cup(case, candidate)
    assert accepted, reason


def test_cup_math_defects_are_not_reported_as_bad_model_input(
    cup_source_certificate, monkeypatch,
):
    case, candidate = cup_source_certificate

    def broken_product(*args):
        raise ValueError("internal product regression")

    monkeypatch.setattr(algebraic_cup_checker, "alexander_whitney_product", broken_product)
    with pytest.raises(ValueError, match="internal product regression"):
        algebraic_cup_checker.check_algebraic_cup_certificate(case, candidate)
