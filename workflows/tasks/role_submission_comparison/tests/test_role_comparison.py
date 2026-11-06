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

PILOT_FILE = Path(os.environ.get("PFP_PILOT_000010_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("quiz10_under_test", PILOT_FILE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def document(task=None, request="record", execute=False):
    task = task or p.inequality([2, 3], [4, 1])
    return {"task": task, "red": p.role_proposal(task, "red"), "green": p.role_proposal(task, "green"),
            "request": request, "execute_check": execute}


def frozen(task=None):
    doc = document(task)
    raw = p.freeze(doc["task"], doc["red"], doc["green"])
    return doc, raw


def test_all_source_items_and_controls():
    report = p.exercise_report()
    rows = {row["id"]: row["result"] for row in report["exercises"]}
    assert set(rows) == {f"P10.{i}" for i in range(1, 5)} | {f"DRILL10.{i}" for i in range(1, 6)}
    assert len(report["contextual_tags"]) == 8
    assert rows["P10.1"]["claim_status"] == "UNVERIFIED"
    assert rows["P10.1"]["check"]["status"] == "UNBOUND"
    assert rows["P10.1"]["frozen"]["task"]["proposition"]["text"] == "We have mathematically proven that the transformer attention mechanism is identical to the continuous Riemann zeta function."
    assert len(rows["P10.1"]["missing_declared_inputs"]) == 4
    assert rows["P10.2"]["proposal_changes"][0]["new_claim_status"] == "UNVERIFIED"
    assert rows["P10.2"]["proposal_changes"][0]["semantic_loss"] == "NOT_MEASURED"
    assert len(rows["P10.2"]["proposal_changes"][0]["dropped_requirements"]) == 4
    assert rows["P10.3"]["refusal"] == "ref<2>"
    assert rows["P10.4"]["frozen"]["green"]["tag"] == "DERIVED"
    assert rows["P10.4"]["frozen"]["task"]["claim_id"] == "born_rule_hilbert_lift"
    assert rows["P10.4"]["frozen"]["task"]["proposition"]["text"] == "born_rule_hilbert_lift (worksheet scope: discrete_weights)"
    assert rows["P10.4"]["claim_status"] == "UNVERIFIED"
    assert rows["DRILL10.5"]["refusal"] == "ref<2>"
    assert rows["DRILL10.5"]["check"]["executed"] is True
    assert all(row["authority_effect"] == "None" for row in rows.values())
    assert report["controls"]["checked_true"]["claim_status"] == "CHECKED"
    assert report["controls"]["false_consensus"]["claim_status"] == "CONTRADICTED"
    assert report["controls"]["true_despite_disagreement"]["claim_status"] == "CHECKED"
    assert report["historical_label_status"] == "SOURCE_PROPOSALS_NOT_COMPUTED_CONCLUSIONS"


def test_exact_predicate_against_independent_margin():
    # Fold subtraction one operand at a time, independently of the checker sums.
    for a, b, c, d in itertools.product(range(-3, 4), repeat=4):
        margin = c
        margin += d
        margin -= a
        margin -= b
        task = p.inequality([a, b], [c, d])
        check = p.finite_check(task)
        assert check["status"] == ("PASS" if margin >= 0 else "FAIL")
        assert check["margin"] == margin
        assert check["executed"] is True
        assert check["task_sha256"] == p.digest(task)
    for left, right in (([-10**6] * 16, [10**6] * 16), ([10**6] * 16, [-10**6] * 16)):
        assert p.finite_check(p.inequality(left, right))["margin"] == sum(right) - sum(left)


def test_observed_call_not_consensus(monkeypatch):
    calls = []
    real = p.finite_check
    def observed(task):
        calls.append(deepcopy(task))
        return real(task)
    monkeypatch.setattr(p, "finite_check", observed)
    doc = document(request="verified")
    result = p.evaluate(doc)
    assert calls == []
    assert result["claim_status"] == "UNVERIFIED"
    assert result["protocol_status"] == "REFUSED"
    doc["execute_check"] = True
    result = p.evaluate(doc)
    assert calls == [doc["task"]]
    assert result["claim_status"] == "CHECKED"
    assert result["protocol_status"] == "RECORDED"


def test_false_consensus():
    result = p.evaluate(document(p.inequality([2, 3], [4]), "verified", True))
    assert "stance" in result["agreements"]
    assert result["check"]["status"] == "FAIL"
    assert result["claim_status"] == "CONTRADICTED"
    assert result["protocol_status"] == "REFUSED"


@pytest.mark.parametrize("left,right", [([0], [0]), ([-1], [0]), ([2], [1])])
@pytest.mark.parametrize("action_request", ["record", "verified", "global_authority"])
@pytest.mark.parametrize("execute", [False, True])
def test_request_matrix(left, right, action_request, execute):
    result = p.evaluate(document(p.inequality(left, right), action_request, execute))
    checked = execute and sum(left) <= sum(right)
    assert result["claim_status"] == ("CHECKED" if checked else "CONTRADICTED" if execute else "UNVERIFIED")
    refused = action_request == "global_authority" or (action_request == "verified" and not checked)
    assert (result["refusal"] == "ref<2>") is refused
    assert result["authority_effect"] == "None"


@pytest.mark.parametrize("tag", p.TAGS)
def test_tags_do_not_verify_or_authorize(tag):
    task = p.opaque("unknown", "An unverified interpretation", ["bridge"])
    task["supplied"] = {"bridge": "claimed witness"}
    doc = document(task, "verified", True)
    doc["red"]["tag"] = doc["green"]["tag"] = tag
    result = p.evaluate(doc)
    assert result["frozen"]["red"]["tag"] == tag
    assert result["claim_status"] == "UNVERIFIED"
    assert result["check"]["status"] == "UNBOUND"
    assert result["missing_declared_inputs"] == []
    assert result["supplied_content_validated"] is False
    assert result["authority_effect"] == "None"


def test_disagreement_and_original_preserved():
    doc = document(p.inequality([5], [4]), "verified", True)
    original = deepcopy(doc["task"])
    doc["red"]["revision"] = p.inequality([3], [4])
    doc["red"]["observations"] = ["not established", "not established"]
    doc["green"]["tag"] = "Q-HELD"
    doc["green"]["stance"] = "oppose"
    doc["green"]["observations"] = ["unsupported"]
    result = p.evaluate(doc)
    assert result["frozen"]["task"] == original
    assert result["claim_status"] == "CONTRADICTED"
    assert set(result["disagreements"]) == {"tag", "stance", "observations", "revision"}
    for field in ("tag", "stance", "observations", "revision"):
        assert result["disagreements"][field] == {"red": doc["red"][field], "green": doc["green"][field]}
    assert result["proposal_changes"][0]["new_claim_status"] == "UNVERIFIED"
    assert result["proposal_changes"][0]["changed_fields"] == ["proposition"]
    assert result["role_independence"] == "NOT_ESTABLISHED"
    assert result["semantic_loss"] == "NOT_MEASURED"


def test_frozen_snapshot_and_canonical_key_order():
    doc, raw = frozen()
    kept = deepcopy(doc)
    expected = p.sha(raw)
    reordered = dict(reversed(list(doc["task"].items())))
    assert p.freeze(reordered, doc["red"], doc["green"]) == raw
    result = p.integrate(reordered, raw, expected)
    doc["red"]["observations"].append("mutated after freeze")
    doc["task"]["proposition"]["left"].append(99)
    assert p.sha(raw) == expected
    assert result["frozen"]["task"] == kept["task"]
    assert result["frozen"]["red"] == kept["red"]
    assert p.integrate(kept["task"], raw, expected) == result


def test_frozen_hash_and_task_binding():
    doc, raw = frozen()
    with pytest.raises(p.InvalidInput, match="Frozen bytes"):
        p.integrate(doc["task"], raw, "0" * 64)
    changed_task = deepcopy(doc["task"])
    changed_task["proposition"]["left"] = [6]
    with pytest.raises(p.InvalidInput, match="Frozen task"):
        p.integrate(changed_task, raw, p.sha(raw))
    other = json.loads(raw)
    other["red"]["stance"] = "oppose"
    changed = p.encoded(other)
    with pytest.raises(p.InvalidInput, match="Frozen bytes"):
        p.integrate(doc["task"], changed, p.sha(raw))
    noncanonical = json.dumps(json.loads(raw), indent=2).encode()
    with pytest.raises(p.InvalidInput, match="Noncanonical"):
        p.integrate(doc["task"], noncanonical, p.sha(noncanonical))


def test_canonical_revision_delta():
    task = p.opaque("original", "Unverified original", ["bridge", "proof"])
    doc = document(task)
    doc["green"]["revision"] = p.opaque("revised", "Proposed revision", ["bridge"])
    raw = p.freeze(task, doc["red"], doc["green"])
    first = p.integrate(task, raw, p.sha(raw))
    for order in itertools.permutations(task):
        reordered = {key: task[key] for key in order}
        assert p.freeze(reordered, doc["red"], doc["green"]) == raw
        second = p.integrate(reordered, raw, p.sha(raw))
        assert p.encoded(first) == p.encoded(second)
    assert first["proposal_changes"][0]["changed_fields"] == ["claim_id", "proposition", "requirements"]
    assert first["proposal_changes"][0]["dropped_requirements"] == ["proof"]


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, [], {}, 1000001, -1000001])
def test_invalid_integers(bad):
    with pytest.raises(p.InvalidInput):
        p.validate_task(p.inequality([bad], [1]))


