"""Coverage tests for exact.py, exactsym.py, and edge branches in PO-001.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
import pytest

from cochain_complex import Cochain1, Cochain2, Section0Cochain
from covering_edge_poset import ComparablePair, CoverEdge, FinitePoset
import exact
from exact import (
    as_rational,
    check_2cell_coboundary_zero,
    exact_column,
    exact_equal,
    exact_matrix,
    exact_matrix_from_matrix,
    expression_text,
    l1_norm,
)
import exactsym as ex
from exactsym import Abs, Basic, Matrix, Max, Rational, Symbol, cos, exp, pi, simplify, sin, sqrt, symbols


def test_exact_as_rational():
    assert as_rational(5) == Rational(5)
    assert as_rational(Fraction(3, 4)) == Rational(3, 4)
    assert as_rational("7/8") == Rational(7, 8)
    assert as_rational(Rational(1, 2)) == Rational(1, 2)

    with pytest.raises(TypeError, match="Boolean values are not valid"):
        as_rational(True)
    with pytest.raises(TypeError, match="Boolean values are not valid"):
        as_rational(False)
    with pytest.raises(TypeError, match="exact arithmetic rejects"):
        as_rational(3.14)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exact arithmetic rejects"):
        as_rational(object())  # type: ignore[arg-type]


def test_exact_matrix_builders():
    empty = exact_matrix([])
    assert empty.shape == (0, 0)

    m = exact_matrix([[1, Fraction(2, 1)], ["3", Rational(4)]])
    assert m.shape == (2, 2)
    assert m[0, 0] == 1
    assert m[0, 1] == 2
    assert m[1, 0] == 3
    assert m[1, 1] == 4

    with pytest.raises(ValueError, match="equal length"):
        exact_matrix([[1, 2], [3]])

    m_copy = exact_matrix_from_matrix(m)
    assert m_copy == m

    col = exact_column([1, Fraction(2, 3), "4"])
    assert col.shape == (3, 1)
    assert col[1, 0] == Rational(2, 3)


def test_exact_2cell_coboundary():
    assert check_2cell_coboundary_zero(1, -3, 2) is True
    assert check_2cell_coboundary_zero(Fraction(1, 2), Fraction(1, 2), -1) is True
    assert check_2cell_coboundary_zero(1, 1, 1) is False


def test_exact_l1_norm():
    v = exact_column([1, -2, Fraction(3, 2)])
    norm = l1_norm(v)
    assert norm == Rational(9, 2)

    m = exact_matrix([[1, 2], [3, 4]])
    with pytest.raises(ValueError, match="expects a column vector"):
        l1_norm(m)


def test_exact_equal_and_expression_text():
    m1 = exact_matrix([[1, 2], [3, 4]])
    m2 = exact_matrix([[1, 2], [3, 4]])
    m3 = exact_matrix([[1, 2]])
    assert exact_equal(m1, m2) is True
    assert exact_equal(m1, m3) is False
    assert exact_equal(m1, Rational(5)) is False
    assert exact_equal(Rational(5), m1) is False

    b1 = sqrt(2) + 1
    b2 = 1 + sqrt(2)
    assert exact_equal(b1, b2) is True
    assert exact_equal(b1, sqrt(3)) is False

    t_m = expression_text(m1)
    assert "1" in t_m and "4" in t_m
    t_b = expression_text(b1)
    assert "sqrt(2)" in t_b
    assert expression_text("hello") == "hello"


def test_exactsym_float_firewall():
    with pytest.raises(TypeError, match="rejects float"):
        Matrix([[0.5]])
    with pytest.raises(TypeError):
        sqrt(2) + 0.5
    with pytest.raises(TypeError):
        Matrix([[1]]) * 0.5
    with pytest.raises(TypeError, match="rejects float"):
        Matrix([[1]]) + Matrix([[0.5]])


def test_exactsym_basic_edges():
    assert ex.Rational is Fraction
    with pytest.raises(TypeError):
        sqrt(2) + object()

    assert Rational(2) + True == 3
    assert Rational(2) + 3 == 5

    s = sqrt(2)
    assert isinstance(s, Basic)
    assert s.__add__(object()) is NotImplemented
    assert s.__sub__(object()) is NotImplemented
    assert s.__rsub__(object()) is NotImplemented
    assert s.__mul__(object()) is NotImplemented
    assert s.__truediv__(object()) is NotImplemented
    assert s.__eq__(object()) is NotImplemented
    assert s.__ne__(object()) is NotImplemented

    with pytest.raises(ValueError, match="negative"):
        sqrt(-4)
    with pytest.raises(TypeError, match="non-constant"):
        sqrt(Symbol("x"))

    with pytest.raises(TypeError, match="nonnegative integers"):
        sqrt(2) ** -1
    with pytest.raises(TypeError, match="nonnegative integers"):
        sqrt(2) ** 0.5

    with pytest.raises(ZeroDivisionError):
        Rational(1) / 0

    x = Symbol("x")
    with pytest.raises(TypeError, match="symbolic value"):
        Rational(1) / x
    with pytest.raises(TypeError, match="symbolic value"):
        1 / x

    assert +Rational(3) == 3
    assert abs(Rational(-3)) == 3
    assert Abs(-3) == 3
    assert Abs(sqrt(2)) == sqrt(2)

    with pytest.raises(TypeError, match="at least one argument"):
        Max()
    assert Max(1, 5, 3) == 5

    with pytest.raises(TypeError, match="nonempty strings"):
        Symbol("")
    with pytest.raises(TypeError, match="nonempty strings"):
        Symbol(None)  # type: ignore[arg-type]

    one = symbols("solo")
    assert str(one) == "solo"
    a, b = symbols("a b")
    assert str(a) == "a" and str(b) == "b"

    assert {str(sym) for sym in (x * a + b).free_symbols} == {"x", "a", "b"}
    assert sqrt(2).free_symbols == set()

    with pytest.raises(TypeError, match="plain symbol"):
        (x * x).diff(Rational(2))
    assert (x * x).diff(x) == 2 * x

    assert (x + 1).subs({x: 2}) == 3
    assert (x + 1).subs({"x": 2}) == 3
    with pytest.raises(TypeError, match="substitution keys"):
        (x + 1).subs({Rational(1): 2})  # type: ignore[dict-item]

    with pytest.raises(TypeError, match="free symbols"):
        bool(x < 1)

    assert Rational(1) < Rational(2)
    assert Rational(2) <= Rational(2)
    assert Rational(3) > Rational(2)
    assert Rational(2) >= Rational(2)
    assert sqrt(2) < 2
    assert sqrt(2) > 1

    zero = sqrt(2) * 0
    assert str(zero) == "0"
    assert zero == 0
    assert x - x == 0

    assert hash(Rational(4)) == hash(Rational(4))
    assert hash(Matrix([[1]])) == hash(Matrix([[1]]))

    assert exp(0) == 1
    assert exp(1) > 2
    assert exp(-1) < 1
    assert pi > 3
    assert pi < 4
    with pytest.raises(TypeError, match="non-constant"):
        exp(Symbol("x"))

    for k, expected_cos, expected_sin in [(0, 1, 0), (1, 0, 1), (2, -1, 0), (3, 0, -1)]:
        angle = pi * Rational(k) / 2
        assert cos(angle) == expected_cos
        assert sin(angle) == expected_sin

    with pytest.raises(TypeError, match="rational multiples"):
        cos(Rational(1))
    with pytest.raises(TypeError, match="rational multiples"):
        sin(Rational(1))
    with pytest.raises(TypeError, match="rational multiples"):
        cos(Symbol("x"))
    with pytest.raises(TypeError, match="rational multiples"):
        sin(Symbol("x"))


def test_exactsym_matrix_operations():
    with pytest.raises(TypeError, match="dimensions must be integers"):
        Matrix("a", "b", [1])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="data must be a list or tuple"):
        Matrix(1, 1, 5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="length does not match"):
        Matrix(2, 2, [1, 2, 3])
    with pytest.raises(TypeError, match="one data argument"):
        Matrix(1, 2, 3, 4)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="cannot build a Matrix"):
        Matrix(5)  # type: ignore[call-overload]
    with pytest.raises(ValueError, match="equal length"):
        Matrix([[1, 2], [3]])

    empty = Matrix([])
    assert empty.shape == (0, 0)
    assert len(empty) == 0

    m = Matrix([[1, 2], [3, 4]])
    assert m[0, 1] == 2
    assert m[3] == 4
    with pytest.raises(IndexError, match="out of range"):
        _ = m[9]
    with pytest.raises(TypeError, match="unsupported matrix index"):
        _ = m[object()]  # type: ignore[index]
    with pytest.raises(TypeError, match="index component"):
        _ = m[object(), 0]  # type: ignore[index]

    assert m[0:2, 0].shape == (2, 1)
    assert m[[0, 1], [1]].shape == (2, 1)
    sub_ext = m.extract([0, 1], [1])
    assert sub_ext == Matrix([[2], [4]])

    m[0, 1] = 9
    assert m[0, 1] == 9
    m[0, 1] = 2

    a = Matrix([[1, 2]])
    b = Matrix([[1], [2]])
    with pytest.raises(ValueError, match="differ"):
        _ = a + Matrix([[1, 2, 3]])
    with pytest.raises(ValueError, match="differ"):
        _ = a - Matrix([[1, 2, 3]])
    with pytest.raises(ValueError):
        _ = b * b

    assert (m * 2) == Matrix([[2, 4], [6, 8]])
    assert (2 * m) == Matrix([[2, 4], [6, 8]])
    assert (m / 2) == Matrix([[Rational(1, 2), 1], [Rational(3, 2), 2]])

    assert Matrix.vstack() == Matrix.zeros(0, 0)
    assert Matrix.vstack(Matrix([[1]]), Matrix([[2]])) == Matrix([[1], [2]])
    with pytest.raises(ValueError, match="equal column counts"):
        Matrix.vstack(Matrix([[1]]), Matrix([[1, 2]]))
    with pytest.raises(ValueError, match="equal row counts"):
        Matrix([[1]]).row_join(Matrix([[1], [2]]))
    assert Matrix([[1]]).row_join(Matrix([[2]])).shape == (1, 2)

    assert str(m).startswith("Matrix([")
    assert repr(m) == str(m)

    assert Matrix.zeros(0, 0).rank() == 0
    assert Matrix([[1, 2], [2, 4]]).rank() == 1
    assert Matrix([[1, 0], [0, 1]]).rank() == 2

    with pytest.raises(ValueError, match="only square"):
        Matrix([[1, 2]]).inv()
    with pytest.raises(ValueError, match="not invertible"):
        Matrix([[1, 2], [2, 4]]).inv()
    inverse = Matrix([[2, 0], [0, 4]]).inv()
    assert inverse == Matrix([[Rational(1, 2), 0], [0, Rational(1, 4)]])

    assert Matrix([[1, 0], [0, 1]]).nullspace() == []
    basis = Matrix([[1, 1]]).nullspace()
    assert len(basis) == 1
    assert (Matrix([[1, 1]]) * basis[0]) == Matrix([[0]])

    eye = Matrix.eye(2)
    with pytest.raises(ValueError, match="matching column vector"):
        eye.gauss_jordan_solve(Matrix([[1, 2]]))
    solution, params = eye.gauss_jordan_solve(Matrix([[3], [4]]))
    assert solution == Matrix([[3], [4]])
    assert params.shape == (0, 1)

    with pytest.raises(ValueError, match="no solution"):
        Matrix([[1], [0]]).gauss_jordan_solve(Matrix([[1], [1]]))

    solution, params = Matrix.zeros(1, 2).gauss_jordan_solve(Matrix([[0]]))
    assert solution == Matrix.zeros(2, 1)
    assert params == Matrix.zeros(2, 1)

    x, y = symbols("x y")
    with pytest.raises(ValueError, match="requires a vector"):
        Matrix([[x, y], [y, x]]).jacobian([x, y])
    jac = Matrix([[x * y], [x + y]]).jacobian([x, y])
    assert jac.shape == (2, 2)

    with pytest.raises(TypeError):
        Matrix([[x]]).rank()

    sym_mat = Matrix([[x, 1]])
    assert sym_mat.free_symbols == {x}
    assert sym_mat.subs({x: 5}) == Matrix([[5, 1]])

    doubled = m.applyfunc(lambda v: v * 2)
    assert doubled == Matrix([[2, 4], [6, 8]])

    assert m.T == Matrix([[1, 3], [2, 4]])
    assert m.rows == 2
    assert m.cols == 2
    assert m.row(0) == [1, 2]


def test_cochain_and_poset_edges():
    with pytest.raises(ValueError, match="reflexive"):
        CoverEdge("a", "a")
    ce = CoverEdge("a", "b")
    assert ce != object()
    assert ce == CoverEdge("a", "b")

    cp = ComparablePair("a", "b")
    assert cp != object()
    assert cp == ComparablePair("a", "b")

    with pytest.raises(ValueError, match="at least one element"):
        FinitePoset([], [])
    with pytest.raises(ValueError, match="not in poset"):
        FinitePoset(["a"], [("a", "b")])

    poset = FinitePoset(["a", "b"], [("a", "b")])
    assert poset.strict_comparable_pairs() == (ComparablePair("a", "b"),)
    assert poset.saturated_chains("a", "a") == [("a",)]
    assert poset.saturated_chains("b", "a") == []
    assert poset.is_diamond("a", "b", "b", "c") is False

    with pytest.raises(ValueError, match="missing 0-cochain value"):
        Section0Cochain(poset, {"a": Matrix([[1]])})
    s1 = Section0Cochain(poset, {"a": Matrix([[1]]), "b": Matrix([[2]])})
    assert s1 != object()
    poset2 = FinitePoset(["a", "c"], [("a", "c")])
    s2 = Section0Cochain(poset2, {"a": Matrix([[1]]), "c": Matrix([[2]])})
    assert s1 != s2

    with pytest.raises(ValueError, match="missing 1-cochain value"):
        Cochain1(poset, {("a", "a"): Matrix([[1]])})
    c1 = Cochain1(poset, {("a", "a"): Matrix([[1]]), ("a", "b"): Matrix([[2]]), ("b", "b"): Matrix([[3]])})
    assert c1 != object()

    c2_a = Cochain2(poset, {("a", "a", "a"): Matrix([[1]])})
    assert c2_a != object()
    c2_b = Cochain2(poset, {("a", "a", "b"): Matrix([[1]])})
    assert c2_a != c2_b
