"""Bounded source-vetted local checks; no provider/native/kernel execution."""
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_008_support';B=R/'papers/pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks';O=H/'paper_008_support_inspection';T=O/'temporary';T.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
s=json.loads((H/(P+'_scope.json')).read_text());before={r['path']:sha((R/r['path']).read_bytes()) for r in s['files']};env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONUTF8='1',TEMP=str(T),TMP=str(T));out=[]
def run(label,args,cwd=B):
 cmd=[sys.executable,'-B','-X','utf8',*map(str,args)];r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60);x={'id':label,'command':cmd,'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr};out.append(x);print(json.dumps(x),flush=True)
for name in ['mssn_tower_retraction','deposit_gates','source_bound_examples']:
 run('current_'+name,['-m','pytest','code/tests/test_008_'+name+'.py','-c','pyproject.toml','--confcutdir=.', '-o','addopts=','-q','-ra','-p','no:cacheprovider','--basetemp',O/('pytest_'+name)])
run('current_custody',['verify_deposit.py']);run('named_census_generation_only',['tools/replay_lean_axiom_census.py','--check','.'])
spec=importlib.util.spec_from_file_location(P+'_runner',B/'code/retraction_benchmark_runner.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
n=m.GraphInstance('nan',['A'],[('A','A',float('nan'))],'CONTRADICTION','out of declared integer domain');q=m.GraphInstance('bool',['A','B'],[('A','B',True)],'CONSISTENT','out of exact integer type');bc=m.BudgetController(.1);bc.record_cost(float('nan'));bc.check_pre_call(100.)
checks={'nan_self_loop_witness_accepted':m.verify_inconsistency_witness(n,[(0,1)]),'boolean_edge_claim_potential_accepted':m.verify_potential(q,{'A':0,'B':1}),'nan_recorded_cost_allows_large_estimate':True,'flow_net_out_of_carrier_counterexample':{'nodes':0,'arcs':[[0,1]],'weight':[1],'load':[1],'flow':[1],'level':[],'price':1,'capacity':True,'balanced_vacuously':True,'zero_gap':True,'price_matches':True,'method':'Direct finite reconstruction of definitions with defaults, not Lean run.'},'reindex_category_identity_counterexample':{'f.name':'custom','compSub(id,f).name':'comp','identity_law_equal':False,'method':'Direct constructor reduction, not Lean run.'},'limit':'Callable API boundary probes outside six fixed integer graphs; run_benchmark receipt serialization rejects NaN, so no invalid stored receipt or actual overspend is claimed.'}
assert checks['nan_self_loop_witness_accepted'] and checks['boolean_edge_claim_potential_accepted'];out.append({'id':'admission_boundary_controls',**checks});print(json.dumps(checks))
assert before=={p:sha((R/p).read_bytes()) for p in before};(H/(P+'_probes.json')).write_text(json.dumps({'python':sys.version,'commands':out,'originals_unchanged':len(before),'provider_calls':0},indent=2)+'\n',encoding='utf-8')
