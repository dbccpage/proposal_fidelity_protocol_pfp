from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

RUNNER = Path(os.environ.get("PFP_PILOT_000011_UNDER_TEST", Path(__file__).resolve().parents[2] / "run.py"))
spec = importlib.util.spec_from_file_location("quiz01_under_test", RUNNER)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def test_source_mapping_and_controls():
    report = p.exercise_report()
    rows = {row["id"]: row for row in report["exercises"]}
    assert len(rows) == 8
    assert set(rows) == {f"P1.{i}" for i in range(1, 4)} | {f"DRILL1.{i}" for i in range(1, 6)}
    assert all(row["result"]["verdict"] == "MATCH" for row in rows.values())
    assert rows["P1.2"]["source_answer"] == "ans<eqexpr<pd<>,a,0>>"
    assert rows["P1.3"]["source_answer"] == "ans<audit<curr<a>,prev<pd<>>,hist<pd<>>,ment<ab>,intern<a>>>"
    assert rows["DRILL1.5"]["result"]["computed_answer"] == {"current": "a", "previous": "ground", "mentioned_only": ["ab"]}
    assert report["P1.2_refusal_trap"]["computed_answer"]["refusal"] == "ref<2>"
    assert len(report["controls"]) == 9
    assert {name for name, result in report["controls"].items() if result["verdict"] == "MISMATCH"} == {"forged_successor", "forged_internal"}
    assert all(result["authority_effect"] == result["genesis_effect"] == "None" for result in report["controls"].values())
    assert report["controls"]["same_text_distinct_records"]["computed_answer"]["separating_tests"] == ["t1"]
    assert report["controls"]["declared_not_true"]["computed_answer"]["status"] == "DECLARED_NOT_VALIDATED"


def test_all_three_vertex_relations_against_matrix_oracle():
    names = ["ground", "a", "ab"]
    for mask in range(512):
        task = p.ground_task()
        task["transitions"] = [[names[i], names[j]] for i in range(3) for j in range(3) if mask & (1 << (i * 3 + j))]
        for i, seed in enumerate(names):
            expected = sorted(names[j] for j in range(3) if (mask >> (3 * i + j)) % 2 == 1)
            result = p.answer_for(task, {"kind": "successors", "seed": seed})
            assert result == {"successors": expected, "quiescent": not expected,
                              "sole_successor": expected[0] if len(expected) == 1 else None, "inevitability": "NOT_ESTABLISHED"}


def test_relation_permission_does_not_force_progress():
    task = p.ground_task()
    for edges, permitted in (([], False), ([["a", "ab"]], False), ([["ground", "a"]], True),
                             ([["ground", "a"], ["ground", "ab"]], True), ([["ground", "ground"]], False)):
        task["transitions"] = edges
        assert p.answer_for(task, {"kind": "permitted_next", "seed": "ground", "target": "a"}) == {"permitted": permitted, "scope": "DECLARED_RELATION_ONLY"}
        assert p.answer_for(task, {"kind": "forced_next", "seed": "ground", "target": "a"}) == {"refusal": "ref<2>", "reason": "NO_FORCING_CONTRACT", "permitted": permitted}
    assert p.answer_for(task, {"kind": "successors", "seed": "ground"})["quiescent"] is False


def test_complete_observations_against_independent_profiles():
    for same_text in (False, True):
        task = p.observation_task(same_text)
        for bits in itertools.product(("x", "y"), repeat=4):
            task["observations"] = [
                {"test_id": "second", "domain": ["a", "ground"], "values": {"ground": bits[2], "a": bits[3]}},
                {"test_id": "first", "domain": ["ground", "a"], "values": {"ground": bits[0], "a": bits[1]}}]
            for left, right in itertools.product(("ground", "a"), repeat=2):
                li, ri = int(left == "a"), int(right == "a")
                expected = [name for name, offset in (("first", 0), ("second", 2)) if bits[offset + li] != bits[offset + ri]]
                result = p.answer_for(task, {"kind": "profiles", "left": left, "right": right})
                assert result["separating_tests"] == expected
                assert result["external_text_equal"] == (same_text or left == right)
                assert result["operands_admitted"] is True
                assert result["comparison_status"] == "CHECKED_DECLARED_TABLES"
                assert result["object_equality"] == "NOT_INFERRED"
                assert result["expressive_power"] == "NOT_MEASURED"
                claimed = p.answer_for(task, {"kind": "claim_discrimination", "left": left, "right": right})
                assert claimed == ({"separating_tests": expected} if expected else {"refusal": "ref<2>", "reason": "NO_DECLARED_SEPARATING_WITNESS"})


