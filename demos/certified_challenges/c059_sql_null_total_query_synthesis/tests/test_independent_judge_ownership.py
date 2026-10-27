"""The pure second judge works with every proposer import actively denied."""

import subprocess
import sys
from pathlib import Path


def test_second_judge_acceptance_and_rejection_without_proposer_imports():
    script = r'''
import importlib.abc
import sys

class NoProposer(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if "reference_solver" in fullname.split("."):
            raise AssertionError("proposer import attempted")

sys.meta_path.insert(0, NoProposer())
try:
    importlib.import_module("c059_sql_null_total_query_synthesis.reference_solver")
except AssertionError:
    pass
else:
    raise AssertionError("negative import control did not fire")
from c059_sql_null_total_query_synthesis.judge_packet.independent_checker import independent_check
case = {"case_id": "independent-owner", "schema": {"t": {"id": "INTEGER"}},
        "spec": {"op": "select", "from": "t"}, "protected": [],
        "test_databases": [{"t": [{"id": 1}]}]}
answer = {"case_id": case["case_id"], "status": "SOLVED", "sql": "SELECT id FROM t",
          "preflight_sql": "SELECT 1 WHERE 0", "null_ledger": []}
assert independent_check(case, answer)[0]
assert not independent_check(case, dict(answer, sql="SELECT 99 AS id"))[0]
assert not independent_check(case, dict(answer, sql="SELECT 1 AS other"))[0]
assert not independent_check(dict(case, test_databases=[]), answer)[0]
assert not any("reference_solver" in name.split(".") for name in sys.modules)
'''
    result = subprocess.run([sys.executable, "-B", "-c", script], capture_output=True, text=True, timeout=30,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stdout + result.stderr
