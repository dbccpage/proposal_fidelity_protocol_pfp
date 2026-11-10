"""Bounded vetted offline probes; preserve all frozen original bytes."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_009_support';B=R/'papers/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates';O=H/'paper_009_support_inspection';T=O/'temporary';T.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
s=json.loads((H/(P+'_scope.json')).read_text());before={r['path']:sha((R/r['path']).read_bytes()) for r in s['files']+s['excluded_prior_full_reads']};env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONUTF8='1',TEMP=str(T),TMP=str(T));results=[]
for name,args in [
 ('current_pytest',['-m','pytest','code/tests','-c','pyproject.toml','--confcutdir=.','-o','addopts=','-q','-ra','-p','no:cacheprovider','--basetemp',str(O/'pytest')]),
 ('current_capstone',['tools/review_capstone.py']),
 ('current_notebook_cpython',['tools/replay_notebook.py','--engine','cpython']),
 ('current_default_verifier',['verify_deposit.py']),
 ('named_census_generation_only',['tools/replay_lean_axiom_census.py','--check','.'])]:
 cmd=[sys.executable,'-B','-X','utf8',*args];r=subprocess.run(cmd,cwd=B,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90);v={'id':name,'command':cmd,'cwd':str(B),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr};results.append(v);print(json.dumps({'id':name,'exit_code':r.returncode,'stdout_tail':r.stdout[-1800:],'stderr_tail':r.stderr[-1200:]}),flush=True)
assert before=={p:sha((R/p).read_bytes()) for p in before}
(H/(P+'_probes.json')).write_text(json.dumps({'python':sys.version,'commands':results,'originals_unchanged':len(before),'provider_calls':0,'lean_builds':0},indent=2)+'\n',encoding='utf-8')
