"""Per-artifact parsed assessments; never creates full source-read receipts."""
import sys,json,hashlib,time,subprocess
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,file,read
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
MISSING=object()
def parse(p):
    duplicates=[]
    def pairs(items):
        obj={}
        for k,v in items:
            if k in obj:duplicates.append(k)
            obj[k]=v
        return obj
    return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs),duplicates
def replay(family,case,answer=MISSING):
    if family=='c059':
        from additional_challenges_051_059_c059_probe import evaluate
        return evaluate(case) if answer is MISSING else evaluate(case,answer)
    if family=='c058':
        from additional_challenges_051_059_c058_probe import evaluate
        return evaluate(case) if answer is MISSING else evaluate(case,answer)
    if family=='c057':
        from additional_challenges_051_059_c057_probe import evaluate
        return evaluate(case) if answer is MISSING else evaluate(case,answer)
    if family=='c056':
        from additional_challenges_051_059_c056_probe import evaluate
        return evaluate(case) if answer is MISSING else evaluate(case,answer)
    if family=='c055':
        from additional_challenges_051_059_c055_probe import evaluate
        return {**(evaluate(case) if answer is MISSING else evaluate(case,answer)),'limits':'Exact dual/Hall arithmetic; full independent permutation enumeration only through dimension eight.'}
    if family=='c054':
        from c054_exact_linear_systems.reference_solver import solve
        from c054_exact_linear_systems.judge_packet.exact_checker import check_exact as primary
        from c054_exact_linear_systems.judge_packet.independent_checker import independent_check as secondary
        from additional_challenges_051_059_c054_probe import certificate_math
        if answer is MISSING:answer=solve(case)
        verdict=[]
        for fn in (primary,secondary):
            try:verdict.append(fn(case,answer))
            except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
        return {'answer':answer,'owner_verdict':verdict,'independent_certificate':certificate_math(case,answer),'limits':'Exact solution/kernel arithmetic; Leibniz minors only through order seven.'}
    if family=='c053':
        from c053_bareiss_fraction_free_matrix_inversion.reference_solver import solve
        from c053_bareiss_fraction_free_matrix_inversion.judge_packet.exact_checker import check_solution as primary
        from c053_bareiss_fraction_free_matrix_inversion.judge_packet.independent_checker import check_solution as secondary
        from additional_challenges_051_059_c053_probe import certificate_math
        if answer is MISSING:answer=solve(case)
        verdict=[]
        for fn in (primary,secondary):
            try:verdict.append(fn(case,answer))
            except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
        return {'answer':answer,'owner_verdict':verdict,'independent_certificate':certificate_math(case,answer),'limits':'Exact inverse/kernel arithmetic; independent Leibniz determinant only through dimension seven.'}
    if family=='c052':
        from c052_maxflow_mincut_certificates.reference_solver import solve
        from c052_maxflow_mincut_certificates.judge_packet.exact_checker import check_solution as primary
        from c052_maxflow_mincut_certificates.judge_packet.independent_checker import check_solution as secondary
        from additional_challenges_051_059_c052_probe import certificate_math,bounded_cut_truth
        if answer is MISSING:answer=solve(case)
        verdict=[]
        for fn in (primary,secondary):
            try:verdict.append(fn(case,answer))
            except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
        return {'answer':answer,'owner_verdict':verdict,'independent_certificate':certificate_math(case,answer),'independent_cut_enumeration':bounded_cut_truth(case),'limits':'Input-domain checks and exact flow/cut arithmetic; independent full cut enumeration only through12 vertices.'}
    if family=='c051':
        from c051_exact_lp_solver_with_duals.reference_solver.solver import solve
        from c051_exact_lp_solver_with_duals.judge_packet.exact_checker import check_solution as primary
        from c051_exact_lp_solver_with_duals.judge_packet.independent_checker import check_solution as secondary
        from additional_challenges_051_059_c051_probe import certificate_math
        if answer is MISSING:answer=solve(case)
        verdict=[]
        for fn in (primary,secondary):
            try:verdict.append(fn(case,answer))
            except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
        return {'answer':answer,'owner_verdict':verdict,'independent_certificate_equations':certificate_math(case,answer),'limits':'Direct rational certificate equations, not an independent source of case labels or proof of solver completeness.'}
    raise ValueError('Family replay not yet reviewed/implemented: '+family)
