"""
test_c005_bakeoff.py — Verification suite for Challenge C005 (Hosted Decoding Controls Bake-off).

Tests:
1. JSON Schema and GBNF definitions (schemas.py)
2. Decoding control configurations and logit bias builders (controls.py)
3. 10 Control-honored probes and probe_before_trust.v1 enforcement (probes.py)
4. Poisoned case false witness detection (poisoned_cases.py)
5. Exact mathematical certificate and repair checkers (checkers.py)
6. Budget controller ceiling and fail-closed invariants (budget_controller.py)
7. End-to-end solver execution and refusal envelope contracts (solve.py)
8. Arm runner, Wilson intervals, and exact McNemar testing (runner.py)
9. No-verdict labels and run-folder custody for the bake-off, the two benchmark scripts and
   run_150_tests_suite.py (every write goes to pytest's tmp_path; no provider is called)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges import run_150_tests_suite as suite150
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls import (
    benchmark_3arm_scratchpad,
    benchmark_arm4_hybrid,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c005_hosted_decode_controls import (
    run_woland_bakeoff as bakeoff,
)

from .budget_controller import BudgetController, BudgetExceededError
from .checkers import verify_consistency_certificate, verify_cycle_repair
from .client import GovernedClient
from .controls import ControlKind, build_logit_bias_map, get_control_config
from .poisoned_cases import POISONED_CASES
from .probes import CONTROL_HONORED_PROBES, evaluate_probe_response
from .runner import compare_arms_mcnemar, run_c005_arm, wilson_score_interval
from .schemas import (
    validate_json_schema,
)
from .solve import solve_c005_case


def test_schemas_validation():
    # Valid consistency
    valid_cons = {"verdict": "CONSISTENT", "certificate": {"a": "0", "b": "5"}}
    ok, err = validate_json_schema(valid_cons, "consistency_verdict")
    assert ok is True
    assert err is None

    # Invalid consistency (missing certificate)
    invalid_cons = {"verdict": "CONSISTENT"}
    ok, err = validate_json_schema(invalid_cons, "consistency_verdict")
    assert ok is False

    # Valid cycle repair
    valid_repair = {"status": "SOLVED", "repaired": ["1", "-2", "1"], "weighted_l1": "2"}
    ok, err = validate_json_schema(valid_repair, "cycle_repair_solution")
    assert ok is True
    assert err is None

    # Invalid cycle repair (repaired numbers not strings)
    invalid_repair = {"status": "SOLVED", "repaired": [1, -2, 1], "weighted_l1": "2"}
    ok, err = validate_json_schema(invalid_repair, "cycle_repair_solution")
    assert ok is False


def test_logit_bias_builder():
    token_mapping = {"Sure": 101, "0": 201, "1": 202, "-": 203, "Other": 999}
    bias = build_logit_bias_map(custom_token_mapping=token_mapping)
    assert bias[101] == -100  # Prose starter suppressed
    assert bias[201] == 5  # Digit boosted
    assert bias[202] == 5
    assert bias[203] == 5
    assert 999 not in bias


def test_control_configs():
    none_cfg = get_control_config(ControlKind.NONE)
    assert none_cfg.kind == ControlKind.NONE
    assert none_cfg.parameters == {}

    bias_cfg = get_control_config(ControlKind.LOGIT_BIAS)
    assert bias_cfg.kind == ControlKind.LOGIT_BIAS

    schema_cfg = get_control_config(ControlKind.JSON_SCHEMA, task_family="consistency")
    assert "response_format" in schema_cfg.parameters

    gbnf_cfg = get_control_config(ControlKind.GBNF, task_family="consistency")
    assert "grammar" in gbnf_cfg.parameters


def test_probes_pass_and_fail():
    probe_schema = CONTROL_HONORED_PROBES[0]  # Expects schema

    # Passing schema output
    pass_out = json.dumps({"verdict": "CONSISTENT", "certificate": {"x": "1"}})
    res_pass = evaluate_probe_response(probe_schema, pass_out, ControlKind.JSON_SCHEMA)
    assert res_pass.respected is True

    # Failing schema output (conversational text)
    fail_out = "Hello! How can I assist you today?"
    res_fail = evaluate_probe_response(probe_schema, fail_out, ControlKind.JSON_SCHEMA)
    assert res_fail.respected is False

    # Logit bias probe avoiding suppressed word
    probe_bias = CONTROL_HONORED_PROBES[4]
    res_bias_pass = evaluate_probe_response(
        probe_bias, "Certainly, here it is.", ControlKind.LOGIT_BIAS
    )
    assert res_bias_pass.respected is True
    res_bias_fail = evaluate_probe_response(
        probe_bias, "Sure, I can do that.", ControlKind.LOGIT_BIAS
    )
    assert res_bias_fail.respected is False


def test_exact_checkers():
    # Consistency valid
    edges = [("A", "B", 3), ("B", "C", 2), ("C", "A", -5)]
    res = verify_consistency_certificate(edges, "CONSISTENT", {"A": "0", "B": "3", "C": "5"})
    assert res.is_valid is True

    # Consistency invalid edge
    res_bad = verify_consistency_certificate(edges, "CONSISTENT", {"A": "0", "B": "3", "C": "4"})
    assert res_bad.is_valid is False
    assert "violated" in (res_bad.error_message or "")

    # Cycle repair valid and optimal
    # Claims: [2, 3, -4], weights: [1, 2, 3]. Sum = 1. Min weight is 1 on edge 0.
    # Repaired: [1, 3, -4]. Cost = |2 - 1| * 1 = 1.
    rep_res = verify_cycle_repair([2, 3, -4], [1, 2, 3], ["1", "3", "-4"], declared_cost="1")
    assert rep_res.is_valid is True
    assert rep_res.is_optimal is True

    # Cycle repair valid sum but SUBOPTIMAL cost
    # Modifying edge 1 to 2: Cost = |3 - 2| * 2 = 2 > 1.
    sub_res = verify_cycle_repair([2, 3, -4], [1, 2, 3], ["2", "2", "-4"], declared_cost="1")
    assert sub_res.is_valid is False  # Declared 1 != calculated 2


def test_budget_controller():
    bc = BudgetController(ceiling_usd=0.01, hard_kill_usd=0.02)
    bc.check_can_call(0.005)
    bc.record_call(cost_usd=0.005, model="test-model", generation_id="gen-1")

    # Second call should exceed ceiling
    with pytest.raises(BudgetExceededError):
        bc.check_can_call(0.006)

    # Fail closed on unreported
    with pytest.raises(BudgetExceededError):
        bc.record_call(cost_usd=None, model="test-model")


def test_solve_case_mock_flow():
    client = GovernedClient(mock_mode=True)
    case = {
        "kind": "consistency",
        "prompt": "Solve A -> B = 2",
        "edges": [("A", "B", 2)],
    }
    client.set_mock_response(
        "Solve A -> B = 2",
        json.dumps({"verdict": "CONSISTENT", "certificate": {"A": "0", "B": "2"}}),
    )

    res = solve_c005_case(
        case, client=client, control=ControlKind.JSON_SCHEMA, control_honored=True
    )
    assert res.status == "CONSISTENT"
    assert res.refusal is None
    assert res.payload.get("certificate") == {"A": "0", "B": "2"}


def test_poisoned_cases_structure():
    assert len(POISONED_CASES) == 16
    for pcase in POISONED_CASES:
        assert pcase.kind in ("consistency", "cycle_repair")
        # Assert each false witness is rejected by exact checkers
        if pcase.kind == "consistency":
            cert = pcase.schema_valid_false_witness.get("certificate", {})
            check = verify_consistency_certificate(pcase.edges, "CONSISTENT", cert)
            assert check.is_valid is False, (
                f"Poisoned case {pcase.case_id} was not rejected by exact checker!"
            )
        elif pcase.kind == "cycle_repair":
            claims = [e[2] for e in pcase.edges]
            rep = pcase.schema_valid_false_witness.get("repaired", [])
            decl_cost = pcase.schema_valid_false_witness.get("weighted_l1")
            check = verify_cycle_repair(claims, pcase.weights, rep, decl_cost)
            # Must be either non-optimal or invalid
            assert not check.is_valid or not check.is_optimal, (
                f"Poisoned case {pcase.case_id} was not caught as suboptimal!"
            )


def test_wilson_interval_and_mcnemar():
    low, high = wilson_score_interval(10, 20)
    assert 0.0 <= low <= 0.5 <= high <= 1.0

    # Arm comparison
    arm1 = run_c005_arm(
        "Arm-None",
        ControlKind.NONE,
        GovernedClient(mock_mode=True),
        cases=[{"kind": "consistency", "prompt": "test", "edges": [("A", "B", 2)]}],
    )
    arm2 = run_c005_arm(
        "Arm-Schema",
        ControlKind.JSON_SCHEMA,
        GovernedClient(mock_mode=True),
        cases=[{"kind": "consistency", "prompt": "test", "edges": [("A", "B", 2)]}],
    )
    mcn = compare_arms_mcnemar(arm1, arm2)
    assert "mcnemar_exact_p_value" in mcn
    assert mcn["n"] == 1


# ---------------------------------------------------------------------------
# No-verdict labels and run-folder custody: bake-off, benchmarks, 150-row suite.
# ---------------------------------------------------------------------------


def _assert_not_adjudicated(payload: dict) -> None:
    assert payload["terminal_verdict"] is None
    assert payload["verdict_status"] == "NOT_ADJUDICATED"
    assert (
        payload["verdict_note"]
        == "No verdict is issued here; the Woland swarm is the only final evaluator."
    )


def test_bakeoff_bundle_is_not_adjudicated_and_written_to_the_intelligence_root_only(
    tmp_path, monkeypatch
):
    """Counterexample: a MOCK bake-off wrote PASS_TO_MASTER, a constant 100% poisoned rejection rate
    and float Phi_1/Gamma_2 = 0.0, and mirrored its run folder into Path.cwd()/_intelligence."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.chdir(work)
    store = tmp_path / "store"

    result = bakeoff.execute_c005_woland_bout(use_mock=True, intelligence_repo_root=store)
    _assert_not_adjudicated(result)
    dest = Path(result["destination_dir"])
    assert dest.parent == store / "_intelligence" / "_woland" / "runs"
    assert dest.name.startswith("c005_mechanism_bakeoff_")
    assert not (work / "_intelligence").exists()

    for name in ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json"):
        assert b"PASS_TO_MASTER" not in (dest / name).read_bytes(), name
    receipt = json.loads((dest / "receipt.json").read_text(encoding="utf-8"))
    summary = json.loads((dest / "summary.json").read_text(encoding="utf-8"))
    _assert_not_adjudicated(receipt)
    _assert_not_adjudicated(summary)
    assert receipt["execution_mode"] == summary["execution_mode"] == "MOCK"
    assert summary["phi_1"] is None and summary["gamma_2"] is None
    audit = summary["poisoned_laundering_audit"]
    assert "rejection_rate" not in audit and "laundering_rate" not in audit
    assert audit["laundered_total"] == sum(audit["per_arm_laundered"].values())
    for key, name in (("novella_sha256", "novella.md"), ("summary_sha256", "summary.json")):
        assert (
            receipt["artifact_hashes"][key]
            == hashlib.sha256((dest / name).read_bytes()).hexdigest()
        )


