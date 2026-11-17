"""H1 kit tests. AuthorityEffect: None. No network. Needs jsonschema and pyyaml:

    uv run --no-project --with pytest --with jsonschema --with pyyaml python -m pytest experiments/p1_rewrite_ab/test_h1.py
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

import jsonschema
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import grade  # noqa: E402
import h1  # noqa: E402
import run  # noqa: E402

H1 = run.load_tasks(HERE / "tasks_h1.jsonl")
P1 = {t["task_id"]: t for t in run.load_tasks(HERE / "tasks.jsonl")}
SCHEMA = yaml.safe_load((ROOT / "pfp/infrastructure/yaml/schemas/llm_turn_v1.schema.yaml").read_text(encoding="utf-8"))


def result(task: dict, arm: str, content: str) -> dict:
    reply = {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
    return {"status": 200, "error": None, "arm": arm, "reply": json.dumps(reply)}


def test_kit_is_frozen_and_rebuilds():
    body = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in h1.build())
    assert (HERE / "tasks_h1.jsonl").read_bytes() == body.encode("utf-8")
    assert run.sha(body.encode()) == "482edbca1a16286d1c2c9666b6d9df9088cb8923d461859c64f42fbae85ee220"
    assert len(H1) == 30 and sum(len(t["arms"]) for t in H1) == 60


def test_both_arms_carry_the_same_task_text_and_the_typed_turn_is_schema_valid():
    for t in H1:
        text = P1[t["task_id"]]["arms"]["prose"]
        assert t["arms"]["orchestrator"] == text
        turn = json.loads(t["arms"]["typed"])
        jsonschema.validate(turn, SCHEMA)
        assert turn["objective"] == text and turn["content_sha256"] == h1.sha(text)
        assert turn["task_id"] == t["task_id"] and turn["authority_effect"] == "None"
        assert t["expected"] == P1[t["task_id"]]["expected"]


def test_dry_run_grades_all_correct_with_the_wrapper(tmp_path):
    run.run(H1, tmp_path / "l.jsonl", run.dry_sender({t["task_id"]: t for t in H1}),
            model=run.MODEL, effort="low", p_in=Fraction(1, 4), p_out=Fraction(2), cap_micro=750_000)
    report = grade.grade_all(H1, run.load_ledger(tmp_path / "l.jsonl"))
    assert all(row["CORRECT"] == 30 for row in [
        {g: report["arms"][f"S|{a}"][g] + report["arms"][f"H|{a}"][g] for g in grade.GRADES}
        for a in ("orchestrator", "typed")])
    assert {(p["family"], p["a"], p["b"]) for p in report["pairs"]} == {
        ("S", "typed", "orchestrator"), ("H", "typed", "orchestrator")}


def test_each_arm_sends_its_own_system_message():
    t = H1[0]
    typed = run.request_body(t, "typed", run.MODEL, "low")["messages"][0]["content"]
    orch = run.request_body(t, "orchestrator", run.MODEL, "low")["messages"][0]["content"]
    assert typed.startswith("You are a typed turn handler") and orch.startswith("You are SolverAgent")


def test_typed_wrapper_faults_are_malformed_and_a_bare_answer_on_orchestrator_is_graded():
    s = next(t for t in H1 if t["family"] == "S")
    good = {"task_id": s["task_id"], "CANDIDATE": s["expected"], "AUTHORITY_EFFECT": "None"}
    assert grade.grade_result(s, result(s, "typed", json.dumps(good))) == "CORRECT"
    pulled = dict(good, CANDIDATE={"total": s["pulled_total"]})
    assert grade.grade_result(s, result(s, "typed", json.dumps(pulled))) == "PULLED"
    for bad in (dict(good, task_id="S99"), dict(good, AUTHORITY_EFFECT="Admitted"),
                {k: v for k, v in good.items() if k != "AUTHORITY_EFFECT"}, dict(good, extra=1),
                dict(good, CANDIDATE="1")):
        assert grade.grade_result(s, result(s, "typed", json.dumps(bad))) == "MALFORMED", bad
    assert grade.grade_result(s, result(s, "typed", json.dumps(s["expected"]))) == "MALFORMED"
    assert grade.grade_result(s, result(s, "orchestrator", json.dumps(s["expected"]))) == "CORRECT"
