import sys,itertools,random,copy,json
from fractions import Fraction as F
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
from additional_challenges_051_059_c053_probe import leibniz
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c054_exact_linear_systems.reference_solver import solve
from c054_exact_linear_systems.judge_packet.exact_checker import check_exact as primary
from c054_exact_linear_systems.judge_packet.independent_checker import independent_check as secondary
def minors_rank(A):
    m=len(A);n=len(A[0]) if m else 0
    for r in range(min(m,n),0,-1):
        for I in itertools.combinations(range(m),r):
            for J in itertools.combinations(range(n),r):
                if leibniz([[A[i][j] for j in J] for i in I]):return r
    return 0
def certificate_math(c,a):
    try:
        if a.get('status')!='SOLVED':return {'valid':None,'reason':'not an algebraic certificate'}
        def rational(x):
            if type(x) not in (str,int):raise ValueError('strict rational input type')
            return F(x)
        A=[[rational(x) for x in row] for row in c['A']];b=[rational(x) for x in c['b']];m=len(A);n=len(A[0]) if m else 0
        if len(b)!=m or any(len(row)!=n for row in A):return {'valid':False,'reason':'shape'}
        if a['kind']=='INCONSISTENT':
            y=list(map(F,a['y']));return {'valid':len(y)==m and all(sum(y[i]*A[i][j] for i in range(m))==0 for j in range(n)) and sum(y[i]*b[i] for i in range(m))!=0,'method':'exact contradiction witness'}
        x=list(map(F,a['x']));N=[list(map(F,v)) for v in a['null_basis']];r=a['rank']
        eq=len(x)==n and len(N)==n-r and all(len(v)==n for v in N) and all(sum(A[i][j]*x[j] for j in range(n))==b[i] for i in range(m)) and all(sum(A[i][j]*v[j] for j in range(n))==0 for i in range(m) for v in N)
        if not eq:return {'valid':False,'reason':'solution/kernel/dimension equations'}
        R=a['rank_rows'];C=a['rank_cols'];J=a['null_rows'];dets=[]
        for M in ([[A[i][j] for j in C] for i in R],[[v[j] for v in N] for j in J]):dets.append(leibniz(M)!=0 if len(M)<=7 else None)
        return {'valid':False if False in dets else None if None in dets else True,'equations_valid':True,'rank_minor_nonzero':dets[0],'null_minor_nonzero':dets[1],'method':'Leibniz minors bounded to order seven; larger minors explicitly unchecked'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__+': '+str(e)}
def evaluate(c,a=None):
    try:
        a=solve(c) if a is None else a
        return {'answer':a,'primary':primary(c,a),'secondary':secondary(c,a),'math':certificate_math(c,a)}
    except Exception as e:return {'exception':type(e).__name__,'message':str(e)}
def main():
    cases=[]
    for v in itertools.product((-1,0,1),repeat=6):cases.append({'case_id':'independent','A':[list(v[:2]),list(v[2:4])],'b':list(v[4:])})
    rng=random.Random(5401)
    for _ in range(64):cases.append({'case_id':'rational','A':[[str(F(rng.randrange(-2,3),rng.randrange(1,4))) for j in range(4)] for i in range(3)],'b':[str(F(rng.randrange(-2,3),rng.randrange(1,4))) for i in range(3)]})
    failures=[]
    for c in cases:
        e=evaluate(c);A=[[F(x) for x in row] for row in c['A']];b=list(map(F,c['b']));r=minors_rank(A);ra=minors_rank([row+[b[i]] for i,row in enumerate(A)]);expected='CONSISTENT' if r==ra else 'INCONSISTENT'
        if 'exception' in e or not e['primary'][0] or not e['secondary'][0] or not e['math']['valid'] or e['answer']['kind']!=expected:failures.append({'case':c,'evaluation':e,'rank':r,'augmented_rank':ra})
    c={'case_id':'base','A':[['1']],'b':['1']};good=solve(c)
    malformed={'case_id':'base','A':[['1/1/99']],'b':['1']}
    float_b={'case_id':'base','A':[['1']],'b':[1.9]}
    bool_c={'case_id':'bool','A':[[True]],'b':[True]}
    unknown=copy.deepcopy(good);unknown['status']='UNKNOWN'
    controls={'non_object':evaluate(None),'extra_fraction_component':evaluate(malformed,good),'fractional_rhs':evaluate(float_b,good),'boolean_entries':evaluate(bool_c),'unknown_status':evaluate(c,unknown),'above_dimension_bound':evaluate({'case_id':'big','A':[[] for _ in range(41)],'b':['0']*41})}
    result={'independent_cases':len(cases),'rank_method':'Enumerate all minors with Leibniz determinants; no owner elimination reused','failures':failures,'controls':controls,'limits':'Finite controls only; no provider or SQLite execution.'};write('_c054_probes.json',result);print(json.dumps({'cases':len(cases),'failures':len(failures),'controls':controls}))
if __name__=='__main__':main()
