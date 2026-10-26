"""Swarm Personas and Coloured Operad Architecture Domain Models."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .deliberation import DeliberationBout, SwarmDeliberationTurn
    from .operad_colours import OperadColour
    from .personas import SPECIALIST_PERSONAS, AgentPersona, SwarmBranch

__all__ = ['OperadColour', 'SwarmBranch', 'AgentPersona', 'SPECIALIST_PERSONAS', 'SwarmDeliberationTurn', 'DeliberationBout']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'DeliberationBout': ('.deliberation', 'DeliberationBout'),
    'SwarmDeliberationTurn': ('.deliberation', 'SwarmDeliberationTurn'),
    'OperadColour': ('.operad_colours', 'OperadColour'),
    'SPECIALIST_PERSONAS': ('.personas', 'SPECIALIST_PERSONAS'),
    'AgentPersona': ('.personas', 'AgentPersona'),
    'SwarmBranch': ('.personas', 'SwarmBranch'),
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
