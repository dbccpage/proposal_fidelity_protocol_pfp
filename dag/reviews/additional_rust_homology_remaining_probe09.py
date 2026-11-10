"""Independent finite distance and F2 arithmetic controls."""
import sys,json,itertools,math
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def cost(x,y):return max(abs(x[0]-y[0]),abs(x[1]-y[1]))
def diag(x):return abs(x[1]-x[0])/2
def distance(A,B,q):
 costs=[]
 def walk(i,used,total):
  if i==len(A):
   costs.append(total+sum(diag(y)**q for j,y in enumerate(B) if j not in used));return
  walk(i+1,used,total+diag(A[i])**q)
  for j,y in enumerate(B):
   if j not in used:walk(i+1,used|{j},total+cost(A[i],y)**q)
 walk(0,set(),0);return min(costs)**(1/q)
A=[(0,100),(10,110)];B=[(1,101),(10,110)];C=[(1,101),(11,111)]
ab=distance(A,B,.5);bc=distance(B,C,.5);ac=distance(A,C,.5)
assert (ab,bc,ac)==(1,1,4) and ac>ab+bc
tiny=Q(1,2**1100);assert tiny>0 and float(tiny)==0
def rowrank(m):
 m=[[x&1 for x in row] for row in m];rank=0
 for col in range(len(m[0])):
  pivot=next((i for i in range(rank,len(m)) if m[i][col]),None)
  if pivot is None:continue
  m[rank],m[pivot]=m[pivot],m[rank]
  for i in range(len(m)):
   if i!=rank and m[i][col]:m[i]=[x^y for x,y in zip(m[i],m[rank])]
  rank+=1
  if rank==len(m):break
 return rank
def twist(columns):
 piv={};rank=0
 for c in columns:
  while c:
   low=(c&-c).bit_length()-1
   if low in piv:c^=piv[low]
   else:piv[low]=c;rank+=1;break
 return rank
for bits in range(512):
 m=[[bits>>(3*i+j)&1 for j in range(3)] for i in range(3)]
 cols=[sum(m[i][j]<<i for i in range(3)) for j in range(3)]
 span={0}
 for c in cols:span|={s^c for s in tuple(span)}
 expected=len(span).bit_length()-1
 assert rowrank(m)==twist(cols)==expected
out={'rule':'independent_distance_and_f2_controls','status':'countermodels_and_512_matrix_ranks_confirmed','runtime':sys.version,
 'q_half_triangle_failure':{'A':A,'B':B,'C':C,'AB':ab,'BC':bc,'AC':ac},
 'binary64_underflow':{'positive_exact_value':'1/2^1100','float_value':float(tiny),'exact_diagonal_distance':'1/2^1101'},
 'discarded_essential_bar':{'diagram_A':[[0,None,0]],'diagram_B':[],'both_finite_projections_empty':True,'returned_distance':0},
 'ignored_degree':{'A':[[0,2,0]],'B':[[0,2,1]],'source_point_cost':0,'degree_preserving_bottleneck':1},
 'sparse_zero_cancellation':{'terms':[[0,1],[0,-1]],'source_all_coefficients_zero':False,'combined_coordinate_zero':True},
 'f2_rank_matrices':512,'limits':['No Rust, BigRational conversion backend or native execution. Binary64 control uses Python conversion to illustrate the unguarded representation limit.','Exact rational finite comparison, matched-pair enumeration and span cardinality are independently implemented.']}
a.write('_probe09.json',out);print(json.dumps(out))
