"""Final-only manual-grade custody tools; no output access without an explicit freeze flag.

Default invocation validates preparation only. After the parent confirms freezing,
--inspect prints only final answer_text; --grade assembles manual criterion judgments.
This code never performs a provider call or reads intermediate response content.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCHMARK = HERE.parent
RUN_ID = 'qm-model-repaired-20261110:direct:000'
RUN_PATH = HERE / 'runs/00_direct/run.json'
RUBRIC = BENCHMARK / 'pilot_20261110/evaluator_rubric.json'
RUBRIC_SHA = 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
PROVENANCE_SHA = '74e0aac9ae4e707cf0e10beecf53123b9d5f03bb5224cac8f9911546d1d045a6'
SECTION_MAP = {'spectrum': 'spectrum', 'dynamics': 'dynamics',
               'pure_state': 'pure_entanglement', 'thermal': 'thermal_entanglement',
               'checks': 'checks'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def preparation():
    raw = RUBRIC.read_bytes()
    assert sha(raw) == RUBRIC_SHA, 'Original rubric changed'
    provenance_raw = (HERE / 'reference_provenance.json').read_bytes()
    assert sha(provenance_raw) == PROVENANCE_SHA, 'Reference provenance changed'
    provenance = json.loads(provenance_raw)
    assert provenance['current_run_output_content_read'] is False
    rubric = json.loads(raw)
    criteria = {c['id']: c for s in rubric['sections'] for c in s['criteria']}
    assert len(criteria) == 25 and sum(c['max_points'] for c in criteria.values()) == 100
    return criteria


def validator():
    path = BENCHMARK / 'summarize_runs.py'
    spec = importlib.util.spec_from_file_location('manual_grade_validator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, sha(path.read_bytes())


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-confirmed-frozen', action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--inspect', action='store_true')
    group.add_argument('--grade', action='store_true')
    args = parser.parse_args()
    criteria = preparation()
    if not args.inspect and not args.grade:
        print(json.dumps({'ready': True, 'criteria': 25, 'current_output_accessed': False,
                          'rubric_sha256': RUBRIC_SHA, 'reference_sha256': PROVENANCE_SHA}))
        return
    if not args.parent_confirmed_frozen:
        parser.error('Explicit parent freeze confirmation is required before output access')
    module, validator_sha = validator()
    receipt, run_sha = module.read_frozen_receipt(RUN_PATH)
    assert receipt['run_id'] == RUN_ID
    answer = receipt['answer_text']
    if args.inspect:
        print(json.dumps({'run_id': RUN_ID, 'run_sha256': run_sha,
                          'answer_sha256': receipt['answer_sha256'],
                          'characters': None if answer is None else len(answer)}))
        print('FINAL ANSWER ONLY')
        print(answer)
        print('END FINAL ANSWER')
        return
    manual = json.loads((HERE / 'criterion_assessments.json').read_text(encoding='utf-8'))
    assert manual['run_sha256'] == run_sha
    assert manual['answer_sha256'] == receipt['answer_sha256']
    rows = manual['criteria']
    assert len(rows) == len(criteria) and {r['criterion_id'] for r in rows} == set(criteria)
    points = {key: 0 for key in module.RUBRIC}
    deductions = []
    for row in rows:
        criterion = criteria[row['criterion_id']]
        maximum = criterion['max_points']
        assert type(row['points']) in (int, float) and 0 <= row['points'] <= maximum
        assert row['assessment']
        row['max_points'] = maximum
        row['deducted_points'] = maximum - row['points']
        points[SECTION_MAP[row['criterion_id'].split('.')[0]]] += row['points']
        for evidence in row['evidence']:
            if 'quote' in evidence:
                start, end = evidence['character_range']
                assert answer[start:end] == evidence['quote']
            else:
                assert evidence['kind'] == 'full_final_body_review_for_omission'
                assert evidence['character_range'] == [0, len(answer)]
        if row['deducted_points']:
            deductions.append({'criterion_id': row['criterion_id'],
                               'points': row['deducted_points'], 'reason': row['assessment'],
                               'evidence': row['evidence']})
    grade = {'run_id': RUN_ID, 'run_sha256': run_sha,
             'answer_sha256': receipt['answer_sha256'], 'seed_sha256': receipt['seed_sha256'],
             'evaluator_id': 'audit_systems_independent_public_seed_evaluator_v1',
             'method': 'trusted_post_freeze_mathematical_review',
             'rubric_sha256': RUBRIC_SHA, 'reference_provenance_sha256': PROVENANCE_SHA,
             'points': points, 'deductions': deductions, 'total': sum(points.values())}
    assert module.validate_grade(grade, receipt, run_sha) == grade['total']
    assert sum(d['points'] for d in deductions) == 100 - grade['total']
    write_json('grades.json', {RUN_ID: grade})
    write_json('criterion_evidence.json', {'run_id': RUN_ID, 'run_sha256': run_sha,
               'answer_sha256': receipt['answer_sha256'], 'seed_sha256': receipt['seed_sha256'],
               'rubric_sha256': RUBRIC_SHA, 'reference_provenance_sha256': PROVENANCE_SHA,
               'full_final_body_read': True, 'reviewed_character_ranges': [[0, len(answer)]],
               'criteria': rows, 'counterexamples': manual.get('counterexamples', []),
               'limits': ['Final-answer content only; no draft or checker credit.',
                          'One length-control attempt on one item; no general ranking.']})
    write_json('evaluation_validation.json', {'passed': True, 'runs': 1, 'criteria': 25,
               'validator_sha256': validator_sha, 'rubric_sha256': RUBRIC_SHA,
               'reference_provenance_sha256': PROVENANCE_SHA,
               'grades_sha256': sha((HERE / 'grades.json').read_bytes()),
               'criterion_evidence_sha256': sha((HERE / 'criterion_evidence.json').read_bytes()),
               'checks': ['Frozen run and answer hashes', 'validate_grade',
                          'Unchanged criterion IDs and maxima', 'Exact quote ranges',
                          'Per-section totals and deductions']})
    print(json.dumps({'validated': True, 'total': grade['total'], 'points': points}))


if __name__ == '__main__':
    main()