def review(path,family):
    p=ROOT/path;obj,dups=parse(p)
    row={'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'full_source_read':False,'status':'bounded_automated_assessment','checks':[{'rule':'json_structure','status':'parsed','top_level':type(obj).__name__,'keys':sorted(obj) if isinstance(obj,dict) else None,'duplicate_keys':dups}]}
    if isinstance(obj,dict) and 'input' in obj:
        expected=next((obj[k] for k in ('expected_output','expected','output') if k in obj),None)
        check={'rule':'public_case_expected_output','status':'observed','case_id':obj['input'].get('case_id'),'fresh_reference':replay(family,obj['input'])}
        if expected is not None:check['retained_expected_answer']=replay(family,obj['input'],expected)
        row['checks'].append(check)
    elif isinstance(obj,dict) and 'case' in obj and 'expected_output' in obj:
        row['checks'].append({'rule':'public_case_expected_output','status':'observed','fresh_reference':replay(family,obj['case']),'retained_expected_answer':replay(family,obj['case'],obj['expected_output'])})
    elif isinstance(obj,dict) and 'case' in obj:
        answer=next((obj[k] for k in ('corrupted_result','candidate','answer','corrupted_answer','mutated_result','corrupted_solution') if k in obj),MISSING)
        row['checks'].append({'rule':'mutation_or_case_envelope','status':'observed','mutation_id':obj.get('mut_id',obj.get('mutation_id')),'declared_type':obj.get('type'),**replay(family,obj['case'],answer)})
    elif p.name=='case_id_ledger.json':
        row['checks'].append({'rule':'case_identifier_mapping','status':'parsed','entries':len(obj),'all_string_pairs':all(isinstance(k,str) and isinstance(v,str) for k,v in obj.items()),'distinct_targets':len(set(obj.values())),'existing_target_case_files':sum((p.parent/'cases'/(v+'.json')).exists() for v in obj.values()),'limits':'Identifier mapping only; not truth labels or provenance authentication.'})
    elif p.name in ('accounting.json','manifest.json'):
        row['checks'].append({'rule':'metadata_declaration','status':'parsed','record':obj,'limits':'Declaration only; not actual execution, spend, custody or mathematical truth.'})
    else:row['checks'].append({'rule':'problem_case_replay','status':'observed','case_id':obj.get('case_id'),**replay(family,obj)})
    return row
def run(family):
    rows=[r for r in read('_scope.json')['files'] if '/'+family+'_' in r['path'] and r['path'].endswith('.json')]
    with file('_'+family+'_automated.jsonl').open('w',encoding='utf-8') as dest:
        for r in rows:
            t=time.monotonic()
            try:
                proc=subprocess.run([sys.executable,'-X','utf8',__file__,'worker',family,r['path']],capture_output=True,text=True,encoding='utf-8',timeout=8)
                result=json.loads(proc.stdout) if proc.returncode==0 else {'path':r['path'],'sha256':r['sha256'],'full_source_read':False,'status':'execution_error','checks':[{'rule':'bounded_replay','status':'execution_error','stderr':proc.stderr}]}
            except subprocess.TimeoutExpired:result={'path':r['path'],'sha256':r['sha256'],'full_source_read':False,'status':'bounded_replay_timeout','checks':[{'rule':'bounded_replay','status':'timeout','seconds':8,'limits':'No result or mathematical verdict is inferred.'}]}
            result['elapsed_seconds']=round(time.monotonic()-t,3);dest.write(json.dumps(result,ensure_ascii=False)+'\n');dest.flush()
    print(family,len(rows),'bounded artifact dispositions')
if __name__=='__main__':
    if sys.argv[1]=='worker':
        try:print(json.dumps(review(sys.argv[3],sys.argv[2]),ensure_ascii=False))
        except Exception as e:
            p=ROOT/sys.argv[3];obj,dups=parse(p)
            print(json.dumps({'path':sys.argv[3],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'full_source_read':False,'status':'bounded_parse_with_replay_exception','checks':[{'rule':'json_structure','status':'parsed','top_level':type(obj).__name__,'keys':sorted(obj) if isinstance(obj,dict) else None,'duplicate_keys':dups},{'rule':'bounded_replay','status':'exception','type':type(e).__name__,'message':str(e)}]},ensure_ascii=False))
    else:run(sys.argv[1])

