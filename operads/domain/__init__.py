"""Pure WAS Domain (Zero Infrastructure Dependencies).

Public exports load only when requested; immune ports need no web/kernel runtime.
"""

from importlib import import_module

_EXPORTS = {
    "AUTHORITY_RANK": (".value_objects", "AUTHORITY_RANK"),
    "AdmissionFacet": (".value_objects", "AdmissionFacet"),
    "AgentCapabilityV1": (".capability_catalog_v1", "AgentCapabilityV1"),
    "ArtifactOperandRef": (".value_objects", "ArtifactOperandRef"),
    "AuthorityCeilingExceededError": (".errors", "AuthorityCeilingExceededError"),
    "AuthorityEffect": (".value_objects", "AuthorityEffect"),
    "CapabilityCatalogRefusal": (".capability_catalog_v1", "CapabilityCatalogRefusal"),
    "CapabilityCatalogV1": (".capability_catalog_v1", "CapabilityCatalogV1"),
    "CapabilitySliceV3": (".entities", "CapabilitySliceV3"),
    "CatalogCompiledV3": (".events", "CatalogCompiledV3"),
    "CausationId": (".value_objects", "CausationId"),
    "ColourId": (".value_objects", "ColourId"),
    "CompositionBoundV3": (".events", "CompositionBoundV3"),
    "CompositionV3": (".entities", "CompositionV3"),
    "ContentDigest": (".value_objects", "ContentDigest"),
    "CorrelationId": (".value_objects", "CorrelationId"),
    "DeclarationFacet": (".value_objects", "DeclarationFacet"),
    "DocumentId": (".value_objects", "DocumentId"),
    "DocumentImportedV3": (".events", "DocumentImportedV3"),
    "DocumentLeafNode": (".entities", "DocumentLeafNode"),
    "DomainEventV3": (".events", "DomainEventV3"),
    "DomainInvariantError": (".errors", "DomainInvariantError"),
    "EstateCapturedV3": (".events", "EstateCapturedV3"),
    "EstateCatalogV3": (".entities", "EstateCatalogV3"),
    "EstateRef": (".value_objects", "EstateRef"),
    "ExecutorBindingFacet": (".value_objects", "ExecutorBindingFacet"),
    "ExecutorBindingV1": (".capability_catalog_v1", "ExecutorBindingV1"),
    "IdempotencyKey": (".value_objects", "IdempotencyKey"),
    "InstructionOperand": (".value_objects", "InstructionOperand"),
    "InvalidCompositionError": (".errors", "InvalidCompositionError"),
    "OeopDomainError": (".errors", "OeopDomainError"),
    "OperandId": (".value_objects", "OperandId"),
    "OperationDeclaredV3": (".events", "OperationDeclaredV3"),
    "OperationId": (".value_objects", "OperationId"),
    "OperationV3": (".entities", "OperationV3"),
    "PortSpecV3": (".entities", "PortSpecV3"),
    "ResidualPackageSpan": (".value_objects", "ResidualPackageSpan"),
    "ResourceRefV1": (".capability_catalog_v1", "ResourceRefV1"),
    "SchemaBindingFacet": (".value_objects", "SchemaBindingFacet"),
    "SchemaMismatchError": (".errors", "SchemaMismatchError"),
    "SchemaRef": (".value_objects", "SchemaRef"),
    "SkillCapabilityV1": (".capability_catalog_v1", "SkillCapabilityV1"),
    "SkillConsolidationRecordedV3": (".events", "SkillConsolidationRecordedV3"),
    "SkillDocumentV3": (".entities", "SkillDocumentV3"),
    "SkillId": (".value_objects", "SkillId"),
    "SkillLifecycleV3": (".value_objects", "SkillLifecycleV3"),
    "SourceByteSpan": (".value_objects", "SourceByteSpan"),
    "UnresolvedResidualError": (".errors", "UnresolvedResidualError"),
    "ValidationFacet": (".value_objects", "ValidationFacet"),
    "WorkflowId": (".value_objects", "WorkflowId"),
    "compute_agent_license_digest": (".capability_catalog_v1", "compute_agent_license_digest"),
    "decode_capability_catalog": (".capability_catalog_v1", "decode_capability_catalog"),
    "encode_capability_catalog": (".capability_catalog_v1", "encode_capability_catalog"),
    "seal_capability_catalog": (".capability_catalog_v1", "seal_capability_catalog"),
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
