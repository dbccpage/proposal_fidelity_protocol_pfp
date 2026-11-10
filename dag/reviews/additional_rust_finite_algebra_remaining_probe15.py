"""Independent exact finite models; no retained Rust execution/imports."""
import sys,itertools,json
from fractions import Fraction as Q
from pathlib import Path
sys.dont_write_bytecode=True
def mul(x,y):return (x[0]*y[0]+5*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def add(x,y):return (x[0]+y[0],x[1]+y[1])
one=(Q(1),Q(0));zero=(Q(0),Q(0))
phi=(Q(1,2),Q(1,2));inv=(Q(-1,2),Q(1,2));conj=(Q(1,2),Q(-1,2))
f=((inv,one),(inv,tuple(-x for x in inv)))
assert [[add(mul(f[i][0],f[0][j]),mul(f[i][1],f[1][j])) for j in range(2)] for i in range(2)]==[[one,zero],[zero,one]]
assert mul(mul(phi,phi),mul(inv,inv))==one
conjugate_check=mul(mul(conj,conj),mul(inv,inv));assert conjugate_check!=one
def pent(w):
 return all(w(b,c,d)*w(a,(b+c)%2,d)*w(a,b,c)==w((a+b)%2,c,d)*w(a,b,(c+d)%2) for a,b,c,d in itertools.product(range(2),repeat=4))
accepted=[];gauges=0
for v in range(-3,4):
 w=lambda a,b,c:Q(v) if a==b==c==1 else Q(1)
 if pent(w):accepted.append(v)
 if v not in (-1,1):continue
 for values in itertools.product((Q(-1),Q(1,2),Q(2)),repeat=4):
  u=lambda a,b:values[2*a+b]
  transformed=lambda a,b,c:w(a,b,c)*u(a,b)*u((a+b)%2,c)/(u(b,c)*u(a,(b+c)%2))
  assert pent(transformed);gauges+=1
assert accepted==[-1,1]
rank=4
def product(a,b):
 r=[0]*rank
 if a<3 and b<3:r[(a+b)%3]=1
 elif a==b==3:r=[1,1,1,2]
 else:r[3]=1
 return r
for a,b,c,d in itertools.product(range(rank),repeat=4):
 assert sum(product(a,b)[e]*product(e,c)[d] for e in range(rank))==sum(product(b,c)[e]*product(a,e)[d] for e in range(rank))
duals=[0,2,1,3]
for a,b,c in itertools.product(range(rank),repeat=3):
 assert product(a,b)[c]==product(duals[a],c)[b]==product(c,duals[b])[a]
assert max(max(product(a,b)) for a,b in itertools.product(range(rank),repeat=2))==2
out={'status':'completed_bounded','z2_normalized_scalar_cocycle_candidates':7,'accepted_nonzero_scalars':accepted,'nonzero_gauge_coboundaries_checked':gauges,'fibonacci_fixed_F_squared_identity':True,'ordinary_dimension_consistent':True,'conjugate_dimension_with_fixed_F_consistency_value':[str(x) for x in conjugate_check],'conjugate_dimension_rejected':True,'rep_A4_rank4_associativity_and_reciprocity_checked':True,'rep_A4_max_multiplicity':2,'limits':'Own exact rational/Q(sqrt5) and finite tables; no Rust execution or claim of arbitrary category coherence.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out))
