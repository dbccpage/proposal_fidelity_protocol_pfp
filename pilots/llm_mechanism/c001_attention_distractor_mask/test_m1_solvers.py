"""
test_m1_solvers.py — Targeted unit tests for Challenge C001 Milestone 1 solvers.

Tests:
1. Invariant & Graph Validation (Strict Zero-Float Law, canonical strings, schema checks).
2. Exact Potential Propagation (Consistency detection, potential assignment, Phi_1 = 0).
3. Minimal Directed Contradiction Cycle Extraction ((d_1 omega)(sigma) != 0, closed simple cycles).
4. Single-Edge Repair Solver (Identifies edge and value achieving Phi_1 = 0).
5. Witness Audit Solver (ACCEPT on valid potentials, REJECT on false witnesses with violated relation).
6. Distractor Span Character Offset Mapping (Strict prohibition of token-ID matching).
7. Dataset Suite Generation (40 public, 200 hidden base, 40 relabel controls, 30 poisoned).
8. 100% Mutation Kill Verification across all 7 checker mutations.
9. Standard `solve(case)` Executable Interface and output contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pilots.llm_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_case,
    generate_hidden_base_set,
    generate_mutation_cases,
    generate_poisoned_cases,
    generate_public_set,
    generate_relabel_controls,
    map_spans_to_token_positions,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.pipeline_contract import (
    validate_pipeline_pins,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.solve import (
    solve,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
    audit_witness,
    extract_contradiction_cycle,
    format_int,
    host_verdict,
    is_canonical_int_str,
    solve_single_repair,
    verify_certificate,
    verify_protocol_envelope,
)

# ---------------------------------------------------------------------------
# 1. Invariant & Graph Validation Tests
# ---------------------------------------------------------------------------


def test_canonical_integer_string_validation():
    """Verifies strict zero-float and canonical decimal integer formatting."""
    assert is_canonical_int_str("0") is True
    assert is_canonical_int_str("42") is True
    assert is_canonical_int_str("-100") is True
    assert is_canonical_int_str(0) is True
    assert is_canonical_int_str(42) is True

    # Non-canonical / floats / fractions rejected
    assert is_canonical_int_str("007") is False
    assert is_canonical_int_str("0.5") is False
    assert is_canonical_int_str("1/1") is False
    assert is_canonical_int_str("-0") is False
    assert is_canonical_int_str("+5") is False
    assert is_canonical_int_str(3.14) is False
    assert is_canonical_int_str(True) is False
    assert is_canonical_int_str(False) is False
    assert is_canonical_int_str("abc") is False


def test_format_int_exactness():
    """Verifies that format_int formats exact integers without float degradation."""
    assert format_int(0) == "0"
    assert format_int(-4) == "-4"
    assert format_int(12345) == "12345"
    with pytest.raises(TypeError):
        format_int(3.14)  # type: ignore
    with pytest.raises(TypeError):
        format_int(True)  # type: ignore


def test_constraint_system_validation_rejects_malformed_inputs():
    """Verifies that ConstraintSystem rejects self-loops, duplicate vertices, and invalid edges."""
    # Self loop
    with pytest.raises(ValueError, match="self-loop"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "A", 1]],
                "claims": {"A->A": 0},
            }
        )

    # Undeclared endpoint
    with pytest.raises(ValueError, match="undeclared endpoint"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "C", 1]],
                "claims": {"A->C": 1},
            }
        )

    # Non-integer claim
    with pytest.raises(ValueError, match="Non-canonical integer string"):
        ConstraintSystem.from_dict(
            {
                "items": ["A", "B"],
                "edges": [["A", "B", 1]],
                "claims": {"A->B": "0.5"},
            }
        )

    # Boolean vertex identifier
    with pytest.raises(ValueError, match="Boolean not permitted"):
        ConstraintSystem.from_dict(
            {
                "items": [True, "B"],
                "edges": [["A", "B", 1]],
                "claims": {"A->B": 1},
            }
        )

    # Boolean edge endpoint
    with pytest.raises(ValueError, match="Boolean endpoint not permitted"):
        ConstraintSystem.from_dict(
            {
                "items": ["True", "B"],
                "edges": [[True, "B", 1]],
                "claims": {"True->B": 1},
            }
        )


# ---------------------------------------------------------------------------
# 2. Exact Potential Propagation & Consistency
# ---------------------------------------------------------------------------


def test_potential_propagation_consistent_system():
    """Verifies O(|V|+|E|) potential propagation assigns exact potentials satisfying all edges."""
    items = ["A", "B", "C", "D"]
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "D", 1), ("A", "D", 1)]
    # phi: A=0, B=2, C=5, D=9
    # claims: (A,B)=2, (B,C)=3, (C,D)=4, (A,D)=9
    claims = {
        ("A", "B"): 2,
        ("B", "C"): 3,
        ("C", "D"): 4,
        ("A", "D"): 9,
    }
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    status, result = host_verdict(system)
    assert status == "CONSISTENT"
    assert isinstance(result, dict)
    # Check that phi(v) - phi(u) == claim for each edge
    for u, v, _w in edges:
        assert result[v] - result[u] == claims[(u, v)]


def test_potential_propagation_disconnected_system():
    """Verifies consistent disconnected components are solved with independent component potentials."""
    items = ["A", "B", "C", "D"]
    # Comp 1: A-B, Comp 2: C-D
    edges = [("A", "B", 1), ("C", "D", 1)]
    claims = {("A", "B"): 5, ("C", "D"): -3}
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    status, result = host_verdict(system)
    assert status == "CONSISTENT"
    assert isinstance(result, dict)
    assert result["B"] - result["A"] == 5
    assert result["D"] - result["C"] == -3


# ---------------------------------------------------------------------------
# 3. Contradiction Detection & Minimal Cycle Extraction
# ---------------------------------------------------------------------------


def test_contradiction_detection_and_cycle_extraction():
    """Verifies cycle extraction returns closed cycle with nonzero signed claim sum."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]
    # Cycle: A->B (+2), B->C (+3), but A->C (+4 instead of +5)
    # Directed cycle: A -> B -> C -> A has sum (+2) + (+3) + (-4) = +1 != 0
    claims = {
        ("A", "B"): 2,
        ("B", "C"): 3,
        ("A", "C"): 4,
    }
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    status, cycle = host_verdict(system)
    assert status == "CONTRADICTION"
    assert isinstance(cycle, list)
    assert len(cycle) >= 4
    assert cycle[0] == cycle[-1]

    # Verify signed sum along the cycle is strictly non-zero
    signed_sum = 0
    for i in range(len(cycle) - 1):
        u, v = cycle[i], cycle[i + 1]
        if (u, v) in claims:
            signed_sum += claims[(u, v)]
        elif (v, u) in claims:
            signed_sum -= claims[(v, u)]
        else:
            pytest.fail(f"Step ({u}, {v}) in extracted cycle is not a declared edge")
    assert signed_sum != 0


