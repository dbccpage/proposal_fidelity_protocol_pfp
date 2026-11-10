"""Verify completed core receipt and assign the disjoint formal-history continuation."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report_path=REV/'additional_paper_011_core.json';report=read(report_path)
assert sha(report_path)=='a82d60086ad114597062a702562a2a969344e3762894d8a0990937e4bf5dea42'
scope=read(REV/'additional_paper_011_core_scope.json');expected={x['path']:x['sha256'] for x in scope['files']}
for path,digest in expected.items():assert sha(ROOT/path)==digest
full={x['path']:x for x in report['file_reviews'] if x.get('full_source_read')}
assert len(expected)==51 and len(full)==50
for path,row in full.items():
    assert expected[path]==row['sha256']
    assert row['reviewed_lines']==[[1,len((ROOT/path).read_text(encoding='utf-8-sig').splitlines())]]
swarm_path=ROOT/'dag/swarm_manifest.json';swarm=read(swarm_path)
done='dag/reviews/additional_paper_011_core.json'
if done not in swarm['completed_followup_slices']:swarm['completed_followup_slices'].append(done)
for row in swarm['active_audit_slices']:
    if row['agent']=='audit_challenges_041_050':
        row.update(scope='446 Paper011 g01/g02/g12 formal-history receipt/source paths',status='in_progress',scope_manifest='dag/reviews/additional_paper_011_history_formal_receipts_scope.json',report='dag/reviews/additional_paper_011_history_formal_receipts.json')
swarm_path.write_text(json.dumps(swarm,indent=2)+'\n',encoding='utf-8')
receipt={'status':'core_hashes_and_full_read_ranges_validated','report_sha256':sha(report_path),'files':51,'full_bodies':50,'bounded':1,'claims':len(report['claims']),'findings':len(report['findings']),'next_scope':swarm['active_audit_slices']}
(REV/'additional_paper_011_core_parent_integration.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'validated_files':51,'full':50,'claims':len(report['claims']),'findings':len(report['findings'])}))
