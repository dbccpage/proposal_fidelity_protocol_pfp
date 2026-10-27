"""Unit tests for the curved bicomplex and operator derivation identities (PO-001 v2.0).

AuthorityEffect: None.

Verifies:
1. Theorem 4.1: delta_2(delta_1(T)) == [K, T] identically across all quadruples.
2. Canonical scalar counterexample (Theorem 3.7) evaluating to 6 on both sides.
3. Non-flat diamond poset with 1D, 2D, and 3D matrix fibers.
4. Flat restriction systems recovering standard nilpotency delta_2(delta_1(T)) == 0.
5. 5-node chain poset under arbitrary non-commuting rational restrictions.
6. The residual 3-cochain delta_2(delta_1(T)) - [K, T] is identically zero in all cases.
"""

from fractions import Fraction
import pytest

from covering_edge_poset import FinitePoset
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cohomology_quotient import Operator1Cochain
from curved_bicomplex import (
    CurvedPosetBicomplex,
    compute_curvature_commutator_3cochain,
    compute_curved_derivation_3cochain,
    compute_curved_derivation_residual_3cochain,
    verify_curved_derivation_identity,
)


def _make_diamond_poset() -> FinitePoset:
    """Diamond poset: bot <= x <= top, bot <= y <= top."""
    return FinitePoset(
        elements=["bot", "x", "y", "top"],
        relations=[("bot", "x"), ("bot", "y"), ("x", "top"), ("y", "top")],
    )


def _make_4chain_poset() -> FinitePoset:
    """Linear 4-node chain: a <= b <= c <= d."""
    return FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )


def test_canonical_scalar_counterexample_residual_6():
    """Verify Theorem 3.7 & Theorem 4.1 on the canonical scalar 4-chain.

    In this system:
    r_{b, a} = 2, r_{c, b} = 3, r_{c, a} = 0, so K_{c, b, a} = 2*3 - 0 = 6.
    T_{d, c} = 1, and all other T entries are 0.
    Therefore:
    delta_2(delta_1(T))_{d, c, b, a} = 6
    [K, T]_{d, c, b, a} = K_{c, b, a} * T_{d, c} - T_{b, a} * K_{d, c, b} = 6 * 1 - 0 = 6.
    Both evaluate to exactly 6, and their difference is 0.
    """
    poset = _make_4chain_poset()
    zero = Matrix([[Fraction(0)]])
    one = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={node: 1 for node in poset.elements},
        restrictions=[
            *[
                RestrictionMap(source=node, target=node, matrix=one)
                for node in poset.elements
            ],
            RestrictionMap(source="b", target="a", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="c", target="b", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="d", target="c", matrix=one),
            RestrictionMap(source="c", target="a", matrix=zero),
            RestrictionMap(source="d", target="b", matrix=zero),
            RestrictionMap(source="d", target="a", matrix=zero),
        ],
    )
    t_ops = {
        (p, q): zero
        for p in poset.elements
        for q in poset.elements
        if poset.is_le(p, q)
    }
    t_ops[("c", "d")] = one
    t = Operator1Cochain(poset=poset, operators=t_ops)

    bicomplex = CurvedPosetBicomplex.from_system(system)
    assert not bicomplex.is_flat()
    assert bicomplex.curvature_l1_norm() > 0

    matches, delta2_delta1_t, comm = verify_curved_derivation_identity(system, t)
    assert matches, "delta_2(delta_1(T)) must match [K, T] identically"

    # Verify specific value on the quadruple (a, b, c, d)
    val_lhs = delta2_delta1_t("a", "b", "c", "d")
    val_rhs = comm("a", "b", "c", "d")
    assert val_lhs == Matrix([[Fraction(6)]])
    assert val_rhs == Matrix([[Fraction(6)]])

    # Residual 3-cochain is identically zero
    residual = compute_curved_derivation_residual_3cochain(system, t)
    assert residual.is_zero()


