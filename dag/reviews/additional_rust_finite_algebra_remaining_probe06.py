"""Own bounded exact cyclotomic controls; no Rust or third-party execution."""
import sys
sys.dont_write_bytecode = True
from fractions import Fraction as Q
import additional_rust_finite_algebra_remaining_audit as a

def trim(p):
    while len(p)>1 and p[-1]==0:p.pop()
    return p
def divide(p,d):
    p=list(p); out=[0]*max(1,len(p)-len(d)+1)
    while len(p)>=len(d) and any(p):
        k=len(p)-len(d); c=p[-1]//d[-1];out[k]=c
        for j,v in enumerate(d):p[k+j]-=c*v
        trim(p)
    assert not any(p)
    return trim(out)
phis={}
for n in range(1,121):
    p=[-1]+[0]*(n-1)+[1]
    for d in range(1,n):
        if n%d==0:p=divide(p,phis[d])
    phis[n]=p
fixed={5:[1]*5,8:[1,0,0,0,1],12:[1,0,-1,0,1],24:[1,0,0,0,-1,0,0,0,1],
       28:[(-1)**(k//2) if k%2==0 else 0 for k in range(13)],
       44:[(-1)**(k//2) if k%2==0 else 0 for k in range(21)],
       52:[(-1)**(k//2) if k%2==0 else 0 for k in range(25)],
       120:[int(k in [0,4,28,32])-int(k in [12,16,20]) for k in range(33)]}
for n,p in fixed.items():assert p==phis[n]

def reduce(p,phi):
    p=list(p);d=len(phi)-1;p += [0]*max(0,d-len(p))
    for k in range(len(p)-1,d-1,-1):
        c=p[k]
        for j,v in enumerate(phi):p[k-d+j]-=c*v
    return tuple(p[:d])
def mul(x,y,phi):
    p=[0]*(len(x)+len(y)-1)
    for i,u in enumerate(x):
        for j,v in enumerate(y):p[i+j]+=u*v
    return reduce(p,phi)
def add(x,y):return tuple(u+v for u,v in zip(x,y))
def scale(x,c):return tuple(u*c for u in x)
def root(n,k):return reduce([0]*(k%n)+[1],phis[n])
def inv(x,phi):
    d=len(x);cols=[mul(x,tuple(int(i==j) for i in range(d)),phi) for j in range(d)]
    m=[[Q(cols[j][i]) for j in range(d)]+[Q(i==0)] for i in range(d)]
    for c in range(d):
        pivot=next(r for r in range(c,d) if m[r][c]);m[c],m[pivot]=m[pivot],m[c]
        s=m[c][c];m[c]=[v/s for v in m[c]]
        for r in range(d):
            if r!=c:
                s=m[r][c];m[r]=[v-s*w for v,w in zip(m[r],m[c])]
    return tuple(row[-1] for row in m)
laws=0;inverse_cases=0
for n in fixed:
    one=root(n,0)
    for k in range(n):
        for j in [-2,-1,0,1,2,n//2]:
            assert mul(root(n,k),root(n,j),phis[n])==root(n,k+j);laws+=1
    for k in [1,2,3]:
        x=add(scale(one,3),root(n,k));assert mul(x,inv(x,phis[n]),phis[n])==one;inverse_cases+=1
gauss=[]
for p in [7,11,13]:
    n=4*p;g=tuple(0 for _ in range(len(phis[n])-1))
    for x in range(p):g=add(g,root(n,4*x*x))
    s=g if p%4==1 else scale(mul(root(n,p),g,phis[n]),-1)
    assert mul(s,s,phis[n])==scale(root(n,0),p);gauss.append(p)
for n,k,m in [(24,3,2),(24,2,3),(120,15,2)]:
    s=add(root(n,k),root(n,-k));assert mul(s,s,phis[n])==scale(root(n,0),m)
s=add(root(120,0),scale(add(root(120,24),root(120,-24)),2))
assert mul(s,s,phis[120])==scale(root(120,0),5)
k=1<<29;exact=(8*k)%24;wrapped=((8*k+(1<<31))%(1<<32)-(1<<31))%24
assert exact==16 and wrapped==0 and root(24,exact)!=root(24,wrapped)
checks=[{'rule':'fixed_polynomials_match_divisor_recurrence','status':'passed_bounded','fields':list(fixed)},
        {'rule':'root_products_and_exact_inverse_replays','status':'passed_bounded','root_products':laws,'inverse_cases':inverse_cases},
        {'rule':'quadratic_gauss_and_explicit_square_root_identities','status':'passed_bounded','gauss_primes':gauss,'other_square_identities':4},
        {'rule':'zeta3_pow_i32_overflow','status':'counterexample','input_k':k,'exact_exponent_mod24':exact,'wrapping_exponent_mod24':wrapped,'debug_behavior':'checked overflow panic'}]
a.write('_probe06.json',{'id':'RFA-C006','checks':checks,'limits':'Own integer/Fraction quotient-ring models; no Rust compilation or execution. Irreducibility of cyclotomic polynomials and positivity in the intended complex embedding remain mathematical premises; square identities do not establish positive-root order. Finite exact inverse replays do not establish every possible operand.'})
print({'checks':len(checks),'root_products':laws,'inverse_cases':inverse_cases})
