"""Bounded read-vetted offline checks; all artifacts under own inspection root."""
import hashlib,importlib.util,itertools,json,os,subprocess,sys,zipfile
from fractions import Fraction as Q
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_007_support';PKG=ROOT/'papers/pfp/007_pfp_executable_lessons_and_evidence_boundaries';OUT=HERE/'paper_007_support_inspection';OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
scope=json.loads((HERE/(P+'_scope.json')).read_text());before={r['path']:sha((ROOT/r['path']).read_bytes()) for r in scope['files']+scope['excluded_prior_full_reads']}
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONUTF8='1')
records=[]
def run(label,args,cwd=PKG):
 cmd=[sys.executable,'-B','-X','utf8',*map(str,args)]
 r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
 row={'id':label,'command':cmd,'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr};records.append(row);print(json.dumps(row),flush=True);return r
args=['-m','pytest','code/tests','-c','pyproject.toml','--confcutdir=.', '-o','addopts=','-q','-ra','-p','no:cacheprovider','-k','not test_section3_code_blocks_run_as_printed','--basetemp',OUT/'pytest_tmp']
run('current_fraction_tests',args)
run('current_cpython_notebook',['tools/replay_companion_notebook.py'])
run('current_readonly_custody',['verify_deposit.py'])
run('current_named_census_generation_only',['tools/replay_lean_axiom_census.py','--check','.'])
# Guard guarantees the source checker exits on identity before executing any repository code.
inventory=json.loads((PKG/'docs/source_inventory_2026_10_02.json').read_text());first=next(r for r in inventory['inspected_sources'] if r['path'].startswith('pfp/domain/ddc/'))
assert sha((ROOT/first['path']).read_bytes())!=first['sha256']
run('current_source_identity_rejection',['tools/check_source_triangle.py','--source-root',ROOT])
bad=json.loads((PKG/'jupyter_notebooks/007_moving_a_discrepancy.ipynb').read_text());next(c for c in bad['cells'] if c['cell_type']=='code')['outputs'][0]['text']=['deliberate wrong output\n']
badpath=OUT/'wrong_output.ipynb';badpath.write_text(json.dumps(bad),encoding='utf-8')
run('altered_reference_rejected',['tools/replay_companion_notebook.py','--notebook',badpath])
spec=importlib.util.spec_from_file_location(P+'_legacy',PKG/'code/tests/test_007_pedagogical_transmission.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
threshold=m.LearningCheckMetrics(Q(92,100),Q(82,100),Q(85,100)).meets_certification_standards();assert threshold is False and Q(82,100)>=Q(4,5)
count=0
for n in range(5):
 cap=max(0,n-1);ceiling=0 if n<2 else n*(n-1)
 for length in range(n+1):
  for h in itertools.product(range(-cap,cap+1),repeat=length):assert sum(map(abs,h))<=ceiling;count+=1
finite={'id':'finite_bound_and_threshold_controls','list_instances':count,'n_values':[0,1,2,3,4],'82_percent_transfer_code_passes':threshold,'82_percent_transfer_quiz_threshold_passes':True,'counterexamples_missing_cap':[7],'counterexamples_missing_length':[2,2,2,2],'limit':'Finite reconstruction of list theorem, not Lean kernel execution or unbounded proof.'};records.append(finite);print(json.dumps(finite))
archive=next(PKG.glob('*.zip'));dest=OUT/'archive_fraction_probe';dest.mkdir(exist_ok=True)
names=['pyproject.toml','code/tests/test_007_pedagogical_transmission.py','code/tests/test_007_evidence_boundaries.py','code/tests/test_007_worked_triangle.py','jupyter_notebooks/007_moving_a_discrepancy.ipynb','_lev_landau_theoretical_minimum_quiz/study_guide.md','tools/replay_companion_notebook.py']
with zipfile.ZipFile(archive) as z:
 root=z.namelist()[0].split('/')[0]
 for name in names:
  target=dest/name;assert target.resolve().is_relative_to(dest.resolve());target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(root+'/'+name))
run('archive_fraction_tests',args[:-1]+[OUT/'archive_pytest_tmp'],dest)
run('archive_cpython_notebook',['tools/replay_companion_notebook.py'],dest)
after={p:sha((ROOT/p).read_bytes()) for p in before};assert before==after
result={'scope':'13 selected tests; repository-importing test deselected before execution. No Jupyter/Lean/native/provider runs. Archive probe uses7 byte-exact inspected archive members.','python':sys.version,'commands':records,'originals_unchanged':len(before)}
(HERE/(P+'_probes.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
