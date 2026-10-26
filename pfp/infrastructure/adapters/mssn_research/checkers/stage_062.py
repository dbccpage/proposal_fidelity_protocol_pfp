"""Target checker of record for MSS-062, row 62 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 62): multiply ordered links around a closed face. Negative
instance: an open walk is rejected as a face.

Input (closed): ``{"labels": k, "objects": [name], "edges": [[name, source,
target, perm]], "faces": [[[[edge, "+" | "-"]], perm]]}``. Every fibre is the
label set {0, ..., k-1}; a link transport is a permutation written as its
list of images. A face is a walk of steps, each an edge read forward (``+``,
its transport) or backward (``-``, the inverse transport), together with the
producer's claimed ordered product, x -> t_n(... t_1(x)), based at the
face's first object.

Declared input class: finite graphs whose link transports lie in the full
permutation group of one finite label set; orientation is declared per step.
The product is ordered: for labels >= 3 it is not a function of the unordered
set of links.

Clauses, decided in this order:

- C1 ``R062_UNDECLARED_EDGE``: a face step names an undeclared edge or an
  undeclared direction;
- C2 ``R062_OPEN_WALK``: a face is empty, has consecutive steps that do not
  meet, or does not end where it starts (the level's negative);
- C3 ``R062_PRODUCT``: a claimed face product differs from the recomputed
  ordered product.
"""

STAGE = 62
ROW_SHA256 = "sha256:628d2145c0d47397df6bab43ea696287b190ab612d1fcd699aea0282acfe09ee"
FIELDS = ("edges", "faces", "labels", "objects")
CLAUSES = (
    ("C1", "R062_UNDECLARED_EDGE"),
    ("C2", "R062_OPEN_WALK"),
    ("C3", "R062_PRODUCT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "edges": [
        ["e01", "0", "1", [1, 2, 0]],
        ["e13", "1", "3", [1, 0, 2]],
        ["e32", "3", "2", [0, 1, 2]],
        ["e20", "2", "0", [0, 2, 1]],
        ["e03", "0", "3", [2, 1, 0]],
    ],
    "faces": [[[["e01", "+"], ["e13", "+"]], [0, 2, 1]]],
    "labels": 3,
    "objects": ["0", "1", "2", "3"],
}
OWN_NEGATIVE_CODE = "R062_OPEN_WALK"


def _perm(value, k):
    images = [_nat(x) for x in _seq(value, k)]
    _require(sorted(images) == list(range(k)), "R_SCHEMA")
    return images


def _inverse(p):
    out = [0] * len(p)
    for x, image in enumerate(p):
        out[image] = x
    return out


def _decide(payload):
    k = _nat(payload["labels"])
    _require(k >= 1, "R_SCHEMA")
    objects = [_text(name) for name in _seq(payload["objects"])]
    _require(objects and len(set(objects)) == len(objects), "R_SCHEMA")
    edges = {}
    for item in _seq(payload["edges"]):
        _seq(item, 4)
        name, source, target = _text(item[0]), _text(item[1]), _text(item[2])
        _require(name not in edges and source in objects and target in objects, "R_SCHEMA")
        edges[name] = (source, target, _perm(item[3], k))
    faces = []
    for item in _seq(payload["faces"]):
        _seq(item, 2)
        steps = []
        for step in _seq(item[0]):
            _seq(step, 2)
            steps.append((step[0], step[1]))
        faces.append((steps, [_nat(x) for x in _seq(item[1])]))
    _require(faces, "R_SCHEMA")
    for steps, _ in faces:
        _require(all(edge in edges and direction in ("+", "-") for edge, direction in steps), "R062_UNDECLARED_EDGE")
    for steps, _ in faces:
        _require(steps, "R062_OPEN_WALK")
        ends = []
        for edge, direction in steps:
            source, target, _ = edges[edge]
            ends.append((source, target) if direction == "+" else (target, source))
        _require(all(a[1] == b[0] for a, b in zip(ends, ends[1:])), "R062_OPEN_WALK")
        _require(ends[-1][1] == ends[0][0], "R062_OPEN_WALK")
    for steps, claimed in faces:
        product = list(range(k))
        for edge, direction in steps:
            link = edges[edge][2] if direction == "+" else _inverse(edges[edge][2])
            product = [link[product[x]] for x in range(k)]
        _require(claimed == product, "R062_PRODUCT")
