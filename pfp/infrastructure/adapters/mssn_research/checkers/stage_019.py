"""Target checker of record for MSS-019, row 19 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 19): compute the exact polynomial from a finite matrix and
retain its scope. Negative instance: an irrational pole rounded to a rational
is rejected.

Input (closed): ``{"matrix": [[q]], "coefficients": [q], "roots": [q],
"enclosures": [[q, q]], "scope": str}``. ``coefficients`` is the
characteristic polynomial det(xI - A), highest degree first (so it is monic
and has n + 1 entries). The reciprocal det(I - zA) has the same coefficients
in the opposite order, so its poles are the reciprocals of these roots.

The polynomial is computed by the Faddeev-LeVerrier recursion over the
rationals, never read. A rational root claim must be an exact root. An
irrational root may be claimed only by a rational enclosure [lo, hi], lo < hi,
with a sign change of the polynomial across it. The scope is derived from the
evidence object: a finite matrix supports exactly ``finite_matrix``.

Clauses:

- C1 ``R019_POLYNOMIAL_MISMATCH``: the declared coefficients are not the
  recomputed characteristic polynomial (a wrong degree included);
- C2 ``R019_ROUNDED_ROOT``: a claimed rational root is not a root (the
  negative: an irrational root rounded to a rational);
- C3 ``R019_ENCLOSURE_INVALID``: an enclosure shows no sign change;
- C4 ``R019_SCOPE_ESCALATION``: the declared scope exceeds the finite matrix.
"""

STAGE = 19
ROW_SHA256 = "sha256:0cc789afa3d2ab5445e4ec9ff02c76901638a08678e7751da2a1ea775bd70e99"
FIELDS = ("coefficients", "enclosures", "matrix", "roots", "scope")
CLAUSES = (
    ("C1", "R019_POLYNOMIAL_MISMATCH"),
    ("C2", "R019_ROUNDED_ROOT"),
    ("C3", "R019_ENCLOSURE_INVALID"),
    ("C4", "R019_SCOPE_ESCALATION"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "coefficients": ["1/1", "-1/1", "-1/1"],
    "enclosures": [],
    "matrix": [["1/1", "1/1"], ["1/1", "0/1"]],
    "roots": ["809/500"],
    "scope": "finite_matrix",
}
OWN_NEGATIVE_CODE = "R019_ROUNDED_ROOT"
DERIVED_SCOPE = "finite_matrix"


def characteristic(matrix):
    """det(xI - A), highest degree first, by Faddeev-LeVerrier over the rationals."""
    n = len(matrix)
    coefficients = [Fraction(1)]
    product = [[Fraction(0)] * n for _ in range(n)]
    for k in range(1, n + 1):
        previous = coefficients[-1]
        product = [
            [sum((matrix[i][t] * product[t][j] for t in range(n)), Fraction(0)) + (previous if i == j else 0)
             for j in range(n)]
            for i in range(n)
        ]
        trace = sum((sum((matrix[i][t] * product[t][i] for t in range(n)), Fraction(0)) for i in range(n)), Fraction(0))
        coefficients.append(-trace / k)
    return coefficients


def _value(coefficients, x):
    out = Fraction(0)
    for coefficient in coefficients:
        out = out * x + coefficient
    return out


def _decide(payload):
    rows = _seq(payload["matrix"])
    n = len(rows)
    _require(n >= 1, "R_SCHEMA")
    matrix = _matrix(rows, columns=n)
    _require(isinstance(payload["scope"], str), "R_SCHEMA")
    _require(payload["scope"] == DERIVED_SCOPE, "R019_SCOPE_ESCALATION")
    declared = _rats(payload["coefficients"])
    polynomial = characteristic(matrix)
    _require(declared == polynomial, "R019_POLYNOMIAL_MISMATCH")
    for root in _rats(payload["roots"]):
        _require(_value(polynomial, root) == 0, "R019_ROUNDED_ROOT")
    for enclosure in _seq(payload["enclosures"]):
        low, high = _rats(enclosure, 2)
        _require(low < high, "R_SCHEMA")
        _require(_value(polynomial, low) * _value(polynomial, high) < 0, "R019_ENCLOSURE_INVALID")
