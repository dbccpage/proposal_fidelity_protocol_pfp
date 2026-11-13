"""Assemble only manually admitted, parent-confirmed frozen final-answer grades.

No discovery of run outputs. Only paths in criterion_assessments.json are read.
No proposal/repair text or provider reasoning is selected for grading.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

H = Path(__file__).resolve().parent
B = H.parent
RUBRIC_SHA = 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
REFERENCE_SHA = 'b2679b9ba498f4ed26533908ac7d1c7be5e0a3112d85cfb54f42b80d7dad79b6'
SEED_SHA = '9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7'
MAP = {'spectrum':'spectrum', 'dynamics':'dynamics', 'pure_state':'pure_entanglement',
       'thermal':'thermal_entanglement', 'checks':'checks'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(name, value):
    (H/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent-confirmed-frozen', action='store_true')
    args = parser.parse_args()
    rubric_path = B/'pilot_20261110/evaluator_rubric.json'
    assert digest(rubric_path) == RUBRIC_SHA
    assert digest(H/'reference_provenance.json') == REFERENCE_SHA
    provenance = read(H/'reference_provenance.json')
    assert provenance['current_run_output_content_read'] is False
    criteria = {c['id']:c for s in read(rubric_path)['sections'] for c in s['criteria']}
    assert len(criteria)==25 and sum(c['max_points'] for c in criteria.values())==100
    if not args.parent_confirmed_frozen:
        print(json.dumps({'ready':True,'current_outputs_accessed':False,'criteria':25}))
        return
    spec = importlib.util.spec_from_file_location('summary_validator', B/'summarize_runs.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    assessments = read(H/'criterion_assessments.json')
    grades = {}; evidence = {}; validations = []
    for item in assessments['runs']:
        assert item['parent_confirmed_frozen'] is True
        path = H/item['run_path']
        assert path.resolve().is_relative_to((H/'runs').resolve())
        run, run_sha = validator.read_frozen_receipt(path)
        run_id = run['run_id']
        assert run_id in provenance['expected_run_ids'] and run_id not in grades
        assert run_sha == item['run_sha256'] and run['answer_sha256'] == item['answer_sha256']
        assert run['seed_sha256'] == SEED_SHA
        answer = run['answer_text']
        rows = item['criteria']
        assert len(rows)==25 and {r['criterion_id'] for r in rows}==set(criteria)
        points = {name:0 for name in MAP.values()}; deductions=[]; quotes=0
        for row in rows:
            maximum = criteria[row['criterion_id']]['max_points']
            assert type(row['points']) is int and 0<=row['points']<=maximum and row['assessment']
            row['max_points']=maximum;row['deducted_points']=maximum-row['points']
            points[MAP[row['criterion_id'].split('.')[0]]]+=row['points']
            assert row['evidence']
            for ev in row['evidence']:
                if 'quote' in ev:
                    a,z=ev['character_range'];lo,hi=ev['line_range']
                    assert type(answer) is str and answer[a:z]==ev['quote']
                    assert '\n'.join(answer.splitlines()[lo-1:hi])==ev['quote'];quotes+=1
                elif ev['kind']=='no_delivered_final_answer':
                    assert answer is None and ev['json_pointer']=='/answer_text' and ev['observed_value'] is None
                    assert row['points']==0
                else:
                    assert ev['kind']=='full_final_body_review_for_omission'
                    assert type(answer) is str and ev['character_range']==[0,len(answer)]
            if row['deducted_points']:
                deductions.append({'criterion_id':row['criterion_id'],'points':row['deducted_points'],
                                   'reason':row['assessment'],'evidence':row['evidence']})
        grade={'run_id':run_id,'run_sha256':run_sha,'answer_sha256':run['answer_sha256'],
               'seed_sha256':SEED_SHA,'evaluator_id':'audit_systems_independent_public_seed_evaluator_v1',
               'method':'trusted_post_freeze_mathematical_review','rubric_sha256':RUBRIC_SHA,
               'reference_provenance_sha256':REFERENCE_SHA,'points':points,'deductions':deductions,
               'total':sum(points.values())}
        assert validator.validate_grade(grade,run,run_sha)==grade['total']
        assert sum(d['points'] for d in deductions)==100-grade['total']
        for counterexample in item.get('counterexamples',[]):
            for ev in counterexample.get('evidence',[]):
                a,z=ev['character_range'];lo,hi=ev['line_range']
                assert type(answer) is str and answer[a:z]==ev['quote']
                assert '\n'.join(answer.splitlines()[lo-1:hi])==ev['quote']
        grades[run_id]=grade
        host=run.get('host_checks') or {}
        safe_stages=[{'stage_id':s.get('stage_id'),'status':s.get('status'),
                      'accepted':s.get('accepted'),'feedback_kind':s.get('feedback',{}).get('kind'),
                      'feedback_code':s.get('feedback',{}).get('code'),
                      'native_executed':s.get('verification_receipt',{}).get('native_executed')}
                     for s in host.get('stage_checks',[])]
        evidence[run_id]={'run_sha256':run_sha,'answer_sha256':run['answer_sha256'],
            'seed_sha256':SEED_SHA,'rubric_sha256':RUBRIC_SHA,'reference_provenance_sha256':REFERENCE_SHA,
            'classification':item['classification'],'full_final_body_read':answer is not None,
            'reviewed_character_ranges':[] if answer is None else [[0,len(answer)]],
            'criteria':rows,'counterexamples':item.get('counterexamples',[]),
            'safe_host_status_projection':safe_stages,
            'content_policy':'Final answer only; no proposal, repair, checker or provider reasoning credit.'}
        calls=[{k:c.get(k) for k in ['stage_id','finish_reason','input_tokens','output_tokens','actual_microusd']}
               for c in run['calls'] if 'request' in c]
        assert sum(c['actual_microusd'] for c in calls)==run['budget']['spent_microusd']
        validations.append({'run_id':run_id,'run_path':item['run_path'],'run_sha256':run_sha,
            'answer_sha256':run['answer_sha256'],'status':run['status'],'grade_total':grade['total'],
            'criteria':25,'exact_quote_ranges_checked':quotes,'final_characters':None if answer is None else len(answer),
            'final_lines':None if answer is None else len(answer.splitlines()),'safe_call_metadata':calls,
            'spent_microusd':run['budget']['spent_microusd'],'held_microusd':run['budget']['held_microusd']})
    write('grades.json',grades)
    write('criterion_evidence.json',{'schema':'independent_charpoly_final_only_evidence_v1','runs':evidence})
    write('evaluation_validation.json',{'passed':True,'status':'complete' if len(grades)==2 else 'partial_awaiting_second_frozen_run',
        'validator_sha256':digest(B/'summarize_runs.py'),'rubric_sha256':RUBRIC_SHA,
        'reference_provenance_sha256':REFERENCE_SHA,'runs':validations,
        'pending_run_ids':[rid for rid in provenance['expected_run_ids'] if rid not in grades],
        'grades_sha256':digest(H/'grades.json'),'criterion_evidence_sha256':digest(H/'criterion_evidence.json'),
        'preparation_policy_update':'Original preparation planned to wait for both runs. Parent subsequently explicitly authorized grading the checked run immediately after its individual freeze; the other output is not accessed until its own freeze confirmation.',
        'limits':['One item and one attempt per arm; no general efficacy inference.',
                  'Mechanical validation checks custody, quotation and score arithmetic, not the trusted mathematical judgment.']})
    print(json.dumps({'passed':True,'grades':{rid:g['total'] for rid,g in grades.items()},'graded_runs':len(grades)}))

if __name__=='__main__':
    main()
