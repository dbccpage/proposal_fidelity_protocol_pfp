import sys,itertools,json
from fractions import Fraction as F
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c051_exact_lp_solver_with_duals.reference_solver.solver import solve
from c051_exact_lp_solver_with_duals.judge_packet.exact_checker import check_solution as primary
from c051_exact_lp_solver_with_duals.judge_packet.independent_checker import check_solution as secondary

def truth_1d(A,b,c):
    lower=F(0);upper=None
    for aa,bb in zip(A,b):
        if aa>0:upper=min(upper,F(bb,aa)) if upper is not None else F(bb,aa)
        elif aa<0:lower=max(lower,F(bb,aa))
        elif bb<0:return {'kind':'INFEASIBLE'}
    if upper is not None and lower>upper:return {'kind':'INFEASIBLE'}
    if c>0 and upper is None:return {'kind':'UNBOUNDED','feasible_point':str(lower)}
    point=upper if c>0 else lower
    return {'kind':'OPTIMAL','value':str(c*point),'point':str(point)}
def verdict(case,a):
    vals=[]
    for fn in (primary,secondary):
        try:vals.append(fn(case,a))
        except Exception as e:vals.append({'exception':type(e).__name__,'message':str(e)})
    return vals
def certificate_math(case,a):
    try:
        A=[[F(x) for x in r] for r in case['A']];b=list(map(F,case['b']));c=list(map(F,case['c']));m=len(b);n=len(c)
        dot=lambda u,v:sum(x*y for x,y in zip(u,v));kind=a.get('kind')
        if kind in ('OPTIMAL','UNBOUNDED'):
            x=list(map(F,a['x']))
            if len(x)!=n or any(v<0 for v in x) or any(dot(row,x)>bb for row,bb in zip(A,b)):return False
        if kind=='OPTIMAL':
            y=list(map(F,a['y']));return len(y)==m and all(v>=0 for v in y) and all(dot([A[i][j] for i in range(m)],y)>=c[j] for j in range(n)) and dot(x,c)==dot(b,y)==F(a['value'])
        if kind=='INFEASIBLE':
            y=list(map(F,a['farkas_y']));return len(y)==m and all(v>=0 for v in y) and all(dot([A[i][j] for i in range(m)],y)>=0 for j in range(n)) and dot(b,y)<0
        if kind=='UNBOUNDED':
            d=list(map(F,a['ray']));return len(d)==n and all(v>=0 for v in d) and all(dot(row,d)<=0 for row in A) and dot(c,d)>0
        return None
    except Exception:return False
def main():
    cases=0;wrong=0;rejected=0;samples=[];accepted_wrong=0
    for m in (1,2):
        for pairs in itertools.product(list(itertools.product(range(-2,3),repeat=2)),repeat=m):
            aa,bb=zip(*pairs)
            for cc in range(-1,2):
                case={'case_id':'audit_interval','A':[[str(x)] for x in aa],'b':list(map(str,bb)),'c':[str(cc)]};ans=solve(case);actual=truth_1d(aa,bb,cc);v=verdict(case,ans);cases+=1
                differs=ans.get('kind')!=actual['kind'] or ans.get('kind')=='OPTIMAL' and ans.get('value')!=actual.get('value')
                wrong+=differs;rejected+=not all(x[0] for x in v);accepted_wrong+=differs and all(x[0] for x in v)
                if differs and len(samples)<6:samples.append({'case':case,'answer':ans,'actual_interval_math':actual,'owner_verdict':v})
    simple={'case_id':'audit_feasible_negative_rhs','A':[['-1']],'b':['-1'],'c':['1']};ans=solve(simple)
    correct={'case_id':simple['case_id'],'status':'SOLVED','kind':'UNBOUNDED','x':['1'],'ray':['1']}
    boolean={'case_id':'audit_boolean_input','A':[[True]],'b':['1'],'c':['1']};bool_ans=solve(boolean)
    out={'one_dimensional_exhaustion':{'cases':cases,'reference_wrong_kind_or_value':wrong,'reference_rejected_by_at_least_one_checker':rejected,'wrong_answers_accepted_by_both':accepted_wrong,'counterexample_samples':samples,'limits':'All one/two-row one-variable systems with A,b coefficients -2..2 and costs -1..1; interval intersection is independent of simplex.'},'phase_one_feasible_case':{'case':simple,'reference_answer':ans,'reference_verdict':verdict(simple,ans),'independent_correct_answer':correct,'correct_answer_verdict':verdict(simple,correct)},'boolean_input_disagreement':{'case':boolean,'answer':bool_ans,'owner_verdict':verdict(boolean,bool_ans)},'limits':['No source modification or provider run.','Existing checker read receipts remain excluded from this slice; their source was consulted as supporting evidence.']}
    write('_c051_probes.json',out);print(json.dumps({'exhaustion':{k:v for k,v in out['one_dimensional_exhaustion'].items() if k!='counterexample_samples'},'phase_one':out['phase_one_feasible_case'],'boolean':out['boolean_input_disagreement']},ensure_ascii=False))
if __name__=='__main__':main()
