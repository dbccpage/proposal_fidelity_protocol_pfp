"""Target checker of record for MSS-010, row 10 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 10): prevent a discrete spectral claim becoming a continuum
assertion. Negative instance (paraphrased): a pole of a finite graph's
reciprocal-determinant function, relabelled as a zero of a continuum function,
is rejected.

Input (closed): ``{"matrix": [[nat]], "claim": {"kind": str, "scope": str,
"value": "num/den"}}``. ``matrix`` is the evidence: a square nonnegative
integer matrix, a finite carrier's adjacency.

The fence reads nothing the candidate declares about scope. The scope is
derived from the evidence object: a finite integer matrix supports exactly the
scope ``finite_carrier`` and exactly the kind ``reciprocal_pole``, a value u
with det(I - uA) = 0, recomputed over the rationals.

Clauses:

- C1 ``R010_CONTINUUM_CLAIM``: the claim's kind is anything but a reciprocal
  pole of this matrix (the negative's relabelling);
- C2 ``R010_SCOPE_ESCALATION``: the declared scope exceeds the derived one;
- C3 ``R010_NOT_A_POLE``: det(I - uA) is not zero at the claimed value.
"""

STAGE = 10
ROW_SHA256 = "sha256:228095ac746ff94e3d47557eb67177ede412f8583f31798706e7a67c0d123b11"
FIELDS = ("claim", "matrix")
CLAUSES = (
    ("C1", "R010_CONTINUUM_CLAIM"),
    ("C2", "R010_SCOPE_ESCALATION"),
    ("C3", "R010_NOT_A_POLE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "claim": {"kind": "continuum_zero", "scope": "finite_carrier", "value": "1/1"},
    "matrix": [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
}
OWN_NEGATIVE_CODE = "R010_CONTINUUM_CLAIM"
DERIVED_KIND = "reciprocal_pole"


def _det(matrix):
    rows = [list(row) for row in matrix]
    size, out = len(rows), Fraction(1)
    for col in range(size):
        pivot = next((r for r in range(col, size) if rows[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            rows[col], rows[pivot] = rows[pivot], rows[col]
            out = -out
        out *= rows[col][col]
        for r in range(col + 1, size):
            factor = rows[r][col] / rows[col][col]
            rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col])]
    return out


def _decide(payload):
    rows = _seq(payload["matrix"])
    size = len(rows)
    matrix = [[_nat(x) for x in _seq(row, size)] for row in rows]
    _require(size >= 1, "R_SCHEMA")
    derived_scope = "finite_carrier"
    claim = payload["claim"]
    _require(isinstance(claim, dict) and set(claim) == {"kind", "scope", "value"}, "R_SCHEMA")
    _require(isinstance(claim["kind"], str) and isinstance(claim["scope"], str), "R_SCHEMA")
    _require(claim["kind"] == DERIVED_KIND, "R010_CONTINUUM_CLAIM")
    _require(claim["scope"] == derived_scope, "R010_SCOPE_ESCALATION")
    u = _rat(claim["value"])
    shifted = [[Fraction(int(i == j)) - u * matrix[i][j] for j in range(size)] for i in range(size)]
    _require(_det(shifted) == 0, "R010_NOT_A_POLE")
