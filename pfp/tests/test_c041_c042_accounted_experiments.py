"""Actual accounted PFP turns retain the original experiment methods and judges."""

import base64
import json

import pytest

from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver import (
    symbol_game_experiment as lean,
)
from pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver import (
    run_symbol_game_matrix as sweep,
)
from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver import (
    symbol_game_routing as sat,
)
from pfp.infrastructure.formal_matrix import ArmAntibodyStore
from pfp.tests.test_pilot_matrix_pfp import make_gateway
from operations.domain.rop.result import Err
from adversary.domain.providers.attempt import ProviderFailure, RetryClass


MODEL = "vendor/model"
LEAN_CASE = {
    "case_id": "PRIVATE-LEAN",
    "statement": "True",
    "prelude": "",
    "expected_kind": "PRIVATE-ANSWER",
}
SAT_CASE = {
    "case_id": "PRIVATE-SAT",
    "family": "coloring",
    "n": 3,
    "k": 3,
    "edges": [[0, 1], [1, 2], [0, 2]],
    "expected_kind": "SAT",
    "category": "PRIVATE-CATEGORY",
}
SAT_ANSWER = {"status": "SOLVED", "kind": "SAT", "solution": {"colour": [0, 1, 2]}}


def test_actual_sat_accounted_turn_reaches_original_judge_and_preserves_wire(tmp_path):
    gateway, provider = make_gateway(tmp_path, answer=SAT_ANSWER)
    result = sat.run_case(
        "unused",
        MODEL,
        "M1_LOGITS",
        SAT_CASE,
        ArmAntibodyStore("own"),
        gateway=gateway,
        max_tokens=256,
    )
    assert result["outcome"] == "VERIFIED"
    row = result["rounds"][0]
    assert row["pfp"]["schema_valid"] and row["attempt_state"] == "CompletedSettled"
    assert row["answer"]["case_id"] == SAT_CASE["case_id"]
    assert base64.b64decode(row["provider_wire"]["raw_reply_base64"]) == provider.raw
    assert row["request"]["max_tokens"] == 256
    assert all(
        secret not in provider.calls[0].user
        for secret in ("PRIVATE-SAT", "PRIVATE-CATEGORY", "expected_kind")
    )


@pytest.mark.parametrize("owner,case", [(lean, LEAN_CASE), (sat, SAT_CASE)])
@pytest.mark.parametrize(
    "raw",
    ["not JSON", '{"task_id":"wrong","attempt_id":"wrong","input_sha256":"wrong","answer":{}}'],
)
def test_failed_bound_reply_never_reaches_judge_and_retains_custody(
    tmp_path, monkeypatch, owner, case, raw
):
    gateway, provider = make_gateway(tmp_path, raw_content=raw)
    monkeypatch.setattr(
        owner, "evaluate_dual", lambda *_a: pytest.fail("unbound reply reached judge")
    )
    if owner is lean:
        result = lean.run_experiment_on_lemma(
            "unused", case, MODEL, "M1_LOGITS", gateway=gateway, max_tokens=256
        )
    else:
        result = sat.run_case(
            "unused",
            MODEL,
            "M1_LOGITS",
            case,
            ArmAntibodyStore("own"),
            gateway=gateway,
            max_tokens=256,
        )
    row = result["rounds"][0]
    assert result["outcome"] == "INFRA_ERROR" and not row["stop"]
    assert not row["pfp"]["schema_valid"] or row["pfp"]["failure_class"] != "NONE"
    assert row["usage"] and row["request"] and row["attempt_state"] == "CompletedSettled"
    assert base64.b64decode(row["provider_wire"]["raw_reply_base64"]) == provider.raw


def test_retraction_uses_unique_bound_attempts_and_stops_on_existing_budget(tmp_path, monkeypatch):
    gateway, provider = make_gateway(
        tmp_path, max_calls=2, answer={"status": "SOLVED", "kind": "PROOF", "proof": "bad"}
    )
    monkeypatch.setattr(
        lean, "evaluate_dual", lambda *_a: (False, "PRIVATE-LEAN rejected", {"outcome": "REJECTED"})
    )
    result = lean.run_experiment_on_lemma(
        "unused", LEAN_CASE, MODEL, "M3_RETRACTION", gateway=gateway, max_tokens=256
    )
    assert len(provider.calls) == 2 and len(result["rounds"]) == 3 and result["stop"]
    assert result["rounds"][-1]["error"] == "CALL_ALLOWANCE_EXHAUSTED"
    bindings = [json.loads(call.user)["attempt_id"] for call in provider.calls]
    assert len(set(bindings)) == 2
    assert all("PRIVATE-LEAN" not in call.user for call in provider.calls)
    assert result["rounds"][1]["injected_antibody_ids"]


def test_c041_ambiguous_transport_without_reply_keeps_unknown_cost(tmp_path, monkeypatch):
    gateway, provider = make_gateway(tmp_path)
    monkeypatch.setattr(
        provider,
        "complete_result",
        lambda *_a, **_k: Err(ProviderFailure("TRANSPORT_LOST", "fixture", RetryClass.TERMINAL)),
    )
    result = lean.run_experiment_on_lemma(
        "unused", LEAN_CASE, MODEL, "M1_LOGITS", gateway=gateway, max_tokens=256
    )
    assert result["stop"] and result["rounds"][0]["provider_wire"] is None
    assert result["rounds"][0]["error"] == "TRANSPORT_LOST"
    assert result["cost_usd"] is None and result["cost_known_subtotal_usd"] == 0


