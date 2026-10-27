"""Current task scripts reach PFP from outside the checkout without legacy aliases."""

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
PILOTS = ROOT / "pfp/tests/demo_004"
MATRICES = sorted(
    path
    for strand in ("e_formal_math", "f_program_synthesis")
    for path in (PILOTS / strand).glob("c*/run_c*_matrix.py")
    if path.parent.name[:4] in {f"c{i:03}" for i in (*range(43, 51), 56, 57, 58)}
)


@pytest.mark.parametrize("script", MATRICES, ids=lambda p: p.parent.name[:4])
def test_direct_help_loads_original_judges_without_legacy_aliases(tmp_path, script):
    driver = """
import importlib.abc
import runpy
import socket
import sys

class NoLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'projects':
            raise ModuleNotFoundError('Retired owner: ' + fullname)

def no_network(*args, **kwargs):
    raise AssertionError('CLI help must not open a network connection')

sys.meta_path.insert(0, NoLegacy())
socket.create_connection = no_network
socket.socket.connect = no_network
sys.argv = [sys.argv[1], '--help']
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", driver, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--max-provider-calls" in result.stdout
    assert "--max-estimated-cost-microusd" in result.stdout
    assert "--model" in result.stdout
    assert not list(tmp_path.iterdir())


def test_all_selected_matrix_commands_are_covered():
    assert {p.parent.name[:4] for p in MATRICES} == {
        f"c{i:03}" for i in (*range(43, 51), 56, 57, 58)
    }