def test_nonflat_diamond_scalar_fibers():
    """Verify delta_2(delta_1(T)) == [K, T] on a non-flat diamond with 1D fibers."""
    poset = _make_diamond_poset()
    one = Matrix([[Fraction(1)]])

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={node: 1 for node in poset.elements},
        restrictions=[
            *[
                RestrictionMap(source=node, target=node, matrix=one)
                for node in poset.elements
            ],
            RestrictionMap(source="x", target="bot", matrix=Matrix([[Fraction(3, 2)]])),
            RestrictionMap(source="y", target="bot", matrix=Matrix([[Fraction(4, 3)]])),
            RestrictionMap(source="top", target="x", matrix=Matrix([[Fraction(5, 7)]])),
            RestrictionMap(source="top", target="y", matrix=Matrix([[Fraction(2, 5)]])),
            RestrictionMap(source="top", target="bot", matrix=Matrix([[Fraction(1, 10)]])),
        ],
    )

    t_ops = {
        (p, q): Matrix([[Fraction(2)]])
        for p in poset.elements
        for q in poset.elements
        if poset.is_le(p, q)
    }
    t = Operator1Cochain(poset=poset, operators=t_ops)

    bicomplex = CurvedPosetBicomplex.from_system(system)
    assert not bicomplex.is_flat()

    matches, delta2_delta1_t, comm = verify_curved_derivation_identity(system, t)
    assert matches
    assert not delta2_delta1_t.is_zero()
    assert not comm.is_zero()

    residual = compute_curved_derivation_residual_3cochain(system, t)
    assert residual.is_zero()


def test_nonflat_diamond_matrix_2x2_fibers():
    """Verify delta_2(delta_1(T)) == [K, T] on a non-flat diamond with 2x2 matrix fibers."""
    poset = _make_diamond_poset()
    eye2 = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])

    r_top_x = RestrictionMap(
        source="top",
        target="x",
        matrix=Matrix([[Fraction(1, 2), Fraction(1, 3)], [Fraction(1, 4), Fraction(1)]]),
    )
    r_top_y = RestrictionMap(
        source="top",
        target="y",
        matrix=Matrix([[Fraction(1), Fraction(2)], [Fraction(-1), Fraction(1)]]),
    )
    r_x_bot = RestrictionMap(
        source="x",
        target="bot",
        matrix=Matrix([[Fraction(2), Fraction(-1)], [Fraction(1, 2), Fraction(3)]]),
    )
    r_y_bot = RestrictionMap(
        source="y",
        target="bot",
        matrix=Matrix([[Fraction(1), Fraction(1, 2)], [Fraction(0), Fraction(1)]]),
    )
    r_top_bot = RestrictionMap(
        source="top",
        target="bot",
        matrix=Matrix([[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]),
    )

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 2, "x": 2, "y": 2, "top": 2},
        restrictions=[
            RestrictionMap(source="bot", target="bot", matrix=eye2),
            RestrictionMap(source="x", target="x", matrix=eye2),
            RestrictionMap(source="y", target="y", matrix=eye2),
            RestrictionMap(source="top", target="top", matrix=eye2),
            r_x_bot,
            r_y_bot,
            r_top_x,
            r_top_y,
            r_top_bot,
        ],
    )

    t_ops = {}
    for p in poset.elements:
        for q in poset.elements:
            if poset.is_le(p, q):
                t_ops[(p, q)] = Matrix(
                    [[Fraction(1, 3), Fraction(-2, 5)], [Fraction(1, 7), Fraction(4, 3)]]
                )

    t = Operator1Cochain(poset=poset, operators=t_ops)
    bicomplex = CurvedPosetBicomplex.from_system(system)

    assert not bicomplex.is_flat()
    assert bicomplex.verify_identity(t)

    residual = compute_curved_derivation_residual_3cochain(system, t)
    assert residual.is_zero()


def test_nonflat_diamond_matrix_3x3_fibers():
    """Verify delta_2(delta_1(T)) == [K, T] with 3x3 matrix fibers."""
    poset = _make_diamond_poset()

    def eye3():
        return Matrix([
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ])

    def rand_mat(offset: int):
        return Matrix([
            [Fraction(offset, 2), Fraction(1, 3), Fraction(-1, 4)],
            [Fraction(2, 5), Fraction(offset, 3), Fraction(1, 2)],
            [Fraction(-1, 2), Fraction(3, 4), Fraction(offset, 5)],
        ])

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={node: 3 for node in poset.elements},
        restrictions=[
            *[RestrictionMap(source=n, target=n, matrix=eye3()) for n in poset.elements],
            RestrictionMap(source="x", target="bot", matrix=rand_mat(1)),
            RestrictionMap(source="y", target="bot", matrix=rand_mat(2)),
            RestrictionMap(source="top", target="x", matrix=rand_mat(3)),
            RestrictionMap(source="top", target="y", matrix=rand_mat(4)),
            RestrictionMap(source="top", target="bot", matrix=rand_mat(0)),
        ],
    )

    t_ops = {
        (p, q): rand_mat(7)
        for p in poset.elements
        for q in poset.elements
        if poset.is_le(p, q)
    }
    t = Operator1Cochain(poset=poset, operators=t_ops)

    bicomplex = CurvedPosetBicomplex.from_system(system)
    assert not bicomplex.is_flat()
    assert bicomplex.verify_identity(t)

    residual = compute_curved_derivation_residual_3cochain(system, t)
    assert residual.is_zero()


