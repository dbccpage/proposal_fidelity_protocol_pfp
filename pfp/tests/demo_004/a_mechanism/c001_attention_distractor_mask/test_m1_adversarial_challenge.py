"""
test_m1_adversarial_challenge.py — Empirical challenge and mutation resistance test suite for M1.

Adversarially tests:
1. 100% kill rate on the 7 canonical checker mutations.
2. Comprehensive variations of the 7 checker mutations:
   - Off-by-one potential mutations (root, leaf, cycle, +/-1, large off-by-N)
   - Unclosed cycles (open walk, mismatched start/end, empty, len 1/2/3, disconnected)
   - Undeclared edge traversals (nonexistent vertices, non-adjacent vertices, zero-sum loops)
   - Multiple-edge repairs & invalid repairs (2 edges, 3 edges, 0 edges, non-restoring values)
   - Float strings & non-canonical representations ("1.0", "0.5", "1/1", "007", "-0", "+5", bools)
   - False reject attacks (naming satisfied edges, undeclared edges, malformed edge structures)
   - False accept attacks (accepting invalid potentials with 1, 2, all violated relations)
3. Fail-closed verification on corrupted inputs for ConstraintSystem, solve(), and verify_certificate().
4. Empirical vulnerability discovery:
   - Trailing newline ("\\n") regex boundary behavior in _CANONICAL_INT_RE ($ vs \\Z)
   - Uncaught ValueError in verify_certificate() on float strings in claimed_potential
   - Case validity check omission in audit REJECT verification
   - Blind acceptance of arbitrary UNKNOWN and OUT_OF_SCOPE payloads on valid solvable cases
"""

from __future__ import annotations

from typing import Any, List

import pytest
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_case,
    generate_mutation_cases,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solve import (
    solve,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
    audit_witness,
    format_int,
    host_verdict,
    is_canonical_int_str,
    verify_certificate,
    verify_protocol_envelope,
)

# ===========================================================================
# 1. Canonical 7 Checker Mutations (100% Kill Rate Verification)
# ===========================================================================


def test_canonical_7_mutations_killed():
    """Verifies that all 7 canonical checker mutations from case_generator are rejected."""
    mutations = generate_mutation_cases()
    assert len(mutations) == 7

    kill_count = 0
    for mut in mutations:
        is_valid, reason = verify_certificate(mut["case"], mut["solution"])
        if not is_valid:
            kill_count += 1
        else:
            pytest.fail(f"Mutant {mut['mutation_id']} survived: reason='{reason}'")

    assert kill_count == 7
    kill_rate = kill_count / len(mutations)
    assert kill_rate == 1.0


# ===========================================================================
# 2. Mutation Category 1: Off-By-One Potential Variations
# ===========================================================================


@pytest.mark.parametrize(
    "delta,target_node",
    [
        (1, "A"),  # +1 at root
        (-1, "A"),  # -1 at root
        (1, "F"),  # +1 at leaf
        (-1, "F"),  # -1 at leaf
        (2, "C"),  # +2 at intermediate
        (-5, "D"),  # -5 at intermediate
        (1000, "B"),  # large offset
        (-9999, "E"),
    ],
)
def test_off_by_one_potential_mutations_killed(delta: int, target_node: str):
    """Mutates potential by non-zero delta at various nodes; verify_certificate must reject."""
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=101, contradictory_verdict=False
    )
    system = ConstraintSystem.from_dict(case)
    status, pot = host_verdict(system)
    assert status == "CONSISTENT" and isinstance(pot, dict)

    mutated_pot = {k: format_int(v) for k, v in pot.items()}
    if target_node in mutated_pot:
        mutated_pot[target_node] = format_int(int(mutated_pot[target_node]) + delta)

    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": mutated_pot,
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "violates relation" in reason or "not a canonical" in reason


# ===========================================================================
# 3. Mutation Category 2: Unclosed & Malformed Cycle Variations
# ===========================================================================


@pytest.mark.parametrize(
    "bad_cycle,desc",
    [
        (["A", "B", "C"], "open walk length 3"),
        (["A", "B", "C", "D"], "open walk length 4"),
        (["A", "B", "C", "B"], "ends at intermediate node B instead of A"),
        ([], "empty cycle"),
        (["A"], "length 1 cycle"),
        (["A", "A"], "length 2 self-loop"),
        (["A", "B", "A"], "length 3 back-and-forth"),
    ],
)
def test_unclosed_cycle_mutations_killed(bad_cycle: List[str], desc: str):
    """Verifies that unclosed or under-length cycles are rejected."""
    case = generate_case(
        kind="verdict", n_items=6, n_relations=8, seed=201, contradictory_verdict=True
    )
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": bad_cycle,
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False, f"Mutant survived ({desc}): {reason}"
    assert "not closed" in reason or "requires cycle of at least 3 vertices" in reason


