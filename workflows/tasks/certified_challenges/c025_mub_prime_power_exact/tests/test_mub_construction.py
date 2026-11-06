# AuthorityEffect: None.
"""Unit tests for MUB construction and refusal logic."""

from c025_mub_prime_power_exact.reference_solver.mub_construction import (
    build_mub_solution,
    get_standard_mubs,
)


def test_standard_mubs_prime_powers():
    for d, expected_bases in [(2, 3), (3, 4), (4, 5), (5, 6), (7, 8), (8, 9), (9, 10)]:
        m, bases = get_standard_mubs(d)
        assert len(bases) == expected_bases
        for b in bases:
            assert len(b) == d


def test_standard_mubs_composites():
    # d = 6 gives 3 bases in Q(zeta_12)
    m6, b6 = get_standard_mubs(6)
    assert m6 == 12
    assert len(b6) == 3

    # d = 10 gives 3 bases in Q(zeta_20)
    m10, b10 = get_standard_mubs(10)
    assert m10 == 20
    assert len(b10) == 3


def test_open_problem_refusal():
    # d = 6 with k >= 4 must refuse with OPEN_PROBLEM
    for k in (4, 5, 7):
        sol = build_mub_solution({"case_id": f"d6_k{k}", "dimension": 6, "num_bases": k})
        assert sol["status"] == "UNKNOWN"
        assert sol["refusal_code"] == "OPEN_PROBLEM"


def test_out_of_scope_refusal():
    # k > d + 1 must refuse with OUT_OF_SCOPE
    sol = build_mub_solution({"case_id": "oos", "dimension": 3, "num_bases": 5})
    assert sol["status"] == "OUT_OF_SCOPE"
    assert sol["witness"]["requested"] == 5
    assert sol["witness"]["max_possible"] == 4
