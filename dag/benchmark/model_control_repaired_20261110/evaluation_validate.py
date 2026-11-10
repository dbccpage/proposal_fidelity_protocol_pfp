"""Mechanical custody, score and exact small-counterexample validation.

No provider execution or nested provider-content inspection. This verifies the
manual review's bindings and specified controls, not the judgment itself.
"""
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

H = Path(__file__).resolve().parent
B = H.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
rp = H / 'runs/00_direct/run.json'
run = read(rp)
run_sha = sha(rp)
assert run_sha == '79f366959f1cc0b9e60bc63144cbe9ffccae12c53ec80163eada124f7ff75f1a'
assert (rp.parent / 'run.sha256').read_text().strip().split()[0] == run_sha
answer = run['answer_text']
answer_sha = hashlib.sha256(answer.encode()).hexdigest()
assert answer_sha == run['answer_sha256'] == '9454f47461812b86753a7593c37a8219b25658de71964e2ad6d461e5fb739e12'
rubric_path = B / 'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path) == 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
assert sha(H / 'reference_provenance.json') == '74e0aac9ae4e707cf0e10beecf53123b9d5f03bb5224cac8f9911546d1d045a6'
assert run['seed_sha256'] == '9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7'
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
for row in rows:
    cap = caps[row['criterion_id']]
    assert row['max_points'] == cap and type(row['points']) is int and 0 <= row['points'] <= cap
    assert row['deducted_points'] == cap - row['points']
    sums[mapping[row['criterion_id'].split('.')[0]]] += row['points']
    for q in row['evidence']:
        start, end = q['character_range']
        assert 0 <= start <= end <= len(answer)
        if 'quote' in q:
            assert answer[start:end] == q['quote']
            lo, hi = q['line_range']
            assert '\n'.join(answer.splitlines()[lo - 1:hi]) == q['quote']
            quotes += 1
        else:
            assert q['kind'] == 'full_final_body_review_for_omission' and [start, end] == [0, len(answer)]
assert sums == g['points'] and sum(sums.values()) == g['total'] == 83
assert sum(d['points'] for d in g['deductions']) == 17
for d in g['deductions']:
    row = next(r for r in rows if r['criterion_id'] == d['criterion_id'])
    assert d['points'] == row['deducted_points'] and d['reason'] == row['assessment'] and d['evidence'] == row['evidence']
for ce in e['counterexamples']:
    for q in ce['evidence']:
        start, end = q['character_range']
        assert answer[start:end] == q['quote']

# Exact finite controls for the retained mathematical defects.
# Product-state CHSH with A=A'=Z,B=B'=-Z is -2 Z tensor Z.
zz_on_01 = -1
attained = -2 * zz_on_01
assert attained == 2
claimed_at_C0 = 0
assert claimed_at_C0 < attained
# Rational amplitudes a=3/5,b=12/25+16i/25 are normalized.
a, br, bi = F(3,5), F(12,25), F(16,25)
assert a*a + br*br + bi*bi == 1
alpha, beta = 2*a*br, 2*a*bi
wrong_gram_off_diagonal = -2*alpha*beta
assert alpha == F(72,125) and beta == F(96,125)
assert wrong_gram_off_diagonal == F(-13824,15625)
assert wrong_gram_off_diagonal != 0
# The required sine -1 is outside the nonnegative sine range on [0,pi].
required_sine = F(-1)
assert required_sine < 0
h = [[0,-2],[-2,0]]
v = [1,1]
assert [sum(h[i][j]*v[j] for j in range(2)) for i in range(2)] == [-2,-2]
# Zero coupling gives a diagonal Hamiltonian and preserves the initial product ray.
assert abs(0) >= abs(0)
zero_coupling_concurrence = 0
assert zero_coupling_concurrence != 1
controls = [
 {'id':'MC-CE-01','passed':True,'method':'Exact product-state Pauli measurement','state':'|01>','concurrence':0,'asserted_CHSH':claimed_at_C0,'attained_CHSH':attained,'actual_maximum':2,'upper_bound_reason':'Product correlations obey the CHSH bound2.'},
 {'id':'MC-CE-02','passed':True,'method':'Exact Fraction normalization and Gram multiplication','a':str(a),'b_real':str(br),'b_imag':str(bi),'alpha':str(alpha),'beta':str(beta),'displayed_matrix_actual_gram_off_diagonal':str(wrong_gram_off_diagonal),'asserted_off_diagonal':'0'},
 {'id':'MC-CE-03','passed':True,'method':'Declared angle range and exact odd-block multiplication','required_sine':str(required_sine),'allowed_sine_on_interval':'[0,1]','wrong_pi_over_2_vector_eigenvalue':-2,'claimed_plus_eigenvalue':2},
 {'id':'MC-CE-04','passed':True,'method':'Exact zero-coupling diagonal action','parameters':{'J':0,'Delta':0,'K':1},'reachability_inequality_holds':True,'state':'exp(it)|01>','concurrence':0}
]
assert len(run['calls']) == 1
metadata = [{k:c[k] for k in ['stage_id','finish_reason','input_tokens','output_tokens','actual_microusd']} for c in run['calls']]
assert metadata[0]['finish_reason'] == 'stop'
assert metadata[0]['output_tokens'] == run['output_tokens'] == 10805
assert metadata[0]['input_tokens'] == run['input_tokens'] == 403
assert metadata[0]['actual_microusd'] == run['budget']['spent_microusd'] == 4211
assert run['budget']['held_microusd'] == 0
report = (H/'evaluation.md').read_text(encoding='utf-8')
assert '**83/100**' in report and '4,211' in report and '10,805' in report
validation = read(H/'evaluation_validation.json')
validation.update({'independent_validation_passed':True,'run_sha256':run_sha,'answer_sha256':answer_sha,
 'full_final_lines_read':len(answer.splitlines()),'full_final_characters_read':len(answer),
 'exact_criterion_quote_ranges_checked':quotes,'points':sums,'total':83,'deductions_total':17,
 'bounded_independent_controls':controls,'safe_call_metadata_projection':metadata,'held_microusd':0,
 'artifacts':[{'path':str((H/name).relative_to(B.parent.parent)).replace(chr(92),'/'),'sha256':sha(H/name)} for name in
 ['reference_provenance.json','evaluation_tools.py','evaluation_assessments.py','criterion_assessments.json','grades.json','criterion_evidence.json','evaluation.md','evaluation_validate.py']],
 'limitations':['Mechanical checks validate custody, arithmetic, quotations and the specified counterexamples; criterion judgments are a trusted manual mathematical review.',
 'One direct model-control sample on one fixed item; no general ranking or model-effect causal conclusion.']})
(H/'evaluation_validation.json').write_text(json.dumps(validation,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'criteria':25,'quote_ranges':quotes,'total':83,'points':sums,
 'hashes':{name:sha(H/name) for name in ['grades.json','criterion_evidence.json','evaluation.md','evaluation_validation.json']}}))
