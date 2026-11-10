"""Independent quadratic arithmetic and root/sign controls; pure rational arithmetic."""
import sys,math,itertools
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a
def mul(x,y,d):return(x[0]*y[0]+d*x[1]*y[1],x[0]*y[1]+x[1]*y[0])
def norm(x,d):return x[0]**2-d*x[1]**2
def rootq(q):
 if q<0:return None
 n,m=math.isqrt(q.numerator),math.isqrt(q.denominator)
 return Q(n,m) if n*n==q.numerator and m*m==q.denominator else None
def root(x,d):
 aa,b=x
 if not b:
  r=rootq(aa)
  if r is not None:return(r,Q(0))
  r=rootq(aa/d)
  return None if r is None else (Q(0),r)
 r=rootq(norm(x,d))
 if r is None:return None
 for t in (r,-r):
  s=rootq((aa+t)/2)
  if s:return(s,b/(2*s))
 return None
def signq(q):return (q>0)-(q<0)
def sign(x,d):
 aa,b=x
 if aa>=0 and b>=0:return int(bool(aa or b))
 if aa<=0 and b<=0:return -int(bool(aa or b))
 return signq(aa*aa-d*b*b)*(1 if aa>0 else -1)
vals=list(map(Q,[-2,-1]))+[Q(-1,2),Q(0),Q(1,2),Q(1),Q(2)]
coords=list(itertools.product(vals,repeat=2));ds=(-7,-3,-2,-1,2,3,5,6,7,10)
rootcases=paircases=signcases=0
for d in ds:
 for x in coords:
  xx=mul(x,x,d);r=root(xx,d);assert r is not None and mul(r,r,d)==xx;rootcases+=1
  r=root(x,d)
  if r is not None:assert mul(r,r,d)==x
  if x!=(0,0):
   n=norm(x,d);assert n!=0 and mul(x,(x[0]/n,-x[1]/n),d)==(1,0)
  if d>0:
   scale=10**8;k=math.isqrt(d*scale*scale);ends=sorted([x[0]+x[1]*Q(k,scale),x[0]+x[1]*Q(k+1,scale)])
   expected=1 if ends[0]>0 else -1 if ends[1]<0 else 0 if x==(0,0) else None
   assert expected is not None and sign(x,d)==expected;signcases+=1
  for y in coords:assert norm(mul(x,y,d),d)==norm(x,d)*norm(y,d);paircases+=1
checks=[{'rule':'quadratic_square_root_replay','status':'bounded_identities_verified','generated_squares':rootcases,'radicands':list(ds),'limits':'Generated-square completeness and returned-root soundness on finite rational grid; no exhaustive search over all possible rational roots.'},{'rule':'quadratic_norm_multiplicativity','status':'bounded_identities_verified','pairs':paircases},{'rule':'quadratic_sign_vs_rational_bracket','status':'bounded_identities_verified','cases':signcases,'scale':10**8},{'rule':'real_complex_conjugation_distinction','status':'observed','real_d2':'Complex conjugation fixes sqrt2; named Galois conjugation negates it.','imaginary_d_minus1':'Both conjugations negate i.','limits':'Matches explicit owner Involution implementation, not inferred from name alone.'}]
p='code/rust/core_number_theory/src/quadratic.rs'
a.write('_probe04.json',{'status':'complete_bounded_controls','runtime':sys.version,'original_program_execution':False,'sources':[a.ev(p,1,1937)],'checks':checks});print({'root_cases':rootcases,'norm_pairs':paircases,'sign_cases':signcases})
