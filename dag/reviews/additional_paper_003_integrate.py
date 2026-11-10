"""Integrate completed support assessment and freeze the next parent slice."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / 'dag'
REV = DAG / 'reviews'
report = json.loads((REV/'additional_paper_003_support.json').read_text())
assert report['status'] == 'scope_complete' and len(report['file_reviews']) == 80 and not report['remaining_scope']
for row in report['file_reviews']:
    assert row['full_source_read']
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
coverage = json.loads((REV/'coverage.json').read_text())
next_rows = []
for row in coverage['files']:
    if not row['path'].startswith('papers/pfp/005_pfp_practitioners_field_manual/') or row['substantive_status'] == 'full_text_source_review_recorded':
        continue
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
    next_rows.append({'path':row['path'],'sha256':row['sha256'],'bytes':row['size_bytes'],'coverage_at_freeze':row['substantive_status']})
next_scope = {'source_commit':coverage['source_commit'],'files':next_rows,
    'limit':'Frozen next support scope only; no substantive reading is asserted by this inventory.'}
next_path = REV/'additional_paper_005_support_scope.json'
if next_path.exists():
    assert json.loads(next_path.read_text()) == next_scope
else:
    next_path.write_text(json.dumps(next_scope,indent=2)+'\n',encoding='utf-8')
swarm = json.loads((DAG/'swarm_manifest.json').read_text())
completed = 'dag/reviews/additional_paper_003_support.json'
if completed not in swarm['completed_followup_slices']:
    swarm['completed_followup_slices'].append(completed)
swarm['parent_active_slice'] = {'scope':'Paper005 supporting files','scope_manifest':'dag/reviews/additional_paper_005_support_scope.json',
    'status':'scope_frozen_reading_not_started','full':0,'pending':len(next_rows),
    'previous_completed_report':completed}
(DAG/'swarm_manifest.json').write_text(json.dumps(swarm,indent=2)+'\n',encoding='utf-8')
validation = json.loads((DAG/'validation.json').read_text())
entry = next(x for x in validation['checks'] if x['name'] in {'Paper003_incremental_tests_and_countercontrols','Paper003_complete_support_slice'})
entry.update(name='Paper003_complete_support_slice',
    result='80_full_logical_contents_62_PDF_pages_79_archive_members_155_bindings_31_diff_reconstructions_59_Python_pass_1_native_skip_7_probes',
    limit='Historical rational checks and interval recomputation are separate from fresh package tests. No full native build, notebook/provider execution, independent historical-call authentication or model-effect evidence.')
entry['archive_validation'] = 'dag/reviews/additional_paper_003_archive_checks.json'
entry['historical_checks'] = 'dag/reviews/additional_paper_003_historical_checks.json'
(DAG/'validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
progress = DAG/'PROGRESS.md'
paragraph = (
    '\nThe parent completed all 80 Paper003 support files, with a contextual current-manuscript reread. '
    'All 62 PDF pages and all 79 historical ZIP logical members have direct/base-plus-complete-difference reading evidence; '
    '155 embedded digest bindings and 31 full reverse-diff reconstructions pass. The 1,256 difference lines include three '
    'long changed JSON log pairs reviewed through exact character deltas against complete current logs. '
    'Thirty historical trials reduce to ten distinct bodies after seed/envelope removal; all 48 finite witness dispositions, '
    'fuel/call totals, 20,382 declared tokens and reported interval arithmetic reproduce, but provider independence and performance do not follow. '
    'Two additional traces expose prompt/feedback arithmetic inconsistency and unpopulated admission fields. '
    'Twelve findings retain live-accounting/status/parser/native-input defects, absent notebook dependencies, current custody drift, '
    'edited dated records, source-pin path renaming, historical-trial limits and rendering defects. '
    'The three elementary lemmas and evaluation design remain useful. Fresh evidence remains 59 Python passes, one deliberately skipped '
    'native-parity case and seven isolated controls, plus separate historical arithmetic and public teaching worksheet checks. '
    'No provider/private-answer access or original Paper003 byte changes occurred. '
    'See reviews/additional_paper_003_support.json and additional_paper_003_archive_checks.json. '
    f'The next parent slice freezes {len(next_rows)} Paper005 support files without claiming a reading yet.\n'
)
if b'The parent completed all 80 Paper003 support files' not in progress.read_bytes():
    with progress.open('a',encoding='utf-8') as f:
        f.write(paragraph)
print(json.dumps({'paper003':len(report['file_reviews']),'findings':len(report['findings']),
    'next_paper005_scope':len(next_rows),'coverage':coverage['counts']}))
