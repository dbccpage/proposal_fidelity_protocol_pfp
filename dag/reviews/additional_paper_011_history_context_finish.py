"""Finish the 29-file historical-context slice without promoting dataset parsing to body review."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
path=REV/'additional_paper_011_history_context.json'; report=read(path)
scope=read(REV/'additional_paper_011_history_context_scope.json'); frozen={x['path']:x for x in scope['files']}
data=read(REV/'additional_paper_011_history_context_data.json')
archive=read(REV/'additional_paper_011_history_context_archive_line_deltas.json')
assert len(archive['rows'])==28 and all(x['archive_matches_recorded_hash'] for x in archive['rows'])
assert archive['changed_line_pairs']==95
rows={x['path']:x for x in report['file_reviews']}
assessments={
 'demo10_input_location_accounting.json':'All six historical path/blob/SHA/size records inspected for internal agreement. The referenced old and possible relocated source paths are absent in this checkout; external source repository was not accessed. These are historical source-location declarations, not evidence of missing files caused by the current migration or current checker success.',
 'external_pin_availability.json':'All107 literal path records,176 pin/path statuses,25 local specification bindings and169 line references checked. Counts reproduce18 sealed blobs/1 tree/50 missing,52 research blobs/17 trees, and23 H3 blobs/15 trees. All169 anchors remain at their declared lines, but none of25 local spec digests match even after LF normalization. External Git objects were not opened; availability is not theorem or complete dependency closure verification.',
 'genesis_replay.json':'All25 IDs/status/Lean metadata rows reconciled with the retained master report. All75 falsifier input hashes,75 source section texts and false positive-obligation flags checked. Selected AST hashes inspected on Python3.12.14: six of seven match; ArtifactVerifier changes a renamed crate string. Historical harness, report and recovery-manifest byte bindings fail even after LF normalization. The fresh isolated controls independently reproduce the constant-True checker, not the historical model experiment.',
 'recovery_manifest.json':'All28 path/size/SHA/Git-blob declarations and aggregate324333 recorded bytes checked. Current raw matches0/28; LF-normalized and Git-blob matches1/28. All28 corresponding ZIP members exactly match the recorded SHA values, including the explicit g25 omega-to-core filename mapping. Current/archive95 changed line pairs were compared; complete changed substrings are naming/path replacements. The original archive remains recoverable; the rewritten files are not identical historical originals.',
 'recovered_sources/results/genesis_master_report.json':'All25 IDs, statuses, relations, Lean metadata, nonnegative finite token/cost/latency fields and totals checked. Eleven CHECKED rows comprise6 timeouts,2 failures and3 absent proofs; none compiled. All25 artifact flags are True.34,537 input and9,460 output tokens yield0.00698244USD at the historical fixed tariff; stored total differs by floating-point rounding only. Summed declared call latency369.787s excludes other workflow overhead. No raw reply/proof fields are retained; current text also includes historical naming substitutions. These records do not establish billed cost or mathematical capability.',
}
for name,assessment in assessments.items():
    p=PREFIX+name
    rows[p]={'path':p,'sha256':sha(ROOT/p),'full_source_read':False,'reviewed_lines':[],
             'review_level':'all_declared_rows_schema_bindings_and_explicit_semantic_limits',
             'assessment':assessment,'detail_receipt':'dag/reviews/additional_paper_011_history_context_data.json'}
for p,row in rows.items():
    assert row['sha256']==sha(ROOT/p)==frozen[p]['sha256']
    if row['full_source_read']:assert row['reviewed_lines']==[[1,len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())]]
assert set(rows)==set(frozen) and sum(x['full_source_read'] for x in rows.values())==24
def ev(name):return {'path':PREFIX+name,'sha256':sha(ROOT/(PREFIX+name))}
findings={x['id']:x for x in report['findings']}
findings['PAPER011-HISTORY-RECOVERED-BYTE-DRIFT']={
 'id':'PAPER011-HISTORY-RECOVERED-BYTE-DRIFT',
 'statement':'The28-file recovery manifest matches0 current raw files and only1 after LF normalization; all28 corresponding ZIP members match its original hashes. Ninety-five current/archive line pairs change naming and paths, including retained result prose and two harness lines. These rewritten copies cannot support an assertion of unchanged historical source or provider text. The archive preserves the originals.',
 'evidence':[PREFIX+'recovery_manifest.json',PREFIX+'recovered_sources/run_genesis_suite.py',PREFIX+'recovered_sources/results/genesis_master_report.json'],
 'source_evidence':[ev('recovery_manifest.json'),ev('recovered_sources/run_genesis_suite.py'),ev('recovered_sources/results/genesis_master_report.json')],
 'recommended_action':'Retain original archive bytes and explicit transformation provenance; issue fresh receipts for adapted source instead of silently reusing historical hashes.'}
report['findings']=list(findings.values())
report['claims']=[
 {'id':'PAPER011-HISTORY-FINITE-FACTORIZATION','statement':'For fixed finite states X, an observable signature s:X->S and target f:X->Y, f factors through s exactly when f is constant on every s-fiber. A full finite grouping certifies that property on X; two equal-signature states with different targets refute it.',
  'evidence':[PREFIX+'recovered_sources/g18_x6_definability_census_rows.md'],'source_evidence':[ev('recovered_sources/g18_x6_definability_census_rows.md')],
  'status':'classical_conditional_mathematics_underlying_planned_protocol',
  'dependencies':['Fixed finite state rectangle, signature and target functions','Complete enumeration or explicit collision witness'],
  'limits':'Necessity follows by substitution; sufficiency defines the quotient function on each occupied signature. No actual foreign census or universal definability proof performed here.'},
 {'id':'PAPER011-HISTORY-SHORTEST-PATH-BOUND','statement':'For a fixed transition relation, every valid path from s to t of length L gives global shortest distance d(s,t)<=L. Restricting the search may miss shorter routes but does not invalidate this upper bound; equality requires an independent no-shorter-path argument.',
  'evidence':[PREFIX+'recovered_sources/g22_h3v7n5qf_a_perform_lower_bound.md'],'source_evidence':[ev('recovered_sources/g22_h3v7n5qf_a_perform_lower_bound.md')],
  'status':'direct_order_argument_with_small_graph_countercontrol',
  'dependencies':['A replayable path in the same declared transition system','Path length is the same nonnegative cost measure'],
  'limits':'The control has restricted minimum3 and global minimum2, so3 remains an upper bound. No claim about the actual external17:O3 theorem or global equality.'},
]
report.update(status='context_partition_complete_with_bounded_data_limits',file_reviews=sorted(rows.values(),key=lambda x:x['path']),pending_paths=[],
              scope_summary={'assigned':29,'full_source_bodies':24,'bounded_data_artifacts':5,'recovered_archive_members_digest_checked':28,'archive_current_changed_line_pairs':95},
              validation=[{'rule':'isolated_historical_harness_countercontrols','receipt':'dag/reviews/additional_paper_011_history_context_probes.json','status':'reproduced'},
                          {'rule':'all_dataset_rows_and_local_bindings','receipt':'dag/reviews/additional_paper_011_history_context_data.json','status':'completed_with_recorded_drift'},
                          {'rule':'recovered_archive_current_deltas','receipt':'dag/reviews/additional_paper_011_history_context_archive_line_deltas.json','status':'all28_original_hashes_match_95_line_pair_deltas_inspected'},
                          {'rule':'all29_frozen_source_hashes','status':'unchanged'}],
              limits=['Historical task/PR/approval instructions treated as data, not current directions.','No paid model call, secret/private QM answer access, external Git access or native build.','Dataset admission is bounded review, not full proof-text or external source review.','Historical run labels are not mathematical validation; no raw model/proof replay is possible from these entries.','Whole Paper011, archive and repository review remain unfinished.'])
write(path,report)
md='''# Paper011 historical-context review

The29-file context slice is complete:24 full source/prose bodies and5 bounded datasets. The planned tasks contain useful mechanisms—fixed-statement proofs, exact finite census, replayable paths, quotient/fiber checks, explicit translations and matched-budget ablations. They do not implement those mechanisms merely by describing them, and their historical per-arm budgets do not satisfy the new0.10USD whole-workflow ceiling.

The retained batch harness is a negative control. Fresh isolated calls reproduce75 empty, wrong-task and UNKNOWN submissions all receiving artifact success. Wording gates and permissive JSON extraction also fail their intended boundaries. CHECKED survives failed or absent Lean; process success alone is labeled core_clean without an axiom census. The budget ledger accepts overspend and negative token counts in isolated controls. No provider was invoked.

All25 historical result rows were reconciled. Eleven CHECKED labels have6 Lean timeouts,2 failures and3 absent proofs, with zero compiled proofs. Reported34,537 input/9,460 output tokens reproduce the old0.00698244USD tariff to floating-point precision, not provider-billed spend. Raw responses and submitted proof snippets were not retained. Six claimed demo-input source locations refer outside the present checkout and were not reopened; this is not evidence of a failed migration.

G22 contains a mathematical direction error: every valid path is already an upper bound on the global shortest path. An outside shortcut invalidates equality, not that bound. The small graph control records restricted distance3 and unrestricted distance2. G18's useful foundation is the classical finite factorization criterion: a target descends to an observable signature exactly when it is constant on each fiber.

Current recovered files differ from their historical byte records:0/28 raw and1/28 LF-normalized matches. All28 corresponding ZIP members match the recorded original hashes. Ninety-five changed line pairs consist of naming/path substitutions, including retained result text. They do not erase the harness defects, but rewritten copies must not be represented as untouched historical artifacts. All75 cited specification sections and169 external-reference line anchors remain locatable. External Git objects, proofs and runtimes were not replayed.

These reviews preserve useful test designs and explicit counterexamples; they supply no evidence that PFP/EIS/PCIV/operads improve model performance. The other Paper011 partitions and the repository-wide review remain open.
'''
(REV/'additional_paper_011_history_context.md').write_text(md,encoding='utf-8')
write(REV/'additional_paper_011_history_context_final_validation.json',{'status':'passed_context_accounting_only','source_hashes_unchanged':29,'full_bodies':24,'bounded_artifacts':5,'claims':2,'findings':len(report['findings']),
      'report_sha256':sha(path),'scope_sha256':sha(REV/'additional_paper_011_history_context_scope.json'),'whole_paper_review_complete':False})
swarm_path=ROOT/'dag/swarm_manifest.json';swarm=read(swarm_path)
done='dag/reviews/additional_paper_011_history_context.json'
if done not in swarm['completed_followup_slices']:swarm['completed_followup_slices'].append(done)
swarm['parent_active_slice'].update(status=report['status'])
write(swarm_path,swarm)
print(json.dumps(report['scope_summary']))
