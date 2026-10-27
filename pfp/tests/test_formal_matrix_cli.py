"""Explicit exploratory CLI selection uses the original accounted PFP runner."""

from copy import deepcopy
import json
from pathlib import Path
import urllib.request

import pytest

from pfp.infrastructure import formal_matrix as matrix
from pfp.infrastructure import pilot_matrix
from pfp.tests.test_pilot_matrix_pfp import make_gateway


ARGS = [
    "--model",
    "vendor/model",
    "--max-estimated-cost-microusd",
    "50000",
    "--max-provider-calls",
    "1",
    "--max-output-tokens",
    "256",
]


def options():
    return dict(
        challenge_id="C044",
        models=[{"id": "vendor/model", "max_tokens": 4096}, {"id": "vendor/other"}],
        cases=[
            {"case_id": "PRIVATE-ONE", "expected": 1, "data": 2},
            {"case_id": "PRIVATE-TWO", "expected": 2, "data": 3},
        ],
        system_prompt="Solve the public task.",
        evaluate=lambda case, answer: (answer["value"] == case["expected"], "original judge"),
        max_tokens=4096,
        pause_sec=0,
    )


def forbid_work(monkeypatch):
    monkeypatch.setattr(matrix, "run_folder", lambda *_a: pytest.fail("output before preflight"))
    monkeypatch.setattr(
        pilot_matrix,
        "make_pilot_gateways",
        lambda *_a, **_k: pytest.fail("gateway before preflight"),
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: pytest.fail("raw transport"))


def test_actual_cli_selection_accounting_and_original_catalog_preserved(tmp_path, monkeypatch):
    original = options()
    catalog = deepcopy((original["models"], original["cases"]))
    folder = tmp_path / "matrix"
    monkeypatch.setattr(matrix, "run_folder", lambda *_a: folder.mkdir() or folder)
    created, providers, judged, prompted = [], [], [], []

    def factory(model_ids, **policy):
        created.append((model_ids, policy))
        gateways = {}
        for model in model_ids:
            gateway, provider = make_gateway(
                tmp_path,
                model=model,
                max_calls=policy["max_calls"],
                max_output_tokens=policy["max_output_tokens"],
                answer={"value": 1},
            )
            gateways[model] = gateway
            providers.append(provider)
        return gateways

    def judge(case, answer):
        judged.append((case, answer))
        return answer == {"value": 1, "case_id": case["case_id"]}, "original judge"

    def prompt(case, token):
        prompted.append((case, token))
        return matrix.build_user_prompt(case, token)

    monkeypatch.setattr(pilot_matrix, "make_pilot_gateways", factory)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: pytest.fail("raw transport"))
    original.update(evaluate=judge, prompt_builder=prompt)
    result = matrix.run_model_matrix_cli(
        argv=ARGS + ["--case-limit", "1", "--env-file", str(tmp_path / "explicit.env")], **original
    )
    assert result == folder and isinstance(result, Path)
    assert (original["models"], original["cases"]) == catalog
    assert len(created) == len(providers) == len(judged) == len(prompted) == 1
    assert created[0][0] == ["vendor/model"]
    assert created[0][1] == dict(
        max_output_tokens=256,
        max_estimated_cost_microusd=50000,
        max_calls=1,
        accounting_path=folder / "budget.sqlite3",
        env_file=tmp_path / "explicit.env",
    )
    assert judged[0][0]["case_id"] == "PRIVATE-ONE"
    assert all(secret not in providers[0].calls[0].user for secret in ("PRIVATE-ONE", '"expected"'))
    record = json.loads((folder / "run_record.json").read_bytes())
    assert record["models"]["vendor/model"]["records"][0]["outcome"] == "VERIFIED"
    config = record["configuration"]
    assert config["original_case_count"] == 2 and config["selected_case_count"] == 1
    assert config["original_max_tokens"] == 4096 and config["max_output_tokens"] == 256
    assert config["original_model_max_tokens"] == {"vendor/model": 4096, "vendor/other": 4096}


@pytest.mark.parametrize(
    "flag",
    ["--model", "--max-estimated-cost-microusd", "--max-provider-calls", "--max-output-tokens"],
)
def test_required_controls_have_no_provider_or_model_defaults(monkeypatch, flag):
    forbid_work(monkeypatch)
    args = ARGS.copy()
    index = args.index(flag)
    del args[index : index + 2]
    with pytest.raises(SystemExit) as raised:
        matrix.run_model_matrix_cli(argv=args, **options())
    assert raised.value.code == 2


@pytest.mark.parametrize(
    "flag,value",
    [
        ("--model", "unknown/model"),
        ("--max-estimated-cost-microusd", "0"),
        ("--max-estimated-cost-microusd", "50001"),
        ("--max-provider-calls", "0"),
        ("--max-provider-calls", "65"),
        ("--max-output-tokens", "0"),
        ("--max-output-tokens", "3001"),
        ("--case-limit", "0"),
    ],
)
def test_unknown_model_and_invalid_limits_refuse_before_work(monkeypatch, flag, value):
    forbid_work(monkeypatch)
    args = ARGS.copy()
    if flag in args:
        args[args.index(flag) + 1] = value
    else:
        args.extend([flag, value])
    with pytest.raises(SystemExit) as raised:
        matrix.run_model_matrix_cli(argv=args, **options())
    assert raised.value.code == 2


def test_help_requires_neither_configuration_nor_credentials(monkeypatch, capsys):
    forbid_work(monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit) as raised:
        matrix.run_model_matrix_cli(argv=["--help"])
    assert raised.value.code == 0
    assert "--max-provider-calls" in capsys.readouterr().out


def test_empty_cases_refuse_before_output_or_gateway_work(monkeypatch):
    forbid_work(monkeypatch)
    plan = options()
    plan["cases"] = []
    with pytest.raises(SystemExit) as raised:
        matrix.run_model_matrix_cli(argv=ARGS, **plan)
    assert raised.value.code == 2


def test_repeatable_models_share_existing_continuing_call_allowance(tmp_path, monkeypatch):
    first, provider = make_gateway(tmp_path, max_calls=1, answer={"value": 1})
    second, other = make_gateway(tmp_path, model="vendor/other", max_calls=1)
    folder = tmp_path / "matrix"
    monkeypatch.setattr(matrix, "run_folder", lambda *_a: folder.mkdir() or folder)
    matrix.run_model_matrix_cli(
        argv=ARGS + ["--model", "vendor/other", "--case-limit", "1"],
        gateways={"vendor/model": first, "vendor/other": second},
        **options(),
    )
    assert len(provider.calls) == 1 and other.calls == []
    record = json.loads((folder / "run_record.json").read_bytes())
    assert record["stop_reason"] == "CALL_ALLOWANCE_EXHAUSTED"


def test_injected_gateway_cannot_exceed_explicit_cli_call_cap(tmp_path, monkeypatch):
    gateway, provider = make_gateway(tmp_path, max_calls=4)
    forbid_work(monkeypatch)
    with pytest.raises(SystemExit) as raised:
        matrix.run_model_matrix_cli(argv=ARGS, gateways={"vendor/model": gateway}, **options())
    assert raised.value.code == 2 and provider.calls == []
