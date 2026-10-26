"""Target checker of record for MSS-093, row 93 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 93): check source target simulation on bounded fragment.
Negative instance: a compiled branch changing outcome is rejected.

Input (closed): ``{"source": expr, "target": [instruction], "inputs": [n],
"fuel": f, "outcomes": [[n, value]]}``.

Source language (evaluated here): ``["num", k]``, ``["var"]`` (the input),
``["add", a, b]``, ``["sub", a, b]``, ``["if_lt", a, b, then, else]``.
Target language (run here): a stack machine with ``["push", k]``,
``["load"]``, ``["add"]``, ``["sub"]``, ``["jlt", t]`` (pop b, pop a, jump
to t when a < b), ``["jmp", t]`` and ``["halt"]``; the result is the top of
the stack at ``halt``. Integers are exact and unbounded.

The bounded fragment is the declared inputs under the declared fuel. For each
input the checker evaluates the source, runs the target, and compares; it also
requires the inputs to take both arms of every source branch, so no compiled
branch goes unexercised. The claimed outcome table must be the source's.

Declared input class: loop-free source expressions; target programs of any
shape under fuel at most 100000; natural inputs.

Clauses, decided in this order:

- C1 ``R093_BAD_TARGET``: a jump leaves the program, or the stack underflows
  or is empty at ``halt``;
- C2 ``R093_UNCOVERED_BRANCH``: some arm of a source branch is taken by no
  declared input;
- C3 ``R093_TARGET_DIVERGES``: the target does not halt within the fuel on
  some input;
- C4 ``R093_BRANCH_CHANGES_OUTCOME``: the target's result differs from the
  source's on some input (the level's negative);
- C5 ``R093_OUTCOME_TABLE``: the outcome table is not the source's results
  on exactly the declared inputs.
"""

STAGE = 93
ROW_SHA256 = "sha256:bcb25dc969fa8e6dc4074f743d1d605b7baa5f32a6eb1fd2240651c221011dc9"
FIELDS = ("fuel", "inputs", "outcomes", "source", "target")
CLAUSES = (
    ("C1", "R093_BAD_TARGET"),
    ("C2", "R093_UNCOVERED_BRANCH"),
    ("C3", "R093_TARGET_DIVERGES"),
    ("C4", "R093_BRANCH_CHANGES_OUTCOME"),
    ("C5", "R093_OUTCOME_TABLE"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
_SOURCE = ["if_lt", ["var"], ["num", 3], ["add", ["var"], ["num", 10]], ["sub", ["var"], ["num", 3]]]
# The two arms compiled in swapped places: n < 3 runs the else code.
OWN_NEGATIVE = {
    "fuel": 100,
    "inputs": [1, 5],
    "outcomes": [[1, 11], [5, 2]],
    "source": _SOURCE,
    "target": [["load"], ["push", 3], ["jlt", 7], ["load"], ["push", 10], ["add"], ["halt"],
               ["load"], ["push", 3], ["sub"], ["halt"]],
}
OWN_NEGATIVE_CODE = "R093_BRANCH_CHANGES_OUTCOME"
_SHAPES = {"num": 2, "var": 1, "add": 3, "sub": 3, "if_lt": 5}
_OPS = {"push": 2, "load": 1, "add": 1, "sub": 1, "jlt": 2, "jmp": 2, "halt": 1}


def _expr(value, depth=0):
    _require(isinstance(value, list) and value and depth <= 64, "R_SCHEMA")
    _require(_SHAPES.get(value[0]) == len(value), "R_SCHEMA")
    if value[0] == "num":
        _nat(value[1])
    for part in value[1:] if value[0] != "num" else ():
        _expr(part, depth + 1)
    return value


def _evaluate(expr, n, taken, path="r"):
    head = expr[0]
    if head == "num":
        return expr[1]
    if head == "var":
        return n
    if head == "add":
        return _evaluate(expr[1], n, taken, path + "a") + _evaluate(expr[2], n, taken, path + "b")
    if head == "sub":
        return _evaluate(expr[1], n, taken, path + "a") - _evaluate(expr[2], n, taken, path + "b")
    arm = 3 if _evaluate(expr[1], n, taken, path + "a") < _evaluate(expr[2], n, taken, path + "b") else 4
    taken.add((path, arm))
    return _evaluate(expr[arm], n, taken, path + str(arm))


def _branches(expr, path="r"):
    head = expr[0]
    if head in ("num", "var"):
        return set()
    out = _branches(expr[1], path + "a") | _branches(expr[2], path + "b")
    if head == "if_lt":
        out |= {(path, 3), (path, 4)}
        out |= _branches(expr[3], path + "3") | _branches(expr[4], path + "4")
    return out


def _run(target, n, fuel):
    """(``"HALT"``, value), (``"FUEL"``, None) or (``"BAD"``, None)."""
    stack, pc = [], 0
    for _ in range(fuel + 1):
        if not 0 <= pc < len(target):
            return "BAD", None
        op = target[pc]
        kind = op[0]
        if kind == "halt":
            return ("HALT", stack[-1]) if stack else ("BAD", None)
        if kind == "push":
            stack.append(op[1])
        elif kind == "load":
            stack.append(n)
        elif kind in ("add", "sub", "jlt"):
            if len(stack) < 2:
                return "BAD", None
            b, a = stack.pop(), stack.pop()
            if kind == "add":
                stack.append(a + b)
            elif kind == "sub":
                stack.append(a - b)
            elif a < b:
                pc = op[1]
                continue
        elif kind == "jmp":
            pc = op[1]
            continue
        pc += 1
    return "FUEL", None


def _decide(payload):
    source = _expr(payload["source"])
    target = _seq(payload["target"])
    _require(target, "R_SCHEMA")
    for op in target:
        _require(isinstance(op, list) and op and _OPS.get(op[0]) == len(op), "R_SCHEMA")
        if len(op) == 2:
            _nat(op[1])
    inputs = [_nat(n) for n in _seq(payload["inputs"])]
    _require(inputs and len(set(inputs)) == len(inputs), "R_SCHEMA")
    fuel = _nat(payload["fuel"])
    _require(fuel <= 100000, "R_SCHEMA")
    outcomes = {}
    for row in _seq(payload["outcomes"]):
        _seq(row, 2)
        _require(isinstance(row[1], int) and not isinstance(row[1], bool) and _nat(row[0]) not in outcomes, "R_SCHEMA")
        outcomes[row[0]] = row[1]
    _require(all(op[1] < len(target) for op in target if op[0] in ("jlt", "jmp")), "R093_BAD_TARGET")
    taken = set()
    expected = {n: _evaluate(source, n, taken) for n in inputs}
    runs = {n: _run(target, n, fuel) for n in inputs}
    _require(all(kind != "BAD" for kind, _ in runs.values()), "R093_BAD_TARGET")
    _require(_branches(source) <= taken, "R093_UNCOVERED_BRANCH")
    _require(all(kind == "HALT" for kind, _ in runs.values()), "R093_TARGET_DIVERGES")
    _require(all(runs[n][1] == expected[n] for n in inputs), "R093_BRANCH_CHANGES_OUTCOME")
    _require(outcomes == expected, "R093_OUTCOME_TABLE")
