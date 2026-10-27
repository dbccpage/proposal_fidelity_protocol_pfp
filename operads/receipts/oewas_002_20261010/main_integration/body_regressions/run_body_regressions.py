"""One authorized three-file regression replay; no production edits or bypasses."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path('C:/Users/a343o/.codex/worktrees/oewas-typed-contracts/the_symbol_game')
OUT = ROOT / 'workflows_agents_skills/receipts/oewas_002_20261010/main_integration/body_regressions'
EXPECTED_MAIN = 'e5dc7774a305a078150a5f06e63c0e2a3e0272e6'
TESTS = [
    'workflows_agents_skills/tests/unit/test_candidate_instruction_body_binding.py',
    'workflows_agents_skills/tests/unit/test_adversary_candidate_plan.py',
    'workflows_agents_skills/tests/unit/test_typed_contract_audit.py',
]
PRODUCTION = [
    'workflows_agents_skills/application/adversary_candidate_plan.py',
    'workflows_agents_skills/application/typed_workflow_compiler.py',
    'workflows_agents_skills/application/typed_contract_audit.py',
    'workflows_agents_skills/application/adversary_instruction_admission.py',
    'workflows_agents_skills/application/adversary_task_selection.py',
    'workflows_agents_skills/application/commands/compile_catalog.py',
    'workflows_agents_skills/application/anti_skill/anti_skill_v2.py',
    'workflows_agents_skills/application/dtos/success_dtos.py',
    'workflows_agents_skills/contracts/typed_capabilities_v1.py',
    'workflows_agents_skills/contracts/typed_workflow_v1.py',
    'workflows_agents_skills/domain/entities/typed_workflow.py',
    'workflows_agents_skills/domain/entities/typed_contract_package.py',
    'workflows_agents_skills/domain/entities/operation_v3.py',
    'workflows_agents_skills/domain/entities/skill_document_v3.py',
    'workflows_agents_skills/domain/value_objects/operands.py',
    'workflows_agents_skills/domain/value_objects/lifecycle_facets.py',
    'workflows_agents_skills/domain/value_objects/content_digest.py',
    'workflows_agents_skills/domain/anti_skills/anti_skill_v2.py',
    'workflows_agents_skills/domain/anti_skills/json_wire.py',
    'workflows_agents_skills/domain/capability_catalog_v1.py',
    'workflows_agents_skills/infrastructure/typed_contract_compiler.py',
    'workflows_agents_skills/infrastructure/fs/adversary_operand_source.py',
    'workflows_agents_skills/infrastructure/parser/markdown_parser_adapter.py',
    'operations/domain/rop/result.py',
    'conftest.py', 'pyproject.toml',
]
PLANS = [
    'product_planning_office/plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md',
    'product_planning_office/plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md',
]
SOURCE_FILES = sorted(TESTS + PRODUCTION + PLANS + [
    p.relative_to(ROOT).as_posix()
    for p in (ROOT / 'workflows_agents_skills/catalog/contracts/v1').rglob('*')
    if p.is_file() and p.suffix in {'.json', '.md'}
], key=lambda value: value.encode('utf-8'))

def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}

def inventory() -> list[dict]:
    return [pin(ROOT / path) for path in SOURCE_FILES]

ENVIRONMENT_SET = {
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
    'PYTHONDONTWRITEBYTECODE': '1',
    'CORE_CREDENTIAL_DISCOVERY': 'off',
}
env = os.environ.copy()
env.update(ENVIRONMENT_SET)
commands = []

def execute(name: str, argv: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    reply = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
    finished = dt.datetime.now(dt.timezone.utc).isoformat()
    (OUT / f'{name}.stdout.log').write_bytes(reply.stdout)
    (OUT / f'{name}.stderr.log').write_bytes(reply.stderr)
    commands.append({'name': name, 'argv': argv, 'cwd': str(ROOT),
                     'environment_set': ENVIRONMENT_SET, 'started_utc': started,
                     'finished_utc': finished, 'exit_code': reply.returncode,
                     'stdout': f'{name}.stdout.log', 'stderr': f'{name}.stderr.log'})
    return reply

before = inventory()
head = execute('git_head_before', ['git', 'rev-parse', 'HEAD'])
branch = execute('git_branch', ['git', 'branch', '--show-current'])
ancestry = execute('main_ancestry', ['git', 'merge-base', '--is-ancestor', EXPECTED_MAIN, 'HEAD'])
if head.returncode or branch.returncode or ancestry.returncode:
    raise SystemExit('Git read/merged-main prerequisite failed; raw logs retained')
uv = ['C:/Users/a343o/.local/bin/uv.exe', 'run', '--offline', '--no-project',
      '--python', 'C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe',
      '--with', 'pytest==9.1.1', '--with', 'pyyaml==6.0.3', '--with', 'numpy',
      '--with', 'pydantic==2.13.5', '--with', 'scipy', '--with', 'networkx',
      '--with', 'sympy', '--with', 'blake3', 'python', '-X', 'utf8']
version_code = ('import importlib.metadata as m,json,platform,sys;'
                'print(json.dumps({"python":sys.version,"executable":sys.executable,'
                '"platform":platform.platform(),"packages":{n:m.version(n) for n in '
                '["pytest","pyyaml","pydantic","blake3","numpy","scipy","networkx","sympy"]}},sort_keys=True))')
versions = execute('versions', uv + ['-c', version_code])
uv_version = execute('uv_version', [uv[0], '--version'])
git_version = execute('git_version', ['git', '--version'])
if versions.returncode or uv_version.returncode or git_version.returncode:
    raise SystemExit('Version prerequisite failed; raw logs retained')
basetemp = Path(tempfile.gettempdir()) / ('oewas002-body-regressions-' + uuid.uuid4().hex)
if basetemp.exists() or ROOT in basetemp.parents:
    raise SystemExit('External unique basetemp precondition failed')
pytest = execute('pytest', uv + ['-m', 'pytest', '-o', 'addopts=', '-o', 'filterwarnings=',
                               '--basetemp', str(basetemp), *TESTS, '-q'])
after = inventory()
head_after = execute('git_head_after', ['git', 'rev-parse', 'HEAD'])
record = {
    'schema_version': 'oewas.main-integration.body-regressions.v1',
    'authority_effect': 'None', 'scope': 'existing three-file regression replay after merged main; no new RED or mutation claim',
    'expected_merged_main': EXPECTED_MAIN,
    'head_before': head.stdout.decode('utf-8').strip(),
    'head_after': head_after.stdout.decode('utf-8').strip(),
    'branch': branch.stdout.decode('utf-8').strip(),
    'main_is_ancestor': ancestry.returncode == 0,
    'versions': json.loads(versions.stdout), 'commands': commands,
    'selected_source_pins_before': before, 'selected_source_pins_after': after,
    'selected_source_pins_unchanged': before == after,
    'head_unchanged': head.stdout == head_after.stdout and head_after.returncode == 0,
    'pytest_exit_code': pytest.returncode,
    'external_unique_basetemp': str(basetemp),
    'production_edits_by_this_runner': False, 'production_mutations_by_this_runner': False,
    'git_mutations': False, 'provider_calls': False, 'native_builds': False,
    'coverage_ceiling': 'Only named finite Python regression files and selected source pins; no full suite, host attestation, execution authority or epic completion.',
    'ic_plan_references': [
        {'path': PLANS[0], 'line': 15, 'claim': 'OEOS composition and checkout lease bind _intelligence/_oeos; path-only rename invalidates ownership/recovery'},
        {'path': PLANS[0], 'line': 21, 'claim': '007/OEOS owns inventoried, lease-aware copy/verify/cutover/recovery;009 owns producer integration'},
        {'path': PLANS[1], 'line': 15, 'claim': 'Adversary runtime and bout service use legacy intelligence storage;007 owns cutover'},
        {'path': PLANS[1], 'line': 33, 'claim': '009 requires actual writer/reader pairs after007 cutover'},
    ],
}
record['artifacts'] = [pin(path) for path in sorted(OUT.iterdir(), key=lambda p: p.name.encode('utf-8')) if path.is_file()]
(OUT / 'receipt.json').write_bytes((json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode('ascii'))
print(pytest.stdout.decode('utf-8', errors='replace'), end='')
if pytest.stderr:
    print(pytest.stderr.decode('utf-8', errors='replace'), end='', file=sys.stderr)
print(json.dumps({'receipt': str(OUT/'receipt.json'), 'receipt_sha256': hashlib.sha256((OUT/'receipt.json').read_bytes()).hexdigest(),
                  'source_pin_count': len(before), 'pins_unchanged': before == after,
                  'head': record['head_before'], 'head_unchanged': record['head_unchanged'],
                  'pytest_exit_code': pytest.returncode}, sort_keys=True))
if pytest.returncode or before != after or not record['head_unchanged']:
    raise SystemExit(1)
