"""Target checker of record for MSS-064, row 64 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 64): check ordered group products on a declared 3-cell
boundary. Negative instance: scalar deficit cancellation is insufficient.

Input (closed): ``{"labels": k, "cell": [v0, v1, v2, v3], "edges": [[u, v,
perm]], "faces": [[position, connector, cycle, value]]}``. The declared
solid cell is the tetrahedron on four vertices, based at v0. Each face gives a
connector walk (vertex list from v0 to the start of its cycle), its boundary
cycle (a closed vertex list), and a group value, a permutation of
{0, ..., k-1} written as its list of images. ``edges`` is either empty
(face values are supplied data) or gives a transport for every edge u < v
(reading v -> u uses the inverse). Walk products and the closure product are
ordered, x -> t_n(... t_1(x)); faces are multiplied in increasing
``position``.

Declared input class: the tetrahedral 3-cell with values in the full
permutation group of k labels. The closure identity holds for every
edge-derived assignment, so a checker fed only edge-derived faces can never
fail; supplied face data is therefore admitted and must close by its ordered
product, not by a parity or other abelian shadow.

Clauses, decided in this order:

- C1 ``R064_WALK``: a connector does not run from the base to its cycle's
  start, a cycle is not closed, or a walk leaves the cell or repeats a
  vertex in place;
- C2 ``R064_NOT_A_BOUNDARY``: the cycles are not four triangles covering every
  edge of the cell exactly once in each orientation;
- C3 ``R064_FACE_MISMATCH``: with edges declared, a face value differs from
  the ordered product along connector, cycle and connector reversed;
- C4 ``R064_NOT_CLOSED``: the ordered product of the face values is not the
  unit (the level's negative: supplied values t1, t2, t1, t2 whose parity
  shadow balances while (t1 t2)^2 is a three-cycle).
"""

STAGE = 64
ROW_SHA256 = "sha256:628ea9e80037334ddf5d1a19fa27e2cd58c0a80ba8782333bad4b9305180b534"
FIELDS = ("cell", "edges", "faces", "labels")
CLAUSES = (
    ("C1", "R064_WALK"),
    ("C2", "R064_NOT_A_BOUNDARY"),
    ("C3", "R064_FACE_MISMATCH"),
    ("C4", "R064_NOT_CLOSED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "cell": [0, 1, 2, 3],
    "edges": [],
    "faces": [
        [0, [0], [0, 1, 2, 0], [1, 0, 2]],
        [1, [0], [0, 2, 3, 0], [0, 2, 1]],
        [2, [0], [0, 3, 1, 0], [1, 0, 2]],
        [3, [0, 1], [1, 3, 2, 1], [0, 2, 1]],
    ],
    "labels": 3,
}
OWN_NEGATIVE_CODE = "R064_NOT_CLOSED"


def _perm(value, k):
    images = [_nat(x) for x in _seq(value, k)]
    _require(sorted(images) == list(range(k)), "R_SCHEMA")
    return images


def _inverse(p):
    out = [0] * len(p)
    for x, image in enumerate(p):
        out[image] = x
    return out


def _then(p, q):
    return [q[p[x]] for x in range(len(p))]


def _decide(payload):
    k = _nat(payload["labels"])
    _require(k >= 1, "R_SCHEMA")
    cell = [_nat(v) for v in _seq(payload["cell"], 4)]
    _require(len(set(cell)) == 4, "R_SCHEMA")
    edges = {}
    for item in _seq(payload["edges"]):
        _seq(item, 3)
        u, v = _nat(item[0]), _nat(item[1])
        _require(u < v and u in cell and v in cell and (u, v) not in edges, "R_SCHEMA")
        edges[(u, v)] = _perm(item[2], k)
    _require(len(edges) in (0, 6), "R_SCHEMA")
    faces = []
    for item in _seq(payload["faces"], 4):
        _seq(item, 4)
        position = _nat(item[0])
        connector = [_nat(v) for v in _seq(item[1])]
        cycle = [_nat(v) for v in _seq(item[2])]
        value = [_nat(x) for x in _seq(item[3])]
        faces.append((position, connector, cycle, value))
    _require(len({face[0] for face in faces}) == 4, "R_SCHEMA")
    base = cell[0]
    for _, connector, cycle, _ in faces:
        _require(connector and connector[0] == base and cycle and connector[-1] == cycle[0], "R064_WALK")
        _require(len(cycle) >= 2 and cycle[-1] == cycle[0], "R064_WALK")
        for walk in (connector, cycle):
            _require(all(v in cell for v in walk), "R064_WALK")
            _require(all(a != b for a, b in zip(walk, walk[1:])), "R064_WALK")
    used = {}
    for _, _, cycle, _ in faces:
        _require(len(cycle) == 4 and len(set(cycle[:3])) == 3, "R064_NOT_A_BOUNDARY")
        for a, b in zip(cycle, cycle[1:]):
            used[(a, b)] = used.get((a, b), 0) + 1
    oriented = {(a, b) for a in cell for b in cell if a != b}
    _require(set(used) == oriented and all(count == 1 for count in used.values()), "R064_NOT_A_BOUNDARY")
    if edges:
        for _, connector, cycle, value in faces:
            walk = connector + cycle[1:] + list(reversed(connector))[1:]
            product = list(range(k))
            for a, b in zip(walk, walk[1:]):
                link = edges[(a, b)] if a < b else _inverse(edges[(b, a)])
                product = _then(product, link)
            _require(value == product, "R064_FACE_MISMATCH")
    closure = list(range(k))
    for _, _, _, value in sorted(faces, key=lambda face: face[0]):
        closure = _then(closure, _perm(value, k))
    _require(closure == list(range(k)), "R064_NOT_CLOSED")
