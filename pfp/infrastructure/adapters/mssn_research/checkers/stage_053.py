"""Target checker of record for MSS-053, row 53 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 53): check product dimension and basis ordering. Negative
instance: a permuted factor basis without transport is rejected.

Input (closed): ``{"factors": [[name, row], [name, row]], "reading": name,
"swap": [slot] | null, "joined": [pair], "dimension": n}``. Rows are lists of
pairs ``[a, b]`` (a + b i, canonical rationals). With factor sizes m and n in
the declared factor order, slot (i, j) of the joined frame is m-major:
index n * i + j. ``reading`` names the factor whose index runs slowest in the
producer's ``joined`` row. When that is the second factor, ``swap`` must be
the transport table: the permutation taking index n * i + j to m * j + i.
Slot order travels as a list, never as mapping keys.

Declared input class: two factors over Q(i), each of size >= 1.

Clauses, decided in this order:

- C1 ``R053_DIMENSION``: the claimed dimension is not m * n, or the joined
  row does not have m * n slots;
- C2 ``R053_UNTRANSPORTED``: the reading order permutes the factors and no
  swap table is given (the level's negative);
- C3 ``R053_SWAP``: a swap table is given for the declared order, or the
  given table is not the factor-exchange permutation;
- C4 ``R053_PRODUCT``: the joined row is not the recomputed product, read in
  the declared order through the given transport.
"""

STAGE = 53
ROW_SHA256 = "sha256:9224d124df6dfe3de78f78fd503e7beb58421f3f2a856cb30386aa36c287d176"
FIELDS = ("dimension", "factors", "joined", "reading", "swap")
CLAUSES = (
    ("C1", "R053_DIMENSION"),
    ("C2", "R053_UNTRANSPORTED"),
    ("C3", "R053_SWAP"),
    ("C4", "R053_PRODUCT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "dimension": 4,
    "factors": [["A", [["3/5", "0/1"], ["4/5", "0/1"]]], ["B", [["1/1", "0/1"], ["0/1", "0/1"]]]],
    "joined": [["3/5", "0/1"], ["4/5", "0/1"], ["0/1", "0/1"], ["0/1", "0/1"]],
    "reading": "B",
    "swap": None,
}
OWN_NEGATIVE_CODE = "R053_UNTRANSPORTED"


def _pair(value):
    return tuple(_rats(value, 2))


def _mul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def _decide(payload):
    factors = []
    for item in _seq(payload["factors"], 2):
        _seq(item, 2)
        factors.append((_text(item[0]), [_pair(entry) for entry in _seq(item[1])]))
    (first, left), (second, right) = factors
    _require(first != second and left and right, "R_SCHEMA")
    reading = _text(payload["reading"])
    _require(reading in (first, second), "R_SCHEMA")
    joined = [_pair(entry) for entry in _seq(payload["joined"])]
    swap = payload["swap"]
    swap = None if swap is None else [_nat(slot) for slot in _seq(swap)]
    m, n = len(left), len(right)
    _require(_nat(payload["dimension"]) == m * n and len(joined) == m * n, "R053_DIMENSION")
    exchange = [m * j + i for i in range(m) for j in range(n)]
    if reading == first:
        _require(swap is None, "R053_SWAP")
    else:
        _require(swap is not None, "R053_UNTRANSPORTED")
        _require(swap == exchange, "R053_SWAP")
    product = [_mul(left[i], right[j]) for i in range(m) for j in range(n)]
    if swap is not None:
        moved = [None] * (m * n)
        for index, target in enumerate(swap):
            moved[target] = product[index]
        product = moved
    _require(joined == product, "R053_PRODUCT")
