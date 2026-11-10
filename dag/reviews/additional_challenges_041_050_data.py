"""Schema-specific parsed artifact review, never a full-source-read receipt."""
import sys,json,hashlib,collections,subprocess,time,itertools,math
from pathlib import Path
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT, file,read,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))

def parse(path):
    duplicates=[]
    def pairs(items):
        d={}
        for k,v in items:
            if k in d: duplicates.append(k)
            d[k]=v
        return d
    txt=path.read_text(encoding='utf-8-sig')
    obj=([json.loads(l,object_pairs_hook=pairs) for l in txt.splitlines() if l.strip()] if path.suffix=='.jsonl' else json.loads(txt,object_pairs_hook=pairs))
    return obj,duplicates

def owner_replay(family,case,answer=None):
    if family=='c050':
        from c050_equational_theorem_proving.reference_solver.solver import solve
        from c050_equational_theorem_proving.judge_packet.exact_checker import check_solution
        from c050_equational_theorem_proving.judge_packet.independent_checker import independent_check
        from additional_challenges_041_050_c050_probe import strict_model,strict_proof
        if answer is None: answer=solve(case)
        extra={}
        if answer.get('kind')=='PROOF':extra['independent_certificate']=strict_proof(case,answer)
        elif answer.get('kind')=='COUNTERMODEL':extra['independent_certificate']=strict_model(case,answer)
        return {'answer':answer,'owner_verdict':[check_solution(case,answer),independent_check(case,answer)],**extra,'limits':'Independent variable-only replay and finite table validation are bounded executable checks; unsupported syntax, lemmas and groundness require separate interpretation.'}
    if family=='c049':
        from c049_finite_category_universal_constructions.reference_solver import solve
        from c049_finite_category_universal_constructions.judge_packet.exact_checker import check_solution
        from c049_finite_category_universal_constructions.judge_packet.independent_checker import independent_check
        from additional_challenges_041_050_c049_probe import independent_category
        if answer is None: answer=solve(case)
        cats=[case.get('category_C',{}),case.get('category_D',{})] if case.get('task')=='ADJUNCTION' else [case]
        return {'answer':answer,'owner_verdict':[check_solution(case,answer),independent_check(case,answer)],'independent_category_axioms':[independent_category(c) for c in cats],'limits':'Category axioms checked independently under compact identity/singleton-hom conventions; universal witness and functor laws not certified by this data replay.'}
    if family=='c048':
        from c048_ternary_quadratic_forms.reference_solver.solver import solve
        from c048_ternary_quadratic_forms.judge_packet.exact_checker import check_solution
        from c048_ternary_quadratic_forms.judge_packet.independent_checker import independent_check
        if answer is None: answer=solve(case)
        extra={}
        if answer.get('kind')=='RATIONAL_POINT':
            try:
                xyz=[int(answer[k]) for k in ('x','y','z')];coeff=[int(case[k]) for k in ('a','b','c')]
                extra['independent_exact_point_check']=any(xyz) and sum(a*x*x for a,x in zip(coeff,xyz))==0
            except (ValueError,TypeError,KeyError):
                extra['independent_exact_point_check']=False
                extra['independent_point_reason']='Coordinates or coefficients cannot be parsed as integers.'
        return {'answer':answer,'owner_verdict':[check_solution(case,answer),independent_check(case,answer)],**extra,'limits':'Local negative certificate depends on primality; bounded replay timeout is not a negative theorem.'}
    if family=='c047':
        from c047_sequence_law_discovery.reference_solver.solver import solve
        from c047_sequence_law_discovery.judge_packet.exact_checker import check_solution
        from c047_sequence_law_discovery.judge_packet.independent_checker import independent_check
        if answer is None: answer=solve(case)
        return {'answer':answer,'owner_verdict':[check_solution(case,answer),independent_check(case,answer)],'limits':'Finite residual agreement only; no symbolic law/all-n authentication. Absence covers answer-declared start range.'}
    if family=='c046':
        from c046_knuth_bendix_completion.reference_solver.solver import solve
        from c046_knuth_bendix_completion.judge_packet.checkers.dual_evaluator import evaluate_dual
        if answer is None: answer=solve(case)
        return {'answer':answer,'owner_verdict':evaluate_dual(case,answer),'limits':'Bounded completion/reachability checks; accepted budget refusal is not evidence of exhaustion.'}
    if family=='c045':
        from c045_knot_polynomials_from_pd.reference_solver.solver import solve
        from c045_knot_polynomials_from_pd.judge_packet.checkers.dual_evaluator import evaluate_dual
        if answer is None: answer=solve(case)
        return {'answer':answer,'owner_verdict':evaluate_dual(case,answer),'limits':'Independent checker recomputes invariants; accepted identification is a catalog-signature match, not general recognition.'}
    if family=='c044':
        from c044_finite_group_identification.reference_solver.solver import solve
        from c044_finite_group_identification.judge_packet.checkers.dual_evaluator import evaluate_dual
        if answer is None: answer=solve(case)
        return {'answer':answer,'owner_verdict':evaluate_dual(case,answer),'limits':'Shared table parser/catalog assumptions; UNKNOWN and OOS acceptance are not independently certified.'}
    if family=='c043':
        import random
        random.seed(0)
        from c043_ramsey_vdw_constructions.reference_solver.solver import solve
        from c043_ramsey_vdw_constructions.judge_packet.checkers.dual_evaluator import evaluate_dual
        from additional_challenges_041_050_c043_probe import independent
        if answer is None: answer=solve(case)
        extra={}
        if answer.get('status')=='SOLVED': extra['independent_certificate_valid']=independent(case,answer['colours'])
        return {'answer':answer,'owner_verdict':evaluate_dual(case,answer),**extra}
    if family=='c042':
        from c042_sat_with_drat_certificates.reference_solver.solver import solve
        from c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import evaluate_dual
        if answer is None: answer=solve(case)
        return {'answer':answer,'owner_verdict':evaluate_dual(case,answer),'independent_problem_truth':problem_truth(case)}
    return {'disposition':'No full native Lean replay of this artifact. Parsed structure and retained labels only; truth labels are not proof.'}