@pytest.mark.parametrize("bad", [None, [], (), {}, [1] * 17, "123"])
def test_invalid_operands(bad):
    with pytest.raises(p.InvalidInput):
        p.validate_task(p.inequality(bad, [1]))


@pytest.mark.parametrize("which,value", [
    ("claim_id", "UPPER"), ("claim_id", ""), ("claim_id", "a" * 49), ("claim_id", True),
    ("proposition", None), ("proposition", {}), ("proposition", {"kind": "unknown", "text": "x"}),
    ("proposition", {"kind": "opaque", "text": ""}), ("proposition", {"kind": "opaque", "text": "x" * 2049}),
    ("requirements", None), ("requirements", ["a"] * 17), ("requirements", ["a", "a"]),
    ("requirements", ["bad name"]), ("supplied", None), ("supplied", {"unrequested": "x"}),
    ("supplied", {"bridge": ""}), ("supplied", {"bridge": False}),
])
def test_invalid_opaque_fields(which, value):
    task = p.opaque("unknown", "claim", ["bridge"])
    task[which] = value
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


def test_finite_external_premises_refused():
    task = p.inequality([0], [1])
    task["requirements"] = ["physical_interpretation"]
    with pytest.raises(p.InvalidInput):
        p.validate_task(task)


@pytest.mark.parametrize("which,value", [
    ("role", "blue"), ("role", "green"), ("task_sha256", "0" * 64),
    ("tag", "CERTIFIED"), ("tag", []), ("stance", "verified"),
    ("observations", "x"), ("observations", ["x"] * 17), ("observations", [""]),
    ("observations", [False]), ("revision", {}), ("revision", False),
])
def test_invalid_role_fields(which, value):
    doc = document()
    doc["red"][which] = value
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)


