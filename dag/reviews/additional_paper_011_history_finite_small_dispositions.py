"""Persist explicitly read small receipts and bounded all-carrier checks."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
target=REV/'additional_paper_011_history_finite_receipts.json';report=read(target)
scope=read(REV/'additional_paper_011_history_finite_receipts_scope.json')
frozen={x['path']:x for x in scope['files']};rows={x['path']:x for x in report['file_reviews']}
checks=read(REV/'additional_paper_011_history_finite_small_checks.json')
notes={
 'g03/count_preserving_poison_request.json':'Permutes datum0/2 and all state incidence while retaining the untransported target2/3. Fresh independent checks confirm equal collapse counts but a now-separated target: useful correspondence poison, not a count-only detector.',
 'g03/count_preserving_poison_restoration_request.json':'Restores the original four-chain state and target2/3. Recomputed all seven valid one-instance repairs; this is a tiny positive control within the declared adapter.',
 'g03/count_preserving_poison_restoration_stdout.json':'Seven raw cost-one repairs partition into five declared classes with sizes1,1,1,2,2; no new-form mark, weak/strong false. Complete raw-delta membership replayed independently, but canonical class inequivalence was not re-proved.',
 'g03/duplicated_pair_request.json':'Two exactly identical case IDs and bodies exercise duplicate population rejection. Request alone is not execution evidence; bound process/stderr remain separate.',
 'g03/fixed_target_reuse_request.json':'Unchanged three-chain state with target0/1 replacing2/3. Endpoint profiles already differ, independently checked; this is a target-binding refusal control.',
 'g03/frozen_failed_replays/control_recording_failure.json':'Explicit FAILED/complete=false with str.relative_to AttributeError; useful failure custody, not a completed replay. Duplicate top-level failure remains separately identified.',
 'g03/independent_replay_failure.json':'Explicit FAILED/complete=false with str.relative_to AttributeError. Preserves the earlier receiver failure instead of presenting native exit0 as whole-replay success.',
 'g03/poisoned_collapse_adapter_request.json':'Adds a unary instance at target2, destroying the required2/3 collapse. Independent unary-profile check confirms the intended mutation; no fresh native refusal executed.',
 'g03/predicates_not_on_classes_request.json':'Sets predicate_domain to raw_deltas while leaving the valid base case intact; tests enforcement of the declared quotient-level predicate domain.',
 'g03/preregistration.json':'Explicit finite domains, new prefix/anchor construction, class predicates, two source hashes, and zero original model arms. Declares extra structure changes repairs; chronology excerpt is useful but does not prove absence of unlogged pre-registration calls.',
 'g03/restored_target_request.json':'Restores target2/3 in the three-chain state. Profiles confirm collapse before repair and exact enumeration yields seven valid one-instance repairs.',
 'g03/restored_target_stdout.json':'Complete seven raw repairs and five declared canonical classes read; partition membership, representative inclusion, sizes, cost and false fresh-mark predicates checked. No fresh quotient-classification proof.',
 'g03/solve.json':'SOLVED is explicitly finite and adapter-relative. Terminal triple3,1,2 repeats across four reading/measure combinations; preserved row digest is custody, not original model-arm success or G4 generality.',
 'g03/stale_script_receipt_mutation.json':'Adds a forward-slash adapter path with all-zero digest beside the original backslash binding. The reviewed loop checks every entry, so Windows aliasing does not make the added false digest disappear. Useful exact-source-binding poison; no fresh native execution.',
 'g03/strict_label_failure.json':'Native exit0 but worker exit1, no passing fallback, strict-label disagreement retained. Python repr ordering versus structured native ordering requires an explicit isomorphism bridge; unequal labels alone are not unequal structures.',
 'g03_package_v1/preservation_receipt.json':'Seven original representation/tool-excerpt entries with sizes/hashes,69members and nonordinal initial ordering. Separates representation repair from mathematical rerun, and retained chronology from retroactive worker preflight. External rollout paths were not opened.',
 'g04/result.json':'Scope-explicit historical aggregate:18798 rows/131586 row-stakes/16331classes/81610 mappings, three bounded invariance labels, endpoint and universal-stake counterexamples. Original held-out and owner estate gates remain false/missing. Exact historical replay helper833583... remains unresolved; no model improvement is established.',
 'g04/universal_poison_v1/counterexample_request.json':'Two L histories differ in which old datum receives a unary instance; pi swaps0/1,phi fixes the form, and supplied stake separates0/2 only. This new supplementary stake differs from the original seven and is not a recovered original held-out.',
 'g04/universal_poison_v1/counterexample_stdout.json':'Explicit source/target prefixes match under the common mapping, while fixed first counts are absent/3 and transported counts absent/absent. Complete small witness read; demonstrates why fixed-stake invariance does not quantify over arbitrary stakes.',
 'g04/universal_poison_v1/universal_fixed_stake_poison_request.json':'Same supplementary witness switches mode to assert_universal_fixed; a proposed universal statement is deliberately false on fixed counts absent/3.',
 'g04/universal_poison_v1/universal_fixed_stake_poison_stdout.json':'Typed UNIVERSAL_FIXED_STAKE_POISON refusal with absent/3 witness. Retained output is consistent with the explicit counterexample, not fresh native execution.',
 'g04/universal_poison_v1/untransported_supplement_stake_request.json':'Uses the original stake matrix as reported transported matrix despite swapping0/1. Isolates missing stake transport from valid prefix transport.',
 'g04/universal_poison_v1/untransported_supplement_stake_stdout.json':'Typed STAKE_TRANSPORT_MISMATCH refusal. Useful negative control with separately bound request/process streams.',
 'g04/universal_poison_v1/wrong_common_data_mapping_request.json':'Changes pi to identity although the histories place the unary instance at different old data. Keeps the original relation as contextual metadata; actual supplied pi fails prefix equivalence.',
 'g04/universal_poison_v1/wrong_common_data_mapping_stdout.json':'Typed COMMON_PREFIX_ISOMORPHISM:2 refusal identifies the first unary-instance prefix discrepancy. Historical finite negative output only.',
 'g07/pinned_python/artifacts/claims.json':'Complete claim table read. Conditional supplied-admission/profile collapse, bounded minima and closure/external-tree reports are distinguished from unboundedness. Recomputed all four node/status and edge/role totals and duplicate tree summaries. Guard/round cutoffs do not prove nontermination. Raw isomorphism-equivariant challenge wording remains too broad: least orbit representatives commute only after quotienting, as the native report countercontrol shows. No fresh full-tree or unbounded proof.',
}
common={
 'M01_stake_untransported_request.json':'Three-point parity stake is supplied without the required0/1 transport; independently recomputed matrix differs. Exercises semantic stake transport rather than changing only a status label.',
 'M01_stake_untransported_stdout.json':'Typed STAKE_TRANSPORT_MISMATCH refusal, historical and separately stream-bound.',
 'M02_pi_applied_to_forms_request.json':'Attempts to apply a length-three datum permutation to a zero-form carrier; explicitly ill-typed cross-sort mapping.',
 'M02_pi_applied_to_forms_stdout.json':'Typed FORM_BIJECTION_DIMENSION refusal. This records narrow sort/dimension rejection, not a general certificate theorem.',
 'M03_endpoint_only_request.json':'Same three admitted data reached with or without an inert Supply step; claims one endpoint-derived first count. The extra event changes history index without changing state.',
 'M03_endpoint_only_stdout.json':'Typed ENDPOINT_NOT_FIRST_INDEX refusal with2/3. Correctly retains history-sensitive counterexample to endpoint-only counting.',
 'comparison.json':'Complete three-base summary read;18798rows,16331classes,81610common mappings. Original opaque-token census has no nonidentical token pairs, so supplement is separate. Source/native provided populations and all common-prefix witness maps reconciled earlier; no fresh exhaustive enumerator.',
 'endpoint_witness.json':'Explicit EMPTY404/460 histories end in equal structure but first counts2/3 because Supply adds an event. An endpoint cannot recover this history index; no temporal or causal metaphysics follows.',
 'native_census_request.json':'Seven explicit5x5 stake matrices and injective nine-token opaque map read. total_apart and one_sided_total coincide on this symmetric projection; count seven named stakes does not imply seven distinct tables. Fixed finite task declaration, not universal stake coverage.',
 'transport_valid_request.json':'Positive parity transport control with pi=[1,0,2]. Independently recomputed transported matrix exactly matches the claimed matrix.',
 'transport_valid_stdout.json':'ACCEPTED plus explicit transported matrix. Useful positive counterpart to M01; historical binary execution not freshly authenticated.',
}
for name,note in common.items():
    notes['g04/full_rectangle_v1/'+name]=note
    if name!='comparison.json':notes['g04/full_rectangle_v2/'+name]=note+' Exact raw-byte equality to fully read v1 counterpart verified; this later run has a distinct completion receipt, so payload equality does not transfer execution success backwards.'
for name,note in notes.items():
    p=PREFIX+name;assert sha(ROOT/p)==frozen[p]['sha256']
    rows[p]={'path':p,'sha256':frozen[p]['sha256'],'full_source_read':True,
             'reviewed_lines':[[1,len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())]],
             'assessment':'Complete body read. '+note}
p=PREFIX+'g03/carriers.json'
rows[p]={'path':p,'sha256':frozen[p]['sha256'],'full_source_read':False,'reviewed_lines':[],
         'review_level':'all_carrier_history_and_transform_checks',
         'assessment':'All96 carrier records assessed: independently reconstructed32 base histories; checked unary profiles, exact interior collapse sets, already-satisfied anchor requirements, dimensions and all token-renamed/reversed states. Original histories are base histories, so variant state interpretation requires its explicit transform. No minimum search/canonical quotient or full raw-line reading inferred.',
         'detail_receipt':'dag/reviews/additional_paper_011_history_finite_small_checks.json'}
for row in rows.values():
    if 'Historical G04 helper833583...' in row.get('assessment','') and '/g04/' not in row['path']:
        row['assessment']=row['assessment'].replace('Historical G04 helper833583... is unresolved at its named current and original ZIP path; no fresh hermetic build or source/executable equivalence established.','No fresh hermetic build or source/executable equivalence established.')
report['file_reviews']=sorted(rows.values(),key=lambda r:r['path'])
report['pending_paths']=sorted(set(frozen)-set(rows))
report['validation']=[{'rule':'scoped checks','receipt':'dag/reviews/'+name+'.json','status':'completed'} for name in ['additional_paper_011_history_finite_probes','additional_paper_011_history_finite_data','additional_paper_011_history_finite_receipt_checks','additional_paper_011_history_finite_small_checks']]
report['limits']=['No native binaries, providers, external repositories or private QM answers accessed.',
 'Full source transfers require exact bytes and explicit caller-context review; they do not certify binary runtime identity.',
 'Nine large G03 raw members have complete archive custody checks but no full embedded mathematical replay; canonical partitions and historical exhaustive generation remain bounded by the stated provided-data checks.',
 'Two original source ledgers are delegated separately; review completion awaits their report.']
write(target,report)
print(json.dumps({'full_bodies':sum(x['full_source_read'] for x in rows.values()),'bounded':sum(not x['full_source_read'] for x in rows.values()),'pending':report['pending_paths']}))
