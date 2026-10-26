"""Target checker of record for MSS-072, row 72 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 72): check incidence nilpotency and boundary conditions.
Negative instance: an invalid mesh boundary (rim) is rejected.

Input (closed): ``{"vertices": [v], "edges": [[u, w]], "faces": [[a, b, c]],
"d0": table, "d1": table, "rim_edges": [edge index], "rim_vertices": [v],
"relative": [n0, n1, n2]}``. The cells are declared; the incidence tables are
derived from them, never accepted: d0 (edges x vertices) puts -1 at an edge's
first vertex and +1 at its second; d1 (faces x edges) puts +1 or -1 where a
face's boundary a->b->c->a runs along or against an edge. The producer claims
both tables, the rim, and the counts of relative cells (cells not on the rim).

The declared rim must be exactly the edges with one incident face together
with their end vertices, so it is a subcomplex and a cochain vanishing on the
rim stays vanishing under the incidence maps.

Declared input class: finite two-dimensional simplicial complexes with
oriented edges and triangular faces; table entries are canonical rationals.

Clauses, decided in this order:

- C1 ``R072_NOT_A_COMPLEX``: a face has repeated vertices or a boundary edge
  that is not declared;
- C2 ``R072_NOT_NILPOTENT``: the claimed d1 times the claimed d0 is not zero,
  or their shapes do not compose;
- C3 ``R072_INCIDENCE``: a claimed table differs from the table derived from
  the cells (supplied tables that compose to zero are not enough);
- C4 ``R072_RIM``: the declared rim edges are not the edges with exactly one
  incident face, or the rim vertices are not their end vertices (the level's
  negative);
- C5 ``R072_RELATIVE_COUNT``: the claimed counts of vertices, edges and faces
  off the rim differ from the derived ones.
"""

STAGE = 72
ROW_SHA256 = "sha256:ee3ff30f5dc97cbddc632505e7ccb017b9600be967c4374f8d586f1ebcfa0cdb"
FIELDS = ("d0", "d1", "edges", "faces", "relative", "rim_edges", "rim_vertices", "vertices")
CLAUSES = (
    ("C1", "R072_NOT_A_COMPLEX"),
    ("C2", "R072_NOT_NILPOTENT"),
    ("C3", "R072_INCIDENCE"),
    ("C4", "R072_RIM"),
    ("C5", "R072_RELATIVE_COUNT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_Z, _P, _N = "0/1", "1/1", "-1/1"
OWN_NEGATIVE = {
    "d0": [[_N, _P, _Z, _Z], [_Z, _N, _P, _Z], [_Z, _Z, _N, _P], [_P, _Z, _Z, _N], [_N, _Z, _P, _Z]],
    "d1": [[_P, _P, _Z, _Z, _N], [_Z, _Z, _P, _P, _P]],
    "edges": [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]],
    "faces": [[0, 1, 2], [0, 2, 3]],
    "relative": [0, 0, 2],
    "rim_edges": [0, 1, 2, 3, 4],
    "rim_vertices": [0, 1, 2, 3],
    "vertices": [0, 1, 2, 3],
}
OWN_NEGATIVE_CODE = "R072_RIM"


def _decide(payload):
    vertices = [_nat(v) for v in _seq(payload["vertices"])]
    _require(vertices and len(set(vertices)) == len(vertices), "R_SCHEMA")
    edges = []
    for item in _seq(payload["edges"]):
        u, w = (_nat(v) for v in _seq(item, 2))
        _require(u != w and u in vertices and w in vertices, "R_SCHEMA")
        _require(all({u, w} != set(e) for e in edges), "R_SCHEMA")
        edges.append((u, w))
    faces = [[_nat(v) for v in _seq(item, 3)] for item in _seq(payload["faces"])]
    d0, d1 = _matrix(payload["d0"]), _matrix(payload["d1"])
    rim_edges = [_nat(i) for i in _seq(payload["rim_edges"])]
    rim_vertices = [_nat(v) for v in _seq(payload["rim_vertices"])]
    relative = [_nat(n) for n in _seq(payload["relative"], 3)]
    _require(len(set(rim_edges)) == len(rim_edges) and len(set(rim_vertices)) == len(rim_vertices), "R_SCHEMA")
    derived_d1 = []
    for face in faces:
        _require(len(set(face)) == 3 and all(v in vertices for v in face), "R072_NOT_A_COMPLEX")
        boundary = [(face[i], face[(i + 1) % 3]) for i in range(3)]
        line = []
        for u, w in edges:
            line.append(Fraction(1) if (u, w) in boundary else Fraction(-1) if (w, u) in boundary else Fraction(0))
        _require(sum(1 for x in line if x != 0) == 3, "R072_NOT_A_COMPLEX")
        derived_d1.append(line)
    derived_d0 = [[Fraction(-1) if v == u else Fraction(1) if v == w else Fraction(0) for v in vertices] for u, w in edges]
    inner = {len(row) for row in d1}
    _require(inner <= {len(d0)} and all(len(row) == len(d0[0]) for row in d0) if d0 else not d1, "R072_NOT_NILPOTENT")
    for row in d1:
        for column in range(len(d0[0]) if d0 else 0):
            _require(sum((row[e] * d0[e][column] for e in range(len(d0))), Fraction(0)) == 0, "R072_NOT_NILPOTENT")
    _require(d0 == derived_d0 and d1 == derived_d1, "R072_INCIDENCE")
    incident = [sum(1 for line in derived_d1 if line[e] != 0) for e in range(len(edges))]
    rim = {e for e in range(len(edges)) if incident[e] == 1}
    ends = {v for e in rim for v in edges[e]}
    _require(set(rim_edges) == rim and set(rim_vertices) == ends, "R072_RIM")
    _require(relative == [len(vertices) - len(ends), len(edges) - len(rim), len(faces)], "R072_RELATIVE_COUNT")