def test_role_slots_and_task_substitution():
    doc = document()
    with pytest.raises(p.InvalidInput):
        p.freeze(doc["task"], doc["green"], doc["red"])
    with pytest.raises(p.InvalidInput):
        p.freeze(doc["task"], doc["red"], doc["red"])
    doc["task"]["proposition"]["right"] = [8]
    with pytest.raises(p.InvalidInput, match="another task"):
        p.evaluate(doc)


@pytest.mark.parametrize("place", ["root", "task", "red", "green", "proposition"])
@pytest.mark.parametrize("field", ["PASS", "verified", "receipt"])
def test_injected_evidence_fields(place, field):
    doc = document(request="verified")
    target = doc if place == "root" else doc["task"]["proposition"] if place == "proposition" else doc[place]
    target[field] = "PASS"
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)


@pytest.mark.parametrize("value", [None, {}, [], False])
def test_non_document(value):
    with pytest.raises(p.InvalidInput):
        p.evaluate(value)


def test_missing_roles():
    doc = document()
    del doc["red"]
    with pytest.raises(p.InvalidInput):
        p.evaluate(doc)


def test_snapshot_byte_bound():
    task = p.opaque("x", "x" * 2048, [f"a{i}" for i in range(16)])
    task["supplied"] = {x: "x" * 2048 for x in task["requirements"]}
    red = p.role_proposal(task, "red", observations=["x" * 2048] * 16)
    green = p.role_proposal(task, "green", observations=["x" * 2048] * 16)
    with pytest.raises(p.InvalidInput, match="byte limit"):
        p.freeze(task, red, green)


