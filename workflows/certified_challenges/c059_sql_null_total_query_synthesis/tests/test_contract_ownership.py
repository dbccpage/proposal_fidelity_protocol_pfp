"""Shared carrier contracts can load with the proposer namespace unavailable."""

import subprocess
import sys
from pathlib import Path


def test_contract_loads_in_a_fresh_process_without_proposer_imports():
    script = r'''
import importlib.abc
import sys

class NoProposer(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if "reference_solver" in fullname.split("."):
            raise AssertionError("proposer import attempted")

sys.meta_path.insert(0, NoProposer())
try:
    importlib.import_module("c059_sql_null_total_query_synthesis.reference_solver.compiler")
except AssertionError as error:
    assert str(error) == "proposer import attempted"
else:
    raise AssertionError("negative import control did not fire")
from c059_sql_null_total_query_synthesis.relational_contract import (
    compare_bags, validate_schema_and_spec,
)
assert validate_schema_and_spec({"t": {"id": "INTEGER"}}, {"op": "select", "from": "t"})[0]
assert not validate_schema_and_spec({"t": {"id": "INTEGER"}}, {"op": "select", "from": "missing"})[0]
assert compare_bags([{"id": None}], [{"id": None}])[0]
assert not compare_bags([{"id": None}], [{"other": None}])[0]
assert not compare_bags([{"id": None}, {"id": None}], [{"id": None}])[0]
assert not any("reference_solver" in name.split(".") for name in sys.modules)
'''
    result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stdout + result.stderr
