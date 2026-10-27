import hashlib
import importlib.util
import itertools
import json
import os
import runpy
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

PILOT_FILE = Path(os.environ.get("PFP_CHAIN_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_chain_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def test_four_exercise_obligations():
    cases = pilot.exercise_report()["cases"]
    assert set(cases) == {f"quiz17.{i}" for i in range(1, 5)}
    scalar = cases["quiz17.1"]
    assert scalar["chain_law"] and scalar["target_closed"]
    assert not scalar["integer_boundary"] and scalar["integer_witness"] is None
    assert scalar["integer_H1"] == "Z/2Z"
    assert scalar["rational_H1"] == "0" and scalar["rational_H0"] == "Q"
    assert not scalar["rational_complex_acyclic"]
    assert not cases["quiz17.2"]["Z"]["submission_accepted"]
    assert cases["quiz17.2"]["Q"]["submission_accepted"]
    assert not cases["quiz17.2"]["Q"]["original_integer_problem_solved"]
    assert not cases["quiz17.2"]["Q"]["carrier_change_authorized"]
    minimum = cases["quiz17.3"]["certificate"]
    assert minimum["submission_accepted"] and minimum["complete_minimizers"]
    assert minimum["expected"]["minimizers"] == [0, 1]
    assert minimum["expected"]["signed_residuals"] == [1, -1]
    assert not cases["quiz17.3"]["mean_solves_integer_problem"]
    assert not cases["quiz17.3"]["repair_applied"]
    triangle = cases["quiz17.4"]
    assert triangle["hollow"]["integer_H1"] == "Z" and not triangle["hollow"]["target_is_boundary"]
    assert triangle["filled"]["integer_H1"] == "0" and triangle["filled"]["boundary_witness"] == [1]
    assert not triangle["face_admission_inferred_from_edges"]


@pytest.mark.parametrize("m", [-7, -2, -1, 1, 2, 7])
def test_scalar_finite_grid_against_independent_enumeration(m):
    for z in range(-21, 22):
        problem = {"kind": "scalar", "multiplier": m, "target": z}
        report = pilot.scalar_report(problem)
        values = {c: abs(z - m * c) for c in range(-30, 31)}
        best = min(values.values())
        expected = sorted(c for c, value in values.items() if value == best)
        minimum = report["minimum"]
        assert minimum["min_abs"] == best and minimum["minimizers"] == expected
        assert report["integer_boundary"] == any(m * c == z for c in values)
        assert Fraction(*report["rational_witness"]) * m == z
        proposal = {"min_abs": best, "minimizers": expected[::-1]}
        assert pilot.scalar_check(problem, proposal)["submission_accepted"]
        if report["integer_boundary"]:
            assert m * report["integer_witness"] == z


def test_large_values_need_no_bounded_search():
    for m, z in [(1, 10**9), (-1, 10**9), (10**9, 1), (-10**9, -1), (10**9, 500000000)]:
        result = pilot.scalar_report({"kind": "scalar", "multiplier": m, "target": z})
        low = result["minimum"]
        assert all(abs(z - m * c) == low["min_abs"] for c in low["minimizers"])
    assert pilot.scalar_report({"kind": "scalar", "multiplier": 10**9, "target": 500000000})["minimum"]["minimizers"] == [0, 1]


@pytest.mark.parametrize("min_abs,candidates", [(1, [0]), (1, [1]), (1, [0, 0]), (1, [1, 2]), (0, [0, 1]), (2, [0, 1])])
def test_incomplete_or_fabricated_minima_rejected(min_abs, candidates):
    assert not pilot.scalar_check(pilot.default_problem(), {"min_abs": min_abs, "minimizers": candidates})["submission_accepted"]


@pytest.mark.parametrize("carrier,witness,accepted,admitted", [
    ("Z", [1, 2], False, False), ("Q", [1, 2], True, True),
    ("Z", [0, 1], False, True), ("Q", [2, 3], False, True),
])
def test_witness_domain_and_equality(carrier, witness, accepted, admitted):
    result = pilot.scalar_check(pilot.default_problem(), {"carrier": carrier, "witness": witness})
    assert result["submission_accepted"] is accepted
    assert result["coefficient_admitted"] is admitted
    integral = pilot.scalar_check({"kind": "scalar", "multiplier": 2, "target": 4}, {"carrier": carrier, "witness": [2, 1]})
    assert integral["original_integer_problem_solved"] and integral["submission_accepted"]


@pytest.mark.parametrize("k,t", list(itertools.product([-3, -1, 0, 1, 2], [-4, 0, 1, 3])))
def test_triangle_multiples_and_real_boundary_witness(k, t):
    problem = pilot.triangle_problem(True)
    problem["d2"] = [[k], [-k], [k]]
    problem["target"] = [t, -t, t]
    result = pilot.triangle_check(problem, pilot.triangle_proof())
    assert result["submission_accepted"]
    assert result["integer_H1"] == ("Z" if k == 0 else ("0" if abs(k) == 1 else f"Z/{abs(k)}Z"))
    expected = t == 0 if k == 0 else t % k == 0
    assert result["target_is_boundary"] is expected
    if expected:
        assert [row[0] * result["boundary_witness"][0] for row in problem["d2"]] == problem["target"]
    else:
        assert result["boundary_witness"] is None


def test_zero_target_and_orientation_transport():
    for signs in itertools.product((-1, 1), repeat=3):
        problem = pilot.triangle_problem(True)
        proof = pilot.triangle_proof()
        problem["d1"] = [[x * signs[j] for j, x in enumerate(row)] for row in problem["d1"]]
        problem["d2"] = [[row[0] * signs[i]] for i, row in enumerate(problem["d2"])]
        problem["target"] = [x * s for x, s in zip(problem["target"], signs, strict=True)]
        proof["generator"] = [x * s for x, s in zip(proof["generator"], signs, strict=True)]
        proof["coordinate"] = [x * s for x, s in zip(proof["coordinate"], signs, strict=True)]
        proof["factor"] = [[x * signs[i] for x in row] for i, row in enumerate(proof["factor"])]
        assert pilot.triangle_check(problem, proof)["integer_H1"] == "0"
    hollow = pilot.triangle_problem(False)
    hollow["target"] = [0, 0, 0]
    report = pilot.triangle_check(hollow, pilot.triangle_proof())
    assert report["target_is_boundary"] and report["boundary_witness"] == []


def test_false_kernel_certificate_not_just_one_boundary_witness():
    problem = pilot.triangle_problem(True)
    problem["d1"] = [[0, 0, 0] for _ in range(3)]
    result = pilot.triangle_check(problem, pilot.triangle_proof())
    assert result["checks"]["chain_law"] and result["checks"]["generator_closed"]
    assert not result["checks"]["kernel_identity"]
    assert not result["submission_accepted"] and result["integer_H1"] is None
    assert result["target_is_boundary"] is None


@pytest.mark.parametrize("field,index,value", [
    ("d1", (0, 0), 1), ("d2", (0, 0), -1), ("target", (0,), 2),
    ("generator", (0,), 2), ("coordinate", (0,), 2), ("factor", (1, 0), 1),
])
def test_mutated_matrix_certificates_are_rejected(field, index, value):
    problem, proof = pilot.triangle_problem(True), pilot.triangle_proof()
    container = problem if field in problem else proof
    node = container[field]
    for i in index[:-1]:
        node = node[i]
    node[index[-1]] = value
    result = pilot.triangle_check(problem, proof)
    assert not result["submission_accepted"] and result["integer_H1"] is None


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, [], {}, 10**9 + 1, -10**9 - 1])
def test_integer_types_and_bounds(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.integer(bad)


@pytest.mark.parametrize("bad", [
    None, [], {}, {"kind": "triangle", "multiplier": 2, "target": 1},
    {"kind": "scalar", "multiplier": 0, "target": 1},
    {"kind": "scalar", "multiplier": True, "target": 1},
    {"kind": "scalar", "multiplier": 2, "target": 1, "verified": True},
])
def test_bad_scalar_problem(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.scalar_report(bad)


@pytest.mark.parametrize("bad", [
    None, [], {}, {"min_abs": -1, "minimizers": [0]}, {"min_abs": 1, "minimizers": []},
    {"min_abs": 1, "minimizers": [0, 1, 2]}, {"min_abs": 1, "minimizers": "01"},
    {"min_abs": 1, "minimizers": [True]}, {"carrier": "R", "witness": [1, 2]},
    {"carrier": "Q", "witness": [1, 0]}, {"carrier": "Q", "witness": [2, 4]},
    {"carrier": "Q", "witness": [1, -2]}, {"carrier": "Q", "witness": [1.0, 2]},
    {"carrier": "Q", "witness": [1]}, {"carrier": "Q", "witness": [1, 2], "verified": True},
])
def test_bad_scalar_proposal(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.scalar_check(pilot.default_problem(), bad)


@pytest.mark.parametrize("which,key,bad", [
    ("problem", "kind", "other"), ("problem", "d1", []), ("problem", "d1", [[0]] * 3),
    ("problem", "d2", []), ("problem", "d2", [0, 0, 0]), ("problem", "d2", [[0, 0]] * 3),
    ("problem", "d2", [[], [1], []]), ("problem", "target", [True, 0, 0]),
    ("proof", "generator", [1, 2]), ("proof", "coordinate", [1, 0, 0.0]),
    ("proof", "factor", [[0, 0, 0], None, [0, 0, 0]]),
])
def test_bad_triangle_intake(which, key, bad):
    problem, proof = pilot.triangle_problem(True), pilot.triangle_proof()
    (problem if which == "problem" else proof)[key] = bad
    with pytest.raises(pilot.InvalidInput):
        pilot.triangle_check(problem, proof)
    with pytest.raises(pilot.InvalidInput):
        pilot.triangle_problem(1)


def test_main_routes_custody_and_no_overwrite(tmp_path, capsys):
    root = tmp_path / "runs"
    args = ["--output-dir", str(root)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    result = json.loads(before["result.json"])
    receipt = json.loads(before["receipt.json"])
    assert receipt["result_sha256"] == pilot.digest(result)
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["network_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["result_sha256"] in before["summary.md"].decode()
    problem, proposal = tmp_path / "problem.json", tmp_path / "proposal.json"
    raw_input = json.dumps(pilot.triangle_problem(True), indent=3).encode() + b"\r\n"
    raw_proposal = json.dumps(pilot.triangle_proof(), indent=4).encode() + b"\r\n"
    problem.write_bytes(raw_input)
    proposal.write_bytes(raw_proposal)
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(proposal)]) == 0
    current = Path(json.loads(capsys.readouterr().out)["output"])
    cert = json.loads((current / "receipt.json").read_text())
    assert (current / "input.json").read_bytes() == raw_input
    assert (current / "proposal.json").read_bytes() == raw_proposal
    assert cert["input_sha256"] == hashlib.sha256(raw_input).hexdigest()
    assert cert["proposal_sha256"] == hashlib.sha256(raw_proposal).hexdigest()
    assert cert["status"] == "ACCEPTED"
    proposal.write_text(json.dumps({"carrier": "Z", "witness": [1, 2]}))
    assert pilot.main(args + ["--proposal", str(proposal)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    proposal.write_text(json.dumps({"carrier": "Q", "witness": [1, 2]}))
    assert pilot.main(args + ["--proposal", str(proposal)]) == 0
    capsys.readouterr()
    assert pilot.main(args + ["--input", str(problem)]) == 2
    capsys.readouterr()
    problem.write_text('{"kind":"unknown"}')
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(proposal)]) == 2
    capsys.readouterr()
    blocked = tmp_path / "not_a_folder"
    blocked.write_text("preserve")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_text() == "preserve"
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}


@pytest.mark.parametrize("raw", [
    b'{"x":0,"x":1}', b'{"x":{"y":0,"y":1}}', b'NaN', b'Infinity', b'-Infinity',
    b'\xff', b"{" , b" " * 65537, b"[" * 7000 + b"0" + b"]" * 7000,
], ids=["duplicate", "nested_duplicate", "nan", "infinity", "negative_infinity", "invalid_utf8", "truncated", "oversize", "deep"])
def test_strict_json_refusals(tmp_path, capsys, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    root = tmp_path / "runs"
    assert pilot.main(["--proposal", str(path), "--output-dir", str(root)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not root.exists()
    path.unlink()
    assert pilot.main(["--proposal", str(path), "--output-dir", str(root)]) == 2


def test_real_cli(tmp_path):
    result = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                            capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 0, result.stderr
    folder = Path(json.loads(result.stdout)["output"])
    assert json.loads((folder / "result.json").read_text())["cases"]["quiz17.1"]["integer_H1"] == "Z/2Z"


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("chain_law_as_exactness", '"integer_boundary": r == 0', '"integer_boundary": True', "test_four_exercise_obligations"),
        ("coerce_rational_to_integer", 'admitted = proposal["carrier"] == "Q" or d == 1', "admitted = True", "test_witness_domain_and_equality"),
        ("drop_tied_minimizer", '"minimizers": minimizers,', '"minimizers": minimizers[:1],', "test_scalar_finite_grid_against_independent_enumeration"),
        ("ignore_kernel_identity", "accepted = all(checks.values())", 'accepted = all(v for k, v in checks.items() if k != "kernel_identity")', "test_false_kernel_certificate_not_just_one_boundary_witness"),
        ("auto_fill_triangle", '"d2": [[1], [-1], [1]] if filled else [[], [], []]', '"d2": [[1], [-1], [1]]', "test_four_exercise_obligations"),
        ("accept_bool", "type(value) is int and abs(value)", "isinstance(value, int) and abs(value)", "test_integer_types_and_bounds"),
    ]
    evidence = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "nonunique anchor")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_CHAIN_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_CHAIN_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
            env=env, capture_output=True, text=True, check=False, timeout=40)
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        evidence.append({
            "name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
            "applied": mutant.read_text(encoding="utf-8") == source.replace(anchor, replacement),
            "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest(),
            "failed_nodes": failures, "exit_code": completed.returncode,
            "original_unchanged": PILOT_FILE.read_bytes() == original,
            "original_sha256": hashlib.sha256(original).hexdigest(),
        })
    assert len(evidence) == 6
    if output := os.environ.get("PFP_CHAIN_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
