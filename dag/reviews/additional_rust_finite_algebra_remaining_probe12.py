"""Independent finite holonomy countercontrols; originals remain inert."""
import sys
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from itertools import product
from hashlib import sha256
import additional_rust_finite_algebra_remaining_audit as a
def mm(x,y):return [[sum(u*v for u,v in zip(r,c)) for c in zip(*y)] for r in x]
def sub(x,y):return [[u-v for u,v in zip(r,s)] for r,s in zip(x,y)]
def neg(x):return [[-v for v in r] for r in x]
I=[[1,0],[0,1]];J=[[0,-1],[1,0]]
def block(A,B,C,D):return [A[0]+B[0],A[1]+B[1],C[0]+D[0],C[1]+D[1]]
Z=[[0,0],[0,0]];L0=block(I,neg(I),neg(I),I);G=block(I,Z,Z,J);Gi=block(I,Z,Z,neg(J));actual=block(I,neg(J),J,I);expected=mm(mm(G,L0),Gi)
assert actual!=expected
v=[[1],[0],[0],[1]];assert mm(actual,v)==[[2],[0],[0],[2]] and mm(expected,v)==[[0],[0],[0],[0]]
checks=[dict(rule='laplacian_gauge_covariance',status='counterexample',fiber_dimension=2,gauge_b=J,actual=actual,expected=expected,transported_parallel_section=[1,0,0,1],actual_section_image=[2,0,0,2])]
w={(0,1):1,(1,2):-1,(2,3):1,(0,3):-1};L=[[0]*4 for _ in range(4)]
for (u,v),weight in w.items():L[u][u]+=weight;L[v][v]+=weight;L[u][v]-=weight;L[v][u]-=weight
assert all(L[i][i]==0 for i in range(4));delta=neg([[2*x for x in r] for r in L]);assert any(v for r in delta for v in r)
checks.append(dict(rule='signed_weights_cancel_degree_bound',status='counterexample',weights=[[u,v,c] for (u,v),c in w.items()],hermitian=True,diagonal=[0]*4,epsilon=2,reported_norm_bound=0,actual_delta=delta,actual_max_absolute_row_sum=4,premise='nonnegative weights violated but not enforced by compute/certificate'))
checks.append(dict(rule='unconstrained_GL_laplacian',status='counterexample',transport=2,inverse='1/2',laplacian=[['1','-2'],['-1/2','1']],hermitian=False,negative_weight_identity_quadratic_form=-4))
matrix_hash=sha256(b'Matrix:1x1:2;').hexdigest()
def conn(u,v):return f'DiscreteConnection:dim=1\nEdge:{u}->{v}:{matrix_hash};\n'
x=conn('a->b','c');y=conn('a','b->c');assert x==y
verts=sorted(['a->b','c','a','b->c'])
prefix='CellComplex:V1\nVertices:4\n'+''.join(v+'\n' for v in verts)+'Edges:1\n'
gx=prefix+'a->b->c\nFaces:0\n';gy=prefix+'a->b->c\nFaces:0\n';assert gx==gy
checks.append(dict(rule='content_hash_noninjective_encoding',status='counterexample',distinct_edges=[['a->b','c'],['a','b->c']],same_vertices=verts,connection_digest=sha256(x.encode()).hexdigest(),graph_digest=sha256(gx.encode()).hexdigest(),cryptographic_collision=False))
checks.append(dict(rule='self_loop_pair_key_inversion',status='counterexample',forward=2,reverse='1/2',get_step_u_u=2,inversion_required='1/2',graph_degree=1,incoming_plus_outgoing=2,laplacian_ignores_loop=True))
A=[[1,1],[0,1]];B=[[1,0],[1,1]];Ai=[[1,-1],[0,1]];Bi=[[1,0],[-1,1]]
comm=mm(mm(mm(Bi,Ai),B),A);assert comm!=I
checks.append(dict(rule='homology_zero_word_nontrivial_transport',status='counterexample',successive_cycle_transports=[A,B,Ai,Bi],path_ordered_result=comm,abelianized_word_zero=True,face_free_flatness_check=True))
# In the built-in nested Gaussian extension, (inner i,inner1) is nonzero but norm=0.
checks.append(dict(rule='nested_gaussian_is_not_field',status='counterexample',outer_element=['inner_i','inner_1'],norm='i^2+1=0',nonzero=True,exact_inverse='ZeroDivision',one_by_one_rank_model=0))
cases=0
for n in range(1,5):
 for f in product(range(-1,n),repeat=n):
  for start in range(n):
   seen={};cur=start;walk=[]
   while cur not in seen and cur!=-1:seen[cur]=len(walk);walk.append(cur);cur=f[cur]
   for k in range(16):
    direct=start
    for _ in range(k):direct=-1 if direct==-1 else f[direct]
    if cur==-1:actual=-1 if k>=len(walk) else walk[k]
    else:
     entry=seen[cur];period=len(walk)-entry;actual=walk[k if k<entry else entry+(k-entry)%period]
    assert actual==direct
   cases+=1
checks.append(dict(rule='all_partial_function_orbits_n_le_4',status='verified_bounded',start_cases=cases,indices_each=16))
a.write('_probe12.json',{'status':'completed_bounded','execution':'own exact finite models and byte-encoding controls only; no original Rust/native execution','checks':checks});print(checks)
