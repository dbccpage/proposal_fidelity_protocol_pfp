import ast
import copy
import hashlib
import importlib.util
import itertools
import json
import os
import re
import runpy
import subprocess
import sys
import typing
from pathlib import Path

import pytest

PILOT_FILE = Path(os.environ.get("PFP_PILOT_000009_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_quiz09_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
SOURCE_RELATIVE_CANDIDATES = (
    Path("_ic/research/briefs/pfp_migration/quiz09_research/sources"),
    Path("_intelligence/research/briefs/pfp_migration/quiz09_research/sources"),
)


def _resolve_source_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        for rel in SOURCE_RELATIVE_CANDIDATES:
            candidate = parent / rel
            if candidate.is_dir():
                return candidate
    pytest.skip("Historical quiz09 source fixture directory is not present in this checkout")


def st(values=(3, 2), rank=1):
    return {"values": list(values), "repair_rank": rank}


def task(initial=None, permissions=None):
    return {"profile": pilot.PROFILE, "initial": st() if initial is None else initial,
            "permissions": [] if permissions is None else permissions}


def step(event, after=None, witness=None):
    return {"event": event, "after": st() if after is None else after, "witness": {} if witness is None else witness}


def independent_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def test_four_numbered_cases_and_five_drills():
    report = pilot.exercise_report()
    assert list(report["cases"]) == ["P9.1", "P9.2", "P9.3", "P9.4"]
    assert [report["cases"][f"P9.{i}"]["accepted"] for i in (1, 2, 3)] == [True, False, False]
    assert [report["cases"]["P9.4"][key]["verdict"] for key in ("equal", "missing", "different")] == [
        "EQUAL_RECORDED_STATES", "UNVERIFIED", "DIFFERENT_RECORDED_STATES"]
    assert [row["accepted"] for row in report["drills"].values()] == [True, True, False, False, False]
    assert all(row["operation_semantics"] == "NOT_CHECKED" for row in report["drills"].values())


@pytest.mark.parametrize("tape,expected", [
    (["C", "T"], True), (["C", "C", "T"], True), (["C", "R", "E", "I", "T"], True),
    (["C", "R", "M", "T"], True), (["C", "D", "E", "I", "T"], True),
    (["C", "R", "LIFT", "E", "I", "T"], True), (["C", "R", "M", "E", "T"], False),
    (["C", "R", "T", "E", "T"], False), (["C", "T", "E"], False), (["E", "C", "T"], False),
    ([], False), (["C"], False), (["C", "X", "T"], False), (["C", "M", "M", "T"], False),
])
def test_shape_rules(tape, expected):
    assert pilot.valid_shape(tape) is expected


def test_shape_against_299593_independent_and_historical_cases():
    source_root = _resolve_source_root()
    source = (source_root / "verify_pfp_quizzes.py").read_text(encoding="utf-8")
    node = next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "validate_dda_trace_tape")
    namespace = {"List": typing.List, "Tuple": typing.Tuple, "Optional": typing.Optional, "DDC_LETTERS": set(pilot.LETTERS)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "historical_shape_only", "exec"), namespace)
    alphabet = ("C", "R", "E", "I", "LIFT", "D", "M", "T")
    pattern = re.compile(r"C(?: (?:C|R|E|I|LIFT|D))*(?: M)? T")
    count = 0
    for length in range(7):
        for symbols in itertools.product(alphabet, repeat=length):
            tape = list(symbols)
            expected = pattern.fullmatch(" ".join(symbols)) is not None
            assert pilot.valid_shape(tape) is expected
            assert namespace["validate_dda_trace_tape"](tape)[0] is expected
            count += 1
    assert count == 299593


@pytest.mark.parametrize("tape", ["CT", ("C", "T"), None, ["C", {}, "T"], ["C", True, "T"], ["C"] * 65])
def test_shape_input_types(tape):
    with pytest.raises(pilot.InvalidInput):
        pilot.valid_shape(tape)


