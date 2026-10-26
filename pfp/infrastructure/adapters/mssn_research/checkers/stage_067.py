"""Target checker of record for MSS-067, row 67 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 67): require a formal reduction before a hardness claim.
Negative instance: surrogate database keys alone do not prove hardness.

Input (closed): ``{"source": family, "target": family, "bound": n,
"reduction": [[x, y]] | null, "evidence": [[kind, text]] | null}``. A family is a
decision problem on natural-number instances that this checker decides
itself: ``"even"``, ``"odd"``, ``"multiple_of_3"``, ``"square"`` or
``"zero"``. ``reduction`` is the producer's map, one row per source instance
0..n; answers are recomputed on both sides, never read. ``evidence`` lists
anything else offered in support (keys, labels, instance or term counts,
timings).

Declared input class: the five families above, source instances 0..n with
n <= 10000, target instances <= 10^6. This is a fence: the checker verifies
that a declared reduction preserves answers on every instance up to the
bound. It proves no hardness, and no class or asymptotic claim descends from a
PASS.

Clauses, decided in this order:

- C1 ``R067_SURROGATE_EVIDENCE``: evidence other than null is offered (keys,
  labels, counts and timings are never evidence of a reduction; the level's
  negative);
- C2 ``R067_NO_REDUCTION``: no reduction is given;
- C3 ``R067_NOT_TOTAL``: the reduction does not give exactly one image for
  every source instance 0..n;
- C4 ``R067_NOT_PRESERVING``: some instance x has answer_target(f(x)) !=
  answer_source(x).
"""

STAGE = 67
ROW_SHA256 = "sha256:cd60bc922455ac1bd9acb27c8ca2980b4186105cf3aec82f307c705a3b1c9b68"
FIELDS = ("bound", "evidence", "reduction", "source", "target")
CLAUSES = (
    ("C1", "R067_SURROGATE_EVIDENCE"),
    ("C2", "R067_NO_REDUCTION"),
    ("C3", "R067_NOT_TOTAL"),
    ("C4", "R067_NOT_PRESERVING"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "bound": 5,
    "evidence": [["database_keys", "40320 surrogate keys, one per term of the expansion"]],
    "reduction": None,
    "source": "even",
    "target": "multiple_of_3",
}
OWN_NEGATIVE_CODE = "R067_SURROGATE_EVIDENCE"


def _square(n):
    root = 0
    while root * root < n:
        root += 1
    return root * root == n


_FAMILIES = {
    "even": lambda n: n % 2 == 0,
    "odd": lambda n: n % 2 == 1,
    "multiple_of_3": lambda n: n % 3 == 0,
    "square": _square,
    "zero": lambda n: n == 0,
}


def _decide(payload):
    source, target = payload["source"], payload["target"]
    _require(source in _FAMILIES and target in _FAMILIES, "R_SCHEMA")
    bound = _nat(payload["bound"])
    _require(bound <= 10000, "R_SCHEMA")
    evidence = payload["evidence"]
    reduction = payload["reduction"]
    _require(evidence is None, "R067_SURROGATE_EVIDENCE")
    _require(reduction is not None, "R067_NO_REDUCTION")
    images = {}
    for item in _seq(reduction):
        _seq(item, 2)
        x, y = _nat(item[0]), _nat(item[1])
        _require(y <= 10 ** 6, "R_SCHEMA")
        _require(x not in images, "R067_NOT_TOTAL")
        images[x] = y
    _require(set(images) == set(range(bound + 1)), "R067_NOT_TOTAL")
    for x in range(bound + 1):
        _require(_FAMILIES[target](images[x]) == _FAMILIES[source](x), "R067_NOT_PRESERVING")