# ===========================================================================
# 4. Mutation Category 3: Undeclared Edge Traversals in Cycle
# ===========================================================================


def test_cycle_traversing_undeclared_vertex():
    """Cycle traverses a completely non-existent vertex."""
    case = generate_case(
        kind="verdict", n_items=6, n_relations=8, seed=301, contradictory_verdict=True
    )
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": ["A", "NON_EXISTENT", "B", "A"],
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "undeclared relation" in reason


def test_cycle_traversing_non_adjacent_vertices():
    """Cycle vertices exist, but edge between two consecutive vertices is not declared."""
    case = generate_case(
        kind="verdict", n_items=8, n_relations=9, seed=302, contradictory_verdict=True
    )
    system = ConstraintSystem.from_dict(case)
    declared_pairs = set(system.claims.keys())

    # Find two items u, v that are NOT connected in either direction
    missing_pair = None
    for u in system.items:
        for v in system.items:
            if u != v and (u, v) not in declared_pairs and (v, u) not in declared_pairs:
                missing_pair = (u, v)
                break
        if missing_pair:
            break

    assert missing_pair is not None, "Failed to find non-adjacent pair"
    u, v = missing_pair
    # Construct cycle traversing this undeclared edge
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": [u, v, system.items[0], u],
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "undeclared relation" in reason


def test_cycle_with_zero_signed_claim_sum_rejected():
    """A closed walk traversing declared edges but with net signed claim sum == 0 must be rejected."""
    # Build a consistent 4-vertex cycle: A -(1)-> B -(2)-> C -(-3)-> A
    case = {
        "items": ["A", "B", "C"],
        "edges": [["A", "B", 1], ["B", "C", 1], ["C", "A", 1]],
        "claims": {"A->B": 1, "B->C": 2, "C->A": -3},
        "kind": "verdict",
    }
    # Signed sum = 1 + 2 + (-3) = 0.
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": ["A", "B", "C", "A"],
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "zero signed claim sum" in reason


# ===========================================================================
# 5. Mutation Category 4: Multiple-Edge & Invalid Repair Mutations
# ===========================================================================


@pytest.mark.parametrize(
    "bad_edge,desc",
    [
        (["A", "B", "C", "D"], "two edges (4 elements)"),
        (["A", "B", "C"], "three elements"),
        (["A"], "one element"),
        ([], "empty edge list"),
        ([["A", "B"], ["C", "D"]], "nested list"),
        (["A", "UNKNOWN_VERTEX"], "undeclared endpoint"),
    ],
)
def test_multiple_or_malformed_edge_repair_rejected(bad_edge: Any, desc: str):
    """Repair payload must specify exactly one valid 2-element declared edge."""
    case = generate_case(kind="repair", n_items=6, n_relations=8, seed=401)
    solution = {
        "status": "SOLVED",
        "kind": "repair",
        "edge": bad_edge,
        "value": "0",
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False, f"Mutant survived ({desc}): {reason}"


def test_repair_with_ineffective_value_rejected():
    """Repair modifies a declared edge, but with a value that does NOT make Phi_1 = 0."""
    case = generate_case(kind="repair", n_items=6, n_relations=8, seed=402)
    first_edge = case["edges"][0]
    u, v = first_edge[0], first_edge[1]

    # Solve genuine repair
    correct_sol = solve(case)
    correct_val = int(correct_sol["value"])

    # Provide a wrong value (e.g. correct_val + 1)
    wrong_val = correct_val + 1
    bad_solution = {
        "status": "SOLVED",
        "kind": "repair",
        "edge": [u, v],
        "value": format_int(wrong_val),
    }
    is_valid, reason = verify_certificate(case, bad_solution)
    assert is_valid is False
    assert "does not yield Phi_1 = 0" in reason or "not a declared edge" in reason


# ===========================================================================
# 6. Mutation Category 5: Float Strings & Non-Canonical Numbers
# ===========================================================================


@pytest.mark.parametrize(
    "non_canonical_val",
    [
        "1.0",
        "0.5",
        "-3.14",
        "1e5",
        "1/1",
        "3/4",
        "-2/3",
        "007",
        "-0",
        "+5",
        " 42 ",
        "",
        "abc",
    ],
)
def test_non_canonical_strings_rejected_in_potential(non_canonical_val: str):
    """Potential values must be canonical decimal integer strings without floats or fractions."""
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=501, contradictory_verdict=False
    )
    system = ConstraintSystem.from_dict(case)
    status, pot = host_verdict(system)
    assert status == "CONSISTENT" and isinstance(pot, dict)

    mutated_pot = {k: format_int(v) for k, v in pot.items()}
    mutated_pot["A"] = non_canonical_val

    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": mutated_pot,
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "not a canonical int string" in reason


