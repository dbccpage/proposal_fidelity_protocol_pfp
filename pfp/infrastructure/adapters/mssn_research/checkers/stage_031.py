"""Target checker of record for MSS-031, row 31 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 31): check cocycle independence and map naturality in
declared coefficients. Negative instance: an operation depending on a
coboundary representative is rejected.

Input (closed): ``{"triangles": [[nat, nat, nat]], "terms": [[triangle,
edge, edge]], "constant": [triangle], "cocycles": [[edge]], "maps":
[[nat]]}``. The complex is the pure 2-dimensional simplicial complex of the
listed triangles (ascending vertex triples) on vertices 0..V-1; an edge is an
ascending vertex pair of some triangle. The operation, from degree-1 to
degree-2 cochains over F2, is a quadratic formula: op(a)(t) is the sum over
the terms ``[t, e1, e2]`` of a(e1) a(e2), plus 1 when t is listed in
``constant`` (a term with e1 = e2 is linear, since a(e)^2 = a(e) over F2).
Cup squaring is the terms ``[t, [x, y], [y, z]]`` for each t = [x, y, z].
``cocycles`` are the declared test cochains, each given by its support.
``maps`` are simplicial maps from the complex to itself, as vertex images.

Declared input class: coefficients F2; pure 2-dimensional complexes with at
most 12 vertices; quadratic cochain formulas. Representative independence is
decided for every declared test cocycle against every 0-cochain (all 2^V of
them); naturality is decided for every declared map and test cocycle. Both
compare classes by exact F2 elimination against the image of the
coboundary. Which operation a formula computes is not decided.

Clauses, each recomputed:

- C1 ``R031_NOT_COCYCLE``: a declared test cochain has a nonzero coboundary;
- C2 ``R031_REP_DEPENDENT``: for some test cocycle a and 0-cochain f, the
  classes of op(a + df) and op(a) differ (the level's negative);
- C3 ``R031_NOT_NATURAL``: for some declared map g and test cocycle a, the
  classes of op(g*a) and g*(op(a)) differ.
"""

STAGE = 31
ROW_SHA256 = "sha256:22505593590907b24542c8e100d66eaf56e0372ef18a1c922aef83b069709e3d"
FIELDS = ("cocycles", "constant", "maps", "terms", "triangles")
CLAUSES = (
    ("C1", "R031_NOT_COCYCLE"),
    ("C2", "R031_REP_DEPENDENT"),
    ("C3", "R031_NOT_NATURAL"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("naturality_square",)
OWN_NEGATIVE = {
    "cocycles": [[[0, 1], [0, 2], [0, 3]]],
    "constant": [],
    "maps": [[0, 1, 2, 3]],
    "terms": [[0, [0, 1], [0, 1]]],
    "triangles": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
}
OWN_NEGATIVE_CODE = "R031_REP_DEPENDENT"


def _edge(value, index):
    pair = tuple(_nat(v) for v in _seq(value, 2))
    _require(pair in index, "R_SCHEMA")
    return pair


def _reduce(vector, basis):
    while vector:
        top = vector.bit_length() - 1
        if top not in basis:
            return vector
        vector ^= basis[top]
    return 0


def _decide(payload):
    triangles = []
    for t in _seq(payload["triangles"]):
        verts = tuple(_nat(v) for v in _seq(t, 3))
        _require(list(verts) == sorted(set(verts)) and verts not in triangles, "R_SCHEMA")
        triangles.append(verts)
    _require(triangles, "R_SCHEMA")
    count = max(max(t) for t in triangles) + 1
    _require(count <= 12 and {v for t in triangles for v in t} == set(range(count)), "R_SCHEMA")
    edges = sorted({(t[i], t[j]) for t in triangles for i in range(3) for j in range(i + 1, 3)})
    edge_index = {e: i for i, e in enumerate(edges)}
    tri_index = {t: i for i, t in enumerate(triangles)}
    faces = [[edge_index[(t[0], t[1])], edge_index[(t[0], t[2])], edge_index[(t[1], t[2])]] for t in triangles]
    terms = []
    for entry in _seq(payload["terms"]):
        _seq(entry, 3)
        t = _nat(entry[0])
        _require(t < len(triangles), "R_SCHEMA")
        terms.append((t, edge_index[_edge(entry[1], edge_index)], edge_index[_edge(entry[2], edge_index)]))
    constant = 0
    for t in _seq(payload["constant"]):
        t = _nat(t)
        _require(t < len(triangles) and not constant >> t & 1, "R_SCHEMA")
        constant |= 1 << t

    def op(alpha):
        out = constant
        for t, e1, e2 in terms:
            if alpha >> e1 & 1 and alpha >> e2 & 1:
                out ^= 1 << t
        return out

    def delta1(alpha):
        out = 0
        for t, face in enumerate(faces):
            if sum(alpha >> e & 1 for e in face) % 2:
                out |= 1 << t
        return out

    def delta0(f):
        out = 0
        for i, (u, v) in enumerate(edges):
            if (f >> u & 1) != (f >> v & 1):
                out |= 1 << i
        return out

    basis = {}
    for i in range(len(edges)):
        vector = _reduce(delta1(1 << i), basis)
        if vector:
            basis[vector.bit_length() - 1] = vector
    cocycles = []
    for support in _seq(payload["cocycles"]):
        alpha = 0
        for e in _seq(support):
            bit = 1 << edge_index[_edge(e, edge_index)]
            _require(not alpha & bit, "R_SCHEMA")
            alpha |= bit
        cocycles.append(alpha)
    maps = []
    simplices = {(v,) for v in range(count)} | set(edges) | set(triangles)
    for images in _seq(payload["maps"]):
        g = [_nat(v) for v in _seq(images, count)]
        _require(all(v < count for v in g), "R_SCHEMA")
        _require(all(tuple(sorted({g[v] for v in t})) in simplices for t in triangles), "R_SCHEMA")
        maps.append(g)
    for alpha in cocycles:
        _require(delta1(alpha) == 0, "R031_NOT_COCYCLE")
    for alpha in cocycles:
        base = op(alpha)
        for f in range(1 << count):
            _require(_reduce(op(alpha ^ delta0(f)) ^ base, basis) == 0, "R031_REP_DEPENDENT")

    def pull1(g, alpha):
        out = 0
        for i, (u, v) in enumerate(edges):
            image = (min(g[u], g[v]), max(g[u], g[v]))
            if image[0] != image[1] and alpha >> edge_index[image] & 1:
                out |= 1 << i
        return out

    def pull2(g, c):
        out = 0
        for i, t in enumerate(triangles):
            image = tuple(sorted({g[v] for v in t}))
            if len(image) == 3 and c >> tri_index[image] & 1:
                out |= 1 << i
        return out

    for g in maps:
        for alpha in cocycles:
            _require(_reduce(op(pull1(g, alpha)) ^ pull2(g, op(alpha)), basis) == 0, "R031_NOT_NATURAL")
