import sys,copy,itertools,random
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c045_knot_polynomials_from_pd.judge_packet.checkers.dual_evaluator import evaluate_dual
from c045_knot_polynomials_from_pd.judge_packet.checkers import independent_checker as ic
from c045_knot_polynomials_from_pd.reference_solver.solver import solve
from c045_knot_polynomials_from_pd.judge_packet.generate_cases import generate_all_cases

def main():
    rows=[]
    def run(name,c,a=None):
        try:
            if a is None:a=solve(c)
            r=evaluate_dual(c,a)
        except Exception as e:r={'exception':type(e).__name__,'message':str(e)}
        rows.append({'name':name,'case':c,'answer':a,'result':r})
    c={'case_id':'probe','pd':[[1,5,2,4],[3,1,4,6],[5,3,6,2]]}
    run('trefoil control',c)
    run('wrong chirality with omitted optional writhe',{**c,'task':'IDENTIFY'},{'case_id':'probe','status':'SOLVED','identified_knot':'3_1','chirality':'LEFT_HANDED','invariants':{}})
    a=solve(c);a['jones_polynomial']['99']=0;run('noncanonical zero term',c,a)
    a=solve(c);a['jones_polynomial']={('01' if k=='1' else k):v for k,v in a['jones_polynomial'].items()};run('noncanonical leading zero exponent',c,a)
    run('refuse valid trefoil',c,{'case_id':'probe','status':'REFUSED','reason':'NON_PLANAR','witness':{}})
    for pd in ([[1,1,2,2]],[[1,2,2,1]]):run('single crossing unknot',{'case_id':'probe','pd':pd})
    try:g={'generated':len(generate_all_cases())}
    except Exception as e:g={'exception':type(e).__name__,'message':str(e)}
    # Leibniz determinant independently at integer points, versus polynomial Bareiss.
    rng=random.Random(405);count=0;bad=[]
    for n in range(1,5):
        for trial in range(30):
            mat=[[[rng.randrange(-2,3),rng.randrange(-2,3)] for _ in range(n)] for _ in range(n)]
            mat=[[ic._trim(p) for p in row] for row in mat];p=ic._det_z(mat)
            for x in (-2,0,1,3):
                scalar=[[sum(v*x**k for k,v in enumerate(p)) for p in row] for row in mat]
                det=0
                for perm in itertools.permutations(range(n)):
                    term=(-1)**sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n))
                    for i,j in enumerate(perm):term*=scalar[i][j]
                    det+=term
                got=sum(v*x**k for k,v in enumerate(p));count+=1
                if got!=det:bad.append({'n':n,'trial':trial,'x':x,'got':got,'expected':det})
    write('_c045_probes.json',{'controls':rows,'generator_dry_function':g,'independent_leibniz_vs_bareiss':{'comparisons':count,'mismatches':bad},'limits':'No knot classification proof or complete Reidemeister invariance audit; finite determinant checks are bounded.'})
    print([(r['name'],r['result']) for r in rows]);print(g,count,len(bad))
if __name__=='__main__':main()