@pytest.mark.parametrize("wire", [" tape<c,t>", "tape<c,t>\n", "tape<C,T>", "tape<c,,t>", "tape<c, t>",
                                       "tape<c,x,t>", "tape<>", "<tape<c,t>>", "tape<c,λ,t>", "tape<c,t>junk"])
def test_wire_is_not_repaired(wire):
    assert not pilot.shape_report(wire)["accepted"]


def test_wire_limits_and_validity():
    assert pilot.shape_report("tape<c,c,lift,d,m,t>")["accepted"]
    assert pilot.shape_report("tape<" + ",".join(["c"] * 63 + ["t"]) + ">")["accepted"]
    for raw in (None, 1, "a" * 513, "tape<" + ",".join(["c"] * 64 + ["t"]) + ">"):
        with pytest.raises(pilot.InvalidInput):
            pilot.shape_report(raw)


@pytest.mark.parametrize("value", [True, 1.0, "1", None, 1000001, -1000001])
def test_invalid_integer(value):
    with pytest.raises(pilot.InvalidInput):
        pilot.state(st([value]))


@pytest.mark.parametrize("value", [None, [], {}, {"values": [1]}, {"values": [1], "repair_rank": 0, "extra": 1},
                                         st([], 0), st([0] * 9, 0), st([1], -1), st([1], 2),
                                         {"values": (1,), "repair_rank": 0}, st([1], True)])
def test_invalid_state(value):
    with pytest.raises(pilot.InvalidInput):
        pilot.state(value)


def test_snapshot_comparison_is_complete_and_three_way():
    same = pilot.compare_snapshots(st(), st())
    assert same["answer"] == "ans<m_invar<stationary>>"
    assert same["unlogged_history"] == "NOT_CHECKED"
    assert pilot.compare_snapshots(st(), st(rank=2))["answer"] == "ref<2>"
    assert pilot.compare_snapshots(st(), st([3, 1]))["answer"] == "ref<2>"
    for before, after in ((None, st()), (st(), None), (None, None)):
        assert pilot.compare_snapshots(before, after)["verdict"] == "UNVERIFIED"
    with pytest.raises(pilot.InvalidInput):
        pilot.compare_snapshots(None, st([True]))
    path = [st([0], 0), st([1], 0), st([0], 0)]
    assert pilot.compare_snapshots(path[0], path[-1])["verdict"] == "EQUAL_RECORDED_STATES"
    assert path[1] != path[0]


def test_refusal_preserves_protected_state_without_alias_mutation():
    before = st()
    snapshot = copy.deepcopy(before)
    after = pilot.refusal_transition(before, "UNREPAIRABLE_TAIL")
    assert after == snapshot and before == snapshot
    assert after is not before and after["values"] is not before["values"]
    after["values"][0] = -100
    assert before == snapshot
    for reason in (True, None, "repair", "", "unrepairable_tail"):
        with pytest.raises(pilot.InvalidInput):
            pilot.refusal_transition(before, reason)
    with pytest.raises(pilot.InvalidInput):
        pilot.transition(task(), before, step("M", st([0, 0]), {"reason": "UNREPAIRABLE_TAIL"}), None)


@pytest.mark.parametrize("kind,expected_length", [("repair", 5), ("refusal", 4), ("descent", 5), ("lift", 6)])
def test_demonstrations_and_independent_record_hashes(kind, expected_length):
    problem, proposal = pilot.demonstration(kind)
    originals = copy.deepcopy((problem, proposal))
    result = pilot.replay(problem, proposal)
    assert (problem, proposal) == originals
    assert result["accepted"] and result["length"] == expected_length
    previous = None
    for index, record in enumerate(result["records"]):
        assert record["index"] == index and record["previous_sha256"] == previous
        assert record["task_sha256"] == independent_hash(problem)
        previous = record["record_sha256"]
        assert previous == independent_hash({key: val for key, val in record.items() if key != "record_sha256"})
    assert result["head_sha256"] == previous
    assert result["external_authorization"] == "NOT_AUTHENTICATED"
    assert result["runtime_equivalence"] == "NOT_CLAIMED"
    if kind in ("descent", "lift"):
        assert result["original_problem_resolution"] == "NOT_CLAIMED_AFTER_SCOPE_CHANGE"
        assert result["scope_change_indices"]
    elif kind == "repair":
        assert result["original_problem_resolution"] == "REPAIRED"
        assert result["final"] == st([0, 0])
    else:
        assert result["sealed_refusal"] and result["original_problem_resolution"] == "UNRESOLVED"
        assert result["final"] == problem["initial"]


