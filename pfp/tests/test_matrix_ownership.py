"""Shared PFP matrix owners load without Education or pytest import aliases."""

import subprocess
import sys
from pathlib import Path

import pytest
import tomllib
from setuptools import find_namespace_packages


def test_distribution_discovers_only_the_declared_pilot_runtime_subset(tmp_path):
    """Exercise setuptools with real directories, including forbidden evidence."""
    root = Path(__file__).resolve().parents[2]
    policy = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
        "tool"
    ]["setuptools"]["packages"]["find"]
    allowed = {
        "pfp.tests.demo_004.e_formal_math.checker",
        "adversary.tests.pilots.matrix",
        "adversary.tests.pilots.relational_spacetime",
        "adversary.tests.pilots.challenge_suite",
        "adversary.tests.pilots.pilot_0000192",
        "education.domain",
    }
    forbidden = {
        "pfp.tests.other_test_helpers",
        "adversary.tests.other_test_helpers",
        "adversary.tests.pilots.pilot_0000193",
        "adversary.tests.pilots.evidence.frozen_sources",
        "adversary.tests.pilots.relational_spacetime.tests",
        "education.pilots.matrix",
        "education.pfp",
        "education.pfp.infrastructure",
    }
    for name in allowed | forbidden:
        directory = tmp_path.joinpath(*name.split("."))
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    discovered = set(find_namespace_packages(
        where=str(tmp_path), include=policy["include"], exclude=policy["exclude"]
    ))
    assert allowed <= discovered
    assert not forbidden & discovered


@pytest.mark.parametrize("module", ["formal_matrix", "synthesis_matrix"])
def test_shared_matrix_owner_has_no_education_runtime_dependency(tmp_path, module):
    root = Path(__file__).resolve().parents[2]
    driver = """
import importlib
import importlib.abc
from pathlib import Path
import sys

root, name = sys.argv[1:]
sys.path.insert(0, root)

class MissingEducation(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'education', 'projects'}:
            raise ModuleNotFoundError('Education and legacy aliases unavailable: ' + fullname)

sys.meta_path.insert(0, MissingEducation())
module = importlib.import_module('pfp.infrastructure.' + name)
assert Path(module.__file__).resolve() == Path(root) / 'pfp/infrastructure' / (name + '.py')
if name == 'formal_matrix':
    assert module.participant_view({'case_id': 'private', 'expected': 7, 'data': 2}, 'public') == {'case_id': 'public', 'data': 2}
    result = module.call_openrouter('', 'vendor/model', [{'role': 'user', 'content': 'public task'}])
    assert not result['ok'] and result['error'] == 'PFP_ACCOUNTED_GATEWAY_REQUIRED'
else:
    assert module.prompt_view({'case_id': 'private', 'expected': 7, 'data': 2}, 'public') == {'case_id': 'public', 'data': 2}
    result = module.call_model('', 'vendor/model', 'public system', 'public task', max_tokens=256, title='ownership control')
    assert not result.ok and result.error == 'PFP_ACCOUNTED_GATEWAY_REQUIRED'
assert not any(key.split('.')[0] in {'education', 'projects'} for key in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-E", "-B", "-c", driver, str(root), module],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())


def test_c059_matrix_help_reaches_the_canonical_cli_without_a_provider(tmp_path):
    root = Path(__file__).resolve().parents[2]
    driver = """
import os
import runpy
import sys
sys.path.insert(0, sys.argv[1])
def readonly_help(event, args):
    if event == 'os.mkdir':
        raise RuntimeError('C059_HELP_MKDIR_FORBIDDEN')
    if event == 'open' and isinstance(args[2], int) and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
        raise RuntimeError('C059_HELP_FILE_WRITE_FORBIDDEN')
sys.addaudithook(readonly_help)
sys.argv = ['run_c059_matrix', '--help']
runpy.run_module('adversary.tests.pilots.c059_sql_null_total_query_synthesis.run_c059_matrix', run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-E", "-B", "-c", driver, str(root)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--max-provider-calls" in result.stdout
    assert "--max-estimated-cost-microusd" in result.stdout
    assert not list(tmp_path.iterdir())
