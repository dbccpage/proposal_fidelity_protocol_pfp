"""A bounded regular-expression subset for detector rules.

Detector rules are run by Python's backtracking `re` engine, both by the
regex matcher and by the thymus when it screens a rule against the self panel.
Some patterns take time exponential in the number of repeats on a short
non-matching subject (``(a+)+b``, ``\\w*\\w*\\w*!``, ``.*.*.*=``). Even one
unbounded repeat followed by something that can fail is quadratic under
`re.search`: every start position runs the repeat to the end of its run and
backs off (measured on 2026-09-29: ``\\w*!`` took 14 s on 50,000 characters).
So an unrestricted pattern lets a rule author, or a model proposing a rule,
stall a screen.

The admission rule. `compile_safe_pattern` parses the pattern with the parser
`re` itself uses (`re._parser`) and admits it only if all of these hold:

1. it is a string of 1 to `MAX_PATTERN_LENGTH` characters that `re` parses;
2. it has no backreference (``\\1``, ``(?P=name)``) and no conditional group;
3. no repeat occurs inside another repeat, and no alternation (``|``) occurs
   inside a repeat;
4. every repeat is bounded: ``*``, ``+`` and ``{m,}`` are refused (write
   ``{0,k}`` or ``{1,k}``), and every upper bound is at most `MAX_REPEAT_BOUND`;
5. the choice product P is at most `MAX_CHOICE_PRODUCT`, where P is the product,
   over every repeat ``{m,n}`` (``?`` is ``{0,1}``) of (n - m + 1), and over
   every alternation of its number of alternatives;
6. the pattern cannot match the empty string (its minimum width, as computed
   by the parser, is at least 1), so every match covers at least one character.

Why this bounds the work (an argument, not a machine-checked proof). With rules
2 to 4 every attempt of the backtracking matcher at one start position is
determined by one count per repeat and one alternative per alternation, so one
start position explores at most P choice vectors, and each vector is tried in
at most L + B character steps, where L is the pattern length and B the sum of
the repeat bounds. A search over a subject of n characters therefore takes at
most (n + 1) * P * (L + B) steps: linear in n. The constants are capped by the
limits above; measured on 2026-09-29, an admitted pattern with P = 256 took
0.37 s on 50,000 characters.

No matching-time backstop. `re` has no timeout, and it matches in C while
holding the interpreter lock, so neither a watchdog thread nor `signal.alarm`
(which does not exist on Windows) can interrupt a match. The third-party
`regex` package accepts a timeout, but it is not a declared dependency of this
repository, and running each match in a subprocess would add a process start
per fixture. The admission rule is therefore the only guard.
"""

from __future__ import annotations

import re
from re import _constants as _sre_constants
from re import _parser as _sre_parser

from .definitions_loader import load_danger_signals

_bounds = load_danger_signals().get("safe_pattern_bounds", {})

MAX_PATTERN_LENGTH = int(_bounds.get("max_pattern_length", 256))
MAX_REPEAT_BOUND = int(_bounds.get("max_repeat_bound", 64))
MAX_CHOICE_PRODUCT = int(_bounds.get("max_choice_product", 256))

UNSAFE_PATTERN_CODES = frozenset(
    _bounds.get(
        "unsafe_pattern_codes",
        (
            "PATTERN_NOT_A_STRING",
            "PATTERN_EMPTY",
            "PATTERN_TOO_LONG",
            "PATTERN_SYNTAX",
            "PATTERN_BACKREFERENCE",
            "PATTERN_NESTED_QUANTIFIER",
            "PATTERN_QUANTIFIED_ALTERNATION",
            "PATTERN_UNBOUNDED_REPEAT",
            "PATTERN_REPEAT_BOUND",
            "PATTERN_CHOICE_PRODUCT",
            "PATTERN_ZERO_WIDTH",
        ),
    )
)

_REPEATS = frozenset(
    {
        _sre_constants.MAX_REPEAT,
        _sre_constants.MIN_REPEAT,
        _sre_constants.POSSESSIVE_REPEAT,
    }
)


class UnsafePatternRefusal(ValueError):
    """A detector pattern outside the admitted subset."""

    def __init__(self, code: str, detail: str = "") -> None:
        if code not in UNSAFE_PATTERN_CODES:
            raise ValueError(f"unknown unsafe-pattern code: {code}")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


class _ChoiceProduct:
    def __init__(self) -> None:
        self.value = 1

    def multiply(self, factor: int) -> None:
        self.value *= factor
        if self.value > MAX_CHOICE_PRODUCT:
            raise UnsafePatternRefusal(
                "PATTERN_CHOICE_PRODUCT", f"choice product exceeds {MAX_CHOICE_PRODUCT}"
            )


def _walk(items: object, inside_repeat: bool, product: _ChoiceProduct) -> None:
    for op, av in items:  # type: ignore[attr-defined]
        if op in (_sre_constants.GROUPREF, _sre_constants.GROUPREF_EXISTS):
            raise UnsafePatternRefusal("PATTERN_BACKREFERENCE")
        if op in _REPEATS:
            low, high, body = av
            if inside_repeat:
                raise UnsafePatternRefusal("PATTERN_NESTED_QUANTIFIER")
            # The body first, so a nested repeat or alternation is named as such.
            _walk(body, True, product)
            if high is _sre_constants.MAXREPEAT:
                raise UnsafePatternRefusal(
                    "PATTERN_UNBOUNDED_REPEAT", "use a bounded repeat such as {0,k} or {1,k}"
                )
            if high > MAX_REPEAT_BOUND:
                raise UnsafePatternRefusal("PATTERN_REPEAT_BOUND", str(high))
            product.multiply(high - low + 1)
        elif op is _sre_constants.BRANCH:
            if inside_repeat:
                raise UnsafePatternRefusal("PATTERN_QUANTIFIED_ALTERNATION")
            branches = av[1]
            product.multiply(len(branches))
            for branch in branches:
                _walk(branch, inside_repeat, product)
        elif op is _sre_constants.SUBPATTERN:
            _walk(av[3], inside_repeat, product)
        elif op in (_sre_constants.ASSERT, _sre_constants.ASSERT_NOT):
            _walk(av[1], inside_repeat, product)
        elif op is _sre_constants.ATOMIC_GROUP:
            _walk(av, inside_repeat, product)


def compile_safe_pattern(pattern: object) -> re.Pattern[str]:
    """Compile `pattern` case-insensitively, or refuse it with a typed code."""
    if type(pattern) is not str:
        raise UnsafePatternRefusal("PATTERN_NOT_A_STRING", type(pattern).__name__)
    if not pattern.strip():
        raise UnsafePatternRefusal("PATTERN_EMPTY")
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise UnsafePatternRefusal("PATTERN_TOO_LONG", str(len(pattern)))
    try:
        tree = _sre_parser.parse(pattern, re.IGNORECASE)
    except re.error as exc:
        raise UnsafePatternRefusal("PATTERN_SYNTAX", str(exc)) from exc
    _walk(tree, False, _ChoiceProduct())
    if tree.getwidth()[0] < 1:
        raise UnsafePatternRefusal("PATTERN_ZERO_WIDTH", "the pattern can match the empty string")
    return re.compile(pattern, re.IGNORECASE)


__all__ = [
    "MAX_CHOICE_PRODUCT",
    "MAX_PATTERN_LENGTH",
    "MAX_REPEAT_BOUND",
    "UNSAFE_PATTERN_CODES",
    "UnsafePatternRefusal",
    "compile_safe_pattern",
]
