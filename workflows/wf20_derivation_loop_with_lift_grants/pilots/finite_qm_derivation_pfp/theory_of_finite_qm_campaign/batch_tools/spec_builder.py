"""Compact builder for a node spec (specs/<NODE>.json) with the standard four native gates.

The mathematics of a node (producer, independent checker, wire formatter, semantic mutants, Lean module)
is written by the researcher. This module only assembles the bookkeeping around it, so that every node
declares the same gates: Python tests, a Rust lib test filter, a Rust replay example fed with the public
TSV, and a Lean module compiled with `lean -j 1` whose `#print axioms` anchors are checked against the
standard axiom set. Nothing here accepts a theorem. AuthorityEffect: None.

    from spec_builder import build_spec, write_spec
    spec = build_spec(node='X', short='x', lean='XModule', anchors=['XModule.thm'], ...)
    write_spec(spec_dir, 'X', spec)
"""
from __future__ import annotations

import json
from pathlib import Path

from stages import CARGO_TESTS

BUILD_SOURCES = ['code/rust/Cargo.toml', 'code/rust/src/finite_probability/Cargo.toml', 'code/rust/Cargo.lock',
                 'lean4/lake-manifest.json', 'lean4/lean-toolchain']


def _lean_gate(lean):
    return {'id': 'lean', 'argv': ['{lean}', '-j', '1', '-o', '.lake/build/lib/lean/%s.olean' % lean, lean + '.lean'],
            'needs': 'lean', 'cwd': 'lean4'}


