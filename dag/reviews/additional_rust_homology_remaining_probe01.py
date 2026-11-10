"""Independent finite arithmetic and graph controls; no Rust or native execution."""
import sys,json,math
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def components(n,edges):
 seen=set();count=0
 for v in range(n):
  if v in seen:continue
  count+=1;stack=[v];seen.add(v)
  while stack:
   u=stack.pop()
   for x,y in edges:
    for w in ([y] if x==u else [])+([x] if y==u else []):
     if w not in seen:seen.add(w);stack.append(w)
 return count
def signed_le(n):
 size=1
 while not -(1<<(size*8-1))<=n<(1<<(size*8-1)):size+=1
 return n.to_bytes(size,'little',signed=True)
def frame(n):
 b=signed_le(n);return len(b).to_bytes(8,'little')+b
rows=[]
for n,edges,declared in [(2,[(0,1)],2),(3,[(0,1),(1,2),(2,0)],1)]:
 actual=components(n,edges);accepted=0<declared<=n and len(edges)+declared>=n
 rows.append({'vertices':n,'edges':edges,'declared_components':declared,'source_predicate_accepts':accepted,'source_formula_betti_one':len(edges)+declared-n,'independently_computed_components':actual,'true_graph_betti_one':len(edges)+actual-n})
assert rows[0]['source_predicate_accepts'] and rows[0]['source_formula_betti_one']==1 and rows[0]['true_graph_betti_one']==0
assert rows[1]['source_formula_betti_one']==rows[1]['true_graph_betti_one']==1
raw1=signed_le(1)+signed_le(515);raw2=signed_le(769)+signed_le(2)
assert raw1==raw2==bytes.fromhex('010302') and frame(1)+frame(515)!=frame(769)+frame(2)
out={'rule':'independent_finite_graph_and_encoding_controls','status':'counterexample_and_positive_controls_confirmed','runtime':sys.version,'graph_rows':rows,'rational_framing':{'raw_equal_hex':raw1.hex(),'length_framed_different':True,'hash_computation_or_collision_resistance_not_tested':True},'factorial_bounds':{'factorial20':math.factorial(20),'fits_u64':math.factorial(20)<2**64,'factorial21_exceeds_u64':math.factorial(21)>=2**64},'source_bindings':[a.ev('code/rust/core_homology/src/lib.rs',216,256),a.ev('code/rust/core_homology/src/scalar.rs',104,125),a.ev('code/rust/core_homology/src/e_infinity_operad.rs',64,75)],'limits':['Independent Python reconstruction of the fully read finite predicates and standard graph invariant; not Rust execution.','Encoding control concerns raw framing, not authentication or injectivity of a fixed-width hash.']}
a.write('_probe01.json',out);print(json.dumps(out))