@pytest.mark.parametrize(
    "non_canonical_val",
    [
        "1.0",
        "0.5",
        "1/1",
        "007",
        "-0",
        "+10",
        "NaN",
    ],
)
def test_non_canonical_strings_rejected_in_repair(non_canonical_val: str):
    """Repair value must be a canonical decimal integer string."""
    case = generate_case(kind="repair", n_items=6, n_relations=8, seed=502)
    first_edge = case["edges"][0]
    solution = {
        "status": "SOLVED",
        "kind": "repair",
        "edge": [first_edge[0], first_edge[1]],
        "value": non_canonical_val,
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False
    assert "not a canonical integer string" in reason


# ===========================================================================
# 7. Mutation Category 6: False Reject in Witness Audit
# ===========================================================================


def test_false_reject_naming_satisfied_edge():
    """When a claimed potential satisfies all edges, REJECT naming any edge is killed."""
    case = generate_case(
        kind="audit", n_items=6, n_relations=7, seed=601, false_witness_audit=False
    )
    # Check that claimed_potential is genuinely valid
    audit_res = audit_witness(ConstraintSystem.from_dict(case), case["claimed_potential"])
    assert audit_res["answer"] == "ACCEPT"

    # Attack: Submit REJECT naming each declared edge
    for edge in case["edges"]:
        u, v = edge[0], edge[1]
        false_reject_sol = {
            "status": "SOLVED",
            "kind": "audit",
            "answer": "REJECT",
            "violated": [u, v],
        }
        is_valid, reason = verify_certificate(case, false_reject_sol)
        assert is_valid is False
        assert "actually satisfied" in reason


def test_false_reject_naming_undeclared_edge():
    """REJECT naming an edge not in the graph is killed."""
    case = generate_case(kind="audit", n_items=6, n_relations=7, seed=602, false_witness_audit=True)
    false_reject_sol = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "REJECT",
        "violated": ["A", "NON_EXISTENT_VERTEX"],
    }
    is_valid, reason = verify_certificate(case, false_reject_sol)
    assert is_valid is False
    assert "not a declared relation" in reason


# ===========================================================================
# 8. Mutation Category 7: False Accept in Witness Audit
# ===========================================================================


@pytest.mark.parametrize("seed", [701, 702, 703, 704, 705])
def test_false_accept_on_invalid_potential(seed: int):
    """When claimed potential violates relations, ACCEPT is killed."""
    case = generate_case(
        kind="audit", n_items=6, n_relations=8, seed=seed, false_witness_audit=True
    )
    audit_res = audit_witness(ConstraintSystem.from_dict(case), case["claimed_potential"])
    assert audit_res["answer"] == "REJECT"

    false_accept_sol = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "ACCEPT",
    }
    is_valid, reason = verify_certificate(case, false_accept_sol)
    assert is_valid is False
    assert "False ACCEPT" in reason


# ===========================================================================
# 9. Fail-Closed Robustness on Corrupted Graph Inputs
# ===========================================================================


def test_constraint_system_rejects_self_loops():
    with pytest.raises(ValueError, match="self-loop"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "A", 1]],
                "claims": {"A->A": 0},
            }
        )


def test_constraint_system_rejects_undeclared_endpoint():
    with pytest.raises(ValueError, match="undeclared endpoint"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "Z", 1]],
                "claims": {"A->Z": 1},
            }
        )


def test_constraint_system_rejects_duplicate_items():
    with pytest.raises(ValueError, match="distinct vertex identifiers"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B", "A"],
                "edges": [["A", "B", 1]],
                "claims": {"A->B": 1},
            }
        )


