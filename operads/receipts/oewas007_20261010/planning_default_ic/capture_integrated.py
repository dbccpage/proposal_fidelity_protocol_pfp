"""Capture final named integration commands with exact bytes and source pins."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic'
label=sys.argv[1];assert not (OUT/(label+'.json')).exists()
uv='C:/Users/a343o/.local/bin/uv.exe';python='C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe'
prefix=[uv,'run','--offline','--no-project','--python',python,'--with','pytest==9.1.1','--with','pyyaml==6.0.3','--with','pydantic==2.13.5','python','-X','utf8']
ppo='product_planning_office/'
nav=json.loads((OUT/'command_navigation.json').read_bytes())
docs=sorted({r['path'] for r in nav['changes']}|{ppo+'plans/decisions/adr_20261010_oewas_intelligence_migration.md',ppo+'plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md',ppo+'plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md',ppo+'plans/epics/oewas/README.md','workflows_agents_skills/documentation/intelligence_migration_v1.md'})
code=[ppo+'domain/contracts/historical_sources.py',ppo+'infrastructure/prior_art_sources.py',ppo+'use_cases/prior_art_epic_audit.py',ppo+'use_cases/epic_tdd_plan_audit.py',ppo+'use_cases/epic_manifest_audit.py',ppo+'tests/test_prior_art_historical_sources.py',ppo+'tests/test_prior_art_epic_audit.py',ppo+'tests/test_epic_tdd_plan_audit.py',ppo+'tests/test_epic_manifest_audit.py']
manifest=ppo+'plans/epics/epic_manifest.json'
paths=docs+code+[manifest]+[p.relative_to(ROOT).as_posix() for p in (ROOT/ppo/'receipts').glob('*successor.json')]+[ppo+'plans/epics/epic_relevance_5_prior_art.yaml','operating_system/adapters/intelligence_custody/ic_routing.py','operating_system/adapters/intelligence_custody/ic_migration.py','governance/domain/intelligence_community.py','governance/_types/ic_casefold_v15_1.json','_ic/odni/migrations/oewas007/receipt.json','_ic/odni/migrations/oewas007/inventory.json']
paths+= [p.relative_to(ROOT).as_posix() for p in (ROOT/ppo/'plans/epics').rglob('epic_*.md')]
def pins():return {rel:{'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),'size_bytes':(ROOT/rel).stat().st_size} for rel in sorted(set(paths))}
if label=='integrated_manifest':argv=prefix+['-m','product_planning_office.use_cases.epic_manifest_audit','--write']
elif label in {'integrated_planning','integrated_historical'}:
 tests=([ppo+'tests/test_epic_tdd_plan_audit.py',ppo+'tests/test_prior_art_epic_audit.py',ppo+'tests/test_epic_manifest_audit.py'] if label=='integrated_planning' else [ppo+'tests/test_prior_art_historical_sources.py'])
 argv=prefix+['-m','pytest','-o','addopts=','-o','filterwarnings=',*tests,'--basetemp',str(Path(os.environ['TEMP'])/(label+'-'+uuid.uuid4().hex)),'-q']
elif label=='integrated_cli':argv=prefix+['-m','product_planning_office.infrastructure.prior_art_sources']
elif label=='integrated_versions':argv=prefix+['-c',"import sys,pytest,yaml,pydantic;print(sys.version);print('pytest='+pytest.__version__);print('pyyaml='+yaml.__version__);print('pydantic='+pydantic.__version__)"]
elif label=='integrated_ruff':argv=[uv,'run','--offline','--no-project','--python',python,'--with','ruff','ruff','check','--select','F,I',*code[:4],code[5],code[6]]
elif label=='integrated_markdownlint':argv=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','C:/Users/a343o/AppData/Roaming/npm/markdownlint.ps1','--config','.markdownlint.json',*docs]
else:raise ValueError(label)
before=pins();env=os.environ.copy();overrides={'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PYTHONDONTWRITEBYTECODE':'1'};env.update(overrides);start=time.monotonic();result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=180,check=False);after=pins()
for name,raw in [('stdout',result.stdout),('stderr',result.stderr)]:(OUT/(label+'.'+name+'.log')).write_bytes(raw)
changed=[p for p in before if before[p]!=after[p]]
record={'authority_effect':'None','work_base_revision':'4d207641277ef3d3af16e11aafb411ada1ee10ed','integrated_main_revision':'d47c98402a42fd189acd7cf6ccd23d7a0d09c120','cwd':str(ROOT),'command_argv':argv,'environment_overrides':overrides,'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'source_pins_before':before,'source_pins_after':after,'changed_inputs':changed,'allowed_changed_inputs':[manifest] if label=='integrated_manifest' else [],'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
(OUT/(label+'.json')).write_bytes((json.dumps(record,indent=2,sort_keys=True)+'\n').encode());print(result.stdout.decode('utf8',errors='replace'),end='');print(result.stderr.decode('utf8',errors='replace'),end='',file=sys.stderr);assert not set(changed)-set(record['allowed_changed_inputs']),'Source drift requires replay';sys.exit(result.returncode)