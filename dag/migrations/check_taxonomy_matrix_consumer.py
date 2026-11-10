"""Targeted offline consumer check; no pytest collection or provider/native processes."""
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import types
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
blocked=[]
def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn','os.spawn'}:
        blocked.append(event)
        raise RuntimeError('Offline consumer verification forbids '+event)
sys.addaudithook(audit)
path=ROOT/'pfp/tests/types/test_taxonomy_task_families_yaml.py'
relative=path.relative_to(ROOT).as_posix()
archive=ROOT/'dag/migrations/taxonomy_matrix_consumer_original.zip'
with zipfile.ZipFile(archive) as z:original=z.read(relative)
assert hashlib.sha256(original).hexdigest()=='98a8d70b641c0f97cb9d265eb47dca5c6c4af2ba9a10ce40c3f0a389d074d014'
tree=ast.parse(path.read_text())
for name in ('_MATRIX','_BEDROCK'):
    assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
    assert len(assignments)==1
matrix_assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_MATRIX' for t in n.targets))
ns={'Path':Path,'__file__':str(path)}
exec(compile(ast.Module(body=[matrix_assignment],type_ignores=[]),'<matrix-path-only>','exec'),ns)
matrix=ns['_MATRIX'].resolve()
assert matrix==ROOT/'pilots/anomalon_woland/matrix/max_pilot_matrix.yaml' and matrix.is_file()
stream=io.StringIO()
suite=unittest.defaultTestLoader.discover(str(path.parent),pattern=path.name)
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
module=sys.modules[path.stem]
matrix_data=module.yaml.safe_load(matrix.read_text(encoding='utf-8'))
tokens=module._matrix_task_family_tokens(matrix_data)
catalog=module.yaml.safe_load(module._YAML.read_text(encoding='utf-8'))
ids=[item['id'] for item in catalog['categories']]
assert tokens and all(type(t) is str and t for t in tokens)
assert len(set(tokens))>=31 and {'linear_algebra','arithmetic_enumeration'}<=set(tokens)
missing_tokens=sorted(set(tokens)-set(ids))
baseline_output=io.StringIO()
baseline_module=types.ModuleType('original_taxonomy_matrix_consumer')
baseline_module.__file__=str(path)
exec(compile(original,'<archived-original-taxonomy-test>','exec'),baseline_module.__dict__)
baseline=unittest.TextTestRunner(stream=baseline_output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(baseline_module))
same_preexisting_failure=(len(result.failures)==len(baseline.failures)==1 and not result.errors and not baseline.errors
    and result.failures[0][0]._testMethodName==baseline.failures[0][0]._testMethodName
    and 'self.assertEqual(ids, sorted(set(ids)))' in result.failures[0][1]
    and result.failures[0][1].partition('AssertionError:')[2]==baseline.failures[0][1].partition('AssertionError:')[2]
    and ids!=sorted(set(ids)))
consumer_verified=result.wasSuccessful() or same_preexisting_failure
receipt={'status':'passed' if result.wasSuccessful() and not missing_tokens else 'path_verified_catalog_checks_fail',
 'source_repo':'pfp','path':relative,'original_sha256':hashlib.sha256(original).hexdigest(),
 'current_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'original_archive':archive.relative_to(ROOT).as_posix(),'archive_member':relative,
 'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
 'change':'Use one matrix path under pilots/anomalon_woland; remove overwritten legacy path and identical duplicate bedrock set.',
 'matrix_path':matrix.relative_to(ROOT).as_posix(),'matrix_sha256':hashlib.sha256(matrix.read_bytes()).hexdigest(),
 'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
 'test_output':stream.getvalue(),'blocked_effect_attempts':blocked,
 'matrix_coverage_check':{'passed':not missing_tokens,'distinct_matrix_tokens':len(set(tokens)),'catalog_ids':len(ids),'missing_tokens':missing_tokens},
 'baseline_test_output':baseline_output.getvalue(),'baseline_failures':len(baseline.failures),'baseline_errors':len(baseline.errors),
 'same_preexisting_catalog_order_failure':same_preexisting_failure,
 'limits':['Targeted unittest module only; pytest/conftest and broad suite were not run.',
           'Network and subprocess audit events were blocked; no model/provider/native host process invoked.',
           'This consumer adaptation preserves the archived original audit snapshot; the historical finding remains evidence about that snapshot.']}
(ROOT/'dag/migrations/taxonomy_matrix_consumer_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(stream.getvalue())
print(json.dumps({k:receipt[k] for k in ('status','tests_run','failures','errors','skipped','blocked_effect_attempts','current_sha256')}))
print(json.dumps(receipt['matrix_coverage_check']))
raise SystemExit(0 if consumer_verified else 1)
