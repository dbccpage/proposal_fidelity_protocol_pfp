"""Independent exact finite Alexander-Whitney and shell-boundary controls."""
import sys,itertools,json
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
bases={k:list(itertools.combinations(range(4),k+1)) for k in range(5)}
def vector(k,mask):return {s:(mask>>i)&1 for i,s in enumerate(bases[k])}
def d(f,k):return {s:sum(f[s[:i]+s[i+1:]] for i in range(len(s)))%2 for s in bases[k+1]}
def cup(f,p,g,q):return {s:f[s[:p+1]]*g[s[p:]] for s in bases[p+q]}
def add(f,g):return {s:f[s]^g[s] for s in f}
cases=0
for p,q in [(1,1),(2,0)]:
 for ma in range(1<<len(bases[p])):
  f=vector(p,ma)
  for mb in range(1<<len(bases[q])):
   g=vector(q,mb)
   assert d(cup(f,p,g,q),p+q)==add(cup(d(f,p),p+1,g,q),cup(f,p,d(g,q),q+1))
   cases+=1
assert cases==4352
cells=[(0,0),(1,1)]
assert len({i for i,k in cells})==len(cells) and cells[1][1]-cells[0][1]==1
assert 0 not in {1,2}
left={0,1};right={0,2};join={x|y for x in left for y in right}
assert len(join)==len(left)*len(right)==4
fake_family=[(0,1)];link=[tuple(x for x in s if x!=0) for s in fake_family if 0 in s]
assert link==[(1,)] and (1,) not in fake_family
out={'rule':'independent_aw_leibniz_and_shell_admission_controls','status':'4352_aw_cases_and_admission_limits_confirmed','runtime':sys.version,
 'aw_carrier':'standard tetrahedron, all F2 cochains in degree pairs (1,1) and (2,0)','aw_cases':cases,
 'morse_path_without_incidence':{'cells':cells,'actual_vertex':0,'actual_edge':[1,2],'shape_guard_accepts':True,'incidence_holds':False},
 'link_missing_closure':{'input':fake_family,'output_link':link,'returned_face_absent_from_input':True},
 'join_with_empty_face_count':len(join),'limits':['Independent finite Python definitions only; no Rust, F2 backend or original test execution.','The link control isolates an unchecked caller premise; it does not dispute the bijection for an actual closed complex.']}
a.write('_probe11.json',out);print(json.dumps(out))
