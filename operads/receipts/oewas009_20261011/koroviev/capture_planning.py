"""Capture small planning batches without rewriting earlier evidence."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
label=sys.argv[1];assert not (OUT/(label+'.json')).exists(),'Never overwrite an evidence label'
uv='C:/Users/a343o/.local/bin/uv.exe';python='C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe'
prefix=[uv,'run','--offline','--no-project','--python',python,'--with','pytest==9.1.1','--with','pyyaml==6.0.3','--with','pydantic==2.13.5','python','-X','utf8']
ppo='omega_engine_product_planning_office/';epic=ppo+'plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oewoland_plan.md';readme=ppo+'plans/epics/oewas/README.md';manifest=ppo+'plans/epics/epic_manifest.json'
files=[p.relative_to(ROOT).as_posix() for p in (ROOT/ppo/'plans/epics').rglob('epic_*.md')]
files += [readme,manifest,ppo+'plans/epics/epic_relevance_5_prior_art.yaml',ppo+'use_cases/epic_tdd_plan_audit.py',ppo+'use_cases/prior_art_epic_audit.py',ppo+'use_cases/epic_manifest_audit.py',ppo+'infrastructure/prior_art_sources.py',ppo+'domain/contracts/historical_sources.py',ppo+'tests/test_epic_tdd_plan_audit.py',ppo+'tests/test_prior_art_epic_audit.py',ppo+'tests/test_epic_manifest_audit.py','_ic/odni/migrations/oewas007/receipt.json','_ic/odni/migrations/oewas007/inventory.json']
files += [p.relative_to(ROOT).as_posix() for p in (ROOT/ppo/'receipts').glob('*successor.json')]
def pins():return {rel:{'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),'size_bytes':(ROOT/rel).stat().st_size} for rel in sorted(set(files))}
if label=='planning_red':
 argv=prefix+['-m','pytest','-o','addopts=','-o','filterwarnings=',ppo+'tests/test_epic_tdd_plan_audit.py::test_shipped_walk_covers_every_reviewed_epic',ppo+'tests/test_prior_art_epic_audit.py::test_current_map_resolves_all_declared_systems',ppo+'tests/test_epic_manifest_audit.py::test_the_shipped_manifest_audits_clean','--basetemp',str(Path(os.environ['TEMP'])/('oewas009-'+label+'-'+uuid.uuid4().hex)),'-q']
elif label=='planning_green':
 argv=prefix+['-m','pytest','-o','addopts=','-o','filterwarnings=',ppo+'tests/test_epic_tdd_plan_audit.py',ppo+'tests/test_prior_art_epic_audit.py',ppo+'tests/test_epic_manifest_audit.py','--basetemp',str(Path(os.environ['TEMP'])/('oewas009-'+label+'-'+uuid.uuid4().hex)),'-q']
elif label=='manifest_write':argv=prefix+['-m','omega_engine_product_planning_office.use_cases.epic_manifest_audit','--write']
elif label=='prior_art_cli':argv=prefix+['-m','omega_engine_product_planning_office.infrastructure.prior_art_sources']
elif label=='versions':argv=prefix+['-c',"import sys,pytest,yaml,pydantic;print(sys.version);print('pytest='+pytest.__version__);print('pyyaml='+yaml.__version__);print('pydantic='+pydantic.__version__)"]
elif label=='markdownlint':argv=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','C:/Users/a343o/AppData/Roaming/npm/markdownlint.ps1','--config','.markdownlint.json',epic,readme,*(p.relative_to(ROOT).as_posix() for p in sorted(OUT.glob('*.md')))]
else:raise ValueError(label)
before=pins();env=os.environ.copy();overrides={'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONDONTWRITEBYTECODE':'1'};env.update(overrides);start=time.monotonic();result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=180,check=False);after=pins()
for stream,raw in [('stdout',result.stdout),('stderr',result.stderr)]:(OUT/(label+'.'+stream+'.log')).write_bytes(raw)
changed=[rel for rel in before if before[rel]!=after[rel]];allowed=[manifest] if label=='manifest_write' else []
record={'schema':'oewas009.koroviev.command.v1','authority_effect':'None','base_revision':'c1964010689b0d396ec6392325bd2fe0b26d97d4','cwd':str(ROOT),'command_argv':argv,'environment_overrides':overrides,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'source_pins_before':before,'source_pins_after':after,'changed_inputs':changed,'allowed_changed_inputs':allowed,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
(OUT/(label+'.json')).write_bytes((json.dumps(record,indent=2,sort_keys=True)+'\n').encode());print(result.stdout.decode('utf8',errors='replace'),end='');print(result.stderr.decode('utf8',errors='replace'),end='',file=sys.stderr);assert not set(changed)-set(allowed),'Source drift requires replay';sys.exit(result.returncode)