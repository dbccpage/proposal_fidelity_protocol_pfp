import datetime, hashlib, json, os, pathlib, subprocess, sys
root=pathlib.Path.cwd()
out=root/'omega_engine_workflows_agents_skills/receipts/oewas_002_20261010/planning_integration'
out.mkdir(parents=True,exist_ok=True)
attrs=root/'.gitattributes'
lines=attrs.read_text(encoding='utf-8').splitlines()
markers={'<<<<<<< HEAD','=======','>>>>>>> c4de2f6e4c76e7d6ef7495daae9360255bd7133e'}
assert sum(line in markers for line in lines)==3
attrs.write_bytes(('\n'.join(line for line in lines if line not in markers)+'\n').encode('utf-8'))
commands=[('manifest_rebuild',[sys.executable,'-X','utf8','-m','omega_engine_product_planning_office.use_cases.epic_manifest_audit','--repo-root','.','--write']),('planning_tests',[sys.executable,'-X','utf8','-m','pytest','-o','addopts=','-o','filterwarnings=','omega_engine_product_planning_office/tests/test_epic_manifest_audit.py','omega_engine_product_planning_office/tests/test_epic_tdd_plan_audit.py','omega_engine_product_planning_office/tests/test_prior_art_epic_audit.py','-q','--basetemp',str(pathlib.Path(os.environ['TEMP'])/'oewas002-planning-715')])]
runs=[]
for label,argv in commands:
    result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,cwd=root)
    log=out/(label+'.log')
    log.write_bytes(result.stdout)
    runs.append({'label':label,'argv':argv,'exit_code':result.returncode,'log':log.relative_to(root).as_posix(),'sha256':hashlib.sha256(result.stdout).hexdigest()})
    print(label,result.returncode,result.stdout.decode('utf-8',errors='replace')[-2500:],flush=True)
    if result.returncode: break
(out/'checks.json').write_bytes((json.dumps({'schema_version':'oewas.planning-integration-checks.v1','created_utc':datetime.datetime.now(datetime.UTC).isoformat(),'incoming_main':'c4de2f6e4c76e7d6ef7495daae9360255bd7133e','authority_effect':'None','runtime_activation':'HOLD','runs':runs},indent=2,sort_keys=True)+'\n').encode('utf-8'))
sys.exit(any(r['exit_code'] for r in runs))
