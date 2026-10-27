"""
Swarm Immune System & Pharmacy Subsystem.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .catalog_repository import PharmacyCatalogRepository
    from .models import Antibody, ConstraintType, Operatorizability, PharmacyStatus, RuntimeAction, Severity
    from .seeder import PharmacySeeder
    from .templates import DEFAULT_ANTIBODY_TEMPLATES

__all__ = ['Antibody', 'ConstraintType', 'Operatorizability', 'RuntimeAction', 'Severity', 'PharmacyStatus', 'PharmacyCatalogRepository', 'PharmacySeeder', 'DEFAULT_ANTIBODY_TEMPLATES']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'PharmacyCatalogRepository': ('.catalog_repository', 'PharmacyCatalogRepository'),
    'Antibody': ('.models', 'Antibody'),
    'ConstraintType': ('.models', 'ConstraintType'),
    'Operatorizability': ('.models', 'Operatorizability'),
    'PharmacyStatus': ('.models', 'PharmacyStatus'),
    'RuntimeAction': ('.models', 'RuntimeAction'),
    'Severity': ('.models', 'Severity'),
    'PharmacySeeder': ('.seeder', 'PharmacySeeder'),
    'DEFAULT_ANTIBODY_TEMPLATES': ('.templates', 'DEFAULT_ANTIBODY_TEMPLATES'),
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
