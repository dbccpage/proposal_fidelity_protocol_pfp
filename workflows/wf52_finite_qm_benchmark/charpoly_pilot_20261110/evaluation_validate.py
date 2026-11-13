"""Final independent custody, score, quote and two finite-branch controls.

No intermediate proposal/repair content, private reference or provider calls.
"""
import hashlib
import json
from pathlib import Path

H=Path(__file__).resolve().parent
B=H.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(H/'reference_provenance.json')=='b2679b9ba498f4ed26533908ac7d1c7be5e0a3112d85cfb54f42b80d7dad79b6'
rubric_path=B/'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path)=='eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
caps={c['id']:c['max_points'] for s in read(rubric_path)['sections'] for c in s['criteria']}
grades=read(H/'grades.json');evidence=read(H/'criterion_evidence.json')['runs']
assert set(grades)==set(evidence) and len(grades)==2
mapping={'spectrum':'spectrum','dynamics':'dynamics','pure_state':'pure_entanglement','thermal':'thermal_entanglement','checks':'checks'}
expected=[
 ('runs/00_checked/run.json','64bdea8a8391b5bdc20e8bb517c88531616a1a24f852a1de0e7bf0ded64ae747',None,0,1685),
 ('runs/01_ungated/run.json','28a9aa26ee1fa6caa87817541573b3a86d4ead368d4ad8d979a05c5a667eb93c','92dff27860cdb2b6db06847c45bf30d4556b1a614ac20805f921024061650a00',47,5329),
]
quotes=0;cost=0;graded=[]
for path,run_sha,answer_sha,total,spent in expected:
    p=H/path;run=read(p);answer=run['answer_text'];rid=run['run_id']
    assert sha(p)==run_sha and (p.parent/'run.sha256').read_text().strip()==run_sha
    assert run['answer_sha256']==answer_sha
    if answer is None:assert answer_sha is None
    else:assert hashlib.sha256(answer.encode()).hexdigest()==answer_sha
    assert run['seed_sha256']=='9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7'
    g=grades[rid];ev=evidence[rid]
    for key,value in [('run_sha256',run_sha),('answer_sha256',answer_sha),('seed_sha256',run['seed_sha256'])]:
        assert g[key]==ev[key]==value
    assert g['method']=='trusted_post_freeze_mathematical_review'
    rows=ev['criteria'];assert len(rows)==25 and {r['criterion_id'] for r in rows}==set(caps)
    sums={s:0 for s in mapping.values()}
    def check_quote(q):
        a,z=q['character_range'];lo,hi=q['line_range']
        assert type(answer) is str and 0<=a<=z<=len(answer) and answer[a:z]==q['quote']
        assert '\n'.join(answer.splitlines()[lo-1:hi])==q['quote']
    for row in rows:
        maximum=caps[row['criterion_id']]
        assert row['max_points']==maximum and type(row['points']) is int and 0<=row['points']<=maximum
        assert row['deducted_points']==maximum-row['points']
        sums[mapping[row['criterion_id'].split('.')[0]]]+=row['points']
        for q in row['evidence']:
            if 'quote' in q:check_quote(q);quotes+=1
            elif q['kind']=='no_delivered_final_answer':
                assert answer is None and q['observed_value'] is None and q['json_pointer']=='/answer_text'
            else:
                assert q['kind']=='full_final_body_review_for_omission'
                assert q['character_range']==[0,len(answer)] and q['line_range']==[1,len(answer.splitlines())]
    assert sums==g['points'] and sum(sums.values())==g['total']==total
    assert sum(d['points'] for d in g['deductions'])==100-total
    for d in g['deductions']:
        row=next(r for r in rows if r['criterion_id']==d['criterion_id'])
        assert d['points']==row['deducted_points'] and d['reason']==row['assessment'] and d['evidence']==row['evidence']
    for ce in ev['counterexamples']:
        for q in ce['evidence']:check_quote(q)
    assert run['budget']['spent_microusd']==spent and run['budget']['held_microusd']==0
    cost+=spent
    if total==0:
        assert run['status']=='certificate_refused' and answer is None
        assert ev['classification']=='safe_encoding_gate_refusal_no_delivered_solution'
        assert ev['reviewed_character_ranges']==[]
        stages=ev['safe_host_status_projection']
        assert [x['feedback_code'] for x in stages]==['RATIONAL_NONCANONICAL','MALFORMED_JSON']
        assert all(x['native_executed'] is False for x in stages)
    else:
        assert len(answer)==35015 and len(answer.splitlines())==641
        assert ev['full_final_body_read'] and ev['reviewed_character_ranges']==[[0,35015]]
        assert run['calls'][-1]['stage_id']=='solve' and run['calls'][-1]['finish_reason']=='length'
        assert run['calls'][-1]['output_tokens']==12000
        assert sums=={'spectrum':20,'dynamics':17,'pure_entanglement':4,'thermal_entanglement':0,'checks':6}
    graded.append({'run_id':rid,'score':total,'spent_microusd':spent,'run_sha256':run_sha,'answer_sha256':answer_sha})
assert cost==7014

# Public Pauli convention gives H(J=0,Delta=1,K=0)=diag(0,2,-2,0).
# Hence |01> only acquires a phase, transition probability is identically0,
# and the nonnegative-time set of maximizers has minimum0.
constant_H=[0,2,-2,0]
e01=[0,1,0,0]
assert [x*y for x,y in zip(constant_H,e01)]==[0,2,0,0]
# At J=Delta=0,K=1, H=diag(1,-1,-1,1), so evolution is exp(it)|01>.
zero_H=[1,-1,-1,1]
assert [x*y for x,y in zip(zero_H,e01)]==[0,-1,0,0]
controls=[
 {'id':'CP-UNGATED-CE-01','passed':True,'method':'Exact diagonal basis action and the least element of[0,infinity)',
  'H_diagonal':constant_H,'initial_basis_index':1,'eigenvalue':2,'transition_probability_all_times':0,'earliest_maximizer':0,
  'limit':'The all-time conclusion uses the diagonal exponential identity and the declared ordered time domain, not numerical time sampling.'},
 {'id':'CP-UNGATED-CE-02','passed':True,'method':'Exact diagonal basis action',
  'H_diagonal':zero_H,'initial_basis_index':1,'eigenvalue':-1,'state':'exp(it)|01>',
  'limit':'Shows the omitted zero-radius branch; does not refute the correct nonzero-radius formula.'},
]
md=(H/'evaluation.md').read_text(encoding='utf-8')
assert '**0/100**' in md and '**47/100**' in md and '7,014' in md
validation=read(H/'evaluation_validation.json')
assert validation['passed'] and validation['status']=='complete' and validation['pending_run_ids']==[]
validation.update({'independent_validation_passed':True,'graded_runs':graded,
    'criteria_checked':50,'exact_criterion_quote_ranges_checked':quotes,'total_spent_microusd':cost,
    'total_held_microusd':0,'bounded_independent_controls':controls,
    'artifacts':[{'path':str((H/name).relative_to(B.parent.parent)).replace(chr(92),'/'),'sha256':sha(H/name)} for name in
        ['reference_provenance.json','evaluation_tools.py','evaluation_ungated_assessments.py','criterion_assessments.json',
         'grades.json','criterion_evidence.json','evaluation.md','evaluation_validate.py']]})
(H/'evaluation_validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'scores':[0,47],'criteria':50,'exact_quote_ranges':quotes,'total_spent_microusd':cost,
    'hashes':{name:sha(H/name) for name in ['grades.json','criterion_evidence.json','evaluation.md','evaluation_validation.json']}}))
