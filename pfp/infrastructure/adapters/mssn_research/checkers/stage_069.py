"""Target checker of record for MSS-069, row 69 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 69): check a unique root in a rational interval, with exact
polynomial evaluation. Negative instance: an interval containing two roots is
rejected.

Input (closed): ``{"polynomial": [c0, c1, ...], "interval": [a, b],
"values": [p(a), p(b)]}``. Coefficients are canonical rationals in ascending
degree with a nonzero leading coefficient and degree >= 1; a < b. The pair
(p, [a, b]) names an algebraic real number when [a, b] isolates exactly one
root of p. ``values`` is the producer's evaluation of p at the two ends.

The checker builds the Sturm chain of p over exact rationals (p, p', then
negated remainders). Its last nonzero member is gcd(p, p') up to a unit, so
p is squarefree exactly when that member is constant; the number of distinct
real roots in (a, b) is then the drop in sign variations of the chain from a
to b.

Declared input class: rational polynomials of degree 1 to 12 with rational
interval ends. Arithmetic on algebraic numbers (sums, products, resultants)
is not in the class.

Clauses, decided in this order:

- C1 ``R069_NOT_SQUAREFREE``: gcd(p, p') is not constant (a repeated root);
- C2 ``R069_ENDPOINT_ROOT``: p vanishes at an end of the interval;
- C3 ``R069_NOT_ISOLATING``: the Sturm count on the interval is not exactly 1
  (the level's negative: x^2 - 2 on [-2, 2] has two roots);
- C4 ``R069_EVALUATION``: a claimed end value differs from the exact p(a) or
  p(b).
"""

STAGE = 69
ROW_SHA256 = "sha256:a0845413472dc9e661736f330614cd8b65764747a227cf335878d41f5ffe9813"
FIELDS = ("interval", "polynomial", "values")
CLAUSES = (
    ("C1", "R069_NOT_SQUAREFREE"),
    ("C2", "R069_ENDPOINT_ROOT"),
    ("C3", "R069_NOT_ISOLATING"),
    ("C4", "R069_EVALUATION"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"interval": ["-2/1", "2/1"], "polynomial": ["-2/1", "0/1", "1/1"], "values": ["2/1", "2/1"]}
OWN_NEGATIVE_CODE = "R069_NOT_ISOLATING"


def _trim(p):
    p = list(p)
    while p and p[-1] == 0:
        p.pop()
    return p


def _evaluate(p, x):
    total = Fraction(0)
    for c in reversed(p):
        total = total * x + c
    return total


def _remainder(num, den):
    num = list(num)
    while len(num) >= len(den) and num:
        factor = num[-1] / den[-1]
        shift = len(num) - len(den)
        for i, c in enumerate(den):
            num[shift + i] -= factor * c
        num = _trim(num)
    return num


def _chain(p):
    chain = [p, _trim([i * c for i, c in enumerate(p)][1:])]
    while chain[-1]:
        chain.append([-c for c in _remainder(chain[-2], chain[-1])])
    return chain[:-1]


def _variations(chain, x):
    signs = [v for v in (_evaluate(q, x) for q in chain) if v != 0]
    return sum(1 for u, v in zip(signs, signs[1:]) if (u > 0) != (v > 0))


def _decide(payload):
    p = _rats(payload["polynomial"])
    _require(2 <= len(p) <= 13 and p[-1] != 0, "R_SCHEMA")
    a, b = _rats(payload["interval"], 2)
    _require(a < b, "R_SCHEMA")
    values = _rats(payload["values"], 2)
    chain = _chain(p)
    _require(len(chain[-1]) == 1, "R069_NOT_SQUAREFREE")
    _require(_evaluate(p, a) != 0 and _evaluate(p, b) != 0, "R069_ENDPOINT_ROOT")
    _require(_variations(chain, a) - _variations(chain, b) == 1, "R069_NOT_ISOLATING")
    _require(values == [_evaluate(p, a), _evaluate(p, b)], "R069_EVALUATION")
