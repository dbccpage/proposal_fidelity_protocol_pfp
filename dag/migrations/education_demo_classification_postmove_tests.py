"""Run only the requested pure-Python education tests after relocation.

No notebook, media renderer, provider, native host, generator or repository
conftest is loaded. This file is a prepared command, not an execution receipt.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import sysconfig

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--suite',choices=['simulations','local-game','operad'],required=True)
args=parser.parse_args()
report=json.loads((HERE/'education_demo_classification.json').read_text(encoding='utf-8'))
rows={r['proposed_destination']:r for r in report['files'] if r['disposition']=='move'}
if args.suite=='simulations':
    modules=['pilots/education/eis_simulation/code/eis_core.py','pilots/education/pciv_simulation/code/prompt_civilization_core.py']
    tests=['pilots/education/eis_simulation/code/tests/test_eis_levels.py','pilots/education/pciv_simulation/code/tests/test_prompt_civilization_levels.py']
elif args.suite=='local-game':
    modules=['pilots/education/symbol_game/educational_governor.py']
    tests=['pilots/education/symbol_game/test_how_to_play_scenarios.py','pilots/education/symbol_game/test_educational_governor_boundaries.py']
else:
    modules=['pilots/education/operad_simulation/code/was_operad_core.py']
    tests=['pilots/education/operad_simulation/code/tests/test_was_operad_levels.py']
for rel in modules+tests:
    path=ROOT/rel
    if not path.is_file():raise SystemExit('NOT_MOVED: '+rel)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=rows[rel]['sha256']:
        raise SystemExit('SOURCE_DRIFT_REVIEW_REQUIRED: '+rel)
for rel in modules:sys.path.insert(0,str((ROOT/rel).parent))
# Repository code/ and the companion code/ packages must not shadow stdlib code.
spec=importlib.util.spec_from_file_location('code',Path(sysconfig.get_path('stdlib'))/'code.py')
module=importlib.util.module_from_spec(spec)
sys.modules['code']=module
spec.loader.exec_module(module)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
os.environ.pop('PYTEST_ADDOPTS',None)
import pytest
raise SystemExit(pytest.main(['-c',os.devnull,'--noconftest','--import-mode=importlib','-p','no:cacheprovider','-q',*[str(ROOT/t) for t in tests]]))