def test_empty_tables_differ_from_unadmitted_operands():
    task = p.observation_task()
    task["observations"] = []
    result = p.answer_for(task, {"kind": "profiles", "left": "ground", "right": "a"})
    assert result["comparison_status"] == "NO_DECLARED_TESTS" and result["operands_admitted"]
    result = p.answer_for(task, {"kind": "profiles", "left": "ab", "right": "a"})
    assert result["comparison_status"] == "UNADMITTED_OPERAND" and not result["operands_admitted"]
    assert result["separating_tests"] == []


def test_provenance_facets_and_projection_order():
    task = p.provenance_task()
    expected = {"current": "a", "previous": "ground", "history": ["ground"], "supplied": ["a", "ground"], "mentioned_only": ["ab"], "internal": ["a"]}
    for order in itertools.permutations(p.FACETS):
        assert p.answer_for(task, {"kind": "provenance", "facets": list(order)}) == expected
    assert p.answer_for(p.ground_task(), {"kind": "provenance", "facets": list(p.FACETS)}) == {
        "current": "ground", "previous": None, "history": [], "supplied": ["ground"], "mentioned_only": [], "internal": []}
    assert p.answer_for(p.ground_task(), {"kind": "presentation"}) == {"id": "ground", "text": "<>", "internally_admitted": False, "semantics": "NOT_INFERRED"}
    assert p.answer_for(task, {"kind": "presentation"})["internally_admitted"] is True


def test_chronological_designation_resets_only_active_admission():
    task = p.provenance_task()
    task["events"].append({"kind": "mention", "event_id": "m2", "presentation": "a"})
    assert p.answer_for(task, {"kind": "provenance", "facets": ["mentioned_only"]}) == {"mentioned_only": ["ab"]}
    task["events"].append({"kind": "designate", "event_id": "d2", "presentation": "ground"})
    assert p.answer_for(task, {"kind": "provenance", "facets": list(p.FACETS)}) == {
        "current": "ground", "previous": "a", "history": ["ground", "a"], "supplied": ["a", "ground"], "mentioned_only": ["ab"], "internal": []}
    p.append_admission(task, "ground", "s0", "d2", "r2")
    task["events"][-1]["basis"] = "consumer"
    assert p.answer_for(task, {"kind": "provenance", "facets": ["internal"]}) == {"internal": ["ground"]}


