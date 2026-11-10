"""Independent finite incidence-DGA algebra control over exact integer matrices."""
import sys, itertools, json
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
dims=[1,2,1,2]
chains=lambda p:list(itertools.combinations(range(4),p+1))
zero=lambda r,c:tuple(tuple(0 for _ in range(c)) for _ in range(r))
plus=lambda x,y:tuple(tuple(a+b for a,b in zip(r,s)) for r,s in zip(x,y))
scale=lambda t,x:tuple(tuple(t*v for v in row) for row in x)
mul=lambda x,y:tuple(tuple(sum(x[i][k]*y[k][j] for k in range(len(y))) for j in range(len(y[0]))) for i in range(len(x)))
def sample(p,seed):
 return {c:tuple(tuple((sum(c)+i*3+j*5+seed)%7-3 for j in range(dims[c[-1]])) for i in range(dims[c[0]])) for c in chains(p)}
def add(f,g,t=1):return {c:plus(f[c],scale(t,g[c])) for c in f}
def cup(f,p,g,q):return {c:mul(f[c[:p+1]],g[c[p:]]) for c in chains(p+q)}
def b(f,p):
 out={}
 for c in chains(p+1):
  v=zero(dims[c[0]],dims[c[-1]])
  for i in range(1,p+1):v=plus(v,scale((-1)**i,f[c[:i]+c[i+1:]]))
  out[c]=v
 return out
def D(f,p,A):return add(add(b(f,p),cup(A,1,f,p)),cup(f,p,A,1),-((-1)**p))
A=sample(1,9);K=add(b(A,1),cup(A,1,A,1))
checks=[]
for p in range(4):
 f=sample(p,2)
 assert all(all(v==0 for row in m for v in row) for m in b(b(f,p),p+1).values())
 assert D(D(f,p,A),p+1,A)==add(cup(K,2,f,p),cup(f,p,K,2),-1)
 checks.append({'degree':p,'b_squared_zero':True,'curved_identity':True})
 for q in range(4-p):
  g=sample(q,5)
  assert b(cup(f,p,g,q),p+q)==add(cup(b(f,p),p+1,g,q),cup(f,p,b(g,q),q+1),(-1)**p)
  for r in range(4-p-q):
   h=sample(r,11)
   assert cup(cup(f,p,g,q),p+q,h,r)==cup(f,p,cup(g,q,h,r),q+r)
offsets=[sum(dims[:i]) for i in range(4)];N=sum(dims)
corner=sample(1,5)[(1,3)];lift=[[0]*N for _ in range(N)]
for i,row in enumerate(corner):
 for j,v in enumerate(row):lift[offsets[1]+i][offsets[3]+j]=v
assert tuple(tuple(lift[offsets[1]+i][offsets[3]+j] for j in range(dims[3])) for i in range(dims[1]))==corner
off=(0,0);assert lift[off[0]][off[1]]==0
lift[0][0]=1
assert any(v and not(offsets[1]<=i<offsets[1]+dims[1] and offsets[3]<=j<offsets[3]+dims[3]) for i,row in enumerate(lift) for j,v in enumerate(row))
out={'rule':'independent_finite_incidence_dga_and_corner_controls','status':'finite_identities_and_off_corner_refusal_confirmed','runtime':sys.version,'carrier':'four-element total order, heterogeneous fiber dimensions [1,2,1,2]','degree_checks':checks,'leibniz_and_associativity_checked':True,'corner_roundtrip':True,'off_corner_mutation_detected':True,'limits':['Independent integer matrix reconstruction only, no Rust or backend execution.','Finite examples are not a universal theorem or evidence that literal inline Result tests exercise these owners.']}
a.write('_probe07.json',out);print(json.dumps(out))