# ---------------------------------------------------------------------------
# 4. Single-Edge Repair Solver
# ---------------------------------------------------------------------------


def test_single_edge_repair_solver():
    """Verifies single-edge repair finds replacement edge claim making Phi_1 = 0."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]
    # Consistent potential: A=0, B=2, C=5
    # True claims: (A,B)=2, (B,C)=3, (A,C)=5
    # Perturb (A,C) to 99
    claims = {
        ("A", "B"): 2,
        ("B", "C"): 3,
        ("A", "C"): 99,
    }
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    repair_result = solve_single_repair(system)
    assert repair_result["status"] == "SOLVED"
    assert repair_result["kind"] == "repair"
    assert repair_result["edge"] in (["A", "C"], ["A", "B"], ["B", "C"])

    # Verify that the returned repair actually achieves Phi_1 = 0
    repaired_edge = tuple(repair_result["edge"])
    new_claims = dict(claims)
    new_claims[repaired_edge] = int(repair_result["value"])
    repaired_system = ConstraintSystem(items=items, edges=edges, claims=new_claims)
    status, _ = host_verdict(repaired_system)
    assert status == "CONSISTENT"


# ---------------------------------------------------------------------------
# 5. Witness Audit Solver
# ---------------------------------------------------------------------------


def test_witness_audit_accept_and_reject():
    """Verifies witness audit returns ACCEPT for valid potentials and REJECT with violated edge."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1)]
    claims = {("A", "B"): 3, ("B", "C"): 4}
    system = ConstraintSystem(items=items, edges=edges, claims=claims)

    # Valid potential
    valid_pot = {"A": "0", "B": "3", "C": "7"}
    audit_acc = audit_witness(system, valid_pot)
    assert audit_acc["status"] == "SOLVED"
    assert audit_acc["answer"] == "ACCEPT"

    # Invalid potential violating B->C
    invalid_pot = {"A": "0", "B": "3", "C": "10"}
    audit_rej = audit_witness(system, invalid_pot)
    assert audit_rej["status"] == "SOLVED"
    assert audit_rej["answer"] == "REJECT"
    assert audit_rej["violated"] == ["B", "C"]


