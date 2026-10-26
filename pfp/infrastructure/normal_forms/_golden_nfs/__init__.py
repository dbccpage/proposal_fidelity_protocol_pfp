"""Golden normal forms schema, definitions, and SQL specifications."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContract
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema import NormalFormContractMetaSchema
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions import NormalFormFoundationalDefinitions
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions import QuadrilateralCriterion
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_standard_schema import NormalFormStandard

__all__ = ['NormalFormContract', 'NormalFormContractMetaSchema', 'NormalFormFoundationalDefinitions', 'QuadrilateralCriterion', 'NormalFormStandard']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'NormalFormContract': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContract'),
    'NormalFormContractMetaSchema': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_contract_schema', 'NormalFormContractMetaSchema'),
    'NormalFormFoundationalDefinitions': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions', 'NormalFormFoundationalDefinitions'),
    'QuadrilateralCriterion': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_definitions', 'QuadrilateralCriterion'),
    'NormalFormStandard': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs.normal_form_standard_schema', 'NormalFormStandard'),
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