def test_interpretations_are_declarations_not_semantic_truth():
    task = p.ground_task()
    query = {"kind": "interpretation", "presentation": "ground", "meaning": "void"}
    assert p.answer_for(task, query) == {"refusal": "ref<1>", "reason": "UNDECLARED_INTERPRETATION"}
    task["interpretations"] = [{"declaration_id": "z", "presentation": "ground", "meaning": "void"},
                               {"declaration_id": "a", "presentation": "ground", "meaning": "void"},
                               {"declaration_id": "other", "presentation": "a", "meaning": "void"},
                               {"declaration_id": "set", "presentation": "ground", "meaning": "set"}]
    assert p.answer_for(task, query) == {"status": "DECLARED_NOT_VALIDATED", "declarations": ["a", "z"]}
    assert p.answer_for(task, {"kind": "authority"}) == {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"}


@pytest.mark.parametrize("mutate", [
    lambda t: t.update(extra=True), lambda t: t.pop("observations"), lambda t: t.update(task_id=True),
    lambda t: t.update(presentations=[]), lambda t: t["presentations"].append(deepcopy(t["presentations"][0])),
    lambda t: t["presentations"][0].update(text=""), lambda t: t["presentations"][0].update(text="x" * 257),
    lambda t: t["presentations"][0].update(id="Bad"), lambda t: t["presentations"][0].update(text=True),
    lambda t: t["presentations"][0].update(extra=0), lambda t: t.update(events=[]),
    lambda t: t["events"].append(None), lambda t: t["events"][0].update(kind="invent"),
    lambda t: t["events"][0].update(presentation="missing"), lambda t: t["events"][0].update(presentation=[]),
    lambda t: t["events"][1].update(event_id="s0"), lambda t: t["events"][1].update(presentation="a"),
    lambda t: t.update(events=[{"kind": "mention", "event_id": "m0", "presentation": "ground"}, {"kind": "mention", "event_id": "m1", "presentation": "a"}]),
    lambda t: t["events"].append({"kind": "supply", "event_id": "s2", "presentation": "ground"}),
    lambda t: t.update(transitions=[["ground"]]), lambda t: t.update(transitions=[["ground", "missing"]]),
    lambda t: t.update(transitions=[["ground", "a"], ["ground", "a"]]), lambda t: t.update(transitions="ground"),
    lambda t: t.update(observations=None), lambda t: t.update(observations=[{}]),
    lambda t: t.update(interpretations=None), lambda t: t.update(interpretations=[{}]),
])
def test_invalid_task_shapes(mutate):
    task = p.ground_task()
    mutate(task)
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


@pytest.mark.parametrize("field,value", [
    ("supply_event", "future"), ("supply_event", "s0"), ("supply_event", []),
    ("regime_event", "d0"), ("regime_event", None), ("basis", "self_assertion"),
    ("prefix_sha256", "0" * 64), ("inscription_sha256", "0" * 64), ("receipt_id", True),
])
def test_admission_binding_fields(field, value):
    task = p.provenance_task()
    task["events"][-1][field] = value
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


def test_admission_task_and_history_substitution():
    for mutation in ("task_id", "inscription", "order", "repeat", "before_designation", "receipt_reuse"):
        task = p.provenance_task()
        if mutation == "task_id":
            task["task_id"] = "replacement"
        elif mutation == "inscription":
            task["presentations"][1]["text"] = "different"
        elif mutation == "order":
            task["events"][2], task["events"][5] = task["events"][5], task["events"][2]
        elif mutation == "repeat":
            p.append_admission(task, "a", "s1", "d1", "second")
        elif mutation == "before_designation":
            task["events"] = [task["events"][0], task["events"][-1]]
            task["events"][-1].update(presentation="ground", supply_event="s0")
        else:
            task["events"].append({"kind": "designate", "event_id": "d2", "presentation": "ground"})
            p.append_admission(task, "ground", "s0", "d2", "new")
            task["events"][-1]["receipt_id"] = "r1"
        with pytest.raises(p.InvalidInput):
            p.validate_task(task)


@pytest.mark.parametrize("mutate", [
    lambda t: t["observations"][0].update(domain=["a"]),
    lambda t: t["observations"][0].update(domain=["a", "a"]),
    lambda t: t["observations"][0].update(domain=["a", "missing"]),
    lambda t: t["observations"][0].update(values={"a": "0"}),
    lambda t: t["observations"][0].update(values=[]),
    lambda t: t["observations"][0]["values"].update(a=True),
    lambda t: t["observations"][0]["values"].update(a="x" * 33),
    lambda t: t["observations"].append(deepcopy(t["observations"][0])),
    lambda t: t["observations"][0].update(test_id=True),
])
def test_incomplete_or_invalid_observations_are_not_equal(mutate):
    task = p.observation_task()
    mutate(task)
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


@pytest.mark.parametrize("value", [None, [], {}, {"kind": []}, {"kind": "missing"}, {"kind": "presentation", "extra": 1},
                                       {"kind": "successors", "seed": "missing"}, {"kind": "successors", "seed": True},
                                       {"kind": "provenance", "facets": []}, {"kind": "provenance", "facets": ["current", "current"]},
                                       {"kind": "provenance", "facets": [1]}, {"kind": "provenance", "facets": ["invented"]},
                                       {"kind": "interpretation", "presentation": "ground", "meaning": ""}])
def test_invalid_queries(value):
    with pytest.raises(p.InvalidInput):
        p.answer_for(p.ground_task(), value)


def test_invalid_interpretation_registry():
    task = p.ground_task()
    item = {"declaration_id": "i1", "presentation": "ground", "meaning": "void"}
    for values in ([item, deepcopy(item)], [{**item, "presentation": "missing"}], [{**item, "meaning": ""}], [{**item, "declaration_id": False}]):
        task["interpretations"] = values
        with pytest.raises(p.InvalidInput):
            p.validate_task(task)


def test_bounded_collection_limits():
    task = p.ground_task()
    for field, length in (("presentations", 17), ("events", 65), ("transitions", 65), ("observations", 9), ("interpretations", 17)):
        bad = deepcopy(task)
        bad[field] = [{}] * length
        with pytest.raises(p.InvalidInput):
            p.validate_task(bad)
    assert p.validate_task(p.ground_task())["current"] == "ground"


def test_proposal_binding_canonical_types_and_snapshot():
    task = p.ground_task()
    query = {"kind": "presentation"}
    answer = {"id": "ground", "text": "<>", "internally_admitted": False, "semantics": "NOT_INFERRED"}
    doc = p.submission(task, query, answer)
    result = p.evaluate(doc)
    stable = p.encoded(result)
    assert result["verdict"] == "MATCH"
    answer["internally_admitted"] = 0
    assert p.evaluate(doc)["verdict"] == "MISMATCH"
    answer["invented"] = True
    task["presentations"][0]["text"] = "changed"
    query["kind"] = "authority"
    assert p.encoded(result) == stable
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)
    doc = p.submission(p.ground_task(), {"kind": "authority"}, {})
    doc["proposal"]["problem_sha256"] = "0" * 64
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(extra=1), lambda d: d["proposal"].update(PASS=True),
    lambda d: d["proposal"].update(answer=[]), lambda d: d["proposal"].update(answer={"blob": "x" * p.MAX_BYTES}),
])
def test_invalid_proposal_shapes(mutate):
    doc = p.submission(p.ground_task(), {"kind": "authority"}, {})
    mutate(doc)
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)


