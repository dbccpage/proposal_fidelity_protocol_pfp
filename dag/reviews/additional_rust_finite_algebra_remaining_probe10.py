"""Independent bounded group/cocycle controls; no retained Rust execution."""
import sys
sys.dont_write_bytecode=True
from itertools import product
from fractions import Fraction as Q
from math import isqrt
import additional_rust_finite_algebra_remaining_audit as a
checks=[]
try:
 holds=1+sum([0])==1 and all(1%x==0 for x in [0])
except ZeroDivisionError:
 checks.append(dict(rule='class_equation_zero_class',status='counterexample',order=1,centre_order=1,class_sizes=[0],result='division_by_zero_in_owned_model'))
assert [sum(x*y for x,y in zip([1,99],[1]))]==[1]
checks.append(dict(rule='mckay_extra_value',status='counterexample',input=[1,99],class_values=[1],zip_result=1,expected='reject_wrong_class_count'))
assert isqrt(3)**2!=3
checks.append(dict(rule='rational_cosine_vs_sine',status='counterexample',cosine='1/2',sine_squared='3/4',rational_sine=False))
valid=[]
for bits in product((-1,1),repeat=9):
 alpha=[[1]*4 for _ in range(4)]
 for (i,j),v in zip(product(range(1,4),repeat=2),bits):alpha[i][j]=v
 if not all(alpha[x][y]*alpha[x^y][z]==alpha[y][z]*alpha[x][y^z] for x,y,z in product(range(4),repeat=3)):continue
 radical=[x for x in range(4) if all(alpha[x][y]==alpha[y][x] for y in range(4))]
 assert len(radical) in (1,4)
 # For basis x,y, involution reverses multiplication and preserves norms.
 for x,y in product(range(4),repeat=2):
  assert alpha[x][y]*alpha[x^y][x^y]==alpha[y][y]*alpha[x][x]*alpha[y][x]
 valid.append(len(radical))
assert len(valid)==16
checks.append(dict(rule='all_normalized_sign_cocycles_C2_squared',status='verified_bounded',candidates=512,valid=len(valid),centre_dimensions={str(r):valid.count(r) for r in set(valid)},basis_triples_each=64))
# Connected pair groupoid on two objects times C2; arrows (target,source,g).
arrows=list(product(range(2),range(2),range(2)))
def prod(x,y):return (x[0],y[1],x[2]^y[2]) if x[1]==y[0] else None
def conv(u,v):
 out={}
 for x,c in u.items():
  for y,d in v.items():
   z=prod(x,y)
   if z is not None:out[z]=out.get(z,Q(0))+c*d
 return {z:c for z,c in out.items() if c}
p={(i,i,g):Q(1,2) for i,g in product(range(2),repeat=2)}
assert conv(p,p)==p
for x in arrows:assert conv(p,{x:Q(1)})==conv({x:Q(1)},p)
assert {(x[1],x[0],x[2]):c for x,c in p.items()}==p
checks.append(dict(rule='isotropy_average_pair_groupoid_times_C2',status='verified_bounded',arrows=8,idempotent=True,central_against_basis=8,selfadjoint=True,identity_trace=1))
out={'status':'completed_bounded','execution':'own stdlib exact finite models only; no original Rust/Cargo/native execution','checks':checks}
a.write('_probe10.json',out)
print(out)
