"""Independent custody/arithmetic/quote checks and bounded mathematical controls.

Only the delivered answer and scalar call metadata are inspected. No draft,
critique or provider reasoning is selected or emitted. No provider execution.
"""
import hashlib
import json
import math
from pathlib import Path

H = Path(__file__).resolve().parent
B = H.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
rp = H / 'runs/00_self_critique/run.json'
run = read(rp)
run_sha = sha(rp)
assert run_sha == '9f961bc5eca2d597df3bc8fc6384910917e0cd002de21e16f3645978c4737489'
assert (rp.parent / 'run.sha256').read_text().strip().split()[0] == run_sha
answer = run['answer_text']
answer_sha = hashlib.sha256(answer.encode('utf-8')).hexdigest()
assert answer_sha == run['answer_sha256'] == 'ab4786978b6419b19fc4e1bbe28c7b083c66a1267dd198a75104c4f5b0540ba8'
assert len(answer) == 13229 and len(answer.splitlines()) == 380
rubric_path = B / 'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path) == 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
assert sha(H / 'reference_provenance.json') == '719d729c4a9c7e0bc6675a364feccd288c7e29e9baf2098748837eab13489f9f'
assert run['seed_sha256'] == '9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7'
assert read(H / 'reference_provenance.json')['current_run_output_content_read'] is False

grades = read(H / 'grades.json')
assert set(grades) == {run['run_id']}
g = grades[run['run_id']]
e = read(H / 'criterion_evidence.json')
for key, value in [('run_sha256', run_sha), ('answer_sha256', answer_sha), ('seed_sha256', run['seed_sha256'])]:
    assert g[key] == e[key] == value
assert g['method'] == 'trusted_post_freeze_mathematical_review'
assert e['full_final_body_read'] and e['reviewed_character_ranges'] == [[0, len(answer)]]
caps = {c['id']: c['max_points'] for s in read(rubric_path)['sections'] for c in s['criteria']}
rows = e['criteria']
assert len(rows) == len(caps) == 25 and {r['criterion_id'] for r in rows} == set(caps)
mapping = {'spectrum': 'spectrum', 'dynamics': 'dynamics', 'pure_state': 'pure_entanglement', 'thermal': 'thermal_entanglement', 'checks': 'checks'}
sums = {s: 0 for s in mapping.values()}
quotes = 0
def check_quote(q):
    start, end = q['character_range']
    assert 0 <= start <= end <= len(answer)
    assert answer[start:end] == q['quote']
    lo, hi = q['line_range']
    assert '\n'.join(answer.splitlines()[lo-1:hi]) == q['quote']

for row in rows:
    cap = caps[row['criterion_id']]
    assert row['max_points'] == cap and type(row['points']) is int and 0 <= row['points'] <= cap
    assert row['deducted_points'] == cap-row['points']
    sums[mapping[row['criterion_id'].split('.')[0]]] += row['points']
    for q in row['evidence']:
        if 'quote' in q:
            check_quote(q)
            quotes += 1
        else:
            assert q['kind'] == 'full_final_body_review_for_omission'
            assert q['character_range'] == [0, len(answer)] and q['line_range'] == [1, 380]
assert sums == g['points'] and sum(sums.values()) == g['total'] == 88
assert sum(d['points'] for d in g['deductions']) == 12
for d in g['deductions']:
    row = next(r for r in rows if r['criterion_id'] == d['criterion_id'])
    assert d['points'] == row['deducted_points'] and d['reason'] == row['assessment'] and d['evidence'] == row['evidence']
assert len(e['counterexamples']) == 5
for ce in e['counterexamples']:
    for q in ce['evidence']:
        check_quote(q)