def test_constraint_system_rejects_empty_items():
    with pytest.raises(ValueError, match="non-empty list"):
        ConstraintSystem.from_dict(
            {
                "items": [],
                "edges": [],
                "claims": {},
            }
        )


def test_constraint_system_rejects_negative_weight():
    with pytest.raises(ValueError, match="invalid weight"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "B", -1]],
                "claims": {"A->B": 1},
            }
        )


def test_constraint_system_rejects_float_claim():
    with pytest.raises(ValueError, match="Non-canonical integer string"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "B", 1]],
                "claims": {"A->B": "1.5"},
            }
        )


def test_constraint_system_rejects_claims_mismatch():
    with pytest.raises(ValueError, match="claims keys mismatch declared edges"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B", "C"],
                "edges": [["A", "B", 1], ["B", "C", 1]],
                "claims": {"A->B": 1},  # missing B->C
            }
        )


# ===========================================================================
# 10. Fail-Closed Robustness on solve() Interface
# ===========================================================================


@pytest.mark.parametrize(
    "corrupted_case",
    [
        None,
        "not_a_dict",
        [1, 2, 3],
        {"kind": "bogus_kind", "items": ["A"]},
        {"kind": "audit", "items": ["A"], "edges": [], "claims": {}},  # missing claimed_potential
        {
            "items": ["A"],
            "edges": [["A", "A", 1]],
            "claims": {"A->A": 0},
            "kind": "verdict",
        },  # self-loop
    ],
)
def test_solve_interface_fails_closed_on_corrupted_inputs(corrupted_case: Any):
    """solve() must emit OUT_OF_SCOPE with a structured witness rather than crashing."""
    res = solve(corrupted_case)  # type: ignore
    assert isinstance(res, dict)
    assert res["status"] == "OUT_OF_SCOPE"
    assert "witness" in res
    assert "field" in res["witness"]
    assert "reason" in res["witness"]


# ===========================================================================
# 11. Fail-Closed Robustness on verify_certificate()
# ===========================================================================


@pytest.mark.parametrize(
    "bad_solution,expected_msg",
    [
        (None, "Solution must be a dictionary"),
        ("string", "Solution must be a dictionary"),
        ([1, 2], "Solution must be a dictionary"),
        ({}, "Invalid status: None"),
        ({"status": "BOGUS"}, "Invalid status: 'BOGUS'"),
        ({"status": "UNKNOWN"}, "UNKNOWN refusal"),
        ({"status": "OUT_OF_SCOPE"}, "OUT_OF_SCOPE is a refusal"),
        ({"status": "OUT_OF_SCOPE", "witness": "not_a_dict"}, "OUT_OF_SCOPE is a refusal"),
        ({"status": "SOLVED", "kind": "unknown_kind"}, "Unknown kind: 'unknown_kind'"),
        (
            {"status": "SOLVED", "kind": "verdict", "answer": "MAYBE"},
            "Unknown verdict answer: 'MAYBE'",
        ),
    ],
)
def test_verify_certificate_fails_closed_on_malformed_solution(
    bad_solution: Any, expected_msg: str
):
    """verify_certificate must fail-closed on malformed solution payloads."""
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=801, contradictory_verdict=False
    )
    is_valid, reason = verify_certificate(case, bad_solution)
    assert is_valid is False
    assert expected_msg in reason


def test_verify_certificate_fails_closed_on_corrupted_case():
    """verify_certificate must fail-closed when case_dict is invalid."""
    bad_case = {"items": ["A", "B"], "edges": [["A", "A", 1]], "claims": {"A->A": 0}}
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": {"A": "0", "B": "0"},
    }
    is_valid, reason = verify_certificate(bad_case, solution)
    assert is_valid is False
    assert "Invalid case dict" in reason


# ===========================================================================
# 12. Empirical Vulnerability Demonstrations
# ===========================================================================


def test_vulnerability_trailing_newline_survives_validation():
    """EMPIRICAL FINDING 1 (FIXED): Trailing newline ('\\n') rejected by is_canonical_int_str via \\Z anchor.

    Verifies that:
    1. is_canonical_int_str('0\\n') returns False.
    2. is_canonical_int_str('42\\n') returns False.
    3. verify_certificate rejects potentials with trailing newlines.
    """
    assert is_canonical_int_str("0\n") is False, "Trailing newline must be rejected by \\Z anchor"
    assert is_canonical_int_str("42\n") is False

    # Attack: Inject trailing newline into potential
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=901, contradictory_verdict=False
    )
    sys = ConstraintSystem.from_dict(case)
    _stat, pot = host_verdict(sys)
    assert isinstance(pot, dict)
    mutated_pot = {k: format_int(v) + "\n" for k, v in pot.items()}

    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": mutated_pot,
    }
    is_valid, reason = verify_certificate(case, solution)
    assert is_valid is False, "Potential with trailing newline must be rejected"
    assert "not a canonical int string" in reason.lower()


