"""Offline, independently constructed C058 controls; no source writes."""
import sys,json,itertools,random,io,contextlib
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,file,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c058_straight_line_superoptimization.reference_solver import solve
from c058_straight_line_superoptimization.judge_packet.exact_checker import verify_candidate
from c058_straight_line_superoptimization.judge_packet.independent_checker import check_candidate_indep,independent_eval
from c058_straight_line_superoptimization.reference_solver.evaluator import execute_program
MISSING=object()
def interpret(ops,out,values,width):
    modulus=2**width;state=dict(values)
    for dst,op,*args in ops:
        a=[state[x] if isinstance(x,str) else x for x in args]
        if op=='const':v=a[0]
        elif op=='not':v=modulus-1-a[0]
        elif op=='neg':v=-a[0]
        elif op=='add':v=a[0]+a[1]
        elif op=='sub':v=a[0]-a[1]
        elif op=='mul':v=a[0]*a[1]
        elif op=='and':v=a[0]&a[1]
        elif op=='or':v=a[0]|a[1]
        elif op=='xor':v=a[0]^a[1]
        elif op=='shl':v=a[0]*2**(a[1]%width)
        elif op=='lshr':v=a[0]//2**(a[1]%width)
        elif op=='ashr':v=(a[0] if a[0]<modulus//2 else a[0]-modulus)//2**(a[1]%width)
        else:raise ValueError(op)
        state[dst]=v%modulus
    return state[out]
def math_check(case,answer):
    if not isinstance(answer,dict) or answer.get('status')!='SOLVED':return {'status':'not_a_solved_equivalence_claim'}
    try:
        width=case['width'];names=case['inputs'];rng=random.Random(580051)
        if type(width) is not int or width not in (8,16,32,64):return {'status':'invalid_width_domain'}
        exhaustive=width==8
        tests=itertools.product(range(256),repeat=len(names)) if exhaustive else [tuple(rng.randrange(2**width) for _ in names) for _ in range(128)]
        checked=0
        for values in tests:
            values=dict(zip(names,values));checked+=1
            a=interpret(case['ops'],case['out'],values,width);b=interpret(answer['ops'],answer['out'],values,width)
            if a!=b:return {'status':'counterexample','values':values,'source':a,'candidate':b,'checked':checked}
        return {'status':'exhaustive_equal' if exhaustive else 'bounded_sample_agreement','checked':checked,'length_within_bound':len(answer['ops'])<=case.get('target_len',len(case['ops'])-1),'limits':'Independent arithmetic only; owner schema checks remain separately reported. Wide sample agreement is not universal equivalence.'}
    except Exception as e:return {'status':'exception','type':type(e).__name__,'message':str(e)}
def evaluate(case,answer=MISSING):
    if answer is MISSING:
        try:answer=solve(case)
        except Exception as e:return {'reference_exception':type(e).__name__,'message':str(e)}
    verdict=[]
    for fn in (verify_candidate,check_candidate_indep):
        try:verdict.append(fn(case,answer))
        except Exception as e:verdict.append({'exception':type(e).__name__,'message':str(e)})
    return {'answer':answer,'owner_verdict':verdict,'independent_equivalence':math_check(case,answer)}
def main():
    rare={'case_id':'audit_rare','width':64,'inputs':['x'],'ops':[['t','xor','x',123456789],['n','neg','t'],['u','or','t','n'],['v','lshr','u',63],['o','xor','v',1]],'out':'o','target_len':1}
    wrong={'case_id':'audit_rare','status':'SOLVED','ops':[['r','const',0]],'out':'r'}
    constant={'case_id':'audit_constant','width':8,'inputs':['x'],'ops':[['r','const',0]],'out':'r','target_len':0}
    second={'case_id':'audit_second','width':8,'inputs':['x','y'],'ops':[['r','const',0]],'out':'y','target_len':0}
    reverse={'case_id':'audit_reverse','width':8,'inputs':['x'],'ops':[['c','const',4],['r','sub','c','x']],'out':'r','target_len':1}
    rows={'rare_trigger_false_accept':{'case':rare,'candidate':evaluate(rare,wrong),'reference':evaluate(rare),'explicit_counterexample':{'x':123456789,'source':interpret(rare['ops'],rare['out'],{'x':123456789},64),'candidate':0}},'unrepresentable_zero_op_constant':{'case':constant,'reference':evaluate(constant)},'false_unknown_second_input':{'case':second,'candidate':evaluate(second,{'case_id':second['case_id'],'status':'UNKNOWN','code':'NO_SHORTER_FOUND'})},'missed_reverse_immediate':{'case':reverse,'reference':evaluate(reverse),'valid_short_program':evaluate(reverse,{'case_id':reverse['case_id'],'status':'SOLVED','ops':[['r','sub',4,'x']],'out':'r'})}}
    malformed=[]
    for name,case in [('float_width',{**constant,'width':8.0}),('null_target',{**constant,'target_len':None}),('boolean_constant',{**constant,'ops':[['r','const',True]],'target_len':1})]:
        malformed.append({'name':name,'reference':evaluate(case),'candidate':evaluate(case,{'case_id':case['case_id'],'status':'SOLVED','ops':case['ops'],'out':case['out']})})
    rows['malformed']=malformed
    # Deterministic random straight-line programs, exhaust every 8-bit input.
    rng=random.Random(580058);failures=[];count=0
    for index in range(128):
        ops=[];names=['x']
        for j in range(5):
            op=rng.choice(['const','not','neg','add','sub','mul','and','or','xor','shl','lshr','ashr']);dst='r'+str(j)
            args=[rng.randrange(256)] if op=='const' else [rng.choice(names)] if op in ('not','neg') else [rng.choice(names),rng.choice(names+[rng.randrange(256)])]
            ops.append([dst,op,*args]);names.append(dst)
        for x in range(256):
            expected=interpret(ops,'r4',{'x':x},8);count+=1
            got=[fn(ops,'r4',{'x':x},8) for fn in (execute_program,independent_eval)]
            if any(v!=expected for v in got):failures.append({'program':index,'x':x,'expected':expected,'got':got})
    rows['bounded_interpreter_comparison']={'programs':128,'evaluations':count,'mismatches':failures,'limits':'All inputs for these 128 generated one-input programs, not all programs or wide equivalence.'}
    from c058_straight_line_superoptimization.participant_packet import runner
    fixture=file('_c058_runner_fixture');(fixture/'examples').mkdir(parents=True,exist_ok=True)
    (fixture/'examples/case.json').write_text(json.dumps(constant),encoding='utf8')
    oldfile,oldsolve=runner.__file__,runner.solve
    try:
        runner.__file__=str(fixture/'runner.py');runner.solve=lambda case:{'case_id':case['case_id'],'status':'BANANA'}
        output=io.StringIO()
        with contextlib.redirect_stdout(output):result=runner.main()
        rows['runner_failure_exit']={'return_value':result,'stdout':output.getvalue(),'limits':'Only in-memory module globals redirected; original runner unchanged. Its __main__ calls main without sys.exit.'}
    finally:runner.__file__,runner.solve=oldfile,oldsolve
    rows['stale_generator_path_exists']=(ROOT/'workflows/tasks/certified_challenges/c058_straight_line_superoptimization/judge_packet/cases/c058_b01_xor_sub.json').exists()
    write('_c058_probes.json',rows)
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
