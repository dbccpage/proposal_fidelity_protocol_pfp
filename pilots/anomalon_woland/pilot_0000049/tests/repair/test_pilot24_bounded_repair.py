import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import types

import pytest
from pydantic import ValidationError
import yaml

SOURCE = Path(__file__).resolve().parents[2] / "run.py"
SPEC = importlib.util.spec_from_file_location("pilot24_under_test", SOURCE)
m = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = m
SPEC.loader.exec_module(m)


def answer(value=42, task="addition"):
    return json.dumps({"kind": "answer", "task_id": task, "value": value})


def job(responses, limit=3):
    value = m.default_job()
    value.update(responses=responses, max_attempts=limit)
    return value


def oracle(mod):
    assert mod.replay(job([answer(41)])).status == "EXHAUSTED"
    assert mod.replay(job([answer(task="other")])).status == "EXHAUSTED"
    assert mod.replay(job(['{"kind":"abstain","task_id":"addition","reason":"unknown"}'])).status == "EXHAUSTED"
    stopped = mod.replay(job([answer(41), answer()], 1))
    assert stopped.status == "EXHAUSTED" and stopped.mock_calls == 1
    accepted = mod.replay(job([answer(), answer(0)]))
    assert accepted.status == "ACCEPTED" and accepted.mock_calls == 1


def test_corrected_reply_and_known_answer():
    result = m.replay(m.default_job())
    assert result.answer == 42 and result.mock_calls == 2
    assert [row.outcome for row in result.attempts] == ["WRONG_VALUE", "ACCEPTED"]
    assert result.provider_calls == result.cost_microusd == 0
    assert result.stop_reason == "correct_answer"
    oracle(m)


@pytest.mark.parametrize("left,right,expected", [(-1000, -1000, -2000), (1000, 1000, 2000), (-9, 9, 0)])
def test_signed_boundaries(left, right, expected):
    value = job([answer(expected)])
    value["task"].update(left=left, right=right)
    assert m.replay(value).answer == expected


@pytest.mark.parametrize("raw", ['not json', '[]', '{}', 'null', '{"kind":"unknown"}', answer(True), answer(42.0),
                                 answer("42"), '{"kind":"answer","task_id":"addition","value":42,"extra":0}',
                                 '{"kind":"answer","task_id":"addition","value":0,"value":42}',
                                 '{"kind":"answer","task_id":"addition","value":NaN}'],
                         ids=["syntax", "array", "empty", "null", "variant", "bool", "float", "string", "extra", "duplicate", "nan"])
def test_malformed_can_be_followed_by_correction(raw):
    result = m.replay(job([raw, answer()], 2))
    assert result.status == "ACCEPTED" and result.mock_calls == 2
    assert result.attempts[0].outcome == "MALFORMED" and result.attempts[0].raw == raw
    assert result.attempts[0].detail


def test_abstention_wrong_task_limit_and_sequence_end():
    abstain = '{"kind":"abstain","task_id":"addition","reason":"unknown"}'
    result = m.replay(job([answer(task="other"), abstain, answer(0), answer()]))
    assert [row.outcome for row in result.attempts] == ["WRONG_TASK", "ABSTAINED", "WRONG_VALUE"]
    assert result.status == "EXHAUSTED" and result.answer is None and result.stop_reason == "attempt_limit"
    assert result.mock_calls == 3
    empty = m.replay(job([]))
    assert empty.stop_reason == "sequence_end" and empty.mock_calls == 0
    short = m.replay(job([abstain]))
    assert short.stop_reason == "sequence_end" and short.answer is None


def test_tail_is_not_parsed_and_input_is_not_changed(monkeypatch):
    value = job([answer(), "not evaluated"], 1)
    before = json.dumps(value)
    called = []
    original = m.parse
    def counted(raw):
        called.append(raw)
        return original(raw)
    monkeypatch.setattr(m, "parse", counted)
    result = m.replay(value)
    assert called == [answer()] and json.dumps(value) == before
    value["task"]["left"] = 0
    value["responses"][0] = "changed"
    assert result.task.left == 19 and result.attempts[0].raw == answer()


