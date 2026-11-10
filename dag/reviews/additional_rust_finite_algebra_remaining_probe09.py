"""Exact rational and F2 Lie/Cayley controls; no retained execution."""
import sys
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from itertools import product,combinations
from math import comb
import additional_rust_finite_algebra_remaining_audit as a
def mm(x,y):return [[sum((a*b for a,b in zip(row,col)),Q(0)) for col in zip(*y)] for row in x]
def sub(x,y):return [[a-b for a,b in zip(r,s)] for r,s in zip(x,y)]
def rank(x):
 if not x:return 0
 x=[list(map(Q,row)) for row in x];r=0
 for c in range(len(x[0])):
  p=next((i for i in range(r,len(x)) if x[i][c]),None)
  if p is None:continue
  x[r],x[p]=x[p],x[r];v=x[r][c];x[r]=[z/v for z in x[r]]
  for i in range(len(x)):
   if i!=r:
    v=x[i][c];x[i]=[z-v*w for z,w in zip(x[i],x[r])]
  r+=1
  if r==len(x):break
 return r
def ce(c,n,k):
 cols=list(combinations(range(n),k));rows=list(combinations(range(n),k+1));out=[[0]*len(cols) for _ in rows]
 for j,word in enumerate(cols):
  for pos,e in enumerate(word):
   for x in range(n):
    for y in range(x+1,n):
     v=-c.get((x,y,e),0)
     w=word[:pos]+(x,y)+word[pos+1:]
     if not v or len(set(w))!=len(w):continue
     inversions=sum(w[i]>w[j] for i in range(len(w)) for j in range(i+1,len(w)))
     out[rows.index(tuple(sorted(w)))][j]+=v*((-1)**(pos+inversions))
 return out
def jac(c,n,mod=None):
 vals=[sum(c.get((x,y,d),0)*c.get((d,z,e),0)+c.get((y,z,d),0)*c.get((d,x,e),0)+c.get((z,x,d),0)*c.get((d,y,e),0) for d in range(n)) for x,y,z,e in product(range(n),repeat=4)]
 return all((v%mod if mod else v)==0 for v in vals)
f2={(0,0,1):1}
assert all((f2.get((x,y,e),0)+f2.get((y,x,e),0))%2==0 for x,y,e in product(range(2),repeat=3))
assert jac(f2,2,2) and f2[(0,0,1)]==1
bad={}
for x,y,e in [(0,1,0),(0,2,2),(1,2,1)]:bad[x,y,e]=1;bad[y,x,e]=-1
assert not jac(bad,3)
ds=[ce(bad,3,k) for k in range(3)];ranks=list(map(rank,ds))+[0]
betti=[comb(3,k)-ranks[k]-(ranks[k-1] if k else 0) for k in range(4)]
assert ranks==[0,3,1,0] and betti==[1,0,-1,0]
def commdim(mats):
 d=len(mats[0]);rows=[]
 for m in mats:
  for i,j in product(range(d),repeat=2):
   rows.append([int(v==j)*m[i][u]-int(u==i)*m[v][j] for u,v in product(range(d),repeat=2)])
 return d*d-rank(rows)
assert commdim([[[0,-1],[1,0]]])==2
assert commdim([[[1,0],[0,0]],[[0,1],[0,0]]])==1
circle_cases=0
qs=sorted({Q(x,y) for x in range(-5,6) for y in range(1,6)})
def circle(t):return ((1-t*t)/(1+t*t),2*t/(1+t*t))
for s,t in product(qs,repeat=2):
 u,v=circle(s),circle(t);z=(u[0]*v[0]-u[1]*v[1],u[0]*v[1]+u[1]*v[0])
 assert u[0]**2+u[1]**2==1 and u[1]/(1+u[0])==s
 if s*t==1:assert z==(-1,0)
 else:assert z==circle((s+t)/(1-s*t))
 circle_cases+=1
spin_cases=0
for n in range(9):
 d=n+1;z=[[Q(n-2*i,2) if i==j else Q(0) for j in range(d)] for i in range(d)]
 plus=[[Q(j) if i==j-1 else Q(0) for j in range(d)] for i in range(d)]
 minus=[[Q(n-j) if i==j+1 else Q(0) for j in range(d)] for i in range(d)]
 assert sub(mm(z,plus),mm(plus,z))==plus
 assert sub(mm(z,minus),mm(minus,z))==[[-v for v in row] for row in minus]
 assert sub(mm(plus,minus),mm(minus,plus))==[[2*v for v in row] for row in z]
 zp=mm(z,z);pm=mm(plus,minus);mp=mm(minus,plus)
 assert [[zp[i][j]+(pm[i][j]+mp[i][j])/2 for j in range(d)] for i in range(d)]==[[Q(n*(n+2),4) if i==j else 0 for j in range(d)] for i in range(d)]
 spin_cases+=1
dimension=1<<22;assert dimension**3%(1<<64)==0
checks=[{'rule':'characteristic_two_alternation_missing','status':'counterexample','dimension':2,'nonzero_bracket':'[e0,e0]=e1','antisymmetry':True,'jacobi':True,'alternating':False},
 {'rule':'unchecked_noncomplex_betti_subtraction','status':'counterexample','dimension':3,'positive_brackets':[[0,1,0],[0,2,2],[1,2,1]],'differential_ranks':ranks,'integer_betti_formula':betti},
 {'rule':'general_rational_commutant_not_irreducibility_test','status':'counterexamples','irreducible_rational_J_commutant_dimension':2,'reducible_upper_triangular_family_commutant_dimension':1},
 {'rule':'structure_constant_cube_overflow','status':'counterexample','word_bits':64,'dimension':dimension,'wrapped_expected_length':0},
 {'rule':'exact_rational_circle_chart_and_product','status':'passed_bounded','parameter_pairs':circle_cases},
 {'rule':'sl2_brackets_and_casimir','status':'passed_bounded','twice_spins':list(range(spin_cases))}]
a.write('_probe09.json',{'id':'RFA-C009','checks':checks,'limits':'Own rational matrices, exterior differential and finite-field scalar model. No native execution. Noncomplex Betti example deliberately violates its documented caller premise; characteristic2 is allowed by generic Field+ExactRing bounds. The rational J example is irreducible because x²+1 has no rational root; the triangular example visibly preserves span(e0).'} )
print({'checks':len(checks),'circle_pairs':circle_cases,'spins':spin_cases})
