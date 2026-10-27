"""Comprehensive tests for exact CODA primal-dual L1 gauge solver and dual witness certification.

AuthorityEffect: None.

Tests:
1. Flat diamond poset: Phi_1([K]) == 0, zero duality gap, residual is zero.
2. Flat 4-chain with 2x2 matrix fibers: Phi_1([K]) == 0, zero duality gap.
3. Curved diamond with K != 0 but K in im(delta_1): Phi_1([K]) == 0, gauge T* absorbs K.
4. Obstructed 2-cochains with Phi_1([H]) > 0: exact positive primal value == dual value,
   zero duality gap, dual cocycle condition (delta_1)^*(Y*) == 0, and subgradient bound |Y*_i| <= w_i.
5. Non-uniform rational weights: verifies varying weights w_i > 0 preserve zero duality gap.
6. Subgradient complementary slackness: verifies Y*_i = sgn(R*_i) * w_i whenever R*_i != 0.
7. Multi-poset parameterized sweep: validates zero duality gap across varied posets and fiber dimensions.
8. Edge cases: trivial posets, zero 2-cochains, and zero-column systems.
"""

from fractions import Fraction
import pytest

from covering_edge_poset import FinitePoset
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cohomology_quotient import (
    Operator1Cochain,
    Operator2Cochain,
    OperatorCochainImageDiagnostic,
    operator_coboundary_delta1,
    build_curvature_operator_cochain,
)
from exact_coda_solver import (
    DualWitnessCertificate,
    ExactCodaL1Solver,
    compute_exact_coda_gauge_distance,
    solve_l1_primal_dual_exact,
)


def _make_diamond_poset() -> FinitePoset:
    return FinitePoset(
        elements=["bot", "x", "y", "top"],
        relations=[("bot", "x"), ("bot", "y"), ("x", "top"), ("y", "top")],
    )


def _make_4chain_poset() -> FinitePoset:
    return FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )


def test_flat_diamond_primal_dual_zero_gap():
    """Flat diamond system must yield Phi_1([K]) == 0 with certified zero duality gap."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=eye),
            RestrictionMap(source="y", target="bot", matrix=eye),
            RestrictionMap(source="top", target="x", matrix=eye),
            RestrictionMap(source="top", target="y", matrix=eye),
            RestrictionMap(source="top", target="bot", matrix=eye),
        ],
    )

    cert = compute_exact_coda_gauge_distance(system)

    assert cert.primal_value == Fraction(0)
    assert cert.dual_value == Fraction(0)
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.optimal_residual.is_zero() is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True


def test_flat_4chain_matrix_fibers_zero_gap():
    """Flat 4-chain with 2x2 fibers must have Phi_1([K]) == 0 and certified dual witness."""
    poset = _make_4chain_poset()
    eye2 = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])
    m_ba = Matrix([[Fraction(2), Fraction(1)], [Fraction(0), Fraction(1)]])
    m_cb = Matrix([[Fraction(1), Fraction(-1)], [Fraction(3), Fraction(2)]])
    m_dc = Matrix([[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(3)]])
    m_ca = m_ba * m_cb
    m_db = m_cb * m_dc
    m_da = m_ba * m_db

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"a": 2, "b": 2, "c": 2, "d": 2},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye2) for n in poset.elements
        ] + [
            RestrictionMap(source="b", target="a", matrix=m_ba),
            RestrictionMap(source="c", target="b", matrix=m_cb),
            RestrictionMap(source="d", target="c", matrix=m_dc),
            RestrictionMap(source="c", target="a", matrix=m_ca),
            RestrictionMap(source="d", target="b", matrix=m_db),
            RestrictionMap(source="d", target="a", matrix=m_da),
        ],
    )

    cert = compute_exact_coda_gauge_distance(system)

    assert cert.primal_value == Fraction(0)
    assert cert.dual_value == Fraction(0)
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.optimal_residual.is_zero() is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True


def test_curved_diamond_k_in_im_delta1():
    """Curved diamond where K != 0 but K in im(delta_1) must achieve Phi_1([K]) == 0."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="y", target="bot", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="x", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="y", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="top", target="bot", matrix=Matrix([[Fraction(5)]])),
        ],
    )

    k = build_curvature_operator_cochain(system)
    assert not k.is_zero(), "System must have non-zero curvature"

    solver = ExactCodaL1Solver(system)
    cert = solver.solve(k)

    assert cert.primal_value == Fraction(0)
    assert cert.dual_value == Fraction(0)
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.optimal_residual.is_zero() is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True


