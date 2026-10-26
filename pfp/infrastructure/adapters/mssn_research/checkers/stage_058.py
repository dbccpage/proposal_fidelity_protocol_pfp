"""Target checker of record for MSS-058, row 58 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 58): check consistent shared outcome labels on overlapping
contexts. Negative instance: a context assignment inconsistent on an overlap
is rejected.

Input (closed): ``{"labels": [label], "contexts": [[name, [item], rule]],
"family": [[name, [label]]]}``. Each context names its items (distinct
strings) and a local rule: ``"differ"`` (the chosen labels are pairwise
distinct) or ``"equal"`` (they are all the same). ``family`` gives one local
choice per context, one label per item in the context's item order.

Declared input class: finite scenarios with explicit contexts and labels from
a declared finite label set; the two local rules above. Agreement is checked
on every pair of contexts that share an item, not only on neighbours in list
order. This checker decides a claimed family; it does not certify that no
agreeing family exists.

Clauses, decided in this order:

- C1 ``R058_CONTEXT``: the family does not give exactly one choice for every
  declared context, or a choice has the wrong length;
- C2 ``R058_LOCAL_RULE``: a choice uses an undeclared label or breaks its
  context's rule;
- C3 ``R058_OVERLAP``: two contexts sharing an item give it different labels
  (the level's negative).
"""

STAGE = 58
ROW_SHA256 = "sha256:ccd5d1f1707770f002a24289938a4534163d2a53203e30b868aecc7fcf1dfff3"
FIELDS = ("contexts", "family", "labels")
CLAUSES = (
    ("C1", "R058_CONTEXT"),
    ("C2", "R058_LOCAL_RULE"),
    ("C3", "R058_OVERLAP"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "contexts": [["C1", ["x", "y"], "differ"], ["C2", ["y", "z"], "differ"], ["C3", ["z", "x"], "differ"]],
    "family": [["C1", [0, 1]], ["C2", [1, 0]], ["C3", [0, 1]]],
    "labels": [0, 1],
}
OWN_NEGATIVE_CODE = "R058_OVERLAP"
_RULES = ("differ", "equal")


def _decide(payload):
    labels = [_nat(label) for label in _seq(payload["labels"])]
    _require(labels and len(set(labels)) == len(labels), "R_SCHEMA")
    contexts = {}
    for item in _seq(payload["contexts"]):
        _seq(item, 3)
        name = _text(item[0])
        items = [_text(x) for x in _seq(item[1])]
        _require(name not in contexts and items and len(set(items)) == len(items), "R_SCHEMA")
        _require(item[2] in _RULES, "R_SCHEMA")
        contexts[name] = (items, item[2])
    _require(contexts, "R_SCHEMA")
    family = {}
    for item in _seq(payload["family"]):
        _seq(item, 2)
        name = _text(item[0])
        _require(name in contexts and name not in family, "R058_CONTEXT")
        family[name] = [_nat(label) for label in _seq(item[1])]
    _require(set(family) == set(contexts), "R058_CONTEXT")
    _require(all(len(family[name]) == len(contexts[name][0]) for name in contexts), "R058_CONTEXT")
    for name, (items, rule) in contexts.items():
        choice = family[name]
        _require(all(label in labels for label in choice), "R058_LOCAL_RULE")
        if rule == "differ":
            _require(len(set(choice)) == len(choice), "R058_LOCAL_RULE")
        else:
            _require(len(set(choice)) == 1, "R058_LOCAL_RULE")
    names = sorted(contexts)
    for a in names:
        for b in names:
            if a < b:
                left = dict(zip(contexts[a][0], family[a]))
                right = dict(zip(contexts[b][0], family[b]))
                _require(all(left[x] == right[x] for x in set(left) & set(right)), "R058_OVERLAP")
