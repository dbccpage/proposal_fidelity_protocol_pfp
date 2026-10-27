"""The public CLI distinguishes a controlled refusal from failed execution."""
import importlib
import json
from pathlib import Path

import pytest

CLI = importlib.import_module(f"{Path(__file__).resolve().parents[1].name}.entrypoints.cli.pfp")


def test_expected_negative_mode_control_does_not_fail_a_completed_prefix(tmp_path, capsys):
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"14": {"payload": {}, "expected_reason": "MISSING_OR_EXTRA_FIELDS: candidate"}}))
    code = CLI.main(["run-seed", "DEMO-N02", "--stages", "1", "--modes", "14", "--mode-inputs", str(inputs)])
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result["completed_stages"] == [1]
    assert result["host_checks"][0]["passed"] is False
    assert result["provider_calls"] == 0
    assert result["all_stages_passed"] is False


def test_unavailable_offline_seed_witness_returns_failure(capsys):
    assert CLI.main(["run-seed", "DEMO_07", "--stages", "5"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFUSED"
    assert result["provider_calls"] == 0


def live_args(tmp_path):
    return ["run-seed", "DEMO-N02", "--stages", "1", "--model", "vendor/model",
            "--output", str(tmp_path / "run"), "--max-provider-calls", "1",
            "--max-output-tokens", "512", "--max-estimated-cost-microusd", "1000"]


@pytest.mark.parametrize("flag,value", [
    ("--max-provider-calls", "0"), ("--max-output-tokens", "3001"),
    ("--max-estimated-cost-microusd", "0"), ("--timeout", "nan"),
])
def test_invalid_live_limits_refuse_before_credentials_or_output(tmp_path, monkeypatch, capsys, flag, value):
    from pfp.infrastructure import estimated_gateway

    monkeypatch.setattr(estimated_gateway, "create_accounted_openrouter_gateway",
                        lambda *a, **kw: pytest.fail("invalid input reached credentials"))
    args = live_args(tmp_path)
    if flag in args:
        args[args.index(flag) + 1] = value
    else:
        args += [flag, value]
    assert CLI.main(args) == 2
    assert json.loads(capsys.readouterr().out)["provider_calls"] == 0
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize("suffix", ["", ".budget.sqlite3", ".budget.sqlite3.replies"])
def test_live_output_or_accounting_cannot_be_reused(tmp_path, monkeypatch, capsys, suffix):
    from pfp.infrastructure import estimated_gateway

    monkeypatch.setattr(estimated_gateway, "create_accounted_openrouter_gateway",
                        lambda *a, **kw: pytest.fail("existing state reached credentials"))
    existing = tmp_path / ("run" + suffix)
    existing.write_bytes(b"preserve existing state")
    assert CLI.main(live_args(tmp_path)) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "LIVE_OUTPUT_AND_ACCOUNTING_MUST_BE_NEW"
    assert existing.read_bytes() == b"preserve existing state"


def test_live_cli_composes_explicit_bounds_and_original_pipeline(tmp_path, monkeypatch, capsys):
    from pfp.infrastructure import estimated_gateway
    from pfp.infrastructure.adapters import pfp_campaign
    from pfp.infrastructure.providers import OfflineDeterministicPfpProvider

    sentinel = object()
    observed = {}

    def factory(model, tokens, **options):
        observed.update(model=model, tokens=tokens, **options)
        return sentinel

    class Adapter(OfflineDeterministicPfpProvider):
        def __init__(self, output, model, *, gateway):
            assert gateway is sentinel and model == "vendor/model"
            output.mkdir()
            self.provider_calls = 0  # This is a CLI composition fixture, not provider evidence.
            self.cost_microusd = 0

    monkeypatch.setattr(estimated_gateway, "create_accounted_openrouter_gateway", factory)
    monkeypatch.setattr(pfp_campaign, "PfpPipelineProviderAdapter", Adapter)
    assert CLI.main(live_args(tmp_path) + ["--timeout", "180"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["completed_stages"] == [1] and result["provider_calls"] == 0
    assert observed["tokens"] == 512 and observed["max_calls"] == 1
    assert observed["max_estimated_cost_microusd"] == 1000 and observed["max_cost_microusd"] is None
    assert observed["timeout"] == 180 and observed["accounting_path"] == tmp_path / "run.budget.sqlite3"
    config = json.loads((tmp_path / "run/config.json").read_bytes())
    assert config["run_id"] == observed["run_id"]
    assert config["objective_sha256"] == observed["objective_sha256"]
    assert config["schema"] == "pfp.numbered-seed-config.v2"


def test_live_requires_explicit_limits_and_reports_credential_refusal(tmp_path, monkeypatch, capsys):
    from pfp.infrastructure import estimated_gateway
    from adversary.domain.providers.types import ProviderConfigError

    calls = []
    def unavailable(*args, **options):
        calls.append(options)
        raise ProviderConfigError("TEST_CREDENTIAL_UNAVAILABLE")
    monkeypatch.setattr(estimated_gateway, "create_accounted_openrouter_gateway", unavailable)
    assert CLI.main(live_args(tmp_path)[:8]) == 2
    assert not calls
    capsys.readouterr()
    assert CLI.main(live_args(tmp_path)) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["reason"] == "TEST_CREDENTIAL_UNAVAILABLE" and result["provider_calls"] == 0
    assert len(calls) == 1 and not (tmp_path / "run").exists()
