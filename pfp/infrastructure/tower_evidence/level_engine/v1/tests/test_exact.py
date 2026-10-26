"""Exact library: differential tests against fractions.Fraction on a seeded
corpus, golden vectors for the text form, and refusals by exact code."""

from __future__ import annotations

import random
from collections.abc import Callable
from fractions import Fraction

import pytest

from engine.errors import ExactError
from engine.exact import QI, Alg, Interval, Q, alg_cmp, alg_equal, alg_sign_of, isolate
from engine.exact import linalg as L
from engine.exact import poly as P
from engine.exact.q import fmt_q, parse_q
from engine.exact.qi import fmt_qi, parse_qi, qi_from_q

SEED = 20260924


def _corpus(n: int) -> list[tuple[int, int]]:
    rng = random.Random(SEED)
    out = []
    for _ in range(n):
        d = rng.randint(1, 60)
        out.append((rng.randint(-90, 90), d))
    return out


def _f(x: Q) -> Fraction:
    return Fraction(x.num, x.den)


def test_differential_against_fraction() -> None:
    xs = _corpus(120)
    for (a, b), (c, d) in zip(xs, xs[1:]):
        p, q = Q.of(a, b), Q.of(c, d)
        fp, fq = Fraction(a, b), Fraction(c, d)
        assert _f(p) == fp and _f(q) == fq
        assert _f(p + q) == fp + fq
        assert _f(p - q) == fp - fq
        assert _f(p * q) == fp * fq
        if c != 0:
            assert _f(p / q) == fp / fq
        assert (p < q) == (fp < fq) and (p <= q) == (fp <= fq)
        assert (p > q) == (fp > fq) and (p >= q) == (fp >= fq)
        assert (p == q) == (fp == fq)
        assert fmt_q(p) == f"{fp.numerator}/{fp.denominator}"


def test_golden_text_vectors() -> None:
    assert fmt_q(Q(5)) == "5/1"
    assert fmt_q(Q(0)) == "0/1"
    assert fmt_q(Q.of(-6, 4)) == "-3/2"
    assert parse_q("-3/2") == Q(-3, 2)
    assert str(Q(1, 3)) == "1/3" and repr(Q(1, 3)) == "Q(1, 3)"


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("5", "RR-PARSE"),
        ("0.5", "RR-PARSE"),
        ("1e3", "RR-PARSE"),
        ("+1/2", "RR-PARSE"),
        ("-0/1", "RR-PARSE"),
        ("1/0", "RR-PARSE"),
        ("2/4", "RR-NOT-REDUCED"),
    ],
)
def test_parse_refusals(text: str, code: str) -> None:
    with pytest.raises(ExactError) as e:
        parse_q(text)
    assert e.value.code == code


def test_float_refused_everywhere() -> None:
    floats: list[Callable[[], object]] = [
        lambda: Q(0.5, 1),  # type: ignore[arg-type]
        lambda: Q(1, 2.0),  # type: ignore[arg-type]
        lambda: parse_q(0.5),
    ]
    for bad in floats:
        with pytest.raises(ExactError) as e:
            bad()
        assert e.value.code == "RR-FLOAT"
    with pytest.raises(ExactError) as e:
        fmt_q(0.5)  # type: ignore[arg-type]
    assert e.value.code == "RR-FLOAT"
    with pytest.raises(ExactError) as e:
        QI(Q(1), 0.5)  # type: ignore[arg-type]
    assert e.value.code == "RR-FLOAT"
    with pytest.raises(ExactError) as e:
        Interval(Q(0), 1.0)  # type: ignore[arg-type]
    assert e.value.code == "RR-FLOAT"
    with pytest.raises(ExactError) as e:
        L.det([[0.5]])  # type: ignore[list-item]
    assert e.value.code == "RR-FLOAT"


