"""Target checker of record for MSS-002, row 2 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 2): resolve each directed endpoint and preserve the
obstruction carrier. Negative instance: an edge to an absent vertex is
rejected.

Input (closed):
``{"vertices": [nat], "edges": [[nat, nat]], "obstructions": [edge index],
"lift": {"vertices": [nat], "edges": [[nat, nat]]}}``.

The declared law is irreflexivity, so the obstruction carrier is the set of
self-loop edges. The checker recomputes that set; the declared
``obstructions`` list is compared with it, never trusted. ``lift`` is the next
stage's graph, and the carrier must reappear in it.

Clauses:

- C1 ``R002_ABSENT_ENDPOINT``: an edge endpoint (in either graph) is not a
  declared vertex;
- C2 ``R002_DUPLICATE_VERTEX``: a vertex is declared twice;
- C3 ``R002_OBSTRUCTION_DROPPED``: a recomputed self-loop is not recorded as an
  obstruction;
- C4 ``R002_OBSTRUCTION_UNFOUNDED``: a recorded obstruction is not a self-loop;
- C5 ``R002_CARRIER_NOT_PRESERVED``: the lift drops an old vertex or edge
  (edges compared as a multiset), so the carrier does not survive the lift.
"""

STAGE = 2
ROW_SHA256 = "sha256:be4535c6f0efcbb83557a22549d06c7860f0aba47643902d710dd1fe13c3aa6d"
FIELDS = ("edges", "lift", "obstructions", "vertices")
CLAUSES = (
    ("C1", "R002_ABSENT_ENDPOINT"),
    ("C2", "R002_DUPLICATE_VERTEX"),
    ("C3", "R002_OBSTRUCTION_DROPPED"),
    ("C4", "R002_OBSTRUCTION_UNFOUNDED"),
    ("C5", "R002_CARRIER_NOT_PRESERVED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "edges": [[0, 1], [0, 2]],
    "lift": {"edges": [[0, 1], [0, 2]], "vertices": [0, 1]},
    "obstructions": [],
    "vertices": [0, 1],
}
OWN_NEGATIVE_CODE = "R002_ABSENT_ENDPOINT"


def _graph(vertices, edges):
    vertices = [_nat(v) for v in _seq(vertices)]
    _require(len(set(vertices)) == len(vertices), "R002_DUPLICATE_VERTEX")
    declared = set(vertices)
    out = []
    for edge in _seq(edges):
        _seq(edge, 2)
        tail, head = _nat(edge[0]), _nat(edge[1])
        _require(tail in declared and head in declared, "R002_ABSENT_ENDPOINT")
        out.append((tail, head))
    return vertices, out


def _decide(payload):
    vertices, edges = _graph(payload["vertices"], payload["edges"])
    recorded = [_nat(index) for index in _seq(payload["obstructions"])]
    _require(len(set(recorded)) == len(recorded), "R_SCHEMA")
    for index in recorded:
        _require(index < len(edges) and edges[index][0] == edges[index][1], "R002_OBSTRUCTION_UNFOUNDED")
    carrier = {index for index, (tail, head) in enumerate(edges) if tail == head}
    _require(carrier <= set(recorded), "R002_OBSTRUCTION_DROPPED")
    lift = payload["lift"]
    _require(isinstance(lift, dict) and set(lift) == {"edges", "vertices"}, "R_SCHEMA")
    lifted_vertices, lifted_edges = _graph(lift["vertices"], lift["edges"])
    _require(set(vertices) <= set(lifted_vertices), "R002_CARRIER_NOT_PRESERVED")
    remaining = list(lifted_edges)
    for edge in edges:
        _require(edge in remaining, "R002_CARRIER_NOT_PRESERVED")
        remaining.remove(edge)
