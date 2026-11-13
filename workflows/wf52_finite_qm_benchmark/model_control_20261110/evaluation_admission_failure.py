"""Retain a frozen pre-dispatch infrastructure failure without grading a model answer."""
import hashlib
import importlib.util
import json
from pathlib import Path

H = Path(__file__).resolve().parent
RUN_ID = 'qm-model-20261110:direct:000'
RUN_SHA = '3936a5f565ea826681d621bd619968094207f38f26ee26f3e157816d25e427b6'
REF_SHA = '4a9e28ec4e48aa23fb4cbfe23320f7e288a96804a5fc67cba528651d06078a14'
RUBRIC_SHA = 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H / 'reference_provenance.json') == REF_SHA
rubric_path = H.parent / 'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path) == RUBRIC_SHA
validator_path = H.parent / 'summarize_runs.py'
spec = importlib.util.spec_from_file_location('admission_failure_validator', validator_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
run, run_sha = module.read_frozen_receipt(H / 'runs/00_direct/run.json')
assert run_sha == RUN_SHA and run['run_id'] == RUN_ID
assert run['status'] == 'admission_failure'
assert run['answer_text'] is None and run['answer_sha256'] is None
assert run['budget']['spent_microusd'] == run['budget']['held_microusd'] == 0
assert len(run['calls']) == 1 and run['calls'][0]['dispatched'] is False
assert run['calls'][0]['error'] == 'Previous prepared dispatch must not be overwritten'
rubric = json.loads(rubric_path.read_text(encoding='utf-8'))
reason = 'No final answer was delivered: a pre-dispatch provider-instance admission guard rejected this orchestration attempt. Zero delivered-solution points; model mathematical performance is not assessable.'
rows = [{'criterion_id': c['id'], 'max_points': c['max_points'], 'points': 0,
         'deducted_points': c['max_points'], 'assessment': reason,
         'evidence': [{'kind': 'no_delivered_final_answer', 'answer_text': None,
                       'run_status': run['status'], 'dispatched': False}]} for s in rubric['sections'] for c in s['criteria']]
assert len(rows) == 25 and sum(c['max_points'] for c in rows) == 100
deductions = [{'criterion_id': c['criterion_id'], 'points': c['max_points'],
               'reason': reason, 'evidence': c['evidence']} for c in rows]
grade = {'run_id': RUN_ID, 'run_sha256': run_sha, 'answer_sha256': None,
         'seed_sha256': run['seed_sha256'], 'evaluator_id': 'audit_systems_independent_public_seed_evaluator_v1',
         'method': 'trusted_post_freeze_mathematical_review', 'rubric_sha256': RUBRIC_SHA,
         'reference_provenance_sha256': REF_SHA, 'points': {k: 0 for k in module.RUBRIC},
         'deductions': deductions, 'total': 0,
         'outcome_class': 'infrastructure_admission_failure_before_dispatch',
         'model_mathematical_performance_assessable': False}
assert module.validate_grade(grade, run, run_sha) == 0
def write(name, data):
    (H / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
write('grades.json', {RUN_ID: grade})
write('criterion_evidence.json', {'run_id': RUN_ID, 'run_sha256': run_sha,
      'answer_sha256': None, 'seed_sha256': run['seed_sha256'], 'rubric_sha256': RUBRIC_SHA,
      'reference_provenance_sha256': REF_SHA, 'final_answer_present': False,
      'full_final_body_read': False, 'reviewed_character_ranges': [],
      'criteria': rows, 'outcome_class': grade['outcome_class'],
      'model_mathematical_performance_assessable': False,
      'dispatch_attempt_records': 1, 'provider_dispatches': 0,
      'error': run['calls'][0]['error'], 'spent_microusd': 0, 'held_microusd': 0,
      'limits': ['This is zero delivered-solution credit in the all-attempt denominator, not evidence of an incorrect model answer.']})
(H / 'evaluation.md').write_text('''# Original model-control admission failure

**0/100 delivered-solution points; no model mathematical answer to assess.**

The frozen run ended in `admission_failure` before provider dispatch. One failed attempt record says `dispatched=false` and records “Previous prepared dispatch must not be overwritten”. The final answer and answer hash are null. Spending and held charges are both zero.

All25 unchanged rubric criteria receive zero delivered-solution credit so this attempted run remains in the all-attempt denominator. This is an infrastructure/orchestration failure, not a mathematical model failure or evidence about the model's ability. The separately named corrected campaign is a new attempt and does not overwrite this record.

Receipt, seed, rubric and pre-output public-reference bindings were verified. No response text, draft, private answer material or provider call was accessed or executed by the evaluator.
''', encoding='utf-8')
write('evaluation_validation.json', {'passed': True, 'runs': 1, 'criteria': 25,
      'run_id': RUN_ID, 'run_sha256': run_sha, 'answer_sha256': None,
      'seed_sha256': run['seed_sha256'], 'rubric_sha256': RUBRIC_SHA,
      'reference_provenance_sha256': REF_SHA, 'validator_sha256': sha(validator_path),
      'validate_grade_passed': True, 'total': 0, 'deductions_total': 100,
      'provider_dispatches': 0, 'spent_microusd': 0, 'held_microusd': 0,
      'model_mathematical_performance_assessable': False,
      'artifacts': [{'path': str((H / name).relative_to(H.parent.parent.parent)).replace('\\', '/'), 'sha256': sha(H / name)} for name in
                    ['reference_provenance.json', 'grades.json', 'criterion_evidence.json', 'evaluation.md', 'evaluation_admission_failure.py']]})
print(json.dumps({'passed': True, 'total': 0, 'provider_dispatches': 0,
      'model_mathematical_performance_assessable': False,
      'hashes': {name: sha(H / name) for name in ['grades.json', 'criterion_evidence.json', 'evaluation.md', 'evaluation_validation.json']}}))
