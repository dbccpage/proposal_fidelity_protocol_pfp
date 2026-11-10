"""Reconcile completed slices while preserving active Paper011 work."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DAG=ROOT/'dag';REV=DAG/'reviews'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=read(REV/'additional_paper_010_support.json');data=read(REV/'additional_paper_010_data.json')
assert parent['status']=='complete_with_explicit_artifact_bounds'
assert sha(REV/'additional_paper_010_data.json')==read(REV/'additional_paper_010_data_final_validation.json')['report_sha256']
rows=parent['file_reviews']+data['file_reviews']
assert len(rows)==len({x['path'] for x in rows})==83 and sum(x['full_source_read'] for x in rows)==73
for x in rows:assert sha(ROOT/x['path'])==x['sha256']
assert parent['scope_summary']['archive_body_counts']=={'full_text_body_transfer':73,'bounded_artifact':9,'pending_base_read':0}
receipt={'status':'complete_for83_frozen_support_paths','parent_report_sha256':sha(REV/'additional_paper_010_support.json'),'data_report_sha256':sha(REV/'additional_paper_010_data.json'),
         'assigned_paths':83,'full_source_bodies':73,'bounded_artifacts':10,'all83_original_hashes_unchanged':True,'claims':8,'findings':11,
         'archive_members':82,'archive_full_text_transfers':73,'archive_bounded_artifacts':9,'pdf_pages':46,'direct_visual_pages':23,'raw_equal_pages':14,'pixel_equal_pages':9,
         'current_tests':'40pass3fail','archive_tests':'43pass after workspace temp correction; first permission obstruction retained','independent_finite_state_checks':3344,
         'limits':['No fresh Lean/provider/QM-answer access.','Data controls and host finite-state controls are different denominators.','Archive/current drift remains; audit is not source repair.']}
write(REV/'additional_paper_010_final_validation.json',receipt)
adapters=read(REV/'additional_pfp_adapters.json');reconciliation=read(REV/'additional_pfp_adapters_reconciliation.json')
assert adapters['status']=='complete' and reconciliation['all_frozen_hashes_match']
assert len(adapters['file_reviews'])==155 and len(adapters['automated_reviews'])==138
for x in adapters['file_reviews']+adapters['automated_reviews']:assert sha(ROOT/x['path'])==x['sha256']
swarm=read(DAG/'swarm_manifest.json');validation=read(DAG/'validation.json')
for name in ('additional_pfp_adapters.json','additional_paper_010_support.json','additional_paper_010_data.json'):
    path='dag/reviews/'+name
    if path not in swarm['completed_followup_slices']:swarm['completed_followup_slices'].append(path)
for x in swarm['active_audit_slices']:
    if x['agent']=='audit_imported_pilots':x.update(scope='249 Paper011 native source/evidence paths',status='in_progress',scope_manifest='dag/reviews/additional_paper_011_native_scope.json',report='dag/reviews/additional_paper_011_native.json')
    elif x['agent']=='audit_challenges_041_050':x.update(scope='51 Paper011 core code/test paths',status='in_progress',scope_manifest='dag/reviews/additional_paper_011_core_scope.json',report='dag/reviews/additional_paper_011_core.json')
checks=[{'name':'PFP_adapter_slice_complete','result':'155 full bodies28647lines;138 bounded data assessments;26 findings2conditional claims;1033 retained-case labels agree','receipt':'dag/reviews/additional_pfp_adapters_reconciliation.json','limit':'Retained-label agreement is regression evidence; malformed native envelopes and AST dependency stubs explicitly scoped.'},
        {'name':'Paper010_all_support_dispositions_complete','result':'83 assigned paths73full10bounded;82 ZIP members46 PDF pages;8claims11findings','receipt':'dag/reviews/additional_paper_010_final_validation.json','limit':'Finite algebra and retained-record checks; no general mathematical/formal/model improvement certification.'}]
for c in checks:validation['checks']=[x for x in validation['checks'] if x['name']!=c['name']]+[c]
write(DAG/'swarm_manifest.json',swarm);write(DAG/'validation.json',validation)
progress=DAG/'PROGRESS.md';marker=b'Completed the293-path PFP adapter and83-path Paper010 support slices'
if marker not in progress.read_bytes():
    with progress.open('a',encoding='utf-8') as out:
        out.write('\nCompleted the293-path PFP adapter and83-path Paper010 support slices:155/73 full bodies and138/10 bounded artifacts respectively. Paper010 has8 conditional claims11 findings; all82 ZIP members46 PDF pages accounted. Independent data audit reads6953lines and distinguishes arithmetic/input-binding errors in three retained false nonflat certificates. Parent now owns41 Paper011 support paths, challenge agent51 core paths and paper agent249 native paths.666 history and1550 run-evidence paths remain separate unassigned partitions. Systems agent continues203 Rust quantum-physics owners. No original edits, provider calls or private answer reads.\n')
print(json.dumps({'adapters':293,'paper010':83,'paper011_active':341}))