def test_other_refusals() -> None:
    cases: list[tuple[Callable[[], object], str]] = [
        (lambda: Q(True, 1), "RR-NOT-INTEGER"),
        (lambda: Q(1, 0), "RR-DENOMINATOR"),
        (lambda: Q(2, 4), "RR-NOT-REDUCED"),
        (lambda: Q.of(1, 0), "RR-DENOMINATOR"),
        (lambda: Q(0).inv(), "RR-DIVISION-BY-ZERO"),
        (lambda: parse_q(3), "RR-PARSE"),
        (lambda: fmt_q("x"), "RR-PARSE"),  # type: ignore[arg-type]
        (lambda: parse_qi(["1/1"]), "RR-PARSE"),
        (lambda: QI(Q(0), Q(0)).inv(), "RR-DIVISION-BY-ZERO"),
    ]
    for fn, code in cases:
        with pytest.raises(ExactError) as e:
            fn()
        assert e.value.code == code
    with pytest.raises(AttributeError):
        Q(1).num = 2


def test_qi_against_complex_fraction_pairs() -> None:
    xs = _corpus(40)
    for (a, b), (c, d) in zip(xs[::2], xs[1::2]):
        z = QI(Q.of(a, b), Q.of(c, d))
        w = QI(Q.of(c, d + 1), Q.of(-a, b + 2))
        zr, zi, wr, wi = _f(z.re), _f(z.im), _f(w.re), _f(w.im)
        m = z * w
        assert (_f(m.re), _f(m.im)) == (zr * wr - zi * wi, zr * wi + zi * wr)
        assert z.conj().conj() == z
        assert (z * w).conj() == z.conj() * w.conj()
        assert _f(z.norm2()) == zr * zr + zi * zi
        if not z.is_zero():
            assert z * z.inv() == qi_from_q(Q(1))
        assert (z + w) - w == z and -(-z) == z
    assert parse_qi(fmt_qi(QI(Q(1, 2), Q(-3)))) == QI(Q(1, 2), Q(-3))


def test_polynomials_and_sturm() -> None:
    x2m2 = (Q(-2), Q(0), Q(1))
    assert P.root_count(x2m2, Q(-4), Q(4)) == 2
    assert P.root_count(x2m2, Q(0), Q(4)) == 1
    cubic = P.mul(P.mul((Q(-1), Q(1)), (Q(-2), Q(1))), (Q(-3), Q(1)))
    assert P.root_count(cubic, Q(0), Q(3)) == 3  # (0, 3] holds 1, 2, 3
    assert P.root_count(cubic, Q(1), Q(3)) == 2
    q, r = P.divmod_poly(cubic, (Q(-1), Q(1)))
    assert r == () and P.mul(q, (Q(-1), Q(1))) == cubic
    sq = P.mul(x2m2, x2m2)
    assert P.squarefree(sq) == x2m2
    assert P.degree(P.gcd_poly(cubic, (Q(-2), Q(1)))) == 1
    with pytest.raises(ExactError):
        P.root_count((), Q(0), Q(1))
    with pytest.raises(ExactError):
        P.root_count(x2m2, Q(1), Q(0))
    with pytest.raises(ExactError):
        P.divmod_poly(cubic, ())
    assert P.monic(()) == () and P.squarefree((Q(3),)) == (Q(1),)
    assert P.cauchy_bound((Q(5),)) == Q(1)
    assert P.mul((), cubic) == ()