def test_exact_finite_projection_and_repair_oracle():
    count = 0
    for size in range(1, 5):
        for coordinates in itertools.product(range(-2, 3), repeat=size):
            for rank in range(size + 1):
                before = st(coordinates, rank)
                observed = pilot.measurement(before)
                projected = [v if i >= rank else 0 for i, v in enumerate(coordinates)]
                assert observed["unrepairable_l1"] == sum(abs(v) for v in projected)
                assert observed["projected_tail"] == projected
                assert observed["prefix_potential"] == list(coordinates[:rank])
                assert pilot.transition(task(before), before, step("R", before,
                    {"potential": list(coordinates[:rank]), "projected": projected}), None) == before
                repair = step("E", st([0] * size, rank), {"potential": list(coordinates[:rank])})
                if any(projected):
                    with pytest.raises(pilot.InvalidInput):
                        pilot.transition(task(before), before, repair, None)
                else:
                    assert pilot.transition(task(before), before, repair, None) == st([0] * size, rank)
                count += 1
    assert count == 3710


def test_false_residual_and_repair_witnesses():
    before = st([3, 0])
    invalid = [step("R", before, {"potential": [2], "projected": [0, 0]}),
               step("R", before, {"potential": [3], "projected": [0, 1]}),
               step("R", before, {"potential": [3.0], "projected": [0, 0]}),
               step("R", st([0, 0]), {"potential": [3], "projected": [0, 0]}),
               step("E", st([0, 0]), {"potential": [2]}), step("E", st([0, 0]), {"potential": [3.0]}),
               step("E", before, {"potential": [3]}), step("E", st([0, 0]), {"potential": [3], "verified": True})]
    for item in invalid:
        with pytest.raises(pilot.InvalidInput):
            pilot.transition(task(before), before, item, None)
    with pytest.raises(pilot.InvalidInput, match="unrepairable"):
        pilot.transition(task(), st(), step("E", st([0, 0]), {"potential": [3]}), None)


def test_integration_receipt_is_computed_and_task_bound():
    problem, proposal = pilot.demonstration("repair")
    for fake in ("0" * 64, "A" * 64, None, True, "receipt", ""):
        altered = copy.deepcopy(proposal)
        altered["steps"][3]["witness"]["record_sha256"] = fake
        with pytest.raises(pilot.InvalidInput):
            pilot.replay(problem, altered)
    changed = copy.deepcopy(problem)
    changed["permissions"] = [pilot.permission_for("LIFT", st(), st(rank=2))]
    with pytest.raises(pilot.InvalidInput, match="Integration receipt"):
        pilot.replay(changed, proposal)
    with pytest.raises(pilot.InvalidInput):
        pilot.transition(task(), st(), step("I", witness={"record_sha256": "0" * 64}), None)