def problem_truth(c):
    """Independent finite problem enumeration, not owner encodings or solver traces."""
    f=c.get('family'); candidates=0
    try:
        if f=='coloring':
            n,k=c['n'],c['k']; edges=c['edges']
            if type(n)!=int or type(k)!=int or n<0 or k<=0 or any(type(x)!=int or x<0 or x>=n for e in edges for x in e): return {'domain':'invalid'}
            if k**n>1000000:return {'domain':'outside_enumeration_ceiling'}
            for colors in itertools.product(range(k),repeat=n):
                candidates+=1
                if all(colors[u]!=colors[v] for u,v in edges):return {'sat':True,'examined':candidates,'witness':colors}
        elif f=='php':
            p,h=c['pigeons'],c['holes'];blocked=set(map(tuple,c.get('blocked',[])))
            if p<=0 or h<=0:return {'domain':'invalid'}
            if p>h:return {'sat':False,'reason':'injective map from larger finite set to smaller impossible'}
            if math.perm(h,p)>1000000:return {'domain':'outside_enumeration_ceiling'}
            for assignment in itertools.permutations(range(h),p):
                candidates+=1
                if all((i,v) not in blocked for i,v in enumerate(assignment)):return {'sat':True,'examined':candidates,'witness':assignment}
        elif f=='latin_square':
            n=c['order'];preset=c.get('prefilled',[])
            if n<=0 or any(not(0<=r<n and 0<=col<n and 0<=v<n) for r,col,v in preset):return {'domain':'invalid'}
            if math.factorial(n)**n>1000000:return {'domain':'outside_enumeration_ceiling'}
            perms=list(itertools.permutations(range(n)))
            rows=[[p for p in perms if all(p[col]==v for r,col,v in preset if r==i)] for i in range(n)]
            for grid in itertools.product(*rows):
                candidates+=1
                if all(len({grid[i][j] for i in range(n)})==n for j in range(n)):return {'sat':True,'examined':candidates,'witness':grid}
        elif f=='tseitin':
            n=c['vertices'];edges=c['edges'];charges=c['charges']
            if len(charges)!=n or any(type(x)!=int or x not in(0,1) for x in charges) or any(not(0<=v<n) for e in edges for v in e):return {'domain':'invalid'}
            if len(edges)>19:return {'domain':'outside_enumeration_ceiling'}
            for bits in itertools.product((0,1),repeat=len(edges)):
                candidates+=1; totals=[0]*n
                for bit,(u,v) in zip(bits,edges):totals[u]^=bit;totals[v]^=bit
                if totals==charges:return {'sat':True,'examined':candidates,'witness':bits}
        elif f=='tiling':
            tiles=c['tiles'];blocked=set(map(tuple,c.get('blocked',[])));needed={(r,col) for r in range(c['rows']) for col in range(c['cols'])}-blocked
            if len(tiles)>19:return {'domain':'outside_enumeration_ceiling'}
            for selected in itertools.product((0,1),repeat=len(tiles)):
                candidates+=1;cells=[tuple(cell) for yes,tile in zip(selected,tiles) if yes for cell in tile]
                if len(cells)==len(set(cells)) and set(cells)==needed:return {'sat':True,'examined':candidates,'witness':[i for i,v in enumerate(selected) if v]}
        else:return {'domain':'unsupported'}
        return {'sat':False,'examined':candidates,'reason':'complete bounded enumeration'}
    except (KeyError,TypeError,ValueError,IndexError):return {'domain':'malformed'}

