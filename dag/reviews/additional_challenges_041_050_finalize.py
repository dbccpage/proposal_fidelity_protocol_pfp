"""Reconcile this audit slice without changing source or historical evidence."""
import sys,json,hashlib,collections,datetime,re
sys.dont_write_bytecode=True
import additional_challenges_041_050_audit as a

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize_checks(row):
    for c in row.get('checks',[]):
        if isinstance(c,dict):c.setdefault('status','parsed' if c.get('rule') in ('json_structure','budget_configuration','lean_case_envelope') else 'observed')

def verdicts(obj):
    if isinstance(obj,dict):
        if 'owner_verdict' in obj:yield obj['owner_verdict']
        for k,v in obj.items():
            if k not in ('answer','owner_verdict'):yield from verdicts(v)
    elif isinstance(obj,list):
        for v in obj:yield from verdicts(v)

def flags(v):
    if isinstance(v,list) and v and isinstance(v[0],list):return [x[0] for x in v]
    if isinstance(v,list) and v and isinstance(v[0],bool):
        meta=v[2] if len(v)>2 and isinstance(v[2],dict) else {}
        for p,q in [('primary_pass','independent_pass'),('exact_pass','independent_pass'),('exact_passed','independent_passed')]:
            if p in meta and q in meta:return [meta[p],meta[q]]
        return [v[0]]
    return []

