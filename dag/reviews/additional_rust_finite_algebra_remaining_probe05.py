"""Independent finite polynomial identities and explicit root-certificate boundaries."""
import sys,itertools,math
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a
def trim(f):
 f=list(map(Q,f))
 while f and not f[-1]:f.pop()
 return f
def add(f,g):return trim([(f[k] if k<len(f) else 0)+(g[k] if k<len(g) else 0) for k in range(max(len(f),len(g)))])
def scale(f,s):return trim([v*s for v in f])
def sub(f,g):return add(f,scale(g,-1))
def mul(f,g):
 if not f or not g:return []
 out=[Q(0)]*(len(f)+len(g)-1)
 for i,x in enumerate(f):
  for j,y in enumerate(g):out[i+j]+=x*y
 return trim(out)
def div(f,g):
 assert g
 r=f[:];q=[Q(0)]*max(0,len(f)-len(g)+1)
 while r and len(r)>=len(g):
  k=len(r)-len(g);c=r[-1]/g[-1];q[k]=c;r=sub(r,[Q(0)]*k+scale(g,c))
 return trim(q),r
def monic(f):return scale(f,1/f[-1]) if f else []
def gcd(f,g):
 while g:f,g=g,div(f,g)[1]
 return monic(f)
def derivative(f):return trim([k*f[k] for k in range(1,len(f))])
def value(f,x):
 out=Q(0)
 for c in reversed(f):out=out*x+c
 return out
def resultant(f,g):
 scalar=Q(1)
 while f and g:
  m,n=len(f)-1,len(g)-1
  if n==0:return scalar*g[0]**m
  if m==0:return scalar*f[0]**n
  r=div(f,g)[1]
  if not r:return Q(0)
  scalar*=(-1)**(m*n)*g[-1]**(m-len(r)+1);f,g=g,r
 return Q(0)
def det(m):
 n=len(m);total=Q(0)
 for perm in itertools.permutations(range(n)):
  term=Q((-1)**sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n)))
  for i,j in enumerate(perm):term*=m[i][j]
  total+=term
 return total
def sylvester(f,g):
 m,n=len(f)-1,len(g)-1;rows=[]
 for base,repeat in ((list(reversed(f)),n),(list(reversed(g)),m)):
  for k in range(repeat):rows.append([Q(0)]*k+base+[Q(0)]*(m+n-k-len(base)))
 return det(rows)
polys=[trim(x) for x in itertools.product((-1,0,1),repeat=3)]
pairs=rescases=0
for f in polys:
 for g in polys:
  if g:
   q,r=div(f,g);assert add(mul(q,g),r)==f and len(r)<len(g);pairs+=1
  if f and g:assert resultant(f,g)==sylvester(f,g);rescases+=1
def sturm(f):
 sf=monic(div(f,gcd(f,derivative(f)))[0]);seq=[sf]
 if len(sf)<2:return seq
 seq.append(derivative(sf))
 while True:
  r=scale(div(seq[-2],seq[-1])[1],-1)
  if not r:return seq
  seq.append(r)
def variations(seq,x):
 signs=[1 if v>0 else -1 for f in seq if (v:=value(f,x))]
 return sum(x!=y for x,y in zip(signs,signs[1:]))
sturm_cases=0
ends=list(map(Q,[-2,-1]))+[Q(-1,2),Q(0),Q(1),Q(2),Q(3)]
for mults in itertools.product(range(3),repeat=3):
 if not any(mults):continue
 f=[Q(1)];known=[]
 for root,m in zip((-1,0,2),mults):
  if m:known.append(root)
  for _ in range(m):f=mul(f,[Q(-root),Q(1)])
 seq=sturm(f)
 for lo,hi in itertools.combinations_with_replacement(ends,2):
  assert variations(seq,lo)-variations(seq,hi)==sum(lo<r<=hi for r in known);sturm_cases+=1
phis={}
for n in range(1,65):
 f=[Q(-1)]+[Q(0)]*(n-1)+[Q(1)]
 for d in range(1,n):
  if n%d==0:f,r=div(f,phis[d]);assert not r
 phis[n]=f
 assert len(f)-1==sum(math.gcd(k,n)==1 for k in range(1,n+1)) and all(c.denominator==1 for c in f)
 product=[Q(1)]
 for d in range(1,n+1):
  if n%d==0:product=mul(product,phis[d])
 assert product==[Q(-1)]+[Q(0)]*(n-1)+[Q(1)]
# Direct source branch model: tolerance >=width skips bisection after endpoint test.
assert value([0,-1,0,1],Q(-2))<0<value([0,-1,0,1],Q(2))
assert value([-1,2],Q(0))<0<value([-1,2],Q(1))
checks=[{'rule':'euclidean_division_reconstruction','status':'bounded_identities_verified','pairs':pairs},{'rule':'resultant_vs_independent_permutation_determinant','status':'bounded_identities_verified','pairs':rescases,'maximum_degree':2},{'rule':'sturm_half_open_counts_vs_known_distinct_roots','status':'bounded_identities_verified','cases':sturm_cases,'roots':[-1,0,2],'multiplicities':[0,1,2]},{'rule':'cyclotomic_divisor_products_and_totient_degrees','status':'bounded_identities_verified','conductors':64,'limits':'Exact polynomial factor-product identities and elementary totient enumeration; no universal irreducibility proof or Rust execution.'},{'rule':'refinement_record_boundaries','status':'counterexample_found','valid_isolating_rational_case':{'polynomial':[-1,2],'interval':[0,1],'tolerance':1,'output':'Isolated([0,1])','root':'1/2 is rational'},'untrusted_multi_root_case':{'polynomial':[0,-1,0,1],'interval':[-2,2],'tolerance':4,'output':'Isolated([-2,2])','distinct_roots':[-1,0,1]},'untrusted_exact_record':{'polynomial':[-2,0,1],'input_root':123,'multiplicity':0,'output':'Exact(123), multiplicity0 unchanged'},'limits':'First case meets actual isolating/simple-root premise and contradicts Isolated irrationality documentation. Other cases violate documented caller premises and show missing admission, not failure of isolate_real_roots.'},{'rule':'factor_product_vs_irreducibility','status':'observed','input':[-1,0,1],'submitted_factors':[[[-1,0,1],1]],'unit':1,'product_replay_accepts':True,'factor_reducible':True,'limits':'verify_product explicitly disclaims irreducibility verification; this is expected contract separation, not an algorithm defect.'}]
paths=['polynomial.rs','polynomial_factorization.rs']
a.write('_probe05.json',{'status':'complete_bounded_controls','runtime':sys.version,'original_program_execution':False,'sources':[a.ev('code/rust/core_number_theory/src/'+p,1,len(a.source('code/rust/core_number_theory/src/'+p))) for p in paths],'checks':checks});print({'division_pairs':pairs,'resultant_pairs':rescases,'sturm_cases':sturm_cases,'cyclotomic_conductors':64})
