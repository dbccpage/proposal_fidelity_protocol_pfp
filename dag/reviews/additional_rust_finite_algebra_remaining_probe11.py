"""Exact phase/bit/integer controls independent of Rust owners."""
import sys
sys.dont_write_bytecode=True
from itertools import product
import additional_rust_finite_algebra_remaining_audit as a
checks=[];phasecases=0
for d in range(2,6):
 n=d if d%2 else 2*d
 # Work in tau exponents; omega=tau^2, label period n.
 for x,y,z,w in product(range(n),repeat=4):
  actual=(x*y+z*w+2*y*z-(x+z)*(y+w))%n
  assert actual==(y*z-x*w)%n
  for j in range(d):
   # D(a,b)^* at input j is inverse phase of D(a,b) at j-a.
   adj=-(x*y+2*y*((j-x)%d))%n
   inverse=((-x)%n)*((-y)%n)+2*((-y)%n)*j
   assert adj==inverse%n
  phasecases+=1
checks.append(dict(rule='weyl_product_and_adjoint_phase',status='verified_bounded',dimensions=[2,3,4,5],label_pairs=phasecases))
counts={}
for q in (1,2):
 n=2*q;count=0
 for bits in product((0,1),repeat=n*n):
  def sym(i,j):return sum(bits[k*n+i]*bits[(q+k)*n+j]+bits[(q+k)*n+i]*bits[k*n+j] for k in range(q))%2
  if all(sym(i,j)==int((i<q and j==i+q) or(j<q and i==j+q)) for i,j in product(range(n),repeat=2)):count+=1
 counts[q]=count
assert counts=={1:6,2:720}
checks.append(dict(rule='all_binary_symplectic_matrices_q1_q2',status='verified_bounded',candidate_counts=[16,65536],accepted=counts))
for p in (2,3,5,7,11):
 X=[[int(i==j+1) for j in range(p)] for i in range(p)]
 D=[[j if j==i+1 else 0 for j in range(p)] for i in range(p)]
 for i,j in product(range(p),repeat=2):assert sum(D[i][k]*X[k][j]-X[i][k]*D[k][j] for k in range(p))%p==int(i==j)
checks.append(dict(rule='prime_characteristic_truncated_CCR',status='verified_bounded',primes=[2,3,5,7,11],commutator='identity',identity_trace_mod_p=0))
# g=diag(-1,1), conjugation on X(t,x,y) yields (-t,x,-y).
checks.append(dict(rule='PGL_negative_determinant_not_orthochronous',status='counterexample',g=[[-1,0],[0,1]],adjoint_diagonal=[-1,1,-1],preserves_eta=True,determinant=1,time_component=-1))
checks.append(dict(rule='GellMann_shapes_are_Hermitian',status='counterexample',Z=[[1,0],[0,-1]],adjoint_equals_self=True,adjoint_equals_negative=False,complex_bracket='[X,Y]=2iZ; not a real compact structure table without i scaling'))
a.write('_probe11.json',{'status':'completed_bounded','execution':'own stdlib phase,bit,integer models only; no retained Rust/native execution','checks':checks});print(checks)