def test_algebraic_numbers() -> None:
    roots = isolate((Q(-2), Q(0), Q(1)))
    assert len(roots) == 2
    neg, pos = roots
    assert alg_cmp(neg, pos) == -1 and alg_cmp(pos, neg) == 1 and alg_cmp(pos, pos) == 0
    same = Alg(pos.poly, Q(1), Q(2))
    assert alg_equal(pos, same) and not alg_equal(neg, pos)
    # sqrt2 against sqrt3: different polynomials, strict order
    r3 = isolate((Q(-3), Q(0), Q(1)))[1]
    assert alg_cmp(pos, r3) == -1 and not alg_equal(pos, r3)
    # the same number named by two different polynomials
    quartic = P.mul((Q(-2), Q(0), Q(1)), (Q(-3), Q(0), Q(1)))
    q_roots = isolate(quartic)
    assert len(q_roots) == 4
    assert sum(1 for r in q_roots if alg_equal(r, pos)) == 1
    # signs of polynomials at algebraic points
    assert alg_sign_of(pos, (Q(-3, 2), Q(1))) == -1
    assert alg_sign_of(pos, (Q(-1), Q(1))) == 1
    assert alg_sign_of(pos, (Q(-2), Q(0), Q(1))) == 0
    assert alg_sign_of(pos, ()) == 0
    enc = pos.refine().refine().enclosure()
    assert enc.contains(Q(141, 100)) and enc.width() < Q(4)
    assert isolate((Q(1), Q(0), Q(1))) == ()  # x^2 + 1 has no real root
    assert isolate((Q(7),)) == ()
    algs: list[Callable[[], object]] = [
        lambda: Alg((Q(3),), Q(0), Q(1)),
        lambda: Alg((Q(-4), Q(0), Q(2)), Q(0), Q(4)),
        lambda: Alg(P.mul((Q(-1), Q(1)), (Q(-1), Q(1))), Q(0), Q(2)),
        lambda: Alg((Q(-2), Q(0), Q(1)), Q(-4), Q(4)),
    ]
    for bad in algs:
        with pytest.raises(ExactError) as e:
            bad()
        assert e.value.code == "RR-ALG"


def test_intervals() -> None:
    a = Interval(Q(-1), Q(2))
    b = Interval(Q(3), Q(4))
    assert (a + b) == Interval(Q(2), Q(6))
    assert (a * b) == Interval(Q(-4), Q(8))
    assert a.contains(Q(0)) and not a.contains(Q(3))
    with pytest.raises(ExactError):
        Interval(Q(1), Q(0))


def test_linear_algebra() -> None:
    reg = [[Q(1), Q(1, 2), Q(1, 2)], [Q(1, 2), Q(1), Q(1, 2)], [Q(1, 2), Q(1, 2), Q(1)]]
    assert L.leading_minors(reg) == (Q(1), Q(3, 4), Q(1, 2))
    assert L.is_positive_definite(reg) and L.rank(reg) == 3
    assert L.char_poly(reg) == (Q(-1, 2), Q(9, 4), Q(-3), Q(1))
    ind = [[Q(1), Q(2), Q(2)], [Q(2), Q(1), Q(2)], [Q(2), Q(2), Q(1)]]
    assert L.det(ind) == Q(5) and L.first_nonpositive_minor(ind) == 2
    deg = [[Q(1), Q(0), Q(0)], [Q(0), Q(1), Q(0)], [Q(0), Q(0), Q(0)]]
    assert L.first_nonpositive_minor(deg) == 3 and L.rank(deg) == 2
    swap = [[Q(0), Q(1)], [Q(1), Q(0)]]
    assert L.det(swap) == Q(-1)
    assert L.rank([]) == 0 and L.rank([[Q(0), Q(0)]]) == 0
    with pytest.raises(ExactError):
        L.first_nonpositive_minor([[Q(1), Q(2)], [Q(0), Q(1)]])
    with pytest.raises(ExactError):
        L.det([[Q(1), Q(2)]])
    with pytest.raises(ExactError):
        L.as_matrix([[Q(1)], [Q(1), Q(2)]])
    # characteristic polynomial against the determinant at a few points
    for t in (Q(0), Q(1), Q(-2), Q(5, 3)):
        shifted = [[(t if i == j else Q(0)) - ind[i][j] for j in range(3)] for i in range(3)]
        assert P.evaluate(L.char_poly(ind), t) == L.det(shifted)
