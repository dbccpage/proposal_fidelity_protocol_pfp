"""Target checker of record for MSS-041, row 41 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 41): check use counts and typed tensor introduction. Negative
instance: a protected resource duplicated without contraction is rejected.

Input (closed): ``{"context": [[name, kind]], "duplicable": [kind], "term":
term, "type": type}``. A term is ``["var", x]``, ``["pair", t, u]`` (tensor
introduction), ``["dup", x, y, z, t]`` (contraction: consumes x and binds y
and z, both of x's kind, in t) or ``["drop", x, t]`` (weakening: consumes x
unused). A type is a kind name or a pair ``[type, type]``, the tensor of the
two. Contraction and weakening are allowed only on a kind listed as
duplicable.

Declared input class: finite derivation trees of this linear term language;
use counts are computed from the leaves and the binders, never read.

Clauses, each recomputed:

- C1 ``R041_UNTYPED``: a variable is used that is neither in the context nor
  bound by an enclosing contraction;
- C2 ``R041_DUPLICATE``: a variable is consumed more than once without a
  contraction (the level's negative);
- C3 ``R041_UNUSED``: a variable is never consumed, with no weakening;
- C4 ``R041_CONTRACTION_KIND``: a contraction or weakening is applied to a
  variable whose kind is not duplicable;
- C5 ``R041_TYPE_MISMATCH``: the declared type is not the recomputed tensor
  type of the term.
"""

STAGE = 41
ROW_SHA256 = "sha256:b29ce667d49cf231dfb11b6bdb415d3046af7fbb6efeb3fa68ba6a759b2bdcac"
FIELDS = ("context", "duplicable", "term", "type")
CLAUSES = (
    ("C1", "R041_UNTYPED"),
    ("C2", "R041_DUPLICATE"),
    ("C3", "R041_UNUSED"),
    ("C4", "R041_CONTRACTION_KIND"),
    ("C5", "R041_TYPE_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "context": [["r", "A"], ["s", "B"]],
    "duplicable": [],
    "term": ["pair", ["var", "r"], ["var", "r"]],
    "type": ["A", "A"],
}
OWN_NEGATIVE_CODE = "R041_DUPLICATE"


def _type(value):
    if isinstance(value, str):
        return _text(value)
    pair = _seq(value, 2)
    return (_type(pair[0]), _type(pair[1]))


def _decide(payload):
    kinds = {}
    for entry in _seq(payload["context"]):
        _seq(entry, 2)
        name, kind = _text(entry[0]), _text(entry[1])
        _require(name not in kinds, "R_SCHEMA")
        kinds[name] = kind
    duplicable = {_text(k) for k in _seq(payload["duplicable"])}
    uses = {name: 0 for name in kinds}
    scope = dict(kinds)
    retired = set()

    def consume(name):
        _require(isinstance(name, str) and name in scope, "R041_UNTYPED")
        uses[name] = uses.get(name, 0) + 1
        _require(uses[name] == 1, "R041_DUPLICATE")
        return scope[name]

    def walk(term):
        node = _seq(term)
        _require(node and node[0] in ("var", "pair", "dup", "drop"), "R_SCHEMA")
        if node[0] == "var":
            _seq(node, 2)
            return consume(node[1])
        if node[0] == "pair":
            _seq(node, 3)
            return (walk(node[1]), walk(node[2]))
        if node[0] == "drop":
            _seq(node, 3)
            _require(consume(node[1]) in duplicable, "R041_CONTRACTION_KIND")
            return walk(node[2])
        _seq(node, 5)
        kind = consume(node[1])
        _require(kind in duplicable, "R041_CONTRACTION_KIND")
        fresh = (_text(node[2]), _text(node[3]))
        _require(fresh[0] != fresh[1] and all(n not in scope and n not in retired for n in fresh), "R_SCHEMA")
        for n in fresh:
            scope[n] = kind
            uses[n] = 0
        result = walk(node[4])
        _require(all(uses[n] == 1 for n in fresh), "R041_UNUSED")
        for n in fresh:
            del scope[n]
            del uses[n]
            retired.add(n)
        return result

    computed = walk(payload["term"])
    _require(all(count == 1 for count in uses.values()), "R041_UNUSED")
    _require(_type(payload["type"]) == computed, "R041_TYPE_MISMATCH")
