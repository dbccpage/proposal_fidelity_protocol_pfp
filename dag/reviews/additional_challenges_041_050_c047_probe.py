import sys,itertools,random,json
sys.dont_write_bytecode=True
from fractions import Fraction
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c047_sequence_law_discovery.judge_packet.exact_checker import check_solution
from c047_sequence_law_discovery.judge_packet.independent_checker import independent_check,_has_integer_root_at_or_after,independent_det
from c047_sequence_law_discovery.reference_solver.rational_linalg import bareiss_determinant
def main():
    rows=[]
    def run(name,c,a):
        out=[]
        for f in(check_solution,independent_check):
            try:out.append(f(c,a))
            except Exception as e:out.append({'exception':type(e).__name__,'message':str(e)})
        rows.append({'name':name,'case':c,'answer':a,'results':out})
    c={'case_id':'probe','terms':[str(n*n+1) for n in range(30)],'held_out_terms':[str(n*n+1) for n in range(30,60)],'r_max':1,'d_max':0,'start_range':[0,5]}
    a={'case_id':'probe','status':'SOLVED','kind':'RECURRENCE','start':58,'polys':[['-3482'],['3365']]}
    run('one last index fit beyond declared start range',c,a)
    run('vacuous start',c,{**a,'start':100})
    # Supply a false hidden-law declaration: neither checker consults it.
    c2={'case_id':'probe','terms':['1']*30,'held_out_terms':['1']*30,'r_max':1,'d_max':0,'law':{'type':'c_finite','characteristic_polynomial':[-2,1]}}
    run('law metadata ignored',c2,{'case_id':'probe','status':'SOLVED','kind':'RECURRENCE','start':0,'polys':[['-1'],['1']]})
    # Full-rank rows only rule out starts<=0, while case permits start1 constant tail.
    c3={'case_id':'probe','terms':['2']+['1']*29,'r_max':1,'d_max':0,'start_range':[0,5]}
    run('narrowed absence range ignores case range',c3,{'case_id':'probe','status':'SOLVED','kind':'NONE_WITHIN_BOUNDS','order':1,'degree':0,'start_range':[0,0],'minor_rows':[0,1]})
    run('far cubic root primary misses secondary rejects',{**c2,'d_max':3}, {'case_id':'probe','status':'SOLVED','kind':'RECURRENCE','start':0,'polys':[['500','-1','500','-1'],['-500','1','-500','1']]})
    rng=random.Random(47);dets=0;bad=[]
    for n in range(1,6):
        for _ in range(20):
            m=[[rng.randrange(-5,6) for _ in range(n)] for _ in range(n)]
            truth=0
            for p in itertools.permutations(range(n)):
                v=(-1)**sum(p[i]>p[j] for i in range(n) for j in range(i+1,n))
                for i,j in enumerate(p):v*=m[i][j]
                truth+=v
            if bareiss_determinant(m)!=truth or independent_det(m)!=truth:bad.append(m)
            dets+=1
    rootcount=0;rootbad=[]
    for co in itertools.product(range(-2,3),repeat=4):
        if not any(co):continue
        for start in (0,3):
            expected=any(sum(c*n**i for i,c in enumerate(co))==0 for n in range(start,20))
            got=_has_integer_root_at_or_after(list(co),start);rootcount+=1
            if got!=expected:rootbad.append([co,start,got,expected])
    # Arithmetic counterexamples to source generator's claimed exact ratios.
    formulas=[{'name':'base22 ratio at n1','lhs':2*7,'rhs':5*3},{'name':'base27 source recurrence at n0','lhs':2*11,'rhs':12*2-1},{'name':'base28 source recurrence at n0','lhs':3*5,'rhs':9*2-1}]
    write('_c047_probes.json',{'controls':rows,'determinants':{'count':dets,'failures':bad},'integer_roots':{'count':rootcount,'failures':rootbad},'source_generator_exact_ratio_failures':formulas,'limits':'Residual agreement through finite retained terms is not all-n law certification. No hidden source was solved or opened beyond ordinary inventory fixtures.'})
    print([(r['name'],r['results']) for r in rows]);print(dets,len(bad),rootcount,len(rootbad))
if __name__=='__main__':main()
