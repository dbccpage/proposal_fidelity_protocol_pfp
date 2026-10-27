"""Targeted tests for the operator cocycle and image diagnostics.

Verifies:
1. Theorem 3.6: delta_2(K) == 0 unconditionally across quadruples.
2. Flat systems make delta_2(delta_1(T)) vanish in the tested finite model.
3. Exact rational membership in im(delta_1).
4. A non-flat counterexample where delta_2(delta_1(T)) is nonzero.
"""

from fractions import Fraction
import pytest

from covering_edge_poset import FinitePoset
from restriction_system import RestrictionMap, RestrictionSystem
from curvature_cochain import compute_curvature_operator
from exactsym import Matrix
from cohomology_quotient import (
    Operator1Cochain,
    Operator2Cochain,
    Operator3Cochain,
    operator_coboundary_delta1,
    operator_coboundary_delta2,
    build_curvature_operator_cochain,
    verify_unconditional_operator_cocycle,
    OperatorCochainImageDiagnostic,
    _solve_linear_system_exact,
)


def _make_diamond_poset() -> FinitePoset:
    """Diamond poset: bot <= x <= top, bot <= y <= top."""
    return FinitePoset(
        elements=["bot", "x", "y", "top"],
        relations=[("bot", "x"), ("bot", "y"), ("x", "top"), ("y", "top")],
    )


def test_operator_cocycle_identity_diamond():
    """Verify delta_2(K) == 0 unconditionally on the diamond poset."""
    poset = _make_diamond_poset()
    r_top_x = RestrictionMap(source="top", target="x", matrix=Matrix([[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(1)]]))
    r_top_y = RestrictionMap(source="top", target="y", matrix=Matrix([[Fraction(1), Fraction(1)], [Fraction(0), Fraction(1)]]))
    r_x_bot = RestrictionMap(source="x", target="bot", matrix=Matrix([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]]))
    r_y_bot = RestrictionMap(source="y", target="bot", matrix=Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]))
    r_top_bot = RestrictionMap(source="top", target="bot", matrix=Matrix([[Fraction(3), Fraction(0)], [Fraction(0), Fraction(2)]]))

    eye2 = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])

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

    is_zero, delta2_k = verify_unconditional_operator_cocycle(system)
    assert is_zero, "delta_2(K) must vanish identically on all quadruples"


def test_operator_cocycle_identity_linear_chain():
    """Verify delta_2(K) == 0 on a 4-element chain A <= B <= C <= D with arbitrary matrices."""
    poset = FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )

    eye = Matrix([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])
    m_ba = Matrix([[Fraction(3, 1), Fraction(-1, 1)], [Fraction(1, 2), Fraction(2, 1)]])
    m_cb = Matrix([[Fraction(2, 1), Fraction(1, 1)], [Fraction(0, 1), Fraction(1, 2)]])
    m_dc = Matrix([[Fraction(1, 2), Fraction(1, 3)], [Fraction(2, 5), Fraction(3, 4)]])

    m_ca = Matrix([[Fraction(5, 1), Fraction(2, 1)], [Fraction(1, 3), Fraction(4, 1)]])
    m_db = Matrix([[Fraction(1, 7), Fraction(2, 3)], [Fraction(3, 5), Fraction(1, 1)]])
    m_da = Matrix([[Fraction(2, 9), Fraction(1, 4)], [Fraction(4, 5), Fraction(-1, 3)]])

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"a": 2, "b": 2, "c": 2, "d": 2},
        restrictions=[
            RestrictionMap(source="a", target="a", matrix=eye),
            RestrictionMap(source="b", target="b", matrix=eye),
            RestrictionMap(source="c", target="c", matrix=eye),
            RestrictionMap(source="d", target="d", matrix=eye),
            RestrictionMap(source="b", target="a", matrix=m_ba),
            RestrictionMap(source="c", target="b", matrix=m_cb),
            RestrictionMap(source="d", target="c", matrix=m_dc),
            RestrictionMap(source="c", target="a", matrix=m_ca),
            RestrictionMap(source="d", target="b", matrix=m_db),
            RestrictionMap(source="d", target="a", matrix=m_da),
        ],
    )

    is_zero, delta2_k = verify_unconditional_operator_cocycle(system)
    assert is_zero