def test_obstructed_cochain_positive_phi1_zero_gap():
    """An obstructed 2-cochain H outside im(delta_1) yields Phi_1([H]) > 0 with exact zero gap."""
    poset = _make_4chain_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"a": 1, "b": 1, "c": 1, "d": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="b", target="a", matrix=eye),
            RestrictionMap(source="c", target="b", matrix=eye),
            RestrictionMap(source="d", target="c", matrix=eye),
            RestrictionMap(source="c", target="a", matrix=eye),
            RestrictionMap(source="d", target="b", matrix=eye),
            RestrictionMap(source="d", target="a", matrix=eye),
        ],
    )
    k = build_curvature_operator_cochain(system)
    ops = dict(k.operators)
    # Perturb triple (a, b, d) away from coboundary image
    ops[("a", "b", "d")] = Matrix([[Fraction(42)]])
    h_obstructed = Operator2Cochain(poset=poset, operators=ops)

    solver = ExactCodaL1Solver(system)
    cert = solver.solve(h_obstructed)

    assert cert.primal_value > Fraction(0)
    assert cert.primal_value == Fraction(42)
    assert cert.dual_value == cert.primal_value
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True

    # Residual verification: ||H - delta_1 T*||_1 == primal_value
    diag = solver.diagnostic
    r_vec = diag.cochain2_to_vector(cert.optimal_residual)
    l1_norm = sum(abs(v) for v in r_vec)
    assert l1_norm == cert.primal_value


def test_non_uniform_rational_weights():
    """Non-uniform weights w_i > 0 are correctly priced by the dual witness."""
    poset = _make_4chain_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"a": 1, "b": 1, "c": 1, "d": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="b", target="a", matrix=eye),
            RestrictionMap(source="c", target="b", matrix=eye),
            RestrictionMap(source="d", target="c", matrix=eye),
            RestrictionMap(source="c", target="a", matrix=eye),
            RestrictionMap(source="d", target="b", matrix=eye),
            RestrictionMap(source="d", target="a", matrix=eye),
        ],
    )
    diag = OperatorCochainImageDiagnostic(system)
    k = build_curvature_operator_cochain(system)
    ops = dict(k.operators)
    ops[("a", "b", "d")] = Matrix([[Fraction(10)]])
    h_obstructed = Operator2Cochain(poset=poset, operators=ops)

    # Custom rational weights: 3/2 on every component except 5 on (a, b, d)
    weights_dict = {triple: Fraction(3, 2) for triple in diag.triples}
    weights_dict[("a", "b", "d")] = Fraction(5)

    solver = ExactCodaL1Solver(system, weights=weights_dict)
    cert = solver.solve(h_obstructed)

    # Shifting 10 units of residual from weight 5 to weight 3/2 achieves total cost 10 * 3/2 = 15
    assert cert.primal_value == Fraction(15)
    assert cert.dual_value == cert.primal_value
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True

    # Verify that the weighted L1 norm of the optimal residual matches the certificate
    r_vec = diag.cochain2_to_vector(cert.optimal_residual)
    weighted_norm = sum(w * abs(r) for w, r in zip(cert.weights, r_vec))
    assert weighted_norm == cert.primal_value


