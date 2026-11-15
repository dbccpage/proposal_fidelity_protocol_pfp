"""
Executable test witness suite for Paper 002 derivations:
- ATL-P002-007 (Worked frontier trace)
- ATL-P002-008 (Pairwise cancellation necessity & {+2, -1, -1} counterexample)
- ATL-P002-010 (Single snapshot hashing of one-shot matrices)
"""

from fractions import Fraction
import math
from pathlib import Path
import sys
import pytest

# Ensure genesis_alpha modules are accessible
genesis_dir = Path(__file__).resolve().parents[1] / "atlas" / "archive" / "pfp" / "002_pfp_signed_presentations_and_search_frontier" / "code" / "genesis_alpha"
if str(genesis_dir) not in sys.path:
    sys.path.insert(0, str(genesis_dir))

from frontier_search import (
    CHECKER_VERSION,
    DIAGONAL_Z2_GRAMMAR,
    PresentationKey,
    exact_matrix_digest,
    search_exact_matrix,
    verify_search_receipt,
)
from sign_graph import (
    GaugeWitness,
    OddCycleWitness,
    SignedRewrite,
    matrix_sign_graph,
    verify_gauge,
    verify_odd_cycle,
)

RUNNING_MATRIX = ((0, 1, -1), (1, 0, 1), (-1, 1, 0))
POSITIVE_TRIANGLE = ((0, 1, 1), (1, 0, 1), (1, 1, 0))


def _make_key(matrix):
    return PresentationKey(
        hamiltonian_digest=exact_matrix_digest(matrix),
        basis="declared-three-state-basis",
        ensemble="toy-none",
        filling="toy-not-defined",
        boundary="finite-three-state",
        representation="fixed-real-matrix",
        estimator="off-diagonal-sign-only",
        observables=("toy-matrix-sign",),
        beta="not-used",
        parameters=(),
        transformation_grammar=DIAGONAL_Z2_GRAMMAR,
        adapter_digest="0" * 64,
        checker_version=CHECKER_VERSION,
    )


# ===========================================================================
# ATL-P002-007: Worked Frontier Trace
# ===========================================================================

def test_atl_p002_007_endpoint_sign_equations():
    """Verify endpoint sign equations on candidate gauges for RUNNING_MATRIX."""
    # Candidate 0: bits (0, 0, 0) -> signs (1, 1, 1)
    s0 = (1, 1, 1)
    assert s0[0] * RUNNING_MATRIX[0][1] * s0[1] == 1 > 0  # Fails nonpositivity

    # Candidate 1: bits (0, 0, 1) -> signs (1, 1, -1)
    s1 = (1, 1, -1)
    assert s1[0] * RUNNING_MATRIX[0][1] * s1[1] == 1 > 0  # Fails nonpositivity
    assert s1[0] * RUNNING_MATRIX[0][2] * s1[2] == 1 > 0  # Fails nonpositivity

    # Candidate 2: bits (0, 1, 0) -> signs (1, -1, 1)
    s2 = (1, -1, 1)
    assert s2[0] * RUNNING_MATRIX[0][1] * s2[1] == -1 <= 0  # Satisfied
    assert s2[0] * RUNNING_MATRIX[0][2] * s2[2] == -1 <= 0  # Satisfied
    assert s2[1] * RUNNING_MATRIX[1][2] * s2[2] == -1 <= 0  # Satisfied


def test_atl_p002_007_worked_trace_budget2_unknown_and_resume_budget1_verifies():
    """Verify worked trace: budget 2 -> UNKNOWN with [2,8); resume with budget 1 -> GAUGE_VERIFIED at index 2."""
    key = _make_key(RUNNING_MATRIX)
    vertices, edges = matrix_sign_graph(RUNNING_MATRIX)

    # Initial search with node_budget = 2
    first = search_exact_matrix(RUNNING_MATRIX, key, node_budget=2)
    assert first.status == "UNKNOWN"
    assert first.witness is None
    assert [(c.index, c.bits, c.valid) for c in first.checks] == [
        (0, (0, 0, 0), False),
        (1, (0, 0, 1), False),
    ]
    assert (first.frontier.next_index, first.frontier.stop_index) == (2, 8)

    # Resumption with node_budget = 1 from frontier [2, 8)
    second = search_exact_matrix(
        RUNNING_MATRIX,
        key,
        node_budget=1,
        frontier=first.frontier,
        prior_receipts=(first,),
    )
    assert second.status == "GAUGE_VERIFIED"
    assert isinstance(second.witness, GaugeWitness)
    assert second.witness.bits == (0, 1, 0)
    assert [(c.index, c.bits, c.valid) for c in second.checks] == [(2, (0, 1, 0), True)]
    assert second.frontier.next_index == 3

    # Receipt replay verification
    assert verify_search_receipt(vertices, edges, key, second, prior_receipts=(first,))
    # Omitting prior receipt fails verification due to incomplete index coverage
    assert not verify_search_receipt(vertices, edges, key, second)


# ===========================================================================
# ATL-P002-008: Pairwise Cancellation Necessity & Counterexample
# ===========================================================================