@pytest.mark.parametrize("action_request,execute,digest", [("unknown", False, "0" * 64), ("record", 1, "0" * 64),
    ("record", False, None), ("record", False, "x" * 64), ("record", False, "0" * 63)])
def test_invalid_integration_controls(action_request, execute, digest):
    doc, raw = frozen()
    with pytest.raises(p.InvalidInput):
        p.integrate(doc["task"], raw, digest, action_request, execute)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'NaN', b'Infinity', b'\xff', b'{', b'x' * 65537, b'', None],
                         ids=["duplicate", "nan", "infinity", "utf8", "syntax", "oversize", "empty", "notbytes"])
def test_bad_raw_json(raw):
    with pytest.raises((ValueError, p.InvalidInput)):
        p.decode(raw)


def test_receipts_raw_input_and_no_overwrite(tmp_path, monkeypatch):
    report = p.exercise_report()
    raw = b'  {"kept":"raw spacing"}\r\n'
    fixed = SimpleNamespace(hex="a" * 32)
    monkeypatch.setattr(p, "uuid4", lambda: fixed)
    folder = p.write_run(tmp_path, report, raw, "DEMONSTRATED")
    receipt = json.loads((folder / "receipt.json").read_bytes())
    assert (folder / "input.bin").read_bytes() == raw
    assert set(receipt["artifact_sha256"]) == {"input.bin", "result.json", "summary.md"}
    for name, expected in receipt["artifact_sha256"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["model_calls"] == 0 and receipt["cost_usd"] == "0"
    with pytest.raises(FileExistsError):
        p.write_run(tmp_path, report, raw, "DEMONSTRATED")


def test_main_paths_and_error_codes(tmp_path, capsys):
    assert p.main(["--output-dir", str(tmp_path / "default")]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"
    source = tmp_path / "input.json"
    for doc, expected, code in ((document(execute=True), "RECORDED", 0),
                                (document(request="verified"), "REFUSED", 1),
                                ({}, "REJECTED", 1)):
        raw = json.dumps(doc, indent=2).encode() + b"\r\n"
        source.write_bytes(raw)
        assert p.main(["--input", str(source), "--output-dir", str(tmp_path / expected)]) == code
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == expected
        assert (Path(output["output"]) / "input.bin").read_bytes() == raw
    source.write_bytes(b"{")
    assert p.main(["--input", str(source), "--output-dir", str(tmp_path / "bad")]) == 2
    assert not (tmp_path / "bad").exists()
    assert p.main(["--input", str(tmp_path / "missing")]) == 2
    capsys.readouterr()
    source.write_bytes(b"x" * 65537)
    with pytest.raises(p.InvalidInput):
        p.read_document(source)
    source.write_text("file, not directory")
    assert p.main(["--output-dir", str(source)]) == 2


def test_subprocess_cli(tmp_path):
    output = tmp_path / "subprocess"
    completed = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(output)],
                               capture_output=True, text=True, timeout=30, check=False)
    assert completed.returncode == 0, completed.stderr
    item = json.loads(completed.stdout)
    assert item["status"] == "DEMONSTRATED"
    receipt = json.loads((Path(item["output"]) / "receipt.json").read_bytes())
    assert receipt["model_calls"] == 0


