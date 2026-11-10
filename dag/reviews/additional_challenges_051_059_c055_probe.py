import sys,itertools,copy,json
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c055_assignment_with_potentials.reference_solver import solve
from c055_assignment_with_potentials.judge_packet.exact_checker import check_exact as primary
from c055_assignment_with_potentials.judge_packet.independent_checker import independent_check as secondary
def certificate_math(c,a):
    try:
        if a.get('status')!='SOLVED':return {'valid':None,'reason':'not a certificate'}
        C=[[None if x is None else int(x) for x in r] for r in c['cost']];n=len(C)
        if not n or any(len(r)!=n for r in C):return {'valid':False,'reason':'shape'}
        if a['kind']=='NO_PERFECT_ASSIGNMENT':
            S=a['hall_rows']
            if any(type(i)is not int or i<0 or i>=n for i in S) or len(set(S))!=len(S):return {'valid':False,'reason':'Hall subset'}
            N={j for i in S for j in range(n) if C[i][j] is not None};return {'valid':len(N)<len(S),'rows':len(S),'neighbors':len(N)}
        p=a['sigma'];u=list(map(int,a['u']));v=list(map(int,a['v']));value=int(a['value']);s=sum(u)+sum(v)
        if len(p)!=n or any(type(j)is not int for j in p) or sorted(p)!=list(range(n)) or len(u)!=n or len(v)!=n:return {'valid':False,'reason':'dimensions/permutation'}
        if any(C[i][p[i]] is None for i in range(n)) or sum(C[i][p[i]] for i in range(n))!=value:return {'valid':False,'reason':'primal value'}
        lower=lambda sign:all(u[i]+v[j]<=sign*C[i][j] for i in range(n) for j in range(n) if C[i][j] is not None)
        upper=all(u[i]+v[j]>=C[i][j] for i in range(n) for j in range(n) if C[i][j] is not None)
        valid=(s==value and lower(1)) if c.get('sense','min')=='min' else ((s==-value and lower(-1)) or (s==value and upper))
        return {'valid':valid,'method':'exact weak-duality inequalities and objective equality, both max conventions independently allowed'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__+': '+str(e)}
def permutation_truth(c):
    try:
        C=[[None if x is None else int(x) for x in r] for r in c['cost']];n=len(C)
        if n>8:return {'status':'not_enumerated','reason':'dimension exceeds eight'}
        if not n or any(len(r)!=n for r in C):return {'status':'invalid_shape'}
        values=[sum(C[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n)) if all(C[i][p[i]] is not None for i in range(n))]
        return {'status':'enumerated','feasible_count':len(values),'value':(min(values) if c.get('sense','min')=='min' else max(values)) if values else None}
    except Exception as e:return {'status':'invalid_or_unparsed','exception':type(e).__name__}
MISSING=object()
def evaluate(c,a=MISSING):
    try:a=solve(c) if a is MISSING else a
    except Exception as e:return {'solver_exception':type(e).__name__}
    vs=[]
    for f in (primary,secondary):
        try:vs.append(f(c,a))
        except Exception as e:vs.append({'exception':type(e).__name__})
    return {'answer':a,'owner_verdict':vs,'math':certificate_math(c,a),'permutations':permutation_truth(c)}
def main():
    failures=[];count=0
    for n,alphabet in ((2,(None,-1,0,1)),(3,(None,0))):
        for v in itertools.product(alphabet,repeat=n*n):
            for sense in ('min','max'):
                c={'case_id':'independent','cost':[list(v[i*n:(i+1)*n]) for i in range(n)],'sense':sense};e=evaluate(c);count+=1;t=e['permutations'];a=e['answer']
                if not all(x[0] for x in e['owner_verdict']) or not e['math']['valid'] or (a['kind']=='OPTIMAL')!=(t['value'] is not None) or a['kind']=='OPTIMAL' and int(a['value'])!=t['value']:failures.append({'case':c,'result':e})
    c={'case_id':'max_zero','sense':'max','cost':[[1,-1],[-1,-1]]};a={'case_id':'max_zero','status':'SOLVED','kind':'OPTIMAL','sigma':[0,1],'u':['1','-1'],'v':['0','0'],'value':'0'}
    h={'case_id':'hall','cost':[[None]]};bad={'case_id':'hall','status':'SOLVED','kind':'NO_PERFECT_ASSIGNMENT','hall_rows':[[0]]}
    normal={'case_id':'normal','cost':[[1]]};unknown=solve(normal);unknown['status']='UNKNOWN'
    controls={'valid_standard_max_zero':evaluate(c,a),'unhashable_hall_rows':evaluate(h,bad),'non_object':evaluate(None),'unknown_status':evaluate(normal,unknown),'cost_above_bound':evaluate({'case_id':'cost','cost':[[10**18+1]]}),'dimension_above_bound':evaluate({'case_id':'dimension','cost':[[None]*61 for _ in range(61)]})}
    result={'independent_cases':count,'failures':failures,'controls':controls,'limits':'Finite integer/forbidden matrices; no provider execution.'};write('_c055_probes.json',result);print(json.dumps({'cases':count,'failures':len(failures),'controls':controls}))
if __name__=='__main__':main()
