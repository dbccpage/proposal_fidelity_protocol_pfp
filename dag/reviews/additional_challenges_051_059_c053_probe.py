import sys,itertools,json,random,math
from fractions import Fraction as F
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c053_bareiss_fraction_free_matrix_inversion.reference_solver import solve
from c053_bareiss_fraction_free_matrix_inversion.reference_solver.bareiss import bareiss_determinant,find_null_vector
from c053_bareiss_fraction_free_matrix_inversion.judge_packet.exact_checker import check_solution as primary
from c053_bareiss_fraction_free_matrix_inversion.judge_packet.independent_checker import check_solution as secondary
def leibniz(A):
    n=len(A);total=F(0)
    for p in itertools.permutations(range(n)):
        parity=sum(p[i]>p[j] for i in range(n) for j in range(i+1,n))%2
        total+=(-1 if parity else 1)*math.prod(A[i][p[i]] for i in range(n))
    return total
def certificate_math(c,a):
    try:
        A=[[F(x) for x in r] for r in c['matrix']];n=len(A)
        if not n or any(len(r)!=n for r in A):return {'valid':False,'reason':'matrix shape'}
        if a.get('status')!='SOLVED':return {'valid':None,'reason':'not an algebraic certificate'}
        d=F(a['det']);kind=a['kind']
        if kind=='SINGULAR':
            v=list(map(F,a['null_vector']));return {'valid':d==0 and len(v)==n and any(v) and all(sum(x*y for x,y in zip(r,v))==0 for r in A),'reason':'direct nonzero kernel witness'}
        inv=[[F(x) for x in r] for r in a['inverse']];adj=[[F(x) for x in r] for r in a['adjugate']]
        if d==0 or len(inv)!=n or len(adj)!=n or any(len(r)!=n for r in inv+adj):return {'valid':False,'reason':'inverse dimensions/determinant'}
        identities=all(sum(A[i][k]*inv[k][j] for k in range(n))==int(i==j) and adj[i][j]==d*inv[i][j] for i in range(n) for j in range(n))
        if n<=7:return {'valid':identities and d==leibniz(A),'reason':'Leibniz determinant and exact product identities'}
        return {'valid':None,'identity_equations':identities,'reason':'determinant enumeration ceiling7; scalar determinant not independently pinned here'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__}
def verdict(c,a):return [primary(c,a),secondary(c,a)]
def main():
    matrices=[]
    for n,values in [(2,range(-2,3)),(3,(0,1))]:
        for flat in itertools.product(values,repeat=n*n):matrices.append([[F(flat[n*i+j]) for j in range(n)] for i in range(n)])
    rng=random.Random(5301)
    for _ in range(64):matrices.append([[F(rng.randrange(-3,4),rng.randrange(1,5)) for j in range(4)] for i in range(4)])
    bad=[];singular=0
    for A in matrices:
        c={'case_id':'audit_matrix','matrix':[[str(x) for x in r] for r in A]};ans=solve(c);det=leibniz(A);cert=certificate_math(c,ans);v=verdict(c,ans)
        if det==0:singular+=1
        if F(ans.get('det','0'))!=det or not cert['valid'] or not all(x[0] for x in v):bad.append({'case':c,'answer':ans,'det':str(det),'independent':cert,'owner_verdict':v})
    controls={}
    try:controls['non_object']={'answer':solve(None)}
    except Exception as e:controls['non_object']={'exception':type(e).__name__,'message':str(e)}
    c={'case_id':'audit_above_dimension','matrix':[['0']*31 for _ in range(31)]};ans=solve(c)
    controls['above_dimension_bound']={'dimension':31,'answer_kind':ans['kind'],'owner_verdict':verdict(c,ans),'independent_kernel_valid':certificate_math(c,ans),'limits':'Mathematically valid singular witness beyond the TASK n<=30 contract.'}
    c={'case_id':'audit_det_pin','matrix':[['1','0'],['0','1']]};a={'case_id':c['case_id'],'status':'SOLVED','kind':'INVERTIBLE','det':'5','adjugate':[['5','0'],['0','5']],'inverse':[['1','0'],['0','1']]}
    controls['historic_scalar_spoof_now_rejected']={'owner_verdict':verdict(c,a),'independent':certificate_math(c,a)}
    out={'matrix_controls':{'matrices':len(matrices),'singular':singular,'failures':bad,'domain':'625 integer2x2 matrices,512 binary3x3 matrices,64 seeded rational4x4 matrices; determinant by independent permutation sum.'},'controls':controls,'null_vector_loop_assessment':'The r-=1 assignment does not alter Python for iteration. No invalid first-free-column null vector was reproduced: the earliest skipped column is zero below preceding pivots, so later skipped-row logic need not corrupt that particular vector. Do not promote this code smell to an unsupported mathematical failure.','limits':['Finite algebra checks do not establish a general implementation theorem.','Both judges share canonical-rational syntax but use different determinant calculations.']};write('_c053_probes.json',out);print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
