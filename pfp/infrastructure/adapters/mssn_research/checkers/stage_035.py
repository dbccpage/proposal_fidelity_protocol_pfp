"""Target checker of record for MSS-035, row 35 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 35): check every rational row sums to one and entries are
nonnegative. Negative instance: a transition row summing to three halves is
rejected.

Input (closed): ``{"states": [name], "kernel": [[rational]]}``. ``kernel``
is square, one row and one column per state, in the order of ``states``.

Declared input class: finite state sets and exact rational kernels. Square
row-stochastic tables only; a rectangular stochastic table is refused as a
schema error, not accepted.

Clauses, each recomputed from the entries:

- C1 ``R035_ROW_SUM``: some row does not sum to exactly 1 (the level's
  negative);
- C2 ``R035_NEGATIVE_ENTRY``: some entry is negative.

C2 is decided before C1, so a row that sums to 1 through a negative entry is
refused as a negative entry.
"""

STAGE = 35
ROW_SHA256 = "sha256:a8e6ea978680f5ad24402263db458707bfa2533a47348ba597b56ba66a486000"
FIELDS = ("kernel", "states")
CLAUSES = (
    ("C1", "R035_ROW_SUM"),
    ("C2", "R035_NEGATIVE_ENTRY"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"kernel": [["1/1", "1/2"], ["0/1", "1/1"]], "states": ["0", "1"]}
OWN_NEGATIVE_CODE = "R035_ROW_SUM"


def _decide(payload):
    states = [_text(s) for s in _seq(payload["states"])]
    _require(states and len(set(states)) == len(states), "R_SCHEMA")
    kernel = _matrix(payload["kernel"], len(states), len(states))
    for row in kernel:
        _require(all(x >= 0 for x in row), "R035_NEGATIVE_ENTRY")
    for row in kernel:
        _require(sum(row, Fraction(0)) == 1, "R035_ROW_SUM")
