"""Final bounded-slice custody and receipt reconciliation; originals remain read-only."""
import sys,json,re,collections,datetime,subprocess
sys.dont_write_bytecode=True
import additional_challenges_051_059_audit as a

def clean(text):
    text=re.sub(r'\b(all|All|finds|covers|in|on|first|expected|Read all|derives|Derives|public|valid|to|includes|becomes|is|through|and|of)(?=\d)',r'\1 ',text)
    text=re.sub(r'(\d)(lines|cases|vertices|passed|programs|matrices|networks|controls|read|small|one|two)\b',r'\1 \2',text)
    return text
def walk(obj):
    if isinstance(obj,dict):
        if 'owner_verdict' in obj:yield obj['owner_verdict']
        for k,v in obj.items():
            if k not in ('answer','owner_verdict'):yield from walk(v)
    elif isinstance(obj,list):
        for v in obj:yield from walk(v)
def flags(verdict):return [v[0] if isinstance(v,list) and v and isinstance(v[0],bool) else None for v in verdict]
def main():
    scope=a.read('_scope.json');ledger=a.read('_read_ledger.json');notes=a.read('_notes.json')
    # Refresh only a probe whose audit-side strict width classification was improved.
    p=subprocess.run([sys.executable,'-X','utf8',str(a.file('_c058_probe.py'))],capture_output=True,text=True,encoding='utf8',timeout=30)
    assert p.returncode==0,p.stderr
    for r in ledger:r['assessment']=clean(r['assessment'])
    a.write('_read_ledger.json',ledger)
    pins={r['path']:r for r in scope['files']};prior={r['path']:r for r in scope['excluded_already_fully_reviewed']};allpins=pins|prior
    receipts={r['path']:r for r in ledger}
    def evidence(family,suffix):
        matching=[r for r in allpins.values() if ('/'+family.lower()+'_' in r['path'] or '/test_'+family.lower() in r['path']) and r['path'].endswith(suffix)]
        assert len(matching)==1,(family,suffix,len(matching))
        r=matching[0];count=len((a.ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines())
        return {'path':r['path'],'sha256':r['sha256'],'lines':[[1,count]] if count else [],'range_basis':'Whole supporting body; finding assessment identifies the relevant branch.','receipt_basis':'new_full_source_read' if r['path'] in receipts else 'previous_full_review_consulted_without_new_credit','prior_receipts':r.get('prior_receipts',[])}
    mapping={
    'AC51-F01':['reference_solver/simplex.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC51-F02':['reference_solver/simplex.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC52-F01':['reference_solver/solver.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC52-F02':['reference_solver/solver.py','reference_solver/max_flow.py','participant_packet/TASK.md'],
    'AC52-F03':['participant_packet/TASK.md','reference_solver/solver.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC53-F01':['reference_solver/solver.py'],
    'AC53-F02':['participant_packet/TASK.md','reference_solver/solver.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC54-F01':['judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC54-F02':['participant_packet/TASK.md','reference_solver/linear_solver.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC54-F03':['test_c054_replay_custody.py'],
    'AC54-F04':['judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC55-F01':['participant_packet/TASK.md','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC55-F02':['reference_solver/hungarian.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC55-F03':['participant_packet/TASK.md','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC55-F04':['test_c055_replay_custody.py'],
    'AC55-F05':['judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC56-F01':['participant_packet/TASK.md','reference_solver/regex_parser.py'],
    'AC56-F02':['participant_packet/TASK.md','reference_solver/regex_parser.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC56-F03':['participant_packet/TASK.md','reference_solver/solver.py','judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC56-F04':['participant_packet/runner.py'],
    'AC57-F01':['participant_packet/runner.py'],
    'AC57-F02':['judge_packet/exact_checker.py','judge_packet/independent_checker.py'],
    'AC57-F03':['judge_packet/generate_mutations.py'],
    'AC57-F04':['CHALLENGE.md','participant_packet/TASK.md','reference_solver/sorting_network.py']}
    data_summary={};allrows=[]
    for num in range(51,60):
        family='C'+str(num).zfill(3);path=a.file('_'+family.lower()+'_automated.jsonl');rows=[json.loads(l) for l in path.read_text(encoding='utf8').splitlines()]
        for row in rows:
            raw=(a.ROOT/row['path']).read_text(encoding='utf-8-sig');nonfinite=[]
            obj=json.loads(raw,parse_constant=lambda token:(nonfinite.append(token),None)[1])
            checks=[c for c in row['checks'] if c.get('rule')!='strict_json_domain']
            checks.append({'rule':'strict_json_domain','status':'observed','nonfinite_tokens':nonfinite,'rfc8259_number_domain':not nonfinite,'parsed_lines':len(raw.splitlines()),'assessment_range':'Entire JSON parsed; semantic replay bounds are recorded separately. This is not a full source read.'})
            row['checks']=checks
            assert row['full_source_read'] is False and row['sha256']==pins[row['path']]['sha256']
            assert all(isinstance(c,str) or c.get('rule') and c.get('status') for c in checks)
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
        observed=[flags(v) for r in rows for v in walk(r)];mutants=[flags(v) for r in rows if 'hostile_mutations/' in r['path'] for v in walk(r)]
        summary={'data_files':len(rows),'full_source_reads':sum('/'+family.lower()+'_' in r['path'] or '/test_'+family.lower() in r['path'] for r in ledger),'findings':len(next(f for f in notes['family_assessments'] if f['family']==family)['findings']),'dispositions':dict(collections.Counter(r['status'] for r in rows)),'owner_replay_records':len(observed),'owner_replay_records_with_exception':sum(None in v for v in observed),'owner_replay_records_both_accept':sum(len(v)==2 and v==[True,True] for v in observed),'mutation_replays':len(mutants),'mutations_both_accept':sum(v==[True,True] for v in mutants),'mutations_primary_accept':sum(bool(v) and v[0] is True for v in mutants),'mutations_secondary_accept':sum(len(v)>1 and v[1] is True for v in mutants),'nonfinite_json_files':sum(any(c['rule']=='strict_json_domain' and not c['rfc8259_number_domain'] for c in r['checks']) for r in rows),'limits':'Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.'}
        data_summary[family]=summary;allrows.extend(rows)
    conditions={
    'C051':'Rational A,b,c; maximization over x>=0 and Ax<=b. Exact witness inequalities imply optimality/infeasibility/unboundedness; the producer is not complete/correct on all feasible negative-RHS cases.',
    'C052':'A well-formed directed graph with nonnegative integer capacities and distinct source/sink. Feasible flow and an equal-capacity separating cut prove maximality, conditional on binding to original values rather than int-coerced malformed inputs.',
    'C053':'Square rational matrices. A nonzero kernel vector proves singularity; an exact inverse identity proves nonsingularity. Determinant normalization needs its separate exact check. Bareiss divisibility uses an integral scaled matrix and nonzero pivots.',
    'C054':'Rational linear systems with matching dimensions. Feasible x plus independent kernel columns and a nonzero rank minor certify the claimed affine solution space; yA=0 and yb!=0 certify inconsistency.',
    'C055':'Bipartite assignment with exact costs and forbidden edges. A permutation and feasible equal-objective dual prove optimality; Hall deficiency proves no perfect matching. Maximization supports two sign conventions, but current zero-optimum dispatch rejects a valid convention.',
    'C056':'Parsed regular languages over a finite declared alphabet. DFA reachability plus pairwise separating suffixes proves minimality of its recognized language. Exact product/equivalence checks must bind that language to the parsed source regex; tokenization must preserve declared literal symbols.',
    'C057':'Compare-exchange under a total order, with complete binary checks and enforced prefix/forbidden/length constraints. Thresholding proves the zero-one principle. Negative proofs require their exact bound/adjacency assumptions; literature size lower bounds are a trusted external theorem table, not proved by code.',
    'C058':'Well-formed modular bit-vector IR at width 8 permits exhaustive equivalence over all one/two-input assignments. Wide widths are only sampled and have a confirmed false acceptance. Search failure/UNKNOWN is not a general lower-bound theorem.',
    'C059':'Typed finite supplied database instances, explicit bag/heading carrier, and a specified NULL/type-coercion semantics. Finite SQL/AST agreement is instance validation, not universal query equivalence or dialect neutrality. Python/SQLite mixed-value semantics currently disagree.'}
    for fam in notes['family_assessments']:
        family=fam['family'];fam['math']=clean(fam['math']);fam['data']=f"{data_summary[family]['data_files']} JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. " + data_summary[family]['limits']
        fam['limits']=[clean(v) for v in fam['limits']]
        for finding in fam['findings']:
            finding['claim']=clean(finding['claim']);suffixes=finding.get('source_suffixes',mapping.get(finding['id']))
            assert suffixes,finding['id']
            finding['evidence']=[evidence(family,suffix) for suffix in suffixes]
            probe=a.file('_'+family.lower()+'_probes.json');finding['countercontrol_evidence']={'path':str(probe.relative_to(a.ROOT)).replace('\\','/'),'sha256':a.sha(probe),'selector':finding.get('probe_key',finding.get('probe')),'limits':'Offline audit controls; source-only claims are explicitly identified by selector. Controls do not prove all-input correctness.'}
    notes['claims']=[{'id':'AC'+str(n)+'-C01','family':'C'+str(n).zfill(3),'status':'conditional_mathematical_claim_with_implementation_limits','claim':conditions['C'+str(n).zfill(3)],'evidence':[evidence('C'+str(n).zfill(3),s) for s in ('judge_packet/exact_checker.py','judge_packet/independent_checker.py')],'limits':next(f['limits'] for f in notes['family_assessments'] if f['family']=='C'+str(n).zfill(3))} for n in range(51,60)]
    notes['data_summary']=data_summary
    notes['custody']={'provider_calls':0,'source_edits':0,'historical_receipt_edits':0,'paid_models':False,'sealed_material_read':False,'test_temporary_root':'dag/reviews/additional_challenges_051_059*','original_scope_sha256':a.sha(a.file('_scope.json')),'note':'Only new audit artifacts owned by this slice were written. Broader repository audit remains incomplete.'}
    used_prior={e['path'] for f in notes['family_assessments'] for finding in f['findings'] for e in finding['evidence'] if e['receipt_basis'].startswith('previous')}
    notes['supporting_prior_reviews']=[{'path':p,'sha256':prior[p]['sha256'],'prior_receipts':prior[p]['prior_receipts'],'new_reading_credit':False} for p in sorted(used_prior)]
    notes['evidence_artifacts']=[{'path':str(p.relative_to(a.ROOT)).replace('\\','/'),'sha256':a.sha(p)} for p in sorted(a.PREFIX.parent.glob(a.PREFIX.name+'*')) if p.is_file() and (p.suffix=='.py' or p.name.endswith(('_probes.json','_automated.jsonl')))]
    a.write('_notes.json',notes)
    assert len(ledger)==102 and len(allrows)==1138 and len(pins)==1240 and len(prior)==49
    observed={r['path']:r for r in ledger+allrows};assert len(observed)==1240 and set(observed)==set(pins)
    mismatches=[]
    for path,pin in allpins.items():
        current=a.sha(a.ROOT/path)
        if current!=pin['sha256'] or path in observed and current!=observed[path]['sha256']:mismatches.append(path)
    assert not mismatches,mismatches
    for r in ledger:
        count=len((a.ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines());assert r['full_source_read'] and r['reviewed_lines']==([[1,count]] if count else [])
    reconciliation={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':scope['source_commit'],'candidate_files':1289,'excluded_already_fully_reviewed':49,'newly_scoped_files':1240,'full_source_reads':102,'full_source_lines':sum(b-x+1 for r in ledger for x,b in r['reviewed_lines']),'bounded_data_dispositions':1138,'current_hashes_matching_inventory':1289,'hash_mismatches':mismatches,'receipt_duplicates':0,'pending_files':[],'all_automated_check_dicts_have_rule_and_status':True,'data_full_source_reads':0,'findings':sum(len(f['findings']) for f in notes['family_assessments']),'conditional_claims':len(notes['claims']),'limits':['Completion concerns only this frozen remaining-path slice.','Data assessments are bounded parsed dispositions, not full content reading or independent truth labels.','49 prior full-review paths are excluded without duplicate credit.','The repository-wide goal remains incomplete.']}
    a.write('_reconciliation.json',reconciliation);a.report()
    result=a.read('.json');assert not result['remaining_unsupported_files']
    md=['# C051–C059 remaining-path audit','',f"Completed the frozen scope: **102 full source reads (16,932 lines)** and **1,138 bounded parsed-data dispositions** across 1,240 new paths. Forty-nine previously fully reviewed paths were excluded. All 1,289 candidate hashes still match the original inventory. There are {reconciliation['findings']} findings and nine conditional mathematical claims.",'','The repository-wide every-file audit remains incomplete. Parsed JSON and owner replay do not count as full content reading. No original sources, historical receipts, provider services or sealed material were changed or accessed.','',f"Original inventory commit: `{scope['source_commit']}`.",'','| Family | Full bodies | Data dispositions | Findings |','|---|---:|---:|---:|']
    for fam,s in data_summary.items():md.append(f"| {fam} | {s['full_source_reads']} | {s['data_files']} | {s['findings']} |")
    md+=['','## Mathematical scope and findings','']
    for fam in notes['family_assessments']:
        md+=['### '+fam['family'],'',fam['math'],'',fam['data'],'']
        for f in fam['findings']:
            md+=['- **'+f['id']+'** — '+f['claim']]
        md+=['','Limits: '+' '.join(fam['limits']),'']
    md+=['## Checks and custody','', 'The JSON report records exact source paths, SHA256 values and ranges for every body and finding, plus each bounded data assessment. It retains the frozen coverage exclusions and prior receipt references. Full-range evidence identifies the supporting body; probe selectors identify the independent countercontrol.','']
    for test in notes.get('owner_tests',[]):md.append('- '+test['family']+': '+test['result']+'. '+test.get('limits','See structured test receipt for scope')+'.')
    md+=['','Source generators were read; their writing entry points were not run. The C059 root custody test was not rerun. Per-artifact mathematical and parser limits remain explicit, including nonfinite JSON tokens and owner exceptions.','', 'C057 published lower bounds are trusted literature rather than reconstructed proofs: [Harder, 11 and 12 channels](https://arxiv.org/abs/2012.04400) and [Codish et al., nine and ten inputs](https://arxiv.org/abs/1405.5754). Only the abstracts were consulted; stored networks establish construction upper bounds.','','## Full source-reading ledger','']
    for r in ledger:
        ranges=', '.join(f'{x}–{y}' for x,y in r['reviewed_lines']) or 'empty body'
        md+=['### `'+r['path']+'`','',f"SHA256 `{r['sha256']}`; lines {ranges}.",'',r['assessment'],'']
    a.file('.md').write_text('\n'.join(md)+'\n',encoding='utf8')
    print(json.dumps({'reconciliation':reconciliation,'data_summary':data_summary},indent=2))
if __name__=='__main__':main()
