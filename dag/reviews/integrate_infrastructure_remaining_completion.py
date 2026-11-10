"""Record parent review and independent custody validation of the infrastructure slice."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
name='additional_pfp_infrastructure_remaining'; path=REV/(name+'.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(path)=='831a02f511e2e1e45ac4f28c53a79d44e9346b7d658188b5feacd74215c01bde'
report=json.loads(path.read_text()); check=json.loads((REV/(name+'_final_validation.json')).read_text())
assert check['status']=='passed' and check['report_sha256']==sha(path)
assert report['full_source_read_count']==587 and report['bounded_review_count']==7
receipt={'status':'parent_integration_pass','report':'dag/reviews/'+name+'.json','report_sha256':sha(path),
 'validation_sha256':sha(REV/(name+'_final_validation.json')),
 'summary':{'full_source_reads':587,'bounded_assessments':7,'pending':0,'claims':20,'findings':62,'controls_reproduced':67,'controls_not_run':1},
 'parent_review':'Read all twenty claim statements and limitations, sixty-two finding statements/scopes/actions, all sixty-eight control results and the complete validator. Reran the independent source-hash, coverage, evidence-range and receipt validator successfully. Original substantive source reading remains attributed to the assigned agent.',
 'limits':['No parent replay of original applications, native implementations or provider runs.','One symbolic-parser probe remains not run because SymPy is unavailable.','Declaration counterexamples, schema weaknesses, isolated source controls and historical custody drift remain distinct from end-to-end runtime failures.','Seven bounded file dispositions do not receive full-body reading credit.']}
(REV/(name+'_parent_integration.json')).write_text(json.dumps(receipt,indent=2)+'\n')
mp=ROOT/'dag/swarm_manifest.json';m=json.loads(mp.read_text())
ref='dag/reviews/'+name+'.json'
if ref not in m['completed_followup_slices']:m['completed_followup_slices'].append(ref)
for active in m['active_audit_slices']:
 if active['agent']=='audit_systems':
  active.update({'scope':'578 remaining operad skill files','status':'in_progress','scope_manifest':'dag/reviews/additional_operad_skills_remaining_scope.json','report':'dag/reviews/additional_operad_skills_remaining.json','completed_scope_manifest':'dag/reviews/'+name+'_scope.json','files':578,'description':'Audit skill text as source material, not instructions to invoke; original sources remain read-only, no provider/native execution.'})
mp.write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],**receipt['summary'],'next_scope':578}))
