"""Target checker of record for MSS-025, row 25 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 25): check weak-equivalence class and well-typed roofs in a
declared model. Negative instance: an untyped inverted arrow is rejected.

Input (closed): ``{"objects": [name], "arrows": [[name, source, target]],
"identities": [[object, arrow]], "compose": [[first, second, result]],
"weak": [arrow], "roofs": [[inverted, forward, from, to]]}``. ``compose``
is the full composition table of the declared finite category: one row per
composable pair, ``[f, g, h]`` meaning h = g after f. A roof ``[w, f, b,
c]`` presents f after the formal inverse of w, a formal arrow b -> c; its
left leg w must be a weak equivalence with target b, and f must share w's
source and end at c.

Declared input class: a finite category given by a full composition table.
The checker decides the category laws, the class of weak equivalences
(containing identities, closed under composition) and the typing of every
declared roof. It does not compute localized hom-sets or roof equivalence
(Ore conditions are not decided).

Clauses, each recomputed from the tables:

- C1 ``R025_NOT_A_CATEGORY``: the composition table is not total on
  composable pairs, is ill-typed, breaks an identity law or associativity;
- C2 ``R025_WEQ_NOT_CLOSED``: the weak class misses an identity or is not
  closed under composition;
- C3 ``R025_UNTYPED_INVERSE``: a roof inverts an arrow outside the weak class
  (the level's negative);
- C4 ``R025_ROOF_TYPE``: a roof's legs do not share a source, or its declared
  endpoints are not the targets of its legs.
"""

STAGE = 25
ROW_SHA256 = "sha256:8839292d3f8c549ec3424352142ab923c225655d79fde5aaee7027af730e25a1"
FIELDS = ("arrows", "compose", "identities", "objects", "roofs", "weak")
CLAUSES = (
    ("C1", "R025_NOT_A_CATEGORY"),
    ("C2", "R025_WEQ_NOT_CLOSED"),
    ("C3", "R025_UNTYPED_INVERSE"),
    ("C4", "R025_ROOF_TYPE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "arrows": [["ida", "a", "a"], ["idb", "b", "b"], ["idc", "c", "c"], ["w", "a", "b"], ["f", "a", "c"]],
    "compose": [
        ["ida", "ida", "ida"], ["idb", "idb", "idb"], ["idc", "idc", "idc"],
        ["ida", "w", "w"], ["w", "idb", "w"], ["ida", "f", "f"], ["f", "idc", "f"],
    ],
    "identities": [["a", "ida"], ["b", "idb"], ["c", "idc"]],
    "objects": ["a", "b", "c"],
    "roofs": [["f", "w", "c", "b"]],
    "weak": ["ida", "idb", "idc", "w"],
}
OWN_NEGATIVE_CODE = "R025_UNTYPED_INVERSE"


def _decide(payload):
    objects = [_text(o) for o in _seq(payload["objects"])]
    _require(len(set(objects)) == len(objects), "R_SCHEMA")
    arrows = {}
    for entry in _seq(payload["arrows"]):
        _seq(entry, 3)
        name, source, target = (_text(x) for x in entry)
        _require(name not in arrows and source in objects and target in objects, "R_SCHEMA")
        arrows[name] = (source, target)
    identity = {}
    for entry in _seq(payload["identities"]):
        _seq(entry, 2)
        obj, name = _text(entry[0]), _text(entry[1])
        _require(obj in objects and obj not in identity and name in arrows, "R_SCHEMA")
        identity[obj] = name
    _require(set(identity) == set(objects), "R_SCHEMA")
    comp = {}
    for entry in _seq(payload["compose"]):
        _seq(entry, 3)
        f, g, h = (_text(x) for x in entry)
        _require(f in arrows and g in arrows and h in arrows and (f, g) not in comp, "R_SCHEMA")
        ok = arrows[f][1] == arrows[g][0] and arrows[h] == (arrows[f][0], arrows[g][1])
        _require(ok, "R025_NOT_A_CATEGORY")
        comp[(f, g)] = h
    for f in arrows:
        for g in arrows:
            if arrows[f][1] == arrows[g][0]:
                _require((f, g) in comp, "R025_NOT_A_CATEGORY")
    for obj, i in identity.items():
        _require(arrows[i] == (obj, obj), "R025_NOT_A_CATEGORY")
    for f, (source, target) in arrows.items():
        _require(comp[(identity[source], f)] == f and comp[(f, identity[target])] == f, "R025_NOT_A_CATEGORY")
    for (f, g), fg in comp.items():
        for h in arrows:
            if arrows[g][1] == arrows[h][0]:
                _require(comp[(fg, h)] == comp[(f, comp[(g, h)])], "R025_NOT_A_CATEGORY")
    weak = [_text(w) for w in _seq(payload["weak"])]
    _require(len(set(weak)) == len(weak) and set(weak) <= set(arrows), "R_SCHEMA")
    weak = set(weak)
    _require(set(identity.values()) <= weak, "R025_WEQ_NOT_CLOSED")
    for (f, g), h in comp.items():
        _require(not (f in weak and g in weak) or h in weak, "R025_WEQ_NOT_CLOSED")
    for entry in _seq(payload["roofs"]):
        _seq(entry, 4)
        w, f, start, end = (_text(x) for x in entry)
        _require(w in arrows and f in arrows and start in objects and end in objects, "R_SCHEMA")
        _require(w in weak, "R025_UNTYPED_INVERSE")
        _require(arrows[w][0] == arrows[f][0], "R025_ROOF_TYPE")
        _require((arrows[w][1], arrows[f][1]) == (start, end), "R025_ROOF_TYPE")
