"""Integrate source-pinned completed slices and the bounded benchmark adapter."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / 'dag'
REV = DAG / 'reviews'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


completed = [
    ('additional_rust_functional_certifiers.json', 64, 64, 'Rust_functional_certifiers_complete_64',
     '64 full source bodies;31002 lines;11 conditional claims;19 findings;7 scoped validation entries',
     'dag/reviews/additional_rust_functional_certifiers_final_validation.json'),
    ('additional_paper_007_support.json', 57, 46, 'Paper007_support_dispositions_complete',
     '57 assigned paths:46 full bodies and11 bounded artifacts;44 PDF pages and56 ZIP members assessed;4 claims;7 findings',
     'dag/reviews/additional_paper_007_final_validation.json'),
    ('additional_paper_008_support.json', 74, 55, 'Paper008_support_dispositions_complete',
     '74 assigned paths:55 full bodies and19 bounded artifacts;48 PDF pages and73 ZIP members assessed;6 claims;8 findings',
     'dag/reviews/additional_paper_008_support_final_validation.json'),
    ('additional_challenges_051_059.json', 102, 102, 'C051_C059_complete_assigned_corpus',
     '1240 newly scoped paths:102 full source bodies and1138 bounded parsed-data dispositions;36 findings;9 conditional claims',
     'dag/reviews/additional_challenges_051_059_reconciliation.json'),
]
swarm = read(DAG / 'swarm_manifest.json')
validation = read(DAG / 'validation.json')
for filename, count, full, name, result, receipt in completed:
    report = read(REV / filename)
    assert len(report['file_reviews']) == count
    assert sum(bool(row.get('full_source_read')) for row in report['file_reviews']) == full
    for row in report['file_reviews']:
        assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
    report_path = 'dag/reviews/' + filename
    if report_path not in swarm['completed_followup_slices']:
        swarm['completed_followup_slices'].append(report_path)
    item = {'name': name, 'result': result, 'receipt': receipt,
            'limit': 'Only the explicitly marked source bodies receive full-reading credit; finite checks and bounded artifact dispositions do not prove the whole program.'}
    validation['checks'] = [r for r in validation['checks'] if r['name'] != name] + [item]
for row in swarm['active_audit_slices']:
    if row['agent'] == 'audit_challenges_041_050':
        row.update(scope='293 pending original pfp/infrastructure/adapters paths', status='in_progress',
                   scope_manifest='dag/reviews/additional_pfp_adapters_scope.json')
    elif row['agent'] == 'audit_imported_pilots':
        row.update(scope='Pending Paper009 supporting paths', status='freezing_scope',
                   scope_manifest='dag/reviews/additional_paper_009_support_scope.json')
    elif row['agent'] == 'audit_systems':
        row.update(scope='Pending original code/rust/core_quantum_physics source slice',
                   status='in_progress', scope_manifest='dag/reviews/additional_rust_quantum_physics_scope.json',
                   completed_scope_manifest='dag/reviews/additional_rust_functional_certifiers_scope.json')
        row.pop('next_task', None)
swarm['parent_active_slice'] = {
    'scope': 'Bounded rational-counterexample workflow adaptation and ablations',
    'status': 'bounded_adapter_complete_independent_review_repaired_and_verified',
    'implementation': 'dag/benchmark/rational_panel.py',
    'documentation': 'dag/benchmark/RATIONAL_PANEL.md',
    'previous_completed_report': 'dag/reviews/additional_paper_005_support.json',
    'scope_limit': 'Three runnable plans do not implement the full research registry or its composition grammar. No paid calls or private answer access.',
}
panel_validation = read(DAG / 'benchmark/rational_panel_validation.json')
assert panel_validation['status'] == 'passed' and panel_validation['external_provider_requests'] == 0
for filename, expected in panel_validation['source_sha256'].items():
    assert hashlib.sha256((DAG / 'benchmark' / filename).read_bytes()).hexdigest() == expected, filename
check_name = 'bounded_rational_panel_adapter_synthetic_validation'
validation['checks'] = [row for row in validation['checks'] if row['name'] != check_name] + [{
    'name': check_name, 'result': 'passed_no_external_requests', 'passed': panel_validation['passed'],
    'receipt': 'dag/benchmark/rational_panel_validation.json',
    'limit': 'Bounded rational-substitution adaptation only; exact witnesses concern model encodings, not semantic correctness of the entire QM solution. Independent review checkpoint is separate.',
}]
review = read(DAG / 'benchmark/rational_panel_review.json')
review_validation = read(DAG / 'benchmark/rational_panel_review_final_validation.json')
assert review['status'] == 'complete_bounded_review_all_findings_repaired'
assert review_validation['status'] == 'passed'
assert hashlib.sha256((DAG / 'benchmark/rational_panel_review.json').read_bytes()).hexdigest() == review_validation['report_sha256']
for row in review['file_reviews']:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
check_name = 'bounded_rational_panel_independent_review'
validation['checks'] = [row for row in validation['checks'] if row['name'] != check_name] + [{
    'name': check_name, 'result': 'five_findings_repaired_and_independently_reproduced',
    'independent_tests_passed': review_validation['independent_final_tests'],
    'receipt': 'dag/benchmark/rational_panel_review_final_validation.json',
    'limit': 'Eleven full implementation/test reads and one partial helper-test read. Independent80-test subset and parent119-test suite overlap; do not add them. Fabricated task with actual-seed and socket access denied.',
}]
swarm['completed_benchmark_review'] = 'dag/benchmark/rational_panel_review.json'
write(DAG / 'swarm_manifest.json', swarm)
write(DAG / 'validation.json', validation)
progress = DAG / 'PROGRESS.md'
marker = b'Completed Paper007 support dispositions and C051-C059 source review'
if marker not in progress.read_bytes():
    with progress.open('a', encoding='utf-8') as stream:
        stream.write('\nCompleted Paper007 support dispositions and C051-C059 source review: '
                     '46 and102 new full bodies respectively, with11 and1138 bounded artifact dispositions retained separately. '
                     'Paper007 reports seven findings, including inconsistent historical Lean provenance; '
                     'C051-C059 reports36 findings, including a concrete C058 false acceptance shared by both sampled judges. '
                     'The support agent now reviews Paper008; the challenge agent now reviews293 pending Python adapter paths. '
                     'Parent implemented a rational-substitution-only R05-I02 adaptation with blind, visible and fixed-panel plans. '
                     'Synthetic checks cover exact witnesses, partial domains, malformed artifacts, visibility and shared cost accounting. '
                     'Accuracy and empirical workflow benefits remain unmeasured; other research adapters and the broader every-file audit remain incomplete.\n')
marker = b'Completed the bounded rational-panel adapter and independent repair review'
if marker not in progress.read_bytes():
    with progress.open('a', encoding='utf-8') as stream:
        stream.write('\nCompleted the bounded rational-panel adapter and independent repair review: three registered executable plans, '
                     '119 passing parent tests and an overlapping80-test independent subset. Five review findings were fixed and re-probed: '
                     'invalid-Unicode answer extraction, hashing before input validation, missing execution source pins, '
                     'provider-metadata receipt loss and unchecked stale/negative-cost summary input. '
                     'Original failure probes remain preserved. All model/campaign tests used synthetic transport; no real charges or private answer access. '
                     'The completed64-file Rust functional/certifier review adds11 conditional claims and19 findings. '
                     'The systems agent now reviews203 quantum-physics source files. Both evidence graphs validate as acyclic, '
                     'but repository-wide source coverage and empirical workflow comparisons remain incomplete.\n')
if b'Completed the74-path Paper008 support slice' not in progress.read_bytes():
    with progress.open('a', encoding='utf-8') as stream:
        stream.write('\nCompleted the74-path Paper008 support slice:55 full bodies,19 bounded artifacts,48 PDF pages and73 ZIP members. '
                     'Six conditional claims and eight findings distinguish exact finite graph/forward-difference mathematics '
                     'from unsupported categorical or learning labels. Current runner34 and mocked gates7 pass; current examples10 pass/1 custody failure; '
                     'exact archive examples11 pass. Current verifier has31 custody issues; archive manifests pass. '
                     'Original bytes and historical receipts remain unchanged. Paper009 support is the next delegated slice.\n')
print(json.dumps({'integrated': [row[0] for row in completed], 'parent': swarm['parent_active_slice']['status']}))