def review(path,family):
    p=ROOT/path; obj,dups=parse(p)
    row={'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'full_source_read':False,'status':'bounded_automated_assessment','duplicate_json_keys':dups,'checks':[]}
    check={'rule':'json_structure','top_level':type(obj).__name__,'keys':sorted(obj) if isinstance(obj,dict) else None}
    row['checks'].append(check)
    root=Path(*p.parts[:p.parts.index(family+'_'+next(x.split('_',1)[1] for x in p.parts if x.startswith(family+'_')))+1])
    # Metadata manifests authenticate bytes, not mathematical truth or provider execution.
    if '/commit_reveal/' in path:
        row['checks'].append({'rule':'commitment_metadata','status':'parsed','fields':sorted(obj),'limits':'Commitment metadata only; no seed, sealed answer or private material opened or inferred. No chronology/provenance verification.'})
    elif family in ('c045','c046') and isinstance(obj,list):
        results=[]
        for idx,item in enumerate(obj):
            case=item.get('case',item);answer=item.get('corrupted_ans')
            try:result=owner_replay(family,case,answer)
            except Exception as e:result={'exception':type(e).__name__,'message':str(e)}
            results.append({'index':idx,'case_id':case.get('case_id'),'mutation_id':item.get('mutation_id'),**result})
        row['checks'].append({'rule':'case_or_mutation_array_replay','status':'observed','records':results})
    elif family in ('c045','c046','c047','c048','c049','c050') and isinstance(obj,dict) and 'input' in obj:
        row['checks'].append({'rule':'public_input_output_pair','status':'observed','retained_answer':owner_replay(family,obj['input'],obj.get('output',obj.get('expected'))),'fresh_reference':owner_replay(family,obj['input'])})
    elif family=='c044' and p.name=='small_groups_catalog.json':
        from additional_challenges_041_050_c044_probe import independent
        row['checks'].append({'rule':'finite_group_table_axioms_and_invariants','entries':[{'id':r['id'],'name':r['name'],'declared_order':r['order'],'independent':independent(r['table']),'retained_invariants':r['invariants']} for r in obj],'limits':'No independent authentication of numeric SmallGroups IDs. A4xC2 name is disproved by center order4 versus2.'})
    elif p.name=='manifest.json':
        entries=obj.get('entries',obj.get('files',{})); refs=[]
        iterable=entries.items() if isinstance(entries,dict) else [(e.get('path',e.get('file')),e) for e in entries]
        for rel,detail in iterable:
            target=root/rel; expected=detail if isinstance(detail,str) else detail.get('sha256')
            actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
            refs.append({'path':str(target.relative_to(ROOT)).replace('\\','/'),'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected})
        row['checks'].append({'rule':'manifest_raw_byte_binding','references':refs,'declared_counts':{k:v for k,v in obj.items() if 'count' in k or k=='total_files'},'limits':'Manifest hash agreement does not authenticate truth, chronology or independent custody.'})
    elif p.name=='accounting.json':
        row['checks'].append({'rule':'budget_configuration','record':obj,'limits':'Budget/model configuration declaration, not actual spend or provider receipt.'})
    elif p.suffix=='.jsonl':
        examples={json.loads(e.read_text(encoding='utf-8'))['case_id']:json.loads(e.read_text(encoding='utf-8')) for e in (root/'participant_packet/examples').glob('*.json')}
        results=[]
        for idx,answer in enumerate(obj,1):
            cid=answer.get('case_id',answer.get('id')); case=examples.get(cid)
            results.append({'line':idx,'case_id':cid,'status':answer.get('status'),'source_example_found':case is not None,**(owner_replay(family,case,answer) if case else {})})
        row['checks'].append({'rule':'answer_stream_binding','records':results,'limits':'No provider provenance inferred from retained outputs.'})
    elif isinstance(obj,dict) and 'case' in obj and any(k in obj for k in ('answer','corrupted_answer','mutated_answer','candidate')):
        answer=next(obj[k] for k in ('answer','corrupted_answer','mutated_answer','candidate') if k in obj)
        row['checks'].append({'rule':'mutation_envelope','mutation_id':obj.get('mutation_id'),'case_id':obj['case'].get('case_id',obj['case'].get('id')),'expected_rejection':obj.get('expected_rejection'),'answer_status':answer.get('status'),**owner_replay(family,obj['case'],answer)})
    else:
        case=obj.get('case',obj) if isinstance(obj,dict) else obj
        if family=='c041':
            good=isinstance(case,dict) and isinstance(case.get('case_id'),str) and isinstance(case.get('statement'),str) and isinstance(case.get('prelude',''),str)
            c={'rule':'lean_case_envelope','schema_fields_valid':good,'case_id':case.get('case_id'),'retained_expected_kind':case.get('expected_kind'),'retained_expected_status':case.get('expected_status'),'statement_characters':len(case.get('statement','')),'within_400_character_bound':len(case.get('statement',''))<=400,'limits':'No fresh proof of this complete Lean expression; full formal replay remains unclaimed.'}
            if case.get('statement')=='∃ x : Fin 11, x * x = 3':
                c['independent_countercheck']={'witness':5,'square_mod_11':3,'actual_math_kind':'PROOF','retained_label_matches_math':case.get('expected_kind')=='PROOF'}
            row['checks'].append(c)
        else:
            row['checks'].append({'rule':'problem_case_replay','case_id':case.get('case_id',case.get('id')),'family':case.get('family'),'retained_expected_kind':case.get('expected_kind'),'retained_expected_status':case.get('expected_status'),**owner_replay(family,case)})
    return row

def run(family):
    rows=[r for r in read('_scope.json')['files'] if '/'+family+'_' in r['path'] and r['path'].endswith(('.json','.jsonl'))]
    out=file('_'+family+'_automated.jsonl')
    with out.open('w',encoding='utf-8') as dest:
        for r in rows:
            started=time.monotonic()
            try:
                proc=subprocess.run([sys.executable,'-X','utf8',__file__,'worker',family,r['path']],capture_output=True,text=True,encoding='utf-8',timeout=8)
                result=json.loads(proc.stdout) if proc.returncode==0 else {'path':r['path'],'sha256':r['sha256'],'full_source_read':False,'status':'execution_error','stderr':proc.stderr}
            except subprocess.TimeoutExpired:
                result={'path':r['path'],'sha256':r['sha256'],'full_source_read':False,'status':'bounded_attempt_timeout','limits':'Eight-second per-artifact owner replay ceiling; no mathematical result inferred.'}
            result['elapsed_seconds']=round(time.monotonic()-started,3)
            dest.write(json.dumps(result,ensure_ascii=False)+'\n');dest.flush()
    print(family,len(rows),'artifact dispositions')
if __name__=='__main__':
    if sys.argv[1]=='worker':
        try: print(json.dumps(review(sys.argv[3],sys.argv[2]),ensure_ascii=False))
        except Exception as e:
            p=ROOT/sys.argv[3]
            print(json.dumps({'path':sys.argv[3],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'full_source_read':False,'status':'bounded_automated_assessment_with_owner_exception','exception':type(e).__name__,'message':str(e),'checks':[{'rule':'json_parse_and_owner_replay','status':'owner_exception_recorded'}]}))
    else: run(sys.argv[1])
