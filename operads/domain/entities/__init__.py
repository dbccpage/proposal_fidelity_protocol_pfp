"""Entities and Aggregates for OEWAS V3 domain."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .catalog_v3 import CapabilitySliceV3, EstateCatalogV3
    from .composition_v3 import CompositionV3
    from .operation_v3 import OperationV3, PortSpecV3
    from .skill_document_v3 import DocumentLeafNode, SkillDocumentV3

__all__ = ['CapabilitySliceV3', 'CompositionV3', 'DocumentLeafNode', 'EstateCatalogV3', 'OperationV3', 'PortSpecV3', 'SkillDocumentV3']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CapabilitySliceV3': ('.catalog_v3', 'CapabilitySliceV3'),
    'EstateCatalogV3': ('.catalog_v3', 'EstateCatalogV3'),
    'CompositionV3': ('.composition_v3', 'CompositionV3'),
    'OperationV3': ('.operation_v3', 'OperationV3'),
    'PortSpecV3': ('.operation_v3', 'PortSpecV3'),
    'DocumentLeafNode': ('.skill_document_v3', 'DocumentLeafNode'),
    'SkillDocumentV3': ('.skill_document_v3', 'SkillDocumentV3'),
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
