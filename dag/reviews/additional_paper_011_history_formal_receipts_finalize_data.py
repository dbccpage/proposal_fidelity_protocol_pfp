import sys,json,re,hashlib,collections,zipfile
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_data as d
a=d.a;P=d.PAPER;H=d.HIST
rows=a.read('_automated.json');by={r['path']:r for r in rows};semantic=a.read('_semantic_controls.json')
def add(p,rule,status='observed',**kw):by[p]['checks'].append(d.check(rule,status,**kw))
with zipfile.ZipFile(a.ROOT/(P+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip')) as z:
    for p in [H+'g12/'+pre+'runtime_inputs_'+post+'.json' for pre in ('','prior_style_run/') for post in ('before','after')]:
        x=json.loads(d.RAW[p]);assert all(isinstance(v,dict) and set(v)=={'sha256','bytes'} and re.fullmatch('[0-9a-f]{64}',v['sha256']) and type(v['bytes']) is int and v['bytes']>=0 for v in x.values())
        peer=p.replace('_before.json','_after.json') if p.endswith('_before.json') else p.replace('_after.json','_before.json');other=json.loads(d.RAW[peer]);same=x==other
        delta={'only_this_map':sorted(x.keys()-other.keys()),'only_paired_map':sorted(other.keys()-x.keys()),'changed_values':[k for k in x.keys()&other.keys() if x[k]!=other[k]]}
        links=d.hashlinks(x,p)
        for link in links:
            member='021_recreated_demos_and_proposal_fidelity_evidence/'+link['target'][len(P):]
            link['original_zip_match']=member in z.namelist() and d.digest(z.read(member))==link['expected']
            link['current_length_match']=len(d.RAW[link['target']])==link['recorded_bytes']
        add(p,'typed_runtime_custody_map','verified' if same else 'different',entries=len(x),record_fields=['sha256','bytes'],paired_path=peer,paired_entries_equal=same,delta=delta,locally_mapped_bindings=links)
        by[p]['assessment']='All historical runtime-map records parsed as nonnegative byte lengths plus SHA256. '+('Entire before/after map is equal. ' if same else 'Prior-style after map adds four mutation sources; shared entries are unchanged, but the added sources lack the initial whole-runtime-map binding. ')+'Available original-paper dependencies are hash-compared in current and original ZIP representations; recorded external compiler/install paths remain unauthenticated and were never followed. This is bounded custody metadata, not source reading or proof of actual runtime isolation.'
    # Named receipt SHA fields that do not contain an explicit path in the same object.
    bindings=[]
    for p,entry in by.items():
        if not p.endswith('.json'):continue
        x=json.loads(d.RAW[p]);
        if not isinstance(x,dict):continue
        family=p[len(H):].split('/')[0];base=p.rsplit('/',1)[0]
        refs={
            'source_manifest_sha256':H+family+'/source_manifest.json',
            'solve_sha256':H+family+'/solve.json',
            'runtime_before_sha256':base+'/runtime_before.json','runtime_after_sha256':base+'/runtime_after.json',
            'inputs_before_sha256':base+'/inputs_before.json','inputs_after_sha256':base+'/inputs_after.json',
            'runtime_inputs_before_sha256':base+'/runtime_inputs_before.json','runtime_inputs_after_sha256':base+'/runtime_inputs_after.json',
            'baseline_receipt_sha256':H+'g02/final_v3/receipt.json','baseline_helper_sha256':H+'g02/final_v3/runner_snapshot.py',
            'build_receipt_sha256':H+'g01/native_build_v3/receipt.json',
            'target_source_sha256':H+'g01/execution_machinery_theorem_v3_native_v2/G01Targets.lean'}
        checks=[]
        for field,t in refs.items():
            if field in x and t in d.BY:
                ch=d.compare_hash(t,x[field]);member='021_recreated_demos_and_proposal_fidelity_evidence/'+t[len(P):];ch['original_zip_match']=d.digest(z.read(member))==x[field];checks.append({'field':field,**ch})
        if checks:add(p,'named_receipt_digest_bindings',bindings=checks);bindings.extend(checks)
    # Direct source/native executable pins remain inert and are checked as bytes only.
    for folder,exe in [('g01/native_build_diagnostic_v1','g01_second_checker.exe'),('g01/native_build_v2','g01_second_checker.exe'),('g01/native_build_v3','g01_second_checker.exe'),('g02/native_build_v1','g02_cut_bitmask.exe')]:
        p=H+folder+'/receipt.json';x=json.loads(d.RAW[p]);t=H+folder+'/'+exe;assert d.digest(d.RAW[t])==x['executable_sha256'];add(p,'inert_executable_byte_pin','verified',executable=t,sha256=x['executable_sha256'],executed=False);add(t,'native_receipt_byte_pin','verified',receipt=p,executed=False)
    # README's cited G02 hashes bind original ZIP receipt bytes despite migration drift.
    readme_bindings=[]
    for p,want in [(H+'g02/final_v3/receipt.json','15c1365812f8b369ddf072e2109c0092a1f513778ab3f6421bff95475f7eeec8'),(H+'g02/mutation_custody_v1/receipt.json','76a851353e6fa4a08f854b0c20dca361849e3914e4389ada520276c2179adb9a')]:
        b=z.read('021_recreated_demos_and_proposal_fidelity_evidence/'+p[len(P):]);assert d.digest(b)==want;readme_bindings.append({'path':p,'cited':want,'current_sha256':d.digest(d.RAW[p]),'original_zip_match':True})
    semantic['readme_original_zip_binding']=readme_bindings
    semantic['named_receipt_digest_bindings']=bindings
# Original G12 gate count: Lean names may themselves contain apostrophes; parse greedily to the fixed phrase.
p=H+'g12/short_original_build_stdout.txt';text=d.RAW[p].decode();axioms=re.findall(r"'(.+)' depends on axioms:\s*\[([^\]]*)\]",text);free=re.findall(r"'(.+)' does not depend on any axioms",text)
names=[n for n,_ in axioms]+free;assert len(names)==len(set(names))==1530 and len(axioms)==1076 and len(free)==454
assert all(set(t.strip() for t in aa.split(',') if t.strip())<={'propext','Quot.sound'} for _,aa in axioms)
add(p,'full_original_log_axiom_census','verified',theorems=1530,with_axioms=1076,axiom_free=454,duplicate_names=0,allowed_axioms=['propext','Quot.sound'])
for folder in ('g12/','g12/prior_style_run/'):
    for stem,msg in [('original_check_axiom_report','axiom reports match (1530 theorems; name-blind count agrees at 1530)'),('original_check_lean_audit',"lean audit clean: 77 sources, 1530 axiom reports, axioms within ['Quot.sound', 'propext']"),('original_check_parked_audit',"parked audit complete: 75 modules, 63 in the root's closure, 12 parked and all named for audit")]:
        p=H+folder+stem+'_stdout.txt';assert d.RAW[p].decode().strip()==msg;add(p,'original_gate_exact_summary','verified',summary=msg,limits='Report consistency only; source census and gate implementations belong to the native lane, not independently reexecuted.')
    # A text-forged census can equal every byte of the parsed census yet carries no compiler provenance.
    p=H+folder+'text_census_stdout.txt';marks,errors=d.markers(d.RAW[p]);assert not errors and marks['G12_CENSUS'][0]['value']==json.loads(d.RAW[H+'g12/census.json'])
    add(p,'forged_text_census_equals_valid_payload','verified',same_parsed_rows=True,scope='Negative control: the identical parsed payload is intentionally insufficient for compiled-environment provenance.')
# Sealed Iso block used in receipt, preserving exact bytes including its following comment.
p=H+'g12/sealed_Minimality.lean';block=b'structure Iso'+d.RAW[p].split(b'structure Iso',1)[1].split(b'def isoRefl',1)[0]
want=json.loads(d.RAW[H+'g12/receipt.json'])['sealed_iso_declaration_sha256'];assert d.digest(block)==want
add(H+'g12/receipt.json','sealed_iso_declaration_byte_pin','verified',source=p,sha256=want)
# Attach every process's observed diagnostics to both its record and its tapes.
for rec in semantic['process_diagnostics']:
    p=rec['path'];add(p,'observed_process_diagnostic_classification',returncode=rec['returncode'],diagnostic_excerpt=rec['diagnostic_excerpt'])
    for ch in by[p]['checks']:
        if ch['rule'].endswith('_raw_binding'):
            t=ch['target'];add(t,'process_diagnostic_context',process=p,returncode=rec['returncode'],diagnostic_excerpt=rec['diagnostic_excerpt'])
a.write('_automated.json',rows);a.write('_semantic_controls.json',semantic)
print(json.dumps({'files':len(rows),'g12_original_axiom_reports':len(names),'named_receipt_edges':len(bindings),'rule_status_checks':sum(len(r['checks']) for r in rows)}))
