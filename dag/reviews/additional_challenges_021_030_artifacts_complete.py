"""Pin prior artifact outcomes and new finite followups without upgrading their scope."""
import ast,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews';PREFIX='additional_challenges_021_030_artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
scope=load(REV/(PREFIX+'_scope.json'));report=load(REV/(PREFIX+'.json'))
prior_path=REV/'additional_challenges_021_030.json';ledger_path=REV/'additional_challenges_021_030_automated.jsonl'
assert sha(prior_path)=='43a8b2e9f9a149421475b15342295d306c80488bf3ae0252121fb082684aaa58'
assert sha(ledger_path)=='34ee5779b8282a3aa77a50213df0286fface84244681a3d2f37ed738866fd066'
prior=load(prior_path);ledger=[json.loads(line) for line in ledger_path.read_text().splitlines()]
frozen={r['path']:r for r in scope['files']};entries={r['path']:(i+1,r) for i,r in enumerate(ledger)}
assert set(frozen)==set(entries) and len(entries)==len(ledger)==1032
full={r['path']:r for r in report['file_reviews'] if r.get('full_source_read')}
for path,(_,r) in entries.items():
    assert sha(ROOT/path)==r['sha256']==r['inventory_sha256']==frozen[path]['sha256']
    if r['status']=='accounting_template_only':
        raw=(ROOT/path).read_bytes();data=json.loads(raw)
        assert data['calls']==[] and data['total_billed_cost_usd']==data['total_tokens_in']==data['total_tokens_out']==0
        full[path]={'path':path,'sha256':frozen[path]['sha256'],'full_source_read':True,
         'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],
         'assessment':f'Complete accounting template read. Empty calls and zero totals supply no provider run or billing evidence. Historical ceiling USD{data["cost_ceiling_usd"]} is above the requested USD0.10 whole-run cap; USD0.05 is a target only. Prospective adapters must use the shared current ledger and include retries rather than treating these old fields as enforcement or authorization.'}
assert len(full)==27
cnf=load(REV/(PREFIX+'_c027.json'));implementation=REV/(PREFIX+'_c027.py')
assert cnf['implementation_sha256']==sha(implementation)
# Revalidate saved proof trees with only the reviewed pure verifier function.
tree=ast.parse(implementation.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='check_refutation')
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<retained-finite-proof-replay>','exec'),ns)
for case in cnf['cases']:
    assert case['sha256']==frozen[case['path']]['sha256']
    assert hashlib.sha256(json.dumps(case['clauses'],separators=(',',':')).encode()).hexdigest()==case['clauses_sha256']
    assert ns['check_refutation'](case['clauses'],case['merged_ray_count'],case['refutation'])
family_limits={r['id'].split('-')[-1]:{'prior_claim':r['id'],'mathematical_statement':r['claim'],
 'implementation_limits':r['limitations']} for r in prior['claims'] if r['id']!='AC2130-CUSTODY'}
rows=[]
for item in scope['files']:
    path=item['path'];line,r=entries[path];family=path.split('/')[3][:4].upper();status=r['status']
    if path in full:row=dict(full[path])
    else:
        if status=='case_certificate_verified':
            note=f'Prior reference-generated result {r["solver_status"]} passed this family combined checker for the pinned input. This is a finite regression under the reviewed implementation, not an authenticated model response or independent proof of every submitted field.'
        elif status=='mutation_rejected':
            note='Prior combined gate rejected this stored mutant. Its exact reasons remain in the bound ledger; a finite negative fixture cannot establish detector completeness, checker independence or universal soundness.'
        elif status=='mutation_rejected_by_paired_disagreement':
            note='Prior gate rejected because the two checkers disagreed. Preserve that asymmetry; this is not agreement between two independent rejection mechanisms. Some second checkers recompute a value without checking the whole supplied certificate.'
        elif status=='answers_verified':
            note=f'All{len(r["line_reviews"])} retained participant example answers were previously parsed, ID-bound and accepted by the owner checkers. Their exact line outcomes are retained; they are not new model calls and inherit the documented certificate/ingress gaps.'
        elif status=='manifest_bounded_custody_recheck':
            note=f'Prior custody replay under {r["declared_normalization"]} covered{r["entry_count"]} entries with outcomes {r["target_status_counts"]}. Status {r["manifest_status"]} expressly disclaims a pre-run commitment. '
            if r.get('declared_ordered_lines_digest'):note+='Its declared ordered-lines aggregate digest does not match the computed digest. '
            note+='Outside-inventory paths were not opened. These hash/size outcomes are separate from fixture mathematics and do not establish malicious alteration.'
        else:raise AssertionError((path,status))
        row={'path':path,'sha256':item['sha256'],'full_source_read':False,'reviewed_lines':[],
             'review_level':'bounded_contextual_prior_replay_disposition','assessment':note}
    row['detail_receipt']={'path':ledger_path.relative_to(ROOT).as_posix(),'sha256':sha(ledger_path),'line':line,'status':status}
    row['checker_limit_reference']={'report':prior_path.relative_to(ROOT).as_posix(),'sha256':sha(prior_path),'claim_id':family_limits[family]['prior_claim']}
    rows.append(row)
