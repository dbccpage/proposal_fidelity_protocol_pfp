"""Independent bounded fusion-ring and root-exponent admission controls."""
import sys
sys.dont_write_bytecode=True
from itertools import product
import additional_rust_finite_algebra_remaining_audit as a
def valid(N):
 n=len(N)
 if any(N[0][x][y]!=int(x==y) or N[x][0][y]!=int(x==y) for x,y in product(range(n),repeat=2)):return False
 for x,y,z,w in product(range(n),repeat=4):
  if sum(N[x][y][e]*N[e][z][w] for e in range(n))!=sum(N[y][z][e]*N[x][e][w] for e in range(n)):return False
 dual=[]
 for x in range(n):
  ds=[y for y in range(n) if N[x][y][0]]
  if len(ds)!=1 or N[x][ds[0]][0]!=1:return False
  dual.append(ds[0])
 if any(dual[dual[x]]!=x for x in range(n)):return False
 return all(N[x][y][z]==N[dual[x]][z][y]==N[z][dual[y]][x] for x,y,z in product(range(n),repeat=3))
accepted=[]
for bits in product((0,1),repeat=9):
 N=[[[0]*3 for _ in range(3)] for _ in range(3)]
 for x in range(3):N[0][x][x]=N[x][0][x]=1
 for pair,vals in zip(((1,1),(1,2),(2,2)),(bits[:3],bits[3:6],bits[6:])):
  x,y=pair;N[x][y]=list(vals);N[y][x]=list(vals)
 if valid(N):accepted.append(N)
for k in range(1,7):
 n=k+1;N=[[[int(abs(x-y)<=z<=min(x+y,2*k-x-y) and (x+y+z)%2==0) for z in range(n)] for y in range(n)] for x in range(n)]
 assert valid(N)
ising=[[[1,0,0],[0,1,0],[0,0,1]],[[0,1,0],[1,0,1],[0,1,0]],[[0,0,1],[0,1,0],[1,0,0]]]
counts=[1,0,0]
for length in range(1,65):
 counts=[sum(counts[x]*ising[x][1][z] for x in range(3)) for z in range(3)]
 expected=[0,2**((length-1)//2),0] if length%2 else [2**(length//2-1),0,2**(length//2-1)]
 assert counts==expected
k=(1<<63)-1;step=4
assert k*step>(1<<63)-1 and (k%1)*step==0
checks=[dict(rule='root_exponent_pre_reduction_overflow',status='counterexample',field='GaussianRat',root_order=1,k=k,step=step,checked_mul_refuses=True,actual_root=1),dict(rule='rank3_commutative_binary_fusion_tables',status='verified_bounded',shape_unit_commutative_candidates=512,all_law_accepted=len(accepted),limits='not a categorifiability result'),dict(rule='SU2_level_ring_laws',status='verified_bounded',levels=list(range(1,7))),dict(rule='Ising_path_parity_exact',status='verified_bounded',lengths=64)]
a.write('_probe14.json',{'status':'completed_bounded','execution':'own exact integer models only; no retained Rust/native execution','checks':checks});print(checks)