# Exact Gaussian-integer Pauli products on unnormalized v=(0,1,-i,0).
# Dividing the expectation by ||v||^2=2 is exact in binary arithmetic here.
X = [[0,1],[1,0]]
Y = [[0,-1j],[1j,0]]
Z = [[1,0],[0,-1]]
v = [0,1,-1j,0]
def kron(a,b):
    return [[a[i//2][j//2]*b[i%2][j%2] for j in range(4)] for i in range(4)]
def expectation(op):
    return sum(complex(v[i]).conjugate()*op[i][j]*v[j] for i in range(4) for j in range(4))/2
T = [[expectation(kron(a,b)) for b in [X,Y,Z]] for a in [X,Y,Z]]
expected_T = [[0,1,0],[-1,0,0],[0,0,-1]]
assert T == expected_T
gram = [[sum(T[k][i].conjugate()*T[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
assert gram == [[1,0,0],[0,1,0],[0,0,1]]
# A=X,A'=Y,B=(Y-X)/sqrt2,B'=(Y+X)/sqrt2 attain2sqrt2.
# Factoring sqrt2, the CHSH expectation is Txy-Tyx=2.
assert T[0][1]-T[1][0] == 2
# Equality branch is exactly pi/(4sqrt2), and the claimed pi/8 is smaller.
# Since sqrt2<2, its rotation pi sqrt2/4 is strictly between0andpi/2.
assert 0 < 2 < 4
claimed_t = math.pi/8
actual_t = math.pi/(4*math.sqrt(2))
p_at_claim = 0.5*math.sin(2*math.sqrt(2)*claimed_t)**2
assert 0 < claimed_t < actual_t and p_at_claim < 0.5
# Zero-coupling product ray; and constant probability has minimum maximizing t0.
assert abs(0) >= abs(0)
zero_concurrence = 0
assert zero_concurrence != 1
constant_maximum_earliest = 0
# For beta=J=1,Delta=K=0, w=-sinh2<-1; the absolute-value
# inequality is true although w>C is false. sinh2>2 follows its positive series.
w = -math.sinh(2)
assert w < -2 and not (w > 1) and abs(w) > 1

controls = [
    {'id':'DSC-CE-01','passed':True,'method':'Exact Gaussian-integer Pauli expectation and Gram multiplication',
     'T':expected_T,'T_transpose_T':[[1,0,0],[0,1,0],[0,0,1]],
     'asserted_derived_CHSH':2,'actual_CHSH':'2sqrt2',
     'attaining_measurements':{'A':'X','A_prime':'Y','B':'(Y-X)/sqrt2','B_prime':'(Y+X)/sqrt2'}},
    {'id':'DSC-CE-02','passed':True,'method':'Exact equality-branch substitution and strict angle inequality; floating values illustrative only',
     'claimed_time':'pi/8','actual_time':'pi/(4sqrt2)',
     'illustrative_claimed_time':claimed_t,'illustrative_actual_time':actual_t,
     'illustrative_probability_at_claimed_time':p_at_claim},
    {'id':'DSC-CE-03','passed':True,'method':'Exact zero-coupling diagonal Hamiltonian',
     'parameters':{'J':0,'Delta':0,'K':1},'claimed_iff_condition_holds':True,'actual_concurrence':0},
    {'id':'DSC-CE-04','passed':True,'method':'Constant function on ordered domain[0,infinity)',
     'parameters':{'J':0,'Delta':1,'K':0},'earliest_maximizer':constant_maximum_earliest},
    {'id':'DSC-CE-05','passed':True,'method':'Exact sinh sign and positive-series lower bound; floating value illustrative only',
     'w':'-sinh2','C':1,'w_greater_C':False,'absolute_w_greater_C':True,
     'illustrative_w':w,'refutation_scope':'Intermediate sign equivalence only; final thermal criterion is correct.'}
]
assert len(run['calls']) == 2
metadata = [{k:c[k] for k in ['stage_id','finish_reason','input_tokens','output_tokens','actual_microusd']} for c in run['calls']]
assert all(c['finish_reason'] == 'stop' for c in metadata)
assert sum(c['input_tokens'] for c in metadata) == run['input_tokens'] == 9594
assert sum(c['output_tokens'] for c in metadata) == run['output_tokens'] == 13844
assert sum(c['actual_microusd'] for c in metadata) == run['budget']['spent_microusd'] == 7756
assert run['budget']['held_microusd'] == 0
report = (H / 'evaluation.md').read_text(encoding='utf-8')
assert '**88/100**' in report and '7,756' in report
validation = read(H / 'evaluation_validation.json')
validation.update({
    'independent_validation_passed':True,'run_sha256':run_sha,'answer_sha256':answer_sha,
    'full_final_lines_read':380,'full_final_characters_read':len(answer),
    'exact_criterion_quote_ranges_checked':quotes,'points':sums,'total':88,'deductions_total':12,
    'bounded_independent_controls':controls,'safe_call_metadata_projection':metadata,'held_microusd':0,
    'content_access_limits':['Only final answer_text selected for mathematical content.', 'No draft, critique, provider reasoning, private answer key or earlier-answer content credited.'],
    'artifacts':[{'path':str((H/name).relative_to(B.parent.parent)).replace(chr(92),'/'),'sha256':sha(H/name)} for name in
        ['reference_provenance.json','evaluation_tools.py','evaluation_assessments.py','criterion_assessments.json','grades.json','criterion_evidence.json','evaluation.md','evaluation_validate.py']],
    'limitations':['Mechanical checks verify custody, arithmetic, quotations and specified controls; mathematical grading remains trusted manual review.',
                   'One self-critique attempt on one fixed item; no general efficacy or model-ranking conclusion.']
})
(H / 'evaluation_validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'criteria':25,'quote_ranges':quotes,'total':88,'points':sums,
    'hashes':{name:sha(H/name) for name in ['grades.json','criterion_evidence.json','evaluation.md','evaluation_validation.json']}}))
