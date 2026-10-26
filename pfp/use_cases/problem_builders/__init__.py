"""Problem Builders for Symbol Game RuntimeProblem instances."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .airy_problem import DEFAULT_AIRY_LAMBDA, DEFAULT_AIRY_SEEDS, DEFAULT_AIRY_SLOT_IDS, build_airy_problem
    from .coda_problem import build_coda_problem
    from .mub6_problem import build_mub6_deltoid_cusp_problem, encode_mub6_level2_wire

__all__ = ['DEFAULT_AIRY_LAMBDA', 'DEFAULT_AIRY_SEEDS', 'DEFAULT_AIRY_SLOT_IDS', 'build_airy_problem', 'build_coda_problem', 'build_mub6_deltoid_cusp_problem', 'encode_mub6_level2_wire']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DEFAULT_AIRY_LAMBDA': ('.airy_problem', 'DEFAULT_AIRY_LAMBDA'),
    'DEFAULT_AIRY_SEEDS': ('.airy_problem', 'DEFAULT_AIRY_SEEDS'),
    'DEFAULT_AIRY_SLOT_IDS': ('.airy_problem', 'DEFAULT_AIRY_SLOT_IDS'),
    'build_airy_problem': ('.airy_problem', 'build_airy_problem'),
    'build_coda_problem': ('.coda_problem', 'build_coda_problem'),
    'build_mub6_deltoid_cusp_problem': ('.mub6_problem', 'build_mub6_deltoid_cusp_problem'),
    'encode_mub6_level2_wire': ('.mub6_problem', 'encode_mub6_level2_wire'),
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