@pytest.mark.parametrize("raw", [b"", b"{", b"\xff", b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b" " * (p.MAX_BYTES + 1)],
                         ids=("empty", "malformed", "utf8", "duplicate", "nan", "infinity", "oversize"))
def test_bad_raw_input_refused(raw, tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_bytes(raw)
    output = tmp_path / "runs"
    assert p.main(["--input", str(source), "--output-dir", str(output)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not output.exists()


def test_decode_strict_bytes():
    for raw in (None, "", bytearray(b"{}")):
        with pytest.raises(p.InvalidInput):
            p.decode(raw)


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"], ids=("high", "low"))
def test_escaped_surrogate_is_retained_rejection(surrogate, tmp_path, capsys):
    task = p.provenance_task()
    task["presentations"][1]["text"] = surrogate
    task["events"][-1]["prefix_sha256"] = p.event_prefix(task, len(task["events"]) - 1)
    with pytest.raises(p.InvalidInput, match="UTF-8"):
        p.validate_task(task)
    raw = b" \n" + p.encoded(p.submission(task, {"kind": "presentation"}, {})) + b"\t"
    source = tmp_path / "input.json"
    source.write_bytes(raw)
    output = tmp_path / "runs"
    assert p.main(["--input", str(source), "--output-dir", str(output)]) == 1
    message = json.loads(capsys.readouterr().out)
    assert message["status"] == "REJECTED"
    folder = Path(message["output"])
    assert (folder / "input.bin").read_bytes() == raw
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["status"] == "REJECTED" and len(receipt["artifact_sha256"]) == 3
    for name, expected in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    cli = subprocess.run([sys.executable, str(RUNNER), "--input", str(source), "--output-dir", str(output)],
                         text=True, capture_output=True, timeout=20, check=False)
    assert cli.returncode == 1, cli.stderr
    assert json.loads(cli.stdout)["status"] == "REJECTED"
    assert len(list(output.iterdir())) == 2


def test_raw_receipt_and_no_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(p, "uuid4", lambda: SimpleNamespace(hex="fixed"))
    raw = b' \n {"x": 1} \t'
    folder = p.write_run(tmp_path, {"ok": True}, raw, "MATCH")
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert (folder / "input.bin").read_bytes() == raw
    assert set(receipt["artifact_sha256"]) == {"input.bin", "result.json", "summary.md"}
    for name, value in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == value
    assert receipt["code_sha256"] == hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    with pytest.raises(FileExistsError):
        p.write_run(tmp_path, {"other": True}, b"new", "MATCH")
    assert (folder / "input.bin").read_bytes() == raw


@pytest.mark.parametrize("kind,expected", [("match", "MATCH"), ("wrong", "MISMATCH"), ("invalid", "REJECTED"), ("default", "DEMONSTRATED")])
def test_real_cli_paths(kind, expected, tmp_path):
    command = [sys.executable, str(RUNNER), "--output-dir", str(tmp_path / "runs")]
    raw = None
    if kind != "default":
        answer = {"refusal": "ref<2>", "reason": "NO_ACTION_AUTHORITY"} if kind == "match" else {}
        document = {} if kind == "invalid" else p.submission(p.ground_task(), {"kind": "authority"}, answer)
        raw = b" \n" + p.encoded(document) + b"\t"
        source = tmp_path / "input.json"
        source.write_bytes(raw)
        command += ["--input", str(source)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=20, check=False)
    assert result.returncode == (1 if kind in ("wrong", "invalid") else 0), result.stderr
    message = json.loads(result.stdout)
    assert message["status"] == expected
    folder = Path(message["output"])
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert receipt["status"] == expected
    if raw is not None:
        assert (folder / "input.bin").read_bytes() == raw
    if kind == "default":
        assert json.loads((folder / "result.json").read_bytes()) == p.exercise_report()


def test_main_inprocess_branches(tmp_path, capsys):
    output = tmp_path / "runs"
    assert p.main(["--output-dir", str(output)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"
    source = tmp_path / "in.json"
    source.write_bytes(p.encoded(p.submission(p.ground_task(), {"kind": "authority"}, {})))
    assert p.main(["--input", str(source), "--output-dir", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "MISMATCH"
    source.write_bytes(b"{}")
    assert p.main(["--input", str(source), "--output-dir", str(output)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    assert p.main(["--input", str(tmp_path / "missing"), "--output-dir", str(output)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    blocker = tmp_path / "blocker"
    blocker.write_bytes(b"not a directory")
    assert p.main(["--output-dir", str(blocker)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"


MUTATIONS = (
    ("utf8_guard_removed", 'value.encode("utf-8")', "None", "test_escaped_surrogate"),
    ("global_not_local", 'if pre == query["seed"]', 'if True', "test_all_three_vertex_relations"),
    ("self_loop_lost", 'if pre == query["seed"]', 'if pre == query["seed"] and pre != post', "test_all_three_vertex_relations"),
    ("permission_promoted", 'return {"refusal": "ref<2>", "reason": "NO_FORCING_CONTRACT", "permitted": query["target"] in successors}',
     'return {"refusal": "ref<2>", "reason": "FORCED", "permitted": query["target"] in successors}', "test_relation_permission"),
    ("supply_becomes_admission", "supplied.add(mark)", "supplied.add(mark)\n            internal.add(mark)", "test_empty_tables or test_source_mapping"),
    ("history_loses_previous", '"history": designations[:-1]', '"history": []', "test_provenance_facets"),
    ("admission_persists", "internal = set()", "internal = internal", "test_chronological_designation"),
    ("future_supply_allowed", 'supplies.get(event["supply_event"]) == mark', "True", "test_admission_binding_fields"),
    ("wrong_regime", 'regime is not None and event["regime_event"] == regime', "True", "test_admission_binding_fields"),
    ("no_prefix_binding", 'event["prefix_sha256"] == event_prefix(task, index)', "True", "test_admission_binding_fields"),
    ("no_inscription_binding", 'event["inscription_sha256"] == sha(texts[mark].encode("utf-8"))', "True", "test_admission_binding_fields"),
    ("strings_replace_profiles", 'table["values"][left] != table["values"][right]', 'context["texts"][left] != context["texts"][right]', "test_complete_observations"),
    ("unbound_proposal", 'document["proposal"]["problem_sha256"] == problem_digest(document["task"], document["query"])', "True", "test_proposal_binding"),
    ("boolean_numeric_equal", 'encoded(snapshot["proposal"]["answer"]) == encoded(computed)', 'snapshot["proposal"]["answer"] == computed', "test_proposal_binding"),
    ("no_snapshot", "snapshot = decode(raw)", "snapshot = document", "test_proposal_binding"),
    ("duplicate_keys_allowed", 'require(key not in result, "Duplicate JSON key")', 'require(True, "Duplicate JSON key")', "test_bad_raw"),
    ("raw_bytes_lost", '"input.bin": raw_input', '"input.bin": raw_input.strip()', "test_raw_receipt"),
    ("overwrite_allowed", "exist_ok=False", "exist_ok=True", "test_raw_receipt"),
)


def test_implementation_mutations(tmp_path):
    source_bytes = RUNNER.read_bytes()
    source = RUNNER.read_text(encoding="utf-8")
    rows = []
    for name, anchor, replacement, selected in MUTATIONS:
        assert source.count(anchor) == 1, (name, source.count(anchor))
        mutant_text = source.replace(anchor, replacement)
        compile(mutant_text, name, "exec")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(mutant_text, encoding="utf-8")
        environment = dict(os.environ, PFP_PILOT_000011_UNDER_TEST=str(mutant), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                           PYTHONDONTWRITEBYTECODE="1", NO_COLOR="1")
        for variable in ("PFP_PILOT_000011_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            environment.pop(variable, None)
        result = subprocess.run([sys.executable, "-m", "pytest", str(Path(__file__)), "-q", "--color=no", "-p", "no:cacheprovider", "-o", "addopts=",
                                 "--import-mode=importlib", "--basetemp", str(tmp_path / (name + "_temp")), "-k", selected],
                                env=environment, text=True, capture_output=True, timeout=30, check=False)
        failures = [line for line in result.stdout.splitlines() if line.startswith("FAILED ")]
        assert result.returncode == 1 and failures, (name, result.returncode, result.stdout, result.stderr)
        assert RUNNER.read_bytes() == source_bytes
        rows.append({"name": name, "anchor": anchor, "replacement": replacement, "target": str(RUNNER.resolve()),
                     "applied": True, "exit_code": result.returncode, "failed_nodes": failures, "original_unchanged": True,
                     "original_sha256": hashlib.sha256(source_bytes).hexdigest(), "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest()})
    if output := os.environ.get("PFP_PILOT_000011_MUTATION_OUTPUT"):
        with Path(output).open("x", encoding="utf-8") as stream:
            json.dump(rows, stream, indent=2)


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(RUNNER), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert p.OUTPUT_ROOT == RUNNER.resolve().parent.parent / "pilot_output" / p.PILOT_ID


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    computed = p.answer_for

    def drifted(task, query):
        answer = computed(task, query)
        return {**answer, "text": "<x>"} if query["kind"] == "presentation" else answer

    monkeypatch.setattr(p, "answer_for", drifted)
    report = p.exercise_report()
    assert [row["id"] for row in report["exercises"] if row["result"]["verdict"] == "MISMATCH"] == ["DRILL1.1"]
    assert p.demonstration_status(report) == "MISMATCH"
    assert p.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
