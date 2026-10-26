# ---- shared preamble: byte-identical in every stage_NNN.py (a test pins it) ----
import re
from fractions import Fraction

GENERIC_CODES = ("R_EMPTY_INPUT", "R_VERDICT_FIELD", "R_SCHEMA", "R_NOT_EXACT")
_VERDICT_KEY = re.compile(
    r"^(is_.*|has_.*|.*_verified|.*_residual|.*_anticommute|verified|passes|passed|valid|ok|"
    r"accepted|verdict|outcome|grade|status|differential_squared|certified|proved)$",
    re.IGNORECASE,
)
_RATIONAL = re.compile(r"(-?)(0|[1-9][0-9]*)/([1-9][0-9]*)")


class _Refused(Exception):
    def __init__(self, code):
        Exception.__init__(self, code)
        self.code = code


def _refuse(code):
    raise _Refused(code)


def _require(condition, code):
    if not condition:
        _refuse(code)


def _walk(value, leaves, keys, lists):
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            _walk(item, leaves, keys, lists)
    elif isinstance(value, list):
        lists.append(value)
        for item in value:
            _walk(item, leaves, keys, lists)
    else:
        leaves.append(value)


def _admit(payload):
    """The generic refusals, decided before any clause of the stage.

    Not a mapping, or no datum: R_EMPTY_INPUT. A verdict-named key anywhere, or
    every datum a boolean: R_VERDICT_FIELD. Lists present and every one empty:
    R_EMPTY_INPUT. A float anywhere: R_NOT_EXACT. Fields other than FIELDS:
    R_SCHEMA.
    """
    if not isinstance(payload, dict) or not payload:
        _refuse("R_EMPTY_INPUT")
    leaves, keys, lists = [], [], []
    _walk(payload, leaves, keys, lists)
    if any(not isinstance(key, str) or _VERDICT_KEY.match(key) for key in keys):
        _refuse("R_VERDICT_FIELD")
    data = [leaf for leaf in leaves if leaf is not None]
    if data and all(isinstance(leaf, bool) for leaf in data):
        _refuse("R_VERDICT_FIELD")
    if all(leaf == "" for leaf in data) or (lists and not any(lists)):
        _refuse("R_EMPTY_INPUT")
    if any(isinstance(leaf, float) for leaf in data):
        _refuse("R_NOT_EXACT")
    _require(set(payload) == set(FIELDS), "R_SCHEMA")
    return payload


def _nat(value):
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, "R_SCHEMA")
    return value


def _text(value):
    _require(isinstance(value, str) and value != "", "R_SCHEMA")
    return value


def _seq(value, length=None):
    _require(isinstance(value, list), "R_SCHEMA")
    _require(length is None or len(value) == length, "R_SCHEMA")
    return value


def _rat(value):
    """A canonical ``num/den`` string: reduced, ``den >= 1``, zero written ``0/1``."""
    _require(isinstance(value, str), "R_NOT_EXACT")
    match = _RATIONAL.fullmatch(value)
    _require(match is not None, "R_NOT_EXACT")
    sign, num, den = match.groups()
    out = Fraction(int(num), int(den))
    _require(out.denominator == int(den) and not (sign and out == 0), "R_NOT_EXACT")
    return -out if sign else out


def _rats(value, length=None):
    return [_rat(item) for item in _seq(value, length)]


def _matrix(value, rows=None, columns=None):
    """A rectangular matrix of canonical rationals, as a list of rows."""
    out = [_rats(row) for row in _seq(value, rows)]
    widths = {len(row) for row in out}
    _require(len(widths) <= 1, "R_SCHEMA")
    _require(columns is None or not out or widths == {columns}, "R_SCHEMA")
    return out


def check(payload):
    """``("PASS", None)`` or ``("REFUSED", code)``. Pure: no I/O, no clock."""
    try:
        _decide(_admit(payload))
    except _Refused as refusal:
        return ("REFUSED", refusal.code)
    except (TypeError, ValueError, KeyError, IndexError, ZeroDivisionError, AttributeError, RecursionError):
        return ("REFUSED", "R_SCHEMA")
    return ("PASS", None)


# ---- end shared preamble ----