def test_loss_ledger_must_match_dropped_coordinate_exactly():
    problem, proposal = pilot.demonstration("descent")
    for key, wrong in (("value", 0), ("index", 0), ("value", 2.0), ("index", True), ("before_state_sha256", "0" * 64)):
        altered = copy.deepcopy(proposal)
        altered["steps"][1]["witness"]["loss"][key] = wrong
        with pytest.raises(pilot.InvalidInput, match="Loss ledger"):
            pilot.replay(problem, altered)
    for before in (st([3], 0), st([3, 2], 2)):
        with pytest.raises(pilot.InvalidInput, match="D requires"):
            pilot.transition(task(before), before, step("D", before, {"permission_sha256": "0" * 64, "loss": {}}), None)
    before, after = st([-3, -2]), st([-3], 1)
    permission = pilot.permission_for("D", before, after)
    witness = {"permission_sha256": pilot.digest(permission), "loss": {"index": 1, "value": -2, "before_state_sha256": pilot.digest(before)}}
    assert pilot.transition(task(before, [permission]), before, step("D", after, witness), None) == after


@pytest.mark.parametrize("kind,index", [("descent", 1), ("lift", 2)])
def test_permissions_are_complete_state_and_operation_bound(kind, index):
    problem, proposal = pilot.demonstration(kind)
    for modifier in ("missing", "before_rank", "after_rank", "event", "token", "extra_flag"):
        altered_problem, altered = copy.deepcopy((problem, proposal))
        permission = altered_problem["permissions"][0]
        if modifier == "missing":
            altered_problem["permissions"] = []
        elif modifier == "before_rank":
            permission["before_state_sha256"] = pilot.digest(st(rank=0))
        elif modifier == "after_rank":
            permission["after_state_sha256"] = pilot.digest(st(rank=0))
        elif modifier == "event":
            permission["event"] = "D" if kind == "lift" else "LIFT"
        elif modifier == "token":
            altered["steps"][index]["witness"]["permission_sha256"] = "0" * 64
        else:
            altered["steps"][index]["witness"]["licence_verified"] = True
        with pytest.raises(pilot.InvalidInput):
            pilot.transition(altered_problem, altered_problem["initial"], altered["steps"][index], None)


def test_lift_trigger_and_unhelpful_lift():
    for before in (st([0, 0]), st([3, 2], 2)):
        with pytest.raises(pilot.InvalidInput, match="LIFT requires"):
            pilot.transition(task(before), before, step("LIFT", before, {"permission_sha256": "0" * 64}), None)
    before, after = st([3, 0, 2]), st([3, 0, 2], 2)
    permission = pilot.permission_for("LIFT", before, after)
    actual = pilot.transition(task(before, [permission]), before, step("LIFT", after, {"permission_sha256": pilot.digest(permission)}), None)
    assert actual == after and pilot.measurement(actual)["unrepairable_l1"] == 2
    with pytest.raises(pilot.InvalidInput):
        pilot.transition(task(actual), actual, step("E", st([0, 0, 0], 2), {"potential": [3, 0]}), None)


def test_problem_and_proposal_schema_refusals():
    valid, proposal = pilot.demonstration("repair")
    problems = [None, {}, dict(valid, profile="other"), dict(valid, permissions={}), dict(valid, permissions=[{}] * 33),
                dict(valid, permissions=[{"event": "E", "before_state_sha256": "0" * 64, "after_state_sha256": "0" * 64}]),
                dict(valid, permissions=[pilot.permission_for("D", st(), st())] * 2)]
    for problem in problems:
        with pytest.raises(pilot.InvalidInput):
            pilot.replay(problem, proposal)
    for bad in (None, {}, {"steps": "CT"}, {"steps": []}, {"steps": [{}]}, {"steps": [{}, {}]}, {"steps": [{}] * 65}):
        with pytest.raises(pilot.InvalidInput):
            pilot.replay(valid, bad)
    with pytest.raises(pilot.InvalidInput):
        pilot.transition(valid, st(), step("X"), None)
    with pytest.raises(pilot.InvalidInput):
        pilot.demonstration("invented")


def test_shape_rejection_runs_no_operations(monkeypatch):
    calls = []
    monkeypatch.setattr(pilot, "transition", lambda *args: calls.append(args))
    for events in (("C", "R", "M", "E", "T"), ("C", "R", "T", "E", "T")):
        with pytest.raises(pilot.InvalidInput, match="shape"):
            pilot.replay(task(), {"steps": [step(event) for event in events]})
    assert calls == []


