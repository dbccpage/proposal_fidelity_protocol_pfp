"""Target checker of record for MSS-013, row 13 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 13): check repeated state with unchanged progress and replay
chosen route. Negative instance: a syntactic route code alone cannot certify
exact repair.

Input (closed): ``{"d0": [[q]], "d1": [[q]], "cases": [{"cochain": [q],
"route": str, "witness": [q] or null}], "trace": [[case index, route]],
"cycle": [i, j]}``. ``d0`` is the m x n coboundary (one row per edge), ``d1``
the k x m one (one row per 2-cell; it may have no rows).

Each case's route is replayed with its witness, over the rationals:

- ``exact``: the witness alpha has d0 alpha = omega;
- ``residual_closed``: d1 omega = 0, and the witness y has d0^T y = 0 with
  <y, omega> != 0, which excludes every potential because <y, d0 alpha> =
  <d0^T y, alpha> = 0;
- ``open``: d1 omega != 0; no witness is taken.

A traced state is the full pair (cochain, route). Progress is a function of
that full state, so a repeat with unchanged progress is decided by comparing
full states, never a route code alone.

Clauses:

- C1 ``R013_BOARD_INVALID``: d1 d0 != 0;
- C2 ``R013_MISSING_WITNESS``: an exact or residual route carries no witness
  (the negative: a route code alone);
- C3 ``R013_EXACT_NOT_REPLAYED``: d0 alpha != omega;
- C4 ``R013_DUAL_NOT_REPLAYED``: the dual witness fails a condition above;
- C5 ``R013_OPEN_NOT_REPLAYED``: an open route with d1 omega = 0;
- C6 ``R013_NO_REPEAT``: the declared cycle's two traced states differ.
"""

STAGE = 13
ROW_SHA256 = "sha256:232f0130ed7aada454e16f90b0aece5081ee5aa10c98252ca42a55ae629e14f6"
FIELDS = ("cases", "cycle", "d0", "d1", "trace")
CLAUSES = (
    ("C1", "R013_BOARD_INVALID"),
    ("C2", "R013_MISSING_WITNESS"),
    ("C3", "R013_EXACT_NOT_REPLAYED"),
    ("C4", "R013_DUAL_NOT_REPLAYED"),
    ("C5", "R013_OPEN_NOT_REPLAYED"),
    ("C6", "R013_NO_REPEAT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
ROUTES = ("exact", "open", "residual_closed")
OWN_NEGATIVE = {
    "cases": [{"cochain": ["0/1", "0/1", "1/1"], "route": "exact", "witness": None}],
    "cycle": [0, 1],
    "d0": [["-1/1", "1/1", "0/1"], ["0/1", "-1/1", "1/1"], ["1/1", "0/1", "-1/1"]],
    "d1": [],
    "trace": [[0, "exact"], [0, "exact"]],
}
OWN_NEGATIVE_CODE = "R013_MISSING_WITNESS"


def _apply(matrix, vector):
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def _transpose(matrix, columns):
    return [[row[j] for row in matrix] for j in range(columns)]


def _decide(payload):
    d0 = _matrix(payload["d0"])
    m = len(d0)
    _require(m >= 1 and len(d0[0]) >= 1, "R_SCHEMA")
    n = len(d0[0])
    d1 = _matrix(payload["d1"], columns=m)
    for column in _transpose(d0, n):
        _require(all(value == 0 for value in _apply(d1, column)), "R013_BOARD_INVALID")
    states = []
    for case in _seq(payload["cases"]):
        _require(isinstance(case, dict) and set(case) == {"cochain", "route", "witness"}, "R_SCHEMA")
        omega = _rats(case["cochain"], m)
        route = case["route"]
        _require(route in ROUTES, "R_SCHEMA")
        witness = case["witness"]
        if route == "open":
            _require(witness is None, "R_SCHEMA")
            _require(any(value != 0 for value in _apply(d1, omega)), "R013_OPEN_NOT_REPLAYED")
        elif route == "exact":
            _require(witness is not None, "R013_MISSING_WITNESS")
            _require(_apply(d0, _rats(witness, n)) == omega, "R013_EXACT_NOT_REPLAYED")
        else:
            _require(witness is not None, "R013_MISSING_WITNESS")
            y = _rats(witness, m)
            closed = all(value == 0 for value in _apply(d1, omega))
            divergence_free = all(value == 0 for value in _apply(_transpose(d0, n), y))
            pairing = sum((a * b for a, b in zip(y, omega)), Fraction(0))
            _require(closed and divergence_free and pairing != 0, "R013_DUAL_NOT_REPLAYED")
        states.append((tuple(omega), route))
    trace = []
    for entry in _seq(payload["trace"]):
        _seq(entry, 2)
        index = _nat(entry[0])
        _require(index < len(states) and entry[1] == states[index][1], "R_SCHEMA")
        trace.append(states[index])
    cycle = _seq(payload["cycle"], 2)
    first, second = _nat(cycle[0]), _nat(cycle[1])
    _require(first < second < len(trace), "R_SCHEMA")
    _require(trace[first] == trace[second], "R013_NO_REPEAT")
