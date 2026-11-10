"""Audit-authored independent finite mathematics; no retained-program execution."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,itertools,math
from pathlib import Path
from fractions import Fraction as Q
def det(a):return a[0][0]*a[1][1]-a[0][1]*a[1][0]
def invariants(a):
 g=math.gcd(*(x for row in a for x in row));d=abs(det(a))
 return [] if not g else [g]+([d//g] if d else [])
count=0
for vals in itertools.product(range(-2,3),repeat=4):
 a=[list(vals[:2]),list(vals[2:])];want=invariants(a)
 for k in (-2,-1,1,2):
  b=[a[0][:],[a[1][j]+k*a[0][j] for j in range(2)]]
  c=[[row[0],row[1]+k*row[0]] for row in a]
  assert invariants(b)==want==invariants(c)
 count+=1
chains=0
for a,b,c,d in itertools.product(range(-2,3),repeat=4):
 if a*c+b*d:continue
 chains+=1
 rank_d=int(bool(a or b));rank_e=int(bool(c or d));h=2-rank_d-rank_e
 kernel=[[-b,a]] if rank_d else [[1,0],[0,1]]
 basis=[[c,d]] if rank_e else []
 reps=[]
 for z in kernel:
  independent=bool(any(z)) and (not basis or (len(basis)==1 and det([basis[0],z])!=0))
  if independent:basis.append(z);reps.append(z)
 assert len(reps)==h and all(a*x+b*y==0 for x,y in reps)
graphs=0
for n in range(1,5):
 edges=list(itertools.combinations(range(n),2))
 for bits in itertools.product((0,1),repeat=len(edges)):
  selected=[e for e,b in zip(edges,bits) if b];lap=[[0]*n for _ in range(n)]
  for i,j in selected:lap[i][i]+=1;lap[j][j]+=1;lap[i][j]-=1;lap[j][i]-=1
  assert all(sum(r)==0 for r in lap)
  for x in itertools.product((-1,0,1),repeat=n):
   quad=sum(x[i]*lap[i][j]*x[j] for i in range(n) for j in range(n))
   assert quad==sum((x[i]-x[j])**2 for i,j in selected)>=0
  graphs+=1
mx=(1<<64)-1
assert mx*mx>mx and mx*2>mx
big=1e308;err=abs((big+big)-(big+big));assert math.isnan(err) and not(err<=0)
out={'status':'bounded_independent_controls_completed','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':[
 {'id':'RLA-P33','rule':'Integer two-by-two determinantal-divisor invariance under elementary shears','status':'observed','matrices':count,'shears_per_matrix':8,'limits':'Independent integer characterization; not execution of Smith algorithm, termination proof or all-size certification.'},
 {'id':'RLA-P34','rule':'Rational chain-step quotient representatives and graph Laplacian quadratic identity','status':'observed','chain_steps':chains,'graphs':graphs,'limits':'Q chain shapes1x2 and2x1, entries-2..2; simple graphs n<=4 and ternary coordinate vectors; no torsion or native execution.'},
 {'id':'RLA-P35','rule':'Admitted empty/sparse dimension arithmetic and finite-input L1 overflow','status':'counterexample_observed','smith_empty_identity_square':str(mx*mx),'sparse_dense_product':str(mx*2),'l1_error':'NaN','l1_passed':False,'limits':'64-bit symbolic size model and Python binary64; no large allocations or Rust execution.'}]}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
