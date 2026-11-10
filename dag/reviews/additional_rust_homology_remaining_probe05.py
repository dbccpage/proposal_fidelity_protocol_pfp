"""Independent exact and floating predicate controls for residual witnesses."""
import sys,json,math
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
dot=lambda x,y:sum(u*v for u,v in zip(x,y))
def gap_only(h,y,phi,epsilon):return len(h)==len(y) and abs(dot(h,y)-phi)<=epsilon
false_optimum={'d0':[[1]],'omega':[1],'supplied_alpha':[0],'residual':[1],'dual':[1],'claimed_phi':1,'gap_only_accepts':gap_only([1],[1],1,0),'true_optimum':0,'better_alpha':[1],'dual_annihilation_residual':[1]}
assert false_optimum['gap_only_accepts'] and abs(1-1)==0
negative=gap_only([1],[-1],-1,0);infinite_epsilon=gap_only([1],[1],100,math.inf)
assert negative and infinite_epsilon
def numerical_visible_guards(y,stationarity,tolerance,bound):
 return bool(y) and all(math.isfinite(x) for x in y) and all(math.isfinite(x) for x in [stationarity,tolerance,bound]) and tolerance>=0 and bound>=0 and stationarity<=tolerance and max(abs(x) for x in y)<=bound
assert numerical_visible_guards([0.5],-100,1e-6,1)
assert not numerical_visible_guards([0.5],100,1e-6,1)
d0=d1=q=1
assert d1*d0==1 and d1*q==1
trichotomy={'d0':[[1]],'d1':[[1]],'residual':[1],'in_image':True,'closed':False,'source_branch':'ExactRepair','cochain_law':False}
out={'rule':'independent_residual_certificate_preconditions','status':'countermodels_and_positive_refusal_confirmed','runtime':sys.version,'gap_only_false_optimum':false_optimum,'gap_only_accepts_negative_phi':negative,'gap_only_accepts_infinite_tolerance':infinite_epsilon,'numerical_dual_negative_stationarity':{'vector':[0.5],'claimed_stationarity':-100,'tolerance':1e-6,'linf_bound':1,'visible_guards_accept':True,'opposite_positive_stationarity_refuses':True},'trichotomy':trichotomy,'source_bindings':[a.ev('code/rust/core_homology/src/primal_residual.rs',24,42),a.ev('code/rust/core_homology/src/numerical_dual_witness.rs',151,204),a.ev('code/rust/core_homology/src/trichotomy_witness.rs',52,83)],'limits':['Pure finite predicate reconstruction; no Rust or external functional-norm implementation executed.','The exact-dot helper correctly certifies its stated dot product only; this probe does not re-label that helper as an optimizer.']}
a.write('_probe05.json',out);print(json.dumps({k:v for k,v in out.items() if k!='source_bindings'}))
