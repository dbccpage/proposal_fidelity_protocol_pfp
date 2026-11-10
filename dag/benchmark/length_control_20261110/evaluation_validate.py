"""Independent mechanical custody/arithmetic checks for the manual evaluation.

These checks validate bindings and bounded counterexamples, not the completeness
of the mathematical grading judgment. Only answer_text and non-content call
metadata are examined; nested provider evidence is not expanded.
"""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


run_path = HERE / 'runs/00_direct/run.json'
run = read(run_path)
run_sha = sha(run_path)
assert run_sha == 'ac77cbf6a6486715ce146b8c4568742dc673b0430051d1cb0ad6b4e7cb5d748b'
assert (run_path.parent / 'run.sha256').read_text().strip().split()[0] == run_sha
answer = run['answer_text']
answer_sha = hashlib.sha256(answer.encode('utf-8')).hexdigest()
assert answer_sha == run['answer_sha256'] == '2a69e0b747904235b40a098b1e7c3cf06c4151dc16f84ab8d467c8d05a46e4e1'
rubric_path = BENCH / 'pilot_20261110/evaluator_rubric.json'
assert sha(rubric_path) == 'eaeffe10123292bda1385fcf444ae0a1b75e919f40ce09391cf1be49edcdf9dc'
assert sha(HERE / 'reference_provenance.json') == '7a74b3dc3769e562d1195b1965f8d82f3b3a141f1bbfe9eddd1b519d10536959'
assert run['seed_sha256'] == '9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7'

rubric = read(rubric_path)
grades = read(HERE / 'grades.json')
assert set(grades) == {run['run_id']}
grade = grades[run['run_id']]
evidence = read(HERE / 'criterion_evidence.json')
assert grade['run_sha256'] == evidence['run_sha256'] == run_sha
assert grade['answer_sha256'] == evidence['answer_sha256'] == answer_sha
assert grade['seed_sha256'] == evidence['seed_sha256'] == run['seed_sha256']
assert grade['method'] == 'trusted_post_freeze_mathematical_review'
assert evidence['full_final_body_read'] is True
assert evidence['reviewed_character_ranges'] == [[0, len(answer)]]
expected = {c['id']: c['max_points'] for s in rubric['sections'] for c in s['criteria']}
actual = evidence['criteria']
assert len(actual) == len(expected) == 25
assert len(set(r['criterion_id'] for r in actual)) == 25
assert set(r['criterion_id'] for r in actual) == set(expected)
section_map = {'spectrum': 'spectrum', 'dynamics': 'dynamics',
               'pure_state': 'pure_entanglement', 'thermal': 'thermal_entanglement',
               'checks': 'checks'}
sums = {s: 0 for s in section_map.values()}
quote_count = 0
for row in actual:
    maximum = expected[row['criterion_id']]
    assert row['max_points'] == maximum
    assert type(row['points']) is int and 0 <= row['points'] <= maximum
    assert row['deducted_points'] == maximum - row['points']
    sums[section_map[row['criterion_id'].split('.')[0]]] += row['points']
    for e in row['evidence']:
        start, end = e['character_range']
        assert 0 <= start <= end <= len(answer)
        if 'quote' in e:
            assert answer[start:end] == e['quote']
            lo, hi = e['line_range']
            assert '\n'.join(answer.splitlines()[lo - 1:hi]) == e['quote']
            quote_count += 1
        else:
            assert e['kind'] == 'full_final_body_review_for_omission'
            assert [start, end] == [0, len(answer)]
assert sums == grade['points']
assert sum(sums.values()) == grade['total'] == 62
assert sum(d['points'] for d in grade['deductions']) == 38
for deduction in grade['deductions']:
    row = next(r for r in actual if r['criterion_id'] == deduction['criterion_id'])
    assert deduction['points'] == row['deducted_points']
    assert deduction['reason'] == row['assessment']
    assert deduction['evidence'] == row['evidence']

# Exact integer/Fraction controls, independent of a provider or native verifier.
h = ((0, -2), (-2, 0))
v = (1, 1)
hv = [sum(h[i][j] * v[j] for j in range(2)) for i in range(2)]
assert hv == [-2, -2] and hv != [2, 2]
assert Fraction(0 ** 2, 0 ** 2 + 1 ** 2) == 0
assert Fraction(1, 2) * Fraction(1, 2) == Fraction(1, 4)
controls = [
    {'id': 'LC-CE-01', 'passed': True, 'method': 'Exact 2x2 integer multiplication',
     'result': 'At J=-1,Delta=K=0, H(1,1)=(-2,-2), not +2(1,1); the stipulated angle cannot exist.'},
    {'id': 'LC-CE-02', 'passed': True, 'method': 'Exact zero prefactor and order of nonnegative time domain',
     'result': 'J=0,Delta=1 gives constant zero probability; earliest maximizer is 0.'},
    {'id': 'LC-CE-03', 'passed': True, 'method': 'Exact squared-modulus product',
     'result': 'For alpha=1/sqrt(2),beta=i/sqrt(2), both squared products are 1/4; phase does not invalidate modulus multiplicativity.'},
]
for ce in evidence['counterexamples']:
    for e in ce['evidence']:
        start, end = e['character_range']
        assert answer[start:end] == e['quote']

assert len(run['calls']) == 1
call_metadata = {k: run['calls'][0][k] for k in
                 ('stage_id', 'finish_reason', 'input_tokens', 'output_tokens', 'actual_microusd')}
assert call_metadata['finish_reason'] == 'stop'
assert run['output_tokens'] == call_metadata['output_tokens'] == 11241
assert run['budget']['spent_microusd'] == call_metadata['actual_microusd'] == 6222
assert run['budget']['held_microusd'] == 0
report = (HERE / 'evaluation.md').read_text(encoding='utf-8')
assert '**62/100**' in report and '11,241' in report and '6,222' in report
validation = read(HERE / 'evaluation_validation.json')
validation.update({
    'independent_validation_passed': True,
    'run_sha256': run_sha, 'answer_sha256': answer_sha,
    'full_final_lines_read': len(answer.splitlines()), 'full_final_characters_read': len(answer),
    'exact_criterion_quote_ranges_checked': quote_count,
    'points': sums, 'total': 62, 'deductions_total': 38,
    'bounded_independent_controls': controls,
    'safe_call_metadata_projection': call_metadata,
    'held_microusd': 0,
    'artifacts': [{'path': str((HERE / name).relative_to(BENCH.parent.parent)).replace('\\', '/'),
                   'sha256': sha(HERE / name)} for name in
                  ['reference_provenance.json', 'evaluation_tools.py',
                   'evaluation_assessments.py', 'criterion_assessments.json',
                   'grades.json', 'criterion_evidence.json', 'evaluation.md',
                   'evaluation_validate.py']],
    'limitations': ['Mechanical validation checks custody, arithmetic, quotations and the specified finite controls; the criterion judgments are a trusted manual mathematical review.',
                   'One final answer on one fixed item; no universal accuracy or ranking conclusion.']})
(HERE / 'evaluation_validation.json').write_text(
    json.dumps(validation, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'passed': True, 'criteria': 25, 'quote_ranges': quote_count,
                  'total': grade['total'], 'points': sums,
                  'hashes': {name: sha(HERE / name) for name in
                             ['grades.json', 'criterion_evidence.json', 'evaluation.md',
                              'evaluation_validation.json']}}))
