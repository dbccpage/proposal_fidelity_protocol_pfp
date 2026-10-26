"""Target checker of record for MSS-024, row 24 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 24): check mono factorization and a commuting classifier
pullback. Negative instance: an arbitrary boolean label without characteristic
pullback is rejected.

Input (closed): ``{"stages": [name], "below": [[q, p]], "elements": [[stage,
[element]]], "restrictions": [[p, q, [[x, y]]]], "subfamily": [[stage,
[element]]], "labels": [[stage, element, [stage]]]}``. ``below`` lists strict
pairs q < p of a finite order (closed here under transitivity). A family X
gives a finite set at each stage and a restriction map X(p) -> X(q) for every
q < p. ``subfamily`` is A, with A(p) a subset of X(p). The label of x in X(p)
is a truth value at p: a down-closed set of stages at or below p.

Declared input class: families of finite sets over a finite order (presheaves
on a finite poset). Here truth values are down-sets, so a stage with two
stages below it already has more than two truth values; this is why finite
sets alone cannot refute the negative instance.

Clauses, recomputed from the family, never read from a declared label:

- C1 ``R024_NOT_A_FAMILY``: a restriction map is missing, not total, lands
  outside X(q), or the restrictions do not compose;
- C2 ``R024_NOT_MONO``: A is not closed under restriction, so A -> X is not a
  subfamily;
- C3 ``R024_LABEL_MISMATCH``: a label is missing or differs from the
  recomputed one, the set of q <= p with x|q in A(q);
- C4 ``R024_NOT_PULLBACK``: on the declared labels, A(p) is not the set of x
  whose label is all of the stages at or below p (the level's negative: a
  two-valued label for a middle subfamily).

C4 is decided on the declared labels before they are recomputed, so a label
that breaks the pullback square is refused as such.
"""

STAGE = 24
ROW_SHA256 = "sha256:becd84ea09e5326cc6aba6d122059792ba1fe2d0bdf8deb383ac858dff8c6d4a"
FIELDS = ("below", "elements", "labels", "restrictions", "stages", "subfamily")
CLAUSES = (
    ("C1", "R024_NOT_A_FAMILY"),
    ("C2", "R024_NOT_MONO"),
    ("C3", "R024_LABEL_MISMATCH"),
    ("C4", "R024_NOT_PULLBACK"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "below": [["0", "1"]],
    "elements": [["0", ["x0"]], ["1", ["x1"]]],
    "labels": [["0", "x0", ["0"]], ["1", "x1", ["0", "1"]]],
    "restrictions": [["1", "0", [["x1", "x0"]]]],
    "stages": ["0", "1"],
    "subfamily": [["0", ["x0"]], ["1", []]],
}
OWN_NEGATIVE_CODE = "R024_NOT_PULLBACK"


def _per_stage(rows, stages):
    out = {}
    for row in _seq(rows):
        _seq(row, 2)
        stage = _text(row[0])
        items = [_text(x) for x in _seq(row[1])]
        _require(stage in stages and stage not in out and len(set(items)) == len(items), "R_SCHEMA")
        out[stage] = set(items)
    _require(set(out) == set(stages), "R_SCHEMA")
    return out


def _decide(payload):
    stages = [_text(s) for s in _seq(payload["stages"])]
    _require(len(set(stages)) == len(stages), "R_SCHEMA")
    less = set()
    for pair in _seq(payload["below"]):
        _seq(pair, 2)
        q, p = _text(pair[0]), _text(pair[1])
        _require(q in stages and p in stages and q != p, "R_SCHEMA")
        less.add((q, p))
    changed = True
    while changed:
        changed = False
        for (a, b) in list(less):
            for (c, d) in list(less):
                if b == c and (a, d) not in less:
                    _require(a != d, "R_SCHEMA")
                    less.add((a, d))
                    changed = True
    down = {p: {p} | {q for (q, r) in less if r == p} for p in stages}
    X = _per_stage(payload["elements"], stages)
    A = _per_stage(payload["subfamily"], stages)
    for p in stages:
        _require(A[p] <= X[p], "R_SCHEMA")
    res = {}
    for entry in _seq(payload["restrictions"]):
        _seq(entry, 3)
        p, q = _text(entry[0]), _text(entry[1])
        _require((q, p) in less and (p, q) not in res, "R_SCHEMA")
        table = {}
        for row in _seq(entry[2]):
            _seq(row, 2)
            x, y = _text(row[0]), _text(row[1])
            _require(x in X[p] and x not in table and y in X[q], "R024_NOT_A_FAMILY")
            table[x] = y
        _require(set(table) == X[p], "R024_NOT_A_FAMILY")
        res[(p, q)] = table
    _require(set(res) == {(p, q) for (q, p) in less}, "R024_NOT_A_FAMILY")

    def restrict(x, p, q):
        return x if p == q else res[(p, q)][x]

    for (q, p) in less:
        for (r, q2) in less:
            if q2 == q:
                for x in X[p]:
                    _require(res[(q, r)][res[(p, q)][x]] == res[(p, r)][x], "R024_NOT_A_FAMILY")
    for (q, p) in less:
        for x in A[p]:
            _require(res[(p, q)][x] in A[q], "R024_NOT_MONO")
    labels = {}
    for entry in _seq(payload["labels"]):
        _seq(entry, 3)
        p, x = _text(entry[0]), _text(entry[1])
        value = [_text(s) for s in _seq(entry[2])]
        _require(p in X and x in X[p] and (p, x) not in labels and len(set(value)) == len(value), "R_SCHEMA")
        labels[(p, x)] = set(value)
    for p in stages:
        full = {x for x in X[p] if labels.get((p, x)) == down[p]}
        _require(full == A[p], "R024_NOT_PULLBACK")
    for p in stages:
        for x in X[p]:
            recomputed = {q for q in down[p] if restrict(x, p, q) in A[q]}
            _require(labels.get((p, x)) == recomputed, "R024_LABEL_MISMATCH")