answer_count=sum(len(r.get('line_reviews',[])) for r in ledger)
targets=Counter()
for r in ledger:targets.update(r.get('target_status_counts',{}))
assert answer_count==97 and targets==Counter({'declared_lf_match':1053,'declared_lf_mismatch':156,'unresolved_outside_original_inventory':40})
report.update({'status':'complete_declared_bounded_artifact_dispositions_with_source_reading_limits',
 'file_reviews':rows,'pending_paths':[],
 'source_body_reads_not_completed':[r['path'] for r in rows if not r['full_source_read']],
 'counts':{'scope':1032,'full_body_readings':27,'bounded_prior_replay_dispositions':1005,'pending_dispositions':0,
   'prior_status_counts':dict(Counter(r['status'] for r in ledger)),'participant_answer_records':97,
   'manifest_target_status_counts':dict(targets),'new_exact_C027_refutations':6,'new_C028_invalid_shape_check':1},
 'family_checker_limits':family_limits,
 'limits':['27 complete artifact body readings and1005 bounded per-file dispositions are distinct; not every nested certificate/diagnostic was manually reread.',
 'All11 prior claim/limitation summaries and16 finding statements were consulted. Their original source bodies and replay executions remain attributed to that prior audit.',
 'The new six exact CNF refutations and one shape-invalidity control answer specific verification followups; they do not patch the old checker or change historical outcomes.',
 'Prior481 case passes,514 mutant rejections (including50 disagreements), six unavailable cases and one caught exception remain separately graded.',
 '97 participant answer examples and empty accounting templates are not model-run, token-saving or cost-saving evidence.',
 'No repository source edits, new provider/native executions, outside-inventory historical target access or private benchmark access.']})
for row in rows:
    if row['full_source_read']:assert row['reviewed_lines']==[[1,len((ROOT/row['path']).read_text(encoding='utf-8').splitlines())]]
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
validation={'status':'passed','scope_paths':1032,'current_inventory_ledger_pins':1032,'full_body_receipts':27,
 'bounded_dispositions':1005,'retained_C027_refutations_replayed':6,
 'report_sha256':sha(REV/(PREFIX+'.json')),'prior_report_sha256':sha(prior_path),'prior_ledger_sha256':sha(ledger_path),
 'new_c027_evidence_sha256':sha(REV/(PREFIX+'_c027.json')),'other_controls_sha256':sha(REV/(PREFIX+'_controls.json')),
 'limits':'Custody/range reconciliation and saved finite proof replay; no repeat of original solver/checker campaign.'}
(REV/(PREFIX+'_validation.json')).write_text(json.dumps(validation,indent=2)+'\n')
(REV/(PREFIX+'.md')).write_text('# C021-C030 artifact reconciliation\n\n'
 'All1,032 frozen data paths have explicit dispositions:27 full body readings and1,005 bounded assessments of prior replay receipts. The original236 source/spec/test-body review remains separately attributed.\n\n'
 'Prior outcomes remain481 accepted generated cases,464 rejected mutants,50 mutant rejections through checker disagreement, six independently unavailable cases, one caught exception, ten manifests, ten accounting templates and ten answer collections containing97 records. These are not authenticated model trials.\n\n'
 'Six previously unavailable C027 fixtures now have exact standalone Q(sqrt2) geometry and retained47-node DPLL refutations, replayed deduction by deduction. Five merge to33rays; the60ray case has the same unsatisfiable core. This establishes finite uncolourability under the explicit encoding, without a physics or proof-assistant claim. The original20ray verifier limit remains unchanged.\n\n'
 'The copied C028 mutant supplies12 Majoranas of6qubit width for9modes, independently establishing invalid shape. Its old IndexError remains an exception. Additional finite controls check a tableau pairing, projector idempotence/kernel, an8state number-operator identity and the512candidate syndrome minimum3.\n\n'
 'Manifest checks retain1,053 LF matches,156 mismatches and40 outside-inventory unresolved entries; C021 also has a stale aggregate digest. Templates contain empty calls and zero totals, with old ceilings above USD0.10. Prospective workflows must bind the separate whole-run cap.\n',encoding='utf-8')
manifest_path=ROOT/'dag/swarm_manifest.json';manifest=json.loads(manifest_path.read_text())
path='dag/reviews/'+PREFIX+'.json'
if path not in manifest['completed_followup_slices']:manifest['completed_followup_slices'].append(path)
manifest['parent_active_slice']={'status':'selecting_next_scope','completed_report':path,'scope_files':1032,'full_body_reads':27,'bounded_dispositions':1005}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report['counts']))
