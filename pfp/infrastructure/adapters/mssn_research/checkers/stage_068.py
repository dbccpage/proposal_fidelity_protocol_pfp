"""Target checker of record for MSS-068, row 68 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing.

Obligation (row 68): check outward enclosure on every rational operation.
Negative instance: an approximation without a certified bound is rejected.

Input (closed): ``{"values": [[name, [lo, hi]]], "steps": [[name, op, a, b,
[lo, hi]]], "grid": g}``. Every value is a bound with exact canonical
rational ends. A step applies ``op`` (``"add"``, ``"sub"``, ``"mul"`` or
``"div"``) to two earlier names and claims a result bound, rounded outward to
the declared grid (ends with denominators dividing g). Later steps use the
claimed bounds of earlier ones.

The checker computes the exact result bound of every step from its operand
bounds (the four end products for ``mul``; ``div`` multiplies by
[1/hi, 1/lo] and needs a divisor bound excluding 0) and requires the claimed
bound to contain it. Rounding inward, or to the nearest grid point, fails
containment.

Declared input class: finite straight-line programs of the four operations
over exact rational bounds; g >= 1.

Clauses, decided in this order:

- C1 ``R068_NO_BOUND``: a value or claimed result is not a two-end bound of
  canonical rationals, for example a bare decimal (the level's negative);
- C2 ``R068_EMPTY``: a bound has lo > hi;
- C3 ``R068_DIVISOR_ZERO``: a division's divisor bound contains 0;
- C4 ``R068_NOT_ENCLOSED``: a claimed result bound does not contain the exact
  result bound;
- C5 ``R068_OFF_GRID``: a claimed result end is not on the declared grid.
"""

STAGE = 68
ROW_SHA256 = "sha256:840c2bb61b295b340c766b45b54436f2b6a934e6b2b17a1748261f30d82ec5de"
FIELDS = ("grid", "steps", "values")
CLAUSES = (
    ("C1", "R068_NO_BOUND"),
    ("C2", "R068_EMPTY"),
    ("C3", "R068_DIVISOR_ZERO"),
    ("C4", "R068_NOT_ENCLOSED"),
    ("C5", "R068_OFF_GRID"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
OWN_NEGATIVE = {"grid": 100, "steps": [], "values": [["x", "1.4142"]]}
OWN_NEGATIVE_CODE = "R068_NO_BOUND"
_OPS = ("add", "sub", "mul", "div")


def _bound(value):
    _require(isinstance(value, list) and len(value) == 2, "R068_NO_BOUND")
    _require(all(isinstance(end, str) and _RATIONAL.fullmatch(end) for end in value), "R068_NO_BOUND")
    try:
        return (_rat(value[0]), _rat(value[1]))
    except _Refused:
        _refuse("R068_NO_BOUND")


def _exact(op, a, b):
    if op == "add":
        return (a[0] + b[0], a[1] + b[1])
    if op == "sub":
        return (a[0] - b[1], a[1] - b[0])
    if op == "div":
        b = (1 / b[1], 1 / b[0])
    products = [x * y for x in a for y in b]
    return (min(products), max(products))


def _decide(payload):
    grid = _nat(payload["grid"])
    _require(grid >= 1, "R_SCHEMA")
    names, bounds = [], []
    for item in _seq(payload["values"]):
        _seq(item, 2)
        names.append(_text(item[0]))
        bounds.append(_bound(item[1]))
    steps = []
    for item in _seq(payload["steps"]):
        _seq(item, 5)
        name, op, a, b = _text(item[0]), item[1], item[2], item[3]
        _require(op in _OPS and a in names and b in names, "R_SCHEMA")
        names.append(name)
        claimed = _bound(item[4])
        bounds.append(claimed)
        steps.append((op, names.index(a), names.index(b), claimed))
    _require(names and len(set(names)) == len(names), "R_SCHEMA")
    _require(all(lo <= hi for lo, hi in bounds), "R068_EMPTY")
    for op, _, b, _ in steps:
        _require(op != "div" or not (bounds[b][0] <= 0 <= bounds[b][1]), "R068_DIVISOR_ZERO")
    for op, a, b, claimed in steps:
        lo, hi = _exact(op, bounds[a], bounds[b])
        _require(claimed[0] <= lo and hi <= claimed[1], "R068_NOT_ENCLOSED")
    for _, _, _, claimed in steps:
        _require(all(grid % end.denominator == 0 for end in claimed), "R068_OFF_GRID")
