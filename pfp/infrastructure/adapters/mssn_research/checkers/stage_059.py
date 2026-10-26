"""Target checker of record for MSS-059, row 59 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 59): recompute rational correlations and the declared
inequality bound. Negative instance: a bound violation is not inferred from a
receipt label alone.

Input (closed): ``{"near": [row, row], "far": [row, row], "correlations":
[[E00, E01], [E10, E11]], "total": S, "bound": B, "excess": X}``. Rows are
real unit rows of canonical rationals, one per setting. The producer claims:

- E_xy = near[x] . far[y] (recomputed as the exact dot product);
- S = E00 + E01 + E10 - E11 (recomputed from the recomputed E, never read from
  a label);
- B, the local bound: the maximum of a0 b0 + a0 b1 + a1 b0 - a1 b1 over all 16
  deterministic assignments of +-1 (recomputed by enumeration; it is 2, and
  mixtures cannot exceed it by linearity);
- X = S - B, the recomputed margin (positive when the rows exceed the local
  bound).

Declared input class: two parties, two settings each, outcomes +-1, and
correlations given by real rational unit rows of a common length. No
irrational ceiling on S is computed or claimed.

Clauses, decided in this order:

- C1 ``R059_NOT_UNIT``: a setting row does not have size exactly 1;
- C2 ``R059_CORRELATION``: a claimed E_xy differs from the dot product;
- C3 ``R059_TOTAL``: the claimed S differs from the recomputed total (the
  level's negative: a label S = 14/5 over correlations totalling 2);
- C4 ``R059_BOUND``: the claimed local bound differs from the enumerated one;
- C5 ``R059_EXCESS``: the claimed margin differs from S - B.
"""

STAGE = 59
ROW_SHA256 = "sha256:35fbdf13cea8b8ad8be3bd5a585b24e247b7b2f2df035eb4114237cd3d4dcc0d"
FIELDS = ("bound", "correlations", "excess", "far", "near", "total")
CLAUSES = (
    ("C1", "R059_NOT_UNIT"),
    ("C2", "R059_CORRELATION"),
    ("C3", "R059_TOTAL"),
    ("C4", "R059_BOUND"),
    ("C5", "R059_EXCESS"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "bound": "2/1",
    "correlations": [["1/1", "1/1"], ["0/1", "0/1"]],
    "excess": "4/5",
    "far": [["1/1", "0/1"], ["1/1", "0/1"]],
    "near": [["1/1", "0/1"], ["0/1", "1/1"]],
    "total": "14/5",
}
OWN_NEGATIVE_CODE = "R059_TOTAL"


def _decide(payload):
    near = [_rats(row) for row in _seq(payload["near"], 2)]
    far = [_rats(row) for row in _seq(payload["far"], 2)]
    width = len(near[0])
    _require(width >= 1 and all(len(row) == width for row in near + far), "R_SCHEMA")
    correlations = [_rats(line, 2) for line in _seq(payload["correlations"], 2)]
    total, bound, excess = _rat(payload["total"]), _rat(payload["bound"]), _rat(payload["excess"])
    _require(all(sum((x * x for x in row), Fraction(0)) == 1 for row in near + far), "R059_NOT_UNIT")
    e = [[sum((a * b for a, b in zip(near[x], far[y])), Fraction(0)) for y in range(2)] for x in range(2)]
    _require(correlations == e, "R059_CORRELATION")
    s = e[0][0] + e[0][1] + e[1][0] - e[1][1]
    _require(total == s, "R059_TOTAL")
    local = max(
        a0 * b0 + a0 * b1 + a1 * b0 - a1 * b1
        for a0 in (-1, 1) for a1 in (-1, 1) for b0 in (-1, 1) for b1 in (-1, 1)
    )
    _require(bound == local, "R059_BOUND")
    _require(excess == s - local, "R059_EXCESS")
