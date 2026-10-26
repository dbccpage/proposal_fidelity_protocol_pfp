"""Target checker of record for MSS-063, row 63 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 63): check simplex geometry and the discrete action from
incidence. Negative instance: a deficit term without hinge incidence is
rejected.

Input (closed): ``{"triangles": [[u, v, w]], "lengths": [[u, v, s]],
"terms": [[vertex, [triangle], deficit]], "action": A}``. Vertices are
natural numbers; ``lengths`` gives the squared length s of every edge
(u < v) exactly once. Each term is the producer's deficit at one vertex hinge
together with the triangles it was assembled from. Deficits are in turns
(one turn is a full angle), so the deficit at a vertex is 1 minus the sum of
its triangle angles, and the action is the sum of the deficits (every
vertex hinge has measure 1).

Declared input class: closed triangulated surfaces (every edge in exactly two
triangles), vertex hinges only. Angles are exact turn fractions read from the
cosine table cos = 1/2 -> 1/6, cos = 0 -> 1/4, cos = -1/2 -> 1/3, decided on
cos^2 and the sign of b + c - a, with no square root taken. Any other angle is
refused as not exactly representable; with this table the admitted triangles
are exactly the equilateral ones. Three-dimensional hinges (dihedral angles)
are not in the class.

Clauses, decided in this order:

- C1 ``R063_DEGENERATE``: a triangle's Cayley-Menger value
  2(ab + bc + ca) - (a^2 + b^2 + c^2) over squared lengths is not positive;
- C2 ``R063_ANGLE_NOT_EXACT``: a triangle angle is not in the exact table;
- C3 ``R063_INCIDENCE``: a vertex has no term or two, or a term's triangles
  are not exactly the triangles incident to its vertex (the level's negative:
  a term built from a triangle that does not contain the hinge);
- C4 ``R063_DEFICIT``: a claimed deficit differs from 1 - sum of angles;
- C5 ``R063_ACTION``: the claimed action differs from the sum of deficits.
"""

STAGE = 63
ROW_SHA256 = "sha256:9dcd46909726230c84889c32b0f56c7ee6e583b24e8b370813eda7a41a9e6e51"
FIELDS = ("action", "lengths", "terms", "triangles")
CLAUSES = (
    ("C1", "R063_DEGENERATE"),
    ("C2", "R063_ANGLE_NOT_EXACT"),
    ("C3", "R063_INCIDENCE"),
    ("C4", "R063_DEFICIT"),
    ("C5", "R063_ACTION"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "action": "2/1",
    "lengths": [[0, 1, "1/1"], [0, 2, "1/1"], [0, 3, "1/1"], [1, 2, "1/1"], [1, 3, "1/1"], [2, 3, "1/1"]],
    "terms": [[0, [0, 1, 3], "1/2"], [1, [0, 1, 3], "1/2"], [2, [0, 2, 3], "1/2"], [3, [1, 2, 3], "1/2"]],
    "triangles": [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]],
}
OWN_NEGATIVE_CODE = "R063_INCIDENCE"


def _angle(a, b, c):
    """Turns of the angle between sides of squared lengths b and c, opposite a."""
    num = b + c - a
    if num == 0:
        return Fraction(1, 4)
    if num * num == b * c:
        return Fraction(1, 6) if num > 0 else Fraction(1, 3)
    _refuse("R063_ANGLE_NOT_EXACT")


def _decide(payload):
    triangles = []
    for item in _seq(payload["triangles"]):
        corners = [_nat(v) for v in _seq(item, 3)]
        _require(len(set(corners)) == 3, "R_SCHEMA")
        triangles.append(corners)
    _require(triangles, "R_SCHEMA")
    edges = {}
    for t in triangles:
        for i in range(3):
            key = tuple(sorted((t[i], t[(i + 1) % 3])))
            edges[key] = edges.get(key, 0) + 1
    _require(all(count == 2 for count in edges.values()), "R_SCHEMA")
    lengths = {}
    for item in _seq(payload["lengths"]):
        _seq(item, 3)
        u, v, s = _nat(item[0]), _nat(item[1]), _rat(item[2])
        _require(u < v and (u, v) not in lengths and s > 0, "R_SCHEMA")
        lengths[(u, v)] = s
    _require(set(lengths) == set(edges), "R_SCHEMA")
    terms = []
    for item in _seq(payload["terms"]):
        _seq(item, 3)
        used = [_nat(i) for i in _seq(item[1])]
        _require(all(i < len(triangles) for i in used), "R_SCHEMA")
        terms.append((_nat(item[0]), used, _rat(item[2])))
    action = _rat(payload["action"])
    angles = {}
    for index, t in enumerate(triangles):
        s = [lengths[tuple(sorted((t[(i + 1) % 3], t[(i + 2) % 3])))] for i in range(3)]
        _require(2 * (s[0] * s[1] + s[1] * s[2] + s[2] * s[0]) - (s[0] ** 2 + s[1] ** 2 + s[2] ** 2) > 0, "R063_DEGENERATE")
    for index, t in enumerate(triangles):
        for i in range(3):
            opposite = lengths[tuple(sorted((t[(i + 1) % 3], t[(i + 2) % 3])))]
            left = lengths[tuple(sorted((t[i], t[(i + 1) % 3])))]
            right = lengths[tuple(sorted((t[i], t[(i + 2) % 3])))]
            angles[(index, t[i])] = _angle(opposite, left, right)
    vertices = sorted({v for t in triangles for v in t})
    _require(sorted(vertex for vertex, _, _ in terms) == vertices, "R063_INCIDENCE")
    for vertex, used, _ in terms:
        incident = sorted(i for i, t in enumerate(triangles) if vertex in t)
        _require(sorted(used) == incident and len(set(used)) == len(used), "R063_INCIDENCE")
    total = Fraction(0)
    for vertex, used, deficit in terms:
        recomputed = 1 - sum((angles[(i, vertex)] for i in used), Fraction(0))
        _require(deficit == recomputed, "R063_DEFICIT")
        total += recomputed
    _require(action == total, "R063_ACTION")
