"""Target checker of record for MSS-046, row 46 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 46): require an external checker and decrease on recursive
calls. Negative instance: a self-certified unbounded evaluation is refused.

Input (closed): ``{"input": nat, "base": [[nat, nat]], "step": [k, c],
"measure": [a, b], "interpreter": "sha256:<hex>", "confirmations":
[["sha256:<hex>", nat]], "output": nat}``. The program is one recursive
function on naturals: f(n) is the declared base value when n is a base case,
and f(n - k) + c otherwise. ``measure`` declares the termination measure
m(n) = a n + b. ``interpreter`` is the digest of the evaluator that produced
``output``; each confirmation is a checker's digest and the output it
reports.

Declared input class: this one-function recursion scheme with linear
measures, inputs at most 10000. The target checker runs the program itself,
and checks the declared measure at each recursive call before making it, so
it never runs an unbounded evaluation. The external checker's identity is a
declared digest: what is decided is only that it differs from the
interpreter's and that its reported output agrees with the recomputation.
A self-description run by its own interpreter is not modelled.

Clauses, each recomputed:

- C1 ``R046_NO_DECREASE``: at some recursive call the declared measure does
  not strictly decrease, or the call leaves the naturals (the level's
  negative);
- C2 ``R046_NO_EXTERNAL_CHECKER``: no confirmation comes from a digest other
  than the interpreter's, so the evaluation is self-certified;
- C3 ``R046_OUTPUT_MISMATCH``: the declared output, or a confirmation's
  reported output, is not the recomputed value.
"""

STAGE = 46
ROW_SHA256 = "sha256:4e960077a1593dc2a33501be67b8a79d0668c7362a931f5f5f05daf6e293f65e"
FIELDS = ("base", "confirmations", "input", "interpreter", "measure", "output", "step")
CLAUSES = (
    ("C1", "R046_NO_DECREASE"),
    ("C2", "R046_NO_EXTERNAL_CHECKER"),
    ("C3", "R046_OUTPUT_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_SELF = "sha256:" + "a" * 64
OWN_NEGATIVE = {
    "base": [[0, 0]],
    "confirmations": [[_SELF, 0]],
    "input": 3,
    "interpreter": _SELF,
    "measure": [1, 0],
    "output": 0,
    "step": [0, 0],
}
OWN_NEGATIVE_CODE = "R046_NO_DECREASE"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def _digest_text(value):
    _require(isinstance(value, str) and _DIGEST.fullmatch(value) is not None, "R_SCHEMA")
    return value


def _decide(payload):
    n = _nat(payload["input"])
    _require(n <= 10000, "R_SCHEMA")
    base = {}
    for row in _seq(payload["base"]):
        _seq(row, 2)
        case, value = _nat(row[0]), _nat(row[1])
        _require(case not in base, "R_SCHEMA")
        base[case] = value
    step = _seq(payload["step"], 2)
    k, c = _nat(step[0]), _nat(step[1])
    measure = _seq(payload["measure"], 2)
    a, b = _nat(measure[0]), _nat(measure[1])
    interpreter = _digest_text(payload["interpreter"])
    confirmations = []
    for row in _seq(payload["confirmations"]):
        _seq(row, 2)
        confirmations.append((_digest_text(row[0]), _nat(row[1])))
    total, calls = 0, 0
    while n not in base:
        _require(n >= k and a * (n - k) + b < a * n + b, "R046_NO_DECREASE")
        calls += 1
        _require(calls <= 10000, "R_SCHEMA")
        n -= k
        total += c
    value = base[n] + total
    _require(any(digest != interpreter for digest, _ in confirmations), "R046_NO_EXTERNAL_CHECKER")
    _require(_nat(payload["output"]) == value, "R046_OUTPUT_MISMATCH")
    _require(all(reported == value for _, reported in confirmations), "R046_OUTPUT_MISMATCH")
