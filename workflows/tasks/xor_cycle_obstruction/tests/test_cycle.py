"""Positive, hostile-input, exhaustive, CLI and implementation-mutation tests."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

PILOT_FILE = Path(os.environ.get("PFP_PILOT_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
SPEC = importlib.util.spec_from_file_location("pilot_0000026_under_test", PILOT_FILE)
assert SPEC is not None and SPEC.loader is not None
pilot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pilot
SPEC.loader.exec_module(pilot)


def test_original_four_cases():
    report = pilot.analyze(pilot.default_problem())
    assert tuple(report["cases"]) == pilot.CASE_IDS
    assert report["checked_edge_ids"] == ["ab", "bc", "ca"]
    assert report["cases"]["quiz16.1"] == {
        "local_witnesses": [
            {"edge_id": "ab", "assignment": {"a": 0, "b": 1}},
            {"edge_id": "bc", "assignment": {"b": 0, "c": 1}},
            {"edge_id": "ca", "assignment": {"c": 0, "a": 1}},
        ],
        "conflicting_vertices": ["a", "b", "c"],
    }
    assert report["cases"]["quiz16.2"] == {
        "cycle_sum": 1, "summed_lhs_coefficients": {"a": 0, "b": 0, "c": 0},
        "assignments_checked": 8, "solutions": [],
    }
    assert report["cases"]["quiz16.3"]["cost"] == 1
    repairs = report["cases"]["quiz16.3"]["repairs"]
    assert [r["changed_edges"] for r in repairs] == [["ab"], ["bc"], ["ca"]]
    expected = [
        [{"a": 0, "b": 0, "c": 1}, {"a": 1, "b": 1, "c": 0}],
        [{"a": 0, "b": 1, "c": 1}, {"a": 1, "b": 0, "c": 0}],
        [{"a": 0, "b": 1, "c": 0}, {"a": 1, "b": 0, "c": 1}],
    ]
    assert [r["solutions"] for r in repairs] == expected
    assert [r["solutions_with_first_vertex_zero"] for r in repairs] == [[r[0]] for r in expected]
    assert report["cases"]["quiz16.4"]["cycle_sum"] == 1
    assert report["cases"]["quiz16.4"]["solution_count"] == 0
    assert report["cases"]["quiz16.4"]["is_repair"] is False
    assert report["cost_usd"] == "0" and report["kind"] == "NO_LLM"


@pytest.mark.parametrize("rhs", itertools.product((0, 1), repeat=3))
def test_all_rhs_against_independent_parity_and_assignments(rhs):
    payload = pilot.default_problem().payload()
    for edge, value in zip(payload["edges"], rhs, strict=True):
        edge["rhs"] = value
    problem = pilot.parse_problem(payload)
    # Independently derived: x_b=x_a+r_ab; x_c=x_b+r_bc, then test the final equation.
    expected = []
    for a in (0, 1):
        b, c = a ^ rhs[0], a ^ rhs[0] ^ rhs[1]
        if c ^ a == rhs[2]:
            expected.append({"a": a, "b": b, "c": c})
    assert pilot.solutions(problem) == expected
    assert bool(expected) == (sum(rhs) % 2 == 0)
    repairs = pilot.minimum_repairs(problem)
    assert repairs["cost"] == (sum(rhs) % 2)
    if expected:
        assert repairs["repairs"] == [{"changed_edges": [], "solutions": expected}]
    else:
        assert len(repairs["repairs"]) == 3
    for vector in itertools.product((0, 1), repeat=3):
        assignment = dict(zip(("a", "b", "c"), vector, strict=True))
        expected_valid = tuple(vector) in [tuple(r.values()) for r in expected]
        assert pilot.assignment_valid(problem, assignment) is expected_valid


@pytest.mark.parametrize("labels", itertools.permutations(("x", "y", "z")))
def test_faithful_relabel_and_edge_order(labels):
    original = pilot.default_problem()
    renamed = pilot.relabel(original, dict(zip(original.vertices, labels, strict=True)))
    assert pilot.cycle_sum(renamed) == pilot.cycle_sum(original)
    assert pilot.solutions(renamed) == []
    payload = renamed.payload()
    payload["edges"].reverse()
    assert pilot.parse_problem(payload).payload() == renamed.payload()


BAD_PAYLOADS = [
    None, [], {}, {"vertices": [], "edges": [], "extra": 1},
    {"vertices": "abc", "edges": []}, {"vertices": ["a", "b", "c"], "edges": {}},
]


@pytest.mark.parametrize("bad", BAD_PAYLOADS)
def test_problem_shape_rejected(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.parse_problem(bad)


@pytest.mark.parametrize("mutation", [
    lambda p: p["vertices"].pop(),
    lambda p: p["vertices"].__setitem__(0, "b"),
    lambda p: p["vertices"].__setitem__(0, ""),
    lambda p: p["vertices"].__setitem__(0, " a"),
    lambda p: p["vertices"].__setitem__(0, 4),
    lambda p: p["edges"].pop(),
    lambda p: p["edges"].__setitem__(2, p["edges"][0]),
    lambda p: p["edges"][0].__setitem__("edge_id", "foreign"),
    lambda p: p["edges"][0].__setitem__("edge_id", []),
    lambda p: p["edges"][0].__setitem__("source", "c"),
    lambda p: p["edges"][0].__setitem__("target", "d"),
    lambda p: p["edges"][0].__setitem__("rhs", True),
    lambda p: p["edges"][0].__setitem__("rhs", 1.0),
    lambda p: p["edges"][0].__setitem__("rhs", "1"),
    lambda p: p["edges"][0].__setitem__("rhs", -1),
    lambda p: p["edges"][0].__setitem__("rhs", 2),
    lambda p: p["edges"][0].__setitem__("cost", 1),
    lambda p: p["edges"].__setitem__(0, None),
])
def test_malformed_carrier_mutations(mutation):
    payload = pilot.default_problem().payload()
    mutation(payload)
    with pytest.raises(pilot.InvalidInput):
        pilot.parse_problem(payload)


def test_dataclasses_do_not_accept_mutable_or_untyped_storage():
    problem = pilot.default_problem()
    with pytest.raises(pilot.InvalidInput):
        pilot.Problem(list(problem.vertices), problem.edges)
    with pytest.raises(pilot.InvalidInput):
        pilot.Problem(problem.vertices, list(problem.edges))
    with pytest.raises(pilot.InvalidInput):
        pilot.Problem(problem.vertices, ({}, {}, {}))
    with pytest.raises(pilot.InvalidInput):
        pilot.Problem(problem.vertices, (pilot.Edge([], "a", "b", 1),) + problem.edges[1:])


@pytest.mark.parametrize("bad", [None, [], {}, {"a": 0, "b": 1, "d": 0}, {"a": 0, "b": True, "c": 0}])
def test_bad_assignments(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.assignment_valid(pilot.default_problem(), bad)


@pytest.mark.parametrize("bad", [[], {"d": 0}, {"a": True}, {"a": 2}])
def test_bad_pins(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.solutions(pilot.default_problem(), bad)


@pytest.mark.parametrize("bad", [[], {}, {"a": "x", "b": "x", "c": "z"}])
def test_bad_relabelings(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.relabel(pilot.default_problem(), bad)


def test_host_recomputes_candidate_including_boolean_types():
    problem = pilot.default_problem()
    correct = pilot.analyze(problem)
    assert pilot.grade(problem, correct)
    candidates = []
    wrong = copy.deepcopy(correct)
    wrong["checked_edge_ids"] = ["ab", "bc"]
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["cases"]["quiz16.3"]["repairs"] = wrong["cases"]["quiz16.3"]["repairs"][-1:]
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["cases"]["quiz16.2"]["cycle_sum"] = True
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["problem_sha256"] = "0" * 64
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["cases"]["quiz16.1"]["local_witnesses"][0]["assignment"]["b"] = 0
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["cases"]["quiz16.4"]["is_repair"] = True
    candidates.append(wrong)
    wrong = copy.deepcopy(correct)
    wrong["authority_effect"] = "ApplyRepair"
    candidates.append(wrong)
    candidates += [None, {"verified": True}, "obstruction refusal certified", {}]
    assert all(not pilot.grade(problem, candidate) for candidate in candidates)


def test_receipt_no_overwrite_and_shared_result_digest(tmp_path):
    report = pilot.analyze(pilot.default_problem())
    first = pilot.write_run(tmp_path, report, None)
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    second = pilot.write_run(tmp_path, report, True)
    assert first != second
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}
    receipt = json.loads((first / "receipt.json").read_text())
    result = json.loads((first / "result.json").read_text())
    assert receipt["result_sha256"] == pilot.digest(result)
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["network_calls"] == 0
    assert receipt["result_sha256"] in (first / "summary.md").read_text()
    assert json.loads((second / "receipt.json").read_text())["status"] == "ACCEPTED"


def test_main_all_routes(tmp_path, capsys):
    out = tmp_path / "output"
    assert pilot.main(["--output-dir", str(out)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "COMPUTED"
    problem_file = tmp_path / "input.json"
    problem_file.write_text(json.dumps(pilot.default_problem().payload()))
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps(pilot.analyze(pilot.default_problem())))
    args = ["--input", str(problem_file), "--proposal", str(proposal), "--output-dir", str(out)]
    assert pilot.main(args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ACCEPTED"
    proposal.write_text('{"verified": true}')
    assert pilot.main(args) == 1
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["status"] == "REJECTED"
    assert json.loads((Path(rejected["output"]) / "receipt.json").read_text())["status"] == "REJECTED"
    proposal.write_text("{")
    assert pilot.main(args) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    proposal.unlink()
    assert pilot.main(args) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    problem_file.write_text("{}")
    assert pilot.main(["--input", str(problem_file), "--output-dir", str(out)]) == 2
    capsys.readouterr()
    blocked = tmp_path / "not_a_directory"
    blocked.write_text("existing bytes")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert blocked.read_text() == "existing bytes"


def test_real_cli(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    result = json.loads((Path(payload["output"]) / "result.json").read_text())
    assert result["report"]["cases"]["quiz16.2"]["solutions"] == []
    assert len(result["report"]["cases"]["quiz16.3"]["repairs"]) == 3


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"


@pytest.mark.parametrize("raw", [
    b'{"rhs":0,"rhs":1}', b'{"outer":{"x":0,"x":1}}',
    b'{"value":NaN}', b'{"value":Infinity}', b'{"value":-Infinity}',
    b'\xff', b' ' * 65537,
], ids=["duplicate", "nested_duplicate", "nan", "infinity", "negative_infinity", "invalid_utf8", "oversized"])
def test_ambiguous_or_non_json_bytes_are_refused(tmp_path, capsys, raw):
    document = tmp_path / "bad.json"
    document.write_bytes(raw)
    for flag in ("--input", "--proposal"):
        assert pilot.main([flag, str(document), "--output-dir", str(tmp_path / "runs")]) == 2
        assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not (tmp_path / "runs").exists()


def test_raw_input_and_rejected_candidate_are_retained(tmp_path, capsys):
    problem = tmp_path / "input.json"
    raw_problem = (json.dumps(pilot.default_problem().payload(), indent=3) + "\r\n").encode()
    problem.write_bytes(raw_problem)
    proposal = tmp_path / "candidate.json"
    raw_proposal = b'{ "verified" : true }\r\n'
    proposal.write_bytes(raw_proposal)
    assert pilot.main([
        "--input", str(problem), "--proposal", str(proposal),
        "--output-dir", str(tmp_path / "runs"),
    ]) == 1
    run = Path(json.loads(capsys.readouterr().out)["output"])
    problem.write_bytes(b"overwritten source")
    proposal.write_bytes(b"overwritten source")
    assert (run / "input.json").read_bytes() == raw_problem
    assert (run / "proposal.json").read_bytes() == raw_proposal
    receipt = json.loads((run / "receipt.json").read_text())
    assert receipt["input_origin"] == "submitted"
    assert receipt["input_sha256"] == hashlib.sha256(raw_problem).hexdigest()
    assert receipt["proposal_sha256"] == hashlib.sha256(raw_proposal).hexdigest()
    retained_problem, _ = pilot.read_document(run / "input.json")
    retained_proposal, _ = pilot.read_document(run / "proposal.json")
    assert not pilot.grade(pilot.parse_problem(retained_problem), retained_proposal)


def test_deep_json_returns_controlled_refusal(tmp_path, capsys):
    proposal = tmp_path / "deep.json"
    proposal.write_text("[" * 7000 + "0" + "]" * 7000)
    # Python 3.14 parses this depth without RecursionError, so the document reaches
    # validation and is rejected there. Either outcome is a controlled refusal.
    code = pilot.main(["--proposal", str(proposal), "--output-dir", str(tmp_path / "runs")])
    status = json.loads(capsys.readouterr().out)["status"]
    assert (code, status) in ((2, "REFUSED"), (1, "REJECTED"))
    if code == 2:
        assert not (tmp_path / "runs").exists()


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    text = original.decode("utf-8")
    mutations = [
        ("omit_third_edge", "for edge in problem.edges\n", "for edge in problem.edges[:2]\n",
         "test_all_rhs_against_independent_parity_and_assignments"),
        ("discard_tied_repairs", "for edge_id in EDGE_IDS:\n", "for edge_id in EDGE_IDS[-1:]:\n",
         "test_original_four_cases"),
        ("accept_bool_as_bit", "type(value) is int and value in (0, 1)", "isinstance(value, int) and value in (0, 1)",
         "test_malformed_carrier_mutations"),
        ("trust_model_verified_flag", "return canonical(proposal) == canonical(analyze(problem))",
         "return True", "test_host_recomputes_candidate_including_boolean_types"),
    ]
    observations = []
    for name, anchor, replacement, test_name in mutations:
        assert text.count(anchor) == 1, (name, "nonunique mutation anchor")
        mutated = tmp_path / (name + ".py")
        mutated.write_text(text.replace(anchor, replacement), encoding="utf-8")
        environment = dict(os.environ, PFP_PILOT_UNDER_TEST=str(mutated), NO_COLOR="1")
        for variable in ("PFP_PILOT_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            environment.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib",
             "--basetemp", str(tmp_path / name)],
            env=environment, capture_output=True, text=True, check=False, timeout=40,
        )
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        observations.append({
            "name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
            "applied": mutated.read_text(encoding="utf-8") == text.replace(anchor, replacement),
            "mutant_sha256": hashlib.sha256(mutated.read_bytes()).hexdigest(),
            "failed_nodes": failures, "exit_code": completed.returncode,
            "original_unchanged": PILOT_FILE.read_bytes() == original,
            "original_sha256": hashlib.sha256(original).hexdigest(),
        })
    assert len(observations) == 4
    if output := os.environ.get("PFP_PILOT_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
