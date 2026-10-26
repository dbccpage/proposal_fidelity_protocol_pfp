"""Target checker of record for MSS-020, row 20 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 20): compare full canonical states and detect nondecreasing
repeated cycles. Negative instance: a decreasing recursive call is not
declared an expansion cycle.

Input (closed): ``{"trace": [state], "cycles": [[i, j]]}``. A state is a
nonempty JSON object. Its canonical key is its full sorted serialization; its
measure is the sum of the nonnegative integers anywhere in it (an integer
measure, recomputed, never declared). A declared cycle ``[i, j]`` (i < j)
claims an expansion cycle: a revisit of the full state with a measure that
did not decrease.

Clauses:

- C1 ``R020_DECREASING_CALL``: a declared cycle's measure strictly decreases,
  so it is productive recursion, not a cycle (the negative);
- C2 ``R020_PROJECTION_REPEAT``: a declared cycle's two full states differ
  (a projection, such as the head symbol, repeated; the state did not);
- C3 ``R020_UNDECLARED_CYCLE``: a full-state revisit is not declared. Each
  revisit at j must be declared from the latest earlier i with the same key.
"""

STAGE = 20
ROW_SHA256 = "sha256:cd373079137699264ed68ef68063a0b60062630afec45db6932d19a2addea36b"
FIELDS = ("cycles", "trace")
CLAUSES = (
    ("C1", "R020_DECREASING_CALL"),
    ("C2", "R020_PROJECTION_REPEAT"),
    ("C3", "R020_UNDECLARED_CYCLE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "cycles": [[0, 2]],
    "trace": [{"args": [2], "call": "f"}, {"args": [1], "call": "f"}, {"args": [0], "call": "f"}],
}
OWN_NEGATIVE_CODE = "R020_DECREASING_CALL"


def _key(value):
    if isinstance(value, dict):
        return "{" + ",".join(repr(k) + ":" + _key(value[k]) for k in sorted(value)) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_key(item) for item in value) + "]"
    _require(value is None or isinstance(value, (str, int)), "R_SCHEMA")
    return repr(value)


def _measure(value):
    if isinstance(value, dict):
        return sum(_measure(item) for item in value.values())
    if isinstance(value, list):
        return sum(_measure(item) for item in value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return 0


def _decide(payload):
    trace = _seq(payload["trace"])
    _require(len(trace) >= 2 and all(isinstance(state, dict) and state for state in trace), "R_SCHEMA")
    keys = [_key(state) for state in trace]
    measures = [_measure(state) for state in trace]
    declared = set()
    for pair in _seq(payload["cycles"]):
        _seq(pair, 2)
        first, second = _nat(pair[0]), _nat(pair[1])
        _require(first < second < len(trace) and (first, second) not in declared, "R_SCHEMA")
        declared.add((first, second))
    for first, second in sorted(declared):
        _require(measures[second] >= measures[first], "R020_DECREASING_CALL")
        _require(keys[first] == keys[second], "R020_PROJECTION_REPEAT")
    for second in range(len(trace)):
        earlier = [first for first in range(second) if keys[first] == keys[second]]
        if earlier:
            _require((max(earlier), second) in declared, "R020_UNDECLARED_CYCLE")
