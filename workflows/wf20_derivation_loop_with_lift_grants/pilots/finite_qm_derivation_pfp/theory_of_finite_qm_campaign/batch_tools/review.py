"""Batch review: seal each run, refine evidence status without promoting a target, record second reviewers.

The author reviews their own run here, which is a self-review. A node whose profile sets
dag_status_depends_on_result needs a second review by a different reviewer; finalize refuses
to seal without one. Source text, stage bytes and historical labels are preserved.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import json_bytes, load_json, load_yaml, replace_bytes, require, save, sha, yaml_bytes, yaml_new  # noqa: E402
from stages import Batch  # noqa: E402

GITATTRIBUTES = b'* -text whitespace=-trailing-space,-blank-at-eof\n'
CLOSING_OBLIGATION = ('A source provider PASS/hash, route index, census label or Boolean flag is not mathematical evidence for '
                      'the original target. No historical provider receipt is newly authenticated.')


def review_dir(batch: Batch, task, label) -> Path:
    return batch.run(task).parent.parent / 'reviews' / label


def review_node(batch: Batch, task, label, second_reviews=None):
    ctx = batch.ctx
    run, row = batch.run(task), batch.row(task)
    review = review_dir(batch, task, label)
    profile = load_json(run / 'p0/profile.json')
    accepted = load_json(run / 'accepted.json')
    path = ctx.root / row['operad_collection']
    collection = load_yaml(path)
    save(review / 'run_manifest.json', {'artifacts': [{'path': p.relative_to(run).as_posix(), 'sha256': sha(p)}
                                                      for p in sorted(run.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]})
    yaml_new(review / 'collection_before_review.yaml', collection)
    delta = load_yaml(run / 'p5/operad_delta.yaml')
    refinement = profile.get('review', {})
    if refinement.get('reviewed_target_qualification'):
        delta['review_scope_clarifications'] = {
            'reviewed_target_qualification': refinement['reviewed_target_qualification'],
            'historical_target_status': 'Original target retained verbatim as source history; the corrected narrow scope governs this run.'}
    hypotheses = list(dict.fromkeys(h for g in delta['add_or_refine_generators'] for h in g.get('hypotheses', [])))
    delta['scope_refinements'] = {
        'historical_source_assumptions_are_not_the_full_work_unit_contract': True, 'work_unit_admitted_hypotheses': hypotheses,
        'boundary': 'Finite carriers, declared operations/readouts and actual native bounds are supplied assumptions, even when the historical source assumption list is empty.'}
    for generator in delta['add_or_refine_generators']:
        generator['evidence_status'] = ('Reviewed exact finite native controls. Kernel signatures are separately scoped. '
                                        'Full refined-carrier operad instantiation remains open.')
    for relation in delta['add_or_refine_relations']:
        relation['historical_evidence_annotation'] = relation['evidence_status']
        relation['evidence_status'] = ('Accepted actual P2 and P4 controls; only the literal named Lean signatures are kernel theorems. '
                                       'Native array-to-signature and physical transports remain as stated.')
        relation['named_Lean_scope'] = profile.get('lean_anchors', [])
    for composition in delta['checked_compositions']:
        composition['hypothesis_match'] = composition.get('hypothesis_match', '') + (
            ' Fixed contexts must agree across both operations. Formal universal refined-carrier closure is unpaid.')
    delta['open_obligations'].append(CLOSING_OBLIGATION)
    yaml_new(review / 'operad_delta.yaml', delta)
    needs_second = bool(profile.get('dag_status_depends_on_result'))
    second = (second_reviews or {}).get(task)
    author = batch.policy().get('researcher', 'one local researcher')
    independent = bool(second and second.get('reviewer') and second['reviewer'] != author)
    save(review / 'scope_review.json', {
        'task_id': task, 'reviewed_finding': profile['source_scope_review'], 'claim_boundary': profile['claim_boundary'], 'accepted': accepted,
        'additional_scope_clarifications': delta.get('review_scope_clarifications', {}),
        'reviewer': author + ' (author self-review). Separate checker code and native kernels do not constitute an independent author/model panel.',
        'needs_second_reviewer': needs_second, 'second_review': second, 'second_review_independent': independent, 'authority_effect': 'None'})
    if delta.get('review_scope_clarifications'):
        collection.setdefault('scope_notes', []).append(delta['review_scope_clarifications']['reviewed_target_qualification'])
        collection['reviewed_target_qualification'] = {'text': delta['review_scope_clarifications']['reviewed_target_qualification'],
                                                       'status': 'corrected_or_qualified_scope',
                                                       'review': ctx.rel(review / 'scope_review.json')}
    collection['presentation'].update(status='scoped_stage_result_reviewed', generators=delta['add_or_refine_generators'],
                                      relations=delta['add_or_refine_relations'], compositions=delta['checked_compositions'],
                                      failed_compositions=delta['failed_compositions'], counterexamples=delta['counterexamples'],
                                      coherence_obligations=delta['open_obligations'])
    collection['latest_run']['status'] = 'scoped_result_or_obstruction_reviewed'
    collection['latest_review'] = {'path': ctx.rel(review), 'status': 'scope_reviewed_pending_final_integration',
                                   'operad_delta': ctx.rel(review / 'operad_delta.yaml')}
    collection['open_obligations'] = delta['open_obligations']
    prepare = ctx.prepare
    collection['operad_slots'][prepare.SLOTS[1]]['composition_plan'] = delta['checked_compositions']
    collection['operad_slots_scope']['review_refinement'] = ctx.rel(review / 'scope_review.json')
    ambient = collection['operad_slots'][prepare.SLOTS[0]]
    ambient['historical_source_assumptions'] = list(ambient.get('admitted_assumptions', []))
    ambient['work_unit_admitted_hypotheses'] = hypotheses
    ambient['admitted_assumptions'] = list(dict.fromkeys(ambient['historical_source_assumptions'] + hypotheses))
    replace_bytes(path, yaml_bytes(collection))
    gitattributes = run.parent.parent / '.gitattributes'
    if not gitattributes.exists():
        gitattributes.write_bytes(GITATTRIBUTES)
    (review / 'README.md').write_bytes(('# ' + task + ' review\n\n' + profile['source_scope_review'] + '\n\nSupported: ' + profile['claim_boundary']['supports'] +
                                        '\n\nRemaining: ' + profile['claim_boundary']['does_not_support'] + '\n\nNext test: ' + profile['claim_boundary']['next_test'] +
                                        '\n\nHistorical source annotations and all stage bytes are preserved. No external provider dispatched. AuthorityEffect: None.\n').encode('utf-8'))
    index = load_json(ctx.index_path)
    entry = next(n for n in index['nodes'] if n['node_id'] == task)
    entry.update(status='scoped_result_or_obstruction_reviewed', latest_review=ctx.rel(review))
    replace_bytes(ctx.index_path, json_bytes(index))
    return {'task': task, 'review': 'scoped_result_or_obstruction_reviewed', 'needs_second_reviewer': needs_second, 'independent': independent}


def review_all(batch: Batch, label, second_reviews=None):
    return [review_node(batch, task, label, second_reviews) for task in batch.tasks()]
