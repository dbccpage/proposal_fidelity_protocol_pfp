"""Target checker of record for MSS-011, row 11 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 11): replay each substitution and both arms of a join.
Negative instance: an empty join of distinct nonnormal terms is rejected.

Input (closed): ``{"rules": [[lhs, rhs]], "source": str, "left_step":
[position, rule], "right_step": [position, rule], "left_arm": [[position,
rule]], "right_arm": [[position, rule]], "join": str}``. Terms are strings;
a rule rewrites one occurrence of its left side at the given position.

Every step, including both peak steps, is replayed from its term; nothing a
payload declares about an intermediate term is read.

Clauses:

- C1 ``R011_BAD_REDEX``: a step's rule does not occur at its position;
- C2 ``R011_EMPTY_JOIN``: both arms are empty but the two peak terms differ;
- C3 ``R011_ARMS_DISAGREE``: the replayed arms end at different terms;
- C4 ``R011_JOIN_MISMATCH``: the declared join is not where the arms end.
"""

STAGE = 11
ROW_SHA256 = "sha256:1e20f663b686450709c4289f30d1d4b8005587213b477df8e3081726d434bfef"
FIELDS = ("join", "left_arm", "left_step", "right_arm", "right_step", "rules", "source")
CLAUSES = (
    ("C1", "R011_BAD_REDEX"),
    ("C2", "R011_EMPTY_JOIN"),
    ("C3", "R011_ARMS_DISAGREE"),
    ("C4", "R011_JOIN_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "join": "xc",
    "left_arm": [],
    "left_step": [0, 0],
    "right_arm": [],
    "right_step": [1, 1],
    "rules": [["ab", "x"], ["bc", "y"], ["x", "z"], ["y", "z"]],
    "source": "abc",
}
OWN_NEGATIVE_CODE = "R011_EMPTY_JOIN"


def _decide(payload):
    rules = []
    for rule in _seq(payload["rules"]):
        _seq(rule, 2)
        _require(isinstance(rule[1], str), "R_SCHEMA")
        rules.append((_text(rule[0]), rule[1]))
    _require(rules, "R_SCHEMA")

    def apply(term, step):
        _seq(step, 2)
        position, index = _nat(step[0]), _nat(step[1])
        _require(index < len(rules), "R_SCHEMA")
        lhs, rhs = rules[index]
        _require(term[position : position + len(lhs)] == lhs, "R011_BAD_REDEX")
        return term[:position] + rhs + term[position + len(lhs) :]

    source = _text(payload["source"])
    left = apply(source, payload["left_step"])
    right = apply(source, payload["right_step"])
    left_arm, right_arm = _seq(payload["left_arm"]), _seq(payload["right_arm"])
    left_end, right_end = left, right
    for step in left_arm:
        left_end = apply(left_end, step)
    for step in right_arm:
        right_end = apply(right_end, step)
    join = payload["join"]
    _require(isinstance(join, str), "R_SCHEMA")
    if not left_arm and not right_arm:
        _require(left == right, "R011_EMPTY_JOIN")
    _require(left_end == right_end, "R011_ARMS_DISAGREE")
    _require(left_end == join, "R011_JOIN_MISMATCH")
