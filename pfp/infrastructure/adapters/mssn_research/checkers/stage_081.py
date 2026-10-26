"""Target checker of record for MSS-081, row 81 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 81): check composition against declared finite privacy
budget. Negative instance: a release exceeding remaining budget is refused.

Input (closed): ``{"columns": [name], "records": [[value]], "k": k, "budget":
B, "releases": [{"attributes": [name], "cost": c, "remaining": r}]}``. B, c
and r are canonical rationals; every cost is positive.

Two compositions are decided exactly:

- the budget composes sequentially: after release i the remaining budget is
  B minus the sum of costs 1..i, and no release may cost more than what
  remains before it;
- the releases compose jointly: a reader holding every release can group the
  records by the union of all released attributes, and every class of that
  joint partition must hold at least k records.

Declared input class: sequential composition of declared rational costs;
k-anonymity of partition releases over a finite table. No noise mechanism is
modelled, and no probabilistic privacy guarantee is claimed.

Clauses, decided in this order:

- C1 ``R081_BUDGET_EXCEEDED``: a release costs more than the budget remaining
  before it (the level's negative);
- C2 ``R081_LEDGER_MISMATCH``: a claimed remaining budget is not B minus the
  costs so far;
- C3 ``R081_JOINT_CLASS_TOO_SMALL``: a class of the joint partition holds
  fewer than k records.
"""

STAGE = 81
ROW_SHA256 = "sha256:e9f8e45a27d5448881f447be82366dd74cefdbd08eeb1be48d27a68a0af45f1b"
FIELDS = ("budget", "columns", "k", "records", "releases")
CLAUSES = (
    ("C1", "R081_BUDGET_EXCEEDED"),
    ("C2", "R081_LEDGER_MISMATCH"),
    ("C3", "R081_JOINT_CLASS_TOO_SMALL"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "budget": "1/2",
    "columns": ["age", "zip"],
    "k": 2,
    "records": [["30", "a"], ["30", "a"], ["40", "b"], ["40", "b"]],
    "releases": [
        {"attributes": ["age"], "cost": "1/4", "remaining": "1/4"},
        {"attributes": ["zip"], "cost": "1/2", "remaining": "0/1"},
    ],
}
OWN_NEGATIVE_CODE = "R081_BUDGET_EXCEEDED"


def _decide(payload):
    columns = [_text(c) for c in _seq(payload["columns"])]
    _require(columns and len(set(columns)) == len(columns), "R_SCHEMA")
    records = [tuple(_text(v) for v in _seq(r, len(columns))) for r in _seq(payload["records"])]
    k = _nat(payload["k"])
    budget = _rat(payload["budget"])
    _require(records and k >= 1 and budget >= 0, "R_SCHEMA")
    releases = []
    for release in _seq(payload["releases"]):
        _require(isinstance(release, dict) and set(release) == {"attributes", "cost", "remaining"}, "R_SCHEMA")
        attributes = [_text(a) for a in _seq(release["attributes"])]
        _require(attributes and set(attributes) <= set(columns), "R_SCHEMA")
        cost = _rat(release["cost"])
        _require(cost > 0, "R_SCHEMA")
        releases.append((attributes, cost, _rat(release["remaining"])))
    _require(releases, "R_SCHEMA")
    left = budget
    for _, cost, _ in releases:
        _require(cost <= left, "R081_BUDGET_EXCEEDED")
        left -= cost
    left = budget
    for _, cost, remaining in releases:
        left -= cost
        _require(remaining == left, "R081_LEDGER_MISMATCH")
    released = sorted({columns.index(a) for attributes, _, _ in releases for a in attributes})
    classes = {}
    for record in records:
        key = tuple(record[i] for i in released)
        classes[key] = classes.get(key, 0) + 1
    _require(min(classes.values()) >= k, "R081_JOINT_CLASS_TOO_SMALL")
