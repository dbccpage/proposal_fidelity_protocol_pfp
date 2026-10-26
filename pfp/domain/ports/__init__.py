"""Domain Ports package for the Symbol Game bounded context."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .biochem_ports import IAllostericGate, IKineticProofreader
    from .cec_bridge import ICecBridgeAdapter
    from .code_change_repository import ICodeChangeRepository
    from .exact_ports import ExactDigestPort, ExactFunctionalPort, ExactHolonomyPort, ExactHomologyPort, ExactLinearAlgebraPort, ExactPharmacyPort, RetractionEnginePort, get_retraction_port, set_retraction_port
    from .operad_ports import IOperadRouter, IPlanarGraftEvaluator
    from .ports import CanonicalSerializerProtocol, EvaluatorPort, IEventBus, IOutbox, ObstructionLedgerProtocol, PacketEnvelopeProtocol, ProjectorPort, SolverPort, StoragePort
    from .prompt_repository import IPromptRepository
    from .research_repository import IResearchRepository
    from .scoring_port import IScoringEvaluator
    from .turn_repository import ITurnRepository
    from .genesis_ports import IGenesisCrosswalkOracle, IGenesisStageRegistry
    from .tower_lift_ports import IFiniteExhaustionSearch, ILiftNecessityVerifier
    from .ast_cochain_ports import IAstDependencyParser, ILggrArbiter
    from .flagship_ports import ExactDualLpPort, LeanKernelBridgePort, ProcessSandboxPort

__all__ = ['CanonicalSerializerProtocol', 'EvaluatorPort', 'ExactDigestPort', 'ExactDualLpPort', 'ExactFunctionalPort', 'ExactHolonomyPort', 'ExactHomologyPort', 'ExactLinearAlgebraPort', 'ExactPharmacyPort', 'IAstDependencyParser', 'IAllostericGate', 'ICecBridgeAdapter', 'ICodeChangeRepository', 'IEventBus', 'IFiniteExhaustionSearch', 'IGenesisCrosswalkOracle', 'IGenesisStageRegistry', 'IKineticProofreader', 'ILearningRepository', 'ILggrArbiter', 'ILiftNecessityVerifier', 'IOperadRouter', 'IOutbox', 'IPlanarGraftEvaluator', 'IPromptRepository', 'IResearchRepository', 'IScoringEvaluator', 'ITurnRepository', 'LeanKernelBridgePort', 'ObstructionLedgerProtocol', 'PacketEnvelopeProtocol', 'ProcessSandboxPort', 'ProjectorPort', 'RetractionEnginePort', 'SolverPort', 'StoragePort', 'get_retraction_port', 'set_retraction_port']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'IAllostericGate': ('.biochem_ports', 'IAllostericGate'),
    'IKineticProofreader': ('.biochem_ports', 'IKineticProofreader'),
    'ICecBridgeAdapter': ('.cec_bridge', 'ICecBridgeAdapter'),
    'ICodeChangeRepository': ('.code_change_repository', 'ICodeChangeRepository'),
    'ExactDigestPort': ('.exact_ports', 'ExactDigestPort'),
    'ExactFunctionalPort': ('.exact_ports', 'ExactFunctionalPort'),
    'ExactHolonomyPort': ('.exact_ports', 'ExactHolonomyPort'),
    'ExactHomologyPort': ('.exact_ports', 'ExactHomologyPort'),
    'ExactLinearAlgebraPort': ('.exact_ports', 'ExactLinearAlgebraPort'),
    'ExactPharmacyPort': ('.exact_ports', 'ExactPharmacyPort'),
    'RetractionEnginePort': ('.exact_ports', 'RetractionEnginePort'),
    'get_retraction_port': ('.exact_ports', 'get_retraction_port'),
    'set_retraction_port': ('.exact_ports', 'set_retraction_port'),
    'IOperadRouter': ('.operad_ports', 'IOperadRouter'),
    'IPlanarGraftEvaluator': ('.operad_ports', 'IPlanarGraftEvaluator'),
    'CanonicalSerializerProtocol': ('.ports', 'CanonicalSerializerProtocol'),
    'EvaluatorPort': ('.ports', 'EvaluatorPort'),
    'IEventBus': ('.ports', 'IEventBus'),
    'IOutbox': ('.ports', 'IOutbox'),
    'ObstructionLedgerProtocol': ('.ports', 'ObstructionLedgerProtocol'),
    'PacketEnvelopeProtocol': ('.ports', 'PacketEnvelopeProtocol'),
    'ProjectorPort': ('.ports', 'ProjectorPort'),
    'SolverPort': ('.ports', 'SolverPort'),
    'StoragePort': ('.ports', 'StoragePort'),
    'IPromptRepository': ('.prompt_repository', 'IPromptRepository'),
    'IResearchRepository': ('.research_repository', 'IResearchRepository'),
    'IScoringEvaluator': ('.scoring_port', 'IScoringEvaluator'),
    'ITurnRepository': ('.turn_repository', 'ITurnRepository'),
    'IGenesisCrosswalkOracle': ('.genesis_ports', 'IGenesisCrosswalkOracle'),
    'IGenesisStageRegistry': ('.genesis_ports', 'IGenesisStageRegistry'),
    'IFiniteExhaustionSearch': ('.tower_lift_ports', 'IFiniteExhaustionSearch'),
    'ILiftNecessityVerifier': ('.tower_lift_ports', 'ILiftNecessityVerifier'),
    'IAstDependencyParser': ('.ast_cochain_ports', 'IAstDependencyParser'),
    'ILggrArbiter': ('.ast_cochain_ports', 'ILggrArbiter'),
    'ExactDualLpPort': ('.flagship_ports', 'ExactDualLpPort'),
    'LeanKernelBridgePort': ('.flagship_ports', 'LeanKernelBridgePort'),
    'ProcessSandboxPort': ('.flagship_ports', 'ProcessSandboxPort'),
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
