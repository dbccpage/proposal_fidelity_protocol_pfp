"""Optional real, pinned local checkpoint controls; never fixture/model conflation.

Set PFP_LOCAL_MODEL_DIR and PFP_LOCAL_MODEL_REVISION to execute this named file.
An ordinary offline installation need not download a model to collect tests.
"""
import json
import os

import pytest

from omega_engine_woland.tests.pilots.challenge_suite.local_mechanism_trials import (
    cases,
    expected,
    finite_language,
    judge,
    load_runner,
    second_judge,
    turn_for,
)


@pytest.fixture(scope="module")
def runner():
    path, revision = os.environ.get("PFP_LOCAL_MODEL_DIR"), os.environ.get("PFP_LOCAL_MODEL_REVISION")
    if not path or not revision:
        pytest.skip("Explicit pinned local checkpoint required; no automatic download or fixture fallback")
    return load_runner(path, model_id="HuggingFaceTB/SmolLM2-135M-Instruct", revision=revision,
        custody_manifest=os.environ.get("PFP_LOCAL_MODEL_CUSTODY"))


def prompt(runner):
    return runner.render(turn_for(cases()[2], attempt_id="numerical-control"))


def test_original_case_mutations_are_rejected_and_exact_restore_recovers():
    assert len(cases()) == 8
    for case in cases():
        answer = expected(case)
        assert judge(case, answer)[0] and second_judge(case, answer)[0]
        if case["kind"] == "product_sign":
            mutation = answer | {"negative_count": str(int(answer["negative_count"]) + 2)}
        elif case["kind"] == "cycle_sum":
            mutation = answer | {"sum": str(int(answer["sum"]) + 1)}
        else:
            mutation = answer | {"anticommuting_sites": answer["anticommuting_sites"][:-1]}
        assert not judge(case, mutation)[0] and not second_judge(case, mutation)[0]
        assert judge(case, answer)[0] and second_judge(case, answer)[0]


def test_blind_residual_capture_never_reads_target_expected_certificate(monkeypatch):
    from omega_engine_woland.tests.pilots.challenge_suite import local_mechanism_trials as trials
    class StopAfterCapture(Exception):
        pass
    class Vector:
        def __sub__(self, other):
            return self
        def __getitem__(self, index):
            return self
    class NoOracleRunner:
        def render(self, turn):
            return turn.prompt.user
        def capture(self, text, **kwargs):
            assert "anticommuting_sites" not in text and '"XYIZ"' not in text
            return Vector()
        def generate(self, *args, **kwargs):
            raise StopAfterCapture
    monkeypatch.setattr(trials, "expected", lambda *_: pytest.fail("oracle read before participant generation"))
    with pytest.raises(StopAfterCapture):
        trials.run(NoOracleRunner(), selected_case_ids=["pauli-0"])


def test_local_model_declared_revision_cannot_override_manifest_or_changed_bytes(tmp_path):
    from hashlib import sha256

    from omega_engine_woland.tests.pilots.challenge_suite.local_mechanism_trials import (
        checkpoint_binding,
    )
    model = tmp_path / "checkpoint"
    model.mkdir()
    weights = model / "model.safetensors"
    weights.write_bytes(b"literal test model bytes, not a real model")
    manifest = tmp_path / "custody.json"
    manifest.write_text(json.dumps(dict(model_id="test/model", revision="a" * 40,
        files={"model.safetensors": sha256(weights.read_bytes()).hexdigest()},
        remote_code=False, serialization="safetensors only")))
    def read(revision="a" * 40):
        return checkpoint_binding(model, model_id="test/model", revision=revision, custody_manifest=manifest)
    assert read()["identity_status"] == "EXACT_BYTES_MATCH_EXISTING_COMPOSITION_MANIFEST"
    with pytest.raises(ValueError, match="CUSTODY_MISMATCH"):
        read("b" * 40)
    original = weights.read_bytes()
    weights.write_bytes(b"changed")
    with pytest.raises(ValueError, match="CUSTODY_MISMATCH"):
        read()
    weights.write_bytes(original)
    assert read()["identity_status"] == "EXACT_BYTES_MATCH_EXISTING_COMPOSITION_MANIFEST"


@pytest.mark.parametrize("spec", [dict(heads=dict(layer=-1, heads=[0], alpha=1)),
    dict(patch=dict(layer=2, head=0, value=None)), dict(residual=dict(layer=True, vector=None, alpha=1)),
    dict(attention=dict(layers=[2], positions=[0], delta=1)),
    dict(attention=dict(layers=[], positions=[0], delta=1)),
    dict(attention=dict(layers=[0, 0], positions=[0], delta=1)),
    dict(heads=dict(layer=0, heads=[0], alpha=float("nan"))),
    dict(residual=dict(layer=0, vector=None, alpha=float("inf")))])