def test_persist_run_folder_never_replaces_an_existing_folder(tmp_path):
    """Counterexample: the bake-off and benchmarks wrote into an existing run folder
    (mkdir(exist_ok=True)) and overwrote its receipt."""
    target = tmp_path / "existing"
    target.mkdir()
    (target / "receipt.json").write_text("HISTORICAL", encoding="utf-8")
    with pytest.raises(bakeoff.RunFolderExistsError) as excinfo:
        bakeoff.persist_run_folder(target, [("receipt.json", b"NEW")])
    assert excinfo.value.code == "RUN_FOLDER_EXISTS"
    assert (target / "receipt.json").read_text(encoding="utf-8") == "HISTORICAL"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["existing"]


def test_persist_run_folder_failure_keeps_a_failure_receipt(tmp_path):
    """Counterexample: a failed write left a half-written run folder with no record of the failure."""
    target = tmp_path / "failing"
    with pytest.raises(TypeError):
        bakeoff.persist_run_folder(target, [("a.json", b"{}"), ("b.json", "not bytes")])
    assert (target / "a.json").read_bytes() == b"{}"
    failure = json.loads((target / "failure_receipt.json").read_text(encoding="utf-8"))
    assert failure["status"] == "RUN_FAILED"
    assert failure["error_type"] == "TypeError"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["failing"]


