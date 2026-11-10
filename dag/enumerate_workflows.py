"""Enumerate a declared finite design space, without pretending to compile it.

Every result is a new proposed composition requiring the named adapter contracts.
An external signature is not a native OPERADS port or an implemented QM checker.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAG = ROOT / 'dag'
MAX_CALLS = 4
MAX_EXPANDED_NODES = 16
MAX_MACROS = 4

def read(path):
    return json.loads((DAG / path).read_text(encoding='utf-8'))

def model_stage(stage):
    kind = stage['kind'].lower()
    if kind in ('model', 'model_or_host'):
        return True
    if kind == 'host':
        return False
    raise ValueError(f'Unrecognized stage kind: {kind}')

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def enumerate_space(reports, families, grammar):
    signatures = {}
    for group in grammar['proposed_family_external_signatures']:
        for name in group['families']:
            signatures[name] = group['signature'].split(' -> ')
    if {v for v in signatures if v.startswith('WF')} != {f'WF{i}' for i in range(1, 50)}:
        raise ValueError('Incomplete existing family signature table')
    descriptors = []
    for family in families:
        signatures_pair = signatures[family['id']]
        descriptors.append({
            'id': family['id'], 'origin': 'existing_family',
            'input_type': signatures_pair[0], 'output_type': signatures_pair[1],
            'source': family['definition'], 'definition_sha256': hashlib.sha256((ROOT / family['definition']).read_bytes()).hexdigest(),
            'status': 'external_signature_proposed_native_bindings_pending',
            'max_calls': None, 'normal_path_calls_source': family.get('model_calls_normal_path'),
            'known_normal_path_calls': int(family['model_calls_normal_path']) if str(family.get('model_calls_normal_path', '')).isdigit() else None,
            'expanded_nodes': None, 'grad_qm_applicability': family.get('grad_qm_seed'),
        })
    for report in reports:
        for idea in report['ideas']:
            calls = sum(model_stage(s) for s in idea['stages'])
            input_type, output_type = signatures.get(idea['id'], ('RunContext', 'Outcome'))
            descriptors.append({
                'id': idea['id'], 'origin': 'research_idea',
                'input_type': input_type, 'output_type': output_type,
                'source': f"dag/research/research_{report['agent_number']:02d}.json",
                'definition_sha256': digest(idea), 'status': 'whole_run_envelope_proposed_no_automatic_native_cast',
                'max_calls': calls, 'expanded_nodes': len(idea['stages']),
                'max_output_tokens': sum(s.get('max_output_tokens', 0) for s in idea['stages'] if model_stage(s)),
                'budget_formula': idea['budget_formula'],
                'required_external_bindings': idea['typed_inputs'],
                'uninstantiated_signature': idea.get('mathematical_basis',{}).get('external_signature') if isinstance(idea.get('mathematical_basis'),dict) else None,
                'workflow_output_exclusions': [s for s in idea['typed_outputs'] if 'OfflineOnly' in s or 'PostFreeze' in s],
                'scope_note': 'This design envelope requires a task-specific adapter. A composition with prior context is a new hypothesis and does not inherit the standalone experiment or independence assumptions.',
            })

    by_id = {d['id']: d for d in descriptors}
    if len(by_id) != len(descriptors):
        raise ValueError('Duplicate macro ID')
    solvers = [d for d in descriptors if (d['input_type'], d['output_type']) == ('RunContext', 'Outcome')]
    # These constructors retain the original answer and append a scoped receipt.
    # Preservation and noninterference remain explicit unimplemented obligations.
    annotation_inputs = {'TranslationTask', 'RewriteTask', 'CustodyTask', 'ClaimTask', 'AuthorityTask', 'LeakAuditTask'}
    annotations = [d for d in descriptors if d['input_type'] in annotation_inputs]
    candidates = []; rejected = Counter()

    def candidate(seq, bridge, terminal='Outcome'):
        ds = [by_id[name] for name in seq]
        known_calls = sum(d['max_calls'] if d['max_calls'] is not None else (d.get('known_normal_path_calls') or 0) for d in ds)
        if known_calls > MAX_CALLS:
            rejected['known_path_exceeds_max_paid_calls'] += 1
            return
        calls = None if any(d['max_calls'] is None for d in ds) else sum(d['max_calls'] for d in ds)
        nodes = None if any(d['expanded_nodes'] is None for d in ds) else sum(d['expanded_nodes'] for d in ds) + len(ds) - 1
        if calls is not None and calls > MAX_CALLS:
            rejected['max_paid_calls'] += 1
            return
        if nodes is not None and nodes > MAX_EXPANDED_NODES:
            rejected['max_expanded_nodes'] += 1
            return
        payload = {'macros': list(seq), 'bridge': bridge, 'definition_pins': [d['definition_sha256'] for d in ds]}
        candidates.append({
            'id': 'COMPOSE:' + digest(payload)[:24], 'kind': 'proposed_workflow_composition',
            **payload, 'input_type': 'RunContext', 'output_type': terminal,
            'model_calls_upper_bound_before_adapter': calls,
            'expanded_node_count_before_adapter_lowering': nodes,
            'status': 'design_candidate_with_open_admission_obligations',
            'runnable': False, 'evaluated': False,
            'shared_run_cap_usd': '0.10',
            'cost_admission': 'unresolved_until_current_tariffs_and_full_composed_request_bounds_are_pinned',
            'obligation_set': 'COMPOSITION_ADMISSION_V1',
        })

    # All distinct ordered pairs from existing solver envelopes and research ideas.
    # Unknown old macro internals are retained as unresolved design candidates.
    for left, right in itertools.permutations(solvers, 2):
        candidate((left['id'], right['id']), 'public_outcome_reentry_v1')
    for solver in solvers:
        for annotator in annotations:
            candidate((solver['id'], annotator['id']), 'public_outcome_to_' + annotator['input_type'] + '_with_scoped_annotation_v1')

    # Longer compositions require finite research descriptors. Unknown-cost opaque
    # legacy macros cannot be expanded into an arbitrarily deep permutation space.
    finite = [d for d in solvers if d['origin'] == 'research_idea']
    for length in range(3, MAX_MACROS + 1):
        for seq in itertools.permutations(finite, length):
            candidate(tuple(d['id'] for d in seq), 'public_outcome_reentry_v1')
    ids = [c['id'] for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate canonical composition ID')
    return {
        'schema_version': '1.0', 'status': 'finite_design_enumeration_complete_for_declared_slice',
        'research_reports_present': len(reports), 'ten_researchers_complete': len(reports) == 10,
        'exhaustiveness_scope': 'All distinct ordered solver pairs and solver-to-annotation pairs in this pinned registry; all length 3..4 ordered research-solver permutations satisfying paid-call/node bounds. This is not every possible operadic tree, branch structure, model setting, parameter choice or future idea.',
        'bounds': {'max_macro_occurrences': MAX_MACROS, 'max_paid_calls': MAX_CALLS, 'max_expanded_nodes': MAX_EXPANDED_NODES, 'max_opaque_legacy_macros_per_candidate': 2, 'repeat_same_macro': False, 'retries_added_by_composer': 0, 'shared_run_cap_usd': '0.10'},
        'definition_of_nontrivial': 'At least two distinct mechanisms connected by an explicit producer-consumer bridge; order is retained. Administrative renaming and JSON key order are quotiented; stochastic draws, prompt order and distinct mechanism orders are not identified.',
        'excluded_grammars': ['Campaign/transfer/detector-construction operations require independent typed external inputs and are retained as standalone catalog entries; they are not cast from a solver response.', 'Opaque historical macros occur only in pairs until internal calls, stages and applicability are pinned.', 'General multi-input trees and native fan-out require additional adapters and are not enumerated in this slice.', 'No repeated mechanism, free-text parameter sweep, private-score feedback, or implicit retries.'],
        'obligation_sets': {'COMPOSITION_ADMISSION_V1': [
            'Exact original seed bytes and requested conclusions remain unchanged and actually included in every solver request.',
            'Every bridge has concrete schemas, validators, source pins and a preserving implementation; external type names alone are insufficient.',
            'Every independently required checker/panel/theory/assignment bundle is supplied and frozen. Curried RunContext->Outcome notation does not manufacture these inputs from a prior answer. Post-freeze and offline campaign outputs have no workflow consumers.',
            'Prior-outcome input is public candidate evidence, never trusted truth. Standalone blind/independent stages retain their visibility rules; otherwise the combination is refused or relabeled as a changed experiment.',
            'Do not inherit integer-sum, cochain or graph checker adequacy for the QM seed. Unsupported mathematics remains OPEN.',
            'Mutated candidates invalidate stale receipts; annotation does not upgrade a predicate-scoped result into global correctness.',
            'Reserve the complete expanded path under a single durable USD0.10 ledger using validated input/output/reasoning/fee upper bounds and current tariffs; sum of standalone estimates is not sufficient.',
            'Keep key and post-freeze evaluator completely outside workflow context and tools.',
            'Apply native OPERADS restrictions if lowered there, including exact full-port equality and single-consumer outputs. No fan-out is inferred.',
        ]},
        'descriptors': descriptors, 'candidate_count': len(candidates),
        'counts_by_macro_length': dict(Counter(len(c['macros']) for c in candidates)),
        'rejected_by_first_bound': dict(rejected), 'candidates': candidates,
    }

def main():
    reports = [json.loads(p.read_text(encoding='utf-8')) for p in sorted((DAG / 'research').glob('research_*.json'))]
    families = read('reviews/workflows_audit.json')['registry']['family_nodes']
    grammar = read('research/research_04.json')['finite_composition_grammar']
    result = enumerate_space(reports, families, grammar)
    (DAG / 'composition_catalog.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('candidate_count', 'counts_by_macro_length', 'rejected_by_first_bound', 'ten_researchers_complete')}))

if __name__ == '__main__':
    main()
