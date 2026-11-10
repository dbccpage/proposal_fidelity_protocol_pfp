"""Independent gauge/geometry finite controls, stdlib only."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,itertools,math
from pathlib import Path
from fractions import Fraction as Q
def norm(a):
 n=len(a);p=[0]+[a[i][0] for i in range(1,n)] if n else []
 return [[a[i][j]-p[i]+p[j] for j in range(n)] for i in range(n)]
def moved(a,p):
 n=len(a);b=[[0]*n for _ in range(n)]
 for i in range(n):
  for j in range(n):b[p[i]][p[j]]=a[i][j]
 return b
def canonical(a):return min(tuple(x for r in norm(moved(a,p)) for x in r) for p in itertools.permutations(range(len(a))))
normcases=0
for vals in itertools.product((-1,0,1),repeat=4):
 a=[list(vals[:2]),list(vals[2:])];want=canonical(a)
 for g in itertools.product((-1,0,1),repeat=2):
  b=[[a[i][j]+g[i]-g[j] for j in range(2)] for i in range(2)]
  assert norm(a)==norm(b)
  for p in itertools.permutations(range(2)):assert canonical(moved(b,p))==want
  normcases+=1
maps=desc=obstructed=0
for n in range(5):
 for t in range(5):
  for p in itertools.product(range(t),repeat=n):
   m=[p.count(i) for i in range(t)];criterion=t<=2 or sum(x>0 for x in m)<=1 or len(set(m))<=1
   actual=True
   for u in range(n):
    # Direct P(dg)P^t, not fiber formula.
    b=[[0]*t for _ in range(t)]
    for i in range(n):
     for j in range(n):b[p[i]][p[j]]+=int(i==u)-int(j==u)
    if any(b[i][j]+b[j][k]+b[k][i] for i in range(t) for j in range(t) for k in range(t)):actual=False
   assert criterion==actual
   maps+=1;desc+=criterion;obstructed+=not criterion
def det(a):
 n=len(a)
 return sum((-1)**sum(p[i]>p[j] for i in range(n) for j in range(i+1,n))*math.prod(a[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n)))
def cm(points):
 d=len(points)-1;b=[[0]+[1]*(d+1)]+[[1]+[sum((x-y)**2 for x,y in zip(u,v)) for v in points] for u in points]
 return Q((-1)**(d+1)*det(b),2**d*math.factorial(d)**2)
geometry=0
for d in range(1,5):
 for scales in itertools.product((1,2),repeat=d):
  points=[[0]*d]+[[scales[i]*int(i==j) for j in range(d)] for i in range(d)]
  assert cm(points)==Q(math.prod(scales)**2,math.factorial(d)**2);geometry+=1
bad=[[0,1,1,1],[1,0,1,1],[1,1,0,9],[1,1,9,0]]
badarea=-Q(det(bad),16);assert badarea==-Q(45,16)
wedges=0
for u in itertools.product((-1,0,1),repeat=4):
 for v in itertools.product((-1,0,1),repeat=4):
  c=[Q(u[i]*v[j]-u[j]*v[i],2) for i,j in itertools.combinations(range(4),2)]
  assert c[0]*c[5]-c[1]*c[4]+c[2]*c[3]==0;wedges+=1
out={'status':'bounded_independent_controls_completed','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':[
 {'id':'RLA-P36','rule':'Root normalization, relabeling orbit and complete finite gradient-descent criterion','status':'observed','gauge_cases':normcases,'total_maps':maps,'descending':desc,'obstructed':obstructed,'limits':'Root/gauge panel n2; maps source/target<=4. Complete unit-potential basis suffices for each tested integer-linear map; no retained enumeration dependency executed.'},
 {'id':'RLA-P37','rule':'Cayley-Menger formula versus Euclidean admission, and bivector Plucker identity','status':'observed','coordinate_simplices':geometry,'wedge_pairs':wedges,'admitted_symmetric_positive_squared_lengths':[1,1,9],'nonrealizable_triangle_volume_squared':str(badarea),'forged_so4_diagonal':[2,1,1,1],'forged_so4_first_gram_entry':4,'limits':'Independent exact rational formulas; constructor bypass is source-visible, not native execution. Polynomial correctness does not admit metric geometry.'}]}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
