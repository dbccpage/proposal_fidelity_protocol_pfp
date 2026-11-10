"""Independent small exact models, without Rust or repository-owner imports."""
import sys,itertools,json
from fractions import Fraction as Q
from pathlib import Path
sys.dont_write_bytecode=True
def eye(n):return tuple(tuple(Q(i==j) for j in range(n)) for i in range(n))
def mm(a,b):return tuple(tuple(sum(x*y for x,y in zip(row,col)) for col in zip(*b)) for row in a)
def scale(a,s):return tuple(tuple(x*s for x in row) for row in a)
def plus(a,b):return tuple(tuple(x+y for x,y in zip(ar,br)) for ar,br in zip(a,b))
def diag(xs):return tuple(tuple(x if i==j else Q(0) for j in range(len(xs))) for i,x in enumerate(xs))
def zero(a):return all(x==0 for row in a for x in row)
def project(a):
 first=next(x for row in a for x in row if x);return scale(a,1/first)
def closure(gs,bound,proj=False):
 seen={eye(len(gs[0]))};todo=list(seen)
 for a in todo:
  for g in gs:
   h=mm(a,g)
   if proj:h=project(h)
   if h not in seen:
    if len(seen)==bound:return None
    seen.add(h);todo.append(h)
 return len(seen)
a=((Q(0),Q(-1)),(Q(1),Q(1)));b=((Q(0),Q(1)),(Q(1),Q(0)))
assert closure([a,b],20)==12 and closure([a,b],20,True)==6 and closure([a,b],5) is None
# All bicharacters on C2^2 with F=1, d=1. Admit modularity separately.
points=list(itertools.product(range(2),repeat=2));modular=0;degenerate=0;charges=[]
for coeff in itertools.product(range(2),repeat=4):
 def R(x,y):return Q((-1)**sum(coeff[2*i+j]*x[i]*y[j] for i in range(2) for j in range(2)))
 theta=[R(x,x) for x in points];s=tuple(tuple(R(x,y)*R(y,x) for y in points) for x in points)
 if mm(s,s)!=scale(eye(4),4):degenerate+=1;continue
 modular+=1;p=sum(theta);st=mm(s,diag(theta));assert mm(mm(st,st),st)==scale(mm(s,s),p)
 for x,y,z in itertools.product(range(4),repeat=3):
  value=sum(s[x][t]*s[y][t]*s[z][t] for t in range(4))/4
  assert value==int(tuple((points[x][i]+points[y][i])%2 for i in range(2))==points[z])
 charges.append(0 if p==2 else 4);assert p in (-2,2)
assert (modular,degenerate)==(8,8)
vec_z3=[Q(sum((b+c)%3==a for b,c in itertools.product(range(3),repeat=2)),3) for a in range(3)]
assert vec_z3==[1,1,1] and (1+1)%3!=0
# Independent tensor operators, with row/column coordinates explicitly enumerated.
def flip(n):return tuple(tuple(Q(i//n==j%n and i%n==j//n) for j in range(n*n)) for i in range(n*n))
def embed(r,n,pair):
 coords=list(itertools.product(range(n),repeat=3));other=next(i for i in range(3) if i not in pair)
 return tuple(tuple(r[x[pair[0]]*n+x[pair[1]]][y[pair[0]]*n+y[pair[1]]] if x[other]==y[other] else Q(0) for y in coords) for x in coords)
def spectral(rs,n):
 x,y,z=[embed(r,n,p) for r,p in zip(rs,((0,1),(0,2),(1,2)))];return plus(mm(mm(x,y),z),scale(mm(mm(z,y),x),-1))
def braid(r,n):
 x,y=embed(r,n,(0,1)),embed(r,n,(1,2));return plus(mm(mm(x,y),x),scale(mm(mm(y,x),y),-1))
yang=0;wrong=0
for n in (2,3):
 for u,v in ((Q(-2,3),Q(5,4)),(Q(7,5),Q(-1,3)),(Q(0),Q(2)),(Q(3),Q(1))):
  f=lambda t:plus(scale(eye(n*n),t),flip(n))
  assert zero(spectral([f(u-v),f(u),f(v)],n));yang+=1
  assert not zero(spectral([f(u+v),f(u),f(v)],n));wrong+=1
hecke=0;six=0
for q in (Q(3,2),Q(-2,3),Q(1),Q(-1)):
 h=((q,0,0,0),(0,0,1,0),(0,1,q-1/q,0),(0,0,0,q))
 assert zero(braid(h,2));assert zero(mm(plus(h,scale(eye(4),-q)),plus(h,scale(eye(4),1/q))));hecke+=1
 def v(z):
  aa=q*z-1/(q*z);bb=z-1/z;cc=q-1/q
  return ((aa,0,0,0),(0,bb,cc,0),(0,cc,bb,0),(0,0,0,aa))
 for z1,z2 in ((Q(2,3),Q(-4,5)),(Q(7,2),Q(3,4))):
  assert zero(spectral([v(z1/z2),v(z1),v(z2)],2));six+=1
# Exact finite index/zero-term premises of the bounded Racah formula.
sextuples=0;omitted=0
for k in range(1,7):
 def admitted(a,b,c):return (a+b+c)%2==0 and abs(a-b)<=c<=min(a+b,2*k-a-b)
 for a,b,c,d,e,f in itertools.product(range(k+1),repeat=6):
  if not all(admitted(*t) for t in ((a,b,e),(e,c,d),(b,c,f),(a,f,d))):continue
  sextuples+=1;lower=[(a+b+e)//2,(e+c+d)//2,(b+c+f)//2,(a+f+d)//2];upper=[(a+b+c+d)//2,(a+c+e+f)//2,(b+d+e+f)//2]
  for z in range(max(lower),min(upper)+1):
   indices=[z-x for x in lower]+[x-z for x in upper];assert all(0<=x<=k for x in indices)
   if z>k:omitted+=1;assert z+1>=k+2
out={'status':'completed_bounded','dihedral_linear_order':12,'dihedral_projective_order':6,'bound5_exceeded':True,'C2_squared_bicharacters':16,'modular_bicharacters':modular,'degenerate_bicharacters':degenerate,'central_charge_mod8_counts':{str(c):charges.count(c) for c in sorted(set(charges))},'VecZ3_unverified_Bantay_outputs':[str(x) for x in vec_z3],'VecZ3_nonselfdual_label1_indicator_should_be_zero':True,'yang_additive_controls':yang,'wrong_argument_controls_refused':wrong,'hecke_controls':hecke,'six_vertex_controls':six,'SU2_levels':[1,6],'admissible_racah_sextuples':sextuples,'omitted_terms_with_zero_numerator_and_nonzero_denominator_indices':omitted,'limits':'Own exact finite arithmetic and complete k<=6 index enumeration; not native execution, full Racah coefficient proof, infinite family proof, physical ground-state observation or density certification.'}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
