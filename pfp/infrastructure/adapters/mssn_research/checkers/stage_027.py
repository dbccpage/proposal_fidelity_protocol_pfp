"""Target checker of record for MSS-027, row 27 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 27): check both composite boundaries of the pentagon are
equal. Negative instance: two different 3-cell composites cannot be declared
coherent.

Input (closed): ``{"objects": n, "automorphisms": m, "associator": [[x, y, z,
value]], "class": "coboundary" | "nontrivial"}``. A skeletal monoidal table:
objects are Z/n under addition, every object's automorphisms are Z/m, the
action is trivial, and the associator assigns to each triple (x, y, z) an
automorphism of x + y + z. ``class`` is the producer's claim about
strictifiability, recomputed here.

The two composites of the pentagon at (w, x, y, z) are, additively,

- the two-step side: a(w + x, y, z) + a(w, x, y + z);
- the three-step side: a(x, y, z) + a(w, x + y, z) + a(w, x, y).

Declared input class: skeletal tables over cyclic groups with trivial action.
The pentagon is decided on all n^4 quadruples. Strictifiability (the
associator is the coboundary of some two-argument table b) is decided by
enumerating every b, which is bounded: m^(n*n) must be at most 4096.

Clauses, each recomputed from the table:

- C1 ``R027_TABLE_GAP``: the associator is not defined on some triple;
- C2 ``R027_INCOHERENT``: at some quadruple the two composites differ (the
  level's negative);
- C3 ``R027_CLASS_MISMATCH``: the declared class is not the recomputed one.
"""

from itertools import product

STAGE = 27
ROW_SHA256 = "sha256:2457443f1cbfd87ef2fccd0051c9a6442d0d0323d2d6f53acd7bb5dc24a33d6f"
FIELDS = ("associator", "automorphisms", "class", "objects")
CLAUSES = (
    ("C1", "R027_TABLE_GAP"),
    ("C2", "R027_INCOHERENT"),
    ("C3", "R027_CLASS_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "associator": [[x, y, z, 1 if (x, y, z) == (1, 1, 0) else 0] for x in (0, 1) for y in (0, 1) for z in (0, 1)],
    "automorphisms": 2,
    "class": "nontrivial",
    "objects": 2,
}
OWN_NEGATIVE_CODE = "R027_INCOHERENT"
CLASSES = ("coboundary", "nontrivial")


def _decide(payload):
    n, m = _nat(payload["objects"]), _nat(payload["automorphisms"])
    _require(1 <= n and 1 <= m and m ** (n * n) <= 4096, "R_SCHEMA")
    _require(payload["class"] in CLASSES, "R_SCHEMA")
    a = {}
    for entry in _seq(payload["associator"]):
        _seq(entry, 4)
        x, y, z, value = (_nat(v) for v in entry)
        _require(x < n and y < n and z < n and value < m and (x, y, z) not in a, "R_SCHEMA")
        a[(x, y, z)] = value
    triples = list(product(range(n), repeat=3))
    _require(all(t in a for t in triples), "R027_TABLE_GAP")
    for w, x, y, z in product(range(n), repeat=4):
        two = a[((w + x) % n, y, z)] + a[(w, x, (y + z) % n)]
        three = a[(x, y, z)] + a[(w, (x + y) % n, z)] + a[(w, x, y)]
        _require(two % m == three % m, "R027_INCOHERENT")
    pairs = list(product(range(n), repeat=2))
    coboundary = False
    for values in product(range(m), repeat=len(pairs)):
        b = dict(zip(pairs, values))
        if all(
            (b[(y, z)] - b[((x + y) % n, z)] + b[(x, (y + z) % n)] - b[(x, y)] - a[(x, y, z)]) % m == 0
            for x, y, z in triples
        ):
            coboundary = True
            break
    _require(payload["class"] == ("coboundary" if coboundary else "nontrivial"), "R027_CLASS_MISMATCH")
