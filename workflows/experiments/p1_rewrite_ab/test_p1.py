"""P1 runner and grader tests. AuthorityEffect: None. No network.

    python -m pytest workflows/experiments/p1_rewrite_ab/test_p1.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import run  # noqa: E402

TASKS = run.load_tasks(HERE / "tasks.jsonl")
BY_ID = {t["task_id"]: t for t in TASKS}


def reply(content: str, finish: str = "stop", t_in: int = 100, t_out: int = 200) -> bytes:
    return json.dumps({"choices": [{"message": {"content": content}, "finish_reason": finish}],
                       "usage": {"prompt_tokens": t_in, "completion_tokens": t_out}}).encode()


def result(content: str, status: int = 200, finish: str = "stop") -> dict:
    return {"status": status, "error": None, "reply": reply(content, finish).decode()}


def go(tmp_path, send, **kw):
    opts = dict(model=run.MODEL, effort="low", p_in=Fraction(1, 4), p_out=Fraction(2),
                cap_micro=750_000)
    opts.update(kw)
    return run.run(TASKS, tmp_path / "ledger.jsonl", send, **opts)


def test_task_file_is_the_frozen_kit():
    assert run.sha((HERE / "tasks.jsonl").read_bytes()) == (
        "452c1b2f5c2369ffa7c8dd5e6995bd7ce5d610c5079dba809f069ab1c8fb1fe0")
    assert sum(len(t["arms"]) for t in TASKS) == 110


def test_sum_grades():
    s = BY_ID["S00"]
    assert grade.grade_result(s, result(json.dumps(s["expected"]))) == "CORRECT"
    assert grade.grade_result(s, result(json.dumps({"total": s["pulled_total"]}))) == "PULLED"
    assert grade.grade_result(s, result('{"total": "7"}')) == "WRONG"
    for bad in ('```json\n{"total": "7"}\n```', '{"total": 7}', '{"total": "7.0"}',
                '{"total": "07"}', '{"total": "-0"}', '{"total": "7", "x": 1}', '[1]', ''):
        assert grade.grade_result(s, result(bad)) == "MALFORMED", bad
    assert grade.grade_result(s, result(json.dumps(s["expected"]), finish="length")) == "TRUNCATED"
    assert grade.grade_result(s, result("", status=400)) == "NO_REPLY"


def test_mean_pull_is_caught_when_rounded():
    mean = next(t for t in TASKS if t["family"] == "S" and "/" in t["pulled_total"])
    pulled = Fraction(mean["pulled_total"])
    near = str(round(pulled))
    assert grade.grade_result(mean, result(json.dumps({"total": near}))) == "PULLED"


def test_hodge_reference_grades_correct_and_one_entry_off_is_wrong():
    h = BY_ID["H00"]
    assert grade.grade_result(h, result(json.dumps(h["expected"]))) == "CORRECT"
    off = dict(h["expected"], harmonic_norm_squared="0")
    assert grade.grade_result(h, result(json.dumps(off))) == "WRONG"
    unreduced = dict(h["expected"], potential=["0/1"] + h["expected"]["potential"][1:])
    assert grade.grade_result(h, result(json.dumps(unreduced))) == "MALFORMED"
    floaty = dict(h["expected"], b0=1.0)
    assert grade.grade_result(h, result(json.dumps(floaty))) == "MALFORMED"
    stringy = dict(h["expected"], b0="1")
    assert grade.grade_result(h, result(json.dumps(stringy))) == "MALFORMED"


def test_sign_test_is_exact():
    assert grade.sign_test(0, 0) == 1
    assert grade.sign_test(5, 0) == Fraction(1, 16)
    assert grade.sign_test(3, 3) == 1
    assert grade.sign_test(10, 1) == Fraction(2 * 12, 2**11)


def test_dry_run_is_all_correct_and_resume_sends_nothing(tmp_path):
    send = run.dry_sender(BY_ID)
    first = go(tmp_path, send)
    assert first["sent"] == 110 and first["stop"] is None
    again = go(tmp_path, send)
    assert again["sent"] == 0
    report = grade.grade_all(TASKS, run.load_ledger(tmp_path / "ledger.jsonl"))
    assert all(row["CORRECT"] == sum(row.values()) for row in report["arms"].values())
    assert all(p["a_only_correct"] == p["b_only_correct"] == 0 for p in report["pairs"])


def test_interrupted_call_is_held_not_resent(tmp_path):
    calls = []

    def boom(body, task_id):
        calls.append(task_id)
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        go(tmp_path, boom)
    ledger = run.load_ledger(tmp_path / "ledger.jsonl")
    assert [r["kind"] for r in ledger] == ["intent"]
    seen = []
    out = go(tmp_path, lambda body, tid: (seen.append(tid), (200, reply('{"total": "1"}')))[1],
             limit=1)
    assert out["held"] == ["S00|fenced"]
    assert seen == ["S00"]  # the next arm, not the held one
    report = grade.grade_all(TASKS, run.load_ledger(tmp_path / "ledger.jsonl"))
    assert report["grades"]["S00|fenced"] == "NO_REPLY"


def test_http_error_is_recorded_once_and_costed_at_its_bound(tmp_path):
    calls = []

    def bad(body, task_id):
        calls.append(task_id)
        return 400, b'{"error": {"message": "x"}}'

    out = go(tmp_path, bad, limit=2)
    assert out["sent"] == 2 and len(calls) == 2
    results = [r for r in run.load_ledger(tmp_path / "ledger.jsonl") if r["kind"] == "result"]
    assert all(r["cost_source"] == "bound" and r["cost_nano_usd"] > 0 for r in results)


def test_cost_is_integer_nano_usd_from_usage(tmp_path):
    go(tmp_path, lambda b, t: (200, reply('{"total": "1"}', t_in=1000, t_out=3)), limit=1)
    r = [r for r in run.load_ledger(tmp_path / "ledger.jsonl") if r["kind"] == "result"][0]
    assert r["cost_nano_usd"] == 1000 * 250 + 3 * 2000 and r["cost_source"] == "usage"


def test_cap_stops_before_a_call_that_could_cross_it(tmp_path):
    sent = []
    out = go(tmp_path, lambda b, t: (sent.append(t), (200, reply("{}")))[1], cap_micro=1)
    assert out["stop"] == "OVER_CAP" and sent == []


def test_request_has_one_content_type_and_the_model():
    h = run.headers("k")
    assert [k.lower() for k in h].count("content-type") == 1
    body = run.request_body(BY_ID["H00"], "wire_qed", run.MODEL, "low")
    assert body["model"] == run.MODEL and body["reasoning_effort"] == "low"
    assert body["messages"][0]["content"] == BY_ID["H00"]["system"]


def test_decimal_price_is_refused():
    with pytest.raises(SystemExit):
        run.price("0.25")


def test_key_is_read_only_from_its_variable(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTHER=1\nOPENAI_API_KEY=\"sk-test\"\n", encoding="utf-8")
    assert run.read_key(env) == "sk-test"
    env.write_text("OPENAI_API_KEY=\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        run.read_key(env)


import tier_s  # noqa: E402

TIER_S = run.load_tasks(HERE / "tasks_tier_s.jsonl")


def _decode_int(node):
    return -int(node[1]) if isinstance(node, list) else int(node)


def test_tier_s_arm_is_strict_gamma38_and_carries_the_instance():
    assert run.sha((HERE / "tasks_tier_s.jsonl").read_bytes()) == (
        "52a1e9bf37bfa80a0f41d14e4f41df573e30ec183ab229b43e27cee05ff7eca4")
    for row in TIER_S:
        text = row["arms"]["tier_s_qed"]
        assert set(text) <= tier_s.GAMMA38, row["task_id"]
        tree = tier_s.parse_all(text)
        heads = {kid[0]: kid for kid in tree[1:]}
        inst = BY_ID[row["task_id"]]["instance"]
        assert [_decode_int(x) for x in heads["flow"][1:]] == inst["flow"]
        assert [[int(e[1]), int(e[2])] for e in heads["edges"][1:]] == inst["edges"]
        assert tree[-1] == ["terminal", ["qed", "exact"]]
        assert row["expected"] == BY_ID[row["task_id"]]["expected"]


def test_tier_s_parser_refuses_malformed_packets():
    for bad in ("<a", "<<a>", "<a b>", "a", "<a><b>", "<A>", "<<a>,<b>>"):
        with pytest.raises((ValueError, IndexError)):
            tier_s.parse_all(bad)
    assert tier_s.parse_all("<<a><<neg><2>>>") == ["a", ["neg", "2"]]


def test_merge_adds_the_tier_s_arm_and_its_pairs(tmp_path):
    merged = grade.merge_tasks([TASKS, TIER_S])
    h00 = next(t for t in merged if t["task_id"] == "H00")
    assert set(h00["arms"]) == {"prose", "wire", "wire_qed", "tier_s_qed"}
    run.run(TIER_S, tmp_path / "s.jsonl", run.dry_sender({t["task_id"]: t for t in TIER_S}),
            model=run.MODEL, effort="low", p_in=Fraction(1, 4), p_out=Fraction(2), cap_micro=750_000)
    report = grade.grade_all(merged, run.load_ledger(tmp_path / "s.jsonl"))
    assert report["arms"]["H|tier_s_qed"]["CORRECT"] == 10
    assert report["arms"]["H|wire_qed"]["NOT_RUN"] == 10
    assert not any(p["a"] == "tier_s_qed" for p in report["pairs"])  # no paired tasks yet
    with pytest.raises(SystemExit):
        grade.merge_tasks([TASKS, TASKS])


HODGE_V2 = run.load_tasks(HERE / "tasks_hodge_v2.jsonl")


def test_hodge_v2_fixes_only_the_contract_sentence():
    assert run.sha((HERE / "tasks_hodge_v2.jsonl").read_bytes()) == (
        "f8b86bb3034de7a62e267bc5abc242d5aa9b035d3daed83af3b4faa38a1080df")
    assert len(HODGE_V2) == 10 and sum(len(t["arms"]) for t in HODGE_V2) == 40
    v1s = {t["task_id"]: t for t in TIER_S}
    for t in HODGE_V2:
        old = BY_ID[t["task_id"]]
        assert t["expected"] == old["expected"] and t["instance"] == old["instance"]
        assert {a: t["arms"][a] for a in old["arms"]} == old["arms"]
        assert t["arms"]["tier_s_qed"] == v1s[t["task_id"]]["arms"]["tier_s_qed"]
        assert t["system"] != old["system"] and "JSON integers, not strings" in t["system"]


def test_hodge_v2_dry_run_grades_all_correct_and_int_strings_stay_malformed(tmp_path):
    run.run(HODGE_V2, tmp_path / "v2.jsonl", run.dry_sender({t["task_id"]: t for t in HODGE_V2}),
            model=run.MODEL, effort="low", p_in=Fraction(1, 4), p_out=Fraction(2), cap_micro=750_000)
    report = grade.grade_all(HODGE_V2, run.load_ledger(tmp_path / "v2.jsonl"))
    assert all(report["arms"][f"H|{a}"]["CORRECT"] == 10 for a in ("prose", "wire", "wire_qed", "tier_s_qed"))
    assert {(p["a"], p["b"]) for p in report["pairs"]} >= {("tier_s_qed", "wire_qed"), ("wire_qed", "prose")}
    h = HODGE_V2[0]
    assert grade.grade_result(h, result(json.dumps(dict(h["expected"], b0="1")))) == "MALFORMED"