def main():
    scope=a.read('_scope.json');ledger=a.read('_read_ledger.json');notes=a.read('_notes.json')
    # Repair prose only in this audit's new records. No source body is modified.
    c48={
    'CHALLENGE.md':'Read the local/global theorem for nondegenerate ternary forms, explicit Hilbert formulas, exact point or prime-place witnesses, arbitrary precision bounds, planned squarefree reduction/descent, and native/PARI checks. One local obstruction suffices. Global reciprocity contradicts the proposed mixed-sign form obstructed only at 2. Actual Python algorithms omit the planned descent/reduction. Official PARI qfsolve documentation corroborates output conventions, not this implementation.',
    'participant_packet/TASK.md':'Read the point equation, all-place Hilbert criterion and output schema. Hilbert equivalence requires nonzero coefficients; zero cases are handled directly. TASK bound 10^18 differs from CHALLENGE bound 10^30. Canonical decimal syntax is not enforced beyond integer parsing.',
    'judge_packet/exact_checker.py':'Exactly evaluates a nonzero point or a Hilbert obstruction after a primality gate. The point equation is direct. Its Miller–Rabin helper has a claimed 64-bit domain but is used on unrestricted places. OUT_OF_SCOPE recomputes malformed input but ignores witness content. Missing case fields can raise KeyError, and noncanonical decimal strings pass.',
    'judge_packet/independent_checker.py':'Separately implements Jacobi recursion, Hilbert symbols and exact trial division. Both Hilbert implementations agree with 108 primitive modular conic controls. OUT_OF_SCOPE checks malformed coefficients but not the supplied witness. Trial division is exact if it finishes, but a bounded two-second probe on 2^61-1 was stopped without a verdict. Coordinates must be strings; Boolean values are rejected.',
    'reference_solver/factorization.py':'Read 12-base Miller–Rabin, Pollard rho and the factor stack/fallback. No per-case factorization budget exists; the rho loop is uncapped. An unfactored remainder is inserted as prime after a limited trial fallback. The explicit composite 399165290221 * 798330580441 passes above 64 bits; this is not deterministic arbitrary-precision primality.',
    'reference_solver/hilbert_symbol.py':'Read valuations, odd-prime Euler criterion, 2-adic epsilon/omega factors and the real sign formula. The formulas require nonzero arguments and a prime place; the helper itself does not establish primality. All 108 independent primitive modular conic controls agree. Finite controls do not prove Hasse–Minkowski.',
    'reference_solver/legendre_solver.py':'Read zero-coefficient/opposite-pair fast paths, sign permutations and bounded z search. No Legendre descent or squarefree/coprime reduction is implemented. A z cap of 50000 and coordinate caps of 2000 skip both loops for x²+y²-2001²z², despite the immediate point (2001,0,1). The Holzer label does not justify completeness after practical clamps.',
    'reference_solver/solver.py':'Routes malformed input, real obstruction, bounded point search, Hilbert place 2, and factor-based prime scans before UNKNOWN. It correctly avoids turning failed point search into a negative theorem. FACTORING_LIMIT also labels point-search failure after successful factorization; no operational timer enforces that code. The trace is fixed stage metadata.',
    'reference_solver/__init__.py':'Re-exports solve only; no additional proof or checker is introduced.',
    'judge_packet/generate_hidden_cases.py':'Read all 64 static forms and labels plus top-level writes. Many solvable rows are constructed with (1,1,1). The proposed obstructed form (1,2,-3) also has this point. The form (1,1,-7) claimed obstructed only at 2 is also obstructed at 7. Planned difficult semiprime coverage is absent. Generator source was not executed; retained data labels are separately assessed.',
    'judge_packet/generate_mutations.py':'Read 48 attacks on coordinates, small composite places, false places and OUT_OF_SCOPE claims. These are useful baseline controls but omit large-prime cost and the above-64-bit pseudoprime case. The generator was not executed.',
    'participant_packet/generate_examples.py':'Read 12 examples with expected outputs derived from the owner solver. Top-level writes use a legacy demos path. The purported large solvable example is (3,5,-8); expected labels do not come from an independent PARI replay. The generator was not executed.',
    'participant_packet/runner.py':'Checks status/kind and directly evaluates positive points. Negative answers require only a nonempty place, without primality or Hilbert-symbol validation. Passing the public runner therefore does not certify obstruction answers; this audit invokes the actual checkers separately.',
    'tests/test_c048_independent_checker.py':'Read valid-point, malformed-input, zero/Boolean/float-coordinate, and composite-9 rejection tests. They meaningfully exercise a prior refuse-all repair and intentionally accept bare OUT_OF_SCOPE on malformed input. They omit large-prime bounds/cost and the coordinate-cap counterexample.'}
    for r in ledger:
        if '/c048_' in r['path']:
            suffix=r['path'].split('/c048_ternary_quadratic_forms/',1)[1];r['assessment']=c48[suffix]
    # Expand several compressed phrases that occurred in earlier checkpoints.
    replacements={'says4.34.0':'says 4.34.0','TASK4.34.1':'TASK 4.34.1','toolchain4.35.0':'toolchain 4.35.0','installed4.35.0':'installed 4.35.0','Lean4.35.0':'Lean 4.35.0','although5^2':'although 5^2','Fin11':'Fin 11','mod11':'mod 11','all512formula':'all 512 formula','over2variables':'over 2 variables','3828accepted':'3828 accepted','charges2':'charges 2','mod2':'mod 2','Only512small':'Only 512 small','witness[0,1,1]':'witness [0,1,1]','coloring001':'coloring 001','C042DRAT':'C042 DRAT','seeded0':'seeded 0','All64':'All 64','has4':'has 4','has2':'has 2','modulus4':'modulus 4','Python;480':'Python; 480','40base':'40 base','produces42':'produces 42','disagree12/14':'disagree 12/14','on4constants':'on 4 constants','a2element':'a 2-element','max_steps1000000':'max_steps 1000000','count999':'count 999','check.100':'check. 100','and1248integer':'and 1248 integer','order1':'order 1','start58':'start 58','determinant1':'determinant 1','rows0,1':'rows 0,1','start1':'start 1','range0..5':'range 0..5','root500':'root 500','report0/0':'report 0/0','of648':'of 648','on64':'on 64','verifies47':'verifies 47','Across648':'Across 648','certificates,64':'certificates, 64','integer17':'integer 17','depth5':'depth 5','size3':'size 3','model8':'model 8'}
    def clean(s):
        for old,new in replacements.items():s=s.replace(old,new)
        return s
    for r in ledger:r['assessment']=clean(r['assessment'])
    a.write('_read_ledger.json',ledger)
    bypath={r['path']:r for r in ledger}
    for f in notes['family_assessments']:
        f['family']=f['family'].upper();f['math']=clean(f['math']);f['limits']=[clean(x) for x in f['limits']]
        for finding in f['findings']:finding['claim']=clean(finding['claim'])
    for f in notes['family_assessments']:
        f['math']=f['math'].replace('variables;3828','variables; 3828').replace('Explicit complete finite coloring checks establish','On well-formed domains with consistent fixed constraints, explicit complete finite coloring checks establish')
        for finding in f['findings']:
            finding['claim']=finding['claim'].replace('its40 base','its 40 base').replace('selfcomparison','self-comparison').replace('runner oldpath','runner legacy path').replace('base35/base40','base 35/base 40')
    family48=next(f for f in notes['family_assessments'] if f['family']=='C048')
    family48.update(math='A nonzero integer point is checked by exact quadratic evaluation. For a nondegenerate diagonal form, a Hilbert symbol of -1 at a genuine prime place supplies a local obstruction. All 108 small primitive modular conic controls agree with both implementations. Official PARI documentation supports the rational-point/local-obstruction output convention; PARI was not run.',data='Per-artifact parsing, exact point arithmetic and bounded owner replay are separate from full source reading and retained expected labels.',limits=['No PARI/Rust execution or broad factorization performance result.','Finite modular probes do not prove the local/global theorem.','Primary probable-prime testing above 64 bits is not deterministic primality certification.'])
    claims48=[
    'Reference search returns UNKNOWN on x²+y²-2001²z² although the supplied point (2001,0,1) passes both checkers. Coordinate caps skip the search; the advertised descent and squarefree reduction are absent.',
    'The explicit composite 399165290221 * 798330580441 passes primary Miller–Rabin above 64 bits. Secondary trial division is exact but has no resource ceiling; a bounded two-second test on prime 2^61-1 was stopped without a verdict. Large-place certification is not established by these routes.',
    'Generator source labels solvable (1,2,-3) obstructed and describes (1,1,-7) as obstructed only at 2, although it is also obstructed at 7. The public runner accepts any nonempty obstruction place.',
    'Bare OUT_OF_SCOPE and noncanonical decimal point coordinates pass. Recomputed input failure or exact point arithmetic can support the underlying mathematical decision, but the promised witness and canonical schema are not checked.']
    for f,c in zip(family48['findings'],claims48):f['claim']=c
    allrows=[];summary={}
    for fam in ('c'+str(i).zfill(3) for i in range(41,51)):
        p=a.file('_'+fam+'_automated.jsonl');rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
        for r in rows:normalize_checks(r)
        p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
        allrows.extend(rows);mutations=[(r,v) for r in rows if 'mutation' in r['path'] for v in verdicts(r)];ms=[flags(v) for r,v in mutations];replays=[flags(v) for r in rows for v in verdicts(r)]
        summary[fam.upper()]={'data_files':len(rows),'full_source_reads':sum('/'+fam+'_' in r['path'] or '/test_'+fam in r['path'] for r in ledger),'dispositions':dict(collections.Counter(r['status'] for r in rows)),'owner_replay_records':len(replays),'mutation_replay_records':len(ms),'mutation_accepted_by_all_invoked_routes':sum(bool(v) and all(v) for v in ms),'mutation_accepted_by_first_route':sum(bool(v) and v[0] for v in ms),'mutation_accepted_by_second_route':sum(len(v)>1 and v[1] for v in ms),'limits':'Owner verdict counts are observations, not ground-truth correctness. C041 has envelope/label assessments rather than full native Lean replay.'}
    notes['retained_data_summary']=summary
    for f in notes['family_assessments']:
        base_data=re.sub(r'^(?:All \d+ scoped data files have schema-specific bounded dispositions, separate from \d+ full source reads\. )+','',f['data'])
        s=summary[f['family']];f['data']='All '+str(s['data_files'])+' scoped data files have schema-specific bounded dispositions, separate from '+str(s['full_source_reads'])+' full source reads. '+base_data.replace('Data replay/disposition pending at this checkpoint.','Lean envelopes, mutation candidates and retained answer streams were parsed; complete native proof replay is unclaimed.').replace('Bounded per-file replay pending.','Coloring cases and mutation candidates were replayed within bounded local checks.').replace('current completion statistics pending.','all disposition counts are reported in validation.retained_data_summary.')
    # Evidence selectors name actually read bodies; full ranges are explicit rather
    # than invented narrower source locations. Generated controls are separately hashed.
    selections={
    'C041':[['CHALLENGE.md','TASK.md','lean_compiler.py','exact_checker.py','independent_checker.py'],['generate_cases.py'],['lean_compiler.py','exact_checker.py','independent_checker.py'],['exact_checker.py','CHALLENGE.md','TASK.md']],
    'C042':[['family_solvers.py','sat_checker.py','dual_evaluator.py'],['sat_solver.py','drat_engine.py','drat_checker.py','solver.py'],['family_solvers.py','solver.py'],['dual_evaluator.py','drat_checker.py','family_solvers.py','CHALLENGE.md']],
    'C043':[['ramsey_vdw_checker.py','independent_checker.py'],['ramsey_vdw_checker.py','independent_checker.py','local_search.py'],['ramsey_vdw_checker.py','independent_checker.py','sat_bridge.py'],['test_c043_dual_checkers.py']],
    'C044':[['exact_checker.py','independent_checker.py'],['build_catalog.py'],['solver.py','isomorphism_search.py','exact_checker.py','independent_checker.py'],['algebraic_engine.py','exact_checker.py','independent_checker.py']],
    'C045':[['exact_checker.py','independent_checker.py','knots_catalog.py'],['exact_checker.py','independent_checker.py'],['pd_validator.py','kauffman_bracket.py','solver.py','TASK.md','CHALLENGE.md'],['generate_cases.py','knots_catalog.py']],
    'C046':[['exact_checker.py','independent_checker.py','completion.py'],['solver.py','exact_checker.py','independent_checker.py'],['exact_checker.py','independent_checker.py','judge_completion.py','CHALLENGE.md']],
    'C047':[['exact_checker.py','independent_checker.py','holonomic_guesser.py'],['exact_checker.py','independent_checker.py','holonomic_guesser.py'],['exact_checker.py','independent_checker.py','generate_hidden_cases.py'],['runner.py','test_cases_runner.py']],
    'C048':[['legendre_solver.py','solver.py','CHALLENGE.md'],['factorization.py','exact_checker.py','independent_checker.py'],['generate_hidden_cases.py','runner.py','hilbert_symbol.py'],['exact_checker.py','independent_checker.py','TASK.md']],
    'C049':[['exact_checker.py','independent_checker.py'],['exact_checker.py','independent_checker.py','colimits.py'],['limits.py','exact_checker.py','independent_checker.py'],['category.py','colimits.py','solver.py','generate_hidden_cases.py']],
    'C050':[['terms.py','exact_checker.py','independent_checker.py','TASK.md'],['countermodel.py','exact_checker.py','independent_checker.py','CHALLENGE.md'],['independent_checker.py','countermodel.py'],['exact_checker.py','independent_checker.py','prover.py','solver.py','CHALLENGE.md']]
    }
    def source_evidence(family,selectors):
        return [{'path':r['path'],'sha256':r['sha256'],'lines':r['reviewed_lines']} for r in ledger if ('/'+family.lower()+'_' in r['path'] or '/test_'+family.lower() in r['path']) and any(r['path'].endswith(x) for x in selectors)]
    def generated_evidence(family,suffix):
        p=a.file('_'+family.lower()+suffix)
        return {'path':p.relative_to(a.ROOT).as_posix(),'sha256':sha(p),'generated_audit_artifact':True,'limits':'Generated bounded audit evidence, not an original inventory full-source-read receipt.'}
    notes['claims']=[]
    for f in notes['family_assessments']:
        family=f['family'];f['probe_artifact']=generated_evidence(family,'_probes.json')
        for i,finding in enumerate(f['findings']):
            finding['evidence']=source_evidence(family,selections[family][i])+[generated_evidence(family,'_probes.json')]
            finding['limitations']=['Bounded offline counterexample or directly inspected implementation gap at pinned source bytes; no general claim of exhaustive failure coverage.']
        notes['claims'].append({'id':'AC'+family[2:]+'-C01','claim':f['math'],'status':'conditional_math_and_bounded_checks','evidence':source_evidence(family,['CHALLENGE.md','TASK.md','exact_checker.py','independent_checker.py','dual_evaluator.py','drat_checker.py','sat_checker.py','ramsey_vdw_checker.py'])+[generated_evidence(family,'_probes.json'),generated_evidence(family,'_automated.jsonl')],'dependencies':['Pinned local source bytes','Explicit well-formedness, source-binding and domain premises discussed in the full source receipts'],'limitations':f['limits']})
    a.write('_notes.json',notes)
    records=scope['files'];pins={r['path']:r for r in records};observed={r['path']:r for r in ledger+allrows}
    assert len(observed)==len(ledger)+len(allrows)==len(records)==1207
    assert set(observed)==set(pins)
    for r in ledger:
        n=len((a.ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines());assert r['full_source_read'] is True and r['reviewed_lines']==([[1,n]] if n else [])
    assert all(r['full_source_read'] is False for r in allrows)
    assert all('rule' in c and 'status' in c for r in allrows for c in r.get('checks',[]) if isinstance(c,dict))
    mismatches=[]
    for p,r in pins.items():
        actual=sha(a.ROOT/p)
        if actual!=r['sha256'] or actual!=observed[p]['sha256']:mismatches.append({'path':p,'inventory':r['sha256'],'current':actual,'receipt':observed[p]['sha256']})
    assert not mismatches,mismatches
    recon={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':scope['source_commit'],'scope_files':len(pins),'full_source_reads':len(ledger),'full_source_lines':sum(b-x+1 for r in ledger for x,b in r['reviewed_lines']),'bounded_data_dispositions':len(allrows),'sha256_matches_inventory':len(pins),'hash_mismatches':mismatches,'receipt_duplicates':0,'pending_files':[],'data_full_source_reads':0,'all_automated_check_dicts_have_rule_and_status':True,'source_edits_by_this_slice':0,'historical_receipt_edits_by_this_slice':0,'provider_calls':0,'limits':['Only the declared C041–C050 inventory slice is reconciled.','Full content reading is credited only to source/spec/test bodies actually read, not parsed data.','This does not complete the repository-wide goal or establish every retained proof/data label.']}
    a.write('_reconciliation.json',recon);a.report()
    print(json.dumps({'reconciliation':{k:v for k,v in recon.items() if k not in ('limits','pending_files')},'retained_data_summary':summary},ensure_ascii=False))
if __name__=='__main__':main()
