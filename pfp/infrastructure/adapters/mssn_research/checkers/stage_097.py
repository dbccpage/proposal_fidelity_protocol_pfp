"""Target checker of record for MSS-097, row 97 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 97): check changed fixtures fail for the intended invariant.
Negative instance: a surviving dangerous mutation is flagged.

Input (closed): ``{"invariants": [name], "fixture": [nat], "mutants":
[[operator, position, value, intended]], "kill_matrix": [[name]]}``.

The invariants and the mutation operators are pinned in this file. The
invariants are ``nondecreasing``, ``distinct`` and ``nonempty``. The
operators act on the fixture: ``set`` (position gets value), ``delete``
(remove position), ``duplicate`` (insert a copy after position) and ``swap``
(exchange position and position + 1); value is read by ``set`` only. The
checker applies every operator itself, so the changed fixtures are computed,
never supplied, and evaluates every declared invariant on every mutant. Row i
of the kill matrix lists, sorted, the invariants mutant i violates. Every
declared mutant counts as dangerous: one that no invariant kills survives.

Declared input class: the pinned invariants and operators on lists of
naturals of length at most 64.

Clauses, decided in this order:

- C1 ``R097_BASE_FAILS``: the unmutated fixture violates a declared
  invariant;
- C2 ``R097_NOT_CHANGED``: an operator leaves the fixture unchanged;
- C3 ``R097_SURVIVING_MUTANT``: no declared invariant kills a mutant (the
  level's negative);
- C4 ``R097_WRONG_INVARIANT``: a mutant's intended invariant does not kill
  it;
- C5 ``R097_KILL_MATRIX``: the kill matrix is not the recomputed one.
"""

STAGE = 97
ROW_SHA256 = "sha256:29a5984485ff07f23341a7f41d18b1894849feca32090b790034c7833023ad33"
FIELDS = ("fixture", "invariants", "kill_matrix", "mutants")
CLAUSES = (
    ("C1", "R097_BASE_FAILS"),
    ("C2", "R097_NOT_CHANGED"),
    ("C3", "R097_SURVIVING_MUTANT"),
    ("C4", "R097_WRONG_INVARIANT"),
    ("C5", "R097_KILL_MATRIX"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
INVARIANTS = {
    "distinct": lambda xs: len(set(xs)) == len(xs),
    "nondecreasing": lambda xs: all(a <= b for a, b in zip(xs, xs[1:])),
    "nonempty": lambda xs: len(xs) > 0,
}
OWN_NEGATIVE = {
    "fixture": [1, 2],
    "invariants": ["nondecreasing"],
    "kill_matrix": [[]],
    "mutants": [["set", 1, 3, "nondecreasing"]],
}
OWN_NEGATIVE_CODE = "R097_SURVIVING_MUTANT"


def _apply(fixture, operator, position, value):
    out = list(fixture)
    _require(position < len(out), "R_SCHEMA")
    if operator == "set":
        out[position] = value
    elif operator == "delete":
        del out[position]
    elif operator == "duplicate":
        out.insert(position + 1, out[position])
    else:
        _require(operator == "swap" and position + 1 < len(out), "R_SCHEMA")
        out[position], out[position + 1] = out[position + 1], out[position]
    return out


def _decide(payload):
    names = [_text(name) for name in _seq(payload["invariants"])]
    _require(names and len(set(names)) == len(names) and set(names) <= set(INVARIANTS), "R_SCHEMA")
    fixture = [_nat(v) for v in _seq(payload["fixture"])]
    _require(len(fixture) <= 64, "R_SCHEMA")
    mutants = []
    for mutant in _seq(payload["mutants"]):
        _seq(mutant, 4)
        _require(mutant[0] in ("set", "delete", "duplicate", "swap") and mutant[3] in names, "R_SCHEMA")
        changed = _apply(fixture, mutant[0], _nat(mutant[1]), _nat(mutant[2]))
        mutants.append((changed, mutant[3]))
    _require(mutants, "R_SCHEMA")
    matrix = [[_text(name) for name in _seq(row)] for row in _seq(payload["kill_matrix"])]
    _require(all(INVARIANTS[name](fixture) for name in names), "R097_BASE_FAILS")
    for changed, _ in mutants:
        _require(changed != fixture, "R097_NOT_CHANGED")
    killed = [sorted(name for name in names if not INVARIANTS[name](changed)) for changed, _ in mutants]
    for row in killed:
        _require(row, "R097_SURVIVING_MUTANT")
    for row, (_, intended) in zip(killed, mutants):
        _require(intended in row, "R097_WRONG_INVARIANT")
    _require(matrix == killed, "R097_KILL_MATRIX")
