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
rp = H / 'runs/00_sections/run.json'
run = read(rp)
run_sha = sha(rp)
assert run_sha == '2485687210cbc5b5a68ed078659ada960ad263a5a62fd6f70e42292098cfce8c'
assert (rp.parent / 'run.sha256').read_text().strip().split()[0] == run_sha
answer = run['answer_text']
answer_sha = hashlib.sha256(answer.encode()).hexdigest()
assert answer_sha == run['answer_sha256'] == 'd176dd483a23c8bff6c580929de3609146ab1941a36eb6e6f837e6910dbd8ed5'
rubric_path = B / 'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path) == 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
assert sha(H / 'reference_provenance.json') == 'c30b87a99adb31e1676b85b329af642c12b19e2750287d6ec20d3bcce7e17f60'
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
assert sums == g['points'] and sum(sums.values()) == g['total'] == 26
assert sum(d['points'] for d in g['deductions']) == 74
for d in g['deductions']:
    row = next(r for r in rows if r['criterion_id'] == d['criterion_id'])
    assert d['points'] == row['deducted_points'] and d['reason'] == row['assessment'] and d['evidence'] == row['evidence']
for ce in e['counterexamples']:
    for q in ce['evidence']:
        start, end = q['character_range']
        assert answer[start:end] == q['quote']

# Integer/imaginary-integer tensor entries are exactly represented here.
I = [[1, 0], [0, 1]]
X = [[0, 1], [1, 0]]
Y = [[0, -1j], [1j, 0]]
Z = [[1, 0], [0, -1]]
def kron(a, b):
    return [[a[i // 2][j // 2] * b[i % 2][j % 2] for j in range(4)] for i in range(4)]
xx, yy, zi, iz, zz = [kron(a, b) for a, b in [(X, X), (Y, Y), (Z, I), (I, Z), (Z, Z)]]
def h(j, d, k):
    return [[int((j * (xx[a][b] + yy[a][b]) + d * (zi[a][b] - iz[a][b]) + k * zz[a][b]).real) for b in range(4)] for a in range(4)]
h0, h1 = h(1, 0, 0), h(1, 1, 0)
assert h0 == [[0, 0, 0, 0], [0, 0, 2, 0], [0, 2, 0, 0], [0, 0, 0, 0]]
assert [[h1[a][b] for b in [1, 2]] for a in [1, 2]] == [[2, 2], [2, -2]]
actual_det = F(1, 2) ** 2
asserted_det = F(1, 2) ** 2 - F(1, 2) ** 2
assert actual_det == F(1, 4) and asserted_det == 0
sin_squared_pi_multiple = {F(0): F(0), F(1, 2): F(1), F(1): F(0)}
true_p = F(1, 2) * sin_squared_pi_multiple[F(1)]
claimed_p = F(1, 2) * sin_squared_pi_multiple[F(1, 2)]
assert true_p == 0 and claimed_p == F(1, 2)
controls = [
    {'id': 'SC-CE-01', 'passed': True, 'method': 'Independent exact Pauli tensor products', 'hamiltonian_J1_Delta0_K0': h0, 'true_thermal_trace': '2+2cosh(2beta)', 'asserted_thermal_trace': '4cosh(2beta)', 'strict_difference_for_beta_positive': '2(cosh(2beta)-1)>0'},
    {'id': 'SC-CE-02', 'passed': True, 'method': 'Exact rational determinant and orthogonal second-spin trace', 'actual_reduced_determinant': str(actual_det), 'asserted_reduced_determinant': str(asserted_det)},
    {'id': 'SC-CE-03', 'passed': True, 'method': 'Exact sine values at integer/half-integer multiples of pi', 'actual_probability': str(true_p), 'asserted_probability': str(claimed_p)},
    {'id': 'SC-CE-04', 'passed': True, 'method': 'Independent exact Pauli tensor products', 'hamiltonian_J1_Delta1_K0': h1, 'actual_transition_supremum': '1/2', 'part3_transition_supremum': '1'},
]
assert len(run['calls']) == 5
metadata = [{k: c[k] for k in ['stage_id', 'finish_reason', 'input_tokens', 'output_tokens', 'actual_microusd']} for c in run['calls']]
assert all(c['finish_reason'] == 'length' and c['output_tokens'] == 3200 for c in metadata)
assert sum(c['output_tokens'] for c in metadata) == run['output_tokens'] == 16000
assert sum(c['actual_microusd'] for c in metadata) == run['budget']['spent_microusd'] == 9065
assert run['budget']['held_microusd'] == 0
report = (H / 'evaluation.md').read_text(encoding='utf-8')
assert '**26/100**' in report and '9,065' in report and '16,000' in report
v = read(H / 'evaluation_validation.json')
v.update({'independent_validation_passed': True, 'run_sha256': run_sha, 'answer_sha256': answer_sha,
          'full_final_lines_read': len(answer.splitlines()), 'full_final_characters_read': len(answer),
          'exact_criterion_quote_ranges_checked': quotes, 'points': sums, 'total': 26, 'deductions_total': 74,
          'bounded_independent_controls': controls, 'safe_call_metadata_projection': metadata, 'held_microusd': 0,
          'artifacts': [{'path': str((H / name).relative_to(B.parent.parent)).replace('\\', '/'), 'sha256': sha(H / name)} for name in
                        ['reference_provenance.json', 'evaluation_tools.py', 'evaluation_assessments.py', 'criterion_assessments.json', 'grades.json', 'criterion_evidence.json', 'evaluation.md', 'evaluation_validate.py']],
          'limitations': ['Mechanical checks validate custody, arithmetic, quotations and the specified counterexamples; criterion judgments remain a trusted manual mathematical review.', 'One section-control attempt on one fixed item; no general ranking conclusion.']})
(H / 'evaluation_validation.json').write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'passed': True, 'criteria': 25, 'quote_ranges': quotes, 'total': 26, 'points': sums,
                  'hashes': {name: sha(H / name) for name in ['grades.json', 'criterion_evidence.json', 'evaluation.md', 'evaluation_validation.json']}}))
