"""Target checker of record for MSS-076, row 76 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 76): check boundary squared is zero and relation references
exist. Negative instance: a dangling edge violates the cell schema.

Input (closed): ``{"vertices": [id], "edges": [[id, tail, head]], "faces":
[[id, [[edge, sign]]]]}`` with sign ``"+"`` or ``"-"``. The boundary maps are
derived from the declared cells, never supplied: the boundary of an edge is
head minus tail, and the boundary of a face is its signed sum of edges. The
checker composes them exactly (integer coefficients) and requires every
coefficient of the composite to be zero.

Declared input class: finite two-dimensional cell tables with integer
incidence; one relation per cell dimension; ids unique across all cells.

Clauses, decided in this order:

- C1 ``R076_DANGLING_EDGE``: an edge's tail or head is not a declared vertex
  (the level's negative);
- C2 ``R076_DANGLING_FACE``: a face refers to an undeclared edge;
- C3 ``R076_BOUNDARY_NOT_CLOSED``: some coefficient of the boundary of a
  face's boundary is nonzero.
"""

STAGE = 76
ROW_SHA256 = "sha256:a6e88f9c803d79cf08a609b5cc721222e6bae896e92875bfdc9e9cb30cba7b78"
FIELDS = ("edges", "faces", "vertices")
CLAUSES = (
    ("C1", "R076_DANGLING_EDGE"),
    ("C2", "R076_DANGLING_FACE"),
    ("C3", "R076_BOUNDARY_NOT_CLOSED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "edges": [["e1", "p", "q"], ["e2", "q", "s"]],
    "faces": [],
    "vertices": ["p", "q"],
}
OWN_NEGATIVE_CODE = "R076_DANGLING_EDGE"
_SIGNS = {"+": 1, "-": -1}


def _decide(payload):
    vertices = [_text(v) for v in _seq(payload["vertices"])]
    edges = {}
    for edge in _seq(payload["edges"]):
        _seq(edge, 3)
        name, tail, head = (_text(part) for part in edge)
        _require(name not in edges, "R_SCHEMA")
        edges[name] = (tail, head)
    faces = []
    for face in _seq(payload["faces"]):
        _seq(face, 2)
        terms = []
        for term in _seq(face[1]):
            _seq(term, 2)
            _require(term[1] in _SIGNS, "R_SCHEMA")
            terms.append((_text(term[0]), _SIGNS[term[1]]))
        _require(terms, "R_SCHEMA")
        faces.append((_text(face[0]), terms))
    names = vertices + list(edges) + [name for name, _ in faces]
    _require(len(set(names)) == len(names), "R_SCHEMA")
    known = set(vertices)
    for tail, head in edges.values():
        _require(tail in known and head in known, "R076_DANGLING_EDGE")
    for _, terms in faces:
        for edge, _ in terms:
            _require(edge in edges, "R076_DANGLING_FACE")
    for _, terms in faces:
        total = {vertex: 0 for vertex in vertices}
        for edge, sign in terms:
            tail, head = edges[edge]
            total[head] += sign
            total[tail] -= sign
        _require(all(value == 0 for value in total.values()), "R076_BOUNDARY_NOT_CLOSED")
