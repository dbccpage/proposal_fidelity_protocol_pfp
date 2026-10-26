"""Target checker of record for MSS-071, row 71 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 71): check quantified convergence and retained hypotheses.
Negative instance: a finite orbit count cannot imply analytic continuation.

Input (closed): ``{"numerator": [c], "denominator": [c], "limit": L,
"rate": C | null, "start": n0, "modulus": [[epsilon, N]], "checkpoints":
[[n, value]]}``. The sequence is a_n = P(n) / Q(n) for rational polynomials
P and Q (ascending coefficients). The claim is quantified: for every integer
n >= n0, Q(n) > 0 and |a_n - L| <= C / n; each modulus pair states that
n >= N gives |a_n - L| <= epsilon. The hypotheses n >= n0 and Q > 0 stay
inside the statement. Checkpoints are exact sample values only.

The checker decides the claim for every n >= n0, not on samples: each side
reduces to a polynomial R with R(n) >= 0 (or > 0) for all integers n >= n0,
which holds exactly when R is zero, or its leading coefficient is positive
and R is nonnegative at every integer from n0 up to its Cauchy root bound;
beyond that bound R has no root.

Declared input class: rational sequences P(n)/Q(n) of degree <= 8, n0 >= 1,
rates of the form C / n, with at most 10^5 integers below the Cauchy bound.
No limit object is formed and no statement beyond the bound C / n descends.

Clauses, decided in this order:

- C1 ``R071_CHECKPOINTS_ONLY``: no rate is given, so the claim rests on a
  finite table (the level's negative);
- C2 ``R071_DENOMINATOR``: Q(n) <= 0 for some integer n >= n0 (a hypothesis
  was dropped);
- C3 ``R071_BOUND_FAILS``: |a_n - L| > C / n for some integer n >= n0;
- C4 ``R071_MODULUS``: no modulus pair is given, or a pair has epsilon <= 0,
  N < n0, or C / N > epsilon;
- C5 ``R071_CHECKPOINT_MISMATCH``: a listed checkpoint value is not a_n.
"""

STAGE = 71
ROW_SHA256 = "sha256:f56364ce8c49204ca4e573728e0c85fd8336eb977fad6189d018f01b8082934b"
FIELDS = ("checkpoints", "denominator", "limit", "modulus", "numerator", "rate", "start")
CLAUSES = (
    ("C1", "R071_CHECKPOINTS_ONLY"),
    ("C2", "R071_DENOMINATOR"),
    ("C3", "R071_BOUND_FAILS"),
    ("C4", "R071_MODULUS"),
    ("C5", "R071_CHECKPOINT_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "checkpoints": [[1, "1/1"], [10, "2/5"], [100, "17/50"], [1000, "167/500"]],
    "denominator": ["0/1", "3/1"],
    "limit": "1/3",
    "modulus": [],
    "numerator": ["2/1", "1/1"],
    "rate": None,
    "start": 1,
}
OWN_NEGATIVE_CODE = "R071_CHECKPOINTS_ONLY"


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


def _combine(p, q, sign):
    size = max(len(p), len(q))
    p, q = p + [Fraction(0)] * (size - len(p)), q + [Fraction(0)] * (size - len(q))
    return _trim([a + sign * b for a, b in zip(p, q)])


def _holds(r, n0, strict):
    """R(n) >= 0 (or > 0) for every integer n >= n0, decided exactly."""
    r = _trim(r)
    if not r:
        return not strict
    if r[-1] < 0:
        return False
    bound = 1 + max((abs(c / r[-1]) for c in r[:-1]), default=Fraction(0))
    top = bound.numerator // bound.denominator + 1
    _require(top - n0 <= 100000, "R_SCHEMA")
    for n in range(n0, max(n0, top) + 1):
        value = _evaluate(r, n)
        if value < 0 or (strict and value == 0):
            return False
    return True


def _decide(payload):
    p, q = _trim(_rats(payload["numerator"])), _trim(_rats(payload["denominator"]))
    _require(q and len(p) <= 9 and len(q) <= 9, "R_SCHEMA")
    limit = _rat(payload["limit"])
    n0 = _nat(payload["start"])
    _require(n0 >= 1, "R_SCHEMA")
    modulus = []
    for item in _seq(payload["modulus"]):
        _seq(item, 2)
        modulus.append((_rat(item[0]), _nat(item[1])))
    checkpoints = []
    for item in _seq(payload["checkpoints"]):
        _seq(item, 2)
        checkpoints.append((_nat(item[0]), _rat(item[1])))
    rate = payload["rate"]
    _require(rate is not None, "R071_CHECKPOINTS_ONLY")
    rate = _rat(rate)
    _require(_holds(q, n0, True), "R071_DENOMINATOR")
    gap = _combine(p, [limit * c for c in q], -1)
    scaled_gap = [Fraction(0)] + gap
    allowance = [rate * c for c in q]
    _require(_holds(_combine(allowance, scaled_gap, -1), n0, False), "R071_BOUND_FAILS")
    _require(_holds(_combine(allowance, scaled_gap, 1), n0, False), "R071_BOUND_FAILS")
    _require(modulus, "R071_MODULUS")
    for epsilon, n in modulus:
        _require(epsilon > 0 and n >= n0 and rate <= epsilon * n, "R071_MODULUS")
    for n, value in checkpoints:
        denominator = _evaluate(q, n)
        _require(denominator != 0 and value == _evaluate(p, n) / denominator, "R071_CHECKPOINT_MISMATCH")
