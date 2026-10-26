"""Target checker of record for MSS-022, row 22 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 22): check reindexing identity and fiber typing for every
declared base arrow. Negative instance: a term reindexed into the wrong fiber
is rejected.

Input (closed): ``{"objects": [[name, [term]]], "arrows": [[name, source,
target, [[term, term]]]], "identities": [[object, arrow]], "composites":
[[f, g, h]]}``. Each object carries its fibre, a finite list of terms; fibres
are pairwise disjoint. An arrow ``a -> b`` carries its reindexing table,
contravariant: it sends each term of the fibre over ``b`` to a term of the
fibre over ``a``. A composite ``[f, g, h]`` declares h = g after f, so its
reindexing must be f's after g's.

Declared input class: a finite base presented by its arrows, one declared
identity per object and declared binary composites; reindexing tables are
arbitrary finite maps (not required to be bijective). Associativity of the
base is not decided here; only the declared composites are.

Clauses, each recomputed by applying the tables, never read from a label:

- C1 ``R022_WRONG_FIBRE``: a reindexed term lies outside the fibre over the
  arrow's source (the level's negative);
- C2 ``R022_PARTIAL_TABLE``: a table is not a map on the fibre over the
  arrow's target (a term missing, repeated, or foreign);
- C3 ``R022_IDENTITY_LAW``: an object has no declared identity, or its
  identity is not an endo-arrow whose table is the identity;
- C4 ``R022_NON_FUNCTORIAL``: for a declared composite h = g f, the table of h
  differs from f's after g's at some term;
- C5 ``R022_BASE_NOT_CLOSED``: a composite names an arrow that is not declared
  or does not chain, or two composable non-identity arrows have no declared
  composite.
"""

STAGE = 22
ROW_SHA256 = "sha256:5302b29621885daae547a0c2f52a7e509b33fa4ceec2b32566a06ec47b1e0466"
FIELDS = ("arrows", "composites", "identities", "objects")
CLAUSES = (
    ("C1", "R022_WRONG_FIBRE"),
    ("C2", "R022_PARTIAL_TABLE"),
    ("C3", "R022_IDENTITY_LAW"),
    ("C4", "R022_NON_FUNCTORIAL"),
    ("C5", "R022_BASE_NOT_CLOSED"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ("reindexing",)
OWN_NEGATIVE = {
    "arrows": [
        ["id0", "0", "0", [["p", "p"], ["q", "q"]]],
        ["id1", "1", "1", [["r", "r"], ["s", "s"]]],
        ["id2", "2", "2", [["t", "t"], ["u", "u"]]],
        ["f", "0", "1", [["r", "t"], ["s", "p"]]],
    ],
    "composites": [],
    "identities": [["0", "id0"], ["1", "id1"], ["2", "id2"]],
    "objects": [["0", ["p", "q"]], ["1", ["r", "s"]], ["2", ["t", "u"]]],
}
OWN_NEGATIVE_CODE = "R022_WRONG_FIBRE"


def _decide(payload):
    fibres, owner = {}, {}
    for entry in _seq(payload["objects"]):
        _seq(entry, 2)
        name = _text(entry[0])
        terms = [_text(t) for t in _seq(entry[1])]
        _require(name not in fibres and terms and len(set(terms)) == len(terms), "R_SCHEMA")
        for term in terms:
            _require(term not in owner, "R_SCHEMA")
            owner[term] = name
        fibres[name] = set(terms)
    arrows = {}
    for entry in _seq(payload["arrows"]):
        _seq(entry, 4)
        name, source, target = _text(entry[0]), _text(entry[1]), _text(entry[2])
        _require(name not in arrows and source in fibres and target in fibres, "R_SCHEMA")
        table = {}
        for row in _seq(entry[3]):
            _seq(row, 2)
            term, image = _text(row[0]), _text(row[1])
            _require(term in fibres[target] and term not in table, "R022_PARTIAL_TABLE")
            table[term] = image
        _require(set(table) == fibres[target], "R022_PARTIAL_TABLE")
        for image in table.values():
            _require(image in fibres[source], "R022_WRONG_FIBRE")
        arrows[name] = (source, target, table)
    identity = {}
    for entry in _seq(payload["identities"]):
        _seq(entry, 2)
        obj, name = _text(entry[0]), _text(entry[1])
        _require(obj in fibres and obj not in identity and name in arrows, "R_SCHEMA")
        identity[obj] = name
    for obj in fibres:
        _require(obj in identity, "R022_IDENTITY_LAW")
        source, target, table = arrows[identity[obj]]
        _require(source == obj and target == obj, "R022_IDENTITY_LAW")
        _require(all(table[t] == t for t in table), "R022_IDENTITY_LAW")
    identities = set(identity.values())
    declared = set()
    for entry in _seq(payload["composites"]):
        _seq(entry, 3)
        f, g, h = (_text(n) for n in entry)
        _require(f in arrows and g in arrows and h in arrows, "R022_BASE_NOT_CLOSED")
        fs, ft, ftab = arrows[f]
        gs, gt, gtab = arrows[g]
        hs, ht, htab = arrows[h]
        _require(ft == gs and (hs, ht) == (fs, gt), "R022_BASE_NOT_CLOSED")
        for term in htab:
            _require(htab[term] == ftab[gtab[term]], "R022_NON_FUNCTORIAL")
        declared.add((f, g))
    for f, (_, ft, _) in arrows.items():
        for g, (gs, _, _) in arrows.items():
            if f in identities or g in identities or ft != gs:
                continue
            _require((f, g) in declared, "R022_BASE_NOT_CLOSED")
