"""Controllers Layer for the Symbol Game Bounded Context.

Orchestrates application use cases and routes requests between external boundaries and application use cases.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .code_change_controller import CodeChangeController
    from .prompt_controller import PromptController
    from .symbol_game_controller import SymbolGameController
    from .symbol_game_engine import SymbolGameEngine
    from .turn_controller import TurnController
    from pfp.controllers.pfp_controller import PfpController

__all__ = list(dict.fromkeys([*__all__, 'PfpController']))

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CodeChangeController': ('.code_change_controller', 'CodeChangeController'),
    'PromptController': ('.prompt_controller', 'PromptController'),
    'SymbolGameController': ('.symbol_game_controller', 'SymbolGameController'),
    'SymbolGameEngine': ('.symbol_game_engine', 'SymbolGameEngine'),
    'TurnController': ('.turn_controller', 'TurnController'),
    'PfpController': ('pfp.controllers.pfp_controller', 'PfpController'),
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
