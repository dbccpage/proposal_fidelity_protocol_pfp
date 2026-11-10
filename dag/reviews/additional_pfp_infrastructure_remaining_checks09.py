"""Offline finite certificates, schema drift and FD counterexample; no production imports."""
import ast,dataclasses,hashlib,itertools,json,pathlib,sys
import jsonschema,yaml
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[];pins={}
def raw(i):
 f=fs[i];b=(R/f['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'];pins[f['path']]=f['sha256'];return b
def record(k,result,detail):
 assert result,detail;out.append({'id':'PFPINFRA-P'+k,'status':'reproduced','detail':detail})
t=ast.parse(raw(239));names={'GraphInstance','BENCHMARK_INSTANCES','exact_host_evaluate','_tree_parents','_root_path','inconsistency_witness','verify_inconsistency_witness','verify_potential','host_certificate'}
nodes=[x for x in t.body if getattr(x,'name',None)in names or isinstance(x,ast.AnnAssign)and isinstance(x.target,ast.Name)and x.target.id in names]
ns={'dataclass':dataclasses.dataclass,'__name__':'__main__'};exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[])),'read-owner-subset','exec'),ns)
checks=[]
for instance in ns['BENCHMARK_INSTANCES']:
 c=ns['host_certificate'](instance);ok=c['verdict']==instance.expected_verdict
 ok &= ns['verify_potential'](instance,c['potential'])if'potential'in c else ns['verify_inconsistency_witness'](instance,c['dual_witness_walk'])
 checks.append({'task':instance.task_id,'verdict':c['verdict'],'checked':bool(ok)})
record('043',all(x['checked']for x in checks),{'six_fixed_graph_certificates':checks,'scope':'Actual AST-extracted pure helpers; no benchmark runner/provider/native path.'})
p,c,v,receipt=[json.loads(raw(i))for i in(283,284,285,286)]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
d1=p['boundary_matrices']['d1'];d2=p['boundary_matrices']['d2'];z=p['active_obstruction']['cycle_z'];b=c['repair_boundary_column'];pre=c['claimed_integer_preimage_c'];ext=[row+[b[i]]for i,row in enumerate(d2)]
matvec=lambda m,x:[sum(a*q for a,q in zip(row,x))for row in m]
digestchecks=[c['problem_digest']==digest(p),v['problem_digest']==digest(p),receipt['problem_digest']==digest(p),receipt['candidate_digest']==digest(c),receipt['verifier_digest']==digest(v),receipt['receipt_digest']==digest(dict(receipt,receipt_digest=''))]
raw(168)
record('044',not any(digestchecks)and matvec(d1,z)==[0]*4 and matvec(d1,b)==[0]*4 and matvec(ext,pre)==z,{'digest_links':digestchecks,'recomputed':{'problem':digest(p),'candidate':digest(c),'verifier':digest(v),'receipt':digest(dict(receipt,receipt_digest=''))},'cycle_boundary':matvec(d1,z),'extension_preimage':matvec(ext,pre),'receipt_stays':'UNVERIFIED','scope':'Independent integer arithmetic and exact owner-documented sorted compact UTF8 SHA256 replay; all six embedded links mismatch current fixture objects. No assertion about historical original/archive loss; not SNF or fixed-carrier equivalence.'})
schema=yaml.safe_load(raw(365));mode=yaml.safe_load(raw(353));errs=list(jsonschema.Draft202012Validator(schema).iter_errors(mode))
record('045',any('quotient_descent_guards'in e.message for e in errs),{'mode13_schema_errors':[e.message for e in errs]})
attrs=frozenset('ABC');fd=[(frozenset('AB'),'C'),(frozenset('C'),'B')]
def closure(x,rules):
 x=set(x)
 while True:
  old=set(x)
  for lhs,rhs in rules:
   if lhs<=x:x.add(rhs)
  if old==x:return x
subs=[frozenset(c)for n in range(4)for c in itertools.combinations('ABC',n)]
projected=set()
for sub in subs:
 if sub==attrs:continue
 for lhs in subs:
  if lhs<=sub:
   for rhs in closure(lhs,fd)&sub-lhs:projected.add((lhs,rhs))
ac=closure('AB',projected);record('046','C'not in ac and closure('C',fd)!=set(attrs),{'schema':'ABC','dependencies':['AB->C','C->B'],'nontrivial_dependencies_across_all_proper_projections':sorted(''.join(sorted(x))+'->'+y for x,y in projected),'AB_closure_of_projected_union':sorted(ac),'proof':'Full ABC violates BCNF because C->B and C is not a superkey. Every all-proper decomposition loses AB->C even if every projected dependency is retained. Therefore arbitrary lossless dependency-preserving normalization through BCNF to6NF cannot be promised.'})
reg=yaml.safe_load(raw(322));ids={x['gate_id']for x in reg['primary_gates']};bad=[{'id':x['intergate_id'],'target':x['transition_to']}for x in reg['intergates']if x['transition_to']not in ids]
record('047',len(bad)==2,{'unresolved_primary_targets':bad,'scope':'Identity register only; does not assert current native source-profile evaluator fails.'})
(H/(P+'_checks09.json')).write_text(json.dumps({'python':sys.version,'method':'Standard library AST extraction of already-read pure helpers, independent integer/FD arithmetic and installed Draft202012Validator. No network/model/native/original writes.','source_pins':pins,'outcomes':out},indent=2)+'\n');print(json.dumps(out,indent=2))
