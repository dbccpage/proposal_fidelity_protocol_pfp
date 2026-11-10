"""Independent finite arithmetic controls, with source pins; no Rust imports/execution."""
import sys,math,itertools
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a

def rem(p,q):
 while p and p.bit_length()>=q.bit_length(): p^=q<<(p.bit_length()-q.bit_length())
 return p
def source_irred(p):
 d=p.bit_length()-1
 return all(rem(p,q) for k in range(1,d//2+1) for q in range((1<<k)|1,1<<(k+1),2))
def oracle_irred(p):
 d=p.bit_length()-1
 return d>=1 and all(rem(p,q) for k in range(1,d//2+1) for q in range(1<<k,1<<(k+1)))
def binary_mul(x,y,k,m):
 z=0
 while y:
  if y&1:z^=x
  y>>=1;x<<=1
  if x&(1<<k):x^=m
 return z&((1<<k)-1)
polys=range(1,128)
bad=[p for p in polys if source_irred(p) and not oracle_irred(p)]
assert 1 in bad and 4 in bad and binary_mul(2,2,2,4)==0
law_cases=0
for k in range(1,5):
 for m in range(1<<k,1<<(k+1)):
  if not oracle_irred(m):continue
  for x in range(1<<k):
   assert binary_mul(x,1,k,m)==x
   if x:assert any(binary_mul(x,y,k,m)==1 for y in range(1,1<<k))
   for y in range(1<<k):
    assert binary_mul(x,y,k,m)==binary_mul(y,x,k,m)
    for z in range(1<<k):
     assert binary_mul(x,y^z,k,m)==binary_mul(x,y,k,m)^binary_mul(x,z,k,m)
     assert binary_mul(binary_mul(x,y,k,m),z,k,m)==binary_mul(x,binary_mul(y,z,k,m),k,m)
     law_cases+=1
assert binary_mul(4,1,2,7)==0 and binary_mul(1,4,2,7)==3

def decompose(n,limit):
 if not n:return (0,1)
 r=abs(n);f=s=1;exhausted=True
 for p in range(2,limit+1):
  if any(p%d==0 for d in range(2,math.isqrt(p)+1)):continue
  if p*p>r:exhausted=False;break
  e=0
  while r%p==0:r//=p;e+=1
  s*=p**(e//2);f*=p**(e%2)
 if exhausted:
  t=math.isqrt(r)
  if t*t==r:s*=t;r=1
  elif r>=limit**3:return None
 return ((-1 if n<0 else 1)*f*r,s)
sf_admitted=sf_refused=0
for limit in range(13):
 for n in range(-500,501):
  out=decompose(n,limit)
  if out is None:sf_refused+=1;continue
  f,s=out;assert f*s*s==n and s>=1
  if n:assert all(abs(f)%(d*d) for d in range(2,math.isqrt(abs(f))+1))
  sf_admitted+=1

def factor_trial(n):
 out={};d=2
 while d*d<=n:
  while n%d==0:out[d]=out.get(d,0)+1;n//=d
  d+=1
 if n>1:out[n]=1
 return out
def prime_mr(n):
 if n<2:return False
 for p in (2,3,5,7,11,13,17,19,23,29,31,37):
  if n==p:return True
  if n%p==0:return False
 d=n-1;s=0
 while d%2==0:d//=2;s+=1
 for b in (2,325,9375,28178,450775,9780504,1795265022):
  if b%n==0:continue
  x=pow(b,d,n)
  if x in (1,n-1):continue
  for _ in range(1,s):
   x=x*x%n
   if x==n-1:break
  else:return False
 return True
for n in range(20000):
 assert prime_mr(n)==(n>=2 and all(n%d for d in range(2,math.isqrt(n)+1)))
for n in range(2,1001):
 roots=[0];mod=1
 for p,e in factor_trial(n).items():
  q=p**e
  local=([1,q-1] if p!=2 else [1] if e==1 else [1,3] if e==2 else [1,q-1,1+q//2,q//2-1])
  inv=pow(mod,-1,q)
  roots=[x+mod*((y-x)*inv%q) for x in roots for y in local];mod*=q
 assert sorted(set(roots))==[x for x in range(n) if x*x%n==1]
 assert ([0,n//2] if n%2==0 else [0])==[x for x in range(n) if 2*x%n==0]

checks=[
 {'rule':'binary_irreducibility_all_polynomials_degree_at_most6','status':'counterexample_found','tested':127,'false_admissions':bad,'minimal_nonfield':{'degree':0,'modulus':1},'nonzero_nilpotent':{'degree':2,'modulus':4,'x':2,'x_squared':0}},
 {'rule':'genuine_binary_fields_degree1_to4','status':'bounded_identities_verified','associativity_distributivity_triples':law_cases,'limits':'Enumerated admitted irreducible polynomials and canonical element masks only.'},
 {'rule':'out_of_carrier_binary_mask','status':'counterexample_found','degree':2,'modulus':7,'mul_4_1':0,'mul_1_4':3,'limits':'Canonical masks 0..4 excluded; this demonstrates missing public input admission, not failure on valid field elements.'},
 {'rule':'line_group_subset_count','status':'counterexample_found','degree':1,'generator_count':2,'source_masks':[0,1],'required_subset_masks':[0,1,2,3]},
 {'rule':'squarefree_bounded_trials','status':'bounded_identities_verified','tested':13*1001,'admitted':sf_admitted,'refused':sf_refused,'limits':'Independent square-divisor oracle on integers -500..500 and limits0..12; no complexity equivalence to factoring inferred.'},
 {'rule':'miller_rabin_base_logic','status':'bounded_identities_verified','tested':20000,'limits':'Only n=0..19999 compared against trial primality. Full u64 deterministic-base theorem remains mathematical dependency, not established by this finite control.'},
 {'rule':'residue_crt_and_two_torsion','status':'bounded_identities_verified','moduli':999,'limits':'n=2..1000 compared to complete residue enumeration; factor oracle is independent trial division, not Rust Pollard implementation.'},
 {'rule':'quadratic_gauss_sum_characteristic_two','status':'counterexample_found','GF2_a1_b0_sum':0,'norm_squared':0,'field_order':2,'limits':'Correctly refused by the owner checker; contradiction is only the unrestricted prose claim.'},
 {'rule':'zero_carrier_character_certificate','status':'counterexample_found','constructor':'FiniteField::new(0,1,[])','field_order':0,'linear_sums_checked':0,'gauss_sums_checked':0,'limits':'Unchecked constructor violates its stated field precondition; verifier has no separate nonempty/field admission.'}
]
paths=['rational.rs','finite_field.rs','binary_field.rs','character_sums.rs','integer_factorization.rs','residue.rs']
receipt={'status':'complete_bounded_controls','runtime':sys.version,'original_program_execution':False,'sources':[a.ev('code/rust/core_number_theory/src/'+p,1,len(a.source('code/rust/core_number_theory/src/'+p))) for p in paths],'checks':checks}
a.write('_probe01.json',receipt)
print({'checks':len(checks),'binary_false_admissions':len(bad),'binary_law_triples':law_cases,'squarefree_admitted':sf_admitted,'squarefree_refused':sf_refused})
