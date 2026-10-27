"""Normal forms infrastructure layer: SQLite storage and YAML contract parsing.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pfp.infrastructure.normal_forms.catalog import check_catalog
    from pfp.infrastructure.normal_forms.catalog import check_document
    from pfp.infrastructure.normal_forms.catalog import validate_contract
    from pfp.infrastructure.normal_forms.contract_model import Finding
    from pfp.infrastructure.normal_forms.contract_model import load_yaml
    from pfp.infrastructure.normal_forms.contract_paths import CONTRACTS_DIR
    from pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR
    from pfp.infrastructure.normal_forms.contract_paths import STANDARD_PATH
    from pfp.infrastructure.normal_forms.db_context import NormalFormsDbContext
    from pfp.infrastructure.normal_forms.evaluator import NormalFormsEvaluator
    from pfp.infrastructure.normal_forms.migrate_contract import migrate_v0_to_v1
    from pfp.infrastructure.normal_forms._golden_nfs import NormalFormContract
    from pfp.infrastructure.normal_forms._golden_nfs import NormalFormContractMetaSchema
    from pfp.infrastructure.normal_forms._golden_nfs import NormalFormFoundationalDefinitions
    from pfp.infrastructure.normal_forms._golden_nfs import NormalFormStandard
    from pfp.infrastructure.normal_forms._golden_nfs import QuadrilateralCriterion
    from pfp.infrastructure.normal_forms._golden_nfs import normal_form_contract_schema
    from pfp.infrastructure.normal_forms._golden_nfs import normal_form_definitions
    from pfp.infrastructure.normal_forms._golden_nfs import normal_form_standard_schema

__all__ = ['NormalFormsDbContext', 'NormalFormsEvaluator', 'NormalFormContract', 'NormalFormContractMetaSchema', 'NormalFormFoundationalDefinitions', 'QuadrilateralCriterion', 'NormalFormStandard', 'normal_form_contract_schema', 'normal_form_definitions', 'normal_form_standard_schema', 'NORMAL_FORMS_DIR', 'CONTRACTS_DIR', 'STANDARD_PATH', 'Finding', 'load_yaml', 'validate_contract', 'check_document', 'check_catalog', 'migrate_v0_to_v1']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'check_catalog': ('pfp.infrastructure.normal_forms.catalog', 'check_catalog'),
    'check_document': ('pfp.infrastructure.normal_forms.catalog', 'check_document'),
    'validate_contract': ('pfp.infrastructure.normal_forms.catalog', 'validate_contract'),
    'Finding': ('pfp.infrastructure.normal_forms.contract_model', 'Finding'),
    'load_yaml': ('pfp.infrastructure.normal_forms.contract_model', 'load_yaml'),
    'CONTRACTS_DIR': ('pfp.infrastructure.normal_forms.contract_paths', 'CONTRACTS_DIR'),
    'NORMAL_FORMS_DIR': ('pfp.infrastructure.normal_forms.contract_paths', 'NORMAL_FORMS_DIR'),
    'STANDARD_PATH': ('pfp.infrastructure.normal_forms.contract_paths', 'STANDARD_PATH'),
    'NormalFormsDbContext': ('pfp.infrastructure.normal_forms.db_context', 'NormalFormsDbContext'),
    'NormalFormsEvaluator': ('pfp.infrastructure.normal_forms.evaluator', 'NormalFormsEvaluator'),
    'migrate_v0_to_v1': ('pfp.infrastructure.normal_forms.migrate_contract', 'migrate_v0_to_v1'),
    'NormalFormContract': ('pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormContract'),
    'NormalFormContractMetaSchema': ('pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormContractMetaSchema'),
    'NormalFormFoundationalDefinitions': ('pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormFoundationalDefinitions'),
    'NormalFormStandard': ('pfp.infrastructure.normal_forms._golden_nfs', 'NormalFormStandard'),
    'QuadrilateralCriterion': ('pfp.infrastructure.normal_forms._golden_nfs', 'QuadrilateralCriterion'),
    'normal_form_contract_schema': ('pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_contract_schema'),
    'normal_form_definitions': ('pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_definitions'),
    'normal_form_standard_schema': ('pfp.infrastructure.normal_forms._golden_nfs', 'normal_form_standard_schema'),
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
