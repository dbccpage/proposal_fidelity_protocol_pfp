"""Target checker of record for MSS-044, row 44 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 44): check precondition and postcondition with declared
decidable theory. Negative instance: a satisfiable looking assertion without
solver witness remains pending.

Input (closed): ``{"domain": [lo, hi], "claims": [[name, [lo, hi], ["add",
c], [lo, hi], standing, witness]]}``. A claim is a triple {pre} x := x + c
{post} over the integer x in the declared domain, with interval pre- and
postconditions. ``standing`` is "PROVED", "REFUTED" or "PENDING". A PROVED
claim's witness is the list of every domain value satisfying the
precondition (an enumeration certificate); a REFUTED claim's witness is one
counterexample value; a PENDING claim has no witness (null).

Declared input class: the decidable theory of one natural-number variable
over a finite interval domain, interval predicates and increment programs.
The witness is replayed by enumeration; no solver output is trusted. A
PENDING claim is always acceptable: pending asserts nothing.

Clauses, each recomputed:

- C1 ``R044_NO_WITNESS``: a claim stands as PROVED with no witness (the
  level's negative: it remains pending);
- C2 ``R044_WITNESS_INCOMPLETE``: a PROVED witness is not exactly the domain
  values satisfying the precondition;
- C3 ``R044_WITNESS_FAILS``: a value in a PROVED witness violates the
  postcondition after the program;
- C4 ``R044_BAD_COUNTEREXAMPLE``: a REFUTED claim's counterexample does not
  satisfy the precondition and violate the postcondition.
"""

STAGE = 44
ROW_SHA256 = "sha256:26bd8ffd176c77e6a0898a3cc3f4ca90ea3cb357aae5f1accce73309356d6122"
FIELDS = ("claims", "domain")
CLAUSES = (
    ("C1", "R044_NO_WITNESS"),
    ("C2", "R044_WITNESS_INCOMPLETE"),
    ("C3", "R044_WITNESS_FAILS"),
    ("C4", "R044_BAD_COUNTEREXAMPLE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {
    "claims": [["C", [0, 3], ["add", 1], [1, 4], "PROVED", None]],
    "domain": [0, 3],
}
OWN_NEGATIVE_CODE = "R044_NO_WITNESS"
STANDINGS = ("PENDING", "PROVED", "REFUTED")


def _interval(value):
    pair = _seq(value, 2)
    lo, hi = _nat(pair[0]), _nat(pair[1])
    _require(lo <= hi, "R_SCHEMA")
    return lo, hi


def _decide(payload):
    lo, hi = _interval(payload["domain"])
    _require(hi - lo <= 10000, "R_SCHEMA")
    names = set()
    for entry in _seq(payload["claims"]):
        _seq(entry, 6)
        name = _text(entry[0])
        pre, post = _interval(entry[1]), _interval(entry[3])
        program = _seq(entry[2], 2)
        _require(program[0] == "add" and name not in names, "R_SCHEMA")
        names.add(name)
        step = _nat(program[1])
        standing, witness = entry[4], entry[5]
        _require(standing in STANDINGS, "R_SCHEMA")
        models = [x for x in range(lo, hi + 1) if pre[0] <= x <= pre[1]]
        if standing == "PENDING":
            _require(witness is None, "R_SCHEMA")
        elif standing == "PROVED":
            _require(witness is not None, "R044_NO_WITNESS")
            cases = [_nat(x) for x in _seq(witness)]
            _require(cases == models, "R044_WITNESS_INCOMPLETE")
            for x in cases:
                _require(post[0] <= x + step <= post[1], "R044_WITNESS_FAILS")
        else:
            x = _nat(witness)
            ok = lo <= x <= hi and pre[0] <= x <= pre[1] and not post[0] <= x + step <= post[1]
            _require(ok, "R044_BAD_COUNTEREXAMPLE")
