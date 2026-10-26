"""Prompt Hierarchy Package.

Canonical addressing, parsing, and gate evaluation for attaching OEWAS Anti-Ops
and OEEIS Admitted Antibodies to individual prompts.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .evaluator import collect_derivation_map_operads, evaluate_prompt_gates
    from .models import AntibodyBinding, AntiOpBinding, DerivationMapOperadReport, ImmuneFenceBinding, OperadPromptBinding, PromptGateReceipt, PromptTreeNode, PromptUri
    from .parser import load_prompt_node_from_binding_dict, parse_prompt_uri

__all__ = ['AntiOpBinding', 'AntibodyBinding', 'DerivationMapOperadReport', 'ImmuneFenceBinding', 'OperadPromptBinding', 'PromptGateReceipt', 'PromptTreeNode', 'PromptUri', 'collect_derivation_map_operads', 'evaluate_prompt_gates', 'load_prompt_node_from_binding_dict', 'parse_prompt_uri']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'collect_derivation_map_operads': ('.evaluator', 'collect_derivation_map_operads'),
    'evaluate_prompt_gates': ('.evaluator', 'evaluate_prompt_gates'),
    'AntibodyBinding': ('.models', 'AntibodyBinding'),
    'AntiOpBinding': ('.models', 'AntiOpBinding'),
    'DerivationMapOperadReport': ('.models', 'DerivationMapOperadReport'),
    'ImmuneFenceBinding': ('.models', 'ImmuneFenceBinding'),
    'OperadPromptBinding': ('.models', 'OperadPromptBinding'),
    'PromptGateReceipt': ('.models', 'PromptGateReceipt'),
    'PromptTreeNode': ('.models', 'PromptTreeNode'),
    'PromptUri': ('.models', 'PromptUri'),
    'load_prompt_node_from_binding_dict': ('.parser', 'load_prompt_node_from_binding_dict'),
    'parse_prompt_uri': ('.parser', 'parse_prompt_uri'),
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
