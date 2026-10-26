"""Target checker of record for MSS-098, row 98 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 98): run independent implementations on same canonical input.
Negative instance: different outputs cannot be silently merged.

Input (closed): ``{"function": name, "impl_a": name, "impl_b": name,
"cases": [[input, out_a, out_b]], "merged": [[input, output]],
"disagreements": [input]}``.

The implementations are pinned in this file, each written independently of
its sibling:

- ``round`` (a canonical rational to an integer): ``half_up`` and
  ``half_even``, which disagree exactly on ties;
- ``gcd`` (a pair of naturals, not both zero): ``euclid`` and ``binary``;
- ``isqrt`` (a natural): ``newton`` and ``bisect``.

Every input is canonical (a reduced rational, a natural or a pair of
naturals). The checker runs both named implementations on every input and
compares their outputs with the claimed ones. Where they agree the output may
be merged; where they differ the input must be recorded as a disagreement and
must not be merged. Every agreeing case is merged exactly once.

Declared input class: the three pinned functions and their six
implementations.

Clauses, decided in this order:

- C1 ``R098_NOT_INDEPENDENT``: both sides name the same implementation;
- C2 ``R098_OUTPUT_MISMATCH``: a claimed output is not what its
  implementation returns;
- C3 ``R098_SILENT_MERGE``: a case whose outputs differ is merged (the
  level's negative);
- C4 ``R098_DISAGREEMENT_RECORD``: the disagreements are not exactly the
  differing inputs, or an agreeing case is not merged with its output.
"""

STAGE = 98
ROW_SHA256 = "sha256:f6633a56c62ecc80e410ed1fc1517c062905e9107fa8c82877dd11978f930b76"
FIELDS = ("cases", "disagreements", "function", "impl_a", "impl_b", "merged")
CLAUSES = (
    ("C1", "R098_NOT_INDEPENDENT"),
    ("C2", "R098_OUTPUT_MISMATCH"),
    ("C3", "R098_SILENT_MERGE"),
    ("C4", "R098_DISAGREEMENT_RECORD"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def _half_up(x):
    return (2 * x.numerator + x.denominator) // (2 * x.denominator)


def _half_even(x):
    whole = x.numerator // x.denominator
    rest = x - whole
    if rest > Fraction(1, 2) or (rest == Fraction(1, 2) and whole % 2 == 1):
        return whole + 1
    return whole


def _euclid(pair):
    a, b = pair
    while b:
        a, b = b, a % b
    return a


def _binary(pair):
    a, b = pair
    if a == 0 or b == 0:
        return a + b
    shift = 0
    while (a | b) % 2 == 0:
        a, b, shift = a // 2, b // 2, shift + 1
    while a % 2 == 0:
        a //= 2
    while b:
        while b % 2 == 0:
            b //= 2
        if a > b:
            a, b = b, a
        b -= a
    return a * 2 ** shift


def _newton(n):
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x, y = y, (y + n // y) // 2
    return x


def _bisect(n):
    low, high = 0, n + 1
    while high - low > 1:
        middle = (low + high) // 2
        if middle * middle <= n:
            low = middle
        else:
            high = middle
    return low


def _read_rational(value):
    return _rat(value)


def _read_pair(value):
    pair = [_nat(v) for v in _seq(value, 2)]
    _require(pair[0] or pair[1], "R_SCHEMA")
    return tuple(pair)


FUNCTIONS = {
    "gcd": (_read_pair, {"binary": _binary, "euclid": _euclid}),
    "isqrt": (_nat, {"bisect": _bisect, "newton": _newton}),
    "round": (_read_rational, {"half_even": _half_even, "half_up": _half_up}),
}
OWN_NEGATIVE = {
    "cases": [["5/2", 3, 2], ["7/3", 2, 2]],
    "disagreements": [],
    "function": "round",
    "impl_a": "half_up",
    "impl_b": "half_even",
    "merged": [["5/2", 3], ["7/3", 2]],
}
OWN_NEGATIVE_CODE = "R098_SILENT_MERGE"


def _key(value):
    return repr(value)


def _integer(value):
    _require(isinstance(value, int) and not isinstance(value, bool), "R_SCHEMA")
    return value


def _decide(payload):
    _require(payload["function"] in FUNCTIONS, "R_SCHEMA")
    read, implementations = FUNCTIONS[payload["function"]]
    impl_a, impl_b = payload["impl_a"], payload["impl_b"]
    _require(impl_a in implementations and impl_b in implementations, "R_SCHEMA")
    cases = []
    for case in _seq(payload["cases"]):
        _seq(case, 3)
        cases.append((_key(case[0]), read(case[0]), _integer(case[1]), _integer(case[2])))
    _require(cases and len({key for key, _, _, _ in cases}) == len(cases), "R_SCHEMA")
    merged = {}
    for row in _seq(payload["merged"]):
        _seq(row, 2)
        key = _key(row[0])
        _require(key not in merged, "R_SCHEMA")
        merged[key] = _integer(row[1])
    recorded = [_key(item) for item in _seq(payload["disagreements"])]
    _require(len(set(recorded)) == len(recorded), "R_SCHEMA")
    _require(impl_a != impl_b, "R098_NOT_INDEPENDENT")
    runs = [(key, implementations[impl_a](x), implementations[impl_b](x), a, b) for key, x, a, b in cases]
    for _, out_a, out_b, a, b in runs:
        _require((out_a, out_b) == (a, b), "R098_OUTPUT_MISMATCH")
    differing = {key for key, out_a, out_b, _, _ in runs if out_a != out_b}
    _require(not (differing & set(merged)), "R098_SILENT_MERGE")
    agreeing = {key: out_a for key, out_a, out_b, _, _ in runs if out_a == out_b}
    _require(set(recorded) == differing and merged == agreeing, "R098_DISAGREEMENT_RECORD")
