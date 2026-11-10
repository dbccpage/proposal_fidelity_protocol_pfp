"""Add bounded artifact dispositions to completed source-body readings."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
target = REV / 'additional_governance_remaining.json'
report = json.loads(target.read_text())
scope = json.loads((REV / 'additional_governance_remaining_scope.json').read_text())
checks = json.loads((REV / 'additional_governance_artifact_checks.json').read_text())
assert checks['summary']['files'] == 50
assert checks['summary']['declared_arithmetic_or_structure_issues'] == 0
assert checks['summary']['binding_population'] == {'raw_match': 39633, 'lf_normalized_match_only': 23776, 'different_current_bytes': 1407, 'absent': 18507}
current_bindings = [b for r in checks['files'] if r['kind'] == 'contract_and_policy_grade_declaration'
                    for b in r['bindings'] if not b['locator'].startswith('$.history')]
assert all(b['status'] == 'raw_match' for b in current_bindings)
run_log_bindings = [b for r in checks['files'] if r['kind'] == 'historical_command_record'
                    for b in r['bindings'] if b['locator'] == '$.report']
assert len(run_log_bindings) == 19
assert sum(b['status'] == 'raw_match' for b in run_log_bindings) == 17
assert sum(b['status'] == 'absent' for b in run_log_bindings) == 2
frozen = {r['path']: r for r in scope['files']}
rows = {r['path']: r for r in report['file_reviews'] if r.get('full_source_read')}
assert len(rows) == 32
for result in checks['files']:
    path = result['path']
    if path in rows:
        rows[path]['artifact_predicates'] = 'dag/reviews/additional_governance_artifact_checks.json'
        continue
    kind = result['kind']
    detail = ''
    if 'mutant_count' in result:
        detail = f"All {result['mutant_count']} outcome rows counted: {result['counts']}; ratio {result['ratio']}. "
    elif 'input_count' in result:
        detail = f"All {result['input_count']} input bindings compared; recorded duration {result['reported_elapsed_seconds']} seconds. "
    elif 'entry_count' in result:
        detail = f"All {result['entry_count']} exemption bindings and the complete reason-string population compared. "
    elif 'score_summaries' in result:
        detail = f"Current score {result['score_summaries'][0]['token']}; arithmetic checked for {len(result['score_summaries'])} current/history records. "
    rows[path] = {'path': path, 'sha256': result['sha256'], 'full_source_read': False,
                  'reviewed_lines': [], 'review_level': 'bounded_whole_population_schema_arithmetic_and_custody_assessment',
                  'detail_receipt': 'dag/reviews/additional_governance_artifact_checks.json',
                  'assessment': f"{kind}: {detail}No strict-JSON or selected arithmetic/structure predicate failures. Binding outcomes: {result['binding_status_counts']}. " + ' '.join(result['checks']) + ' This is not a full prose/record-by-record semantic reading or a replay of the historical command.'}
assert set(rows) == set(frozen)
for path, row in rows.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row['sha256'] == frozen[path]['sha256']


def ev(path):
    return {'path': path, 'sha256': frozen[path]['sha256']}


report['claims'] = [c for c in report['claims'] if c['id'] == 'GOV-C01'] + [
    {'id': 'GOV-C02', 'statement': 'All 50 JSON artifacts parse without duplicate keys or nonfinite constants. Selected grade, metric-band and mutation-accounting predicates agree. This establishes internal arithmetic consistency of declarations, not program correctness, empirical efficacy or unrestricted mutation equivalence.',
     'evidence': [ev('governance/tools/metrics.py'), ev('governance/evidence/metrics.json'), ev('governance/evidence/equivalents.json')],
     'validation': 'dag/reviews/additional_governance_artifact_checks.json'},
    {'id': 'GOV-C03', 'statement': 'The 12 mutation receipts contain 1194 declared outcomes: 1074 killed, 22 survived, 37 declared equivalent, 58 invalid and 3 inconclusive. Each report and its per-file totals/ratio reconcile. These are heterogeneous historical populations; they are not pooled into a probability of correctness, and the Python cache counterexample does not establish that any particular retained campaign was affected.',
     'evidence': [ev('governance/evidence/m-gov-mutation.mutation.json'), ev('governance/evidence/m-pfp-cli.mutation.json')],
     'validation': 'dag/reviews/additional_governance_artifact_checks.json'},
    {'id': 'GOV-C04', 'statement': 'The historical baseline is an exemption policy over 9247 paths, not a certification list. Current comparison gives 5872 raw matches, 2596 LF-normalization-only matches, 66 different contents and 713 absent paths. Historical/current movement or drift must be resolved by versioned provenance; none of these categories alone establishes that a past test failed.',
     'evidence': [ev('governance/baseline.json')], 'validation': 'dag/reviews/additional_governance_artifact_checks.json'},
    {'id': 'GOV-C05', 'statement': 'All current top-level contract/score source and evidence bindings match raw current bytes; differences in these files belong to historical versions. Seventeen run-record log bindings match and two named workflow-round/fix logs are absent from the current inventory. All 83323 binding occurrences were compared, with 39633 raw matches, 23776 LF-only matches, 1407 different bytes and 18507 absent targets across repeated snapshots. These repeated occurrences are not independent experiments or authenticated history.',
     'evidence': [ev('governance/tools/metrics.contract.score.json'), ev('governance/evidence/workflow-live-round-tests.run.json'), ev('governance/evidence/workflow-review-fixes-tests.run.json')],
     'validation': 'dag/reviews/additional_governance_artifact_checks.json'},
]
report.update(status='complete_frozen_slice_dispositions', file_reviews=sorted(rows.values(), key=lambda r:r['path']),
              pending_paths=[], body_read_count=32, bounded_assessment_count=44,
              full_body_review_complete=False,
              validation=['dag/reviews/additional_governance_remaining_probes.json', 'dag/reviews/additional_governance_artifact_checks.json'])
report['limits'] = ['32 full source/log/small-JSON readings; 44 explicit bounded artifact dispositions. No silent promotion of selected predicates to full-body reading.',
                   'The two reproduced implementation findings are isolated owner-function/method controls, not historical campaign reproductions.',
                   'No original source edits, real governed mutation campaigns, provider calls, native builds, external-path reads or private benchmark access.']
target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
summary = '''# Governance review

All 76 frozen files have explicit dispositions: **32 full body reads and 44 bounded artifact assessments**. The nine source/test bodies, seventeen logs and six small JSON files were read completely. Large historical manifests and receipts receive population checks with their limits stated per file.

Two concrete implementation defects were reproduced on isolated synthetic inputs:

- C# unbraced conditionals defeat the metric's claimed conservative nesting bound: four nested conditionals report 0.
- A mutation campaign's shared bytecode cache can reuse the first equal-size mutant within one timestamp second. The second mutant is reported killed although a fresh cache lets it survive.

All 50 JSON artifacts pass strict parsing and the selected arithmetic/structure checks. Twelve mutation receipts reconcile 1194 declared outcomes; this is accounting evidence over separate historical populations, not a correctness probability. Thirty-seven equivalence exclusions depend on their stated observation/caller assumptions.

The 9247-path baseline records grandfathering policy. Current raw-byte matching, LF-only matching, content drift and absent targets remain separate. Seventeen run logs match their records; two named historical workflow logs are absent. Current contract/score evidence bindings match raw bytes, while older score versions retain different historical references. Hash consistency cannot authenticate execution or establish historical failure from current drift.

See `additional_governance_remaining.json` for source pins, findings and per-file limits; `additional_governance_artifact_checks.json` retains every checked binding. No original sources or historical evidence were rewritten, and no model/provider/native campaign was run.
'''
(REV / 'additional_governance_remaining.md').write_text(summary, encoding='utf-8')
validation = {'status': 'PASS', 'meaning': 'Disposition/source-pin integrity, not semantic correctness of the reviewed programs.',
              'scope_files': len(frozen), 'full_body_reads': 32, 'bounded_dispositions': 44, 'pending_dispositions': 0,
              'claims': len(report['claims']), 'findings': len(report['findings']),
              'report_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
              'artifact_checks_sha256': hashlib.sha256((REV / 'additional_governance_artifact_checks.json').read_bytes()).hexdigest()}
(REV / 'additional_governance_remaining_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation))
