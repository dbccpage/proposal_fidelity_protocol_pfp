"""Adapters for live-model proposers and LLM backends. AuthorityEffect: None."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_woland.infrastructure.providers.adapters.llm_proposer import Completion, MalformedMove, ProposerRuntimeRetired, claims_from_json, parse_move, run_governed_session, scripted_proposer
    from omega_engine_woland.infrastructure.providers.adapters.model_backends import CHEAP_OPENROUTER_MODEL, AnthropicBackend, Backend, MockBackend, OpenRouterBackend, get_backend
    from omega_engine_woland.infrastructure.providers.adapters.sakana_adapter import DEFAULT_SAKANA_MODEL, SakanaOpenRouterAdapter, SakanaReceipt, ask_sakana

__all__ = ['AnthropicBackend', 'Backend', 'CHEAP_OPENROUTER_MODEL', 'Completion', 'DEFAULT_SAKANA_MODEL', 'MalformedMove', 'MockBackend', 'OpenRouterBackend', 'ProposerRuntimeRetired', 'SakanaOpenRouterAdapter', 'SakanaReceipt', 'ask_sakana', 'claims_from_json', 'get_backend', 'parse_move', 'run_governed_session', 'scripted_proposer']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Completion': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'Completion'),
    'MalformedMove': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'MalformedMove'),
    'ProposerRuntimeRetired': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'ProposerRuntimeRetired'),
    'claims_from_json': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'claims_from_json'),
    'parse_move': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'parse_move'),
    'run_governed_session': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'run_governed_session'),
    'scripted_proposer': ('omega_engine_woland.infrastructure.providers.adapters.llm_proposer', 'scripted_proposer'),
    'CHEAP_OPENROUTER_MODEL': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'CHEAP_OPENROUTER_MODEL'),
    'AnthropicBackend': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'AnthropicBackend'),
    'Backend': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'Backend'),
    'MockBackend': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'MockBackend'),
    'OpenRouterBackend': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'OpenRouterBackend'),
    'get_backend': ('omega_engine_woland.infrastructure.providers.adapters.model_backends', 'get_backend'),
    'DEFAULT_SAKANA_MODEL': ('omega_engine_woland.infrastructure.providers.adapters.sakana_adapter', 'DEFAULT_SAKANA_MODEL'),
    'SakanaOpenRouterAdapter': ('omega_engine_woland.infrastructure.providers.adapters.sakana_adapter', 'SakanaOpenRouterAdapter'),
    'SakanaReceipt': ('omega_engine_woland.infrastructure.providers.adapters.sakana_adapter', 'SakanaReceipt'),
    'ask_sakana': ('omega_engine_woland.infrastructure.providers.adapters.sakana_adapter', 'ask_sakana'),
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
