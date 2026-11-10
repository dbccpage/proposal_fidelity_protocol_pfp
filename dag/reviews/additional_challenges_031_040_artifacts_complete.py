"""Close contextual dispositions, preserving owner/replay and mathematical limits."""
from collections import Counter
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews';PREFIX='additional_challenges_031_040_artifacts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
scope=load(REV/(PREFIX+'_scope.json'));report=load(REV/(PREFIX+'.json'))
prior_path=REV/'additional_challenges_031_040.json'
assert sha(prior_path)=='e538fee7cc7f0ceeef7fcaea128e93c83449d94c95bfe553f1dcfa8efdb23e44'
prior=load(prior_path);frozen={r['path']:r for r in scope['files']}
auto={r['path']:(i,r) for i,r in enumerate(prior['automated_reviews'])}
assert len(auto)==len(prior['automated_reviews'])==1012 and set(auto)==set(frozen)
for source in prior['file_reviews']:
    assert sha(ROOT/source['path'])==source['sha256']
for path,item in frozen.items():assert sha(ROOT/path)==item['sha256']==auto[path][1]['sha256']
full={r['path']:r for r in report['file_reviews'] if r.get('full_source_read')};assert len(full)==20
family_limits={c['id'].split('-')[0].replace('AC','C0'):c for c in prior['claims']}
rows=[];roles=Counter();verdicts=Counter();independent=Counter();targets=Counter();manifest_rows=[]
for item in scope['files']:
    path=item['path'];idx,record=auto[path];checks=[c for c in record['checks'] if isinstance(c,dict)]
    assert len(checks)==1
    check=checks[0];role=check['role'];roles[role]+=1
    owner=check.get('owner_verdict',{});verdict=owner.get('verdict');verdicts[(role,str(verdict))]+=1
    ind=check.get('independent');ind_status=ind.get('status') if isinstance(ind,dict) else None
    if ind_status:independent[ind_status]+=1
    family=path.split('/')[3][:4].upper();claim=family_limits[family]
    if path in full:row=dict(full[path])
    else:
        if role in ('judge_case','example_input_only'):
            note=f'Prior offline reference/owner replay returned {verdict} for this exact input. The independent evidence is graded {ind_status}; its actual details remain in the pinned prior report. Input-only examples are not retained participant solutions or authenticated model calls. '
        elif role=='retained_example':
            note=f'Prior retained-answer replay returned {verdict}, with reference equality={check.get("fresh_reference_equal")} and independent grade {ind_status}. Retained example/owner agreement is a finite check, not proof of all certificate fields or scientific interpretation. '
        elif role=='retained_mutant':
            note=f'Prior owner replay returned {verdict} for this stored mutant. Its exact per-checker reasons are retained; this finite negative example does not establish universal rejection, independent implementations or detector adequacy. '
        elif role=='historical_manifest':
            counts=Counter(r['status'] for r in check['references']);targets.update(counts)
            manifest_rows.append({'path':path,'declared_counts':check['declared_count_fields'],'actual_count':check['actual_count'],
                                  'all_declared_counts_match':check['all_declared_counts_match'],'target_outcomes':dict(counts)})
            note=f'Prior historical custody check found {dict(counts)} over{check["actual_count"]} entries. Declared count fields {check["declared_count_fields"]} have agreement={check["all_declared_counts_match"]}. Listed-byte agreement is neither pre-run commitment nor a mathematical/physical certificate. '
        elif role=='retained_answer_stream':
            counts=Counter(r['owner_verdict']['verdict'] for r in check['records'])
            note=f'Prior per-line replay of{len(check["records"])} retained answers recorded{dict(counts)}. The independent grades remain attached to each line; these participant examples are not fresh paid trials. '
        else:raise AssertionError((path,role))
        note+='The family mathematical implications and implementation gaps are retained under '+claim['id']+'; use only those stated premises.'
        row={'path':path,'sha256':item['sha256'],'full_source_read':False,'reviewed_lines':[],
             'review_level':'bounded_contextual_assessment_of_prior_record','assessment':note}
    row['detail_receipt']={'path':prior_path.relative_to(ROOT).as_posix(),'sha256':sha(prior_path),
      'json_pointer':'/automated_reviews/'+str(idx),'role':role,'owner_verdict':verdict,'independent_grade':ind_status}
    row['checker_limit_reference']=claim['id'];rows.append(row)
assert targets==Counter({'raw_match':956})
assert roles==Counter({'retained_mutant':479,'judge_case':420,'retained_example':50,'example_input_only':42,
                       'historical_manifest':10,'budget_configuration_only':9,'empty_accounting_template':1,'retained_answer_stream':1})
reconciliation={'status':'custody_and_prior_record_attribution_pass','prior_report_sha256':sha(prior_path),
 'current_artifact_source_pins':1012,'prior_source_owner_pins':len(prior['file_reviews']),
 'role_counts':dict(roles),'owner_outcomes':[{'role':role,'verdict':verdict,'files':count} for (role,verdict),count in verdicts.items()],
 'independent_evidence_grades':dict(independent),'manifests':manifest_rows,
 'limits':['Completed_with_stated_limits describes an audit procedure, not scientific success or a universally sound checker.',
           'All original owner replays remain prior evidence, with their positive/refusal/partial-independence distinctions intact.']}
