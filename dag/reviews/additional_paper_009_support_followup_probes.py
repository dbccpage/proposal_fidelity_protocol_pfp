"""Dependency-free bounded replay and exact archive controls; never edit originals."""
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_009_support';B=R/'papers/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates';O=H/'paper_009_support_inspection';T=O/'temporary';T.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
s=json.loads((H/(P+'_scope.json')).read_text());before={r['path']:sha((R/r['path']).read_bytes()) for r in s['files']+s['excluded_prior_full_reads']};env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONUTF8='1',TEMP=str(T),TMP=str(T));env.pop('PYTHONOPTIMIZE',None);results=[]
def run(label,args,cwd):
 cmd=[sys.executable,'-B','-X','utf8',*args];v=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60);r={'id':label,'command':cmd,'cwd':str(cwd),'exit_code':v.returncode,'stdout':v.stdout,'stderr':v.stderr};results.append(r);print(json.dumps({'id':label,'exit_code':v.returncode,'tail':(v.stdout+v.stderr)[-1600:]}),flush=True)
tests=['code/tests/test_'+n+'.py' for n in ['009_adversarial_reality_gate','recorded_bout_counts','review_counts','triangle_cycle_sum']]
def pytest(label,cwd):run(label,['-m','pytest',*tests,'-c','pyproject.toml','--confcutdir=.','-o','addopts=','-q','-ra','-p','no:cacheprovider','--basetemp',str(O/label)],cwd)
pytest('current_non_notebook_tests',B)
c=json.loads((H/(P+'_custody.json')).read_text());dest=O/'archive_probe';dest.mkdir(exist_ok=True);chosen=[]
with zipfile.ZipFile(R/c['archive_path']) as z:
 for x in c['zip_members']:
  rel=x['current_path'].split('/009_pfp_adversarial_dialectics_and_terminal_reality_gates/',1)[1]
  if rel in [*tests,'code/tests/__init__.py','code/review_counts.py','code/triangle_cycle_sum.py','tools/review_capstone.py','tools/replay_notebook.py','jupyter_notebooks/009_triangle_cycle_sum.ipynb','pyproject.toml'] or rel.startswith('docs/historical_evidence/'):
   p=dest/PurePosixPath(*PurePosixPath(x['member']).parts[1:]);assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(x['member']));chosen.append({'member':x['member'],'sha256':sha(p.read_bytes())})
pytest('archive_non_notebook_tests',dest);run('archive_capstone',['tools/review_capstone.py'],dest)
tree=ast.parse((B/'tools/replay_notebook.py').read_text());worker=next(x.value.value for x in ast.walk(tree) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='worker' for t in x.targets));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='compare_code_outputs');ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'reviewed_compare','exec'),ns);compare=ns['compare_code_outputs']
def normalize(obj):
 for cell in obj['cells']:
  if isinstance(cell.get('source'),list):cell['source']=''.join(cell['source'])
  for out in cell.get('outputs',[]):
   if isinstance(out.get('text'),list):out['text']=''.join(out['text'])
 return obj
def notebook(label,cwd,wrong=False):
 p=cwd/'jupyter_notebooks/009_triangle_cycle_sum.ipynb';expected=normalize(json.loads(p.read_text()));actual=copy.deepcopy(expected)
 for cell in actual['cells']:
  if cell['cell_type']=='code':cell['outputs']=[];cell['execution_count']=None
 v=subprocess.run([sys.executable,'-B','-X','utf8','-c',worker],input=json.dumps(actual),cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60);assert v.returncode==0
 if wrong:next(cell for cell in expected['cells'] if cell.get('outputs'))['outputs'][0]['text']='WRONG\n'
 errors=compare(expected,json.loads(v.stdout));r={'id':label,'notebook_sha256':sha(p.read_bytes()),'dependency_sha256':sha((cwd/'code/triangle_cycle_sum.py').read_bytes()),'worker_utf8_sha256':sha(worker.encode()),'code_cells':5,'errors':errors,'method':'Exact fully reviewed embedded CPython worker and comparator extracted by AST. stdlib JSON normalizes source/stream lists; no nbformat validation or Jupyter/IPython check. Wrong expected output changed only in memory.'};results.append(r);print(json.dumps(r));return errors
assert not notebook('current_five_cells_via_stdlib',B)
assert not notebook('archive_five_cells_via_stdlib',dest)
assert notebook('wrong_stored_output_control',B,True)==['cell 4: outputs differ']
spec=importlib.util.spec_from_file_location(P+'_renderer',B/'tools/render_paper.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);calls=[]
def blocked(*a,**k):calls.append(a);raise AssertionError('Native process must not be invoked')
original_run=m.subprocess.run;m.subprocess.run=blocked
try:
 try:m.render('not_invoked_pandoc','not_invoked_xelatex')
 except StopIteration:results.append({'id':'renderer_header_admission','exception':'StopIteration','native_calls':len(calls),'cause':'Current paper author is Jeremy H. Carroll; renderer searches only lines beginning Bare Metal Anchor. Failure occurs before any subprocess or artifact write.'})
 else:raise AssertionError('Expected author extraction failure')
finally:m.subprocess.run=original_run
assert not calls and before=={p:sha((R/p).read_bytes()) for p in before}
(H/(P+'_followup_probes.json')).write_text(json.dumps({'python':sys.version,'commands':results,'archive_extracted':chosen,'originals_unchanged':len(before),'provider_calls':0,'native_calls':0,'limit':'Initial package replay/tests blocked by missing nbformat; these explicitly bounded fallback checks do not claim the package notebook command succeeded.'},indent=2)+'\n',encoding='utf-8')
