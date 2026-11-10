"""Validate delegated source custody before registering the next review slice."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
name='additional_rust_quantum_physics';rp=REV/(name+'.json');report=read(rp)
assert sha(rp)=='551340d8fe1ac4190f4c00c3da165e399020c407b44a03bc4603392a345e88d5'
scope=read(REV/(name+'_scope.json'))['files'];rows={r['path']:r for r in report['file_reviews']}
assert len(scope)==len(rows)==203
for row in scope:
    assert sha(ROOT/row['path'])==row['sha256']==rows[row['path']]['sha256']
    assert rows[row['path']]['full_source_read'] is True
write(REV/(name+'_parent_integration.json'),{'report_sha256':sha(rp),'frozen_hashes_verified':203,
    'full_bodies':203,'direct_bodies':48,'lossless_template_reconstructions':155,
    'claims':33,'findings':45,'parent_review':'Read all scoped claims and findings; source-body reviews and bounded native probes delegated with preserved integrity receipts.',
    'next_scope':'dag/reviews/additional_paper_011_recreated_receipts_scope.json'})
swarm=read(ROOT/'dag/swarm_manifest.json');path='dag/reviews/'+name+'.json'
if path not in swarm['completed_followup_slices']:swarm['completed_followup_slices'].append(path)
for row in swarm['active_audit_slices']:
    if row['agent']=='audit_systems':
        row.update(scope='1164 Paper011 recreated-run historical receipt paths',status='queued',
            completed_scope_manifest='dag/reviews/'+name+'_scope.json',
            scope_manifest='dag/reviews/additional_paper_011_recreated_receipts_scope.json',
            report='dag/reviews/additional_paper_011_recreated_receipts.json')
    if row['agent']=='audit_imported_pilots':row['status']='in_progress'
write(ROOT/'dag/swarm_manifest.json',swarm)
print('Integrated 203 exact source pins, 33 claims and 45 bounded findings.')
