import sys,json,itertools,math
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from pathlib import Path
def convbr(v,w):
    n=max(len(v),len(w));out=[0]*n
    for i in range(n):
        for j in range(n):out[i]+=(v[j] if j<len(v) else 0)*(w[i-j] if i>=j and i-j<len(w) else 0)-(w[j] if j<len(w) else 0)*(v[i-j] if i>=j and i-j<len(v) else 0)
    return out
vectors=[v for n in range(1,5) for v in itertools.product((-1,0,1),repeat=n)]
convs=0
for v,w in itertools.product(vectors,repeat=2):assert not any(convbr(v,w));convs+=1
def bracket(c,a,b):return [sum(c[k][i][j]*a[i]*b[j] for i in range(3) for j in range(3)) for k in range(3)]
def tensorjacobi(c):
    return all(sum(c[m][j][k]*c[o][i][m]+c[m][k][i]*c[o][j][m]+c[m][i][j]*c[o][k][m] for m in range(3))==0 for i,j,k,o in itertools.product(range(3),repeat=4))
def nestedjacobi(c):
    basis=[[int(i==j) for i in range(3)] for j in range(3)]
    for a,b,d in itertools.product(basis,repeat=3):
        terms=[bracket(c,a,bracket(c,b,d)),bracket(c,b,bracket(c,d,a)),bracket(c,d,bracket(c,a,b))]
        if any(sum(t[k] for t in terms) for k in range(3)):return False
    return True
choices=[(0,0,0)]+[tuple(s*int(i==k) for i in range(3)) for k in range(3) for s in(-1,1)]
tables=accepted=0
for vals in itertools.product(choices,repeat=3):
    c=[[[0]*3 for _ in range(3)] for _ in range(3)]
    for (i,j),v in zip([(0,1),(0,2),(1,2)],vals):
        for k,x in enumerate(v):c[k][i][j]=x;c[k][j][i]=-x
    t=tensorjacobi(c);assert t==nestedjacobi(c);tables+=1;accepted+=t
small=Q.from_float(1e-200);c=[[[Q(0)]*3 for _ in range(3)] for _ in range(3)]
for k,i,j in[(0,0,1),(1,1,2),(2,2,0)]:c[k][i][j]=small;c[k][j][i]=-small
assert not tensorjacobi(c) and float(small*small)==0.
nan_original=math.nan;collision=nan_original>1e-10;final=sum([])
assert not collision and final<1e-8
assert 1.5<1.-(-1.) # Increasing norm accepted by negative eps.
path_d1=[-1,1];path_d0=[[-1,1,0],[0,-1,1]];composition=[sum(path_d1[i]*path_d0[i][j] for i in range(2)) for j in range(3)]
assert composition==[1,-2,1]
r={'rule':'linfinity_vacuity_and_active_mc_lie_admission','status':'finite_exact_and_diagnostic_countercontrols_confirmed','runtime':sys.version,'convolution_pairs_identically_zero':convs,'antisymmetric_three_dimensional_tables':tables,'jacobi_admitted_tables':accepted,'exact_float_import_detects_underflow_hidden_jacobi':True,'inactive_nan_transfer':{'collision_count':0,'final_residual':0,'fully_resolved':True},'active_negative_eps_accepts_increase':{'old_norm':1,'new_norm':1.5,'eps':-1},'path_declared_d1_composed_with_cellular_d0':composition,'limits':['No Rust/native/original source execution. Inactive L-infinity findings do not imply live behavior.','Active exact Lie table checks concern ordinary ungraded brackets; they do not create graded DGLA or certify floating MC equality.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
