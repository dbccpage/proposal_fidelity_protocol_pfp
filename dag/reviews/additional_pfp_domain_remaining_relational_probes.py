"""Finite read-vetted relational controls; no external owners executed."""
import sys,types,ast,json,hashlib,itertools
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.normal_forms']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(short,remove_import=None):
 p=ROOT/('pfp/domain/normal_forms/'+short+'.py');tree=ast.parse(p.read_text(encoding='utf8'))
 if remove_import:
  removed=[n for n in tree.body if isinstance(n,ast.ImportFrom) and n.module==remove_import];assert len(removed)==1;tree.body=[n for n in tree.body if n not in removed]
 name='pfp.domain.normal_forms.'+short;m=types.ModuleType(name);m.__package__='pfp.domain.normal_forms';sys.modules[name]=m;exec(compile(tree,str(p),'exec'),m.__dict__)
 bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'execution':'unchanged body' if not remove_import else 'AST removed only '+remove_import+' import; parser-dependent function not invoked'});return m
r=load('relational');tower=load('tower_forms','pfp.domain.tower.parser');ext=load('relational_extensions');adv=load('relational_advanced')
def fd(x,y):return r.FunctionalDependency(frozenset(x),frozenset(y))
def control(i,rule,status,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
keys=[frozenset('AB'),frozenset('AC'),frozenset('BC')];projections=r.synthesize_5nf_projections('ABC',keys);relation=[dict(zip('ABC',bits)) for bits in itertools.product((0,1),repeat=3) if sum(bits)%2==0];jd=r.JoinDependency(frozenset('ABC'),projections);lossless,spurious_count,_=r.evaluate_join_dependency_on_relation(relation,jd);assert not lossless and spurious_count==4
assert all(len({tuple(row[a] for a in sorted(key)) for row in relation})==len(relation) for key in keys)
control(64,'5nf_projection_synthesis_requires_declared_join_dependency','counterexample_observed',declared_keys=[sorted(k) for k in keys],declared_join_dependencies=None,returned_projections=[sorted(k) for k in projections],original_rows=len(relation),spurious_join_rows=spurious_count,all_declared_keys_hold=True)
outside=r.chase_join_dependency('AB',[fd('Z','B')],['A','B']);assert outside.is_implied
one=r.check_lossless_decomposition(r.RelationalSchema(frozenset('AB'),frozenset()),[frozenset('A')]);assert one[0]
control(65,'relational_heading_and_decomposition_coverage','counterexample_observed',out_of_heading_determinant='Z',heading=['A','B'],accepted_chase=outside.is_implied,single_projection=['A'],accepted_lossless=one[0])
low=ext.chase_mvd('ABC',[fd('B','C')],[],components=['AB','BC'],max_iterations=1);high=ext.chase_mvd('ABC',[fd('B','C')],[],components=['AB','BC'],max_iterations=2);unknown=r.chase_join_dependency('ABC',[fd('B','C')],['AB','BC'],max_iterations=0);assert not low.is_implied and high.is_implied and unknown.is_implied is None
control(66,'mvd_chase_budget_is_not_nonimplication','counterexample_observed',same_lossless_decomposition=['AB','BC'],declared_fd='B -> C',budget_one_implied=low.is_implied,budget_two_implied=high.is_implied,fd_only_zero_budget_status=unknown.status)
s=r.RelationalSchema(frozenset('ABCD'),frozenset([fd('A','BCD'),fd('B','ACD')]));out=adv.temporal_6nf_decompose(s,temporal_key_attrs=['Time']);union=frozenset().union(*(x.attributes for x in out));assert union==frozenset('ACD')
control(67,'temporal_decomposition_attribute_preservation','counterexample_observed',original_heading=sorted(s.attributes),candidate_keys=[sorted(x) for x in s.candidate_keys()],output_headings=[sorted(x.attributes) for x in out],dropped_attributes=sorted(s.attributes-union),limit='Temporal key argument also unused; no actual intervals or application state mutated.')
atomic=[fd(x,y) for x in 'ABC' for y in 'ABC' if x!=y];subsets=[frozenset(c) for n in range(4) for c in itertools.combinations('ABC',n)];checked=0
for mask in range(1<<len(atomic)):
 deps=[d for i,d in enumerate(atomic) if mask&(1<<i)];schema=r.RelationalSchema(frozenset('ABC'),frozenset(deps));cover=r.compute_minimal_cover(deps)
 assert all(r.compute_attribute_closure(x,deps)==r.compute_attribute_closure(x,cover) for x in subsets)
 decomposition=adv.synthesize_3nf_bernstein(schema);assert frozenset().union(*decomposition)==schema.attributes
 assert r.check_lossless_decomposition(schema,decomposition)[0] and r.check_dependency_preservation(schema,decomposition)[0]
 for component in decomposition:
  projected=r.RelationalSchema(component,frozenset(adv.project_functional_dependencies(deps,component)));assert r.check_3nf(projected)[0]
 checked+=1
control(68,'minimal_cover_and_3nf_synthesis_finite_equivalence','bounded_positive_controls_observed',theories=checked,heading=['A','B','C'],fd_pool='six single-attribute nontrivial FDs',subsets_per_closure_comparison=8,limit='Cross-checks use reviewed closure/chase/projection owners and are not independent formal proof or all-arity enumeration.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_relational_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[c['id'] for c in controls]}))