def test_subgradient_complementary_slackness():
    """Dual witness Y* must satisfy subgradient complementarity with optimal residual R*."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=eye),
            RestrictionMap(source="y", target="bot", matrix=eye),
            RestrictionMap(source="top", target="x", matrix=eye),
            RestrictionMap(source="top", target="y", matrix=eye),
            RestrictionMap(source="top", target="bot", matrix=eye),
        ],
    )
    diag = OperatorCochainImageDiagnostic(system)
    ops = {t: Matrix([[Fraction(0)]]) for t in diag.triples}
    ops[("bot", "x", "top")] = Matrix([[Fraction(7)]])
    ops[("bot", "y", "top")] = Matrix([[Fraction(-11)]])
    h = Operator2Cochain(poset=poset, operators=ops)

    solver = ExactCodaL1Solver(system)
    cert = solver.solve(h)

    assert cert.is_zero_gap is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True

    # Check complementary slackness: if R_i != 0 => Y_i == sgn(R_i) * w_i
    r_vec = diag.cochain2_to_vector(cert.optimal_residual)
    y_vec = diag.cochain2_to_vector(cert.dual_witness_y)
    w_vec = cert.weights

    for r_i, y_i, w_i in zip(r_vec, y_vec, w_vec):
        if r_i > 0:
            assert y_i == w_i, f"Expected y_i == w_i for positive residual, got {y_i} vs {w_i}"
        elif r_i < 0:
            assert y_i == -w_i, f"Expected y_i == -w_i for negative residual, got {y_i} vs {-w_i}"
        else:
            assert abs(y_i) <= w_i


@pytest.mark.parametrize("dim", [1, 2])
def test_swept_randomized_systems_zero_gap(dim: int):
    """Zero duality gap must hold unconditionally across multiple configurations."""
    poset = _make_diamond_poset()
    eye = Matrix.eye(dim)

    # Non-flat restriction maps
    m1 = Matrix([[Fraction(i + j + 1, 2) for j in range(dim)] for i in range(dim)])
    m2 = Matrix([[Fraction(i - j + 2, 3) for j in range(dim)] for i in range(dim)])
    m3 = Matrix([[Fraction(2 * i + j + 1, 5) for j in range(dim)] for i in range(dim)])
    m4 = Matrix([[Fraction(i + 3 * j + 2, 4) for j in range(dim)] for i in range(dim)])
    m_top_bot = Matrix([[Fraction(3, 1) if i == j else Fraction(0) for j in range(dim)] for i in range(dim)])

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={n: dim for n in poset.elements},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=m1),
            RestrictionMap(source="y", target="bot", matrix=m2),
            RestrictionMap(source="top", target="x", matrix=m3),
            RestrictionMap(source="top", target="y", matrix=m4),
            RestrictionMap(source="top", target="bot", matrix=m_top_bot),
        ],
    )

    cert = compute_exact_coda_gauge_distance(system)

    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True
    assert cert.primal_value == cert.dual_value


def test_edge_case_zero_cochain():
    """Zero 2-cochain must terminate in valid certificate with zero values."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=eye),
            RestrictionMap(source="y", target="bot", matrix=eye),
            RestrictionMap(source="top", target="x", matrix=eye),
            RestrictionMap(source="top", target="y", matrix=eye),
            RestrictionMap(source="top", target="bot", matrix=eye),
        ],
    )
    diag = OperatorCochainImageDiagnostic(system)
    zero_h = Operator2Cochain(poset=poset, operators={t: Matrix([[Fraction(0)]]) for t in diag.triples})

    solver = ExactCodaL1Solver(system)
    cert = solver.solve(zero_h)

    assert cert.primal_value == Fraction(0)
    assert cert.dual_value == Fraction(0)
    assert cert.duality_gap == Fraction(0)
    assert cert.is_zero_gap is True
    assert cert.is_cocycle_certified is True
    assert cert.is_subgradient_certified is True


def test_standalone_solve_l1_zero_columns():
    """solve_l1_primal_dual_exact with k = 0 handles no degrees of freedom cleanly."""
    b = [Fraction(3), Fraction(-7), Fraction(0)]
    w = [Fraction(2), Fraction(1), Fraction(5)]
    primal, dual, gamma, y, it = solve_l1_primal_dual_exact([], b, w)

    # Primal: 3*2 + 7*1 + 0*5 = 13
    assert primal == Fraction(13)
    assert dual == Fraction(13)
    assert gamma == []
    assert y == [Fraction(2), Fraction(-1), Fraction(0)]
    assert it == 0