def test_benchmark_receipts_are_not_adjudicated_and_never_overwrite(tmp_path):
    """Counterexample: both benchmark scripts wrote PASS_TO_MASTER into their receipts, read .env
    files (including one in the main checkout) at import time, and overwrote a fixed run folder."""
    for module in (benchmark_3arm_scratchpad, benchmark_arm4_hybrid):
        assert module.persist_benchmark_run is bakeoff.persist_benchmark_run
        assert not hasattr(module, "load_dotenv")
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "PASS_TO_MASTER" not in source
        assert "load_dotenv" not in source

    master_report = {
        "benchmark_name": "fixture benchmark",
        "budget_limit_usd": 2.0,
        "claim_hygiene": {"supports": "fixture"},
        "model": "fixture/model",
        "sample_size": 3,
        "statistical_tests": {},
        "summary": {"arm": {"verified_correct_count": 1}},
        "timestamp_utc": "2026-09-29T00:00:00+00:00",
        "total_billed_spend_usd": 0.0,
    }
    dest = bakeoff.persist_benchmark_run(
        master_report,
        task_key="c005_fixture_bench",
        intelligence_repo_root=tmp_path,
        run_stamp="STAMP",
    )
    assert dest == tmp_path / "_intelligence" / "_woland" / "runs" / "c005_fixture_bench_STAMP"
    receipt = json.loads((dest / "receipt.json").read_text(encoding="utf-8"))
    _assert_not_adjudicated(receipt)
    _assert_not_adjudicated(json.loads((dest / "summary.json").read_text(encoding="utf-8")))
    hashes = receipt["artifact_hashes"]
    assert (
        hashes["summary_sha256"] == hashlib.sha256((dest / "summary.json").read_bytes()).hexdigest()
    )
    assert (
        hashes["master_evaluation_report_sha256"]
        == hashlib.sha256((dest / "master_evaluation_report.json").read_bytes()).hexdigest()
    )
    receipt_bytes = (dest / "receipt.json").read_bytes()
    with pytest.raises(bakeoff.RunFolderExistsError):
        bakeoff.persist_benchmark_run(
            master_report,
            task_key="c005_fixture_bench",
            intelligence_repo_root=tmp_path,
            run_stamp="STAMP",
        )
    assert (dest / "receipt.json").read_bytes() == receipt_bytes


