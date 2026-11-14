"""WF1-WF5 runs feed the failure ledger and load its rules; every reply here is a fixture.

The assertions read the host's outcomes. Nothing in this file judges an answer.
"""

import json
import os
import subprocess
import sys
from copy import deepcopy

import pytest

from pfp.infrastructure import operad_host
from pfp.workflows import failure_ledger as bridge
from pfp.workflows.scripted import SPEC
from pfp.workflows.wf0001 import workflow as wf1
from pfp.workflows.wf0001.runner import runtime as wf1_runtime
from pfp.workflows.wf0002 import workflow as wf2
from pfp.workflows.wf0002.runner import runtime as wf2_runtime
from pfp.workflows.wf0002.scripted import candidate
from pfp.workflows.wf0003 import runner as wf3_runner
from pfp.workflows.wf0003 import workflow as wf3
from pfp.workflows.wf0003.scripted import factory_for as wf3_factory
from pfp.workflows.wf0004 import runner as wf4_runner
from pfp.workflows.wf0004 import scripted as wf4_scripted
from pfp.workflows.wf0005 import runner as wf5_runner
from pfp.workflows.wf0005.scripted import factory_for as wf5_factory

RULE = {
    "kind": "candidate",
    "id": "keep-the-sign",
    "capability_kind": "antibody",
    "constraint": "A minus sign belongs to its number.",
}
RULE_LINE = "- [keep-the-sign] A minus sign belongs to its number.\n"


