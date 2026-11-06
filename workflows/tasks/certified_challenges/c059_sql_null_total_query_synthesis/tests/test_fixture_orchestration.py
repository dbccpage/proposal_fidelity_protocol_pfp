"""Fixture generation is orchestration, with no writes or solving on import."""

import subprocess
import sys
from pathlib import Path

import pytest

MODULES = ("generate_cases", "generate_mutations")


def test_explicit_assembly_preserves_inventories_without_writing(monkeypatch):
    from pathlib import Path

    from c059_sql_null_total_query_synthesis import (
        generate_cases,
        generate_mutations,
    )

    def no_writes(*args, **kwargs):
        raise AssertionError("fixture assembly attempted a filesystem write")

    monkeypatch.setattr(Path, "mkdir", no_writes)
    cases = generate_cases.build_cases()
    mutations = generate_mutations.build_mutations()
    assert len(cases) == 64
    assert len(mutations) == 48
    package = Path(generate_cases.__file__).resolve().parent
    assert generate_cases.cases_dir == package / "judge_packet" / "cases"
    assert generate_mutations.cases_dir == generate_cases.cases_dir
    assert generate_mutations.mutations_dir == package / "judge_packet" / "hostile_mutations"


@pytest.mark.parametrize("module", MODULES)
def test_generator_import_does_not_create_paths_or_solve_cases(module):
    script = r'''
import importlib
import sys
from pathlib import Path

prefix = "c059_sql_null_total_query_synthesis"
proposer = importlib.import_module(prefix + ".reference_solver")
def no_solving(*args, **kwargs):
    raise AssertionError("generator solved a case at import time")
def no_writes(*args, **kwargs):
    raise AssertionError("generator created paths at import time")
proposer.solve = no_solving
Path.mkdir = no_writes
importlib.import_module(prefix + "." + sys.argv[1])
'''
    result = subprocess.run([sys.executable, "-B", "-c", script, module], capture_output=True, text=True, timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stdout + result.stderr
