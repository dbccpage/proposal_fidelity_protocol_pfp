"""Lazy public exports; optional adapters load only on use."""

from importlib import import_module

_EXPORTS = {
    "CecBridgeAdapter": ".cec_bridge_adapter",
    "ObstructionLedgerAdapter": ".obstruction_adapter",
    "OesosEvidenceAdapter": ".oesos_evidence_adapter",
    "AIRY_CARRIER_ID": ".research_solvers",
    "AIRY_OBSTRUCTION_ID": ".research_solvers",
    "AIRY_PACKET_FAMILY": ".research_solvers",
    "AIRY_SOLVER_ID": ".research_solvers",
    "AiryCriticalCarrierV1": ".research_solvers",
    "AiryCriticalStateV1": ".research_solvers",
    "AiryNewtonProposalSolver": ".research_solvers",
    "ComplexScalarV1": ".research_solvers",
    "CochainCarrier": ".research_solvers",
    "CochainProjector": ".research_solvers",
    "CochainState": ".research_solvers",
    "CodaCascadeProposalSolver": ".research_solvers",
    "build_airy_problem": ".research_solvers",
    "build_coda_problem": ".research_solvers",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value
