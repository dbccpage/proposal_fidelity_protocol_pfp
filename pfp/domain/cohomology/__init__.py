"""Cohomology domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import CohomologyCase, CohomologyResult
    from .certificate_checker import check_certificate
    from .solver import solve

__all__ = ['CohomologyCase', 'CohomologyResult', 'check_certificate', 'solve']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CohomologyCase': ('.models', 'CohomologyCase'),
    'CohomologyResult': ('.models', 'CohomologyResult'),
    'check_certificate': ('.certificate_checker', 'check_certificate'),
    'solve': ('.solver', 'solve'),
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
