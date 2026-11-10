"""Independent exact norm, circle, finite-prefix and rational enclosure controls."""
import sys,math,itertools
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a

def factors(n):
 d=2;out={}
 while d*d<=n:
  while n%d==0:out[d]=out.get(d,0)+1;n//=d
  d+=1
 if n>1:out[n]=1
 return out
def cmul(z,w):return(z[0]*w[0]-z[1]*w[1],z[0]*w[1]+z[1]*w[0])
def prime_norm(p):
 if p==2:return(1,1)
 g=2
 while pow(g,(p-1)//2,p)!=p-1:g+=1
 root=pow(g,(p-1)//4,p)
 for start in (root,p-root):
  u,v=p,start
  while v*v>p:u,v=v,u%v
  w=math.isqrt(p-v*v)
  if v*v+w*w==p:return(v,w)
 raise AssertionError(p)
def two(n):
 s=math.isqrt(n)
 if s*s==n:return(0,s)
 fs=factors(n)
 if any(p%4==3 and e%2 for p,e in fs.items()):return None
 z=(1,0)
 for p,e in fs.items():
  if p%4==3:z=tuple(x*p**(e//2) for x in z);continue
  w=prime_norm(p)
  for _ in range(e):z=cmul(z,w)
 return tuple(sorted(map(abs,z)))
for n in range(1001):
 z=two(n);brute=any(math.isqrt(n-x*x)**2==n-x*x for x in range(math.isqrt(n)+1))
 assert (z is not None)==brute
 if z:assert sum(x*x for x in z)==n
assert two(3) is None and two(1)==(0,1)
norm_cases=0
for den in range(1,31):
 for num in range(1,31):
  q=Q(num,den);u,v=two(q.numerator),two(q.denominator)
  odd={p for p,e in factors(q.numerator).items() if p%4==3 and e%2}^{p for p,e in factors(q.denominator).items() if p%4==3 and e%2}
  assert bool(odd)==(u is None or v is None)
  if not odd:
   z=cmul(u,(v[0],-v[1]));z=tuple(Q(x,q.denominator) for x in z)
   assert sum(x*x for x in z)==q
  norm_cases+=1
def four(n,budget):
 for x in range(math.isqrt(n),-1,-1):
  budget-=1
  if budget<0:return None
  for y in range(min(x,math.isqrt(n-x*x)),-1,-1):
   budget-=1
   if budget<0:return None
   for z in range(min(y,math.isqrt(n-x*x-y*y)),-1,-1):
    budget-=1
    if budget<0:return None
    w=math.isqrt(n-x*x-y*y-z*z)
    if w<=z and x*x+y*y+z*z+w*w==n:return(x,y,z,w)
for n in range(501):
 out=four(n,100000);assert out is not None and sum(x*x for x in out)==n
assert four(1,0) is None and four(0,2) is None and four(0,3)==(0,0,0,0)
for num in range(16):
 for den in range(1,16):
  q=Q(num,den);out=[Q(x,q.denominator) for x in four(q.numerator*q.denominator,100000) if x]
  assert len(out)<=4 and sum(x*x for x in out)==q

def frac(q):return q-(q.numerator//q.denominator)
def dist(x,y):r=frac(x-y);return min(r,1-r)
def nearest(x,n):
 t=frac(x)*n;k=t.numerator//t.denominator
 return min(((j,dist(x,Q(j,n))) for j in (k,(k+1)%n)),key=lambda r:(r[1],r[0]))
near_cases=0
for n in range(1,21):
 for den in range(1,10):
  for num in range(-25,26):
   q=Q(num,den);assert nearest(q,n)==min(((j,dist(q,Q(j,n))) for j in range(n)),key=lambda r:(r[1],r[0]));near_cases+=1
prefixes=[(0,)]
for level in range(1,8):
 prefixes=[p+(n,) for p in prefixes for n in (p[-1],p[-1]+2**(level-1))]
 assert len(prefixes)==2**level
 for p in prefixes:assert all(p[k]%(2**(k-1))==p[k-1] for k in range(1,len(p)))

def sqrt_interval(q,eps):
 scale=1
 while Q(1,scale)>eps:scale*=2
 root=math.isqrt(q.numerator*scale*scale//q.denominator);lo=Q(root,scale)
 return lo,lo if lo*lo==q else Q(root+1,scale)
sqrt_cases=0
for n in range(41):
 for d in range(1,11):
  for eps in (Q(1,3),Q(1,1000)):
   q=Q(n,d);lo,hi=sqrt_interval(q,eps);assert lo*lo<=q<=hi*hi and hi-lo<=eps;sqrt_cases+=1
def small_atan(x,eps):
 s=Q(0);power=x
 for n in range(1024):
  s+=(-1)**n*power/(2*n+1);power*=x*x;tail=power/(2*n+3)
  if tail<=eps:return tuple(sorted((s,s+(-1)**(n+1)*tail)))
 raise AssertionError('budget')
atan_cases=0
for den in range(2,30):
 for num in range(den//2+1):
  x=Q(num,den);lo,hi=small_atan(x,Q(1,1000));fine=small_atan(x,Q(1,10**15))
  assert lo<=fine[0]<=fine[1]<=hi and hi-lo<=Q(1,1000);atan_cases+=1
checks=[
 {'rule':'two_square_construction_vs_complete_search','status':'bounded_identities_verified','integers':1001,'limits':'Independent trial factor oracle and small Cornacchia reconstruction; not Rust or complete factorization backend execution.'},
 {'rule':'normalized_rational_gaussian_norms','status':'bounded_identities_verified','rational_inputs':norm_cases,'limits':'Reduced positive num/den1..30; obstruction parity and constructed quotient norm replay.'},
 {'rule':'unreduced_gaussian_norm_false_negative','status':'counterexample_found','raw_numerator':3,'raw_denominator':3,'value':'1','norm_class':[],'proposed_obstruction':None,'source_realize_norm':None,'actual_witness':['1','0'],'limits':'Well-defined but unreduced BigRational::new_raw(3,3); normalized BigRational::new(3,3) avoids defect. Source refuses before final replay.'},
 {'rule':'four_squares_and_rational_splits','status':'bounded_identities_verified','integers':501,'rational_inputs':240,'zero_minimum_loop_budget':3,'limits':'Complete descending finite search and exact replay; no universal runtime claim.'},
 {'rule':'nearest_circle_root_vs_exhaustive_lattice','status':'bounded_identities_verified','cases':near_cases},
 {'rule':'finite_dyadic_dual_prefix_extensions','status':'bounded_identities_verified','last_level':7,'last_prefix_count':128,'limits':'Exact finite compatible residues only; no infinite character or topology certified.'},
 {'rule':'dyadic_sqrt_enclosure','status':'bounded_identities_verified','cases':sqrt_cases,'limits':'Exact rational squares and widths; no transcendental oracle.'},
 {'rule':'alternating_atan_enclosure_nesting','status':'bounded_identities_verified','cases':atan_cases,'limits':'Exact coarse/fine alternating bounds within [0,1/2]. Containment uses alternating-series theorem; pi/Machin branch identity and external Interval arithmetic not executed.'}
]
names=['gaussian_norm.rs','gaussian_regular.rs','four_squares.rs','sums_of_squares.rs','rational_circle.rs','rational_turns.rs','circle_haar.rs','certified_angles.rs','dyadic_presentation.rs']
a.write('_probe02.json',{'status':'complete_bounded_controls','runtime':sys.version,'original_program_execution':False,'sources':[a.ev('code/rust/core_number_theory/src/'+p,1,len(a.source('code/rust/core_number_theory/src/'+p))) for p in names],'checks':checks})
print({'checks':len(checks),'nearest_cases':near_cases,'sqrt_cases':sqrt_cases,'atan_cases':atan_cases})
