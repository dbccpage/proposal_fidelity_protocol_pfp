"""Lazy public exports; optional adapters load only on use."""

from importlib import import_module

_EXPORTS = {
    "CecBridgeAdapter": ".adapters",
    "ObstructionLedgerAdapter": ".adapters",
    "OesosEvidenceAdapter": ".adapters",
    "InMemoryEventBus": ".events",
    "OutboxMessage": ".events",
    "TransactionalOutbox": ".events",
    "FilePromptRepository": ".persistence",
    "InMemoryDbContext": ".persistence",
    "MemoryPromptRepository": ".persistence",
    "MemoryTurnRepository": ".persistence",
    "SymbolGameDbContext": ".persistence",
    "ENVELOPE_SCHEMA_V2": ".serialization",
    "canonical_bytes": ".serialization",
    "canonical_unwire": ".serialization",
    "canonical_wire": ".serialization",
    "deserialize_envelope_v2": ".serialization",
    "deserialize_prompt_artifact": ".serialization",
    "domain_digest": ".serialization",
    "freeze": ".serialization",
    "serialize_envelope_v2": ".serialization",
    "serialize_prompt_artifact": ".serialization",
    "thaw": ".serialization",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value


_EXPORTS.update(
    {
        "UnifiedPfpDemoRunner": ".pilot_runners.pilot_dispatch",
        "ExactRationalSolver": ".exact_math",
        "AdversaryTribunalGateEvaluator": ".gate_evaluators",
        "FourObjectPacketSuite": ".mssn_transcoder",
        "MssnTranscoderError": ".mssn_transcoder",
        "digest": ".mssn_transcoder",
        "PfpPilotRunner": ".pilot_runner",
        "OfflineDeterministicPfpProvider": ".providers",
        "PfpReportingAdapter": ".reporting",
        "PfpSchemaValidatorAdapter": ".schema_validator",
        "PfpFileSystemStorageAdapter": ".storage",
    }
)
__all__ = list(dict.fromkeys([*__all__, *_EXPORTS]))
