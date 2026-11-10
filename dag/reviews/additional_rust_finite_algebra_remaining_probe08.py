"""Small exhaustive GF2 and numerical-semigroup controls, own implementations."""
import sys
sys.dont_write_bytecode=True
from itertools import product
from heapq import heappop,heappush
from math import gcd
from fractions import Fraction
import additional_rust_finite_algebra_remaining_audit as a
def rref(rows,n):
 rows=list(rows);piv=[];r=0
 for c in range(n):
  if r==len(rows):break
  p=next((i for i in range(r,len(rows)) if rows[i]>>c&1),None)
  if p is None:continue
  rows[r],rows[p]=rows[p],rows[r]
  for i in range(len(rows)):
   if i!=r and rows[i]>>c&1:rows[i]^=rows[r]
  piv.append(c);r+=1
 return rows,piv
def action(rows,x):return sum(((r&x).bit_count()%2)<<i for i,r in enumerate(rows))
matrices=systems=0
for m in range(4):
 for n in range(4):
  for rows in product(range(1<<n),repeat=m):
   rr,piv=rref(rows,n);ker=[]
   for c in range(n):
    if c not in piv:ker.append((1<<c)^sum(((rr[i]>>c)&1)<<p for i,p in enumerate(piv)))
   span={0}
   for v in ker:span|={x^v for x in span}
   expected={x for x in range(1<<n) if action(rows,x)==0}
   assert span==expected and len(span)==1<<len(ker) and len(piv)+len(ker)==n
   for b in range(1<<m):
    aug=[row|(((b>>i)&1)<<n) for i,row in enumerate(rows)];ar,ap=rref(aug,n+1)
    if ap and ap[-1]==n:solutions=set()
    else:
     particular=sum(((ar[i]>>n)&1)<<p for i,p in enumerate(ap));solutions={particular^x for x in span}
    assert solutions=={x for x in range(1<<n) if action(rows,x)==b};systems+=1
   matrices+=1
span_cases=0
for seq in product(range(8),repeat=3):
 basis=[]
 for v in seq:
  for p,b in basis:
   if v>>p&1:v^=b
  if v:
   p=(v&-v).bit_length()-1;basis=[(q,b^v if b>>p&1 else b) for q,b in basis];basis.append((p,v))
 def red(v):
  for p,b in basis:
   if v>>p&1:v^=b
  return v
 span={0}
 for v in seq:span|={x^v for x in span}
 for x in range(8):
  assert (red(x)==0)==(x in span)
  assert all(red(x^v)==red(x) for v in span)
 span_cases+=1
def primes(n):
 out=[];p=2
 while p*p<=n:
  if n%p==0:
   out.append(p)
   while n%p==0:n//=p
  p+=1
 if n>1:out.append(n)
 return out
semigroup_cases=0
for conductor in range(1,121):
 ps=primes(conductor);reachable=[True]+[False]*128
 for k in range(1,129):reachable[k]=any(k>=p and reachable[k-p] for p in ps)
 distances=[0]+[None]*(ps[0]-1) if ps else []
 if ps:
  heap=[(0,0)]
  while heap:
   d,r=heappop(heap)
   if distances[r]!=d:continue
   for p in ps:
    s=(r+p)%ps[0];v=d+p
    if distances[s] is None or v<distances[s]:distances[s]=v;heappush(heap,(v,s))
 for k in range(129):
  answer=k==0 or bool(ps and distances[k%ps[0]] is not None and distances[k%ps[0]]<=k)
  assert answer==reachable[k];semigroup_cases+=1
root_cases=0
for order in range(1,129):
 m=next(m for m in range(1,order+1) if (m if m%2==0 else 2*m)%order==0)
 roots=m if m%2==0 else 2*m
 phase=Fraction(1,m)+(Fraction(1,2) if m%2 else 0)
 phase*=roots//order
 assert phase.denominator==order
 assert m==(order//2 if order%4==2 else order);root_cases+=1
bits=64;largest=(1<<bits)-1
assert 0*largest<=1<<28 and largest+1==1<<bits
checks=[{'rule':'all_gf2_matrices_up_to_3_by_3','status':'passed_bounded','matrices':matrices,'affine_systems':systems},
 {'rule':'incremental_span_coset_reduction','status':'passed_bounded','ordered_generator_triples':span_cases},
 {'rule':'residue_shortest_path_vs_weight_dynamic_program','status':'passed_bounded','cases':semigroup_cases},
 {'rule':'primitive_root_minimal_conductor_rational_phase','status':'passed_bounded','orders':root_cases},
 {'rule':'gf2_zero_axis_augmentation_overflow','status':'counterexample','word_bits':bits,'rows':0,'cols':'usize::MAX','empty_input_storage_words':0,'checked_build_behavior':'self.cols+1 overflow panic before typed error','wrapping_build_behavior':'augmented width wraps0; later vector allocation gate returns TooLarge'}]
a.write('_probe08.json',{'id':'RFA-C008','checks':checks,'limits':'Own bitmask/exhaustive and integer shortest-path models; no native execution or huge allocations. Lam-Leung necessity and full roots-of-unity field theorem remain external mathematical premises, not established by DP or rational phase arithmetic.'})
print({'matrices':matrices,'systems':systems,'semigroup_cases':semigroup_cases})
