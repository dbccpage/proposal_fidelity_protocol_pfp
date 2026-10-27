"""Sampling protocol controls. Replies are explicit fixtures, never model trials."""
import base64
import json
from copy import deepcopy
from hashlib import sha256

import pytest

from pfp.infrastructure.sampling_frontier import (
    ANCHORS,
    bind_original_anchors,
    coverage_at_k,
    pin_ladder,
    rescore_samples,
)
from pfp.infrastructure.task_turn import prepare_task_turn


def prepared(sample_id, seed):
    return prepare_task_turn(system="fixture arithmetic", user="Find 17 + 29.",
        task_id="fixture-sampling-case", attempt_id=sample_id,
        answer_schema=dict(type="object", properties={"value": {"type": "integer"}},
            required=["value"], additionalProperties=False), checker_id="fixture-two-checkers-v1")


def sample(index, value):
    sid, seed = f"draw-{index}", 1000 + index
    turn = prepared(sid, seed)
    raw = json.dumps({key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")} |
        {"answer": {"value": value}}).encode()
    return dict(sample_id=sid, seed=seed, raw_reply_base64=base64.b64encode(raw).decode(),
        raw_reply_sha256=sha256(raw).hexdigest(), arm_claimed_success=True)


def first(_case, answer):
    return answer["value"] == 17 + 29, "fixture arithmetic"


def second(_case, answer):
    return answer["value"] - 29 == 17, "fixture inverse arithmetic"


JUDGES = (("fixture-addition", first), ("fixture-subtraction", second))


def score(rows, **kw):
    return rescore_samples(rows, prepare_turn=prepared, judges=JUDGES,
        judge_packet_sha256="a" * 64, **kw)


def test_exact_estimator_retains_duplicate_draws_and_independently_rescores_every_sample():
    rows = [sample(i, value) for i, value in enumerate((46, 45, 45, 46))]
    result = score(rows)
    assert result["n"] == 4 and result["c"] == 2 and result["distinct_answers"] == 2
    assert result["coverage"] == {"1": "1/2", "2": "5/6", "3": "1", "4": "1"}
    assert [row["sample"] for row in result["samples"]] == rows
    assert result["provider_calls"] == 0
    assert score(json.loads(json.dumps(rows))) == result
    assert coverage_at_k(4, 0, 2) == 0 and coverage_at_k(4, 4, 2) == 1


@pytest.mark.parametrize("args", [(0, 0, 1), (4, 5, 2), (4, 2, 5), (True, 1, 1), (4, -1, 2)])
def test_estimator_refuses_invalid_or_coerced_counts(args):
    with pytest.raises(ValueError, match="INVALID_SAMPLE_COUNTS"):
        coverage_at_k(*args)


def test_wrong_case_raw_mutation_and_exact_restore_are_nonvacuous():
    rows = [sample(0, 46), sample(1, 46)]
    assert score(rows)["c"] == 2
    original = deepcopy(rows)
    raw = json.loads(base64.b64decode(rows[0]["raw_reply_base64"]))
    raw["input_sha256"] = "0" * 64
    encoded = json.dumps(raw).encode()
    rows[0].update(raw_reply_base64=base64.b64encode(encoded).decode(), raw_reply_sha256=sha256(encoded).hexdigest())
    assert score(rows)["c"] == 1
    assert score(original)["c"] == 2
    rows[0]["raw_reply_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="RAW_CUSTODY_MISMATCH"):
        score(rows)


@pytest.mark.parametrize("fault", ["seed", "id", "judge", "case"])
def test_independence_checker_presence_and_matched_case_guards(fault):
    rows = [sample(0, 46), sample(1, 46)]
    prepare, judges = prepared, JUDGES
    if fault == "seed":
        rows[1]["seed"] = rows[0]["seed"]
    elif fault == "id":
        rows[1]["sample_id"] = rows[0]["sample_id"]
    elif fault == "judge":
        judges = (("one", first), ("two", first))
    else:
        def prepare(sid, seed):
            turn = prepared(sid, seed)
            if seed == 1001:
                return prepare_task_turn(system="other task", user="Find 0.", task_id="fixture-other",
                    attempt_id=sid, answer_schema=turn.task.answer_schema, checker_id=turn.checker_id)
            return turn
    with pytest.raises(ValueError):
        rescore_samples(rows, prepare_turn=prepare, judges=judges, judge_packet_sha256="a" * 64)


def test_both_judges_must_approve_even_when_arm_claims_success():
    result = rescore_samples([sample(0, 46)], prepare_turn=prepared,
        judges=(("first", first), ("mutated-second", lambda *_: (False, "mutation"))),
        judge_packet_sha256="a" * 64)
    assert result["c"] == 0
    assert score([sample(0, 46)])["c"] == 1


def test_ladder_pins_original_routes_and_drops_missing_rung_without_replacement():
    route = dict(model_id="Qwen/Qwen2.5-0.5B-Instruct", provider="local",
        total_parameters=500_000_000, allow_fallbacks=False)
    result = pin_ladder({"0.5B": route}, registry_sha256="c" * 64)
    assert result["rungs"][0]["status"] == "PINNED_NOT_PROBED"
    assert all(row["status"] == "DROPPED" for row in result["rungs"][1:])
    for patch in ({"model_id": "Qwen/Qwen2.5-72B"}, {"total_parameters": 72_000_000_000},
                  {"allow_fallbacks": True}, {"total_parameters": True}):
        with pytest.raises(ValueError, match="ROUTE_NOT_ORIGINAL_PIN"):
            pin_ladder({"0.5B": route | patch}, registry_sha256="c" * 64)


@pytest.mark.parametrize("protocol", ["C009", "C010"])
def test_original_anchor_missing_sources_refuse_instead_of_replacing_tasks(protocol, tmp_path):
    paths, hashes = {}, {}
    for anchor in ANCHORS[protocol]:
        path = tmp_path / (anchor + ".md")
        path.write_text("literal authoritative fixture " + anchor)
        paths[anchor], hashes[anchor] = path, sha256(path.read_bytes()).hexdigest()
    assert bind_original_anchors(protocol, paths, expected_sha256=hashes)["protocol"] == protocol
    original = paths["C061"].read_bytes()
    paths["C061"].unlink()
    with pytest.raises(ValueError, match="SOURCE_UNAVAILABLE:C061"):
        bind_original_anchors(protocol, paths, expected_sha256=hashes)
    paths["C061"].write_bytes(original)
    assert bind_original_anchors(protocol, paths, expected_sha256=hashes)["protocol"] == protocol
