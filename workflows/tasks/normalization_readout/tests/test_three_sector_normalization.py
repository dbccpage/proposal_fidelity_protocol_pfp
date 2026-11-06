import hashlib
import importlib.util
import itertools
import json
import os
import runpy
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

PILOT_FILE = Path(os.environ.get("PFP_NORMALIZATION_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_normalization_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def proposal():
    return {"total": 3, "probabilities": [[2, 3], [1, 3], [0, 1]], "lift_radicands": [[2, 3], [1, 3], [0, 1]]}


def amplitude_problem(assumption=pilot.BORN_ASSUMPTION):
    return {"kind": "amplitudes", "amplitudes": [[3, 5], [4, 5], [0, 1]], "assumption": assumption}


def test_four_numbered_cases():
    cases = pilot.exercise_report()["cases"]
    assert set(cases) == {f"quiz07.{i}" for i in range(1, 5)}
    assert cases["quiz07.1"]["total"] == 3
    assert cases["quiz07.1"]["probabilities"] == [[2, 3], [1, 3], [0, 1]]
    assert cases["quiz07.2"]["submission_accepted"] and all(cases["quiz07.2"]["checks"].values())
    comparison = cases["quiz07.3"]
    assert comparison["simplex"]["result"] == comparison["square_root"]["result"] == [[2, 3], [1, 3], [0, 1]]
    assert comparison["coordinates_where_sqrt_p_differs_from_p"] == [0, 1]
    assert comparison["same_probability_readout"] and comparison["born_uniqueness"] == "NOT_ESTABLISHED"
    admitted = cases["quiz07.4"]["with_assumption"]
    missing = cases["quiz07.4"]["without_assumption"]
    assert admitted["probabilities"] == [[9, 25], [16, 25], [0, 1]]
    assert admitted["squared_norm"] == [1, 1] and admitted["probability_interpretation"] == "EXTERNALLY_ASSUMED"
    assert not admitted["born_rule_derived"] and admitted["authority_effect"] == "None"
    assert missing["probabilities"] is None and missing["probability_interpretation"] == "NOT_SUPPLIED"
    assert missing["squared_components"] == admitted["squared_components"]


def test_999_weight_triples_and_positive_rescaling():
    for triple in itertools.product(range(10), repeat=3):
        if sum(triple) == 0:
            continue
        result = pilot.normalize({"kind": "weights", "weights": list(triple)})
        p = [F(*v) for v in result["probabilities"]]
        assert result["total"] == sum(triple) and sum(p) == 1 and all(v >= 0 for v in p)
        assert [v * sum(triple) for v in p] == list(triple)
        scaled = pilot.normalize({"kind": "weights", "weights": [7*w for w in triple]})
        assert scaled["probabilities"] == result["probabilities"]
        assert [r["nonnegative_sqrt_of"] for r in result["square_root_lift"]] == result["probabilities"]
        proposed = {"total": sum(triple), "probabilities": result["probabilities"], "lift_radicands": result["probabilities"]}
        assert pilot.check_lift(result["problem"], proposed)["submission_accepted"]


def test_permutation_zero_sectors_and_maximum_components():
    for triple in itertools.permutations([2, 1, 0]):
        result = pilot.normalize({"kind": "weights", "weights": list(triple)})
        assert result["probabilities"] == [pilot.wire(F(w, 3)) for w in triple]
    problem = {"kind": "weights", "weights": [10**9, 10**9-1, 10**9-2]}
    result = pilot.normalize(problem)
    assert max(v[1] for v in result["probabilities"]) > 10**9
    valid = {"total": result["total"], "probabilities": result["probabilities"], "lift_radicands": result["probabilities"]}
    assert pilot.check_lift(problem, valid)["submission_accepted"]
    trivial = pilot.representation_comparison({"kind": "weights", "weights": [1, 0, 0]})
    assert trivial["coordinates_where_sqrt_p_differs_from_p"] == []
    assert trivial["born_uniqueness"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("weights", [[-1, 2, 0], [2, -1, 0], [2, 0, -1], [0, 0, 0],
                                     [True, 1, 0], [1.0, 1, 0], [10**9+1, 0, 0],
                                     [1, 2], [1, 2, 3, 4], [], None, "210"])
def test_invalid_weights(weights):
    with pytest.raises(pilot.InvalidInput):
        pilot.normalize({"kind": "weights", "weights": weights})


@pytest.mark.parametrize("change", [
    lambda p: p.update(total=2),
    lambda p: p.update(probabilities=[[4, 5], [1, 5], [0, 1]]),
    lambda p: p.update(lift_radicands=[[1, 3], [2, 3], [0, 1]]),
    lambda p: p.update(probabilities=[[1, 3], [2, 3], [0, 1]], lift_radicands=[[1, 3], [2, 3], [0, 1]]),
    lambda p: p.update(lift_radicands=[[-1, 1], [2, 1], [0, 1]]),
])
def test_false_lift_certificates(change):
    candidate = proposal()
    change(candidate)
    result = pilot.check_lift(pilot.default_problem(), candidate)
    assert not result["submission_accepted"]


@pytest.mark.parametrize("change", [
    lambda p: p.update(total=True), lambda p: p.update(total=3*10**9+1),
    lambda p: p.update(probabilities=[[2, 3], [1, 3]]),
    lambda p: p.update(lift_radicands=[[2, 6], [1, 3], [0, 1]]),
    lambda p: p.update(lift_radicands=[[3*10**18+1, 1], [0, 1], [0, 1]]),
    lambda p: p.update(derived=True), lambda p: p.pop("total"),
])
def test_malformed_certificate(change):
    candidate = proposal()
    change(candidate)
    with pytest.raises(pilot.InvalidInput):
        pilot.check_lift(pilot.default_problem(), candidate)


def test_problem_bound_not_just_sum_one():
    original = pilot.check_lift(pilot.default_problem(), proposal())
    changed = {"kind": "weights", "weights": [1, 2, 0]}
    other = pilot.check_lift(changed, proposal())
    assert original["submission_accepted"] and not other["submission_accepted"]
    assert original["problem_sha256"] != other["problem_sha256"]


@pytest.mark.parametrize("amplitudes", [[[3, 5], [4, 5], [0, 1]], [[-3, 5], [4, 5], [0, 1]],
                                      [[0, 1], [-1, 1], [0, 1]], [[1, 3], [2, 3], [-2, 3]]])
def test_signed_normalized_amplitudes(amplitudes):
    problem = dict(amplitude_problem(), amplitudes=amplitudes)
    result = pilot.amplitude_readout(problem)
    expected = [F(*v)**2 for v in amplitudes]
    assert sum(expected) == 1
    assert result["probabilities"] == [pilot.wire(v) for v in expected]
    assert pilot.check_proposal(problem, {"probabilities": result["probabilities"]})["submission_accepted"]
    arithmetic = pilot.amplitude_readout(dict(problem, assumption=None))
    assert arithmetic["squared_components"] == result["probabilities"]
    assert arithmetic["probabilities"] is None


@pytest.mark.parametrize("amplitudes", [[[1, 2], [1, 2], [0, 1]], [[1, 1], [1, 1], [0, 1]],
                                      [[0, 1], [0, 1], [0, 1]], [[1, 2], [1, 3], [1, 6]]])
def test_ordinary_sum_is_not_squared_norm(amplitudes):
    with pytest.raises(pilot.InvalidInput):
        pilot.amplitude_readout(dict(amplitude_problem(), amplitudes=amplitudes))


def test_assumption_is_operational_not_derived():
    problem = amplitude_problem()
    correct = {"probabilities": [[9, 25], [16, 25], [0, 1]]}
    assert pilot.check_proposal(problem, correct)["submission_accepted"]
    missing = pilot.check_proposal(dict(problem, assumption=None), correct)
    assert not missing["submission_accepted"] and not missing["interpretation_supplied"]
    wrong = {"probabilities": [[3, 7], [4, 7], [0, 1]]}
    assert not pilot.check_proposal(problem, wrong)["submission_accepted"]
    for unknown in ["born", "Born", True, {}, [], 0]:
        with pytest.raises(pilot.InvalidInput):
            pilot.amplitude_readout(dict(problem, assumption=unknown))
    assert pilot.check_proposal(pilot.default_problem(), proposal())["submission_accepted"]
    with pytest.raises(pilot.InvalidInput):
        pilot.check_proposal(problem, dict(correct, authorized=True))


@pytest.mark.parametrize("bad", [None, "1/2", {}, [], [1], [1, 2, 3], [True, 1], [1, False],
                                 [1.0, 1], [1, 0], [1, -2], [2, 4], [0, 2], [10**9+1, 1]])
def test_rational_intake(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.rational(bad)


@pytest.mark.parametrize("bad", [None, [], {}, {"kind": "other"}, {"kind": "weights"},
                                 {"kind": "weights", "weights": [2, 1, 0], "verified": True},
                                 {"kind": "amplitudes", "amplitudes": [[1, 1]]*3},
                                 {"kind": "amplitudes", "amplitudes": [], "assumption": None}])
def test_bad_problem_fields(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.calculate(bad)
    with pytest.raises(pilot.InvalidInput):
        pilot.normalize({"kind": "amplitudes", "weights": [2, 1, 0]})
    with pytest.raises(pilot.InvalidInput):
        pilot.amplitude_readout(dict(amplitude_problem(), kind="weights"))


def test_main_custody_real_routes_and_no_overwrite(tmp_path, capsys):
    root = tmp_path / "runs"
    args = ["--output-dir", str(root)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    receipt = json.loads(before["receipt.json"])
    assert receipt["result_sha256"] == pilot.digest(json.loads(before["result.json"]))
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["network_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["result_sha256"] in before["summary.md"].decode()
    problem, candidate = tmp_path / "problem.json", tmp_path / "proposal.json"
    raw = json.dumps(amplitude_problem(), indent=3).encode() + b"\r\n"
    proposed = b'{ "probabilities": [[9,25],[16,25],[0,1]] }\r\n'
    problem.write_bytes(raw)
    candidate.write_bytes(proposed)
    assert pilot.main(args + ["--input", str(problem)]) == 0
    capsys.readouterr()
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(candidate)]) == 0
    folder = Path(json.loads(capsys.readouterr().out)["output"])
    receipt = json.loads((folder / "receipt.json").read_text())
    assert (folder / "input.json").read_bytes() == raw and (folder / "proposal.json").read_bytes() == proposed
    assert receipt["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert receipt["proposal_sha256"] == hashlib.sha256(proposed).hexdigest()
    problem.write_text(json.dumps(amplitude_problem(None)))
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(candidate)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    candidate.write_text(json.dumps(proposal()))
    assert pilot.main(args + ["--proposal", str(candidate)]) == 0
    capsys.readouterr()
    blocked = tmp_path / "file"
    blocked.write_bytes(b"keep")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_bytes() == b"keep" and before == {p.name: p.read_bytes() for p in first.iterdir()}


@pytest.mark.parametrize("raw", [
    b'{"x":0,"x":1}', b'{"x":{"y":0,"y":1}}', b'NaN', b'Infinity', b'-Infinity',
    b'\xff', b'{', b' ' * 65537, b'[' * 7000 + b'0' + b']' * 7000,
], ids=["duplicate", "nested_duplicate", "nan", "infinity", "negative_infinity", "invalid_utf8", "truncated", "oversize", "deep"])
def test_strict_json_refusal(tmp_path, capsys, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    out = tmp_path / "runs"
    assert pilot.main(["--input", str(path), "--output-dir", str(out)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED" and not out.exists()
    path.unlink()
    assert pilot.main(["--input", str(path), "--output-dir", str(out)]) == 2


def test_real_cli(tmp_path):
    run = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                         capture_output=True, text=True, check=False, timeout=20)
    assert run.returncode == 0, run.stderr
    folder = Path(json.loads(run.stdout)["output"])
    assert json.loads((folder / "result.json").read_text())["cases"]["quiz07.2"]["submission_accepted"]


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("accept_bool", "type(value) is int and abs(value)", "isinstance(value, int) and abs(value)", "test_invalid_weights"),
        ("omit_negative_weight_check", "require(all(w >= 0 for w in weights),", "require(True,", "test_invalid_weights"),
        ("omit_lift_binding", '"lift_radicands_match_weights": radicands == expected', '"lift_radicands_match_weights": True', "test_false_lift_certificates"),
        ("square_raw_weights", "probabilities = [F(w, total) for w in weights]", "probabilities = [F(w*w, sum(x*x for x in weights)) for w in weights]", "test_999_weight_triples_and_positive_rescaling"),
        ("ordinary_sum_normalization", "require(sum(squares) == 1,", "require(sum(amplitudes) == 1,", "test_signed_normalized_amplitudes"),
        ("automatic_born_interpretation", "interpreted = assumption == BORN_ASSUMPTION", "interpreted = True", "test_assumption_is_operational_not_derived"),
        ("assumption_as_derivation", '"born_rule_derived": False', '"born_rule_derived": interpreted', "test_four_numbered_cases"),
    ]
    evidence = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "nonunique anchor")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_NORMALIZATION_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_NORMALIZATION_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
            env=env, capture_output=True, text=True, check=False, timeout=40)
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        evidence.append({"name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
                         "applied": mutant.read_text(encoding="utf-8") == source.replace(anchor, replacement),
                         "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest(),
                         "failed_nodes": failures, "exit_code": completed.returncode,
                         "original_unchanged": PILOT_FILE.read_bytes() == original,
                         "original_sha256": hashlib.sha256(original).hexdigest()})
    assert len(evidence) == 7
    if output := os.environ.get("PFP_NORMALIZATION_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