def build_spec(*, node, short, lean, anchors, cases, public_tsv, data, scope_review, predicates, boundary, generators,
               relations, compositions, open_obligations, colour_meanings=None, failed_compositions=(), counterexamples=(),
               depends_on_result=False, qualification=None, checker_id=None, challenge_plan=None, composition_tree=None,
               construction=None, extra_sources=(), carrier=None, coefficient_ring='Exact integers and rationals',
               relation_evidence=None, python_test=None, rust_filter=None, rust_example=None, extra_gates=(),
               max_coordinate_mutants=None, ignore_paths=(), semantic_waiver=None, reviewer=None):
    """Assemble the spec dict. `generators` items need id, ordered_inputs, output, semantic_predicate, hypotheses."""
    python_test = python_test or 'code/python/tests/test_pfp_%s.py' % short
    rust_filter = rust_filter or 'pfp_%s' % short
    rust_example = rust_example or 'pfp_%s_replay' % short
    production = ['lean4/%s.lean' % lean, 'code/python/src/qm/pfp_%s.py' % short, python_test,
                  'code/rust/src/finite_probability/pfp_%s.rs' % short,
                  'code/rust/src/finite_probability/examples/%s.rs' % rust_example] + list(extra_sources)
    carrier = carrier or ', '.join(sorted({c for g in generators for c in g['ordered_inputs']} | {g['output'] for g in generators}))
    ops = []
    for g in generators:
        ops.append(dict(g, arity=len(g['ordered_inputs']), carrier=g.get('carrier', g['ordered_inputs'][0]),
                        coefficient_ring=g.get('coefficient_ring', coefficient_ring)))
    # A composition whose slot colour differs from the inner output colour is not a graft of this presentation (validate_prompts refuses it):
    # record it as a failed composition with the reason instead of a checked one.
    by_id = {g['id']: g for g in ops}
    checked, demoted = [], []
    for c in compositions:
        outer, inner = by_id.get(c['outer_operation']), by_id.get(c['inner_operation'])
        slot = c.get('input_slot', 0)
        if outer is not None and inner is not None and type(slot) is int and 0 <= slot < len(outer['ordered_inputs']) and outer['ordered_inputs'][slot] == inner['output']:
            checked.append(c)
        else:
            demoted.append({'composition': '%s (slot %s) o %s' % (c['outer_operation'], slot, c['inner_operation']),
                            'reason': 'Colour mismatch: the outer slot takes %s but the inner operation outputs %s; composing needs a coercion or a partial-map convention that this presentation does not contain, so it is not a checked graft.' % (
                                outer['ordered_inputs'][slot] if outer and type(slot) is int and 0 <= slot < len(outer['ordered_inputs']) else '?', inner['output'] if inner else '?'),
                            'original_entry': c})
    if not checked:
        # prepare_stage refuses a work unit without a typed composition: add the first colour-correct graft, claiming nothing beyond its typing.
        for outer in ops:
            for slot, colour in enumerate(outer['ordered_inputs']):
                found = next((i for i in ops if i['id'] != outer['id'] and i['output'] == colour), None)
                if found and not checked:
                    checked.append({'outer_operation': outer['id'], 'input_slot': slot, 'inner_operation': found['id'],
                                    'colour_match': '%s -> %s' % (found['output'], colour),
                                    'hypothesis_match': 'Typing only: the inner output colour equals the outer slot colour; hypotheses of both operations apply unchanged.',
                                    'licensing_relations': [], 'evidence_status': 'Colour-typed graft; no relation is claimed to license it and no result is attached to the composite.'})
    compositions, failed_compositions = checked, list(failed_compositions) + demoted
    gates = [
        {'id': 'python', 'argv': ['{python}', '-X', 'utf8', python_test, '-v'], 'needs': None, 'cwd': '.'},
        {'id': 'rust', 'argv': ['{cargo}', 'test', '--manifest-path', 'code/rust/Cargo.toml', '-p', 'tfqm_finite_probability', '--lib',
                                rust_filter, '--offline', '--locked'], 'needs': 'cargo', 'cwd': '.'},
        {'id': 'rust_replay', 'argv': ['{cargo}', 'run', '--manifest-path', 'code/rust/Cargo.toml', '-p', 'tfqm_finite_probability',
                                       '--example', rust_example, '--offline', '--locked'], 'needs': 'cargo', 'cwd': '.',
         'stdin_file': 'public_input.tsv'},
        _lean_gate(lean)] + list(extra_gates)
    boundary = dict(boundary)
    profile = {
        'source_review_status': 'semantics_reviewed_for_selected_step', 'source_scope_review': scope_review,
        'independent_predicates': list(predicates), 'claim_boundary': boundary, 'carrier': carrier, 'coefficient_ring': coefficient_ring,
        'production_sources': production, 'build_sources': list(BUILD_SOURCES),
        'challenge_plan': challenge_plan or 'Coordinate mutants of every certificate leaf plus task-specific semantic near misses.',
        'composition_tree': list(composition_tree or ['%s o %s' % (c['outer_operation'], c['inner_operation']) for c in compositions]),
        'anchors': list(anchors), 'checker_id': checker_id or ('independent-%s-v1' % short.replace('_', '-')),
        'result_or_obstruction': boundary['narrowest_claim'], 'next_mathematical_step': boundary['next_test'],
        'report': '# %s\n\n%s\n\nSupported: %s\n\nRemaining: %s' % (node, scope_review, boundary['supports'], boundary['does_not_support']),
        'construction': construction or scope_review, 'colour_meanings': dict(colour_meanings or {}),
        'lean_anchors': list(anchors), 'relation_evidence': dict(relation_evidence or {}),
        'dag_status_depends_on_result': bool(depends_on_result),
        'p2_gates': gates,
        'p2_checks': {'lean': {'gate': 'lean', 'anchors': list(anchors)}, 'wire': {'gate': 'rust_replay'},
                      'tests': {'python': {'gate': 'python', 'stream': 'stderr'},
                                'rust': {'gate': 'rust', 'stream': 'stdout', 'pattern': CARGO_TESTS}}},
        'challenge': {'ignore_paths': list(ignore_paths), 'max_coordinate_mutants': max_coordinate_mutants},
    }
    if semantic_waiver:
        profile['challenge']['semantic_waiver'] = semantic_waiver
    if qualification:
        profile['review'] = {'reviewed_target_qualification': qualification}
    spec = {'profile': profile, 'public_input': {'cases': cases}, 'operad_delta': {
        'add_or_refine_generators': ops, 'add_or_refine_relations': list(relations), 'checked_compositions': list(compositions),
        'failed_compositions': list(failed_compositions), 'counterexamples': list(counterexamples), 'open_obligations': list(open_obligations)},
        'checker': '%s_check.py' % short, 'format': '%s_format.py' % short, 'semantic_mutants': '%s_semantic.py' % short,
        'candidate': {'data': data, 'public_tsv': public_tsv}}
    if reviewer:
        spec['reviewer'] = reviewer
    return spec


def write_spec(spec_dir, node, spec):
    path = Path(spec_dir) / (node + '.json')
    path.write_bytes((json.dumps(spec, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
    return path
