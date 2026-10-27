"""PFP Contracts, Gates, and Schemas Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .contracts import ContractAuditReceipt, ContractSpec, InvariantCheck, Postcondition, Precondition
    from .gate_types import ComparisonOperator, EmpiricalGate, GateRegister, Intergate, PrimaryGate, gate_ordinal
    from .gates import GateReceipt, GateSpec, GateVerdict, AdversaryGateId
    from .schema_register import EnvelopeSchemaEntry, GrammarSchemaEntry, SchemaRegister
    from .schemas import SchemaCatalog, SchemaSpec, SchemaValidationResult

__all__ = ['ComparisonOperator', 'ContractAuditReceipt', 'ContractSpec', 'EmpiricalGate', 'EnvelopeSchemaEntry', 'GateReceipt', 'GateRegister', 'GateSpec', 'GateVerdict', 'GrammarSchemaEntry', 'Intergate', 'InvariantCheck', 'Postcondition', 'Precondition', 'PrimaryGate', 'SchemaCatalog', 'SchemaRegister', 'SchemaSpec', 'SchemaValidationResult', 'AdversaryGateId', 'gate_ordinal']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ContractAuditReceipt': ('.contracts', 'ContractAuditReceipt'),
    'ContractSpec': ('.contracts', 'ContractSpec'),
    'InvariantCheck': ('.contracts', 'InvariantCheck'),
    'Postcondition': ('.contracts', 'Postcondition'),
    'Precondition': ('.contracts', 'Precondition'),
    'ComparisonOperator': ('.gate_types', 'ComparisonOperator'),
    'EmpiricalGate': ('.gate_types', 'EmpiricalGate'),
    'GateRegister': ('.gate_types', 'GateRegister'),
    'Intergate': ('.gate_types', 'Intergate'),
    'PrimaryGate': ('.gate_types', 'PrimaryGate'),
    'gate_ordinal': ('.gate_types', 'gate_ordinal'),
    'GateReceipt': ('.gates', 'GateReceipt'),
    'GateSpec': ('.gates', 'GateSpec'),
    'GateVerdict': ('.gates', 'GateVerdict'),
    'AdversaryGateId': ('.gates', 'AdversaryGateId'),
    'EnvelopeSchemaEntry': ('.schema_register', 'EnvelopeSchemaEntry'),
    'GrammarSchemaEntry': ('.schema_register', 'GrammarSchemaEntry'),
    'SchemaRegister': ('.schema_register', 'SchemaRegister'),
    'SchemaCatalog': ('.schemas', 'SchemaCatalog'),
    'SchemaSpec': ('.schemas', 'SchemaSpec'),
    'SchemaValidationResult': ('.schemas', 'SchemaValidationResult'),
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
