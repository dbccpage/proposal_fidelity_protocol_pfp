"""Domain package for the Epistemic Immune System (OEEIS).

Pure value objects and gates: the two-signal danger gate and the independence
check for its signals, thymic negative selection, the exact allosteric gate,
idle-run counters, learned-guard activation and external antibody admission.
No module here imports an outer layer.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .allostery import AllostericConsensusGate
    from .clonal_selection import ClonalSelectionEngine
    from .danger_gate import TwoSignalDangerGate
    from .danger_signals import HOST_DANGER_SIGNAL_KINDS, SignalIndependenceRefusal, assert_signals_independent
    from .ports import AntigenMatcher, DangerSensor, ImmuneQuarantineSink, MatcherBindingRefusal, SelfPanelStore
    from .safe_pattern import UnsafePatternRefusal, compile_safe_pattern
    from .thymus import ThymusGate
    from .treg import AuthorityLevel, AutoimmuneToxicityReport, RegulatoryAntibody, TregSupervisor
    from .value_objects import REGEX_MATCHER_ID, AllosteryRefusal, DangerDecision, DangerSeverity, DetectorRule, HillParameters, Signal1Match, Signal2Danger
    from .pharmacy_catalog import PharmacyCatalogRepository
    from .pharmacy_models import Antibody, ConstraintType, Operatorizability, PharmacyStatus, RuntimeAction, Severity
    from .pharmacy_seeder import PharmacySeeder
    from .pharmacy_templates import ANTIBODY_TEMPLATES, CANONICAL_ANTIBODY_TEMPLATES, AntibodyTemplate, classify_failure, generic_template
    from .retired_antibodies import RETIRED_ANTIBODIES, RETIRED_ANTIBODY_IDS, RetirementRecord, is_retired, retirement_reason

__all__ = ['AllostericConsensusGate', 'AllosteryRefusal', 'AntigenMatcher', 'AuthorityLevel', 'AutoimmuneToxicityReport', 'ClonalSelectionEngine', 'DangerDecision', 'DangerSensor', 'DangerSeverity', 'DetectorRule', 'HOST_DANGER_SIGNAL_KINDS', 'HillParameters', 'ImmuneQuarantineSink', 'MatcherBindingRefusal', 'REGEX_MATCHER_ID', 'RegulatoryAntibody', 'SelfPanelStore', 'Signal1Match', 'Signal2Danger', 'SignalIndependenceRefusal', 'ThymusGate', 'TregSupervisor', 'TwoSignalDangerGate', 'UnsafePatternRefusal', 'assert_signals_independent', 'compile_safe_pattern', 'Antibody', 'AntibodyTemplate', 'ANTIBODY_TEMPLATES', 'CANONICAL_ANTIBODY_TEMPLATES', 'ConstraintType', 'Operatorizability', 'PharmacyCatalogRepository', 'PharmacySeeder', 'PharmacyStatus', 'RETIRED_ANTIBODIES', 'RETIRED_ANTIBODY_IDS', 'RetirementRecord', 'RuntimeAction', 'Severity', 'classify_failure', 'generic_template', 'is_retired', 'retirement_reason']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AllostericConsensusGate': ('.allostery', 'AllostericConsensusGate'),
    'ClonalSelectionEngine': ('.clonal_selection', 'ClonalSelectionEngine'),
    'TwoSignalDangerGate': ('.danger_gate', 'TwoSignalDangerGate'),
    'HOST_DANGER_SIGNAL_KINDS': ('.danger_signals', 'HOST_DANGER_SIGNAL_KINDS'),
    'SignalIndependenceRefusal': ('.danger_signals', 'SignalIndependenceRefusal'),
    'assert_signals_independent': ('.danger_signals', 'assert_signals_independent'),
    'AntigenMatcher': ('.ports', 'AntigenMatcher'),
    'DangerSensor': ('.ports', 'DangerSensor'),
    'ImmuneQuarantineSink': ('.ports', 'ImmuneQuarantineSink'),
    'MatcherBindingRefusal': ('.ports', 'MatcherBindingRefusal'),
    'SelfPanelStore': ('.ports', 'SelfPanelStore'),
    'UnsafePatternRefusal': ('.safe_pattern', 'UnsafePatternRefusal'),
    'compile_safe_pattern': ('.safe_pattern', 'compile_safe_pattern'),
    'ThymusGate': ('.thymus', 'ThymusGate'),
    'AuthorityLevel': ('.treg', 'AuthorityLevel'),
    'AutoimmuneToxicityReport': ('.treg', 'AutoimmuneToxicityReport'),
    'RegulatoryAntibody': ('.treg', 'RegulatoryAntibody'),
    'TregSupervisor': ('.treg', 'TregSupervisor'),
    'REGEX_MATCHER_ID': ('.value_objects', 'REGEX_MATCHER_ID'),
    'AllosteryRefusal': ('.value_objects', 'AllosteryRefusal'),
    'DangerDecision': ('.value_objects', 'DangerDecision'),
    'DangerSeverity': ('.value_objects', 'DangerSeverity'),
    'DetectorRule': ('.value_objects', 'DetectorRule'),
    'HillParameters': ('.value_objects', 'HillParameters'),
    'Signal1Match': ('.value_objects', 'Signal1Match'),
    'Signal2Danger': ('.value_objects', 'Signal2Danger'),
    'PharmacyCatalogRepository': ('.pharmacy_catalog', 'PharmacyCatalogRepository'),
    'Antibody': ('.pharmacy_models', 'Antibody'),
    'ConstraintType': ('.pharmacy_models', 'ConstraintType'),
    'Operatorizability': ('.pharmacy_models', 'Operatorizability'),
    'PharmacyStatus': ('.pharmacy_models', 'PharmacyStatus'),
    'RuntimeAction': ('.pharmacy_models', 'RuntimeAction'),
    'Severity': ('.pharmacy_models', 'Severity'),
    'PharmacySeeder': ('.pharmacy_seeder', 'PharmacySeeder'),
    'ANTIBODY_TEMPLATES': ('.pharmacy_templates', 'ANTIBODY_TEMPLATES'),
    'CANONICAL_ANTIBODY_TEMPLATES': ('.pharmacy_templates', 'CANONICAL_ANTIBODY_TEMPLATES'),
    'AntibodyTemplate': ('.pharmacy_templates', 'AntibodyTemplate'),
    'classify_failure': ('.pharmacy_templates', 'classify_failure'),
    'generic_template': ('.pharmacy_templates', 'generic_template'),
    'RETIRED_ANTIBODIES': ('.retired_antibodies', 'RETIRED_ANTIBODIES'),
    'RETIRED_ANTIBODY_IDS': ('.retired_antibodies', 'RETIRED_ANTIBODY_IDS'),
    'RetirementRecord': ('.retired_antibodies', 'RetirementRecord'),
    'is_retired': ('.retired_antibodies', 'is_retired'),
    'retirement_reason': ('.retired_antibodies', 'retirement_reason'),
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