def test_vulnerability_audit_uncaught_value_error_on_float_in_claimed_potential():
    """EMPIRICAL FINDING 2 (FIXED): Exception safety in verify_certificate on float in claimed_potential.

    When an audit case contains a float string ('1.5') in claimed_potential,
    verify_certificate returns (False, reason) fail-closed without raising ValueError.
    """
    case = generate_case(kind="audit", n_items=6, n_relations=7, seed=902)
    # Inject float string into claimed_potential
    case["claimed_potential"]["A"] = "1.5"
    sol = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "REJECT",
        "violated": [case["edges"][0][0], case["edges"][0][1]],
    }
    is_valid, reason = verify_certificate(case, sol)
    assert is_valid is False, "Float in claimed_potential must fail certificate verification"
    assert "out of scope" in reason.lower()


def test_vulnerability_audit_reject_accepted_on_incomplete_case():
    """EMPIRICAL FINDING 3 (FIXED): verify_certificate rejects REJECT solution on incomplete audit case.

    When an audit case has missing endpoints in claimed_potential, audit_witness
    reports OUT_OF_SCOPE. verify_certificate returns (False, reason) rejecting
    the solution on an out-of-scope case.
    """
    case = generate_case(kind="audit", n_items=6, n_relations=7, seed=903)
    # Delete an endpoint not involved in edge 0
    endpoint_to_delete = [
        item for item in case["items"] if item not in (case["edges"][0][0], case["edges"][0][1])
    ][0]
    del case["claimed_potential"][endpoint_to_delete]

    # Ground truth is OUT_OF_SCOPE
    sys = ConstraintSystem.from_dict(case)
    gt_audit = audit_witness(sys, case["claimed_potential"])
    assert gt_audit["status"] == "OUT_OF_SCOPE"

    # Perturb edge 0 endpoints so discrepancy exists
    u, v = case["edges"][0][0], case["edges"][0][1]
    case["claimed_potential"][v] = str(int(case["claimed_potential"][u]) + 99999)

    sol = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "REJECT",
        "violated": [u, v],
    }
    is_valid, reason = verify_certificate(case, sol)
    assert is_valid is False, "SOLVED must be rejected on OUT_OF_SCOPE audit case"
    assert "out of scope" in reason.lower()


def test_vulnerability_bogus_unknown_refusal_accepted_on_solvable_case():
    """EMPIRICAL FINDING 4 (FIXED): verify_certificate rejects arbitrary UNKNOWN refusal on solvable case.

    Demonstrates that verify_certificate no longer treats UNKNOWN refusal as a verified correct solution (C001 §4).
    verify_protocol_envelope confirms envelope validity while verify_certificate returns False.
    """
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=904, contradictory_verdict=False
    )
    fake_refusal_solution = {
        "status": "UNKNOWN",
        "refusal": "arbitrary_refusal_string",
    }
    is_valid, reason = verify_certificate(case, fake_refusal_solution)
    assert is_valid is False
    assert "UNKNOWN refusal" in reason

    is_valid_env, _ = verify_protocol_envelope(fake_refusal_solution)
    assert is_valid_env is True


def test_vulnerability_bogus_out_of_scope_accepted_on_valid_case():
    """EMPIRICAL FINDING 5 (FIXED): verify_certificate rejects arbitrary OUT_OF_SCOPE on schema-valid case.

    Demonstrates that verify_certificate no longer treats OUT_OF_SCOPE as a verified correct solution (C001 §4).
    verify_protocol_envelope confirms envelope validity while verify_certificate returns False.
    """
    case = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=905, contradictory_verdict=False
    )
    fake_out_of_scope = {
        "status": "OUT_OF_SCOPE",
        "witness": {"field": "items", "reason": "fake_out_of_scope_claim"},
    }
    is_valid, reason = verify_certificate(case, fake_out_of_scope)
    assert is_valid is False
    assert "OUT_OF_SCOPE is a refusal" in reason

    is_valid_env, _ = verify_protocol_envelope(fake_out_of_scope)
    assert is_valid_env is True
