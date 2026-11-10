"""Bounded offline execution of audited pure companion tests only."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_004'
PKG=ROOT/'papers/pfp/004_pfp_native_verification_and_evidence_custody'
names=['arity_rewrite_engine','conversational_repair_dag','cut_completeness','hott_symbol_game','l1_sparse_landing','l1_sparsity_bullshit_benchmark','l1_symbol_game_governor','packet_firewall_host','scaling_benchmark_v20','weighted_cycle_supplement']
paths=['code/tests/test_'+n+'.py' for n in names]
env=dict(os.environ)
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
env.pop('CORE_FUNCTIONAL_GRAPH_BIN',None);env.pop('CORE_FUNCTIONAL_GRAPH_SHA256',None)
command=[sys.executable,'-B','-X','utf8','-m','pytest','-c',str(PKG/'pyproject.toml'),'--confcutdir',str(PKG),'-o','addopts=','-p','no:cacheprovider','-q',*paths,'--basetemp',str(HERE/(P+'_pytest_temp'))]
run=subprocess.run(command,cwd=PKG,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
out={'command':command,'cwd':PKG.as_posix(),'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'python':sys.version,'inputs':[{'path':(PKG/n).relative_to(ROOT).as_posix(),'sha256':hashlib.sha256((PKG/n).read_bytes()).hexdigest()} for n in paths],'limits':'Only ten fully read pure companion suites; excluded live Lean wrapper, attention imports/models, native-refusal adapter import and 100-case chordal suite. Native graph selection removed only in child environment. No archived Rust test or Lean build.','provider_calls':0,'native_builds':0}
(HERE/(P+'_test_results.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2))