def test_extending_sealed_proposal_is_rejected_and_old_result_unchanged():
    problem, proposal = pilot.demonstration("refusal")
    result = pilot.replay(problem, proposal)
    snapshot = copy.deepcopy(result)
    proposal["steps"].extend([step("E", st([0, 0]), {"potential": [3]}), step("T", st([0, 0]))])
    with pytest.raises(pilot.InvalidInput):
        pilot.replay(problem, proposal)
    assert result == snapshot


def test_receipts_snapshot_existing_input_witnesses():
    for kind in ("repair", "refusal", "descent", "lift"):
        problem, proposal = pilot.demonstration(kind)
        result = pilot.replay(problem, proposal)
        snapshot = copy.deepcopy(result)
        for item in proposal["steps"]:
            item["witness"]["tampered_after_replay"] = True
            item["after"]["values"][0] = -999
        problem["initial"]["values"][0] = 444
        assert result == snapshot
        for record in result["records"]:
            assert record["record_sha256"] == independent_hash({key: val for key, val in record.items() if key != "record_sha256"})


def test_stateless_context_and_terminal_cannot_hide_work():
    before = st()
    for event in ("C", "T"):
        assert pilot.transition(task(), before, step(event), None) == before
        with pytest.raises(pilot.InvalidInput):
            pilot.transition(task(), before, step(event, st([0, 0])), None)
    result = pilot.replay(task(), {"steps": [step("C"), step("C"), step("T")]})
    assert result["original_problem_resolution"] == "UNRESOLVED" and not result["sealed_refusal"]


def test_no_witness_is_replaced_by_a_boolean_flag():
    for event in ("C", "R", "E", "I", "LIFT", "D", "M", "T"):
        with pytest.raises(pilot.InvalidInput):
            pilot.transition(task(), st(), step(event, witness={"verified": True}), "0" * 64)


def test_document_modes_and_missing_inputs():
    assert pilot.evaluate({"kind": "shape", "wire": "tape<c,t>"}, None)["accepted"]
    assert pilot.evaluate({"kind": "stationarity", "before": st(), "after": None}, None)["verdict"] == "UNVERIFIED"
    problem, proposal = pilot.demonstration("repair")
    assert pilot.evaluate({"kind": "replay", "problem": problem}, proposal)["accepted"]
    invalid = [(None, None), ({"kind": "other"}, None), ({"kind": "shape", "wire": "tape<c,t>"}, {}),
               ({"kind": "stationarity", "before": st(), "after": st()}, {}), ({"kind": "replay", "problem": problem}, None)]
    for document, submitted in invalid:
        with pytest.raises(pilot.InvalidInput):
            pilot.evaluate(document, submitted)


@pytest.mark.parametrize("raw", [b'{"kind":0,"kind":1}', b'NaN', b'Infinity', b'\xff', b'{', b'x' * 65537],
                         ids=["duplicate", "nan", "infinity", "utf8", "syntax", "oversize"])
def test_hostile_raw_documents(tmp_path, raw):
    path = tmp_path / "input.bin"
    path.write_bytes(raw)
    with pytest.raises((pilot.InvalidInput, ValueError)):
        pilot.read_document(path)


def test_run_custody_and_no_overwrite(tmp_path, monkeypatch):
    class Fixed:
        hex = "fixed"
    monkeypatch.setattr(pilot, "uuid4", Fixed)
    report = pilot.exercise_report()
    folder = pilot.write_run(tmp_path, report, "CHECKED", b'  {"a":1}\r\n', b' proposal \n')
    receipt = json.loads((folder / "receipt.json").read_text())
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert set(receipt["artifacts"]) == {"input.bin", "proposal.bin", "result.json", "summary.md"}
    for name, wanted in receipt["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == wanted
    assert (folder / "input.bin").read_bytes() == b'  {"a":1}\r\n'
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    with pytest.raises(FileExistsError):
        pilot.write_run(tmp_path, {}, "CHECKED", b'', None)
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}


