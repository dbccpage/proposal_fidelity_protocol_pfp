"""Independent finite models of fully read coordinate and certificate boundaries."""
import sys,json,struct
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def source_add(x,y):
 if x['degree']!=y['degree'] or len(x['coefficients'])!=len(y['coefficients']):return None
 return {'degree':x['degree'],'basis':x['basis'],'coefficients':[u+v for u,v in zip(x['coefficients'],y['coefficients'])]}
x={'degree':1,'basis':'e','coefficients':[1]};y={'degree':1,'basis':'2e','coefficients':[1]}
summed=source_add(x,y);assert summed['coefficients']==[2] and 1+2==3
typed_vectors=[x,{'degree':7,'basis':'foreign','coefficients':[1]}]
hash_inputs=[v['coefficients'] for v in typed_vectors];assert hash_inputs[0]==hash_inputs[1]
def multiplication(a,b):return [[sum(u*v for u,v in zip(row,col)) for col in zip(*b)] for row in a]
assert multiplication([[1]],[[0]])==[[0]]
assert multiplication([[1]],[[1]])==[[1]]
source_boundaries=[[[1]],[[1]]];maps=[[[1]],[[1]],[[1]]]
squares=[multiplication(source_boundaries[k-1],maps[k])==multiplication(maps[k-1],source_boundaries[k-1]) for k in range(1,3)]
assert all(squares) and multiplication(source_boundaries[0],source_boundaries[1])!=[[0]]
shape_inputs=[(1,2,[1,2]),(2,1,[1,2])]
encoded=[(0).to_bytes(struct.calcsize('P'),'little')+json.dumps(m,separators=(',',':')).encode() for _,_,m in shape_inputs];assert encoded[0]==encoded[1]
out={'rule':'independent_coordinate_and_certificate_binding_controls','status':'source_predicate_countermodels_confirmed','runtime':sys.version,'basis_addition':{'left':x,'right':y,'source_result':summed,'correct_result_in_e_basis':[3]},'typed_vector_hash':{'distinct_inputs':typed_vectors,'same_coefficients_forwarded_to_hash_vector':True,'cryptographic_hash_not_needed_or_executed':True},'boundary_omission':{'identity_matrix':[[1]],'vector':[1],'actual_boundary':[1],'source_some_branch_refuses':True,'source_none_branch_returns_witness':True},'mutable_complex':{'original_d1':[[1]],'original_d0':[[0]],'original_product':[[0]],'replacement_d0':[[1]],'new_product':[[1]],'public_matrix_replacement_does_not_update_cached_witness':True},'chain_map':{'source_and_target_boundaries':source_boundaries,'identity_maps':maps,'both_commuting_squares':squares,'boundary_squared':[[1]],'source_trait_supplies_no_chain_law_check':True},'chain_map_prehash':{'distinct_shapes':[list(x[:2]) for x in shape_inputs],'same_prehash_bytes':True,'native_usize_width_bytes':struct.calcsize('P')},'source_bindings':[a.ev('code/rust/core_homology/src/chain.rs',47,104),a.ev('code/rust/core_homology/src/cochain.rs',47,104),a.ev('code/rust/core_homology/src/cycle.rs',22,60),a.ev('code/rust/core_homology/src/cocycle.rs',22,60),a.ev('code/rust/core_homology/src/chain_map.rs',40,104),a.ev('code/rust/core_homology/src/cochain_complex.rs',49,67)],'limits':['Independent finite Python reconstruction of visible guards and matrix equations, not Rust execution or deserialization.','A caller that separately binds bases, correct carrier maps and refreshed witnesses can prevent these misuse paths; that premise is not enforced at these interfaces.']}
a.write('_probe02.json',out);print(json.dumps({k:v for k,v in out.items() if k!='source_bindings'}))