def test_delta2_delta1_chain_complex_on_flat():
    """Verify delta_2(delta_1 T) == 0 for arbitrary T when the restriction system is flat."""
    poset = FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )
    eye = Matrix([[Fraction(1)]])
    m_ba = Matrix([[Fraction(2)]])
    m_cb = Matrix([[Fraction(3)]])
    m_dc = Matrix([[Fraction(5)]])
    m_ca = m_ba * m_cb  # flat: 6
    m_db = m_cb * m_dc  # flat: 15
    m_da = m_ba * m_db  # flat: 30

    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"a": 1, "b": 1, "c": 1, "d": 1},
        restrictions=[
            RestrictionMap(source="a", target="a", matrix=eye),
            RestrictionMap(source="b", target="b", matrix=eye),
            RestrictionMap(source="c", target="c", matrix=eye),
            RestrictionMap(source="d", target="d", matrix=eye),
            RestrictionMap(source="b", target="a", matrix=m_ba),
            RestrictionMap(source="c", target="b", matrix=m_cb),
            RestrictionMap(source="d", target="c", matrix=m_dc),
            RestrictionMap(source="c", target="a", matrix=m_ca),
            RestrictionMap(source="d", target="b", matrix=m_db),
            RestrictionMap(source="d", target="a", matrix=m_da),
        ],
    )

    t_ops = {
        ("a", "a"): Matrix([[Fraction(1)]]),
        ("b", "b"): Matrix([[Fraction(2)]]),
        ("c", "c"): Matrix([[Fraction(3)]]),
        ("d", "d"): Matrix([[Fraction(4)]]),
        ("a", "b"): Matrix([[Fraction(7)]]),
        ("b", "c"): Matrix([[Fraction(11)]]),
        ("c", "d"): Matrix([[Fraction(13)]]),
        ("a", "c"): Matrix([[Fraction(17)]]),
        ("b", "d"): Matrix([[Fraction(19)]]),
        ("a", "d"): Matrix([[Fraction(23)]]),
    }
    t = Operator1Cochain(poset=poset, operators=t_ops)
    d1_t = operator_coboundary_delta1(system, t)
    d2_d1_t = operator_coboundary_delta2(system, d1_t)

    assert d2_d1_t.is_zero(), "delta_2(delta_1 T) must vanish on flat restriction systems"


def test_flat_curvature_is_in_delta1_image():
    """The flat example has K in im(delta_1)."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source="bot", target="bot", matrix=eye),
            RestrictionMap(source="x", target="x", matrix=eye),
            RestrictionMap(source="y", target="y", matrix=eye),
            RestrictionMap(source="top", target="top", matrix=eye),
            RestrictionMap(source="x", target="bot", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="y", target="bot", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="x", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="y", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="top", target="bot", matrix=Matrix([[Fraction(6)]])),
        ],
    )

    space = OperatorCochainImageDiagnostic(system)
    is_triv, witness = space.is_curvature_trivial()
    assert is_triv is True
    assert witness is not None


def test_constructed_delta1_image_is_detected():
    """A cochain constructed as delta_1(T) is detected in the image."""
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    flat_system = RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source="bot", target="bot", matrix=eye),
            RestrictionMap(source="x", target="x", matrix=eye),
            RestrictionMap(source="y", target="y", matrix=eye),
            RestrictionMap(source="top", target="top", matrix=eye),
            RestrictionMap(source="x", target="bot", matrix=eye),
            RestrictionMap(source="y", target="bot", matrix=eye),
            RestrictionMap(source="top", target="x", matrix=eye),
            RestrictionMap(source="top", target="y", matrix=eye),
            RestrictionMap(source="top", target="bot", matrix=eye),
        ],
    )

    space = OperatorCochainImageDiagnostic(flat_system)
    t_ops = {
        ("bot", "bot"): Matrix([[Fraction(0)]]),
        ("x", "x"): Matrix([[Fraction(0)]]),
        ("y", "y"): Matrix([[Fraction(0)]]),
        ("top", "top"): Matrix([[Fraction(0)]]),
        ("bot", "x"): Matrix([[Fraction(1, 2)]]),
        ("bot", "y"): Matrix([[Fraction(-1, 3)]]),
        ("x", "top"): Matrix([[Fraction(3, 4)]]),
        ("y", "top"): Matrix([[Fraction(2, 5)]]),
        ("bot", "top"): Matrix([[Fraction(1, 6)]]),
    }
    t = Operator1Cochain(poset=poset, operators=t_ops)
    h_coboundary = operator_coboundary_delta1(flat_system, t)

    is_cob, witness = space.is_coboundary(h_coboundary)
    assert is_cob is True
    assert witness is not None


def test_cochain_outside_delta1_image_is_detected():
    """A perturbed cochain outside im(delta_1) is rejected."""
    poset = FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )
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
    space = OperatorCochainImageDiagnostic(system)
    k = build_curvature_operator_cochain(system)

    # Perturb a single triple away from the coboundary image
    ops = dict(k.operators)
    ops[("a", "b", "d")] = Matrix([[Fraction(100)]])
    h_perturbed = Operator2Cochain(poset=poset, operators=ops)

    is_cob, witness = space.is_coboundary(h_perturbed)
    assert is_cob is False, "Perturbed cochain must not be in im(delta_1)"
    assert witness is None


def test_exact_solver_searches_later_columns_for_a_pivot():
    """A zero leading column must not consume the only equation row."""
    a = Matrix([[Fraction(0), Fraction(1)]])
    b = [Fraction(1)]

    solution = _solve_linear_system_exact(a, b)

    assert solution is not None
    assert [
        sum(Fraction(a[r, c]) * solution[c] for c in range(a.cols))
        for r in range(a.rows)
    ] == b


def test_nonflat_delta2_delta1_has_curvature_residual():
    """im(delta_1) is not contained in ker(delta_2) for a non-flat system."""
    poset = FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )
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
    t_ops = {(a, b): zero for a, b in OperatorCochainImageDiagnostic(system).pairs}
    t_ops[("c", "d")] = one
    t = Operator1Cochain(poset=poset, operators=t_ops)

    residual = operator_coboundary_delta2(
        system, operator_coboundary_delta1(system, t)
    )

    assert residual("a", "b", "c", "d") == Matrix([[Fraction(6)]])
    assert not residual.is_zero()
