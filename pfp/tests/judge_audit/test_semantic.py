"""Semantic mutants: valid alternatives and consistent non-minimal answers."""

from __future__ import annotations

from omega_engine_woland.tests.pilots.judge_packet_audit import semantic

# Z2 = {e, a} on a 2x2 open lattice, one plaquette 0,0 -> 1,0 -> 1,1 -> 0,1
Z2 = {
    "identity": "e",
    "elements": ["e", "a"],
    "table": {"e": {"e": "e", "a": "a"}, "a": {"e": "a", "a": "e"}},
}
EDGES = {
    "0,0->1,0": "a",
    "1,0->0,0": "a",
    "1,0->1,1": "e",
    "1,1->1,0": "e",
    "1,1->0,1": "e",
    "0,1->1,1": "e",
    "0,1->0,0": "e",
    "0,0->0,1": "e",
}
CASE_017 = {"id": "k", "L": 2, "M": 2, "boundary": "open", "group": Z2, "edges": EDGES}
REF_017 = {
    "id": "k",
    "status": "SOLVED",
    "verdict": "NOT_FLAT",
    "plaquette": ["0,0", "1,0", "1,1", "0,1"],
    "holonomy": "a",
}


def test_c017_rotation_and_reversal_recompute_the_holonomy() -> None:
    # counterexample: before repair the checker accepted one vertex order only
    rotated = semantic.c017_rotated_plaquette(CASE_017, REF_017)
    assert rotated["plaquette"] == ["1,0", "1,1", "0,1", "0,0"] and rotated["holonomy"] == "a"
    reversed_ = semantic.c017_reversed_plaquette(CASE_017, REF_017)
    assert reversed_["plaquette"] == ["0,1", "1,1", "1,0", "0,0"] and reversed_["holonomy"] == "a"
    assert semantic.c017_rotated_plaquette(CASE_017, dict(REF_017, verdict="PURE_GAUGE")) is None


def test_c017_gauge_translation_keeps_a_valid_gauge() -> None:
    ref = {
        "id": "k",
        "status": "SOLVED",
        "verdict": "PURE_GAUGE",
        "gauge": {"0,0": "e", "1,0": "a"},
    }
    assert semantic.c017_translated_gauge(CASE_017, ref)["gauge"] == {"0,0": "a", "1,0": "e"}


def test_c022_products_give_an_alternative_logical_and_an_overstated_distance() -> None:
    # repetition code on 3 qubits: stabilizers ZZI and IZZ; the logical Z on one qubit (ZII)
    # has weight 1. Products: ZII*ZZI = IZI, ZII*IZZ = ZZZ, ZII*ZZI*IZZ = IIZ.
    case = {"id": "r", "num_qubits": 3, "generators": ["+ZZI", "+IZZ"]}
    ref = {"id": "r", "status": "SOLVED", "distance": 1, "logical": "ZII", "lower_bound": None}
    alternative = semantic.c022_alternative_logical(case, ref)
    assert alternative["logical"] == "IZI" and alternative["distance"] == 1
    overstated = semantic.c022_overstated_distance(case, ref)
    assert overstated["logical"] == "ZZZ" and overstated["distance"] == 3


def test_w10_zero_potential_is_consistent_and_non_minimal() -> None:
    case = {
        "case_id": "w",
        "vertices": ["v0", "v1", "v2"],
        "edges": [["v0", "v1"], ["v1", "v2"], ["v0", "v2"]],
        "faces": [],
        "cochain": [["e0", "1/1"], ["e1", "1/1"], ["e2", "1/1"]],
    }
    ref = {
        "case_id": "w",
        "status": "SOLVED",
        "phi_1": "1/1",
        "gamma_2": "0/1",
        "r_cl": "0/1",
        "three_way_class": "CLOSED_OBSTRUCTION",
        "is_gauge_removable": False,
        "optimal_potential": [["v0", "0/1"], ["v1", "1/1"], ["v2", "2/1"]],
        "residual_quotient_vector": [["e0", "0/1"], ["e1", "0/1"], ["e2", "-1/1"]],
    }
    mutant = semantic.w10_zero_potential(case, ref)
    assert mutant["phi_1"] == "3/1" and mutant["three_way_class"] == "CLOSED_OBSTRUCTION"
    assert mutant["optimal_potential"] == [["v0", "0/1"], ["v1", "0/1"], ["v2", "0/1"]]
    assert mutant["residual_quotient_vector"] == [["e0", "1/1"], ["e1", "1/1"], ["e2", "1/1"]]
    assert mutant["r_cl"] == "0/1" and mutant["is_gauge_removable"] is False
    # the zero potential is optimal here, so the mutant does not apply
    assert semantic.w10_zero_potential(case, dict(ref, phi_1="3/1")) is None


def test_strategies_skip_inexact_references_and_empty_mutants() -> None:
    refs = [{"exact_json": True, "json": REF_017}, {"exact_json": False, "json": REF_017}]
    strategies = semantic.semantic_strategies("C017", [CASE_017, CASE_017], refs)
    assert [s["id"] for s in strategies] == [
        "semantic:rotated_plaquette",
        "semantic:reversed_plaquette",
    ]
    assert strategies[0]["per_case"][1] is None and strategies[0]["expected"] == "ACCEPT"
    assert semantic.semantic_strategies("C011", [CASE_017], refs[:1]) == []