def verify_equal_weight_pairing(carrier, involution, signs, weights):
    """Verifies that involution I is fixed-point-free, sign-reversing, and magnitude-preserving."""
    for x in carrier:
        y = involution.get(x)
        if y is None or y not in carrier:
            return False, f"Missing target for {x}"
        if involution.get(y) != x:
            return False, f"Not an involution for {x}"
        if x == y:
            return False, f"Fixed point at {x}"
        if signs[y] != -signs[x]:
            return False, f"Sign reversal failed for pair ({x}, {y})"
        if weights[y] != weights[x]:
            return False, f"Magnitude preservation failed for pair ({x}, {y})"
    total = sum(signs[x] * weights[x] for x in carrier)
    if total != 0:
        return False, f"Nonzero paired sum: {total}"
    return True, "Valid"


def test_atl_p002_008_involution_cancellation_sufficiency():
    """Verify that an equal-weight fixed-point-free involution yields zero-sum pairwise cancellation."""
    carrier = ("p1", "m1", "p2", "m2")
    involution = {"p1": "m1", "m1": "p1", "p2": "m2", "m2": "p2"}
    signs = {"p1": 1, "m1": -1, "p2": 1, "m2": -1}
    weights = {"p1": 7, "m1": 7, "p2": 3, "m2": 3}

    valid, msg = verify_equal_weight_pairing(carrier, involution, signs, weights)
    assert valid, msg
    assert sum(signs[x] * weights[x] for x in carrier) == 0


def test_atl_p002_008_counterexample_plus2_minus1_minus1_cannot_pair():
    """Verify counterexample {+2, -1, -1}: nonnegative total (0 >= 0), but no equal-weight pairing exists."""
    multiset = [2, -1, -1]
    # Total sum is nonnegative (in fact zero)
    assert sum(multiset) == 0

    # Odd cardinality obstruction: cannot partition 3 elements into pairs
    assert len(multiset) % 2 != 0

    # Magnitude mismatch obstruction: negative terms require positive weight 1, but only 2 exists
    pos_weights = [w for w in multiset if w > 0]
    neg_weights = [-w for w in multiset if w < 0]
    assert pos_weights == [2]
    assert neg_weights == [1, 1]
    assert all(p != n for p in pos_weights for n in neg_weights)


def test_atl_p002_008_thermal_partition_function_positivity_obstruction():
    """Verify that thermal partition function Tr(e^(-beta H)) > 0 obstructs complete equal-weight cancellation."""
    eigenvalues = [-1.5, 0.0, 2.5]
    for beta in [0.0, 0.25, 1.0, 4.0]:
        z = sum(math.exp(-beta * lam) for lam in eigenvalues)
        assert z > 0
        # A complete zero-sum cancellation would require z == 0, which is obstructed
        assert not math.isclose(z, 0.0)


# ===========================================================================
# ATL-P002-010: Single Snapshot Hashing of One-Shot Matrices
# ===========================================================================

def test_atl_p002_010_one_shot_iterator_snapshot_digest_equality():
    """Verify that one-shot iterator produces identical digest to fully realized matrix."""
    pinned_digest = exact_matrix_digest(POSITIVE_TRIANGLE)

    # Pass a one-shot iterator
    iter_matrix = iter(POSITIVE_TRIANGLE)
    digest_from_iterator = exact_matrix_digest(iter_matrix)
    assert digest_from_iterator == pinned_digest


def test_atl_p002_010_one_shot_matrix_searched_from_single_snapshot():
    """Verify that search_exact_matrix validates and searches one-shot matrix without iterator exhaustion."""
    key = _make_key(POSITIVE_TRIANGLE)

    # Pass generator expression (one-shot stream)
    gen_matrix = (row for row in POSITIVE_TRIANGLE)
    result = search_exact_matrix(gen_matrix, key, node_budget=8)

    assert result.status == "RESTRICTED_OBSTRUCTION"
    assert isinstance(result.witness, OddCycleWitness)
    assert verify_odd_cycle(
        ("0", "1", "2"),
        (SignedRewrite("0", "1", 1), SignedRewrite("0", "2", 1), SignedRewrite("1", "2", 1)),
        result.witness,
    )


def test_atl_p002_010_mismatched_key_refusal():
    """Verify refusal when key digest does not match one-shot matrix snapshot."""
    empty_digest = exact_matrix_digest(())
    mismatched_key = PresentationKey(
        hamiltonian_digest=empty_digest,
        basis="declared-three-state-basis",
        ensemble="toy-none",
        filling="toy-not-defined",
        boundary="finite-three-state",
        representation="fixed-real-matrix",
        estimator="off-diagonal-sign-only",
        observables=("toy-matrix-sign",),
        beta="not-used",
        parameters=(),
        transformation_grammar=DIAGONAL_Z2_GRAMMAR,
        adapter_digest="0" * 64,
        checker_version=CHECKER_VERSION,
    )
    with pytest.raises(ValueError, match="presentation Hamiltonian digest does not match exact matrix"):
        search_exact_matrix(iter(POSITIVE_TRIANGLE), mismatched_key, node_budget=8)
