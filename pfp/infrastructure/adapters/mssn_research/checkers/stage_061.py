"""Target checker of record for MSS-061, row 61 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 61): check path composition and endpoint covariance. Negative
instance: changing the frame at the source but not at the target is rejected.

Input (closed): ``{"labels": k, "objects": [name], "arrows": [[name, source,
target, perm]], "walk": [arrow], "composite": perm, "change": [[object,
perm]], "changed": [[arrow, perm]], "changed_composite": perm}``. Every fibre
is the label set {0, ..., k-1}; a transport is a permutation written as its
list of images (x goes to perm[x]). Along a walk a1, a2, ... the composite is
x -> p_an(... p_a1(x)).

A frame change is one permutation g_v per object. It acts on every arrow at
both ends: p'_a = g_target . p_a . g_source^-1. The producer claims the
composite along ``walk``, the changed transports of every arrow, and the
changed composite, which by endpoint covariance must be
g_end . composite . g_start^-1.

Declared input class: finite quivers whose fibres are one finite label set,
with transports in its full permutation group (non-commuting from three
labels). The checker decides the claims above; it does not decide whether a
global section exists.

Clauses, decided in this order:

- C1 ``R061_NOT_A_WALK``: the walk uses an undeclared arrow, is empty, or
  has consecutive arrows that do not meet;
- C2 ``R061_COMPOSITE``: the claimed composite differs from the recomputed one;
- C3 ``R061_ONE_END``: a claimed changed transport is not the both-ends
  conjugate (the level's negative: a change applied at one end only);
- C4 ``R061_COVARIANCE``: the claimed changed composite differs from
  g_end . composite . g_start^-1.
"""

STAGE = 61
ROW_SHA256 = "sha256:7167c258ffc5eaf6d32e3e0286e0d5bbe3e55a0fe927a878545d50f677470a6e"
FIELDS = ("arrows", "change", "changed", "changed_composite", "composite", "labels", "objects", "walk")
CLAUSES = (
    ("C1", "R061_NOT_A_WALK"),
    ("C2", "R061_COMPOSITE"),
    ("C3", "R061_ONE_END"),
    ("C4", "R061_COVARIANCE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "arrows": [["a", "0", "1", [0, 1, 2]], ["b", "1", "2", [0, 1, 2]], ["c", "2", "0", [0, 1, 2]]],
    "change": [["0", [1, 0, 2]], ["1", [0, 1, 2]], ["2", [0, 1, 2]]],
    "changed": [["a", [1, 0, 2]], ["b", [0, 1, 2]], ["c", [0, 1, 2]]],
    "changed_composite": [1, 0, 2],
    "composite": [0, 1, 2],
    "labels": 3,
    "objects": ["0", "1", "2"],
    "walk": ["a", "b"],
}
OWN_NEGATIVE_CODE = "R061_ONE_END"


def _perm(value, k):
    images = [_nat(x) for x in _seq(value, k)]
    _require(sorted(images) == list(range(k)), "R_SCHEMA")
    return images


def _then(p, q):
    """First p, then q."""
    return [q[p[x]] for x in range(len(p))]


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
    arrows = {}
    for item in _seq(payload["arrows"]):
        _seq(item, 4)
        name, source, target = _text(item[0]), _text(item[1]), _text(item[2])
        _require(name not in arrows and source in objects and target in objects, "R_SCHEMA")
        arrows[name] = (source, target, _perm(item[3], k))
    change = {}
    for item in _seq(payload["change"]):
        _seq(item, 2)
        _require(_text(item[0]) in objects and item[0] not in change, "R_SCHEMA")
        change[item[0]] = _perm(item[1], k)
    _require(set(change) == set(objects), "R_SCHEMA")
    changed = {}
    for item in _seq(payload["changed"]):
        _seq(item, 2)
        _require(_text(item[0]) in arrows and item[0] not in changed, "R_SCHEMA")
        changed[item[0]] = [_nat(x) for x in _seq(item[1])]
    _require(set(changed) == set(arrows), "R_SCHEMA")
    composite = [_nat(x) for x in _seq(payload["composite"])]
    changed_composite = [_nat(x) for x in _seq(payload["changed_composite"])]
    walk = [_text(name) for name in _seq(payload["walk"])]
    _require(walk and all(name in arrows for name in walk), "R061_NOT_A_WALK")
    _require(all(arrows[a][1] == arrows[b][0] for a, b in zip(walk, walk[1:])), "R061_NOT_A_WALK")
    along = list(range(k))
    for name in walk:
        along = _then(along, arrows[name][2])
    _require(composite == along, "R061_COMPOSITE")
    for name, (source, target, p) in arrows.items():
        conjugate = _then(_then(_inverse(change[source]), p), change[target])
        _require(changed[name] == conjugate, "R061_ONE_END")
    start, end = arrows[walk[0]][0], arrows[walk[-1]][1]
    covariant = _then(_then(_inverse(change[start]), along), change[end])
    _require(changed_composite == covariant, "R061_COVARIANCE")
