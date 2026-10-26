"""Tests for the PREREG-DA-001 Stage B harness and analysis. No network. AuthorityEffect: None."""

from __future__ import annotations

import copy
import json
import random
from fractions import Fraction

import numpy as np
import pytest

from omega_engine_pfp.use_cases.detector_adequacy import (
    detectors,
    stage_b,
    stage_b_analysis,
    traces,
)


def _item(seed=3):
    return traces.make_item(random.Random(seed), 0)


def _response(text, status=200):
    payload = {"type": "message", "stop_reason": "end_turn", "content": [{"type": "text", "text": text}],
               "usage": {"input_tokens": 700, "output_tokens": 400}}
    return status, json.dumps(payload).encode("utf-8")


def _score(item, steps_or_text):
    text = steps_or_text if isinstance(steps_or_text, str) else json.dumps({"steps": steps_or_text})
    status, raw = _response(text)
    return stage_b.score(item, 0, status, raw, stage_b.request_body(item))


def test_request_sends_no_sampling_parameter_and_disables_thinking():
    body = json.loads(stage_b.request_body(_item()))
    assert body["model"] == stage_b.MODEL
    assert body["thinking"] == {"type": "disabled"}
    assert "temperature" not in body and "top_p" not in body and "top_k" not in body


def test_worst_case_plan_fits_under_the_ceiling_and_the_cap():
    items = stage_b.make_items("0" * 40, stage_b.N_ITEMS)
    plan = sum((stage_b.worst_case_usd(stage_b.request_body(i)) * stage_b.CALLS_PER_ITEM for i in items),
               Fraction(0))
    assert plan <= stage_b.PLAN_CEILING_USD < stage_b.CAP_USD


def test_budget_refuses_a_call_that_could_cross_the_cap():
    budget = stage_b.Budget(Fraction(1, 1000))
    assert budget.reserve(Fraction(6, 10000))
    assert not budget.reserve(Fraction(6, 10000))
    budget.settle(Fraction(6, 10000), Fraction(1, 10000))
    assert budget.reserve(Fraction(6, 10000))
    assert budget.refused == 1


def test_items_are_fixed_by_the_lock_commit():
    assert stage_b.make_items("abc", 5) == stage_b.make_items("abc", 5)
    assert stage_b.make_items("abc", 5) != stage_b.make_items("abd", 5)


def test_extract_object_reads_bare_fenced_and_refuses_junk():
    assert stage_b.extract_object('{"steps": []}') == ({"steps": []}, True)
    assert stage_b.extract_object('```json\n{"steps": []}\n```') == ({"steps": []}, False)
    assert stage_b.extract_object("no json here") == (None, False)


def test_clean_reply_is_valid_green_and_correct():
    item = _item()
    record = _score(item, traces.clean_trace(item)["steps"])
    assert record["schema_valid"] and record["struct_share"] == "1"
    assert record["d4"]["status"] == detectors.GREEN
    assert record["failure"] is False


def test_misread_solution_is_red_and_a_failure():
    item = _item()
    record = _score(item, traces.m1_known_wrong(traces.clean_trace(item), random.Random(1))["steps"])
    assert record["d4"]["status"] == detectors.RED
    assert record["failure"] is True


def test_upstream_rref_error_is_invisible_to_the_read_relation():
    item = _item()
    record = _score(item, traces.m4_mutated_tool_output(traces.clean_trace(item), random.Random(1))["steps"])
    assert record["d4"]["status"] == detectors.GREEN
    assert record["failure"] is True


def test_junk_reply_is_noncertifying_and_a_failure():
    record = _score(_item(), "I cannot do that.")
    assert record["d4"]["status"] == detectors.NONCERTIFYING and record["d4"]["refusal"] == "NO_TRACE"
    assert record["failure"] is True and record["schema_valid"] is False


def test_broken_citation_lowers_the_structure_share():
    item = _item()
    steps = copy.deepcopy(traces.clean_trace(item)["steps"])
    steps[3]["cites"] = ["s2"]
    record = _score(item, steps)
    assert record["struct_share"] == "4/5" and record["schema_valid"] is False


def test_predictor_does_not_read_the_posed_item():
    item = _item()
    steps = traces.m1_known_wrong(traces.clean_trace(item), random.Random(1))["steps"]
    drifted = dict(item, A=[["1"] * len(item["A"])] * len(item["A"]))
    assert _score(item, steps)["d4"] == _score(drifted, steps)["d4"]


def test_http_error_is_a_transport_error_not_an_outcome():
    item = _item()
    record = stage_b.score(item, 0, 529, b'{"type":"error"}', stage_b.request_body(item))
    assert record["transport_error"] is True and "failure" not in record


def test_read_env_file_reads_named_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTHER=1\nexport ANTHROPIC_API_KEY='sk-test'\n", encoding="utf-8")
    assert stage_b.read_env_file(env, "ANTHROPIC_API_KEY") == "sk-test"
    assert stage_b.read_env_file(env, "MISSING") == ""


def test_lock_refuses_an_unknown_commit():
    problems = stage_b.verify_lock(detectors.repo_root(), "0" * 40)
    assert problems and all("MISMATCH" in p for p in problems)


def test_auc_matches_hand_values_with_ties():
    y = np.array([1, 1, 0, 0])
    assert stage_b_analysis.auc(np.array([4.0, 3.0, 2.0, 1.0]), y) == 1.0
    assert stage_b_analysis.auc(np.array([1.0, 1.0, 1.0, 1.0]), y) == 0.5
    assert stage_b_analysis.auc(np.array([3.0, 1.0, 2.0, 0.0]), y) == 0.75


@pytest.mark.parametrize("point, low, high, events, expected", [
    (0.01, -0.02, 0.04, 100, "DROPPED"),
    (0.08, 0.02, 0.14, 100, "SUPPORTED_AT_PILOT_SCALE"),
    (0.04, 0.01, 0.07, 100, "BudgetUnknown:INCONCLUSIVE"),
    (0.20, 0.10, 0.30, 10, "BudgetUnknown:TOO_FEW_EVENTS"),
])
def test_decision_table(point, low, high, events, expected):
    assert stage_b_analysis.decide(point, low, high, events, 500) == expected


def test_fixture_run_end_to_end_detects_the_planted_read_defects(monkeypatch):
    monkeypatch.setattr(stage_b_analysis, "BOOTSTRAP", 200)
    send = stage_b.fixture_transport(5)
    budget = stage_b.Budget(stage_b.CAP_USD)
    items = stage_b.make_items("fixture", 120)
    records = [stage_b._one_call(send, budget, it, k)[0] for it in items for k in range(2)]
    summary = stage_b_analysis.analyse(records, 11)
    assert summary["n_primary"] == 120 and summary["oscillation"]["pairs"] == 120
    assert summary["d4_by_outcome"]["red"]["success"] == 0
    assert summary["delta_auc"] > 0
