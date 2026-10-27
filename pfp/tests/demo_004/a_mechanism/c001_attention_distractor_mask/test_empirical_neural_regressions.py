"""Offline regressions for neural evaluation plumbing; no model weights or downloads."""

import contextlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask import (
    attention_hook as hook,
)
from projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask import (
    empirical_neural_mcnemar_evaluation as runner,
)


class Tensor(np.ndarray):
    @property
    def device(self):
        return "cpu"

    def clone(self):
        return self.copy()

    def unsqueeze(self, axis):
        return np.expand_dims(self, axis)

    def expand(self, batch, width):
        return np.broadcast_to(self, (batch, self.shape[-1] if width == -1 else width)).view(Tensor)


def tensor(value):
    return np.asarray(value).view(Tensor)


class CharacterTokenizer:
    """A deterministic tokenizer exposes chat prefix shifts without model extras."""

    def apply_chat_template(self, messages, **kwargs):
        return (
            "SYSTEM:" + messages[0]["content"] + "\nUSER:" + messages[1]["content"] + "\nASSISTANT:"
        )

    def __call__(self, text, **kwargs):
        assert kwargs["add_special_tokens"] is False
        result = {
            "input_ids": tensor([[ord(c) for c in text]]),
            "attention_mask": tensor([[1] * len(text)]),
        }
        if kwargs.get("return_offsets_mapping"):
            result["offset_mapping"] = tensor([[(i, i + 1) for i in range(len(text))]])
        return result

    def decode(self, tokens, **kwargs):
        return '{"status":"UNKNOWN","refusal":"TEST_FIXTURE"}'


def case():
    return {
        "case_id": "fixture",
        "kind": "verdict",
        "prompt_text": "carrier fluff carrier",
        "distractor_spans": [(8, 13)],
    }


def test_nested_certificate_is_not_truncated():
    solution = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": {"A": "0", "B": "2"},
    }
    for output in (json.dumps(solution), "```json\n" + json.dumps(solution) + "\n```"):
        assert runner.parse_neural_output(output, "verdict") == solution


@pytest.mark.parametrize("kind", ["verdict", "repair", "audit"])
def test_prompt_contract_matches_requested_task(kind):
    prompt = runner.format_chat_prompt("case", kind, CharacterTokenizer())
    assert f'"kind":"{kind}"' in prompt
    if kind == "verdict":
        assert '"potential"' in prompt and '"cycle"' in prompt
    elif kind == "repair":
        assert '"edge"' in prompt and '"value"' in prompt
    else:
        assert '"violated"' in prompt


def test_wrong_task_output_is_refused():
    output = (
        '{"status":"SOLVED","kind":"verdict","answer":"CONTRADICTION","cycle":["A","B","C","A"]}'
    )
    assert runner.parse_neural_output(output, "repair")["refusal"] == "WRONG_TASK_KIND"


@pytest.mark.parametrize("attention_mass, authorized", [(0.1, True), (0.01, False)])
def test_real_input_positions_and_measured_gate(monkeypatch, attention_mass, authorized):
    torch = SimpleNamespace(
        Tensor=Tensor,
        long=int,
        no_grad=contextlib.nullcontext,
        arange=lambda n, **kwargs: tensor(list(range(n))),
        is_floating_point=lambda x: np.issubdtype(x.dtype, np.floating),
    )
    monkeypatch.setattr(runner, "torch", torch)
    monkeypatch.setattr(hook, "torch", torch)
    monkeypatch.setattr(runner, "measure_attention_on_positions", lambda att, pos: att)
    tokenizer = CharacterTokenizer()
    test_case = case()
    full_prompt = runner.format_chat_prompt(test_case["prompt_text"], "verdict", tokenizer)
    expected = list(range(full_prompt.index("fluff"), full_prompt.index("fluff") + 5))

    class Model:
        config = SimpleNamespace(_attn_implementation="eager")

        def __init__(self):
            self.masks = []

        def generate(self, **kwargs):
            self.masks.append(kwargs["attention_mask"].copy())
            assert kwargs["position_ids"].tolist() == [list(range(kwargs["input_ids"].shape[1]))]
            return np.concatenate([kwargs["input_ids"], [[999]]], axis=1).view(Tensor)

        def __call__(self, **kwargs):
            mass = (
                0.0
                if all(kwargs["attention_mask"][0, p] == 0 for p in expected)
                else attention_mass
            )
            return SimpleNamespace(attentions=mass)

    model = Model()
    trace = runner.run_single_neural_case(test_case, model, tokenizer)
    assert trace["fluff_positions"] == expected
    assert trace["is_masking_authorized"] is authorized
    assert trace["masking_verified"] is authorized
    assert trace["fluff_mass_unmasked"] == attention_mass
    assert trace["f_null_matches_a"]
    assert trace["arm_f_null"]["output_tokens"] == trace["arm_a"]["output_tokens"]
    assert np.array_equal(model.masks[0], model.masks[1])
    if authorized:
        assert np.where(model.masks[2][0] == 0)[0].tolist() == expected
    else:
        assert np.array_equal(model.masks[0], model.masks[2])


