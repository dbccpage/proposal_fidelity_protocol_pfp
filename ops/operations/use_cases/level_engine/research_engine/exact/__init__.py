"""Exact arithmetic: Q (native fraction), Q(i), polynomials, real algebraic
numbers by isolating intervals, rational intervals, linear algebra.  No float
path exists anywhere in this package.

AuthorityEffect: None
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .alg import Alg, Interval, alg_cmp, alg_equal, alg_sign_of, isolate
    from .q import ONE, ZERO, Q, fmt_q, parse_q
    from .qi import QI, fmt_qi, parse_qi

__all__ = ['Alg', 'Interval', 'ONE', 'Q', 'QI', 'ZERO', 'alg_cmp', 'alg_equal', 'alg_sign_of', 'fmt_q', 'fmt_qi', 'isolate', 'parse_q', 'parse_qi']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Alg': ('.alg', 'Alg'),
    'Interval': ('.alg', 'Interval'),
    'alg_cmp': ('.alg', 'alg_cmp'),
    'alg_equal': ('.alg', 'alg_equal'),
    'alg_sign_of': ('.alg', 'alg_sign_of'),
    'isolate': ('.alg', 'isolate'),
    'ONE': ('.q', 'ONE'),
    'ZERO': ('.q', 'ZERO'),
    'Q': ('.q', 'Q'),
    'fmt_q': ('.q', 'fmt_q'),
    'parse_q': ('.q', 'parse_q'),
    'QI': ('.qi', 'QI'),
    'fmt_qi': ('.qi', 'fmt_qi'),
    'parse_qi': ('.qi', 'parse_qi'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