def test_invalid_hook_selection_refuses_before_registering_any_handle(spec):
    from omega_engine_pfp.infrastructure.adapters.decode_controls.local_hf_mechanism import (
        HfLocalRunner,
    )
    runner = HfLocalRunner.__new__(HfLocalRunner)
    runner.layers, runner.torch = [object(), object()], None
    with pytest.raises(ValueError):
        with runner.interventions(**spec):
            pytest.fail("invalid control was executed as a silent no-op")


def test_secondary_pauli_sites_reject_same_parity_primary_oracle_mutation(monkeypatch):
    from omega_engine_woland.tests.pilots.challenge_suite import local_mechanism_trials as trials
    case = cases()[6]
    original = expected(case)
    changed = dict(original, anticommuting_sites=["1"])
    assert original["anticommuting_sites"] == ["0"]
    with monkeypatch.context() as m:
        m.setattr(trials, "expected", lambda _case: changed)
        assert trials.judge(case, changed)[0]
        assert not trials.second_judge(case, changed)[0]
    assert trials.judge(case, original)[0] and trials.second_judge(case, original)[0]


def test_local_collation_ignores_forged_success_and_refuses_raw_tamper():
    import base64
    from copy import deepcopy
    from hashlib import sha256

    from omega_engine_woland.tests.pilots.challenge_suite.protocol_collation import recheck_local_trial
    case = cases()[2]
    turn = turn_for(case, attempt_id="collation-mutation")
    answer = expected(case) | {"negative_count": "0"}
    assert not judge(case, answer)[0]
    raw = json.dumps({key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")} |
        {"answer": answer}).encode()
    trial = dict(case=case, binding=turn.binding, prepared_prompt=turn.prompt.to_dict(),
        raw_reply_base64=base64.b64encode(raw).decode(), raw_reply_sha256=sha256(raw).hexdigest(),
        pfp=dict(status="HOST_ACCEPTED", schema_valid=True))
    rechecked = recheck_local_trial(trial, recipe="local-mechanism-v1.0.0")
    assert rechecked["schema_valid"] and rechecked["status"] != "HOST_ACCEPTED"
    changed = deepcopy(trial)
    changed["raw_reply_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="RAW_MISMATCH"):
        recheck_local_trial(changed, recipe="local-mechanism-v1.0.0")
    assert recheck_local_trial(trial, recipe="local-mechanism-v1.0.0")["status"] == rechecked["status"]


@pytest.mark.parametrize("missing", range(4))
def test_moved_protocol_sources_refuse_missing_member_before_inference(missing, tmp_path, monkeypatch):
    from omega_engine_woland.tests.pilots.challenge_suite import local_mechanism_trials as trials
    from omega_engine_woland.tests.pilots.challenge_suite.catalog import SOURCE
    assert trials.SOURCE == SOURCE / "a_mechanism"
    original = trials.protocol_sources()
    assert set(original) == set(trials.PROTOCOL_FILES)
    for name in trials.PROTOCOL_FILES:
        (tmp_path / name).write_bytes((trials.SOURCE / name).read_bytes())
    monkeypatch.setattr(trials, "SOURCE", tmp_path)
    assert trials.protocol_sources() == original
    path = tmp_path / trials.PROTOCOL_FILES[missing]
    raw = path.read_bytes()
    path.unlink()
    with pytest.raises(ValueError, match="PROTOCOL_SOURCE_UNAVAILABLE"):
        trials.run(object())  # No model method can run before source refusal.
    path.write_bytes(raw)
    assert trials.protocol_sources() == original


def test_actual_attention_bias_null_and_restore(runner):
    text = prompt(runner)
    start = text.index('"factors"')
    keys = runner.carrier_positions(text, [(start, start + len('"factors"'))])
    baseline, _ = runner.forward(text)
    null, readouts = runner.forward(text, attention=dict(layers=[0], positions=keys, delta=0))
    assert runner.torch.equal(baseline, null) and all(row["changed_entries"] == 0 for row in readouts)
    biased, readouts = runner.forward(text, attention=dict(layers=[0], positions=keys, delta=4))
    assert any(row["changed_entries"] > 0 for row in readouts)
    assert not runner.torch.equal(baseline, biased)
    restored, _ = runner.forward(text)
    assert runner.torch.equal(baseline, restored)


def test_actual_head_scaling_null_ablation_and_hook_cleanup_on_exception(runner):
    text = prompt(runner)
    baseline, _ = runner.forward(text)
    null, _ = runner.forward(text, heads=dict(layer=0, heads=[0], alpha=1))
    assert runner.torch.equal(baseline, null)
    changed, readouts = runner.forward(text, heads=dict(layer=0, heads=[0], alpha=0))
    assert not runner.torch.equal(baseline, changed) and any(row["changed_norm"] > 0 for row in readouts)
    before = len(runner.layers[0].self_attn.o_proj._forward_pre_hooks)
    with pytest.raises(ValueError, match="SHAPE_MISMATCH"):
        runner.forward(text, patch=dict(layer=0, head=0, value=runner.torch.zeros(1, 1)))
    assert len(runner.layers[0].self_attn.o_proj._forward_pre_hooks) == before
    assert runner.torch.equal(runner.forward(text)[0], baseline)


def test_actual_clean_corrupted_head_patch_changes_corrupted_logits(runner):
    case = cases()[2]
    corrupt = dict(case, factors=[-case["factors"][0], *case["factors"][1:]])
    clean_text = runner.render(turn_for(case, attempt_id="patch"))
    corrupt_text = runner.render(turn_for(corrupt, attempt_id="patch"))
    clean = runner.capture(clean_text, layer=0, kind="head", head=0)
    original, _ = runner.forward(corrupt_text)
    patched, readouts = runner.forward(corrupt_text, patch=dict(layer=0, head=0, value=clean))
    assert not runner.torch.equal(original, patched)
    assert any(row["changed_norm"] > 0 for row in readouts)
    assert runner.torch.equal(runner.forward(corrupt_text)[0], original)


def test_actual_residual_contrast_null_positive_negated_and_restore(runner):
    text = prompt(runner)
    vector = (runner.capture(text + " +", layer=0, kind="residual")
        - runner.capture(text + " -", layer=0, kind="residual"))[0]
    assert float(vector.norm()) > 0
    baseline, _ = runner.forward(text)
    null, _ = runner.forward(text, residual=dict(layer=0, vector=vector, alpha=0))
    positive, pos = runner.forward(text, residual=dict(layer=0, vector=vector, alpha=1))
    negative, neg = runner.forward(text, residual=dict(layer=0, vector=vector, alpha=-1))
    assert runner.torch.equal(null, baseline)
    assert not runner.torch.equal(positive, negative)
    assert any(row["changed_norm"] > 0 for row in pos + neg)
    assert runner.torch.equal(runner.forward(text)[0], baseline)


def test_actual_tokenizer_grammar_generation_checks_raw_bytes_without_host_answer(runner):
    case = cases()[2]
    turn = turn_for(case, attempt_id="finite-grammar")
    language = finite_language(turn, case)
    assert any(not judge(case, json.loads(reply)["answer"])[0] for reply in language)
    result = runner.generate(turn, seed=94, max_tokens=160, allowed_replies=language)
    assert result["raw_reply"].decode() in language
    checked = turn.check(result["raw_reply"], judges=(("original", lambda _c, a: judge(case, a)),
        ("secondary", lambda _c, a: second_judge(case, a))), require_checker=True)
    assert checked["schema_valid"] is True  # Wrong mathematical answers may still fail.
    assert result["enforcement"] == "FINITE_TOKEN_TRIE" and result["token_ids"]


def test_actual_temperature_seed_repeatability(runner):
    turn = turn_for(cases()[3], attempt_id="temperature")
    for temperature in (0, 0.7):
        first = runner.generate(turn, seed=411, max_tokens=8, temperature=temperature)
        replay = runner.generate(turn, seed=411, max_tokens=8, temperature=temperature)
        assert first["token_ids"] == replay["token_ids"]


def test_actual_additive_logit_bias_changes_next_token_and_restores(runner):
    turn = turn_for(cases()[3], attempt_id="logit-bias")
    logits, _ = runner.forward(runner.render(turn))
    ranked = logits[0].topk(2).indices.tolist()
    ordinary = runner.generate(turn, seed=12, max_tokens=1)
    biased = runner.generate(turn, seed=12, max_tokens=1, logit_bias={ranked[1]: 16})
    restored = runner.generate(turn, seed=12, max_tokens=1)
    assert ordinary["token_ids"] == [ranked[0]]
    assert biased["token_ids"] == [ranked[1]]
    assert biased["logit_readouts"][0]["changed_entries"] == 1
    assert restored["token_ids"] == ordinary["token_ids"]


def test_actual_incremental_kv_reuse_matches_full_recompute(runner):
    result = runner.cache_parity(prompt(runner), steps=3)
    assert result["token_exact"] and len(result["cached_token_ids"]) == 3
    assert result["provider_calls"] == 0


def test_actual_selective_kv_surgery_records_literal_parity_without_promotion(runner):
    text = prompt(runner)
    count = len(runner.tokenizer.encode(text, add_special_tokens=False))
    result = runner.cache_parity(text, steps=3, keep_positions=[0, count - 2, count - 1])
    assert result["kept_positions"] == [0, count - 2, count - 1]
    assert len(result["cached_token_ids"]) == 3
    assert result["scope"] == "FINITE_CACHE_MECHANICS_NOT_C007_LONG_HORIZON_RESULT"