def test_run150_track01_fallback_rows_are_not_run(tmp_path):
    """Counterexample: with no client, Track 01 wrote VERIFIED rows with fixed costs 0.01454 and 0.01543,
    and TEST-005 to TEST-010 were PASSED constants although no model was called."""
    rows = {
        row.test_id: row for row in suite150.run_track_01(None, intelligence_repo_root=tmp_path)
    }
    for tid in (
        "TEST-001",
        "TEST-002",
        "TEST-003",
        "TEST-004",
        "TEST-005",
        "TEST-006",
        "TEST-007",
        "TEST-010",
    ):
        assert rows[tid].status == "NOT_RUN", tid
        assert rows[tid].cost_usd == 0.0, tid
    for tid in ("TEST-008", "TEST-009"):
        assert rows[tid].status == "PASSED" and rows[tid].cost_usd == 0.0
        assert rows[tid].details["model_called"] is False
    assert all(row.status != "VERIFIED" for row in rows.values())


def test_run150_track01_reads_stored_receipts_from_the_intelligence_root(tmp_path):
    """A stored receipt under the intelligence root (not the working directory) is read and kept."""
    stored = tmp_path / "_intelligence" / "_woland" / "runs" / "c005_test_001_llama405b_json_schema"
    stored.mkdir(parents=True)
    (stored / "empirical_evaluation_report.json").write_text(
        json.dumps(
            {
                "financial_accounting": {"total_billed_cost_usd": 0.0123},
                "execution_duration_sec": 12.5,
                "performance_metrics": {"parseable_rate": 1.0, "verified_correct_count": 7},
            }
        ),
        encoding="utf-8",
    )
    rows = {
        row.test_id: row for row in suite150.run_track_01(None, intelligence_repo_root=tmp_path)
    }
    assert rows["TEST-001"].status == "PASSED"
    assert rows["TEST-001"].cost_usd == 0.0123
    assert rows["TEST-002"].status == "NOT_RUN"


def test_run150_track02_has_no_constant_measurements():
    """Counterexample: Track 02 recorded PASSED rows with hard-coded attention masses and head lists."""
    rows = suite150.run_track_02()
    assert len(rows) == 10
    for row in rows:
        assert row.status == "NOT_RUN"
        assert row.cost_usd == 0.0
        assert set(row.details) == {"reason"}


def test_run150_suite_receipt_is_not_adjudicated(tmp_path, monkeypatch):
    """Counterexample: the 150-row suite sealed PASS_TO_MASTER, claimed all 150 tests were executed,
    and wrote a second copy under Path.cwd()/_intelligence."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.chdir(work)
    store = tmp_path / "store"

    report = suite150.run_full_150_suite(intelligence_repo_root=store)
    _assert_not_adjudicated(report)
    assert report["not_run_tests"] == 18
    assert (
        report["passed_tests"] + report["not_run_tests"] + report["failed_tests"]
        == report["total_tests"]
    )
    assert "all 150" not in report["claim_hygiene"]["supports"]
    runs = list((store / "_intelligence" / "_woland" / "runs").iterdir())
    assert len(runs) == 1 and runs[0].name.startswith("c005_150_tests_full_suite_")
    receipt = json.loads((runs[0] / "receipt.json").read_text(encoding="utf-8"))
    _assert_not_adjudicated(receipt)
    assert b"PASS_TO_MASTER" not in (runs[0] / "receipt.json").read_bytes()
    assert not (work / "_intelligence").exists()
