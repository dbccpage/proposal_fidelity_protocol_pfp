"""Read-vetted exact owners, isolated from unreviewed package initialization."""
import sys,types,importlib.util,json,hashlib,datetime
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_pfp_domain_remaining'
sources=[]
for name in ['pfp','pfp.domain','pfp.domain.exact','pfp.domain.shared_kernel']:
 module=types.ModuleType(name);module.__path__=[];sys.modules[name]=module
def load(name,path):
 p=ROOT/path;b=p.read_bytes();sources.append({'path':path,'sha256':hashlib.sha256(b).hexdigest()})
 spec=importlib.util.spec_from_file_location(name,p);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
load('pfp.domain.exceptions','pfp/domain/exceptions.py')
load('pfp.domain.exact.errors','pfp/domain/exact/errors.py')
q=load('pfp.domain.exact.q','pfp/domain/exact/q.py');Q=q.Q
poly=load('pfp.domain.exact.poly','pfp/domain/exact/poly.py')
alg=load('pfp.domain.exact.alg','pfp/domain/exact/alg.py')
wire=load('pfp.domain.exact.wire','pfp/domain/exact/wire.py')
exact=load('pfp.domain.shared_kernel.exact','pfp/domain/shared_kernel/exact.py')
p=poly.mul(poly.mul((Q(-1),Q(1)),(Q(-1),Q(1))),(Q(-2),Q(1)))
root_counts=[]
for lo,hi,expected in [(1,3,1),(0,1,1),(0,3,2)]:
 observed=poly.root_count(p,Q(lo),Q(hi));root_counts.append({'polynomial':'(x-1)^2*(x-2)','interval':[lo,hi],'expected_distinct_roots':expected,'observed':observed})
assert any(r['expected_distinct_roots']!=r['observed'] for r in root_counts)
mutable=[Q(-1),Q(1)];a=alg.Alg(mutable,Q(0),Q(3));one=alg.Alg((Q(-1),Q(1)),Q(0),Q(3));two=alg.Alg((Q(-2),Q(1)),Q(0),Q(3))
before=alg.alg_equal(a,one);mutable[0]=Q(-2);after_one=alg.alg_equal(a,one);after_two=alg.alg_equal(a,two);assert before and not after_one and after_two
aliases=[]
for text in [' 1 ','01','1/1','2/2','1/-2','+1','-0']:
 observed=wire.RationalWire.from_wire(text).to_wire()
 try:exact.parse_exact(text);strict='accepted'
 except exact.NotExactError:strict='refused'
 aliases.append({'input':text,'wire_normalized':observed,'strict_shared_parser':strict})
bad=wire.RationalDualityGap(Fraction(1),Fraction(0),Fraction(0),True)
zero=wire.RationalDualityGap.compute(Fraction(0),Fraction(0))
out={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':sys.version,'source_bindings':sources,'import_context':'Explicit source loading with inert namespace packages; original package initializers were not executed. Only read-vetted stdlib/declaration imports occur.','controls':[
 {'id':'PFPDOMAIN-C001','rule':'distinct_root_count_at_repeated_root_endpoints','status':'counterexample_observed','cases':root_counts},
 {'id':'PFPDOMAIN-C002','rule':'algebraic_value_invariant_under_external_mutation','status':'counterexample_observed','before_equals_one':before,'after_equals_one':after_one,'after_equals_two':after_two,'input':'list accepted as poly despite tuple annotation'},
 {'id':'PFPDOMAIN-C003','rule':'rational_wire_canonical_input_uniqueness','status':'counterexample_observed','cases':aliases},
 {'id':'PFPDOMAIN-C004','rule':'duality_gap_constructor_consistency_and_optimality_scope','status':'counterexample_observed','inconsistent_accepted':{'primal':str(bad.primal_objective),'dual':str(bad.dual_objective),'gap':str(bad.duality_gap),'is_optimal':bad.is_optimal},'zero_objectives_marked_optimal':zero.is_optimal,'limit':'No feasibility constraints, primal/dual witnesses or weak-duality relation are accepted by this API; scalar equality alone cannot establish an optimization certificate.'}
]}
PREFIX.with_name(PREFIX.name+'_exact_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
