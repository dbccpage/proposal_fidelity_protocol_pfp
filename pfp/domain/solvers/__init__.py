"""Domain solvers, requirement kinds, stage contracts, and reading ladders.

Classification: Domain Solvers Root.
Governing Invariant: Clean Architecture Inward Dependency & Port Invariant.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .canon import dumps, loads, sha256_tag
    from .encoding import Descender, DownCheck, Encoding, certify_hosting, decode, descend, encode, hosting_history, symbols_of, token, value_of
    from .errors import ClaimFrozen, EmbargoRefusal, ExactError, IntakeRefusal, NonAdmissible, NonDescent, Refusal, SolverRefusal, StageRefusal
    from .guards import ResourceBound, check_delta_size, refuse
    from .iso import CanonKey, IsoBudgetError, automorphisms, canonical, find_iso, group_by_canonical, isomorphic, pair_orbits, rename, serialize
    from .kinds import Assign, Atom, Closure, ConstOracle, Denied, Forbid, Functional, Holds, HolonomyLoopClosed, HomologyBoundaryClosed, SimplicialBoundaryLawSatisfied, Inst, KINDS, Oracle, RegimeOracle, Req, Separate, Term, Total, forms_of, get_holonomy_port, get_homology_port, kind_of, matches, refutation, rename_req, req_json, satisfies, set_holonomy_port, set_homology_port
    from .ladder import Key, Leaf, Setting, Table, Tape, carrier_forget, collisions, explore, full_tables, functional, harness_restrict, key_at, keys, leaves_digest, lift_table, minima, run, universe_size
    from .regime import EMPTY, AdmissionError, AdmitDatum, AdmitForm, AdmitInst, AdmitRuleAll, Context, Delta, Event, Impose, IsoWitness, Item, NewDatum, NewForm, NewInst, NewRuleAll, Pair, Regime, Slot, Supply, apply_delta, canonical_delta, contexts, delta_events, derivable, item_key, mu1, mu2, plug, profile, profiles, replay, separable, slot_tuples, step
    from .regimek import BASE, RegimeK, Stage, admit_response, check_witness_only, claims_unchanged, host, valid_response
    from .retraction import RetractionLoopResult, RetractionTurnOutcome, compute_obstruction_score, execute_retraction_turn, run_retraction_loop
    from .simplicial_cochain import CochainGradientResult, Simplicial1Cochain, SimplicialCochainGradientSolver, CochainCarrier
    from .cochain_gradient_hook import CochainGradientInjectionHook, SimplicialRetractionReceipt, SimplicialTurnRecord, run_simplicial_retraction_loop
    from .search import EVAL_BUDGET, PERM_BUDGET, Exhaustion, Measure, WitnessResult, canonical_k, check_count, class_size_formula, decide_k, delta_json, denied_terminal, iter_class, pruning_sound
    from .stage import FORBIDDEN_FIELDS, ConditionResult, DownRule, LevelCounter, Licence, Route, StageProposal, Stop, certify, execute, family_digest, fits, licensed, regime_digest, restrict, route, stage_lt, uses_only
    from .structure import FiniteStructure, RelSym

__all__ = ['BASE', 'AdmissionError', 'AdmitDatum', 'AdmitForm', 'AdmitInst', 'AdmitRuleAll', 'Assign', 'Atom', 'CanonKey', 'ClaimFrozen', 'Closure', 'CochainGradientInjectionHook', 'CochainGradientResult', 'ConditionResult', 'ConstOracle', 'Context', 'Delta', 'Denied', 'Descender', 'DownCheck', 'DownRule', 'EMPTY', 'EVAL_BUDGET', 'EmbargoRefusal', 'Encoding', 'Event', 'ExactError', 'Exhaustion', 'FORBIDDEN_FIELDS', 'FiniteStructure', 'Forbid', 'Functional', 'Holds', 'HolonomyLoopClosed', 'HomologyBoundaryClosed', 'Impose', 'Inst', 'IntakeRefusal', 'IsoBudgetError', 'IsoWitness', 'Item', 'KINDS', 'Key', 'Leaf', 'LevelCounter', 'Licence', 'Measure', 'NewDatum', 'NewForm', 'NewInst', 'NewRuleAll', 'NonAdmissible', 'NonDescent', 'Oracle', 'PERM_BUDGET', 'Pair', 'Refusal', 'Regime', 'RegimeK', 'RegimeOracle', 'RelSym', 'Req', 'ResourceBound', 'RetractionLoopResult', 'RetractionTurnOutcome', 'Route', 'Separate', 'Setting', 'Simplicial1Cochain', 'SimplicialBoundaryLawSatisfied', 'SimplicialCochainGradientSolver', 'CochainCarrier', 'SimplicialRetractionReceipt', 'SimplicialTurnRecord', 'Slot', 'SolverRefusal', 'Stage', 'StageProposal', 'StageRefusal', 'Stop', 'Supply', 'Table', 'Tape', 'Term', 'Total', 'WitnessResult', 'admit_response', 'apply_delta', 'automorphisms', 'canonical', 'canonical_delta', 'canonical_k', 'carrier_forget', 'certify', 'certify_hosting', 'check_count', 'check_delta_size', 'check_witness_only', 'claims_unchanged', 'class_size_formula', 'collisions', 'compute_obstruction_score', 'contexts', 'decide_k', 'decode', 'delta_events', 'delta_json', 'denied_terminal', 'derivable', 'descend', 'dumps', 'encode', 'execute', 'execute_retraction_turn', 'explore', 'family_digest', 'find_iso', 'fits', 'forms_of', 'full_tables', 'functional', 'get_holonomy_port', 'get_homology_port', 'group_by_canonical', 'harness_restrict', 'host', 'hosting_history', 'isomorphic', 'item_key', 'iter_class', 'key_at', 'keys', 'kind_of', 'leaves_digest', 'licensed', 'lift_table', 'loads', 'matches', 'minima', 'mu1', 'mu2', 'pair_orbits', 'plug', 'profile', 'profiles', 'pruning_sound', 'refuse', 'refutation', 'regime_digest', 'rename', 'rename_req', 'replay', 'req_json', 'restrict', 'route', 'run', 'run_retraction_loop', 'run_simplicial_retraction_loop', 'satisfies', 'separable', 'serialize', 'set_holonomy_port', 'set_homology_port', 'sha256_tag', 'slot_tuples', 'stage_lt', 'step', 'symbols_of', 'token', 'universe_size', 'uses_only', 'valid_response', 'value_of']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'dumps': ('.canon', 'dumps'),
    'loads': ('.canon', 'loads'),
    'sha256_tag': ('.canon', 'sha256_tag'),
    'Descender': ('.encoding', 'Descender'),
    'DownCheck': ('.encoding', 'DownCheck'),
    'Encoding': ('.encoding', 'Encoding'),
    'certify_hosting': ('.encoding', 'certify_hosting'),
    'decode': ('.encoding', 'decode'),
    'descend': ('.encoding', 'descend'),
    'encode': ('.encoding', 'encode'),
    'hosting_history': ('.encoding', 'hosting_history'),
    'symbols_of': ('.encoding', 'symbols_of'),
    'token': ('.encoding', 'token'),
    'value_of': ('.encoding', 'value_of'),
    'ClaimFrozen': ('.errors', 'ClaimFrozen'),
    'EmbargoRefusal': ('.errors', 'EmbargoRefusal'),
    'ExactError': ('.errors', 'ExactError'),
    'IntakeRefusal': ('.errors', 'IntakeRefusal'),
    'NonAdmissible': ('.errors', 'NonAdmissible'),
    'NonDescent': ('.errors', 'NonDescent'),
    'Refusal': ('.errors', 'Refusal'),
    'SolverRefusal': ('.errors', 'SolverRefusal'),
    'StageRefusal': ('.errors', 'StageRefusal'),
    'ResourceBound': ('.guards', 'ResourceBound'),
    'check_delta_size': ('.guards', 'check_delta_size'),
    'refuse': ('.guards', 'refuse'),
    'CanonKey': ('.iso', 'CanonKey'),
    'IsoBudgetError': ('.iso', 'IsoBudgetError'),
    'automorphisms': ('.iso', 'automorphisms'),
    'canonical': ('.iso', 'canonical'),
    'find_iso': ('.iso', 'find_iso'),
    'group_by_canonical': ('.iso', 'group_by_canonical'),
    'isomorphic': ('.iso', 'isomorphic'),
    'pair_orbits': ('.iso', 'pair_orbits'),
    'rename': ('.iso', 'rename'),
    'serialize': ('.iso', 'serialize'),
    'Assign': ('.kinds', 'Assign'),
    'Atom': ('.kinds', 'Atom'),
    'Closure': ('.kinds', 'Closure'),
    'ConstOracle': ('.kinds', 'ConstOracle'),
    'Denied': ('.kinds', 'Denied'),
    'Forbid': ('.kinds', 'Forbid'),
    'Functional': ('.kinds', 'Functional'),
    'Holds': ('.kinds', 'Holds'),
    'HolonomyLoopClosed': ('.kinds', 'HolonomyLoopClosed'),
    'HomologyBoundaryClosed': ('.kinds', 'HomologyBoundaryClosed'),
    'SimplicialBoundaryLawSatisfied': ('.kinds', 'SimplicialBoundaryLawSatisfied'),
    'Inst': ('.kinds', 'Inst'),
    'KINDS': ('.kinds', 'KINDS'),
    'Oracle': ('.kinds', 'Oracle'),
    'RegimeOracle': ('.kinds', 'RegimeOracle'),
    'Req': ('.kinds', 'Req'),
    'Separate': ('.kinds', 'Separate'),
    'Term': ('.kinds', 'Term'),
    'Total': ('.kinds', 'Total'),
    'forms_of': ('.kinds', 'forms_of'),
    'get_holonomy_port': ('.kinds', 'get_holonomy_port'),
    'get_homology_port': ('.kinds', 'get_homology_port'),
    'kind_of': ('.kinds', 'kind_of'),
    'matches': ('.kinds', 'matches'),
    'refutation': ('.kinds', 'refutation'),
    'rename_req': ('.kinds', 'rename_req'),
    'req_json': ('.kinds', 'req_json'),
    'satisfies': ('.kinds', 'satisfies'),
    'set_holonomy_port': ('.kinds', 'set_holonomy_port'),
    'set_homology_port': ('.kinds', 'set_homology_port'),
    'Key': ('.ladder', 'Key'),
    'Leaf': ('.ladder', 'Leaf'),
    'Setting': ('.ladder', 'Setting'),
    'Table': ('.ladder', 'Table'),
    'Tape': ('.ladder', 'Tape'),
    'carrier_forget': ('.ladder', 'carrier_forget'),
    'collisions': ('.ladder', 'collisions'),
    'explore': ('.ladder', 'explore'),
    'full_tables': ('.ladder', 'full_tables'),
    'functional': ('.ladder', 'functional'),
    'harness_restrict': ('.ladder', 'harness_restrict'),
    'key_at': ('.ladder', 'key_at'),
    'keys': ('.ladder', 'keys'),
    'leaves_digest': ('.ladder', 'leaves_digest'),
    'lift_table': ('.ladder', 'lift_table'),
    'minima': ('.ladder', 'minima'),
    'run': ('.ladder', 'run'),
    'universe_size': ('.ladder', 'universe_size'),
    'EMPTY': ('.regime', 'EMPTY'),
    'AdmissionError': ('.regime', 'AdmissionError'),
    'AdmitDatum': ('.regime', 'AdmitDatum'),
    'AdmitForm': ('.regime', 'AdmitForm'),
    'AdmitInst': ('.regime', 'AdmitInst'),
    'AdmitRuleAll': ('.regime', 'AdmitRuleAll'),
    'Context': ('.regime', 'Context'),
    'Delta': ('.regime', 'Delta'),
    'Event': ('.regime', 'Event'),
    'Impose': ('.regime', 'Impose'),
    'IsoWitness': ('.regime', 'IsoWitness'),
    'Item': ('.regime', 'Item'),
    'NewDatum': ('.regime', 'NewDatum'),
    'NewForm': ('.regime', 'NewForm'),
    'NewInst': ('.regime', 'NewInst'),
    'NewRuleAll': ('.regime', 'NewRuleAll'),
    'Pair': ('.regime', 'Pair'),
    'Regime': ('.regime', 'Regime'),
    'Slot': ('.regime', 'Slot'),
    'Supply': ('.regime', 'Supply'),
    'apply_delta': ('.regime', 'apply_delta'),
    'canonical_delta': ('.regime', 'canonical_delta'),
    'contexts': ('.regime', 'contexts'),
    'delta_events': ('.regime', 'delta_events'),
    'derivable': ('.regime', 'derivable'),
    'item_key': ('.regime', 'item_key'),
    'mu1': ('.regime', 'mu1'),
    'mu2': ('.regime', 'mu2'),
    'plug': ('.regime', 'plug'),
    'profile': ('.regime', 'profile'),
    'profiles': ('.regime', 'profiles'),
    'replay': ('.regime', 'replay'),
    'separable': ('.regime', 'separable'),
    'slot_tuples': ('.regime', 'slot_tuples'),
    'step': ('.regime', 'step'),
    'BASE': ('.regimek', 'BASE'),
    'RegimeK': ('.regimek', 'RegimeK'),
    'Stage': ('.regimek', 'Stage'),
    'admit_response': ('.regimek', 'admit_response'),
    'check_witness_only': ('.regimek', 'check_witness_only'),
    'claims_unchanged': ('.regimek', 'claims_unchanged'),
    'host': ('.regimek', 'host'),
    'valid_response': ('.regimek', 'valid_response'),
    'RetractionLoopResult': ('.retraction', 'RetractionLoopResult'),
    'RetractionTurnOutcome': ('.retraction', 'RetractionTurnOutcome'),
    'compute_obstruction_score': ('.retraction', 'compute_obstruction_score'),
    'execute_retraction_turn': ('.retraction', 'execute_retraction_turn'),
    'run_retraction_loop': ('.retraction', 'run_retraction_loop'),
    'CochainGradientResult': ('.simplicial_cochain', 'CochainGradientResult'),
    'Simplicial1Cochain': ('.simplicial_cochain', 'Simplicial1Cochain'),
    'SimplicialCochainGradientSolver': ('.simplicial_cochain', 'SimplicialCochainGradientSolver'),
    'CochainCarrier': ('.simplicial_cochain', 'CochainCarrier'),
    'CochainGradientInjectionHook': ('.cochain_gradient_hook', 'CochainGradientInjectionHook'),
    'SimplicialRetractionReceipt': ('.cochain_gradient_hook', 'SimplicialRetractionReceipt'),
    'SimplicialTurnRecord': ('.cochain_gradient_hook', 'SimplicialTurnRecord'),
    'run_simplicial_retraction_loop': ('.cochain_gradient_hook', 'run_simplicial_retraction_loop'),
    'EVAL_BUDGET': ('.search', 'EVAL_BUDGET'),
    'PERM_BUDGET': ('.search', 'PERM_BUDGET'),
    'Exhaustion': ('.search', 'Exhaustion'),
    'Measure': ('.search', 'Measure'),
    'WitnessResult': ('.search', 'WitnessResult'),
    'canonical_k': ('.search', 'canonical_k'),
    'check_count': ('.search', 'check_count'),
    'class_size_formula': ('.search', 'class_size_formula'),
    'decide_k': ('.search', 'decide_k'),
    'delta_json': ('.search', 'delta_json'),
    'denied_terminal': ('.search', 'denied_terminal'),
    'iter_class': ('.search', 'iter_class'),
    'pruning_sound': ('.search', 'pruning_sound'),
    'FORBIDDEN_FIELDS': ('.stage', 'FORBIDDEN_FIELDS'),
    'ConditionResult': ('.stage', 'ConditionResult'),
    'DownRule': ('.stage', 'DownRule'),
    'LevelCounter': ('.stage', 'LevelCounter'),
    'Licence': ('.stage', 'Licence'),
    'Route': ('.stage', 'Route'),
    'StageProposal': ('.stage', 'StageProposal'),
    'Stop': ('.stage', 'Stop'),
    'certify': ('.stage', 'certify'),
    'execute': ('.stage', 'execute'),
    'family_digest': ('.stage', 'family_digest'),
    'fits': ('.stage', 'fits'),
    'licensed': ('.stage', 'licensed'),
    'regime_digest': ('.stage', 'regime_digest'),
    'restrict': ('.stage', 'restrict'),
    'route': ('.stage', 'route'),
    'stage_lt': ('.stage', 'stage_lt'),
    'uses_only': ('.stage', 'uses_only'),
    'FiniteStructure': ('.structure', 'FiniteStructure'),
    'RelSym': ('.structure', 'RelSym'),
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
