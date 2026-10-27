"""Offline port-boundary regressions; these do not attest native solver capability."""

from __future__ import annotations

import importlib
import io
import json

import pytest
from projects.mssn_sn_symgam.challenges.b_cohomology.judge.certificate_checker import (
    check_cohomology_certificate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.runner import run_cases

from pfp.domain.ports import cohomology_port

MODULES = {
    "c011": "c011_solver",
    "c012": "c012_sheaf_solver",
    "c013": "c013_snf_solver",
    "c014": "c014_hodge_solver",
    "c015": "c015_persistence_solver",
    "c016": "c016_cup_product_solver",
    "c017": "c017_holonomy_solver",
    "c018": "c018_frustration_solver",
    "c019": "c019_h2_obstruction_solver",
    "c020": "c020_spectral_sequence_solver",
}


class RecordingPort:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def solve(self, case):
        self.calls.append(case)
        return self.result


@pytest.mark.parametrize("challenge,module_name", MODULES.items())
def test_legacy_solver_uses_shared_port_and_preserves_refusal(monkeypatch, challenge, module_name):
    result = {
        "status": "UNKNOWN",
        "refusal": "NATIVE_OPERATION_UNAVAILABLE",
        "native_outcome": {"detail": "preserved"},
    }
    port = RecordingPort(result)
    monkeypatch.setattr(cohomology_port, "_DEFAULT_SOLVER", port)
    module = importlib.import_module(
        f"projects.mssn_sn_symgam.challenges.b_cohomology.solvers.{module_name}"
    )
    supplied = {"payload": "case", "challenge": "ignored"}
    assert getattr(module, f"solve_{challenge}")(supplied) is result
    assert port.calls == [{"payload": "case", "challenge": challenge}]
    assert supplied["challenge"] == "ignored"


@pytest.mark.parametrize("challenge", list(MODULES)[1:])
def test_legacy_checker_rejects_uncertified_solved_result(challenge):
    result = check_cohomology_certificate({"challenge": challenge}, {"status": "SOLVED"})
    assert result["passed"] is False


def test_runner_does_not_bill_estimates_or_count_refusal_as_pass(monkeypatch, tmp_path):
    port = RecordingPort({"status": "UNKNOWN", "refusal": "NATIVE_OPERATION_UNAVAILABLE"})
    monkeypatch.setattr(cohomology_port, "_DEFAULT_SOLVER", port)
    path = tmp_path / "accounting.json"
    summary = run_cases([{"challenge": "c015"}], output_accounting=path)
    assert len(port.calls) == 1
    assert summary["passed_cases"] == 0
    assert summary["complete"] is False
    assert summary["billed_cost_usd"] is None
    assert summary["within_target_budget"] is None
    accounting = json.loads(path.read_text())
    assert accounting["measurement_status"] == "UNAVAILABLE"
    assert accounting["records"] == []


def test_runner_checks_returned_c011_certificate(monkeypatch):
    case = {
        "challenge": "c011",
        "nodes": ["u", "v"],
        "edges": [["u", "v"]],
        "claims": {"u->v": "3"},
        "weights": {"u->v": "1"},
    }
    witness = {
        "status": "SOLVED",
        "phi1": "0",
        "potential": {"u": "0", "v": "3"},
        "repair": {},
        "dual": {},
    }
    port = RecordingPort(witness)
    monkeypatch.setattr(cohomology_port, "_DEFAULT_SOLVER", port)
    assert run_cases([case])["complete"] is True
    port.result = {**witness, "potential": {"u": "0", "v": "2"}}
    assert run_cases([case])["complete"] is False


def test_empty_or_unavailable_run_is_incomplete(monkeypatch):
    assert run_cases([])["complete"] is False
    monkeypatch.setattr(cohomology_port, "_DEFAULT_SOLVER", None)
    summary = run_cases([{"challenge": "c011"}])
    assert summary["complete"] is False
    assert summary["results"][0]["res"]["status"] == "UNKNOWN"


def test_solve_cli_exits_nonzero_on_refusal(monkeypatch, capsys):
    module = importlib.import_module(
        "projects.mssn_sn_symgam.challenges.b_cohomology.solve"
    )
    port = RecordingPort({"status": "UNKNOWN", "refusal": "NATIVE_OPERATION_UNAVAILABLE"})
    monkeypatch.setattr(cohomology_port, "_DEFAULT_SOLVER", port)
    monkeypatch.setattr("sys.stdin", io.StringIO('{"challenge":"c020"}'))
    assert module.main() == 1
    assert json.loads(capsys.readouterr().out)["refusal"] == "NATIVE_OPERATION_UNAVAILABLE"


def test_runner_cli_exits_nonzero_for_missing_suite(monkeypatch, tmp_path):
    module = importlib.import_module(
        "projects.mssn_sn_symgam.challenges.b_cohomology.runner"
    )
    monkeypatch.setattr(module, "__file__", str(tmp_path / "runner.py"))
    assert module.main(["--suite", "hidden"]) == 1
    assert not (tmp_path / "accounting.json").exists()
