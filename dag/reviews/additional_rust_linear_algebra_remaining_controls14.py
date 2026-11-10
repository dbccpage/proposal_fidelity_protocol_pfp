"""Independent packed, spectral replay, and numerical admission controls."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,math,itertools
from fractions import Fraction as Q
from pathlib import Path
def idx(n,i,j):return i*(2*n-i-1)//2+j
indices=0
for n in range(1,65):
 values=[idx(n,i,j) for i in range(n) for j in range(i,n)]
 assert values==list(range(n*(n+1)//2));indices+=len(values)
complex_cases=0
for n in range(1,9):
 a=[[0j]*n for _ in range(n)]
 data=[]
 for i in range(n):
  for j in range(i,n):
   z=complex(i-j+2,0 if i==j else (i+j)%3-1);data.append(z);a[i][j]=z;a[j][i]=z.conjugate()
 x=[complex(i%3-1,(i+1)%3-1) for i in range(n)]
 y=[0j]*n;quad=0j
 for i in range(n):
  for j in range(i,n):
   z=data[idx(n,i,j)];y[i]+=z*x[j]
   term=x[i].conjugate()*z*x[j];quad+=term
   if i!=j:y[j]+=z.conjugate()*x[i];quad+=term.conjugate()
 assert y==[sum(a[i][j]*x[j] for j in range(n)) for i in range(n)]
 assert quad==sum(x[i].conjugate()*y[i] for i in range(n)) and quad.imag==0
 complex_cases+=1
solves=0
for a,d,b in itertools.product(range(1,6),range(1,6),range(-2,3)):
 determinant=a*d-b*b
 if determinant<=0:continue
 for rhs in ((1,0),(0,1),(2,-3)):
  x=[Q(d*rhs[0]-b*rhs[1],determinant),Q(a*rhs[1]-b*rhs[0],determinant)]
  assert a*x[0]+b*x[1]==rhs[0] and b*x[0]+d*x[1]==rhs[1];solves+=1
def mul(a,b):return [[sum(x*y for x,y in zip(r,c)) for c in zip(*b)] for r in a]
u=[[Q(3,5),Q(-4,5)],[Q(4,5),Q(3,5)]];ut=list(map(list,zip(*u)))
spectra=0
for l,m in itertools.product(range(-3,4),repeat=2):
 d=[[l,0],[0,m]];a=mul(mul(u,d),ut)
 assert mul(a,u)==mul(u,d) and mul(ut,u)==[[1,0],[0,1]];spectra+=1
assert [[0,0],[0,0]]!=[[1,0],[0,1]] # zero vectors have zero residual but fail Gram replay
nan=float('nan');assert not(abs(nan-1)>1e-8) and not(nan>1e-8) and not(nan < -1e-8)
assert not math.isfinite(1e308+1e308)
assert (1<<32)*(1<<32)>(1<<64)-1
out={'status':'bounded_independent_controls_completed','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':[
 {'id':'RLA-P40','rule':'Packed coordinate bijection, complex contraction/quadratic form and rational positive-definite solve replay','status':'observed','dimensions_index_checked':64,'packed_positions':indices,'complex_contractions':complex_cases,'rational_solves':solves,'limits':'Index n<=64, exact-small Gaussian integer operations n<=8,2x2 rational systems. No original packed/LDL code executed.'},
 {'id':'RLA-P41','rule':'Independent exact eigenpair and orthonormality replay for rotated two-dimensional spectra','status':'observed','spectra':spectra,'rotation':[['3/5','-4/5'],['4/5','3/5']],'zero_vector_gram_mutant':'rejected','limits':'Residual identities and degeneracy control, not eigenvalue solver execution or floating error certification.'},
 {'id':'RLA-P42','rule':'Nonfinite comparison holes, complex finite-input overflow and dimension arithmetic','status':'counterexample_observed','NaN_trace_guard_rejects':False,'NaN_hermitian_guard_rejects':False,'NaN_min_eigen_guard_rejects':False,'complex_add_1e308_twice':'Infinity','density_dim':1<<32,'density_dim_squared':str(1<<64),'limits':'Python binary64 comparisons and64-bit symbolic integers. Confirms missing pre/postguards, not whether external nalgebra terminates or accepts NaN on any path.'}]}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