# ---------------------------------------------------------------------------
# 6. Distractor Span Character Offset Mapping (Strict No Token-ID Matching)
# ---------------------------------------------------------------------------


def test_distractor_span_character_offset_mapping():
    """Verifies exact character offset mapping to token positions without token-ID matching."""
    text = "The relation (A, B) is 7. [Noise: value is 7.] Extra text."
    # The distractor span covers "[Noise: value is 7.]"
    d_start = text.index("[Noise")
    d_end = text.index("Extra")
    distractor_spans = [(d_start, d_end)]

    token_positions = map_spans_to_token_positions(text, distractor_spans)
    assert len(token_positions) > 0

    # Ensure token-ID collision does not affect carrier:
    # Notice that "7." appears in both carrier and distractor text!
    # With offset mapping, the first "7." is NOT in distractor_spans.
    tokens = list(re.finditer(r"\S+", text))
    first_seven_idx = next(i for i, m in enumerate(tokens) if m.group() == "7.")
    assert first_seven_idx not in token_positions


# ---------------------------------------------------------------------------
# 7. Dataset Suites Generation
# ---------------------------------------------------------------------------


def test_dataset_generation_public_set():
    """Verifies generation of 40 public cases (16 verdict, 16 repair, 8 audit)."""
    public_cases = generate_public_set(base_seed=1000)
    assert len(public_cases) == 40

    verdicts = [c for c in public_cases if c["kind"] == "verdict"]
    repairs = [c for c in public_cases if c["kind"] == "repair"]
    audits = [c for c in public_cases if c["kind"] == "audit"]

    assert len(verdicts) == 16
    assert len(repairs) == 16
    assert len(audits) == 8

    # Verify that all 40 public cases can be solved cleanly by solve()
    for case in public_cases:
        sol = solve(case)
        assert sol["status"] == "SOLVED"
        is_valid, reason = verify_certificate(case, sol)
        assert is_valid is True, f"Case {case['case_id']} failed verification: {reason}"


def test_dataset_generation_hidden_base_set_sample():
    """Verifies generation of 200 hidden base cases and tests a deterministic sample."""
    hidden_cases = generate_hidden_base_set(base_seed=2000)
    assert len(hidden_cases) == 200

    verdicts = [c for c in hidden_cases if c["kind"] == "verdict"]
    repairs = [c for c in hidden_cases if c["kind"] == "repair"]
    audits = [c for c in hidden_cases if c["kind"] == "audit"]

    assert len(verdicts) == 80
    assert len(repairs) == 80
    assert len(audits) == 40

    # Sample and solve 10 representative cases
    for case in hidden_cases[::20]:
        sol = solve(case)
        assert sol["status"] == "SOLVED"
        is_valid, reason = verify_certificate(case, sol)
        assert is_valid is True, f"Hidden case {case['case_id']} failed verification: {reason}"


def test_relabel_controls_and_poisoned_cases():
    """Verifies relabel controls (40) and poisoned schema-valid cases (30)."""
    public_cases = generate_public_set(base_seed=1000)
    relabel_cases = generate_relabel_controls(public_cases, seed=3000)
    assert len(relabel_cases) == 40

    poisoned_cases = generate_poisoned_cases(seed=4000)
    assert len(poisoned_cases) == 30

    # Test that solve() handles relabeled cases seamlessly
    for case in relabel_cases[:5]:
        sol = solve(case)
        assert sol["status"] == "SOLVED"
        is_valid, reason = verify_certificate(case, sol)
        assert is_valid is True, f"Relabeled case {case['case_id']} failed: {reason}"


# ---------------------------------------------------------------------------
# 8. 100% Mutation Kill Verification Suite
# ---------------------------------------------------------------------------


def test_100_percent_mutation_kill():
    """Verifies that the independent checker kills 100% of all 7 checker mutations."""
    mutations = generate_mutation_cases()
    assert len(mutations) == 7

    for mut in mutations:
        mut_id = mut["mutation_id"]
        case = mut["case"]
        sol = mut["solution"]
        is_valid, reason = verify_certificate(case, sol)

        # The checker MUST reject every mutation
        assert is_valid is False, (
            f"Checker failed to kill mutation {mut_id}: accepted with reason '{reason}'"
        )


# ---------------------------------------------------------------------------
# 9. Top-Level solve(case) Executable Interface & Schema
# ---------------------------------------------------------------------------