def test_missing_tokenizer_offsets_fails_closed():
    class NoOffsets(CharacterTokenizer):
        def __call__(self, text, **kwargs):
            return {"input_ids": tensor([[1]]), "attention_mask": tensor([[1]])}

    with pytest.raises(ValueError, match="character offsets"):
        runner.tokenize_case_prompt(case(), NoOffsets())


@pytest.mark.parametrize("count", [0, -1, 201, True])
def test_invalid_sample_size_rejected_before_loading_model(monkeypatch, count):
    def never_load(*args):
        pytest.fail("invalid count tried to load a model")

    monkeypatch.setattr(runner, "get_or_load_neural_model", never_load)
    with pytest.raises(ValueError, match="n_cases"):
        runner.run_empirical_neural_mcnemar_evaluation(n_cases=count)


def test_failed_null_gate_withholds_success_claims_and_inference(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        runner, "get_or_load_neural_model", lambda src: (None, None, "offline-test-double")
    )
    trace = {
        "f_null_matches_a": False,
        "is_masking_authorized": False,
        "masking_verified": False,
        "arm_a": {"is_valid": False},
        "arm_f_distractor": {"is_valid": True},
        "arm_f_delete": {"is_valid": False},
    }
    monkeypatch.setattr(runner, "run_single_neural_case", lambda *args, **kwargs: trace)
    report = runner.run_empirical_neural_mcnemar_evaluation(n_cases=10)
    assert report["validity_gate"]["gate_status"] == "FAILED"
    for key in ("comparison_F_distractor_vs_Arm_A", "comparison_F_distractor_vs_F_delete"):
        assert report[key]["mcnemar"]["is_significant_alpha_0_05"] is None
        assert report[key]["mcnemar"]["usable_for_inference"] is False
    assert report["mechanism_measurements"]["verified_mask_cases"] == 0
    assert "inference withheld" in report["claim_discipline"]["narrowest_defensible_claim"]
    assert report["traces"] == [trace] * 10


@pytest.mark.parametrize(
    "authorized, verified, usable",
    [
        (False, False, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_masking_inference_requires_observed_suppression(
    monkeypatch, tmp_path, authorized, verified, usable
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        runner, "get_or_load_neural_model", lambda src: (None, None, "offline-test-double")
    )
    trace = {
        "f_null_matches_a": True,
        "is_masking_authorized": authorized,
        "masking_verified": verified,
        "arm_a": {"is_valid": False},
        "arm_f_distractor": {"is_valid": True},
        "arm_f_delete": {"is_valid": False},
    }
    monkeypatch.setattr(runner, "run_single_neural_case", lambda *args, **kwargs: trace)
    report = runner.run_empirical_neural_mcnemar_evaluation(n_cases=10)
    assert report["validity_gate"]["gate_status"] == "PASSED"
    for key in ("comparison_F_distractor_vs_Arm_A", "comparison_F_distractor_vs_F_delete"):
        assert report[key]["mcnemar"]["usable_for_inference"] is usable
        assert report[key]["mcnemar"]["is_significant_alpha_0_05"] is (True if usable else None)


def test_default_remote_model_and_tokenizer_use_frozen_revision(monkeypatch, tmp_path):
    calls = []
    model = SimpleNamespace(eval=lambda: None)
    monkeypatch.setattr(runner, "torch", SimpleNamespace(float32="float32"))
    monkeypatch.setattr(runner, "DEFAULT_LOCAL_SNAPSHOT", tmp_path / "missing")
    monkeypatch.setattr(runner, "_CACHED_MODEL", None)
    monkeypatch.setattr(runner, "_CACHED_TOKENIZER", None)
    monkeypatch.setattr(runner, "_CACHED_MODEL_SOURCE", None)

    def load(source, **kwargs):
        calls.append((source, kwargs))
        return model

    fake_transformers = SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=load),
        AutoModelForCausalLM=SimpleNamespace(from_pretrained=load),
    )
    missing = object()
    original = sys.modules.get("transformers", missing)
    sys.modules["transformers"] = fake_transformers
    try:
        runner.get_or_load_neural_model()
        assert len(calls) == 2
        assert all(
            source == runner.DEFAULT_MODEL_ID and kw["revision"] == runner.DEFAULT_MODEL_REVISION
            for source, kw in calls
        )
    finally:
        if original is missing:
            del sys.modules["transformers"]
        else:
            sys.modules["transformers"] = original
