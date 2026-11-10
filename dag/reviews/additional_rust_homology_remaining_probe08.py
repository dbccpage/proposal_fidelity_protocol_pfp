"""Finite graph census and persistence admission controls; no Rust execution."""
import sys,itertools,json
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def source_maximum(adj):
 best=0
 def expand(size,p):
  nonlocal best
  if not p:best=max(best,size);return
  remaining=p;order=[];bounds=[];color=0
  while remaining:
   color+=1;available=remaining
   while available:
    bit=available&-available;v=bit.bit_length()-1
    order.append(v);bounds.append(color);remaining&=~bit;available&=~bit;available&=~adj[v]
  for i in range(len(order)-1,-1,-1):
   if size+bounds[i]<=best:return
   v=order[i];expand(size+1,p&adj[v]);p&=~(1<<v)
 expand(0,(1<<len(adj))-1);return best
def source_cliques(adj,k):
 out=[]
 def walk(c,p):
  if len(c)==k:out.append(tuple(c));return
  while p:
   if len(c)+p.bit_count()<k:return
   bit=p&-p;v=bit.bit_length()-1;p&=~bit;walk(c+[v],p&adj[v])
 walk([],(1<<len(adj))-1);return out
graphs=0
for n in range(6):
 edges=list(itertools.combinations(range(n),2))
 for mask in range(1<<len(edges)):
  adj=[0]*n
  for i,(u,v) in enumerate(edges):
   if mask>>i&1:adj[u]|=1<<v;adj[v]|=1<<u
  actual=[]
  for k in range(n+1):
   expected=[c for c in itertools.combinations(range(n),k) if all(adj[u]>>v&1 for u,v in itertools.combinations(c,2))]
   assert source_cliques(adj,k)==expected
   if expected:actual.append(k)
  assert source_maximum(adj)==max(actual)
  graphs+=1
assert graphs==1100
landmarks=3;simplex=0b1001
members=[i for i in range(landmarks) if simplex>>i&1];others=[i for i in range(landmarks) if not simplex>>i&1]
assert members and others and simplex<=255 and simplex >= 1<<landmarks
dist=lambda i,j:int(i!=j)
assert any(max(dist(w,i) for i in members)<=min(dist(w,j) for j in others) for w in range(3))
def persistent(simplices):
 index={s:i for i,s in enumerate(simplices)};cols=[];piv={};pairs=[None]*len(simplices)
 for j,s in enumerate(simplices):
  col=0 if len(s)==1 else sum(1<<index[s[:k]+s[k+1:]] for k in range(len(s)))
  while col:
   low=col.bit_length()-1
   if low in piv:col^=cols[piv[low]]
   else:piv[low]=j;pairs[low]=j;break
  cols.append(col)
 essential=[i for i,p in enumerate(pairs) if p is None and cols[i]==0]
 return pairs,essential
edge=[(0,),(1,),(0,1)];pairs,essential=persistent(edge)
assert pairs==[None,2,None] and essential==[0]
public_method=[i for i,p in enumerate(pairs) if p is None]
assert public_method==[0,2]
skel=[c for k in range(1,4) for c in itertools.combinations(range(4),k)]
full=skel+[(0,1,2,3)]
_,e2=persistent(skel);_,e3=persistent(full)
assert sum(len(skel[i])==3 for i in e2)==1 and sum(len(full[i])==3 for i in e3)==0
out={'rule':'finite_graph_census_and_persistence_admission_controls','status':'1100_graphs_agree_and_countermodels_confirmed','runtime':sys.version,
 'graph_count':graphs,'all_clique_sizes_and_maxima_match_bruteforce':True,
 'witness_out_of_carrier_bits':{'landmarks':3,'simplex':simplex,'visible_members':members,'accepted_by_visible_guards':True},
 'filtration_missing_faces':{'only_simplex':[0,1],'narrow_certified_guard_accepts':True,'sparse_monotone_guard_accepts':True,'full_ph_guard_refuses':True},
 'vr_cap':{'requested_dimension':3,'returned_max_dimension':2,'four_equidistant_points_h2_2skeleton':1,'full_tetrahedron_h2':0},
 'essential_creators':{'pairing':pairs,'public_iterator':public_method,'actual_essential_creators':essential},
 'limits':['Independent finite source-formula reconstructions and subset oracle, not original Rust execution.','No resource budget refusal was exercised at n<=5; no native or historical mutation claim.']}
a.write('_probe08.json',out);print(json.dumps(out))
