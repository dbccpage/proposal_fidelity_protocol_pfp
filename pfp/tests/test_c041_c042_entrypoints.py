"""The two original formal tasks coexist without short-name import aliases."""

from pathlib import Path
import json
import subprocess
import sys

import pytest


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
OWNER = "omega_engine_pfp.tests.demo_004.e_formal_math"
TASKS = ("c041_lean4_finite_lemma_proofs", "c042_sat_with_drat_certificates")
GUARD = """
import importlib.abc
import socket
import sys

class CurrentOwnersOnly(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'reference_solver', 'judge_packet', 'governance', 'omega_engine_projects'}:
            raise ModuleNotFoundError('Ambiguous or retired owner: ' + fullname)

def no_network(*args, **kwargs):
    raise AssertionError('Offline load must not send a provider request')

sys.meta_path.insert(0, CurrentOwnersOnly())
socket.create_connection = no_network
socket.socket.connect = no_network
"""


@pytest.mark.parametrize("order", (TASKS, TASKS[::-1]), ids=("lean-first", "sat-first"))
def test_original_judges_coexist_in_either_import_order(tmp_path, order):
    driver = GUARD + """
import importlib
sys.path.insert(0, sys.argv[1])
for package in sys.argv[2:]:
    judge = importlib.import_module(package + '.judge_packet.checkers.dual_evaluator')
    assert judge.evaluate_dual.__module__ == package + '.judge_packet.checkers.dual_evaluator'
    if package.endswith('c041_lean4_finite_lemma_proofs'):
        assert judge.verify_exact.__module__.startswith(package + '.')
        assert judge.verify_independent.__module__.startswith(package + '.')
    else:
        assert judge.check_sat_submission.__module__.startswith(package + '.')
        assert judge.check_drat_submission.__module__.startswith(package + '.')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", driver, str(ROOT), *(OWNER + "." + t for t in order)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("cost,expected", ((None, "UNKNOWN (known subtotal $0.01000)"), (0, "$0.00000")))
def test_existing_report_preserves_unknown_vs_zero_cost(tmp_path, cost, expected):
    from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.synthesize_matrix_report import synthesize_report

    record = dict(model="vendor/model", method="M3_RETRACTION", passed_cases=1,
        total_cases=1, total_cost_usd=cost, total_cost_known_subtotal_usd=0.01 if cost is None else 0,
        cost_per_verified_success_usd=cost, total_prompt_tokens=2, total_completion_tokens=1)
    source = tmp_path / "M3_RETRACTION_vendor_model.json"
    source.write_text(json.dumps(record), encoding="utf-8")
    original = source.read_bytes()
    report = synthesize_report(tmp_path).read_text(encoding="utf-8")
    assert expected in report
    if cost is None:
        assert "$0.00000" not in report
    else:
        assert "UNKNOWN" not in report
    assert source.read_bytes() == original


@pytest.mark.parametrize("task,script", (
    (TASKS[0], "symbol_game_experiment.py"),
    (TASKS[0], "run_symbol_game_matrix.py"),
    (TASKS[1], "symbol_game_routing.py"),
))
def test_experiment_help_is_offline_and_exposes_explicit_bounds(tmp_path, task, script):
    path = ROOT / OWNER.replace(".", "/") / task / "reference_solver" / script
    driver = GUARD + """
import runpy
sys.argv = [sys.argv[1], '--help']
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", driver, str(path)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    for option in ("--model", "--method", "--max-provider-calls", "--max-estimated-cost-microusd"):
        assert option in result.stdout
    assert not list(tmp_path.iterdir())
