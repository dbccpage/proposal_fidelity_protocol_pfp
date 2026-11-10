"""Integrate attributed pattern reviews without replaying historical executions."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
STEM = 'additional_operad_patterns_remaining'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report_path = REV / (STEM + '.json')
assert sha(report_path) == '75ff5071eded43b314f78297409f28195f136371564993111b8e679d9732f652'
report = json.loads(report_path.read_text())
with contextlib.redirect_stdout(io.StringIO()):
    runpy.run_path(str(REV / (STEM + '_validate.py')))
validation = json.loads((REV / (STEM + '_validation.json')).read_text())
checks = json.loads((REV / (STEM + '_checks.json')).read_text())
assert report['probes'] == checks['probes']
assert len(report['file_reviews']) == 198
assert len(report['supporting_file_reviews']) == 6
support = {
    'review_id': 'operad_pattern_supporting_sources',
    'status': 'complete_declared_supporting_scope',
    'source_commit': report['source_commit'],
    'attributed_report': report_path.relative_to(ROOT).as_posix(),
    'attributed_report_sha256': sha(report_path),
    'file_reviews': report['supporting_file_reviews'],
    'claims': [], 'findings': [],
    'limits': ['Six complete source reads attributed to the pattern reviewer; no duplicate claims or new execution.',
               'Parent reviewed the assessments, controls and custody; did not independently reread all source bodies.'],
}
(REV / 'additional_operad_patterns_supporting_sources.json').write_text(json.dumps(support, indent=2) + '\n')
integration = {
    'status': 'parent_review_and_custody_validation_pass',
    'report': report_path.relative_to(ROOT).as_posix(), 'report_sha256': sha(report_path),
    'scope_full_reads': 198, 'supporting_full_reads': 6,
    'claims': 4, 'findings': 18, 'controls_attributed_to_agent': 13,
    'evidence_ranges_checked': validation['source_evidence_ranges_validated'],
    'parent_review_basis': 'Read all compact claim/finding statements and ceilings, complete checks and validator source, all thirteen observed control results, supporting assessments and workflow/prior-context summaries. Revalidated source pins and ranges with the reviewed validator.',
    'limits': ['Full-source reads remain attributed to the agent.',
               'No native/provider or historical campaign replay; workflow suggestions cross-reference existing families.'],
}
(REV / (STEM + '_parent_integration.json')).write_text(json.dumps(integration, indent=2) + '\n')
manifest_path = ROOT / 'dag/swarm_manifest.json'
manifest = json.loads(manifest_path.read_text())
for path in [report_path.relative_to(ROOT).as_posix(), 'dag/reviews/additional_operad_patterns_supporting_sources.json']:
    if path not in manifest['completed_followup_slices']:
        manifest['completed_followup_slices'].append(path)
assignment = next(a for a in manifest['active_audit_slices'] if a['agent'] == 'audit_imported_pilots')
assignment.update({
    'scope': '622 remaining operad receipt and snapshot files', 'files': 622, 'status': 'in_progress',
    'scope_manifest': 'dag/reviews/additional_operad_receipts_remaining_scope.json',
    'report': 'dag/reviews/additional_operad_receipts_remaining.json',
    'completed_scope_manifest': 'dag/reviews/additional_operad_patterns_remaining_scope.json',
    'description': 'Historical receipt custody, complete code/narrative reads and explicitly bounded generated-artifact assessment; no fresh campaign replay.',
})
next(a for a in manifest['active_audit_slices'] if a['agent'] == 'audit_challenges_041_050')['description'] = '438 unchanged sources plus two migration-adapted consumers with separately pinned original and current revisions.'
manifest['latest_user_priority']['status'] = 'local_move_verified_source_pr_merged'
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(integration))