@pytest.mark.parametrize("document,status,code", [
    ({"kind": "shape", "wire": "tape<c,t>"}, "CHECKED", 0),
    ({"kind": "shape", "wire": "tape<c,t,e,t>"}, "REJECTED", 1),
    ({"kind": "stationarity", "before": st(), "after": None}, "UNVERIFIED", 1),
    ({"kind": "stationarity", "before": st(), "after": st([0, 0])}, "REJECTED", 1),
    ({"kind": "other"}, "REJECTED", 1),
])
def test_main_modes_retain_result(tmp_path, capsys, document, status, code):
    source = tmp_path / "input.json"
    raw = (json.dumps(document) + "\r\n").encode()
    source.write_bytes(raw)
    assert pilot.main(["--input", str(source), "--output-dir", str(tmp_path / "outputs")]) == code
    outcome = json.loads(capsys.readouterr().out)
    assert outcome["status"] == status
    assert (Path(outcome["output"]) / "input.bin").read_bytes() == raw


def test_main_success_default_and_separate_replay(tmp_path, capsys):
    assert pilot.main(["--output-dir", str(tmp_path / "default")]) == 0
    capsys.readouterr()
    problem, proposal = pilot.demonstration("lift")
    source, submission = tmp_path / "task.json", tmp_path / "proposal.json"
    source.write_text(json.dumps({"kind": "replay", "problem": problem}))
    submission.write_text(json.dumps(proposal))
    assert pilot.main(["--input", str(source), "--proposal", str(submission), "--output-dir", str(tmp_path / "replay")]) == 0
    result = json.loads(capsys.readouterr().out)
    assert (Path(result["output"]) / "proposal.bin").read_bytes() == submission.read_bytes()


