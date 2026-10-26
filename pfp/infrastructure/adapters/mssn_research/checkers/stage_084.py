"""Target checker of record for MSS-084, row 84 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 84): validate arguments and compare actual tool result digest.
Negative instance: a guessed tool result is rejected.

Input (closed): ``{"calls": [{"tool": name, "args": {name: value},
"result_digest": d}]}``. The result digest is the SHA-256 of the canonical
JSON of the tool's result (sorted keys, no whitespace, ASCII).

The tools are pinned in this file, reimplemented here from their declared
contracts, so the checker runs the actual tool rather than trusting a
receipt:

- ``gcd`` ``{a: nat, b: nat}``, not both zero -> nat;
- ``sort`` ``{items: [nat]}`` -> the items in nondecreasing order;
- ``sum`` ``{terms: [rational]}`` -> their exact sum, as a canonical rational;
- ``count`` ``{text: str, needle: nonempty str}`` -> non-overlapping
  occurrences, scanning left to right.

Declared input class: calls to these four pinned tools. A call to any other
tool is refused as unattested: this checker cannot run it, and a digest it
cannot recompute is capped, never accepted.

Clauses, decided in this order:

- C1 ``R084_UNKNOWN_TOOL``: the tool is not one of the pinned tools;
- C2 ``R084_ARGUMENTS``: the arguments do not meet the tool's schema (names,
  types, ranges);
- C3 ``R084_GUESSED_RESULT``: the claimed result digest is not the digest of
  the tool's actual result (the level's negative).
"""

import hashlib
import json

STAGE = 84
ROW_SHA256 = "sha256:2492159cc26cbb9d6695c388a16360e53ffb610a70e263b88af363ca20751608"
FIELDS = ("calls",)
CLAUSES = (
    ("C1", "R084_UNKNOWN_TOOL"),
    ("C2", "R084_ARGUMENTS"),
    ("C3", "R084_GUESSED_RESULT"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()


def result_digest(result):
    text = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(text.encode("ascii")).hexdigest()


def _is_nat(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_rat(value):
    match = _RATIONAL.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return False
    sign, num, den = match.groups()
    return Fraction(int(num), int(den)).denominator == int(den) and not (sign and num == "0")


def _canonical_rational(value):
    sign = "-" if value < 0 else ""
    return f"{sign}{abs(value.numerator)}/{value.denominator}"


def _gcd(args):
    _require(set(args) == {"a", "b"} and _is_nat(args["a"]) and _is_nat(args["b"]), "R084_ARGUMENTS")
    _require(args["a"] or args["b"], "R084_ARGUMENTS")
    a, b = args["a"], args["b"]
    while b:
        a, b = b, a % b
    return a


def _sort(args):
    _require(set(args) == {"items"} and isinstance(args["items"], list), "R084_ARGUMENTS")
    _require(all(_is_nat(item) for item in args["items"]), "R084_ARGUMENTS")
    return sorted(args["items"])


def _sum(args):
    _require(set(args) == {"terms"} and isinstance(args["terms"], list), "R084_ARGUMENTS")
    _require(all(_is_rat(term) for term in args["terms"]), "R084_ARGUMENTS")
    return _canonical_rational(sum((_rat(term) for term in args["terms"]), Fraction(0)))


def _count(args):
    _require(set(args) == {"needle", "text"}, "R084_ARGUMENTS")
    text, needle = args["text"], args["needle"]
    _require(isinstance(text, str) and isinstance(needle, str) and needle, "R084_ARGUMENTS")
    return text.count(needle)


TOOLS = {"count": _count, "gcd": _gcd, "sort": _sort, "sum": _sum}
OWN_NEGATIVE = {"calls": [{"args": {"a": 12, "b": 18}, "result_digest": result_digest(3), "tool": "gcd"}]}
OWN_NEGATIVE_CODE = "R084_GUESSED_RESULT"


def _decide(payload):
    calls = _seq(payload["calls"])
    _require(calls, "R_SCHEMA")
    for call in calls:
        _require(isinstance(call, dict) and set(call) == {"args", "result_digest", "tool"}, "R_SCHEMA")
        _text(call["tool"])
        _text(call["result_digest"])
        _require(isinstance(call["args"], dict), "R_SCHEMA")
    for call in calls:
        _require(call["tool"] in TOOLS, "R084_UNKNOWN_TOOL")
    results = [TOOLS[call["tool"]](call["args"]) for call in calls]
    for call, result in zip(calls, results):
        _require(call["result_digest"] == result_digest(result), "R084_GUESSED_RESULT")
