import datetime, hashlib, json, os, pathlib, subprocess, sys
root = pathlib.Path.cwd()
out = root / 'workflows_agents_skills/receipts/oewas_002_20261010/main_integration/root'
out.mkdir(parents=True, exist_ok=True)
base = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-o', 'addopts=', '-o', 'filterwarnings=']
groups = [
 ('wire_cli_laws', ['workflows_agents_skills/tests/unit/test_typed_workflow_wire.py', 'workflows_agents_skills/tests/unit/test_typed_workflow_cli.py', 'workflows_agents_skills/tests/unit/test_planar_slot_laws.py']),
 ('native_manifest', ['workflows_agents_skills/tests/integration/test_typed_workflow_native.py', 'product_planning_office/tests/test_epic_manifest_audit.py']),
 ('upstream_compiler', ['workflows_agents_skills/tests/unit/test_typed_contract_compiler.py']),
]
runs=[]
for label, files in groups:
    command = base + files + ['-q', '--basetemp', str(pathlib.Path(os.environ['TEMP']) / ('oewas002-merged-'+label))]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=root)
    path = out/(label+'.log')
    path.write_bytes(result.stdout)
    runs.append({'label':label, 'argv':command, 'exit_code':result.returncode, 'log':path.relative_to(root).as_posix(), 'log_sha256':hashlib.sha256(result.stdout).hexdigest(), 'tests':[{'path':p, 'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in files]})
    print(label, result.returncode, result.stdout.decode('utf-8', errors='replace')[-1500:], flush=True)
command=[sys.executable, '-X', 'utf8', '-m', 'workflows_agents_skills.infrastructure.typed_contract_compiler', '--repo-root', '.', '--check']
result=subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=root)
path=out/'portable_projection_check.log'
path.write_bytes(result.stdout)
runs.append({'label':'portable_projection_check', 'argv':command, 'exit_code':result.returncode, 'log':path.relative_to(root).as_posix(), 'log_sha256':hashlib.sha256(result.stdout).hexdigest()})
print('portable_projection_check', result.returncode, result.stdout.decode('utf-8',errors='replace')[-1500:], flush=True)
record={'schema_version':'oewas.main-integration-root-checks.v1','created_utc':datetime.datetime.now(datetime.UTC).isoformat(), 'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'main':subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip(),'authority_effect':'None','runs':runs,'environment':{'PYTEST_DISABLE_PLUGIN_AUTOLOAD':os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD'),'CORE_SYMBOL_GAME_HOST':os.environ.get('CORE_SYMBOL_GAME_HOST')},'python':sys.version}
(out/'checks.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
sys.exit(any(r['exit_code'] for r in runs))
