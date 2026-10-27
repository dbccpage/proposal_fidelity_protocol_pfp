"""Bounded braid tournament fixtures through the actual shared PFP gateway."""

import base64
import importlib
import json
from fractions import Fraction

import pytest

from pfp.tests.test_pilot_matrix_pfp import make_gateway


def owner():
    return importlib.import_module("pfp.infrastructure.braid_tournament")


def live(module, tmp_path, gateway, **kwargs):
    config = module.ProposerStrategyConfig("worker", "vendor/model", "echo_mitigated", True)
    return module.AdaptiveBraidTournament("bound", proposers=[config],
        gateways={"vendor/model": gateway}, output_dir=tmp_path / "new",
        max_output_tokens=128, max_provider_calls=4, **kwargs)


def test_offline_uses_real_referee_and_does_not_claim_models(tmp_path):
    module = owner()
    run = module.AdaptiveBraidTournament("offline", output_dir=tmp_path / "new")
    receipt = run.run_sweep([Fraction(1, 100)])
    assert len(receipt.round_results) == 4 and receipt.models_evaluated == ()
    assert all(type(row.circuit_noise_defect) is Fraction for row in receipt.round_results)
    assert run.report["evidence_grade"] == "DETERMINISTIC_ORIGINAL_REFEREE"
    assert run.report["provider_calls"] == 0 and run.report["observed_models"] == []
    assert run.report["financial_policy"] == "no_provider"
    assert run.report["judged_live_results"] == 0
    assert run.report["judged_deterministic_results"] == 4
    assert (tmp_path / "new" / "tournament.json").is_file()


def test_bound_live_reaches_original_referee_and_keeps_wire(tmp_path):
    module = owner()
    gateway, provider = make_gateway(tmp_path, answer={"operations": [["hadamard", [1, 0]]]}, max_output_tokens=128)
    run = live(module, tmp_path, gateway)
    receipt = run.run_sweep([Fraction(1, 100)])
    assert len(provider.calls) == 1 and len(receipt.round_results) == 1
    assert receipt.models_evaluated == ("vendor/model",)
    assert run.report["evidence_grade"] == "BOUND_MODEL_ORIGINAL_REFEREE"
    assert run.report["judged_live_results"] == 1
    trace = run.report["observations"][0]["exchange"]
    assert trace["pfp"]["failure_class"] == "NONE"
    assert base64.b64decode(trace["provider_wire"]["raw_reply_base64"]) == provider.raw
    public = json.loads(provider.calls[0].user)
    assert "expected" not in public["input"]["prompt"]


@pytest.mark.parametrize("raw", ["not-json", '{"task_id":"wrong","answer":{"operations":[]}}'])
def test_bad_binding_does_not_fall_back_or_reach_referee(tmp_path, raw):
    module = owner()
    gateway, provider = make_gateway(tmp_path, raw_content=raw, max_output_tokens=128)
    run = live(module, tmp_path, gateway)
    run.referee = type("NeverJudge", (), {"evaluate": lambda *args: pytest.fail("unbound reply reached judge")})()
    receipt = run.run_sweep([Fraction(1, 100), Fraction(1, 50)])
    assert len(provider.calls) == 1 and not receipt.round_results
    assert run.report["stop_reason"].startswith("PFP_")
    assert run.report["evidence_grade"] == "NO_REFEREE_RESULTS"
    assert run.report["observations"][0]["exchange"]["provider_wire"]


def test_unknown_cost_stops_all_later_rounds(tmp_path):
    module = owner()
    gateway, provider = make_gateway(tmp_path, cost=None,
        answer={"operations": [["hadamard", [1, 0]]]}, max_output_tokens=128)
    run = live(module, tmp_path, gateway)
    receipt = run.run_sweep([Fraction(1, 100), Fraction(1, 50)])
    assert len(provider.calls) == 1 and not receipt.round_results
    assert run.report["stop_reason"] == "CompletedCostUnknown"
    assert run.report["total_cost_usd"] is None
    assert run.report["evidence_grade"] == "NO_REFEREE_RESULTS"


def test_partial_mixed_run_only_grades_observed_deterministic_results(tmp_path):
    module = owner()
    gateway, provider = make_gateway(tmp_path, raw_content="not-json", max_output_tokens=128)
    configs = [
        module.ProposerStrategyConfig("offline", "historical-label", "direct_unmitigated"),
        module.ProposerStrategyConfig("live", "vendor/model", "echo_mitigated", True),
    ]
    run = module.AdaptiveBraidTournament("mixed", proposers=configs,
        gateways={"vendor/model": gateway}, output_dir=tmp_path / "new",
        max_output_tokens=128, max_provider_calls=4)
    receipt = run.run_sweep([Fraction(1, 100)])
    assert len(provider.calls) == 1 and len(receipt.round_results) == 1
    assert not run.report["completed"]
    assert run.report["evidence_grade"] == "DETERMINISTIC_ORIGINAL_REFEREE"
    assert run.report["judged_live_results"] == 0
    assert run.report["judged_deterministic_results"] == 1
    assert run.report["observed_models"] == []


def test_live_without_policy_never_falls_back(tmp_path):
    module = owner()
    config = module.ProposerStrategyConfig("worker", "vendor/model", "echo_mitigated", True)
    run = module.AdaptiveBraidTournament("no-policy", proposers=[config], output_dir=tmp_path / "new")
    with pytest.raises(ValueError, match="ACCOUNTED|POLICY"):
        run.run_sweep([Fraction(1, 100)])
    assert not (tmp_path / "new").exists()


def test_existing_output_refuses_without_calls(tmp_path):
    module = owner()
    gateway, provider = make_gateway(tmp_path, max_output_tokens=128)
    (tmp_path / "new").mkdir()
    (tmp_path / "new" / "tournament.json").write_bytes(b"historical")
    with pytest.raises(ValueError, match="OUTPUT_DIR_EXISTS"):
        live(module, tmp_path, gateway).run_sweep([Fraction(1, 100)])
    assert not provider.calls and (tmp_path / "new" / "tournament.json").read_bytes() == b"historical"


def test_agents_use_one_continuing_call_allowance(tmp_path):
    module = owner()
    gateway, provider = make_gateway(tmp_path, max_calls=1,
        answer={"operations": [["hadamard", [1, 0]]]}, max_output_tokens=128)
    configs = [module.ProposerStrategyConfig(str(i), "vendor/model", "echo_mitigated", True) for i in range(2)]
    run = module.AdaptiveBraidTournament("shared", proposers=configs,
        gateways={"vendor/model": gateway}, output_dir=tmp_path / "new",
        max_output_tokens=128, max_provider_calls=1)
    receipt = run.run_sweep([Fraction(1, 100)])
    assert len(provider.calls) == 1 and len(receipt.round_results) == 1
    assert run.report["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"