MUTATIONS = (
    ("booleans_are_integers", "type(x) is int and abs(x)", "isinstance(x, int) and abs(x)", "test_invalid_integers"),
    ("strict_inequality", "left <= right else", "left < right else", "test_exact_predicate_against_independent_margin"),
    ("ignore_second_operand", 'sum(proposition["left"])', 'proposition["left"][0]', "test_exact_predicate_against_independent_margin"),
    ("wrong_role", 'proposal["role"] == role', "True", "test_role_slots_and_task_substitution"),
    ("wrong_task", 'proposal["task_sha256"] == digest(task)', "True", "test_role_slots_and_task_substitution"),
    ("no_frozen_hash", "sha(frozen) == expected_sha256", "True", "test_frozen_hash_and_task_binding"),
    ("no_frozen_task", 'encoded(snapshot["task"]) == encoded(task)', "True", "test_frozen_hash_and_task_binding"),
    ("consensus_promotes", '.get(check["status"], "UNVERIFIED")', '.get(check["status"], "CHECKED")', "test_observed_call_not_consensus"),
    ("false_claim_checked", '"FAIL": "CONTRADICTED"', '"FAIL": "CHECKED"', "test_false_consensus"),
    ("global_authority_allowed", 'request == "global_authority" or', "False or", "test_request_matrix"),
    ("observations_not_compared", 'COMPARE_FIELDS = ("tag", "stance", "observations", "revision")',
     'COMPARE_FIELDS = ("tag", "stance", "revision")', "test_disagreement_and_original_preserved"),
    ("green_disagreement_lost", '"green": green[key]', '"green": red[key]', "test_disagreement_and_original_preserved"),
    ("invent_semantic_loss", '"new_claim_status": "UNVERIFIED", "semantic_loss": "NOT_MEASURED"',
     '"new_claim_status": "CHECKED", "semantic_loss": 0', "test_all_source_items_and_controls"),
    ("duplicate_keys", 'require(key not in result, "Duplicate JSON key")', 'require(True, "Duplicate JSON key")', "test_bad_raw_json"),
    ("raw_bytes_lost", '"input.bin": input_bytes', '"input.bin": input_bytes.strip()', "test_receipts_raw_input_and_no_overwrite"),
    ("overwrite_allowed", "exist_ok=False", "exist_ok=True", "test_receipts_raw_input_and_no_overwrite"),
    ("insertion_order_delta", "for key in sorted(task) if", "for key in task if", "test_canonical_revision_delta"),
)


def test_implementation_mutations(tmp_path):
    source = PILOT_FILE.read_text(encoding="utf-8")
    original_hash = hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    rows = []
    for name, anchor, replacement, test_name in MUTATIONS:
        assert source.count(anchor) == 1, name
        mutant = tmp_path / name / "run.py"
        mutant.parent.mkdir()
        mutant.write_text(source.replace(anchor, replacement, 1), encoding="utf-8")
        environment = dict(os.environ, PFP_PILOT_000010_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_PILOT_000010_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            environment.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "-p", "no:cacheprovider", "--import-mode=importlib",
             "--basetemp=" + str(tmp_path / (name + "_temp"))],
            env=environment, capture_output=True, text=True, timeout=60, check=False)
        failed = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert completed.returncode == 1 and failed, (name, completed.stdout, completed.stderr)
        assert hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest() == original_hash
        rows.append({"name": name, "anchor": anchor, "replacement": replacement, "target": str(PILOT_FILE),
                     "applied": True, "exit_code": completed.returncode, "failed_nodes": failed,
                     "original_unchanged": True, "original_sha256": original_hash,
                     "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest()})
    if output := os.environ.get("PFP_PILOT_000010_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(rows, indent=2), encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert p.OUTPUT_ROOT == PILOT_FILE.resolve().parent.parent / "pilot_output" / p.PILOT_ID


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    report = p.exercise_report()
    assert [row["verdict"] for row in report["exercises"]] == ["MATCH"] * 9
    monkeypatch.setitem(p.EXPECTED_OUTCOMES, "P10.3", ("RECORDED", "UNVERIFIED"))
    mismatched = p.exercise_report()
    assert [row["id"] for row in mismatched["exercises"] if row["verdict"] == "MISMATCH"] == ["P10.3"]
    assert p.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"