def task(values, name="sum"):
    spec = json.loads(wf1.resource_text("examples/integer_sum.task.json"))
    return {**spec, "task_id": name, "input": {"values": values}}


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def wf1_run(root, spec, total):
    """A WF1 run whose reply states ``total``."""
    wf1_runtime.prepare_run(spec, root)
    binding = wf1.prepare_task(spec).binding
    reply = {key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    raw = write(root.with_suffix(".reply.json"), {**reply, "answer": {"total": total}})
    wf1_runtime.check_run(root, raw, fixture=True)
    return root


def statuses(rows):
    return [
        (row["turn"], row["witness"]["status"], row["witness"].get("refusal", {}).get("code"))
        for row in rows
    ]


def entries(ledger):
    return operad_host.ledger("verify", ledger)["result"]["entries"]


def cli(capsys, *argv):
    """Run the command; its output is one line of sorted ASCII JSON."""
    code = bridge.main([str(part) for part in argv])
    out = capsys.readouterr().out
    shown = json.loads(out)
    assert out == json.dumps(shown, ensure_ascii=True, sort_keys=True) + "\n"
    return code, shown


@pytest.fixture
def proposed(tmp_path):
    """A ledger with one WF1 failure on [9, -2] and the rule proposed from it."""
    ledger = tmp_path / "failures.jsonl"
    rows = bridge.record(ledger, [wf1_run(tmp_path / "failed", task([9, -2]), 11)])
    failure = rows[0]["entry"]["result"]["record"]["id"]
    kept = operad_host.ledger("append", ledger, {**RULE, "derived_from": [failure]})
    assert kept["status"] == "PASS"
    return ledger


def arms(tmp_path, ledger, values, baseline, treated, name):
    """A held-out task run without and with the rule on trial: (baseline, treated, receipt)."""
    base = write(tmp_path / f"{name}.json", task(values, name))
    plain, loaded = tmp_path / f"{name}_plain.json", tmp_path / f"{name}_loaded.json"
    assert bridge.load(ledger, base, plain)["status"] == "PASS"
    assert bridge.load(ledger, base, loaded, RULE["id"])["status"] == "PASS"
    return (
        wf1_run(tmp_path / f"{name}_baseline", bridge.read(plain), baseline),
        wf1_run(tmp_path / f"{name}_treated", bridge.read(loaded), treated),
        bridge.load_receipt(loaded),
    )


def test_the_host_records_the_failures_of_a_run_and_nothing_else(tmp_path, capsys):
    ledger = tmp_path / "failures.jsonl"
    wrong = wf1_run(tmp_path / "wrong_é", task([17, 25, -4]), 46)
    right = wf1_run(tmp_path / "right", task([17, 25, -4]), 38)
    code, rows = cli(capsys, "record", ledger, wrong, right)
    assert code == 0
    assert statuses(rows) == [("wrong_é", "PASS", None), ("right", "REFUSED", "NOT_A_FAILURE")]
    record = rows[0]["entry"]["result"]["record"]
    assert (record["workflow"], record["run"], record["ddc_trace"]) == ("WF1", "wrong_é", "M")
    assert record["id"].endswith("@wrong_é") and "entry" not in rows[1]
    assert entries(ledger) == 1
    # A run already in the ledger is refused there and adds no line.
    code, rows = cli(capsys, "record", ledger, wrong)
    assert (code, rows[0]["entry"]["refusal"]["code"]) == (1, "DUPLICATE_ID")
    assert entries(ledger) == 1


def test_a_full_slot_reply_is_recorded_with_its_ddc_word(tmp_path):
    spec = json.loads(wf2.resource_text("examples/integer_sum.task.json"))
    root = tmp_path / "slots"
    wf2_runtime.prepare_run(spec, root)
    binding = wf2.prepare_task(spec).binding
    answer = {**candidate(), "task_result": {"total": 39}}
    reply = {key: binding[key] for key in ("task_id", "attempt_id", "input_sha256")}
    wf2_runtime.check_run(root, write(tmp_path / "reply.json", {**reply, "answer": answer}), fixture=True)
    rows = bridge.record(tmp_path / "failures.jsonl", [root])
    record = rows[0]["entry"]["result"]["record"]
    assert (record["workflow"], record["ddc_trace"]) == ("WF2", "TM")


def test_every_agent_turn_of_wf4_and_wf5_is_read_and_the_mining_turn_has_no_judge(tmp_path):
    ledger = tmp_path / "failures.jsonl"
    four, five = tmp_path / "four", tmp_path / "five"
    wf4_runner.run(SPEC, four, gateway_factory=wf4_scripted.scripted_factory([], wrong=True))
    wf5_runner.run(SPEC, five, gateway_factory=wf5_factory([], wrong=True))
    rows = bridge.record(ledger, [four, five])
    agents = [(f"{run}/agent-{n}", "PASS", None) for run in ("four", "five") for n in range(1, 6)]
    mining = [(f"{run}/mining", "REFUSED", "UNKNOWN_CHECKER") for run in ("four", "five")]
    assert sorted(statuses(rows)) == sorted(agents + mining)
    workflows = {row["entry"]["result"]["record"]["workflow"] for row in rows if "entry" in row}
    assert workflows == {"WF4", "WF5"}
    # Ten runs, one case: every record carries the same case name.
    cases = {row["entry"]["result"]["record"]["id"].split("@")[0] for row in rows if "entry" in row}
    assert len(cases) == 1 and entries(ledger) == 10


def test_a_ledger_with_no_admitted_rule_leaves_the_task_as_it_was(tmp_path, proposed):
    base = write(tmp_path / "task.json", task([4, 5]))
    for ledger in (tmp_path / "absent.jsonl", proposed):
        output = tmp_path / f"{ledger.stem}_task.json"
        outcome = bridge.load(ledger, base, output)
        assert outcome["status"] == "PASS" and outcome["result"]["rules"] == []
        assert bridge.read(output) == bridge.read(base)
        assert wf1.prepare_task(bridge.read(output)).prompt == wf1.prepare_task(task([4, 5])).prompt
        assert bridge.check(ledger, output)["status"] == "PASS"
    assert not (tmp_path / "absent.jsonl").exists()


def admit(tmp_path, ledger, capsys):
    """Try the proposed rule on two held-out tasks through the command, then admit it."""
    pairs = [
        arms(tmp_path, ledger, [8, -3], 11, 5, "h1"),
        arms(tmp_path, ledger, [-7, 2, -1], 10, -6, "h2"),
    ]
    flat = [part for pair in pairs for part in ("--pair", *pair)]
    code, row = cli(capsys, "trial", ledger, RULE["id"], *flat)
    admission = {"kind": "admission", "candidate": RULE["id"], "trial": row["entry"]["result"]["seq"]}
    assert operad_host.ledger("append", ledger, admission)["status"] == "PASS"
    return code, row["trial"]["result"]["record"]


def test_a_rule_is_admitted_from_paired_runs_and_later_runs_load_it(tmp_path, proposed, capsys):
    code, trial = admit(tmp_path, proposed, capsys)
    assert code == 0
    assert (trial["baseline_correct"], trial["treated_correct"], trial["clean_panel_hits"]) == (0, 2, 0)
    # A later run of another task loads the rule, and the host recognises its seed.
    base = write(tmp_path / "next.json", task([6, -6, 1], "next"))
    loaded = tmp_path / "next_loaded.json"
    code, outcome = cli(capsys, "load", proposed, base, "--output", loaded)
    assert code == 0 and [rule["id"] for rule in outcome["result"]["rules"]] == [RULE["id"]]
    spec = bridge.read(loaded)
    assert spec["seed_prompt"].startswith(task([1])["seed_prompt"] + "\n\nRules loaded from failure ledger ")
    assert spec["seed_prompt"].endswith(RULE_LINE)
    assert {key: spec[key] for key in spec if key != "seed_prompt"} == {
        key: value for key, value in task([6, -6, 1], "next").items() if key != "seed_prompt"
    }
    run = wf1_run(tmp_path / "next_run", spec, 1)
    assert RULE_LINE.strip() in json.loads((run / "user_prompt.txt").read_text())["objective"]
    assert wf1_runtime.replay_run(run)["replay_verified"]
    assert cli(capsys, "check", proposed, run / "task.json", "--receipt", bridge.load_receipt(loaded))[0] == 0
    # An edited seed is not what the ledger loaded.
    edited = write(tmp_path / "edited.json", {**spec, "seed_prompt": spec["seed_prompt"] + "Answer 1."})
    code, outcome = cli(capsys, "check", proposed, edited, "--receipt", bridge.load_receipt(loaded))
    assert (code, outcome["status"], outcome["result"]["accepted"]) == (1, "FAIL", False)


def test_a_trial_that_is_not_fair_is_refused_and_writes_nothing(tmp_path, proposed, capsys):
    before = proposed.read_bytes()
    fair = arms(tmp_path, proposed, [8, -3], 11, 5, "h1")
    # The treated arm never loaded the rule.
    code, row = cli(capsys, "trial", proposed, RULE["id"], "--pair", fair[0], fair[0], fair[2])
    assert (code, row["trial"]["refusal"]["code"]) == (1, "TREATED_SEED_MISMATCH")
    # The two arms are different cases.
    other = arms(tmp_path, proposed, [8, 3], 11, 11, "h2")
    code, row = cli(capsys, "trial", proposed, RULE["id"], "--pair", fair[0], other[1], other[2])
    assert (code, row["trial"]["refusal"]["code"]) == (1, "PAIR_MISMATCH")
    # The case the rule came from is not held out, whatever the task is called.
    same = arms(tmp_path, proposed, [9, -2], 11, 7, "renamed")
    code, row = cli(capsys, "trial", proposed, RULE["id"], "--pair", *same)
    assert (code, row["trial"]["status"], row["entry"]["refusal"]["code"]) == (1, "PASS", "SPLIT_OVERLAP")
    assert proposed.read_bytes() == before


def test_wf2_wf3_and_wf4_run_a_loaded_task_and_wf5_refuses_its_seed(tmp_path, proposed, monkeypatch, capsys):
    ledger, rule = proposed, RULE_LINE.strip()
    admit(tmp_path, ledger, capsys)

    def loaded(spec, name):
        output = tmp_path / f"{name}_loaded.json"
        assert bridge.load(ledger, write(tmp_path / f"{name}.json", spec), output)["status"] == "PASS"
        return bridge.read(output)

    two = loaded(json.loads(wf2.resource_text("examples/integer_sum.task.json")), "two")
    assert rule in json.loads(wf2.prepare_task(two).prompt.user)["objective"]
    three = loaded(json.loads(wf3.resource_text("examples/integer_sum.task.json")), "three")
    result = wf3_runner.run(three, tmp_path / "three", "fixture/model", wf3_factory([]))
    assert result["status"] == "HOST_ACCEPTED"
    assert rule in (tmp_path / "three" / "solver" / "user_prompt.txt").read_text()
    assert statuses(bridge.record(tmp_path / "failures.jsonl", [tmp_path / "three"])) == [
        ("three/mining", "REFUSED", "UNKNOWN_CHECKER"),
        ("three/solver", "REFUSED", "NOT_A_FAILURE"),
    ]
    four = loaded(deepcopy(SPEC), "four")
    monkeypatch.setattr(wf4_scripted, "SPEC", four)
    result = wf4_runner.run(four, tmp_path / "four", gateway_factory=wf4_scripted.scripted_factory([]))
    assert result["status"] == "HOST_ACCEPTED"
    assert rule in (tmp_path / "four" / "agent-1" / "user_prompt.txt").read_text()
    assert wf4_runner.replay_run(tmp_path / "four")["replay_verified"]
    receipt = bridge.load_receipt(tmp_path / "four_loaded.json")
    assert bridge.check(ledger, tmp_path / "four" / "agent-1" / "task.json", receipt)["status"] == "PASS"
    # WF5 reads one seed language and ignores no suffix: a seed with rules is outside it.
    result = wf5_runner.run(four, tmp_path / "five", gateway_factory=wf5_factory([]))
    assert (result["status"], result["failure_class"]) == ("TYPED_REFUSAL", "WF5_UNSUPPORTED_SEED_LANGUAGE")


def test_a_command_line_that_names_no_work_is_a_usage_error(tmp_path):
    for argv in (
        [],
        ["load", "ledger.jsonl", "task.json"],
        ["trial", "ledger.jsonl", "rule"],
    ):
        with pytest.raises(SystemExit) as stopped:
            bridge.main(argv)
        assert stopped.value.code == 2
    # Run as a module, the command's exit code is the process's.
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pfp.workflows.failure_ledger", "check", "none.jsonl"],
        capture_output=True, check=False, cwd=tmp_path, env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
    )
    assert done.returncode == 2 and b"usage:" in done.stderr


def test_the_command_exits_2_when_the_host_did_not_run(tmp_path, monkeypatch, capsys):
    run = wf1_run(tmp_path / "wrong", task([1, 2]), 4)
    monkeypatch.setenv(operad_host.ENVIRONMENT, str(tmp_path / "no_such_host"))
    assert bridge.main(["record", str(tmp_path / "failures.jsonl"), str(run)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and "OPERAD_HOST_DID_NOT_RUN" in captured.err