def test_c041_unknown_cost_stops_all_outer_loops_and_renders_unknown(tmp_path, monkeypatch):
    first, provider = make_gateway(tmp_path, cost=None)
    second, other = make_gateway(tmp_path, model="vendor/other")
    folder = tmp_path / "matrix"
    monkeypatch.setattr(sweep, "run_folder", lambda *_a: folder.mkdir() or folder)
    monkeypatch.setattr(lean, "lean_version", lambda: "fixture: Lean not executed")
    monkeypatch.setattr(
        lean, "evaluate_dual", lambda *_a: pytest.fail("unsettled reply reached judge")
    )
    results = sweep.run_full_matrix(
        [("one", MODEL), ("two", "vendor/other")],
        ["M1_LOGITS", "M3_RETRACTION"],
        cases=[LEAN_CASE, {**LEAN_CASE, "case_id": "PRIVATE-TWO"}],
        gateways={MODEL: first, "vendor/other": second},
        max_tokens=256,
    )
    assert len(provider.calls) == 1 and other.calls == [] and len(results) == 1
    assert results[0]["total_cases"] == 1 and results[0]["total_cost_usd"] is None
    assert results[0]["total_cost_known_subtotal_usd"] == 0
    assert results[0]["outcomes"][0]["cost_usd"] is None
    assert "unknown" in (folder / "c041_matrix_report.md").read_text()


def test_c042_unknown_cost_stops_all_arms_and_cases(tmp_path, monkeypatch):
    first, provider = make_gateway(tmp_path, cost=None, answer=SAT_ANSWER)
    second, other = make_gateway(tmp_path, model="vendor/other")
    folder = tmp_path / "matrix"
    monkeypatch.setattr(sat, "run_folder", lambda *_a: folder.mkdir() or folder)
    monkeypatch.setattr(
        sat, "evaluate_dual", lambda *_a: pytest.fail("unsettled reply reached judge")
    )
    sat.run_c042_symbol_game_matrix(
        [("one", MODEL), ("two", "vendor/other")],
        ["M1_LOGITS", "M3_RETRACTION"],
        cases=[SAT_CASE, {**SAT_CASE, "case_id": "PRIVATE-TWO"}],
        gateways={MODEL: first, "vendor/other": second},
        max_tokens=256,
    )
    record = json.loads((folder / "run_record.json").read_bytes())
    assert len(provider.calls) == 1 and other.calls == [] and len(record["arms"]) == 1
    assert len(record["arms"][0]["outcomes"]) == 1 and record["stop_reason"]


def test_outer_matrix_composes_one_allowance_and_does_not_reset_for_arm(tmp_path, monkeypatch):
    from pfp.infrastructure import pilot_matrix

    folder = tmp_path / "matrix"
    created, providers = [], []
    monkeypatch.setattr(sat, "run_folder", lambda *_a: folder.mkdir() or folder)
    monkeypatch.setattr(sat.time, "sleep", lambda *_a: None)

    def factory(models, **policy):
        created.append((models, policy))
        gateway, provider = make_gateway(
            tmp_path,
            max_calls=policy["max_calls"],
            max_output_tokens=policy["max_output_tokens"],
            answer=SAT_ANSWER,
        )
        providers.append(provider)
        return {MODEL: gateway}

    monkeypatch.setattr(pilot_matrix, "make_pilot_gateways", factory)
    sat.run_c042_symbol_game_matrix(
        [("one", MODEL)],
        ["M1_LOGITS", "M3_RETRACTION"],
        cases=[SAT_CASE],
        max_tokens=256,
        max_estimated_cost_microusd=50000,
        max_provider_calls=1,
    )
    assert len(created) == len(providers) == 1 and len(providers[0].calls) == 1
    assert created[0][1]["accounting_path"] == folder / "budget.sqlite3"
    record = json.loads((folder / "run_record.json").read_bytes())
    assert len(record["arms"]) == 2 and record["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"


@pytest.mark.parametrize("owner", [lean, sweep, sat])
def test_cli_has_no_implicit_model_method_or_allowance(monkeypatch, owner):
    for module in (lean, sweep, sat):
        monkeypatch.setattr(
            module, "run_folder", lambda *_a: pytest.fail("output before explicit policy")
        )
    with pytest.raises(SystemExit) as raised:
        owner.main([])
    assert raised.value.code == 2


def test_missing_gateway_refuses_before_raw_transport_or_judge(monkeypatch):
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: pytest.fail("raw fallback"))
    for owner in (lean, sat):
        monkeypatch.setattr(
            owner, "evaluate_dual", lambda *_a: pytest.fail("missing gateway reached judge")
        )
    first = lean.run_experiment_on_lemma("unused", LEAN_CASE, MODEL, "M1_LOGITS")
    second = sat.run_case("unused", MODEL, "M1_LOGITS", SAT_CASE, ArmAntibodyStore("own"))
    for result in (first, second):
        assert result["outcome"] == "INFRA_ERROR"
        assert result["rounds"][0]["error"] == "PFP_ACCOUNTED_GATEWAY_REQUIRED"
        assert result["stop"]


@pytest.mark.parametrize("runner", [sweep.run_full_matrix, sat.run_c042_symbol_game_matrix])
def test_invalid_outer_selection_refuses_before_output(tmp_path, monkeypatch, runner):
    for owner in (lean, sweep, sat):
        monkeypatch.setattr(owner, "run_folder", lambda *_a: pytest.fail("output before preflight"))
    with pytest.raises((ValueError, RuntimeError)):
        runner([("one", MODEL)], [], cases=[SAT_CASE])
