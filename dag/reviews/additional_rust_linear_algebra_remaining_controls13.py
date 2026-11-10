"""Independent bounded orthogonalization and error-boundary models."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,itertools
from pathlib import Path
from fractions import Fraction as Q
def dot(u,v):return sum(x*y for x,y in zip(u,v))
def mul(a,b):return [[sum(x*y for x,y in zip(r,c)) for c in zip(*b)] for r in a]
independent=dependent=0
for x in itertools.product((-1,0,1),repeat=3):
 for y in itertools.product((-1,0,1),repeat=3):
  if not dot(x,x):dependent+=1;continue
  c=Q(dot(y,x),dot(x,x));z=[Q(v)-c*u for u,v in zip(x,y)]
  if not dot(z,z):dependent+=1;continue
  independent+=1;assert dot(x,z)==0 and all(z[i]+c*x[i]==y[i] for i in range(3))
  p=[[Q(i==j)-Q(x[i]*x[j],dot(x,x))-z[i]*z[j]/dot(z,z) for j in range(3)] for i in range(3)]
  assert mul(p,p)==p and all(dot(r,x)==dot(r,y)==0 for r in p)
assert independent+dependent==729
maxi=(1<<63)-1
assert 3037000500**2>maxi
# Models full drain ownership on error: not a Rust runtime probe.
entries=[(0,0,maxi),(0,0,1),(1,1,7)];before=[0,7]
drained=entries;entries=[]
assert drained[0][2]+drained[1][2]>maxi and entries==[]
z=complex(1,1);assert z*z==2j
out={'status':'bounded_independent_controls_completed','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':[
 {'id':'RLA-P38','rule':'Exact rational Gram-Schmidt triangular replay and complement identities','status':'observed','independent_families':independent,'dependent_families':dependent,'limits':'Two ternary vectors in Q3, exact Fraction; not source execution, general Gram form or normalizing square roots.'},
 {'id':'RLA-P39','rule':'Projector scalar overflow, failed sparse compression state and imaginary Hermitian diagonal','status':'counterexample_observed','projector_norm_square':3037000500**2,'sparse_before_apply_0_1':before,'sparse_after_failed_drain_apply_0_1':[0,0],'one_by_one_input':'1+i','checked_square_result':'2i','limits':'Source-aligned arithmetic/state models only. Drain error semantics statically visible; no retained Rust or external library execution.'}]}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
