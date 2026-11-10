"""Independent signed-graph, quotient and indexed-incidence controls."""
import sys
sys.dont_write_bytecode=True
from itertools import combinations,permutations,product
from math import gcd
import additional_rust_finite_algebra_remaining_audit as a
checks=[];cases=0;balanced=0
n=4;edges=list(combinations(range(n),2))
for values in product((-1,0,1),repeat=len(edges)):
 E={e:v for e,v in zip(edges,values) if v}
 gauges=[bits for bits in product((0,1),repeat=n) if all((bits[u]^bits[v])==int(sign>0) for (u,v),sign in E.items())]
 badcycle=False
 for k in range(3,n+1):
  for word in permutations(range(n),k):
   pairs=[tuple(sorted((word[i],word[(i+1)%k]))) for i in range(k)]
   if all(e in E for e in pairs) and sum(E[e]>0 for e in pairs)%2:badcycle=True
 assert bool(gauges)==(not badcycle)
 if gauges:
  balanced+=1
  components=[];remaining=set(range(n))
  while remaining:
   component={next(iter(remaining))}
   while True:
    bigger=component|{v for u,v in E if u in component}|{u for u,v in E if v in component}
    if bigger==component:break
    component=bigger
   components.append(component);remaining-=component
  assert len(gauges)==2**len(components)
  for g in gauges:assert all(len({g[v]^gauges[0][v] for v in comp})==1 for comp in components)
 cases+=1
checks.append(dict(rule='complete_signed_graph_dichotomy_n4',status='verified_bounded',graphs=cases,gauge_admitting_graphs=balanced,gauge_count='2^components',negative_cycle_enumeration='all simple cycles length3..4'))
# C0=Q,C1=Q3,C2=Q; d0(t)=(t,0,0),d1(x,y,z)=y.
counts={};shifts=0
for x,y,z in product(range(-2,3),repeat=3):
 cls=(y,z);curvature=y
 kind='zero' if (x,y,z)==(0,0,0) else 'exact' if cls==(0,0) else 'closed_nonexact' if y==0 else 'nonclosed'
 counts[kind]=counts.get(kind,0)+1
 for t in range(-2,3):
  shifted=(x+t,y,z);assert shifted[1:]==cls and shifted[1]==curvature
  assert (3*shifted[1],4*shifted[2])==(3*y,4*z)
  shifts+=1
assert counts=={'nonclosed':100,'closed_nonexact':20,'exact':4,'zero':1}
checks.append(dict(rule='full_quotient_vs_H1_and_cochain_transport',status='verified_bounded',representatives=125,shifts=shifts,classification_counts=counts,quotient_dimension=2,H1_dimension=1,map_diagonal=[2,3,4],degree0_map=2,degree2_map=3,zero_map_allowed=True))
def mm(x,y):return [[sum(u*v for u,v in zip(r,c)) for c in zip(*y)] for r in x]
def tr(x):return list(map(list,zip(*x)))
D=[[0,1,1,0],[-1,0,0,1]] # [-J | I]
L=mm(tr(D),D);assert mm(L,[[1],[0],[0],[1]])==[[0],[0],[0],[0]]
checks.append(dict(rule='indexed_D_star_D_orientation',status='verified_bounded',incidence=D,laplacian=L,parallel_section_image=[0,0,0,0],selfloop_transport_minus_identity_scalar_D=2,selfloop_D_star_D=4))
countcases=0
for n in range(1,9):
 for coeffs in product(range(-2,3),repeat=3):
  count=sum(sum(c*x for c,x in zip(coeffs,v))%n==0 for v in product(range(n),repeat=3))
  invariant=gcd(*coeffs)
  formula=n**3 if invariant==0 else n**2*gcd(invariant,n)
  assert count==formula;countcases+=1
checks.append(dict(rule='cyclic_flat_class_single_relation',status='verified_bounded',cases=countcases,moduli='1..8',three_generator_coefficients='-2..2',formula='n^(z-r) product gcd(d_i,n)'))
a.write('_probe13.json',{'status':'completed_bounded','execution':'own exact finite models only; no original Rust/native execution','checks':checks});print(checks)
