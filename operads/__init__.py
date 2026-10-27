"""Engine Operads (OEOP).

Shared capability definitions, compilation, and host projections.
Existing serialized OEWAS schema identifiers remain supported.
AuthorityEffect: None.

Public exports load only when requested; immune ports need no web/kernel runtime.
"""

from importlib import import_module

_EXPORTS = {
    "AUTHORITY_RANK": (".domain.value_objects", "AUTHORITY_RANK"),
    "AdmissionFacet": (".domain.value_objects", "AdmissionFacet"),
    "ArtifactOperandRef": (".domain.value_objects", "ArtifactOperandRef"),
    "AuthorityEffect": (".domain.value_objects", "AuthorityEffect"),
    "CapabilitySliceV3": (".domain.entities", "CapabilitySliceV3"),
    "CausationId": (".domain.value_objects", "CausationId"),
    "ColourId": (".domain.value_objects", "ColourId"),
    "CompositionV3": (".domain.entities", "CompositionV3"),
    "ContentDigest": (".domain.value_objects", "ContentDigest"),
    "CorrelationId": (".domain.value_objects", "CorrelationId"),
    "DeclarationFacet": (".domain.value_objects", "DeclarationFacet"),
    "DocumentId": (".domain.value_objects", "DocumentId"),
    "DocumentLeafNode": (".domain.entities", "DocumentLeafNode"),
    "EstateCatalogV3": (".domain.entities", "EstateCatalogV3"),
    "EstateRef": (".domain.value_objects", "EstateRef"),
    "ExecutorBindingFacet": (".domain.value_objects", "ExecutorBindingFacet"),
    "IdempotencyKey": (".domain.value_objects", "IdempotencyKey"),
    "InstructionOperand": (".domain.value_objects", "InstructionOperand"),
    "OeopApiV3": (".controllers.python_facade", "OeopApiV3"),
    "OeopContainer": (".infrastructure.bootstrap", "OeopContainer"),
    "OperandId": (".domain.value_objects", "OperandId"),
    "OperationId": (".domain.value_objects", "OperationId"),
    "OperationV3": (".domain.entities", "OperationV3"),
    "PortSpecV3": (".domain.entities", "PortSpecV3"),
    "ResidualPackageSpan": (".domain.value_objects", "ResidualPackageSpan"),
    "SchemaBindingFacet": (".domain.value_objects", "SchemaBindingFacet"),
    "SchemaRef": (".domain.value_objects", "SchemaRef"),
    "SkillDocumentV3": (".domain.entities", "SkillDocumentV3"),
    "SkillId": (".domain.value_objects", "SkillId"),
    "SkillLifecycleV3": (".domain.value_objects", "SkillLifecycleV3"),
    "SourceByteSpan": (".domain.value_objects", "SourceByteSpan"),
    "ValidationFacet": (".domain.value_objects", "ValidationFacet"),
    "WorkflowId": (".domain.value_objects", "WorkflowId"),
    "create_oeop_container": (".infrastructure.bootstrap", "create_oeop_container"),
    "create_oeop_router": (".controllers.router", "create_oeop_router"),
}
__all__ = tuple(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_EXPORTS))