@pytest.mark.parametrize("field,value", [("max_attempts", 0), ("max_attempts", 4), ("max_attempts", True),
                                         ("responses", [answer()] * 5), ("responses", [None]), ("responses", ["x" * 2049]),
                                         ("responses", ['\ud800']), ("unknown", 1)],
                         ids=["low", "high", "bool", "sequence", "null-frame", "long-frame", "invalid-unicode", "extra"])
def test_job_refusals(field, value):
    payload = m.default_job()
    payload[field] = value
    with pytest.raises(ValidationError):
        m.replay(payload)


@pytest.mark.parametrize("field,value", [("left", True), ("right", 1001), ("left", -1001), ("left", "19"),
                                         ("operation", "multiply"), ("task_id", "bad id"), ("unknown", 0)])
def test_task_refusals(field, value):
    payload = m.default_job()
    payload["task"][field] = value
    with pytest.raises(ValidationError):
        m.replay(payload)


def test_examples_and_result_twins():
    root = SOURCE.parent / "examples"
    value = json.loads((root / "corrected.json").read_bytes())
    assert value == yaml.safe_load((root / "corrected.yaml").read_bytes())
    result = m.replay(value)
    assert m.Result.model_validate(yaml.safe_load(yaml.safe_dump(result.model_dump()))) == result
    with pytest.raises(ValidationError):
        m.Result.model_validate(dict(result.model_dump(), provider_calls=True))


@pytest.mark.parametrize("kind,expected", [("json", 0), ("yaml", 0), ("exhausted", 1), ("syntax", 2),
                                         ("missing", 2), ("utf8", 2), ("large", 2)])
def test_main(kind, expected, tmp_path, capsys):
    args = []
    if kind == "yaml":
        args = ["--yaml"]
    elif kind != "json":
        path = tmp_path / "input.json"
        if kind != "missing":
            raw = {"exhausted": json.dumps(job([answer(0)], 1)).encode(), "syntax": b"!", "utf8": b"\xff", "large": b" " * 32769}[kind]
            path.write_bytes(raw)
        args = ["--input", str(path)]
    assert m.main(args) == expected
    record = yaml.safe_load(capsys.readouterr().out)
    assert record["status"] == ("ACCEPTED" if expected == 0 else "EXHAUSTED" if expected == 1 else "INVALID")


def test_actual_cli_json_and_yaml():
    for args in ([], ["--yaml"]):
        result = subprocess.run([sys.executable, "-B", str(SOURCE), *args], capture_output=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), check=False)
        assert result.returncode == 0 and not result.stderr
        assert yaml.safe_load(result.stdout)["answer"] == 42


@pytest.mark.parametrize("old,new", [
    ("elif reply.value != expected:", "elif False:"),
    ("if reply.task_id != job.task.task_id:", "if False:"),
    ('outcome = "ABSTAINED"', 'outcome = "ACCEPTED"'),
    ("raw_replies[:job.max_attempts]", "raw_replies"),
    ('if outcome == "ACCEPTED":', "if False:"),
], ids=["value-gate", "task-gate", "abstention", "attempt-limit", "stop-on-success"])
def test_compiled_semantic_mutants(old, new):
    source = SOURCE.read_text(encoding="utf-8")
    assert source.count(old) == 1
    mutant = types.ModuleType("pilot24_mutant")
    sys.modules[mutant.__name__] = mutant
    exec(compile(source.replace(old, new), "pilot24_mutant.py", "exec"), mutant.__dict__)
    with pytest.raises(AssertionError):
        oracle(mutant)


def test_script_entry(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(SOURCE)])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(SOURCE), run_name="__main__")
    assert caught.value.code == 0 and isinstance(json.loads(capsys.readouterr().out), dict)


def test_lone_surrogate_text_is_rejected_before_json_parsing():
    with pytest.raises(ValueError, match="not encodable as UTF-8"):
        m.parse('"\ud800"')
    assert m.require_utf8("ok") == "ok"
    assert isinstance(m.replay(m.default_job()).attempts, tuple)
