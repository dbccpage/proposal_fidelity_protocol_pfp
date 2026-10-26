"""Adversarial certificates cannot turn missing mathematical evidence into PASS."""

import pytest

from omega_engine_pfp.domain.cohomology.certificate_checker import check_certificate
from omega_engine_pfp.domain.cohomology.validation import parse_c011_case, scope_violation


def triangle():
    return {
        "case_id": "cycle", "challenge": "c011", "nodes": ["a", "b", "c"],
        "edges": [["a", "b"], ["b", "c"], ["c", "a"]],
        "claims": {"a->b": "1", "b->c": "1", "c->a": "1"},
        "weights": {"a->b": "1", "b->c": "1", "c->a": "1"},
    }


def triangle_certificate():
    return {
        "status": "SOLVED", "phi1": "3",
        "potential": {"a": "0", "b": "0", "c": "0"},
        "repair": {"a->b": "1", "b->c": "1", "c->a": "1"},
        "dual": {"a->b": "1", "b->c": "1", "c->a": "1"},
    }


def sheaf():
    return {
        "challenge": "c012", "vertices": ["v0", "v1"],
        "edges": [["e0", "v0", "v1"]],
        "stalk_dims_v": {"v0": 1, "v1": 1}, "stalk_dims_e": {"e0": 1},
        "restrictions": {"v0<=e0": [["1"]], "v1<=e0": [["1"]]},
        "targets": [["0"]],
    }


def test_exact_c011_primal_dual_certificate_passes():
    assert check_certificate(triangle(), triangle_certificate()).passed


def test_sparse_zero_repair_and_dual_remain_supported():
    case = {"challenge": "c011", "nodes": ["a", "b"], "edges": [["a", "b"]], "claims": {"a->b": "1/2"}}
    answer = {"status": "SOLVED", "phi1": "0", "potential": {"a": "0", "b": "1/2"}}
    assert check_certificate(case, answer).passed


@pytest.mark.parametrize("field,key,value", [
    ("potential", "b", "1"), ("repair", "a->b", "0"),
    ("dual", "a->b", "2"), ("dual", "a->b", "0"),
    ("repair", "invented", "0"), ("potential", "a", 0.0),
    ("dual", "a->b", True), ("repair", "a->b", "1.0"),
])
def test_tampered_c011_witnesses_fail(field, key, value):
    answer = triangle_certificate()
    answer[field][key] = value
    assert not check_certificate(triangle(), answer).passed


@pytest.mark.parametrize("value", ["0", 3.0, True, "3/1", None])
def test_invalid_reported_optimum_fails(value):
    answer = triangle_certificate()
    answer["phi1"] = value
    assert not check_certificate(triangle(), answer).passed


def test_missing_potential_coordinate_fails():
    answer = triangle_certificate()
    del answer["potential"]["c"]
    assert not check_certificate(triangle(), answer).passed


@pytest.mark.parametrize("challenge", [f"c{n:03d}" for n in range(12, 21)])
def test_unavailable_independent_checker_never_certifies_solved(challenge):
    answer = {"status": "SOLVED", "h0_dim": 0, "h0_basis": [], "homology": [{"n": 0, "betti": 999}], "flat": True, "verdict": "EXTENDS"}
    result = check_certificate({"challenge": challenge}, answer)
    assert not result.passed
    assert "unavailable" in result.error


@pytest.mark.parametrize("refusal", ["BUDGET_EXHAUSTED", "CARRIER_LIMIT_EXCEEDED", "NATIVE_OPERATION_UNAVAILABLE"])
def test_unknown_is_not_verified_success(refusal):
    assert not check_certificate(triangle(), {"status": "UNKNOWN", "refusal": refusal}).passed


@pytest.mark.parametrize("witness", [None, [], {}, {"edge": "a->b", "reason": "SELF_LOOP"}])
def test_refusal_of_valid_case_fails(witness):
    assert not check_certificate(triangle(), {"status": "OUT_OF_SCOPE", "witness": witness}).passed


@pytest.mark.parametrize("defect", ["SELF_LOOP", "NONPOSITIVE_WEIGHT", "UNKNOWN_ENDPOINT"])
def test_c011_scope_refusal_requires_actual_edge(defect):
    case = triangle()
    if defect == "SELF_LOOP":
        case["edges"][0] = ["a", "a"]
        case["claims"]["a->a"] = case["claims"].pop("a->b")
        case["weights"]["a->a"] = case["weights"].pop("a->b")
    elif defect == "NONPOSITIVE_WEIGHT":
        case["weights"]["a->b"] = "0"
    else:
        case["nodes"].remove("b")
    witness = scope_violation(case)
    assert witness["reason"] == defect
    assert check_certificate(case, {"status": "OUT_OF_SCOPE", "witness": witness}).passed
    assert not check_certificate(case, {"status": "OUT_OF_SCOPE", "witness": {**witness, "edge": "invented"}}).passed
    assert not check_certificate(case, triangle_certificate()).passed


def test_parallel_edges_refused_before_coordinates_can_collapse():
    case = triangle()
    case["edges"].append(["a", "b"])
    with pytest.raises(ValueError, match="Parallel"):
        parse_c011_case(case)
    assert not check_certificate(case, triangle_certificate()).passed


@pytest.mark.parametrize("value", [1.0, True, "1.0", "1/0"])
def test_inexact_or_malformed_input_not_certified(value):
    case = triangle()
    case["claims"]["a->b"] = value
    assert not check_certificate(case, triangle_certificate()).passed


@pytest.mark.parametrize("defect", ["MISSING_RESTRICTION_MAP", "RESTRICTION_SHAPE_MISMATCH"])
def test_c012_scope_checks_actual_restrictions(defect):
    case = sheaf()
    assert scope_violation(case) is None
    forged = {"status": "OUT_OF_SCOPE", "witness": {"edge": "e0", "reason": defect}}
    assert not check_certificate(case, forged).passed
    if defect == "MISSING_RESTRICTION_MAP":
        del case["restrictions"]["v1<=e0"]
    else:
        case["stalk_dims_v"]["v1"] = 2
    assert scope_violation(case) == forged["witness"]
    assert check_certificate(case, forged).passed


def test_c012_later_matrix_rows_cannot_hide_shape_mismatch():
    case = sheaf()
    case["stalk_dims_e"]["e0"] = 2
    case["restrictions"] = {"v0<=e0": [["1"], ["1"]], "v1<=e0": [["1"], ["1", "0"]]}
    case["targets"] = []
    assert scope_violation(case) == {"edge": "e0", "reason": "RESTRICTION_SHAPE_MISMATCH"}


def test_c012_scope_does_not_accept_invalid_scalar_as_shape_witness():
    case = sheaf()
    case["stalk_dims_v"]["v1"] = 2
    case["restrictions"]["v1<=e0"] = [[1.0]]
    with pytest.raises(ValueError):
        scope_violation(case)


def test_c012_zero_vector_basis_is_unverified():
    assert not check_certificate(sheaf(), {"status": "SOLVED", "h0_dim": "1", "h0_basis": [["0", "0"]], "h1_dim": "0"}).passed


@pytest.mark.parametrize("case,result", [([], {}), ({}, []), ({"challenge": "c999"}, {"status": "SOLVED"}), (triangle(), {"status": []}), ({"challenge": "c011", "nodes": None}, {"status": "SOLVED"})])
def test_malformed_json_shapes_fail_without_exceptions(case, result):
    assert not check_certificate(case, result).passed
