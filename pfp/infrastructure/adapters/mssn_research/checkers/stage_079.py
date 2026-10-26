"""Target checker of record for MSS-079, row 79 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 79): check commutativity associativity and idempotence on
bounded domain. Negative instance: a nonidempotent merge is rejected.

Input (closed): ``{"states": [s], "merge": [[a, b, c]]}``: a merge table
over a declared finite set of replica states, one row a ⊔ b = c for every
ordered pair (a, b).

The checker requires the table to be total and closed, then decides the three
join laws by exhaustion over the declared states: idempotence on every state,
associativity on every triple, commutativity on every pair. It computes
nothing from a declared law name.

Declared input class: merge operations given as full tables over at most 12
states. A merge given by a rule over an unbounded domain is outside it.

Clauses, decided in this order:

- C1 ``R079_TABLE``: an ordered pair has no row or two rows, or a result is
  not a declared state;
- C2 ``R079_NOT_IDEMPOTENT``: a ⊔ a differs from a for some state (the
  level's negative);
- C3 ``R079_NOT_ASSOCIATIVE``: (a ⊔ b) ⊔ c differs from a ⊔ (b ⊔ c) for some
  triple;
- C4 ``R079_NOT_COMMUTATIVE``: a ⊔ b differs from b ⊔ a for some pair.
"""

STAGE = 79
ROW_SHA256 = "sha256:a2259994673cef9b9e56242bd42c0505a9830bc3abbd0fe013b454ac072507f0"
FIELDS = ("merge", "states")
CLAUSES = (
    ("C1", "R079_TABLE"),
    ("C2", "R079_NOT_IDEMPOTENT"),
    ("C3", "R079_NOT_ASSOCIATIVE"),
    ("C4", "R079_NOT_COMMUTATIVE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
# Counts merged by capped addition: commutative and associative, but 1 + 1 = 2.
OWN_NEGATIVE = {
    "merge": [[a, b, str(min(int(a) + int(b), 2))] for a in ("0", "1", "2") for b in ("0", "1", "2")],
    "states": ["0", "1", "2"],
}
OWN_NEGATIVE_CODE = "R079_NOT_IDEMPOTENT"


def _decide(payload):
    states = [_text(s) for s in _seq(payload["states"])]
    _require(states and len(set(states)) == len(states) and len(states) <= 12, "R_SCHEMA")
    table = {}
    for row in _seq(payload["merge"]):
        _seq(row, 3)
        a, b, c = (_text(part) for part in row)
        _require((a, b) not in table, "R079_TABLE")
        table[(a, b)] = c
    domain = set(states)
    _require(set(table) == {(a, b) for a in states for b in states}, "R079_TABLE")
    _require(all(c in domain for c in table.values()), "R079_TABLE")
    for a in states:
        _require(table[(a, a)] == a, "R079_NOT_IDEMPOTENT")
    for a in states:
        for b in states:
            for c in states:
                _require(table[(table[(a, b)], c)] == table[(a, table[(b, c)])], "R079_NOT_ASSOCIATIVE")
    for a in states:
        for b in states:
            _require(table[(a, b)] == table[(b, a)], "R079_NOT_COMMUTATIVE")
