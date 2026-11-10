"""Finite manifest-projection and Cech-equation controls; no original execution."""
import sys,json,copy,math
from fractions import Fraction
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def rank(rows):
 m=[[Fraction(x) for x in row] for row in rows];r=0
 for c in range(len(m[0]) if m else 0):
  p=next((i for i in range(r,len(m)) if m[i][c]),None)
  if p is None:continue
  m[r],m[p]=m[p],m[r];v=m[r][c];m[r]=[x/v for x in m[r]]
  for i in range(len(m)):
   if i!=r:
    v=m[i][c];m[i]=[x-v*y for x,y in zip(m[i],m[r])]
  r+=1
 return r
def mul(m,v):return [sum(x*y for x,y in zip(row,v)) for row in m]
d0=[[-1,1,0],[0,-1,1],[1,0,-1]];d1=[[0,0,0]]
rows=[]
for delta in ([1,-1,0],[1,1,1]):
 augmented=[r+[delta[i]] for i,r in enumerate(d0)];rows.append({'delta':delta,'closed':mul(d1,delta)==[0],'in_image':rank(augmented)==rank(d0)})
assert rows[0]['in_image'] and not rows[1]['in_image'] and all(x['closed'] for x in rows)
assert rank(d0)==2 and 3-rank(d1)==3
manifest={'manifest_version':2,'coefficient_domain':'Q','coefficient_representation':'BigRational','c0_dim':3,'c1_dim':3,'c2_dim':1,'d0_hash':'unchanged-d0','d1_hash':'unchanged-d1','weights_hash':'unchanged-weights','carrier_hash':'unchanged-carrier','witness_hash':'w','provenance_hash':'p','rank_d0':2,'dim_q1':1,'dim_h1':1}
boundkeys=['manifest_version','coefficient_domain','coefficient_representation','c0_dim','c1_dim','c2_dim','d0_hash','d1_hash','weights_hash']
projection=lambda m:[m[k] for k in boundkeys]
forged=copy.deepcopy(manifest);forged.update(rank_d0=999,dim_q1=999,dim_h1=1000,witness_hash='arbitrary-w',provenance_hash='arbitrary-p')
assert projection(forged)==projection(manifest) and forged['carrier_hash']==manifest['carrier_hash']
assert forged['rank_d0']>forged['c1_dim'] and forged['dim_h1']>forged['dim_q1']
out={'rule':'manifest_field_projection_and_finite_cech_distinctions','status':'counterexample_and_positive_controls_confirmed','runtime':sys.version,'manifest_projection':{'mutated_fields':['rank_d0','dim_q1','dim_h1','witness_hash','provenance_hash'],'all_guard_and_hash_arguments_unchanged':True,'rank_exceeds_ambient_dimension':True,'h1_exceeds_q1':True,'actual_hash_not_needed_or_executed':True},'cech':{'d0':d0,'d1':d1,'rank_d0':2,'ker_d1_dimension':3,'complex_law_holds':True,'sequence_not_exact_at_c1':True,'discrepancy_rows':rows,'empty_local_section_list_passes_local_status_guard':True,'faithful_comparison_is_caller_boolean':True},'floating_sparse_map':{'input_nan_with_unit_entry_produces_nan':math.isnan(1.0*float('nan')),'max_float_times_two_overflows_to_infinity':math.isinf(2.0*sys.float_info.max),'public_invalid_index_would_reach_unchecked_index_expression':True},'source_bindings':[a.ev('code/rust/core_homology/src/carrier_manifest.rs',276,344),a.ev('code/rust/core_homology/src/hashing.rs',113,140),a.ev('code/rust/core_homology/src/cech_gate.rs',124,210),a.ev('code/rust/core_homology/src/coboundary_matrix.rs',43,55)],'limits':['Guard/hash-argument projection and finite exact arithmetic, not Rust/Serde/BLAKE3 execution.','Cech arithmetic is conditional on declared sections and supplied complex; no presheaf extraction or actual local replay occurs in this control.']}
a.write('_probe04.json',out);print(json.dumps({k:v for k,v in out.items() if k!='source_bindings'}))