def test_main_controlled_failures(tmp_path, capsys, monkeypatch):
    assert pilot.main(["--proposal", "absent"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert pilot.main(["--input", str(tmp_path / "missing")]) == 2
    capsys.readouterr()
    raw = tmp_path / "bad.json"
    raw.write_bytes(b'{')
    assert pilot.main(["--input", str(raw)]) == 2
    capsys.readouterr()
    for error in (OSError("no write"), TypeError("bad type"), RecursionError("deep input")):
        def fail(*args, error=error):
            raise error
        monkeypatch.setattr(pilot, "exercise_report", fail)
        assert pilot.main(["--output-dir", str(tmp_path)]) == 2
        assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"


def test_actual_cli_process_and_artifact_replay(tmp_path):
    completed = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                               capture_output=True, text=True, timeout=30, check=False)
    assert completed.returncode == 0, completed.stderr
    folder = Path(json.loads(completed.stdout)["output"])
    receipt = json.loads((folder / "receipt.json").read_text())
    report = json.loads((folder / "result.json").read_text())
    assert [report["cases"][f"P9.{i}"]["answer"] for i in (1, 2, 3)] == ["ans<tape<valid>>", "ref<1>", "ref<1>"]
    assert [report["cases"]["P9.4"][key]["answer"] for key in ("equal", "missing", "different")] == [
        "ans<m_invar<stationary>>", "ans<m_invar<unverified>>", "ref<2>"]
    assert [row["accepted"] for row in report["drills"].values()] == [True, True, False, False, False]
    assert {kind: row["original_problem_resolution"] for kind, row in report["demonstrations"].items()} == {
        "repair": "REPAIRED", "refusal": "UNRESOLVED",
        "descent": "NOT_CLAIMED_AFTER_SCOPE_CHANGE", "lift": "NOT_CLAIMED_AFTER_SCOPE_CHANGE"}
    assert set(receipt["artifacts"]) == {"input.bin", "result.json", "summary.md"}
    for name, expected in receipt["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("boolean_integer", "type(value) is int and abs(value)", "isinstance(value, int) and abs(value)", "test_invalid_integer"),
        ("no_initial_context", 'tape[0] != "C"', 'False', "test_shape_rules"),
        ("terminal_nonabsorbing", 'event == "T" and index != len(tape) - 1', 'False', "test_shape_rules"),
        ("refusal_allows_repair", 'event == "M" and tape[index + 1] != "T"', 'False', "test_shape_rules"),
        ("rank_ignored_in_equality", 'elif left == right:', 'elif left[0] == right[0]:', "test_snapshot_comparison_is_complete_and_three_way"),
        ("missing_is_stationary", 'verdict = "UNVERIFIED"', 'verdict = "EQUAL_RECORDED_STATES"', "test_snapshot_comparison_is_complete_and_three_way"),
        ("omit_residual_witness", 'require(canonical(witness) == canonical({"potential": observed["prefix_potential"], "projected": observed["projected_tail"]}),', 'require(True,', "test_false_residual_and_repair_witnesses"),
        ("omit_repair_potential", 'require(canonical(witness["potential"]) == canonical(list(coordinates[:rank])),', 'require(True,', "test_false_residual_and_repair_witnesses"),
        ("repair_nonexact_tail", 'require(observed["unrepairable_l1"] == 0,', 'require(True,', "test_false_residual_and_repair_witnesses"),
        ("forged_integration", 'require(previous is not None and witness["record_sha256"] == previous,', 'require(True,', "test_integration_receipt_is_computed_and_task_bound"),
        ("unpriced_descent", 'require(canonical(witness["loss"]) == canonical(loss),', 'require(True,', "test_loss_ledger_must_match_dropped_coordinate_exactly"),
        ("ignore_permission", 'require(permission in problem["permissions"] and submitted == digest(permission),', 'require(True,', "test_permissions_are_complete_state_and_operation_bound"),
        ("trust_proposed_after", 'require(state(after) == state(expected),', 'require(True,', "test_refusal_preserves_protected_state_without_alias_mutation"),
        ("scope_change_is_original_solution", 'resolution = "NOT_CLAIMED_AFTER_SCOPE_CHANGE" if scope_changes else', 'resolution = "REPAIRED" if scope_changes else', "test_demonstrations_and_independent_record_hashes"),
        ("trim_raw_wire", 'matched = re.fullmatch(r"tape<([a-z]+(?:,[a-z]+)*)>", wire)', 'matched = re.fullmatch(r"tape<([a-z]+(?:,[a-z]+)*)>", wire.strip())', "test_wire_is_not_repaired"),
        ("mutable_receipt_alias", '    row = json.loads(canonical(row))\n', '', "test_receipts_snapshot_existing_input_witnesses"),
    ]
    evidence = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "anchor count")
        mutated = source.replace(anchor, replacement)
        compile(mutated, name, "exec")
        path = tmp_path / (name + ".py")
        path.write_text(mutated, encoding="utf-8")
        env = dict(os.environ, PFP_PILOT_000009_UNDER_TEST=str(path), NO_COLOR="1")
        for variable in ("PFP_PILOT_000009_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        completed = subprocess.run([sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
                                    "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
                                   env=env, capture_output=True, text=True, check=False, timeout=40)
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        evidence.append({"name": name, "anchor": anchor, "replacement": replacement, "target": str(PILOT_FILE),
                         "applied": path.read_text(encoding="utf-8") == mutated,
                         "mutant_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "original_sha256": hashlib.sha256(original).hexdigest(),
                         "original_unchanged": PILOT_FILE.read_bytes() == original,
                         "failed_nodes": failures, "exit_code": completed.returncode})
    assert len(evidence) == 16
    if output := os.environ.get("PFP_PILOT_000009_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "CHECKED"


def test_default_output_root_is_beside_the_pilot():
    assert pilot.OUTPUT_ROOT == PILOT_FILE.resolve().parent.parent / "pilot_output" / pilot.PILOT_ID
