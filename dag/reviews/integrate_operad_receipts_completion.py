"""Record parent review and custody verification without replaying historical systems."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
name='additional_operad_receipts_remaining'; path=REV/(name+'.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(path)=='2fcbcc6129de8f8f56def8969ad092b99804eec1d238618e1df5c78278b746cb'
report=json.loads(path.read_text()); check=json.loads((REV/(name+'_validation.json')).read_text())
assert check['status']=='pass' and check['report_sha256']==sha(path)
assert report['summary']['full_source_reads']==351 and report['summary']['bounded_assessments']==271
receipt={'status':'parent_integration_pass','report':'dag/reviews/'+name+'.json','report_sha256':sha(path),
 'validation_sha256':sha(REV/(name+'_validation.json')),'summary':report['summary'],
 'parent_review':'Read all four claim summaries, twelve finding statements/details/limits, six control results, four workflow suggestions, prior-context entries, complete validator and complete bounded-control script. Reran custody/range/reading-transfer validator successfully. Agent source reading remains attributed to that agent.',
 'limits':['No retained application/native/provider execution.','Historical pin mismatches remain unresolved historical binding, not historical test failure.','No new workflow families: four suggestions refine existing encoding/admission/publication/accounting mechanisms.']}
(REV/(name+'_parent_integration.json')).write_text(json.dumps(receipt,indent=2)+'\n')
mp=ROOT/'dag/swarm_manifest.json';m=json.loads(mp.read_text())
ref='dag/reviews/'+name+'.json'
if ref not in m['completed_followup_slices']:m['completed_followup_slices'].append(ref)
for active in m['active_audit_slices']:
 if active['agent']=='audit_imported_pilots':
  active.update({'scope':'307 remaining ops/adversary files','status':'in_progress','scope_manifest':'dag/reviews/additional_ops_adversary_remaining_scope.json','report':'dag/reviews/additional_ops_adversary_remaining.json','completed_scope_manifest':'dag/reviews/'+name+'_scope.json','files':307,'description':'Read-only source review and finite controls; no retained/native/provider campaign execution.'})
mp.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'full':351,'bounded':271,'pending':0,'next_scope':307}))
