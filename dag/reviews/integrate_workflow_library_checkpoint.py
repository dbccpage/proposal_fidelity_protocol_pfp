"""Validate and integrate the completed library slice without resetting other work."""
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


stem = 'additional_workflow_library_remaining'
path = REV / (stem + '.json')
data = json.loads(path.read_text())
validation = json.loads((REV / (stem + '_validation.json')).read_text())
assert validation['reports_sha256'][path.relative_to(ROOT).as_posix()] == sha(path)
assert len(data['file_reviews']) == 267
assert sum(bool(r['full_source_read']) for r in data['file_reviews']) == 167
unique = set()
ranges = 0
for item in walk(data):
    if isinstance(item.get('path'), str) and isinstance(item.get('sha256'), str):
        source = (ROOT / item['path']).resolve()
        assert source.is_relative_to(ROOT)
        assert sha(source) == item['sha256'], item['path']
        unique.add(item['path'])
        bounds = item.get('reviewed_lines', item.get('lines', []))
        # File metadata contains a scalar line count, while citations carry ranges.
        if isinstance(bounds, int):
            bounds = []
        if bounds and isinstance(bounds[0], int):
            bounds = [bounds]
        if bounds:
            count = len(source.read_text(encoding='utf-8').splitlines())
            for first, last in bounds:
                assert 1 <= first <= last <= count
                ranges += 1
receipt = {
    'status': 'parent_review_and_integrity_validation_pass',
    'report': path.relative_to(ROOT).as_posix(), 'report_sha256': sha(path),
    'scope_dispositions': 267, 'full_body_receipts': 167, 'bounded_artifact_dispositions': 100,
    'unique_pins_checked_including_prior_reports': len(unique), 'citation_and_reading_ranges_checked': ranges,
    'claims': 4, 'findings': 8,
    'review_basis': 'Parent read the full summary and every compact claim/finding, the complete probe source and validation source, and all13 compact probe outcomes. Agent source readings remain attributed; no duplicate execution credit.',
    'critical_scope': ['WF3 split-ledger control affects the injected factory; the default shared factory stops.',
                       'Word-encoded answer control uses a public sum fixture, not the sealed benchmark.',
                       'Artifact pin drift is current-byte evidence, not proof of historical failure.'],
    'new_provider_calls': 0, 'parent_probe_reexecution': False
}
(REV / (stem + '_parent_integration.json')).write_text(json.dumps(receipt, indent=2)+'\n')

path = ROOT / 'dag/swarm_manifest.json'
manifest = json.loads(path.read_text())
if receipt['report'] not in manifest['completed_followup_slices']:
    manifest['completed_followup_slices'].append(receipt['report'])
for item in manifest['active_audit_slices']:
    if item.get('agent', '').endswith('audit_imported_pilots'):
        item.update(scope='31 EIS level pages and EIS/PCIV narration scripts', files=31,
                    status='in_progress', scope_manifest='dag/reviews/additional_eis_pciv_teaching_scripts_scope.json',
                    report='dag/reviews/additional_eis_pciv_teaching_scripts.json',
                    completed_scope_manifest='dag/reviews/additional_workflow_library_remaining_scope.json',
                    description='Disjoint31-file remainder of the parent126-file EIS/PCIV teaching scope.')
manifest['parent_active_slice'].update(full_body_reads=95, delegated_remaining_files=31,
    delegated_remaining_report='dag/reviews/additional_eis_pciv_teaching_scripts.json')
path.write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(receipt))
