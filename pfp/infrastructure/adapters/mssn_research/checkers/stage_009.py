"""Target checker of record for MSS-009, row 9 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 9): check involution and variance on typed arrows. Negative
instance: reversing only endpoints while dropping obstruction is rejected.

Input (closed): ``{"objects": [nat], "arrows": [[name, src, tgt, mark]],
"dagger": [[name, name]], "composites": [[first, second, result]]}``.
``mark`` is ``"plain"`` or ``"marked"``; a marked arrow carries an
obstruction. A composite ``[f, g, h]`` declares h = g after f.

Clauses, each recomputed from the arrow table:

- C1 ``R009_NOT_TOTAL``: the dagger is not defined on every arrow;
- C2 ``R009_NOT_INVOLUTION``: f†† is not f for some arrow;
- C3 ``R009_ENDPOINTS``: f : a -> b but f† is not b -> a;
- C4 ``R009_OBSTRUCTION_DROPPED``: f† does not carry f's mark (the level's
  negative: endpoints reversed, obstruction dropped);
- C5 ``R009_COMPOSITE_TYPING``: a declared composite is ill-typed;
- C6 ``R009_VARIANCE``: for a composite h = g f, the composite h† = f† g† is
  not declared (contravariance). A covariant reversal is ill-typed and fails
  C5.
"""

STAGE = 9
ROW_SHA256 = "sha256:1e51bf56c78a0c22c9776752261287352d4c2d700697a0a050da19bed92d09e0"
FIELDS = ("arrows", "composites", "dagger", "objects")
CLAUSES = (
    ("C1", "R009_NOT_TOTAL"),
    ("C2", "R009_NOT_INVOLUTION"),
    ("C3", "R009_ENDPOINTS"),
    ("C4", "R009_OBSTRUCTION_DROPPED"),
    ("C5", "R009_COMPOSITE_TYPING"),
    ("C6", "R009_VARIANCE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("dagger_action",)
OWN_NEGATIVE = {
    "arrows": [["l", 0, 0, "marked"], ["L", 0, 0, "plain"], ["f", 0, 1, "plain"], ["F", 1, 0, "plain"]],
    "composites": [],
    "dagger": [["l", "L"], ["L", "l"], ["f", "F"], ["F", "f"]],
    "objects": [0, 1],
}
OWN_NEGATIVE_CODE = "R009_OBSTRUCTION_DROPPED"
MARKS = ("marked", "plain")


def _decide(payload):
    objects = [_nat(x) for x in _seq(payload["objects"])]
    _require(len(set(objects)) == len(objects), "R_SCHEMA")
    arrows = {}
    for entry in _seq(payload["arrows"]):
        _seq(entry, 4)
        name, source, target, mark = _text(entry[0]), _nat(entry[1]), _nat(entry[2]), entry[3]
        _require(name not in arrows and source in objects and target in objects and mark in MARKS, "R_SCHEMA")
        arrows[name] = (source, target, mark)
    dagger = {}
    for pair in _seq(payload["dagger"]):
        _seq(pair, 2)
        _require(pair[0] in arrows and pair[1] in arrows and pair[0] not in dagger, "R_SCHEMA")
        dagger[pair[0]] = pair[1]
    _require(set(dagger) == set(arrows), "R009_NOT_TOTAL")
    for f in arrows:
        _require(dagger[dagger[f]] == f, "R009_NOT_INVOLUTION")
    for f, (source, target, _) in arrows.items():
        _require(arrows[dagger[f]][:2] == (target, source), "R009_ENDPOINTS")
    for f, (_, _, mark) in arrows.items():
        _require(arrows[dagger[f]][2] == mark, "R009_OBSTRUCTION_DROPPED")
    composites = set()
    for triple in _seq(payload["composites"]):
        _seq(triple, 3)
        _require(all(isinstance(n, str) and n in arrows for n in triple), "R_SCHEMA")
        f, g, h = triple
        typed = arrows[f][1] == arrows[g][0] and arrows[h][:2] == (arrows[f][0], arrows[g][1])
        _require(typed, "R009_COMPOSITE_TYPING")
        composites.add((f, g, h))
    for f, g, h in composites:
        _require((dagger[g], dagger[f], dagger[h]) in composites, "R009_VARIANCE")
