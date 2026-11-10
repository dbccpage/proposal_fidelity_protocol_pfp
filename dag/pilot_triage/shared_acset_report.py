"""Assemble receipts for the parent's completed two-owner source review."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
inventory={r['path']:r['sha256'] for r in json.loads((ROOT/'dag/file_inventory.json').read_text())['files']}
migration=json.loads((ROOT/'dag/migrations/anomalon_pilots_move.json').read_text())
custody={'pilots/anomalon_woland/'+r['path']:r['sha256'] for r in migration['entries']}
reviews=[]; pilots=[]
def receipt(path, assessment):
    data=(ROOT/path).read_bytes(); digest=hashlib.sha256(data).hexdigest()
    if digest != {**inventory,**custody}.get(path): raise ValueError('Pinned source changed: '+path)
    result={'path':path,'sha256':digest,'full_source_read':True,'reviewed_lines':[[1,len(data.splitlines())]],'assessment':assessment}
    reviews.append(result)
    return {'path':path,'sha256':digest,'lines':[1,len(data.splitlines())],'review_level':'full_source_read_and_semantic_assessment'}

for name, contribution, basis in [
 ('acset_prompt_rewriting','Restricted graph rewrite with independent exact protected-prompt query comparison.',
  'Finite attributed directed graphs; explicit injective incidence-preserving matches; identity-key interface inclusions; equality of ordered source-slot/role/UTF-8 text and source identity.'),
 ('acset_cochain_rewriting','Source/rule-bound graph repair checked against a supplied fixed rational potential.',
  'For every oriented edge u→v, check c(e)=p(v)-p(u) using Fraction; preserve all vertices/potentials and oriented multiplicities. Sum of residuals zero is insufficient.')]:
    src=ROOT/'pilots/anomalon_woland'/name
    canonical=ROOT/'workflows/wf21_structural_prompt_rewriting/pilots'/name
    evidence=[]; duplicates=[]
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.suffix not in {'.py','.md','.yaml'}:continue
        rel=p.relative_to(ROOT).as_posix(); other=(canonical/p.name).relative_to(ROOT).as_posix()
        evidence.append(receipt(rel,'Full source read; '+contribution+' Existing WF21 owner comparison completed. Legacy import/runner path limits retained.'))
        evidence.append(receipt(other,'Full corresponding content accounted for by direct source reading plus complete diff: only documented legacy namespace/command substitutions where unequal. '+contribution))
        duplicates.append({'imported':rel,'existing':other,'byte_identical':p.read_bytes()==(ROOT/other).read_bytes(),
                           'nonidentical_scope':'Only Woland/adversary namespace substitutions in README/runner; no mathematical mechanism change.'})
    test=(canonical/'tests'/('test_'+name+'.py')).relative_to(ROOT).as_posix()
    evidence.append(receipt(test,'Full test source read: 25 distinct positive/negative finite controls. Fresh suite collection fails on missing legacy omega_engine_pfp import; test bodies were not executed by that invocation.'))
    pilots.append({'id':name,'path':src.relative_to(ROOT).as_posix(),'contribution':contribution,'mathematical_basis':basis,
                   'reusable_mechanism_name':name,'verdict':'duplicate_candidate','workflow_mapping':[{'family_id':'WF21','path':'workflows/wf21_structural_prompt_rewriting','relationship':'Existing canonical implementation of the same mechanism.'}],
                   'source_evidence':evidence,'duplicate_evidence':duplicates,
                   'rationale':'The mechanism is substantive and already present in WF21. Imported local test paths do not exist; canonical tests exist but the current legacy import boundary prevents collection. No extra workflow family follows from another copy.',
                   'next_action':'Consolidate the duplicate source under WF21 after repairing canonical package imports/resource lookup and rerunning all 50 finite controls; preserve lineage and source receipts.',
                   'qm_seed_transfer':{'protected_qm_seed_read':False,'mathematical_support_for_unchanged_qm_seed':'NOT_ESTABLISHED','requires_seed_appropriate_checker_or_encoding':True,'prerequisite':'Byte preservation can protect any declared seed, but the fixed-potential cochain judge cannot grade an arbitrary QM derivation. Supply a separate adequate QM checker; never infer accuracy from graph or byte preservation.'},
                   'actual_execution_status':{'model_calls':0,'canonical_suite':'two collection errors: missing omega_engine_pfp','isolated_probes':'six finite kernel/gradient probes pass under explicit one-module legacy import mapping','full_suite_run':False}})

core=receipt('pfp/domain/rewriting/finite_dpo.py','Full implementation read: typed bounded immutable graph data; explicit injective natural matches, identity-key monic interface, dangling/protection checks, fresh IDs and decreasing fuel. This is a restricted executor, not match search, general ACSet semantics or confluence proof.')
for p in pilots:p['source_evidence'].append(core)
report={'schema_version':'1.0','status':'two_shared_pilot_owners_initially_assessed','pilots':pilots,'provider_calls':0,
        'scope':'Nine imported primary files, nine corresponding WF21 files via full content/diff reading, both canonical 25-test sources, and the finite executor. Cache files and unrelated owners are outside this pass.',
        'validation':{'canonical_tests':'2 collection errors; no cases executed','isolated_public_finite_probes':6,'probe_receipt':'dag/pilot_triage/shared_acset_probe_results.json'}}
(ROOT/'dag/pilot_triage/shared_acset.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
supplement={'schema_version':'1.0','file_reviews':reviews,'claims':[
 {'id':'ACSET-C01','statement':'The finite executor implements one restricted attributed-graph DPO construction with explicit injective matches, identity-key interface inclusions, dangling checks and finite fuel.','evidence':['pfp/domain/rewriting/finite_dpo.py'],'dependencies':['Fixed typed finite attributed-graph schema','Caller supplies a registered rule and an injective incidence-preserving match'],'limits':['No general match search or universal confluence theorem','Structural rewrite acceptance does not establish task correctness']},
 {'id':'ACSET-C02','statement':'Independent query checks distinguish structural admissibility from preservation: prompt checks compare protected ordered bytes/source identity, and the cochain check verifies every exact rational edge residual against a fixed potential.','evidence':['workflows/wf21_structural_prompt_rewriting/pilots/acset_prompt_rewriting/pilot.py','workflows/wf21_structural_prompt_rewriting/pilots/acset_cochain_rewriting/checker.py'],'dependencies':['The protected query adequately represents the intended preservation obligation'],'limits':['Prompt preservation is not semantic equivalence of arbitrary prose or solver accuracy','Fixed-potential checking is not quotient-norm minimization']}],
 'findings':[{'id':'ACSET-F01','finding':'Both imported ACSet owners duplicate existing WF21 mechanisms; core pilot/checker sources are byte-identical.','severity':'info'},
             {'id':'ACSET-F02','finding':'Imported README test paths are absent, while existing WF21 tests fail collection because omega_engine_pfp is unavailable in the current PFP environment.','severity':'medium'},
             {'id':'ACSET-F03','finding':'Prompt runner retains old omega_engine_woland/omega_engine_adversary imports and a parent-relative omega_engine_pfp source path that does not resolve at either new location.','severity':'medium'}],
 'validation':report['validation'],'limits':['No source changes, paid calls, protected benchmark reads or deletions.','The explicit isolated probe binding is not an installed package repair.']}
(ROOT/'dag/reviews/additional_imported_acset.json').write_text(json.dumps(supplement,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'full_read_receipts':len(reviews),'shared_pilots':len(pilots),'new_workflow_families':0}))
