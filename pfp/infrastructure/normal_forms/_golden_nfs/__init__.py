"""Golden normal forms schema, definitions, and SQL specifications."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContract
    from pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContractMetaSchema
    from pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions import NormalFormFoundationalDefinitions
    from pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions import QuadrilateralCriterion
    from pfp.infrastructure.normal_forms._golden_nfs.normal_form_standard_schema import NormalFormStandard

__all__ = ['NormalFormContract', 'NormalFormContractMetaSchema', 'NormalFormFoundationalDefinitions', 'QuadrilateralCriterion', 'NormalFormStandard']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'NormalFormContract': ('pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContract'),
    'NormalFormContractMetaSchema': ('pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContractMetaSchema'),
    'NormalFormFoundationalDefinitions': ('pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions', 'NormalFormFoundationalDefinitions'),
    'QuadrilateralCriterion': ('pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions', 'QuadrilateralCriterion'),
    'NormalFormStandard': ('pfp.infrastructure.normal_forms._golden_nfs.normal_form_standard_schema', 'NormalFormStandard'),
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
