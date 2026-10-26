"""API presentation layer for symbol_game."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .router import ApiResponse, SymbolGameApiRouter
    from .app import run_server
    from .swarm_api import compile_prompt, create_turn, parse_machine_block, validate_reply_residual

__all__ = ['ApiResponse', 'SymbolGameApiRouter', 'run_server', 'compile_prompt', 'create_turn', 'parse_machine_block', 'validate_reply_residual']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ApiResponse': ('.router', 'ApiResponse'),
    'SymbolGameApiRouter': ('.router', 'SymbolGameApiRouter'),
    'run_server': ('.app', 'run_server'),
    'compile_prompt': ('.swarm_api', 'compile_prompt'),
    'create_turn': ('.swarm_api', 'create_turn'),
    'parse_machine_block': ('.swarm_api', 'parse_machine_block'),
    'validate_reply_residual': ('.swarm_api', 'validate_reply_residual'),
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
