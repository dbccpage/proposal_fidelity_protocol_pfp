"""Independent tiny rational certificates, finite relations and text-heuristic controls."""
import sys,types,importlib.util,json,hashlib,itertools
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[]
for name in ['pfp','pfp.domain','pfp.domain.dual_witness','pfp.domain.tower_lift','pfp.domain.biochem']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(name,path):
 p=ROOT/path;bindings.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
dual=load('pfp.domain.dual_witness.models','pfp/domain/dual_witness/models.py')
tower=load('pfp.domain.tower_lift.models','pfp/domain/tower_lift/models.py')
load('pfp.domain.biochem.errors','pfp/domain/biochem/errors.py')
proof=load('pfp.domain.biochem.proofreading','pfp/domain/biochem/proofreading.py')
good=dual.ExactDualWitnessCertificate((F(0),F(2)),((F(1),),(F(1),)),(F(1),F(1)),(F(1),),(F(-1),F(1)),(F(-1),F(1)),F(2),F(0))
bad=dual.ExactDualWitnessCertificate(good.omega,good.d0_matrix,good.weights,good.alpha,good.primal_residual,(F(1),F(1)),F(2),F(0))
zero_weight=dual.ExactDualWitnessCertificate((F(7),),((),),(F(0),),(),(F(7),),(F(0),),F(0),F(0))
assert good.is_valid_dual_certificate() and not bad.is_valid_dual_certificate() and zero_weight.is_valid_dual_certificate()
finite=[]
for size in [1,2]:
 carrier=tower.CarrierSet(size-1,size,tuple(range(size)));pairs=list(itertools.product(carrier.elements,repeat=2));counts=[0,0,0]
 for mask in range(1<<len(pairs)):
  r=tower.BinaryRelation(frozenset(p for i,p in enumerate(pairs) if mask&(1<<i)))
  vals=[r.is_irreflexive(carrier) and r.has_witnessed_pair(carrier),r.has_directed_path_2(carrier),r.has_directed_cycle_3(carrier)]
  counts=[a+int(b) for a,b in zip(counts,vals)]
 finite.append({'carrier_size':size,'relations_tested':1<<len(pairs),'counts':dict(zip(['irreflexive_witnessed','distinct_path2','distinct_cycle3'],counts))})
assert finite[0]['counts']['irreflexive_witnessed']==0 and finite[1]['counts']['distinct_path2']==finite[1]['counts']['distinct_cycle3']==0
pr=proof.HopfieldNinioProofreader();text='gauge invariance and topological protection'
refused=pr.proofread('x',text);admitted=pr.proofread('x',text+' 1=2');negative=pr.proofread('x',text,deformation_factor=F(-1));reset=pr.proofread('x','1=2',initial_phi1=F(-1))
assert refused.status=='DISSOCIATED_DURING_DELAY' and admitted.status=='CATALYTIC_ADMISSION' and negative.delta_phi1==-1 and reset.initial_phi1==0
out={'runtime':sys.version,'source_bindings':bindings,'controls':[
 {'id':'PFPDOMAIN-C027','rule':'exact_weighted_l1_primal_dual_equations','status':'bounded_positive_and_negative_controls_observed','valid_optimum2_accepted':good.is_valid_dual_certificate(),'wrong_annihilator_refused':not bad.is_valid_dual_certificate(),'zero_weight_nonzero_residual_accepted':zero_weight.is_valid_dual_certificate(),'limit':'Zero-weight example correctly solves a seminorm objective; zero optimum alone does not imply zero residual. No source/carrier semantics or external solver certified.'},
 {'id':'PFPDOMAIN-C028','rule':'finite_distinct_vertex_relation_lower_bounds','status':'bounded_exhaustion_observed','cases':finite,'limit':'All2 and16 relations checked only on explicit canonical1/2-element carriers. This verifies predicate-level lower bounds, not stored digest preimages, target witnesses or any ontological stage necessity.'},
 {'id':'PFPDOMAIN-C029','rule':'proofreading_admission_vs_actual_proof','status':'counterexample_observed','without_equation_status':refused.status,'with_false_equation_status':admitted.status,'false_equation':'1=2','executed_mathematical_validator':False},
 {'id':'PFPDOMAIN-C030','rule':'proofreading_negative_input_consistency','status':'counterexample_observed','deformation_factor':'-1','observed_delta':str(negative.delta_phi1),'reason_claims_positive':'> 0' in negative.reason,'negative_initial_input':'-1','reported_initial_after_admission':str(reset.initial_phi1)}
]}
(ROOT/'dag/reviews/additional_pfp_domain_remaining_certificate_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
