"""Independent bounded graph and declared-incidence controls."""
import sys,itertools,json,collections
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def topo(n,edges):
 deg=[0]*n;adj=[[] for _ in range(n)]
 for u,v in edges:deg[v]+=1;adj[u].append(v)
 todo=collections.deque(i for i in range(n) if not deg[i]);order=[]
 while todo:
  u=todo.popleft();order.append(u)
  for v in adj[u]:
   deg[v]-=1
   if not deg[v]:todo.append(v)
 return order if len(order)==n else None
def bfs(n,edges,start):
 dist=[None]*n;dist[start]=0;todo=collections.deque([start])
 while todo:
  u=todo.popleft()
  for x,v in edges:
   if x==u and dist[v] is None:dist[v]=dist[u]+1;todo.append(v)
 return dist
count=0;dag_count=0
for n in range(4):
 pairs=list(itertools.product(range(n),repeat=2))
 for bits in range(1<<len(pairs)):
  edges=[p for i,p in enumerate(pairs) if bits>>i&1];order=topo(n,edges)
  oracle=any(all(p.index(u)<p.index(v) for u,v in edges) for p in itertools.permutations(range(n)))
  assert (order is not None)==oracle;dag_count+=oracle;count+=1
  for start in range(n):
   expected=[None]*n;expected[start]=0;front={start}
   for k in range(1,n):
    front={v for u,v in edges if u in front}
    for v in front:
     if expected[v] is None:expected[v]=k
   assert bfs(n,edges,start)==expected
assert count==531
E=[(0,1),(0,1),(1,3),(0,2),(2,3)]
def paths(u,b):
 if u==b:return [()]
 return [(i,)+tail for i,(x,v) in enumerate(E) if x==u for tail in paths(v,b)]
assert paths(0,3)==[(0,2),(1,2),(3,4)]
families=0
universe=[tuple(c) for k in range(1,4) for c in itertools.combinations(range(3),k)]
for bits in range(1<<len(universe)):
 F={s for i,s in enumerate(universe) if bits>>i&1}
 if not all((v,) in F for v in range(3)):continue
 immediate=all(s[:i]+s[i+1:] in F for s in F if len(s)>1 for i in range(len(s)))
 allfaces=all(c in F for s in F for k in range(1,len(s)+1) for c in itertools.combinations(s,k))
 assert immediate==allfaces
 families+=immediate
assert families==9
d0=[[-1,1,0],[0,-1,1],[-1,0,1]];d1=[1,1,-1]
assert [sum(d1[i]*d0[i][j] for i in range(3)) for j in range(3)]==[0,0,0]
out={'rule':'bounded_graph_and_declared_incidence_controls','status':'531_graphs_and_declared_family_controls_confirmed','runtime':sys.version,
 'directed_graphs_with_loops':count,'acyclic_graphs':dag_count,'topological_and_distance_oracles_agree':True,
 'parallel_edge_paths':paths(0,3),'full_three_vertex_closed_families':families,'oriented_triangle_composition_zero':True,
 'nontransitive_DAG':{'edges':[[0,1],[1,2]],'acyclic':True,'missing_transitive_edge':[0,2]},
 'constant_witness_hash':{'different_edges':[[[0,1]],[[1,0]]],'source_hash_both':'00'*32},
 'limits':['Independent finite Python definitions only; no Rust, matrix backend, Serde or historical receipt execution.','Nontransitive DAG control distinguishes graph generators from a declared transitive relation; it does not deny the reachability partial order.']}
a.write('_probe12.json',out);print(json.dumps(out))
