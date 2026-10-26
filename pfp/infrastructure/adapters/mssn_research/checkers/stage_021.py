"""Target checker of record for MSS-021, row 21 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 21, paraphrased): check the Gram positivity of the 4-simplex
and the ordered rotation products around its hinges. Negative instance: a
scalar sum of angle defects cannot stand in for the ordered-product closure
identity.

Input (closed): ``{"squared_lengths": [[u, v, q]] (the ten edges of the
simplex on vertices 0..4), "generators": [[name, 4x4 matrix of q]], "loops":
[{"hinge": [a, b, c], "word": [letter], "closure": "identity" |
"nontrivial"}]}``. A letter is a generator name, or the name followed by
``-`` for its inverse (its transpose).

Declared class (a booked changed assumption): genuine simplicial rotation
data is irrational (the regular simplex's dihedral angle is arccos(1/4)), so
the rotations are declared exactly, as rational matrices in SO(4). The checker
verifies membership (M M^T = I, det M = 1) and multiplies in order. It never
sets a closing rotation by construction.

Clauses:

- C1 ``R021_GRAM_NOT_POSITIVE``: a leading principal minor of the simplex's
  Gram matrix (based at vertex 0) is not positive;
- C2 ``R021_NOT_ROTATION``: a generator is not in SO(4);
- C3 ``R021_SCALAR_SUM_CLOSURE``: a loop is declared closed while its ordered
  product is not the identity and its abelian image (the exponent sum of every
  generator, the scalar sum) is zero: the scalar sum stood in for closure;
- C4 ``R021_CLOSURE_MISMATCH``: any other disagreement between the declared
  closure and the ordered product.

Hinges are triangles of the simplex; a loop's hinge is checked for incidence.
"""

from itertools import combinations

STAGE = 21
ROW_SHA256 = "sha256:aba5622630090ebf5e6bab21c4b1bd54f81297a9ca7d15d74ecd5a102668e3b5"
FIELDS = ("generators", "loops", "squared_lengths")
CLAUSES = (
    ("C1", "R021_GRAM_NOT_POSITIVE"),
    ("C2", "R021_NOT_ROTATION"),
    ("C3", "R021_SCALAR_SUM_CLOSURE"),
    ("C4", "R021_CLOSURE_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
VERTICES = (0, 1, 2, 3, 4)
CLOSURES = ("identity", "nontrivial")
ROTATE_YZ = [["1/1", "0/1", "0/1", "0/1"], ["0/1", "0/1", "-1/1", "0/1"], ["0/1", "1/1", "0/1", "0/1"], ["0/1", "0/1", "0/1", "1/1"]]
ROTATE_XZ = [["0/1", "0/1", "1/1", "0/1"], ["0/1", "1/1", "0/1", "0/1"], ["-1/1", "0/1", "0/1", "0/1"], ["0/1", "0/1", "0/1", "1/1"]]
OWN_NEGATIVE = {
    "generators": [["Rx", ROTATE_YZ], ["Ry", ROTATE_XZ]],
    "loops": [{"closure": "identity", "hinge": [0, 1, 2], "word": ["Rx", "Ry", "Rx-", "Ry-"]}],
    "squared_lengths": [[a, b, "1/1"] for a, b in combinations(VERTICES, 2)],
}
OWN_NEGATIVE_CODE = "R021_SCALAR_SUM_CLOSURE"


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


def _mul(a, b):
    return [[sum((a[i][t] * b[t][j] for t in range(4)), Fraction(0)) for j in range(4)] for i in range(4)]


def _transpose(a):
    return [[a[j][i] for j in range(4)] for i in range(4)]


IDENTITY = [[Fraction(int(i == j)) for j in range(4)] for i in range(4)]


def _decide(payload):
    lengths = {}
    for entry in _seq(payload["squared_lengths"]):
        _seq(entry, 3)
        low, high, value = _nat(entry[0]), _nat(entry[1]), _rat(entry[2])
        _require(low < high and high in VERTICES and (low, high) not in lengths, "R_SCHEMA")
        lengths[(low, high)] = value
    _require(set(lengths) == set(combinations(VERTICES, 2)), "R_SCHEMA")

    def squared(a, b):
        return Fraction(0) if a == b else lengths[(min(a, b), max(a, b))]

    rest = VERTICES[1:]
    gram = [[(squared(0, a) + squared(0, b) - squared(a, b)) / 2 for b in rest] for a in rest]
    for k in range(1, 5):
        _require(_det([row[:k] for row in gram[:k]]) > 0, "R021_GRAM_NOT_POSITIVE")
    generators = {}
    for entry in _seq(payload["generators"]):
        _seq(entry, 2)
        name = _text(entry[0])
        _require(name not in generators and not name.endswith("-"), "R_SCHEMA")
        matrix = _matrix(entry[1], rows=4, columns=4)
        _require(_mul(matrix, _transpose(matrix)) == IDENTITY and _det(matrix) == 1, "R021_NOT_ROTATION")
        generators[name] = matrix
    loops = _seq(payload["loops"])
    _require(loops, "R_SCHEMA")
    for loop in loops:
        _require(isinstance(loop, dict) and set(loop) == {"closure", "hinge", "word"}, "R_SCHEMA")
        hinge = [_nat(v) for v in _seq(loop["hinge"], 3)]
        _require(len(set(hinge)) == 3 and set(hinge) <= set(VERTICES), "R_SCHEMA")
        _require(loop["closure"] in CLOSURES, "R_SCHEMA")
        product, exponents = IDENTITY, {name: 0 for name in generators}
        word = _seq(loop["word"])
        _require(word, "R_SCHEMA")
        for letter in word:
            _require(isinstance(letter, str), "R_SCHEMA")
            inverse = letter.endswith("-")
            name = letter[:-1] if inverse else letter
            _require(name in generators, "R_SCHEMA")
            factor = _transpose(generators[name]) if inverse else generators[name]
            product = _mul(product, factor)
            exponents[name] += -1 if inverse else 1
        closed = product == IDENTITY
        if loop["closure"] == "identity" and not closed:
            _require(any(exponents.values()), "R021_SCALAR_SUM_CLOSURE")
        _require(closed == (loop["closure"] == "identity"), "R021_CLOSURE_MISMATCH")
