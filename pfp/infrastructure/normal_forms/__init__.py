"""Normal forms infrastructure layer: SQLite storage and YAML contract parsing.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_pfp.infrastructure.normal_forms.catalog import check_catalog
    from omega_engine_pfp.infrastructure.normal_forms.catalog import check_document
    from omega_engine_pfp.infrastructure.normal_forms.catalog import validate_contract
    from omega_engine_pfp.infrastructure.normal_forms.contract_model import Finding
    from omega_engine_pfp.infrastructure.normal_forms.contract_model import load_yaml
    from omega_engine_pfp.infrastructure.normal_forms.contract_paths import CONTRACTS_DIR
    from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
    from omega_engine_pfp.infrastructure.normal_forms.contract_paths import STANDARD_PATH
    from omega_engine_pfp.infrastructure.normal_forms.db_context import NormalFormsDbContext
    from omega_engine_pfp.infrastructure.normal_forms.evaluator import NormalFormsEvaluator
    from omega_engine_pfp.infrastructure.normal_forms.migrate_contract import migrate_v0_to_v1
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import NormalFormContract
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import NormalFormContractMetaSchema
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import NormalFormFoundationalDefinitions
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import NormalFormStandard
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import QuadrilateralCriterion
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import normal_form_contract_schema
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import normal_form_definitions
    from omega_engine_pfp.infrastructure.normal_forms._golden_nfs import normal_form_standard_schema

__all__ = ['NormalFormsDbContext', 'NormalFormsEvaluator', 'NormalFormContract', 'NormalFormContractMetaSchema', 'NormalFormFoundationalDefinitions', 'QuadrilateralCriterion', 'NormalFormStandard', 'normal_form_contract_schema', 'normal_form_definitions', 'normal_form_standard_schema', 'NORMAL_FORMS_DIR', 'CONTRACTS_DIR', 'STANDARD_PATH', 'Finding', 'load_yaml', 'validate_contract', 'check_document', 'check_catalog', 'migrate_v0_to_v1']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'check_catalog': ('omega_engine_pfp.infrastructure.normal_forms.catalog', 'check_catalog'),
    'check_document': ('omega_engine_pfp.infrastructure.normal_forms.catalog', 'check_document'),
    'validate_contract': ('omega_engine_pfp.infrastructure.normal_forms.catalog', 'validate_contract'),
    'Finding': ('omega_engine_pfp.infrastructure.normal_forms.contract_model', 'Finding'),
    'load_yaml': ('omega_engine_pfp.infrastructure.normal_forms.contract_model', 'load_yaml'),
    'CONTRACTS_DIR': ('omega_engine_pfp.infrastructure.normal_forms.contract_paths', 'CONTRACTS_DIR'),
    'NORMAL_FORMS_DIR': ('omega_engine_pfp.infrastructure.normal_forms.contract_paths', 'NORMAL_FORMS_DIR'),
    'STANDARD_PATH': ('omega_engine_pfp.infrastructure.normal_forms.contract_paths', 'STANDARD_PATH'),
    'NormalFormsDbContext': ('omega_engine_pfp.infrastructure.normal_forms.db_context', 'NormalFormsDbContext'),
    'NormalFormsEvaluator': ('omega_engine_pfp.infrastructure.normal_forms.evaluator', 'NormalFormsEvaluator'),
    'migrate_v0_to_v1': ('omega_engine_pfp.infrastructure.normal_forms.migrate_contract', 'migrate_v0_to_v1'),
    'NormalFormContract': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormContract'),
    'NormalFormContractMetaSchema': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormContractMetaSchema'),
    'NormalFormFoundationalDefinitions': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormFoundationalDefinitions'),
    'NormalFormStandard': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormStandard'),
    'QuadrilateralCriterion': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'QuadrilateralCriterion'),
    'normal_form_contract_schema': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_contract_schema'),
    'normal_form_definitions': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_definitions'),
    'normal_form_standard_schema': ('omega_engine_pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_standard_schema'),
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
