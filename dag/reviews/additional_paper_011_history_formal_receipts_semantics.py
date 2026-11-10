"""Read-only bounded semantic/custody reconciliation of retained formal-history data."""
import sys,json,re,hashlib,collections,itertools,zipfile,copy
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_data as d
a=d.a;H=d.HIST;P=d.PAPER
autos=a.read('_automated.json');by={r['path']:r for r in autos};details=[]
def path(s):return H+s
def obj(s):return json.loads(d.RAW[path(s)].decode('utf-8-sig'))
def tape(s):return d.RAW[path(s)].decode('utf8')
def add(s,rule,status='verified',assessment=None,**kw):
    p=path(s) if not s.startswith(P) else s
    by[p]['checks'].append(d.check(rule,status,**kw))
    if assessment:by[p]['assessment']=assessment
def mark(s,key):
    ms,errors=d.markers(d.RAW[path(s)]);assert not errors and len(ms[key])==1
    return ms[key][0]['value']
def gh(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def canonical_key(n,arity,args,req):
    return min([n,[arity],[[0,[p[i] for i in args]]],[],[sorted([p[req[0]],p[req[1]]])]] for p in itertools.permutations(range(n)))
def separates(n,args,req):
    for slots in itertools.product([None,*range(n)],repeat=len(args)):
        if None not in slots:continue
        lhs=tuple(req[0] if s is None else s for s in slots)==args
        rhs=tuple(req[1] if s is None else s for s in slots)==args
        if lhs!=rhs:return True
    return False
def finite(x):
    r=x['request'];assert set(r)=={'reading','measure','max_items','max_arity'} and r['max_items']==r['max_arity']==2 and r['reading'] in ('L','F') and r['measure'] in ('mu1','mu2')
    n=2 if r['reading']=='L' else 3;req=(0,1) if n==2 else (1,2)
    allvalid={(arity,args) for arity in (1,2) for args in itertools.product(range(n),repeat=arity) if separates(n,args,req)}
    expected={v for v in allvalid if r['measure']=='mu1' or v[0]==1}
    observed=set();refined=collections.defaultdict(set);brute=collections.defaultdict(set)
    for row in x['deltas']:
        items=row['items'];assert len(items)==2 and items[0]['kind']=='form' and items[1]['kind']=='inst' and items[1]['form']==0
        v=(items[0]['arity'],tuple(items[1]['args']));assert v not in observed;observed.add(v)
        key=canonical_key(n,*v,req);assert row['brute_key']==key
        refined[d.canon(row['key'])].add(v);brute[d.canon(key)].add(v)
    assert observed==expected and {frozenset(x) for x in refined.values()}=={frozenset(x) for x in brute.values()}
    cls={d.canon(r['key']):r['size'] for r in x['classes']};assert len(cls)==len(x['classes']) and cls=={k:len(v) for k,v in refined.items()}
    assert x['cost']==([2,-1] if r['measure']=='mu1' else [2,1])
    if 'unpruned_valid_count' in x:assert x['unpruned_valid_count']==len(allvalid)
    return {'minimum_rows':len(expected),'all_valid_two_item_rows':len(allvalid),'classes':len(brute),'class_sizes':sorted(map(len,brute.values())),'partition':{k:sorted([[arity,list(args)] for arity,args in v]) for k,v in brute.items()}}
def main():
    zpath=a.ROOT/(P+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip');assert a.sha(zpath)=='8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3'
    archive_checks=[]
    with zipfile.ZipFile(zpath) as z:
        names=set(z.namelist())
        def archived(p):
            member='021_recreated_demos_and_proposal_fidelity_evidence/'+p[len(P):]
            if member not in names:return None
            return z.read(member)
        for family in ('g01','g02','g12'):
            s=family+'/source_manifest.json';m=obj(s);rows=m['files']+([m['sealed_iso_source']] if 'sealed_iso_source' in m else [])
            checks=[]
            for r in rows:
                rel=r.get('recovered_path',r.get('path','')).replace('\\','/')
                t=d.mapped(rel,path(s)) or P+rel
                assert t.startswith((P+'code/native_genesis_',H)) and '..' not in t.split('/')
                original=archived(t);current=(a.ROOT/t).read_bytes() if (a.ROOT/t).is_file() else None
                if t in d.INV:assert d.digest(current)==d.INV[t]['sha256']
                options=([('current_raw',current),('current_lf',current.replace(b'\r\n',b'\n'))] if current is not None else [])+([('original_zip',original)] if original is not None else [])
                matches=[{'representation':label,'sha256_match':d.digest(b)==r['sha256'],'git_blob_match':gh(b)==r.get('git_blob'),'length_match':len(b)==r.get('bytes',r.get('raw_bytes'))} for label,b in options]
                checks.append({'target':t,'expected_sha256':r['sha256'],'expected_git_blob':r.get('git_blob'),'comparisons':matches})
            add(s,'manifest_recovered_byte_and_git_blob_binding',status='observed',files=len(checks),bindings=checks,assessment='Complete manifest-row parse with exact recovered bytes, lengths, SHA256 and Git blob-object SHA1 recomputed across current raw, LF and available original ZIP representations. This checks byte-to-blob consistency, not remote commit/tree membership or historical execution. Dependencies are consulted only for custody; their body review remains in the native/context lanes.')
            archive_checks.extend(checks)
        machinery=obj('g01/execution_machinery_theorem_v3_native_v2/receipt.json')
        links=[]
        for r in machinery['files']:
            t=d.mapped(r['snapshot'],path('g01/execution_machinery_theorem_v3_native_v2/receipt.json'));b=archived(t);assert b is not None
            links.append({'target':t,'current_match':d.digest(d.RAW[t])==r['sha256'],'original_zip_match':d.digest(b)==r['sha256']})
        assert all(x['original_zip_match'] for x in links)
        add('g01/execution_machinery_theorem_v3_native_v2/receipt.json','six_execution_machinery_snapshots',bindings=links,assessment='Six dated machinery snapshots bind exactly to original ZIP bytes. Current Rust/runner imports were renamed; the snapshot explicitly predates full-partition finite normalization. It cannot alone reproduce the later finite receipt with its old direct refined-key comparison.')
        # Every referenced mapped dependency is checked against the same ZIP member when available;
        # failing that, a same-byte retained historical source attempt is explicitly distinguished.
        historical_hashes=collections.defaultdict(list)
        for r in a.read('_scope.json')['files']:
            historical_hashes[r['sha256']].append(r['path'])
            b=archived(r['path'])
            if b is not None:historical_hashes[d.digest(b)].append(r['path']+' [original ZIP]')
        for entry in autos:
            for ch in entry['checks']:
                if ch['rule']=='mapped_path_hash_links':
                    for link in ch['links']:
                        orig=archived(link['target'])
                        link['mapped_target_original_zip_match']=orig is not None and d.digest(orig)==link['expected']
                        if not(link['raw_match'] or link['lf_match'] or link['mapped_target_original_zip_match']):link['retained_same_hash_historical_versions']=sorted(set(historical_hashes.get(link['expected'],[])))
    # Embedded provenance text is byte-hashable without trusting historical metadata.
    prov=obj('g01/claim_ledger_provenance.json');b=prov['raw_template_utf8'].encode();add('g01/claim_ledger_provenance.json','embedded_claim_template',sha256_match=d.digest(b)==prov['sha256'],git_blob_match=gh(b)==prov['git_blob'],statuses=prov['statuses_used'],assessment='Embedded scaffold template bytes and Git blob identity recomputed. PROVED_THEOREM and VERIFIED_FINITE are vocabulary from the template; using those labels does not itself prove any claim or authenticate commit membership.')
    prov=obj('g01/toolchain_provenance.json');checks=[]
    for r in prov['originals']:
        b=r['raw_bytes_utf8'].encode();checks.append({'path':r['path'],'sha256_match':d.digest(b)==r['sha256'],'git_blob_match':gh(b)==r['git_blob']})
    add('g01/toolchain_provenance.json','embedded_toolchain_text',bindings=checks,assessment='Two embedded original toolchain/package text captures have recomputed SHA256 and Git blob hashes. The owned-package byte-equality flag is a historical assertion; installed compiler executable behavior is not established by these tiny text pins.')
    # G01 exact finite census and full class membership, independent of either supplied implementation.
    finite_summaries=[]
    for folder,prefixes in [('g01/finite_run_v2/',['F_mu1_','F_mu2_','L_mu1_','L_mu2_']),('g01/finite_disagreement_diagnostic_v1/',[''])]:
        for prefix in prefixes:
            py=obj(folder+prefix+'python.json');native=json.loads(tape(folder+prefix+'stdout.bin'));req=obj(folder+prefix+'request.json')
            q=finite(py);n=finite(native);assert q==n and py['request']==native['request']==req
            refined_equal={d.canon(r['items']):r['key'] for r in py['deltas']}=={d.canon(r['items']):r['key'] for r in native['deltas']}
            summary={'folder':folder,'prefix':prefix,'request':req,**{k:v for k,v in q.items() if k!='partition'},'python_native_full_partition_equal':True,'refined_representative_bytes_equal':refined_equal}
            finite_summaries.append(summary)
            for suffix in ('python.json','stdout.bin','request.json'):
                add(folder+prefix+suffix,'independent_finite_augmentation_census',**summary,assessment='Independently enumerated all positive arity<=2 form/instance two-item responses from the supplied L/F regime, every finite hole context and every datum permutation. Exact candidate set, minimal cost, brute canonical keys, full refined/brute partitions and class sizes agree. Distinct refined representatives are expected serialization differences. Bounded finite evidence only; no all-arity completeness or physical forcing claim.')
    assert [q['classes'] for q in finite_summaries[:4]]==[5,1,3,1]
    mutant=copy.deepcopy(obj('g01/finite_run_v2/F_mu1_python.json'));mutant['deltas'][0]['brute_key']=mutant['deltas'][2]['brute_key']
    try:finite(mutant)
    except AssertionError:negative_detected=True
    else:negative_detected=False
    assert negative_detected
    for s in ('g01/finite_run_v2/receipt.json','g01/result.json'):add(s,'independent_four_row_finite_crosscheck',rows=finite_summaries[:4],equal_count_wrong_key_control_rejected=True)
    # G01 census, pins, axioms and solve records correspond to the same parsed judge output.
    census=obj('g01/theorem_run_v3/census.json');ax=obj('g01/theorem_run_v3/axioms.json');pins=obj('g01/theorem_run_v3/pins.json');solve=obj('g01/solve.json')['records']
    c={r['name']:r for r in census};assert len(c)==len(census)==100 and len(ax)==90 and len(pins)==11
    assert {r['name'] for r in ax}=={k for k,v in c.items() if v['is_theorem'] is True}
    assert all(set(r['axioms'])<= {'propext','Quot.sound'} and r['type']==c[r['name']]['type'] and r['axioms']==c[r['name']]['axioms'] for r in ax)
    pp={r['goal']:r for r in pins};assert len(pp)==11 and all(r['matched'] is True and r['proof'] in c for r in pins)
    assert len(solve)==11 and len({r['target'] for r in solve})==11
    for r in solve:assert r['goal_type']==pp[r['frozen_goal']]['type'] and r['lean_names']==[pp[r['frozen_goal']]['proof']]
    markers={'G01_CENSUS':census,'G01_AXIOMS':ax,'G01_PINS':pins}
    for key,expected in markers.items():assert mark('g01/theorem_run_v3_judge_stdout.txt',key)==expected
    for s in ('g01/theorem_run_v3/census.json','g01/theorem_run_v3/axioms.json','g01/theorem_run_v3/pins.json','g01/theorem_run_v3_judge_stdout.txt','g01/solve.json','g01/theorem_run_v3/receipt.json','g01/result.json'):
        add(s,'g01_census_axioms_pins_solve_and_stream',census_constants=100,theorems=90,distinct_pins=11,status_counts=dict(collections.Counter(r['status'] for r in solve)),axioms=['propext','Quot.sound'],assessment='Parsed 100 distinct environment constants, the same 90 theorem/type/axiom rows, 11 literal matched pins and 11 solve records; all agree with the retained judge marker payloads. Eight solved obligations and three OUT_OF_SCOPE poison refusals are not interchangeable. The F5 type supplies five pairwise nonisomorphic witnesses, not a Lean upper bound. Historical consistency, not fresh kernel validation or model-arm success.')
    mut=obj('g01/theorem_run_v3/mutations.json');assert len(mut)==8 and sum(r['accepted'] is False for r in mut)==7 and sum(r['accepted'] is True for r in mut)==1
    for r in mut:
        if r.get('process'):
            proc=r['process'];s=d.mapped(proc['stdout_path'],path('g01/theorem_run_v3/mutations.json'));text=d.RAW[s].decode()
            assert proc['returncode']==(0 if r['accepted'] else 1)
            if r.get('expected_gate_error'):assert r['expected_gate_error'] in text
    add('g01/theorem_run_v3/mutations.json','mutation_outcomes_and_error_markers',rejected=7,accepted=1,assessment='All eight controls parsed: four raw lexical refusals, three compiled rejection markers (native oracle axiom, Classical.choice, extra-False type drift), and one accepted exact-type control. Specific expected errors occur in their paired tapes; process return codes alone are not the rejection proof.')
    lex=obj('g01/lexical_guard_supplement_v1/receipt.json');assert len(lex['rows'])==lex['controls_passed']==8
    for r in lex['rows']:
        p=d.mapped(r['path'],path('g01/lexical_guard_supplement_v1/receipt.json'));text=d.RAW[p].decode();hits=[t for t in ('sorry','axiom','partial') if re.search(r'\b'+t+r'\b',text)]
        assert sorted(hits)==sorted(r['hits']) and bool(hits)==r['expected_rejection'] and r['control_passed'] is True
    add('g01/lexical_guard_supplement_v1/receipt.json','raw_lexical_comment_controls',controls=8,assessment='All five comment-only forbidden-token controls and three complete valid sources independently scanned with word boundaries; recorded hits, expected refusal and positive preservation agree. This is the declared lexical policy, not evidence that comments contain logical axioms or proof holes.')
    # G02 complete retained request/response/census compared to independent formula under the exact input domain.
    req=obj('g02/final_v3/native_request.json')['cases'];out=json.loads(tape('g02/final_v3/bitmask_census_stdout.bin'))['cases'];rows=obj('g02/final_v3/census_rows.json')
    assert len(req)==len(out)==1016 and len(rows)==1014 and len({r['case_id'] for r in req})==1016
    expected={(n,aa,bb) for n in range(13) for aa in range(n+2) for bb in range(n+2)};assert {(r['n'],r['a'],r['b']) for r in rows}==expected
    for q,r,x in zip(req[:1014],rows,out[:1014]):
        n,aa,bb=q['n'],q['a'],q['b'];count=0 if aa>=n or aa==bb else 2**(n-1) if bb>=n else 2**(n-2)
        assert q['case_id']==r['case_id']==x['case_id'] and x['success'] is True and r['source_sublist_count']==count and r['native_count']==str(count) and x['result']['count']==str(count) and x['result']['visited_bitmasks']==r['subsets_enumerated_per_route']==2**n
    assert [(x['case_id'],x['error'],x['success']) for x in out[-2:]]==[('TOO_LARGE','CARRIER_LIMIT_12',False),('FLOAT_CARRIER','NATURAL_N_REQUIRED',False)]
    for s in ('g02/final_v3/native_request.json','g02/final_v3/census_rows.json','g02/final_v3/bitmask_census_stdout.bin','g02/final_v3/receipt.json','g02/result.json'):
        add(s,'g02_exact_grid_and_domain_counts',finite_cases=1014,explicit_refusals=2,assessment='All 1014 unique (n,a,b) cases cover exactly n=0..12,a,b=0..n+1. Request IDs, recursive counts, native decimal counts and 2^n enumeration sizes agree with the independent formula including equal/outside/zero-carrier cases. Carrier 13 and floating n are explicit refusals. This bounds the native census; the general all-n theorem remains conditional on in-range distinct targets.')
    ax=obj('g02/final_v3/actual_axiom_reports.json');assert len(ax)==52 and len({r['name'] for r in ax})==52 and sum(r['public_target'] is True for r in ax)==13
    assert all(set(r['axioms'])<={'propext','Quot.sound'} for r in ax) and mark('g02/final_v3/clean_lake_build_stdout.bin','G02_REPORTS')==ax
    for s in ('g02/final_v3/actual_axiom_reports.json','g02/final_v3/clean_lake_build_stdout.bin','g02/final_v3/receipt.json'):
        add(s,'g02_report_and_build_marker_binding',theorem_reports=52,public_targets=13,all_recorded_axioms_whitelisted=True)
    for folder in ('g02/final_v3/','g02/mutation_custody_v1/'):
        muts=obj(folder+'mutation_results.json');assert len(muts)==6 and len({r['mutation'] for r in muts})==6
        for r in muts:
            assert r['compile_returncode']==0 and set(r['disallowed_axioms'])==set(r['actual_axioms'])-{'propext','Quot.sound'}
            assert r['outcome']==('ACCEPTED' if r['mutation']=='valid_control' else 'REJECTED')
            if r['mutation']=='narrowed_pin':assert r['pin_returncode']==1
            if r['mutation']=='valid_control':assert r['pin_returncode']==0
        add(folder+'mutation_results.json','six_mutation_outcome_semantics',negative_controls=5,positive_controls=1,assessment='All six candidates compiled; refusal is supplied by the separate lexical, axiom or exact-type gate. native_decide and replacement_correct carry disallowed dependencies; sorry-in-comment and open Classical compile with permitted axioms but violate raw policy; narrowed n>=4 proof fails the n>=2 pin; valid control passes. These are five specific negative controls, not blanket proof-fraud detection.')
        add(folder+'receipt.json','six_mutation_receipt_crosscheck',same_rows=obj(folder+'receipt.json')['mutations']==muts)
    # G12 retained compiled dump vs census/wrappers, exact historical marker correspondence.
    census=obj('g12/census.json');walk=obj('g12/independent_walk.json');dump=mark('g12/final_independentdump_stdout.txt','G12_INDEPENDENT_DUMP');reports=mark('g12/final_audit_stdout.txt','G12_REPORTS')
    assert mark('g12/final_census_stdout.txt','G12_CENSUS')==census
    extracted=[];total=0
    for module in dump:
        assert len(module['constNames'])==len(set(module['constNames'])) and set(module['constNames'])=={c['name'] for c in module['constants']}
        total+=len(module['constNames'])
        for c in module['constants']:
            if c['is_theorem'] is False and c['forall_result_head']=='Derivation.Iso':extracted.append([module['module'],c['name']])
    expected=sorted([[r['module'],r['definition']] for r in census]);assert sorted(extracted)==expected==sorted(walk['entries']) and total==141 and len(dump)==12 and len(census)==5
    assert len({r['definition'] for r in reports})==5 and {r['definition'] for r in reports}=={r['definition'] for r in census}
    assert all(r['status']=='SOLVED' and set(r['axioms']+r['instance_axioms'])<={'propext','Quot.sound'} for r in reports)
    for s in ('g12/census.json','g12/independent_walk.json','g12/final_census_stdout.txt','g12/final_independentdump_stdout.txt','g12/final_audit_stdout.txt','g12/receipt.json'):
        add(s,'g12_compiled_census_dump_wrapper_reconciliation',modules=12,constants=141,iso_constructors=5,whitelisted_wrapper_and_instance_reports=5,assessment='The retained independent dump has 141 distinct module-local constants in 12 parked modules; filtering non-theorems whose forall-result head is Derivation.Iso yields exactly the same five census constructors and five wrapper/instance reports. This is internal consistency between retained compiled-environment reports, not fresh environment inspection or an exhaustive census outside those modules. Closed instances are identity-regime nonvacuity witnesses.')
    for base in ('g12/','g12/prior_style_run/'):
        rec=obj(base+'receipt.json');assert rec['reports']==reports and len(rec['mutations'])==5 and rec['full_G12_experiment_completed'] is False
        outcomes=[{'mutation':m['mutation'],'reason':m['reason'],'returncode':m.get('process',m.get('gate_process',{})).get('returncode')} for m in rec['mutations']]
        assert [x['returncode'] for x in outcomes]==[1,1,0,0,1]
        add(base+'receipt.json','g12_negative_control_layering',mutations=outcomes,assessment=by[path(base+'receipt.json')]['assessment']+' Five mutation reasons are distinct: explicit False and dropped-hypothesis wrappers fail the Lean audit; forged textual census and misplaced wrapper compile yet are refused by independent census/source policy; comment-sorry compiles then fails lexical policy. No model or entire-estate execution is claimed.')
    # Pair all top-level runtime maps, preserving unmatched input-only attempts.
    for p,x in list(by.items()):
        if not p.endswith('.json'):continue
        val=json.loads(d.RAW[p].decode('utf-8-sig'))
        if isinstance(val,dict) and len(val)>80 and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in val.values()):
            peer=p.replace('_before.json','_after.json') if p.endswith('_before.json') else p.replace('_after.json','_before.json') if p.endswith('_after.json') else None
            exists=peer in by
            x['checks'].append(d.check('paired_runtime_map','matched' if exists and val==json.loads(d.RAW[peer]) else 'different' if exists else 'no_retained_counterpart',paired_path=peer if exists else None,entry_count=len(val)))
    # Attach process references and concrete diagnostic categories to every tape, including empties.
    process_summary=[];reverse=collections.defaultdict(list)
    for p,entry in by.items():
        if p.endswith('.json'):
            value=json.loads(d.RAW[p].decode('utf-8-sig'))
            if isinstance(value,dict) and 'argv' in value and 'returncode' in value:
                binds=[c for c in entry['checks'] if c['rule'].endswith('_raw_binding')]
                for ch in binds:reverse[ch['target']].append({'process':p,'returncode':value['returncode'],'raw_match':ch['raw_match'],'original_zip_match':ch['original_zip_match']})
                stdout=next((c['target'] for c in binds if c['rule']=='stdout_raw_binding'),None)
                lines=d.RAW[stdout].decode('utf8',errors='replace').splitlines() if stdout else []
                relevant=[l for l in lines if re.search('error:|DISALLOWED|STATEMENT_PIN|VACUOUS|FORBIDDEN|failed|unknown|unsolved|passed|checked|verified',l,re.I)]
                process_summary.append({'path':p,'returncode':value['returncode'],'diagnostic_excerpt':[l[:300] for l in relevant[:3]],'bound_streams':len(binds)})
    for p,entry in by.items():
        if p.endswith(('.txt','.bin')):entry['checks'].append(d.check('paired_process_observations','observed' if reverse[p] else 'no_separate_process_record',records=reverse[p]))
    primitive=obj('g02/original/artifacts/primitive_completion_receipt.json')
    add('g02/original/artifacts/primitive_completion_receipt.json','broader_historical_receipt_scope','observed',bounds=primitive['bounds'],open_obligation_count=len(primitive['open_obligations']),frontier_count=len(primitive['frontier_conjectures']),terminal_codes=[r['code'] for r in primitive['terminals']],withdrawn=primitive['withdrawn_or_repaired_claims'],assessment='Bounded parse of a much broader old primitive-completion receipt: 21 adversarial dispositions, 12 extensions, 13 terminals, five conjectures and eight explicit open obligations. Its controller/contact/graph/Genesis claims and 1314-theorem axiom count depend on artifacts outside this slice and are not certified here. Cut-census evidence is assessed independently above. Seed/prompt fields are custody metadata only; no seed or answer material was followed or read.')
    a.write('_automated.json',autos)
    a.write('_semantic_controls.json',{'runtime':sys.version,'finite_augmentation_rows':finite_summaries,'equal_count_wrong_key_control_rejected':negative_detected,'g02_cases':1014,'g02_refusals':2,'g01_census':{'constants':100,'theorems':90,'pins':11},'g02_axiom_reports':52,'g12_census':{'constants':141,'modules':12,'constructors':5},'manifest_bindings':archive_checks,'process_diagnostics':process_summary,'limits':'Read-only data checks and independent bounded arithmetic under Python3.14.2; no binary, compiler, provider or archived command execution.'})
    print(json.dumps({'data_files':len(autos),'finite_rows':finite_summaries,'manifest_rows':len(archive_checks),'process_records':len(process_summary)},indent=2))
if __name__=='__main__':main()
