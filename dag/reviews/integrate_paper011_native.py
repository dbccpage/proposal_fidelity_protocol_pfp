"""Validate the completed delegated report and queue its next frozen slice."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

name = 'additional_paper_011_native'
report = read(REV / (name+'.json'))
assert sha(REV/(name+'.json')) == '9d99a38ec2d415bc8fc9cd58efb05ff88112325cb15cbfaa783baab310131ed9'
scope = read(REV/(name+'_scope.json'))['files']
rows = {r['path']:r for r in report['file_reviews']}
assert len(rows)==len(scope)==249
for r in scope:
    assert sha(ROOT/r['path'])==r['sha256']==rows[r['path']]['sha256'], r['path']
assert sum(bool(r['full_source_read']) for r in rows.values())==247
write(REV/(name+'_parent_integration.json'), {
    'report_sha256':sha(REV/(name+'.json')), 'frozen_hashes_verified':249,
    'full_bodies':247, 'bounded':2, 'claims':len(report['claims']),
    'findings':len(report['findings']),
    'parent_review':'Read scoped claims, findings and validation; did not duplicate all delegated source reading or perform native builds.',
    'next_scope':'dag/reviews/additional_paper_011_aggregate_native_receipts_scope.json'})
swarm=read(ROOT/'dag/swarm_manifest.json')
path='dag/reviews/'+name+'.json'
if path not in swarm['completed_followup_slices']:
    swarm['completed_followup_slices'].append(path)
for row in swarm['active_audit_slices']:
    if row['agent']=='audit_imported_pilots':
        row.update(scope='386 Paper011 aggregate/native historical receipt paths', status='queued',
                   completed_scope_manifest='dag/reviews/'+name+'_scope.json',
                   scope_manifest='dag/reviews/additional_paper_011_aggregate_native_receipts_scope.json',
                   report='dag/reviews/additional_paper_011_aggregate_native_receipts.json')
write(ROOT/'dag/swarm_manifest.json',swarm)
print('Validated 249 exact source pins; integrated 247 full and 2 bounded reviews.')
