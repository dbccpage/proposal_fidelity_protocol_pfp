"""Thin operadic skill compiler (episode → resolve → promote → eval). AuthorityEffect: None."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .episode import append_episode, load_episodes, make_episode
    from .resolve import ResolveResult, resolve_episode, resolve_text
    from .promote import promote_from_text
    from .eval_runner import run_bank

__all__ = ['append_episode', 'load_episodes', 'make_episode', 'ResolveResult', 'resolve_episode', 'resolve_text', 'promote_from_text', 'run_bank']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'append_episode': ('.episode', 'append_episode'),
    'load_episodes': ('.episode', 'load_episodes'),
    'make_episode': ('.episode', 'make_episode'),
    'ResolveResult': ('.resolve', 'ResolveResult'),
    'resolve_episode': ('.resolve', 'resolve_episode'),
    'resolve_text': ('.resolve', 'resolve_text'),
    'promote_from_text': ('.promote', 'promote_from_text'),
    'run_bank': ('.eval_runner', 'run_bank'),
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