def test_solve_interface_out_of_scope_and_error_handling():
    """Verifies that solve() emits OUT_OF_SCOPE on malformed inputs."""
    # Non-dictionary case
    res1 = solve("not_a_dict")  # type: ignore
    assert res1["status"] == "OUT_OF_SCOPE"

    # Unsupported kind
    res2 = solve({"kind": "unsupported", "items": ["A"], "edges": [], "claims": {}})
    assert res2["status"] == "OUT_OF_SCOPE"

    # Missing claimed_potential for audit
    res3 = solve({"kind": "audit", "items": ["A"], "edges": [], "claims": {}})
    assert res3["status"] == "OUT_OF_SCOPE"
    assert res3["witness"]["field"] == "claimed_potential"


def test_frozen_pipeline_json_exists_and_conforms():
    """Verifies that pipeline.json exists in package root and conforms to schema."""
    pkg_dir = Path(__file__).resolve().parent
    pipeline_path = pkg_dir / "pipeline.json"
    assert pipeline_path.exists(), "pipeline.json must exist"

    with open(pipeline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema"] == "core.symbol-game.pipeline.v1"
    assert data["challenge_id"] == "C001"
    assert data["attention_implementation"] == "eager"
    assert data["intervention"] == "distractor_key_mask"
    assert "decoding_parameters" in data
    assert data["authority_effect"] == "None"
    # Digest pins must be real or explicitly UNSET; sentinel digests of empty inputs are refused.
    assert validate_pipeline_pins(data).status in ("READY", "NOT_READY")


def test_hf_like_tokenizer_offset_mapping():
    """Verifies map_spans_to_token_positions with a mock HuggingFace tokenizer returning offset_mapping."""

    class MockTokenizer:
        def __call__(self, text: str, return_offsets_mapping: bool = True):
            # Tokenize by word and return offset mapping
            spans = []
            for match in re.finditer(r"\S+", text):
                spans.append((match.start(), match.end()))
            return {"offset_mapping": [spans]}

    tokenizer = MockTokenizer()
    text = "Alpha Beta Gamma Delta [Noise Span] Epsilon"
    d_start = text.index("[Noise")
    d_end = text.index("Epsilon")
    distractor_spans = [(d_start, d_end)]

    token_positions = map_spans_to_token_positions(text, distractor_spans, tokenizer=tokenizer)
    # "[Noise" is token 4, "Span]" is token 5
    assert token_positions == [4, 5]


def test_graph_bounds_and_claim_magnitudes():
    """Verifies that generated graphs adhere to C001 bounds: 6 <= |V| <= 16, |V| <= |E| <= 40, |c_e| <= 10^4."""
    for seed in range(500, 520):
        case = generate_case(kind="verdict", n_items=6 + (seed % 11), seed=seed)
        items = case["items"]
        edges = case["edges"]
        claims = case["claims"]

        assert 6 <= len(items) <= 16
        assert len(items) <= len(edges) <= 40
        for edge_key, claim_str in claims.items():
            claim_val = int(claim_str)
            assert abs(claim_val) <= 10000


def test_cycle_reversal_negates_claim_sum():
    """Verifies that reversing the traversal of a cycle exactly negates its signed sum."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("A", "C", 1)]
    claims = {("A", "B"): 10, ("B", "C"): 20, ("A", "C"): 25}
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    cycle = extract_contradiction_cycle(system)
    assert cycle is not None
    assert len(cycle) >= 4

    # Forward sum
    fwd_sum = 0
    for i in range(len(cycle) - 1):
        u, v = cycle[i], cycle[i + 1]
        if (u, v) in claims:
            fwd_sum += claims[(u, v)]
        elif (v, u) in claims:
            fwd_sum -= claims[(v, u)]

    # Reverse cycle
    rev_cycle = list(reversed(cycle))
    rev_sum = 0
    for i in range(len(rev_cycle) - 1):
        u, v = rev_cycle[i], rev_cycle[i + 1]
        if (u, v) in claims:
            rev_sum += claims[(u, v)]
        elif (v, u) in claims:
            rev_sum -= claims[(v, u)]

    assert fwd_sum != 0
    assert rev_sum == -fwd_sum


def test_opposed_edges_rejected_during_intake_and_out_of_scope_in_solve():
    """Verifies that opposed edge pairs (e.g. A->B and B->A) are rejected during intake.

    Reproduces the review scenario: items A..F and edges A->B, B->A, B->C, C->D, D->E, E->F.
    - ConstraintSystem.from_dict must raise ValueError for opposed relation.
    - solve() must catch this and return a valid OUT_OF_SCOPE envelope with field='edges'.
    - verify_certificate must score OUT_OF_SCOPE as False (not a correct solution).
    - verify_protocol_envelope must score it as True (valid protocol envelope).
    """
    case = {
        "items": ["A", "B", "C", "D", "E", "F"],
        "edges": [
            ["A", "B"],
            ["B", "A"],
            ["B", "C"],
            ["C", "D"],
            ["D", "E"],
            ["E", "F"],
        ],
        "claims": {
            ("A", "B"): 1,
            ("B", "A"): 0,
            ("B", "C"): 2,
            ("C", "D"): 3,
            ("D", "E"): 4,
            ("E", "F"): 5,
        },
        "kind": "verdict",
    }

    # Intake directly rejects opposed relations
    with pytest.raises(ValueError, match="opposed relation edge not permitted"):
        ConstraintSystem.from_dict(case)

    # solve() handles invalid intake gracefully by emitting OUT_OF_SCOPE
    sol = solve(case)
    assert sol["status"] == "OUT_OF_SCOPE"
    assert sol["witness"]["field"] == "edges"
    assert "opposed relation edge not permitted" in sol["witness"]["reason"]

    # verify_certificate strictly refuses OUT_OF_SCOPE as a correct solution
    is_correct, reason = verify_certificate(case, sol)
    assert is_correct is False
    assert "OUT_OF_SCOPE" in reason

    # verify_protocol_envelope accepts it as schema-compliant
    is_valid_env, _ = verify_protocol_envelope(sol)
    assert is_valid_env is True


def test_solver_certificate_roundtrip_all_public_cases():
    """Verifies that every certificate emitted by solve() on all 40 public cases is verified by verify_certificate."""
    public_cases = generate_public_set(base_seed=42)
    assert len(public_cases) == 40

    solved_count = 0
    for case in public_cases:
        sol = solve(case)
        assert verify_protocol_envelope(sol)[0] is True, (
            f"Invalid protocol envelope on case {case['case_id']}"
        )
        if sol["status"] == "SOLVED":
            is_valid, msg = verify_certificate(case, sol)
            assert is_valid is True, (
                f"verify_certificate rejected solver output on case {case['case_id']}: {msg}"
            )
            solved_count += 1

    # All 40 public cases are solvable
    assert solved_count == 40


def test_unknown_refusal_is_not_counted_as_correct_certificate():
    """Verifies comment 4114007510: UNKNOWN refusal must NOT return True from verify_certificate."""
    case = generate_case(kind="verdict", n_items=6, n_relations=8, seed=123)
    refusal_sol = {"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"}

    # Protocol envelope accepts it as valid refusal syntax
    assert verify_protocol_envelope(refusal_sol)[0] is True

    # But verify_certificate must return False!
    is_correct, msg = verify_certificate(case, refusal_sol)
    assert is_correct is False
    assert "UNKNOWN refusal" in msg


@pytest.mark.parametrize("solution_kind", ["verdict", "repair", "audit"])
def test_certificate_must_answer_the_requested_case_kind(solution_kind):
    """A correct answer to another task must not inflate the model's score."""
    case = {
        "kind": solution_kind,
        "items": ["A", "B", "C"],
        "edges": [["A", "B"], ["B", "C"], ["A", "C"]],
        "claims": {"A->B": "2", "B->C": "3", "A->C": "4"},
        "claimed_potential": {"A": "0", "B": "2", "C": "5"},
    }
    solution = solve(case)
    assert solution["status"] == "SOLVED"
    assert verify_certificate(case, solution)[0] is True

    for requested_kind in ("verdict", "repair", "audit"):
        if requested_kind == solution_kind:
            continue
        valid, reason = verify_certificate({**case, "kind": requested_kind}, solution)
        assert valid is False
        assert "does not match requested case kind" in reason


@pytest.mark.parametrize("bad_vertex", [[], {}, None, True, 1, 1.0])
def test_malformed_cycle_vertex_is_rejected_without_raising(bad_vertex):
    """Malformed model JSON must score as incorrect without stopping evaluation."""
    case = {
        "kind": "verdict",
        "items": ["A", "B", "C"],
        "edges": [["A", "B"], ["B", "C"], ["A", "C"]],
        "claims": {"A->B": "2", "B->C": "3", "A->C": "4"},
    }
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": ["A", bad_vertex, "C", "A"],
    }
    valid, reason = verify_certificate(case, solution)
    assert valid is False
    assert "Cycle vertices must be string identifiers" in reason
