"""Reconcile completed swarm slices without promoting bounded artifacts."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT/'dag'
REV = DAG/'reviews'
completed = [
    ('additional_rust_pfp_foundations.json',368,368,'368 full source reads;22 claims;75 findings;24 validation records'),
    ('additional_paper_004_support.json',89,73,'89 dispositions:73 full and16 bounded;58 Python passes;11 probes;deep archive bodies remain unread'),
    ('additional_challenges_041_050.json',162,162,'1207 dispositions:162 full source reads and1045 bounded parsed-data assessments;39 findings;10 conditional claims'),
    ('additional_paper_006_support.json',46,35,'43 assigned paths:32 full and11 bounded, plus3 fully read dependencies;four claims;seven findings'),
    ('additional_paper_005_support.json',61,61,'61 full logical contents;40 PDF pages;60 archive members;19 findings;62 pure-test passes;18 independent observations'),
]
for filename,count,full,_ in completed:
    report = json.loads((REV/filename).read_text())
    rows = report['file_reviews']
    assert len(rows) == count and sum(x['full_source_read'] for x in rows) == full
    for row in rows:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
swarm = json.loads((DAG/'swarm_manifest.json').read_text())
for filename,_,_,_ in completed:
    path = 'dag/reviews/'+filename
    if path not in swarm['completed_followup_slices']:
        swarm['completed_followup_slices'].append(path)
swarm['active_audit_slices'] = [
    {'agent':'audit_systems','scope':'64 pending Rust core_functional/core_certifiers and shared test/fixture files','status':'in_progress','scope_manifest':'dag/reviews/additional_rust_functional_certifiers_scope.json'},
    {'agent':'audit_challenges_041_050','scope':'1240 new C051-C059 paths, excluding49 prior full reads','status':'in_progress','scope_manifest':'dag/reviews/additional_challenges_051_059_scope.json'},
    {'agent':'audit_imported_pilots','scope':'Paper007 pending supporting files, exact scope being frozen','status':'in_progress','scope_manifest':'dag/reviews/additional_paper_007_support_scope.json'},
]
parent = json.loads((REV/'additional_paper_005_support.json').read_text())
swarm['parent_active_slice'] = {'scope':'Paper005 supporting files','scope_manifest':'dag/reviews/additional_paper_005_support_scope.json',
    'status':'in_progress','full':sum(x['full_source_read'] for x in parent['file_reviews']),
    'pending':len(parent['remaining_scope']),'report':'dag/reviews/additional_paper_005_support.json'}
if parent['status'] == 'scope_complete':
    coverage = json.loads((REV/'coverage.json').read_text())
    prefix = 'papers/pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks/'
    next_path = REV/'additional_paper_008_support_scope.json'
    if not next_path.exists():
        candidates = [r for r in coverage['files'] if r['path'].startswith(prefix) and r['substantive_status'] != 'full_text_source_review_recorded']
        next_scope = {'source_commit':coverage['source_commit'],'files':[],'limit':'Frozen pending support inventory only; no reading credit from inventory.'}
        for r in candidates:
            assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest() == r['sha256']
            next_scope['files'].append({'path':r['path'],'sha256':r['sha256'],'bytes':r['size_bytes'],'coverage_at_freeze':r['substantive_status']})
        next_path.write_text(json.dumps(next_scope,indent=2)+'\n',encoding='utf-8')
    next_scope = json.loads(next_path.read_text())
    swarm['parent_active_slice'] = {'scope':'Paper008 supporting files','scope_manifest':'dag/reviews/additional_paper_008_support_scope.json',
        'status':'scope_frozen_reading_not_started','full':0,'pending':len(next_scope['files']),
        'previous_completed_report':'dag/reviews/additional_paper_005_support.json'}
(DAG/'swarm_manifest.json').write_text(json.dumps(swarm,indent=2)+'\n',encoding='utf-8')
validation = json.loads((DAG/'validation.json').read_text())
records = [
    {'name':'Rust_PFP_foundations_complete_368','result':completed[0][3],'receipt':'dag/reviews/additional_rust_pfp_foundations_completion_validation.json'},
    {'name':'Paper004_support_dispositions_complete','result':completed[1][3],'receipt':'dag/reviews/additional_paper_004_final_validation.json',
        'limit':'Nine selected tar bodies read;7866 other tar bodies and18 nested ZIP contents remain unreviewed. Bounded archive disposition does not complete the every-file semantic objective.'},
    {'name':'C041_C050_complete_assigned_corpus','result':completed[2][3],'receipt':'dag/reviews/additional_challenges_041_050_reconciliation.json'},
    {'name':'Paper006_support_dispositions_complete','result':completed[3][3],'receipt':'dag/reviews/additional_paper_006_final_validation.json',
        'limit':'Current3 toy passes,3 catalog setup errors and worksheet SHA failure; archive6 tests and worksheet pass;11 isolated storage tests pass. CRLF-only catalog byte mismatch, historical archived semantics and ordinary integration remain distinct.'},
    {'name':'Paper005_complete_support_slice','result':completed[4][3],
        'receipt':'dag/reviews/additional_paper_005_final_validation.json','limit':'Earlier full-suite attempt had one environment socket-denial failure and63 passes. Native/source-object skips do not count as passes. No paid calls or private answer access.'},
]
validation['checks'] = [x for x in validation['checks'] if x['name'] != 'Paper005_incremental_source_and_countercontrols']
for item in records:
    matches = [x for x in validation['checks'] if x['name'] == item['name']]
    if matches:
        matches[0].clear()
        matches[0].update(item)
    else:
        validation['checks'].append(item)
(DAG/'validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
marker = b'Integrated the completed368-file Rust PFP foundation slice'
progress = DAG/'PROGRESS.md'
if marker not in progress.read_bytes():
    with progress.open('a',encoding='utf-8') as stream:
        stream.write('\nIntegrated the completed368-file Rust PFP foundation slice (22 claims,75 findings), '
            'Paper004 support dispositions (73 full,16 bounded), and C041-C050 dispositions (162 full,1045 parsed data). '
            'Paper004 deep archives remain an explicit semantic backlog. New active slices are64 Rust functional/certifier files, '
            '1240 C051-C059 paths and43 Paper006 support paths. Paper005 now has source-bound partial coverage and18 offline observations. '
            'Actual graph execution found a Matolcsi accepted move recorded as refused and an R4 failed verification recorded as accepted zero defect. '
            'The pure package suite passed62 with34 skips and2 loopback exclusions; a previous loopback attempt failed with Windows10013. '
            'No native package, paid model or private benchmark answer was used. The overall every-file audit and empirical comparison remain incomplete.\n')
if b'Completed all61 Paper005 support files' not in progress.read_bytes():
    with progress.open('a',encoding='utf-8') as stream:
        stream.write('\nCompleted all61 Paper005 support files:40 PDF pages,60 archive logical members,28 exact changed-member reconstructions '
            'and135 fully read replacement rules. All117 archive manifest bindings and9 historical receipt/chain digests pass. '
            'Current manifests retain31/32 failures after LF normalization; a renamed historical receipt no longer verifies its own stored digest. '
            'The useful finite graph tutorial is retained with19 findings; current demo terminal/refusal misreporting precludes benchmark admission '
            'until repaired. Fresh pure tests62 pass,34 skip,2 HTTP exclusions;18 separate controls reproduced. Source bytes unchanged. '
            'Paper006 also completed43 assigned dispositions plus3 dependency bodies, with archive and runtime limits explicit. '
            'Parent next scope is Paper008; the support agent continues Paper007. Overall audit and empirical comparisons remain incomplete.\n')
print(json.dumps({'integrated':[x[0] for x in completed],'parent':swarm['parent_active_slice']}))
