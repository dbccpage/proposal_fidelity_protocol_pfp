"""Autopoiesis Bounded Context Infrastructure.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .file_harvest_vault import FileHarvestVault
    from .json_pharmacy_adapter import JsonPharmacyAdapter
    from .markdown_skills_adapter import MarkdownSkillsAdapter

__all__ = ['FileHarvestVault', 'JsonPharmacyAdapter', 'MarkdownSkillsAdapter']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'FileHarvestVault': ('.file_harvest_vault', 'FileHarvestVault'),
    'JsonPharmacyAdapter': ('.json_pharmacy_adapter', 'JsonPharmacyAdapter'),
    'MarkdownSkillsAdapter': ('.markdown_skills_adapter', 'MarkdownSkillsAdapter'),
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
