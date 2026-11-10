"""Independent bounded finite-poset census and invariant controls."""
import sys,itertools,json,math
from functools import lru_cache
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def all_relations(n):
 pairs=[(i,j) for i in range(n) for j in range(n) if i!=j]
 for mask in range(1<<len(pairs)):
  r={p for k,p in enumerate(pairs) if mask>>k&1}
  if any((j,i) in r for i,j in r):continue
  if any((i,k) not in r for i,j in r for z,k in r if j==z):continue
  yield frozenset(r)
def incremental(n):
 out=[]
 def extend(k,r):
  if k==n:out.append(frozenset(r));return
  for dm in range(1<<k):
   D={i for i in range(k) if dm>>i&1}
   if any(y in D and x not in D for x,y in r):continue
   for um in range(1<<k):
    U={i for i in range(k) if um>>i&1}
    if D&U or any((x,y) not in r for x in D for y in U):continue
    if any(x in U and y not in U for x,y in r):continue
    extend(k+1,r|{(x,k) for x in D}|{(k,y) for y in U})
 extend(0,set());return out
def width_certificate(n,r):
 succ=[[v for v in range(n) if (u,v) in r] for u in range(n)]
 mr=[None]*n;ml=[None]*n
 def aug(u,seen):
  for v in succ[u]:
   if v in seen:continue
   seen.add(v)
   if mr[v] is None or aug(mr[v],seen):mr[v]=u;ml[u]=v;return True
  return False
 for u in range(n):aug(u,set())
 chains=[]
 for start in range(n):
  if mr[start] is None:
   c=[start]
   while ml[c[-1]] is not None:c.append(ml[c[-1]])
   chains.append(c)
 L={u for u in range(n) if ml[u] is None};R=set();stack=list(L)
 while stack:
  u=stack.pop()
  for v in succ[u]:
   if v not in R:
    R.add(v)
    if mr[v] is not None and mr[v] not in L:L.add(mr[v]);stack.append(mr[v])
 anti=L-R
 assert len(anti)==len(chains)
 assert sorted(i for c in chains for i in c)==list(range(n))
 assert all((u,v) in r for c in chains for u,v in zip(c,c[1:]))
 assert not any((u,v) in r for u in anti for v in anti)
 return len(anti)
def canonical(n,r):
 inv=[(sum(v==i for u,v in r),sum(u==i for u,v in r)) for i in range(n)]
 blocks=[[i for i in range(n) if inv[i]==v] for v in sorted(set(inv))]
 lists=[]
 for perms in itertools.product(*(list(itertools.permutations(b)) for b in blocks)):
  order=[v for p in perms for v in p];lab={v:i for i,v in enumerate(order)}
  lists.append(tuple(sorted((lab[u],lab[v]) for u,v in r)))
 return min(lists,default=())
counts=[];unlabelled=[];checked=0;intervals=0
for n in range(5):
 rs=list(all_relations(n));inc=incremental(n)
 assert len(inc)==len(set(inc)) and set(inc)==set(rs)
 classes={}
 for r in rs:
  checked+=1
  subsets=[set(c) for k in range(n+1) for c in itertools.combinations(range(n),k)]
  width=max(len(s) for s in subsets if not any((u,v) in r for u in s for v in s))
  assert width_certificate(n,r)==width
  perms=[p for p in itertools.permutations(range(n)) if all(p.index(u)<p.index(v) for u,v in r)]
  @lru_cache(None)
  def extensions(s):
   if not s:return 1
   S=set(s)
   return sum(extensions(tuple(sorted(S-{x}))) for x in S if not any((x,y) in r for y in S))
  assert extensions(tuple(range(n)))==len(perms)
  order=perms[0];mu={(x,y):int(x==y) for x in range(n) for y in range(n)}
  for x in range(n):
   for y in order:
    if (x,y) in r:mu[x,y]=-sum(mu[x,z] for z in range(n) if (z,y) in r)
  for x in range(n):
   for y in range(n):
    zs=[z for z in range(n) if (x==z or (x,z) in r) and (z==y or (z,y) in r)]
    assert sum(mu[x,z] for z in zs)==sum(mu[z,y] for z in zs)==int(x==y)
    if (x,y) in r:
     interior={z for z in range(n) if (x,z) in r and (z,y) in r}
     chi=sum((-1)**(len(s)-1) for s in subsets if s and s<=interior and all((u,v) in r or (v,u) in r for u,v in itertools.combinations(s,2)))
     assert mu[x,y]==chi-1;intervals+=1
  key=canonical(n,r);classes[key]=classes.get(key,0)+1
  aut=sum({(p[u],p[v]) for u,v in r}==set(r) for p in itertools.permutations(range(n)))
  assert math.factorial(n)%aut==0
 for key,copies in classes.items():
  rr=set(key);aut=sum({(p[u],p[v]) for u,v in rr}==rr for p in itertools.permutations(range(n)))
  assert copies*aut==math.factorial(n)
 counts.append(len(rs));unlabelled.append(len(classes))
assert counts==[1,1,3,19,219] and unlabelled==[1,1,2,5,16]
memo={};visited=[]
def late_budget(mask,limit):
 if mask==0:return 1
 if mask in memo:return memo[mask]
 if len(memo)>=limit:raise ValueError('budget')
 visited.append(mask)
 x=mask.bit_length()-1
 result=late_budget(mask&~(1<<x),limit)
 memo[mask]=result;return result
assert late_budget(7,1)==1 and len(memo)==3
out={'rule':'finite_poset_census_invariants_and_budget_controls','status':'243_posets_agree_and_budget_counterexample_confirmed','runtime':sys.version,
 'labelled_counts':counts,'unlabelled_counts':unlabelled,'posets_checked':checked,'interval_euler_checks':intervals,
 'checks':['incremental enumeration equals all strict relation subsets without duplicates','matching width certificate equals exhaustive antichain width','downset extension count equals all permutations','Mobius two-sided convolution and open-interval reduced Euler','canonical class multiplicities satisfy orbit-stabilizer'],
 'late_budget':{'chain_elements':3,'budget':1,'result':1,'nonempty_downsets_visited':len(visited),'memo_entries':len(memo)},
 'closure_expansion':{'chain_elements':40,'maximal_chain_budget':1,'nonempty_faces':2**40-1,'constructed':False},
 'limits':['Independent Python finite definitions and source-formula reconstructions, not Rust or external rational backend execution.','No large closure was allocated; its count is the exact subset formula. No Serde payload was executed.']}
a.write('_probe10.json',out);print(json.dumps(out))
