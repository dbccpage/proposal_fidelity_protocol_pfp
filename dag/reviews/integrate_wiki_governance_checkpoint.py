"""Validate completed review reports and record the next disjoint assignments."""
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


validated = []
for stem in ('additional_wiki_tests', 'additional_wiki_workflow_dag', 'additional_governance_remaining'):
    path = REV / (stem + '.json')
    data = json.loads(path.read_text())
    validation = json.loads((REV / (stem + '_validation.json')).read_text())
    assert sha(path) == validation['report_sha256'], stem
    unique = set()
    ranges = 0
    prior_reports = set()
    for item in walk(data):
        if isinstance(item.get('path'), str) and isinstance(item.get('sha256'), str):
            source = (ROOT / item['path']).resolve()
            assert source.is_relative_to(ROOT)
            assert sha(source) == item['sha256'], item['path']
            unique.add((item['path'], item['sha256']))
            bounds = item.get('reviewed_lines', item.get('lines', []))
            if bounds and isinstance(bounds[0], int):
                bounds = [bounds]
            if bounds:
                count = len(source.read_text(encoding='utf-8').splitlines())
                for first, last in bounds:
                    assert 1 <= first <= last <= count, (item['path'], first, last, count)
                    ranges += 1
        if item.get('report_sha256') and isinstance(item.get('report'), str):
            assert sha(ROOT / item['report']) == item['report_sha256'], item['report']
            prior_reports.add(item['report'])
    record = {'report': path.relative_to(ROOT).as_posix(), 'report_sha256': sha(path),
              'status': 'parent_review_and_integrity_validation_pass',
              'review_basis': 'Parent read all compact claims/findings and inspected probe mechanisms; full source-body receipts are attributed to the reviewing agent rather than reread by the parent.',
              'scope_dispositions': len(data['file_reviews']), 'full_body_receipts': sum(bool(x.get('full_source_read')) for x in data['file_reviews']),
              'unique_source_pins_checked': len(unique), 'line_ranges_checked': ranges,
              'prior_report_hashes_checked': sorted(prior_reports),
              'claims': len(data.get('claims', [])), 'findings': len(data.get('findings', []))}
    if stem == 'additional_governance_remaining':
        record['review_basis'] = 'Parent source/log/small-JSON readings, isolated owner probes and bounded artifact population checks; full/body and bounded dispositions remain separate.'
    if stem == 'additional_wiki_workflow_dag':
        b = ((-1, 1, 0), (0, -1, 1), (1, 0, -1))
        w, f, z = (Q(2),) * 3, (Q(0), Q(3), Q(5)), (Q(2),) * 3
        residual = [w[i] + sum(b[i][j] * f[j] for j in range(3)) for i in range(3)]
        assert residual == [5, 4, -3]
        assert all(sum(b[i][j] * z[i] for i in range(3)) == 0 for j in range(3))
        assert sum(w[i] * z[i] for i in range(3)) == sum(map(abs, residual)) == 12
        assert sum(map(abs, w)) == sum(w) == 6
        record['independent_parent_check'] = 'Exact triangle arithmetic reproduces the WF44 counterexample: displayed conditions admit objective12 while the cycle lower bound and f=0 establish optimum6.'
    (REV / (stem + '_parent_integration.json')).write_text(json.dumps(record, indent=2) + '\n')
    validated.append(record)

tests = json.loads((REV / 'additional_wiki_tests.json').read_text())
support = {'source_commit': tests['source_commit'], 'status': 'complete_attributed_supporting_body_reads',
           'source_report': 'dag/reviews/additional_wiki_tests.json',
           'source_report_sha256': sha(REV / 'additional_wiki_tests.json'),
           'file_reviews': tests['supporting_source_reads'],
           'limits': ['Three supporting source bodies explicitly read by the wiki reviewer; not included in the47-page scope count. No additional linked source body credit.']}
(REV / 'additional_wiki_tests_supporting_sources.json').write_text(json.dumps(support, indent=2) + '\n')

path = ROOT / 'dag/swarm_manifest.json'
manifest = json.loads(path.read_text())
active = manifest['active_audit_slices']
completed = manifest['completed_followup_slices']
for record in validated:
    if record['report'] not in completed:
        completed.append(record['report'])
for report in ('dag/reviews/additional_wiki_remaining.json', 'dag/reviews/additional_wiki_tests_supporting_sources.json'):
    if report not in completed:
        completed.append(report)
manifest['wiki_followup_status'] = {'parent_pages_fully_read': 106, 'agent_test_pages_fully_read': 47,
    'agent_workflow_dag_pages_fully_read': 1, 'frozen_remaining_scope_pages': 154, 'pending_pages': 0,
    'limits': 'This completes the154-page frozen remaining wiki slice; broader repository audit remains open.'}
for row in active:
    name = row.get('agent', row.get('name', ''))
    if name.endswith('audit_systems'):
        row.update(scope='165 remaining PFP application boundary and supporting files',
                   scope_manifest='dag/reviews/additional_pfp_application_remaining_scope.json',
                   completed_scope_manifest='dag/reviews/additional_wiki_tests_scope.json',
                   report='dag/reviews/additional_pfp_application_remaining.json', status='in_progress', files=165,
                   description='PFP application boundary, use cases, documentation, fixtures and packet schemas.')
    elif name.endswith('audit_imported_pilots'):
        row.update(scope='267 remaining standalone workflow and library files',
                   scope_manifest='dag/reviews/additional_workflow_library_remaining_scope.json',
                   completed_scope_manifest='dag/reviews/additional_wiki_workflow_dag_scope.json',
                   report='dag/reviews/additional_workflow_library_remaining.json', status='in_progress', files=267,
                   description='Remaining standalone workflow implementations and workflow library records.')
manifest['parent_active_slice'] = {'status': 'governance_slice_completed_selecting_next_scope',
                                 'completed_report': 'dag/reviews/additional_governance_remaining.json',
                                 'full_body_reads': 32, 'bounded_dispositions': 44}
path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'integrated': [{k:r[k] for k in ('report','scope_dispositions','full_body_receipts','claims','findings')} for r in validated],
                  'wiki_supporting_full_reads': len(support['file_reviews'])}))
