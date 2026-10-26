"""Legacy Symbol Game copy of the epistemic immune domain.

LEGACY COPY (notice added 2026-09-29). The owner of immune logic is the
Epistemic Immune System package, `omega_engine_epistemic_immune_system`
(OEEIS); new code must use it (Woland and OEWAS consume it through ports).
This package is a second, diverged copy kept only because existing callers
import it (Symbol Game tests and the c001 attention-mask challenge). It is not
reconciled with OEEIS. Known differences:

- `DetectionContext.granted_persona_roles` defaults to `()` here and to
  `("agent", "researcher")` in OEEIS, and the persona marker lists differ, so
  PERSONA_AUTHORITY_LEAK fires on different inputs;
- the pharmacy here is a Python re-implementation; OEEIS runs the eleven
  native classes of `omega_prompt_civilization` and keeps only the persona
  check in Python;
- the danger gate here puts a HIGH or CRITICAL Signal 2 alone into
  DEFENSIVE_LOCKDOWN; OEEIS requires both signals to suppress and refuses a
  Signal 2 derived from Signal 1 (`TWO_SIGNAL_COLLAPSE`).

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .clonal_selection import ClonalCandidate, ClonalSelectionEngine, DetectorRule, KillConditionReceipt, KillConditionRefusal
    from .danger_gate import DangerDecision, DangerEvaluationResult, DangerSeverity, Signal1AstMatch, Signal1Match, Signal2Danger, Signal2DangerState, TwoSignalDangerGate, TwoSignalDecision
    from .models import CodeString, DetectionContext, DetectorReport, Disposition, FailureClass, FailureReceipt, Finding, HostReplayReceipt, PharmacyDisposition, detect
    from .thymus import ApoptosisReceipt, SelfPanel, SelfPanelEntry, ThymusGate, ThymusSelectionResult
    from .allostery import AllostericQuorumGate, QuorumState
    from .complement import ComplementCascade, ComplementCascadeReceipt, ComplementStage
    from .mhc import EpitopeSlice, MhcPresentationWindow
    from .proofreading import KineticProofreader
    from .treg import AuthorityLevel, AutoimmuneToxicityReport, RegulatoryAntibody, TregSupervisor

__all__ = ['CodeString', 'FailureClass', 'PharmacyDisposition', 'Disposition', 'Finding', 'FailureReceipt', 'HostReplayReceipt', 'DetectionContext', 'DetectorReport', 'detect', 'SelfPanelEntry', 'SelfPanel', 'ApoptosisReceipt', 'ThymusSelectionResult', 'ThymusGate', 'DangerDecision', 'DangerSeverity', 'Signal1AstMatch', 'Signal1Match', 'Signal2DangerState', 'Signal2Danger', 'TwoSignalDecision', 'DangerEvaluationResult', 'TwoSignalDangerGate', 'AuthorityLevel', 'AutoimmuneToxicityReport', 'RegulatoryAntibody', 'TregSupervisor', 'ClonalCandidate', 'DetectorRule', 'KillConditionReceipt', 'KillConditionRefusal', 'ClonalSelectionEngine', 'AllostericQuorumGate', 'QuorumState', 'ComplementCascade', 'ComplementCascadeReceipt', 'ComplementStage', 'KineticProofreader', 'EpitopeSlice', 'MhcPresentationWindow']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ClonalCandidate': ('.clonal_selection', 'ClonalCandidate'),
    'ClonalSelectionEngine': ('.clonal_selection', 'ClonalSelectionEngine'),
    'DetectorRule': ('.clonal_selection', 'DetectorRule'),
    'KillConditionReceipt': ('.clonal_selection', 'KillConditionReceipt'),
    'KillConditionRefusal': ('.clonal_selection', 'KillConditionRefusal'),
    'DangerDecision': ('.danger_gate', 'DangerDecision'),
    'DangerEvaluationResult': ('.danger_gate', 'DangerEvaluationResult'),
    'DangerSeverity': ('.danger_gate', 'DangerSeverity'),
    'Signal1AstMatch': ('.danger_gate', 'Signal1AstMatch'),
    'Signal1Match': ('.danger_gate', 'Signal1Match'),
    'Signal2Danger': ('.danger_gate', 'Signal2Danger'),
    'Signal2DangerState': ('.danger_gate', 'Signal2DangerState'),
    'TwoSignalDangerGate': ('.danger_gate', 'TwoSignalDangerGate'),
    'TwoSignalDecision': ('.danger_gate', 'TwoSignalDecision'),
    'CodeString': ('.models', 'CodeString'),
    'DetectionContext': ('.models', 'DetectionContext'),
    'DetectorReport': ('.models', 'DetectorReport'),
    'Disposition': ('.models', 'Disposition'),
    'FailureClass': ('.models', 'FailureClass'),
    'FailureReceipt': ('.models', 'FailureReceipt'),
    'Finding': ('.models', 'Finding'),
    'HostReplayReceipt': ('.models', 'HostReplayReceipt'),
    'PharmacyDisposition': ('.models', 'PharmacyDisposition'),
    'detect': ('.models', 'detect'),
    'ApoptosisReceipt': ('.thymus', 'ApoptosisReceipt'),
    'SelfPanel': ('.thymus', 'SelfPanel'),
    'SelfPanelEntry': ('.thymus', 'SelfPanelEntry'),
    'ThymusGate': ('.thymus', 'ThymusGate'),
    'ThymusSelectionResult': ('.thymus', 'ThymusSelectionResult'),
    'AllostericQuorumGate': ('.allostery', 'AllostericQuorumGate'),
    'QuorumState': ('.allostery', 'QuorumState'),
    'ComplementCascade': ('.complement', 'ComplementCascade'),
    'ComplementCascadeReceipt': ('.complement', 'ComplementCascadeReceipt'),
    'ComplementStage': ('.complement', 'ComplementStage'),
    'EpitopeSlice': ('.mhc', 'EpitopeSlice'),
    'MhcPresentationWindow': ('.mhc', 'MhcPresentationWindow'),
    'KineticProofreader': ('.proofreading', 'KineticProofreader'),
    'AuthorityLevel': ('.treg', 'AuthorityLevel'),
    'AutoimmuneToxicityReport': ('.treg', 'AutoimmuneToxicityReport'),
    'RegulatoryAntibody': ('.treg', 'RegulatoryAntibody'),
    'TregSupervisor': ('.treg', 'TregSupervisor'),
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
