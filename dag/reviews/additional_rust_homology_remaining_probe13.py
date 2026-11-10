"""Exact two-coordinate control for the primitive split evidence boundary."""
import sys,json
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
basis=2;blocks=[[0],[1]];images=[[],[]]
owner={v:i for i,block in enumerate(blocks) for v in block}
assert set(owner)==set(range(basis)) and len(owner)==sum(map(len,blocks))
assert all(owner[v]==i for i,image in enumerate(images) for v in image)
omega=[1,1];global_d0=[1,1]
global_residual=[x-y for x,y in zip(omega,global_d0)]
assert global_residual==[0,0] and sum(abs(x) for x in omega)==2
out={'rule':'primitive_split_global_image_binding','status':'missing_premise_countermodel_confirmed','runtime':sys.version,
 'basis':basis,'blocks':blocks,'supplied_image_supports':images,'visible_split_predicate_accepts':True,
 'actual_global_image_generator':global_d0,'omega':omega,'global_l1_optimum':0,'local_empty_image_l1_sum':2,
 'limits':['The global map is absent from DirectSumSplit inputs; this is an evidence-insufficiency countermodel, not a runtime claim that the function computed an optimum.','The PrimitiveStatus enum is not automatically minted by this witness. No Rust or optimizer execution.']}
a.write('_probe13.json',out);print(json.dumps(out))