(REV/(PREFIX+'_reconciliation.json')).write_text(json.dumps(reconciliation,indent=2)+'\n')
report.update({'status':'complete_declared_bounded_artifact_dispositions_with_source_reading_limits','file_reviews':rows,'pending_paths':[],
 'source_body_reads_not_completed':[r['path'] for r in rows if not r['full_source_read']],
 'family_checker_limits':{k:{'prior_claim_id':v['id'],'statement':v['claim'],'limitations':v['limitations']} for k,v in family_limits.items()},
 'counts':{'scope':1012,'full_body_readings':20,'bounded_prior_record_dispositions':992,'pending_dispositions':0,
           'prior_roles':dict(roles),'prior_manifest_targets':dict(targets)},
 'claims':[{'id':'CAP-C01','statement':'The public n5/bound9 charge fixture has exactly one canonical solution under the stated nonzero/gcd/non-vector-like/global-sign convention: (-9,-5,-1,7,8). Independent enumeration covers all26334 sorted multisets. This finite arithmetic result does not establish completeness at another bound or a stricter chirality definition.',
  'source_evidence':[{'path':r['path'],'sha256':r['sha256']} for r in rows if r['full_source_read'] and '/base_enum_01_n5_b9.json' in r['path']],
  'validation':'dag/reviews/'+PREFIX+'_controls.json'},
 {'id':'CAP-C02','statement':'Selected finite controls independently reproduce simplex lattice counts(6,126), three path4 transport optima1, and RP2 mod2 boundary ranks(0,0). The associated Hodge/GV and physical interpretations retain the explicit formula/model admissions; matching finite arithmetic does not derive the larger theories.',
  'source_evidence':[{'path':r['path'],'sha256':r['sha256']} for r in rows if r['full_source_read'] and any(t in r['path'] for t in ('base_01_quintic_4simplex','base_11_octic_d01','base_21_graph_path4_alpha0','base_17_surface_rp2_1v_cw'))],
  'validation':'dag/reviews/'+PREFIX+'_controls.json'}],
 'limits':['Twenty complete artifact bodies and992 bounded prior-record assessments are distinct; nested certificates and every diagnostic were not all manually reread.',
 'All10 prior mathematical summaries and35 finding statements consulted;199 previously reviewed owner/spec/test hashes revalidated, without rerunning their code.',
 '420 judge cases,50 retained examples and42 input examples have prior owner PASS, including valid refusals and conditional results. These are not512 independent successful model solves.',
 '479 stored mutants have prior owner FAIL; local coverage does not eliminate the documented accepted counterexamples.',
 '956 listed manifest byte matches retain two inconsistent count fields; there is no automatic inference of pre-run commitment.',
 'No original source edit, paid/model/provider/native execution or private benchmark access.']})
for r in rows:
    if r['full_source_read']:assert r['reviewed_lines']==[[1,len((ROOT/r['path']).read_text(encoding='utf-8').splitlines())]]
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
validation={'status':'passed','scope_paths':1012,'original_artifact_pins':1012,'prior_full_source_owner_pins':199,
 'full_body_reading_receipts':20,'bounded_record_dispositions':992,'report_sha256':sha(REV/(PREFIX+'.json')),
 'prior_report_sha256':sha(prior_path),'controls_sha256':sha(REV/(PREFIX+'_controls.json')),
 'limits':'Custody/range/record-attribution checks and separately stated finite arithmetic only; not broad proof or empirical workflow efficacy.'}
(REV/(PREFIX+'_validation.json')).write_text(json.dumps(validation,indent=2)+'\n')
(REV/(PREFIX+'.md')).write_text('# C031-C040 artifact reconciliation\n\n'
 'All1,012 frozen artifact paths have explicit dispositions:20 full body readings and992 bounded contextual assessments. The earlier199 owner/spec/test readings remain separately attributed and hash-matched.\n\n'
 'Prior replay includes420 judge cases,50 retained examples and42 example inputs with owner PASS;479 stored mutants with FAIL; ten manifests; ten accounting/configuration files; and one12-answer stream. PASS includes bounded refusals and conditional calculations. None of these counts establishes authenticated model performance.\n\n'
 'Independent small controls cover all26,334 sorted charge multisets for the n5/bound9 request, simplex lattice points, the admitted octic first-order formula, exact path transport certificates and an RP2 mod2 boundary calculation. These retain their formula/carrier/physical-model assumptions.\n\n'
 'The ten manifests have956 raw target matches, while C038/C039 retain inconsistent declared count fields. Historical budget/sandbox/model labels are declarations. The current USD0.10 whole-run ledger remains the prospective budget owner.\n',encoding='utf-8')
manifest_path=ROOT/'dag/swarm_manifest.json';manifest=load(manifest_path);path='dag/reviews/'+PREFIX+'.json'
if path not in manifest['completed_followup_slices']:manifest['completed_followup_slices'].append(path)
manifest['parent_active_slice']={'status':'selecting_next_scope','completed_report':path,'scope_files':1012,'full_body_reads':20,'bounded_dispositions':992}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report['counts']))