def test_flat_diamond_recovers_coboundary_nilpotency():
    """On a flat restriction system (K == 0), both [K, T] and delta_2(delta_1(T)) vanish identically."""
    poset = _make_diamond_poset()
    eye2 = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])

    r_top_x = RestrictionMap(
        source="top",
        target="x",
        matrix=Matrix([[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1)]]),
    )
    r_top_y = RestrictionMap(
        source="top",
        target="y",
        matrix=Matrix([[Fraction(1), Fraction(1)], [Fraction(0), Fraction(1)]]),
    )
    r_x_bot = RestrictionMap(
        source="x",
        target="bot",
        matrix=Matrix([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]]),
    )
    r_y_bot = RestrictionMap(
        source="y",
        target="bot",
        matrix=Matrix([[Fraction(1), Fraction(-1)], [Fraction(0), Fraction(1)]]),
    )
    # Composite: r_{x, bot} * r_{top, x} = r_{y, bot} * r_{top, y} = [[1, 0], [0, 1]]
    r_top_bot = RestrictionMap(
        source="top",
        target="bot",
        matrix=Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]),
    )

    flat_system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 2, "x": 2, "y": 2, "top": 2},
        restrictions=[
            RestrictionMap(source="bot", target="bot", matrix=eye2),
            RestrictionMap(source="x", target="x", matrix=eye2),
            RestrictionMap(source="y", target="y", matrix=eye2),
            RestrictionMap(source="top", target="top", matrix=eye2),
            r_x_bot,
            r_y_bot,
            r_top_x,
            r_top_y,
            r_top_bot,
        ],
    )

    t_ops = {
        (p, q): Matrix([[Fraction(1, 3), Fraction(-2, 5)], [Fraction(1, 7), Fraction(4, 3)]])
        for p in poset.elements
        for q in poset.elements
        if poset.is_le(p, q)
    }
    t = Operator1Cochain(poset=poset, operators=t_ops)

    bicomplex = CurvedPosetBicomplex.from_system(flat_system)
    assert bicomplex.is_flat()
    assert bicomplex.curvature_l1_norm() == Fraction(0)

    # In a flat complex, both the commutator and the coboundary composition vanish identically
    comm = bicomplex.evaluate_commutator(t)
    derivation = bicomplex.evaluate_derivation(t)
    assert comm.is_zero(), "[K, T] must vanish when K == 0"
    assert derivation.is_zero(), "delta_2(delta_1(T)) must vanish when K == 0"
    assert bicomplex.verify_identity(t)


def test_linear_5chain_arbitrary_matrices():
    """Verify delta_2(delta_1(T)) == [K, T] on a 5-element chain with arbitrary matrices."""
    poset = FinitePoset(
        elements=["0", "1", "2", "3", "4"],
        relations=[("0", "1"), ("1", "2"), ("2", "3"), ("3", "4")],
    )
    dim = 2
    eye = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])

    restrictions = []
    for p in poset.elements:
        for q in poset.elements:
            if p == q:
                restrictions.append(RestrictionMap(source=p, target=q, matrix=eye))
            elif poset.is_le(p, q):
                ip, iq = int(p), int(q)
                m = Matrix([
                    [Fraction(ip + 1, iq + 2), Fraction(iq, ip + 3)],
                    [Fraction(-ip, iq + 1), Fraction(iq + 2, ip + 4)],
                ])
                restrictions.append(RestrictionMap(source=q, target=p, matrix=m))

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={n: dim for n in poset.elements},
        restrictions=restrictions,
    )

    t_ops = {}
    for p in poset.elements:
        for q in poset.elements:
            if poset.is_le(p, q):
                ip, iq = int(p), int(q)
                t_ops[(p, q)] = Matrix([
                    [Fraction(ip * iq, 7), Fraction(1, iq + 1)],
                    [Fraction(-1, ip + 2), Fraction(ip + iq, 5)],
                ])

    t = Operator1Cochain(poset=poset, operators=t_ops)
    bicomplex = CurvedPosetBicomplex.from_system(system)

    assert not bicomplex.is_flat()
    assert bicomplex.verify_identity(t)

    residual = compute_curved_derivation_residual_3cochain(system, t)
    assert residual.is_zero()
