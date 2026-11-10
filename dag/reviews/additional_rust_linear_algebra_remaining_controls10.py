"""Own finite tensor models; no original program execution."""
import sys,json,hashlib,itertools
from fractions import Fraction as Q
from pathlib import Path
sys.dont_write_bytecode=True
def mat(r,c,f):return tuple(tuple(Q(f(i,j)) for j in range(c)) for i in range(r))
def eye(n):return mat(n,n,lambda i,j:i==j)
def tr(a):return sum(a[i][i] for i in range(len(a)))
def mm(a,b):return tuple(tuple(sum(x*y for x,y in zip(row,col)) for col in zip(*b)) for row in a)
def trans(a):return tuple(zip(*a))
def scale(a,x):return tuple(tuple(v*x for v in row) for row in a)
def add(a,b):return tuple(tuple(x+y for x,y in zip(ar,br)) for ar,br in zip(a,b))
def sub(a,b):return add(a,scale(b,-1))
def kron(a,b):return tuple(tuple(x*y for x in ar for y in br) for ar in a for br in b)
def zero(a):return all(x==0 for row in a for x in row)
def realify(p,q):
 m,n=len(p),len(p[0]);return mat(2*m,2*n,lambda i,j:p[i%m][j%n] if i//m==j//n else q[i%m][j%n]*(1 if i//m else -1))
def balance(m,n):
 def entry(r,c):
  x,y=divmod(c,2*n);a,i=divmod(x,m);b,j=divmod(y,n)
  if r%(m*n)!=i*n+j:return 0
  return {(0,0,0):1,(0,1,1):-1,(1,0,1):1,(1,1,0):1}.get((r//(m*n),a,b),0)
 return mat(2*m*n,4*m*n,entry)
balances=0
for m,n in itertools.product(range(1,4),repeat=2):
 t=balance(m,n);p=scale(mm(trans(t),t),Q(1,2));assert mm(t,trans(t))==scale(eye(2*m*n),2);assert mm(p,p)==p;balances+=1
compressions=0
for a,c,b,d in ((1,1,1,1),(1,2,2,1),(2,1,1,2),(2,2,1,1)):
 for seed in range(3):
  p=mat(a,c,lambda i,j:Q(i+2*j+seed-1,3));q=mat(a,c,lambda i,j:Q(2*i-j-seed,5));r=mat(b,d,lambda i,j:Q(i-j+seed,7));s=mat(b,d,lambda i,j:Q(i+j-seed+1,2))
  got=scale(mm(mm(balance(a,b),kron(realify(p,q),realify(r,s))),trans(balance(c,d))),Q(1,2))
  expected=realify(sub(kron(p,r),kron(q,s)),add(kron(p,s),kron(q,r)));assert got==expected;compressions+=1
# Independent multi-index tensor decomposition with a deliberately non-Hermitian trace-one reference.
rho=((Q(2),Q(1)),(Q(0),Q(-1)));h=diag=((Q(1),Q(0)),(Q(0),Q(-1)))
coords=list(itertools.product(range(2),repeat=3));pos={x:i for i,x in enumerate(coords)};ref=kron(kron(rho,rho),rho)
def component(z,S):
 out=[];omit=[j for j in range(3) if j not in S]
 for x in coords:
  row=[]
  for y in coords:
   value=0
   for omitted in itertools.product(range(2),repeat=len(omit)):
    xx=list(x);yy=list(y)
    for j,v in zip(omit,omitted):xx[j]=yy[j]=v
    value+=z[pos[tuple(xx)]][pos[tuple(yy)]]
   for j in omit:value*=rho[x[j]][y[j]]
   row.append(value)
  out.append(tuple(row))
 return tuple(out)
def differential(z):return sub(add(add(component(z,(0,)),component(z,(1,))),component(z,(2,))),scale(ref,2*tr(z)))
def highest(z):
 total=mat(8,8,lambda i,j:0)
 for mask in range(8):
  S=[j for j in range(3) if mask>>j&1];total=add(total,scale(component(z,S),(-1)**(3-len(S))))
 return total
for i,j in itertools.product(range(8),repeat=2):
 z=mat(8,8,lambda r,c:r==i and c==j);p=differential(z);q=sub(z,p);rr=highest(z)
 assert differential(p)==p and differential(q)==mat(8,8,lambda i,j:0) and highest(rr)==rr
 for site in range(3):assert component(p,(site,))==component(z,(site,))
 two=kron(kron(h,h),rho);assert sub(two,differential(two))==two and zero(highest(two))
assert zero(highest(ref))
proper=mat(8,8,lambda i,j:0)
for mask in range(7):
 S=[j for j in range(3) if mask>>j&1];proper=add(proper,scale(component(ref,S),(-1)**(3-len(S))))
assert sub(ref,proper)==scale(ref,2)
def pt(z,l,r):return mat(l*r,l*r,lambda i,j:z[(i//r)*r+j%r][(j//r)*r+i%r])
ptcases=0
for l,r in itertools.product(range(1,4),repeat=2):
 z=mat(l*r,l*r,lambda i,j:2*i-3*j+1);assert pt(pt(z,l,r),l,r)==z and tr(pt(z,l,r))==tr(z);ptcases+=1
# A Schmidt-rank2 pure state has a negative direction after right partial transpose.
v=(Q(1),Q(0),Q(0),Q(2));state=mat(4,4,lambda i,j:v[i]*v[j]/5);w=(0,1,-1,0);p=pt(state,2,2);quad=sum(w[i]*p[i][j]*w[j] for i,j in itertools.product(range(4),repeat=2));assert quad==Q(-4,5)
u=(1<<64)-1;diagnostic=((u+1)//2)*2;assert diagnostic==1<<64
controls=[{'id':'RLA-P30','rule':'Complex balance projector and rectangular operator compression against direct component algebra','status':'completed_bounded','balance_cases':balances,'rectangular_compressions':compressions,'limits':'Own rational models with dimensions1..3 and12 rectangular pairs; supplied complex structure and invertible2 are assumptions, not physical scalar selection.'},{'id':'RLA-P31','rule':'Reference support projectors on every matrix unit of a three-site carrier','status':'completed_bounded','matrix_units':64,'nonhermitian_reference_trace':str(tr(rho)),'order2_vs_order3_distinguished':True,'wrong_inclusion_exclusion_doubles_reference':True,'limits':'Own exact8x8 rational carrier. Projections are reference-dependent algebraic maps; no positivity or orthogonality claimed.'},{'id':'RLA-P32','rule':'Partial transpose involution and explicit positivity failure; empty-axis diagnostic overflow','status':'completed_bounded_with_counterexample','transpose_cases':ptcases,'negative_quadratic_value':str(quad),'u64_empty_axis_rows':str(u),'error_diagnostic_unrepresentable':str(diagnostic),'limits':'Own finite index/arithmetic models and symbolic64-bit bound; no native huge allocation or panic executed.'}]
out={'status':'complete_bounded_controls','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':controls};Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
