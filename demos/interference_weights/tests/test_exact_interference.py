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

PILOT_FILE = Path(os.environ.get("PFP_INTERFERENCE_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_interference_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def probability(values):
    return [F(*v) for v in values]


def amplitudes(values):
    return [tuple(F(*x) for x in z) for z in values]


def test_four_exercise_obligations():
    report = pilot.exercise_report()
    cases = report["cases"]
    assert set(cases) == {f"quiz20.{i}" for i in range(1, 5)}
    initial = cases["quiz20.1"]
    for name in ("plus", "minus"):
        assert probability(initial[name]["input_probabilities"]) == [F(1, 2), F(1, 2)]
    assert initial["equal_initial_probabilities"] and initial["different_amplitudes"]
    assert amplitudes(cases["quiz20.2"]["plus"]) == [(1, 0), (0, 0)]
    assert amplitudes(cases["quiz20.2"]["minus"]) == [(0, 0), (1, 0)]
    assert cases["quiz20.2"]["different_probabilities"]
    assert not cases["quiz20.2"]["weights_determine_post_h"]
    global_minus = cases["quiz20.3"]
    assert amplitudes(global_minus["global_minus"]["post_h_amplitudes"]) == [(-1, 0), (0, 0)]
    assert global_minus["probabilities_unchanged"] and global_minus["amplitudes_changed"]
    lift = cases["quiz20.4"]
    assert probability(lift["lift"]["basis_probabilities"]) == [F(2, 5), F(3, 5)]
    assert set(lift["refusals"]) == {"zero_total", "negative_weight"}
    assert all(row["status"] == "REFUSED" for row in lift["refusals"].values())
    assert not report["model"]["born_uniqueness_derived"]
    assert not report["model"]["genesis_lift_derived"]
    assert report["model"]["quantum_computing_conclusion"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("sign", [-1, 1])
def test_rational_global_phases_and_hadamard_matrix(sign):
    phases = {(F(1), F(0)), (F(-1), F(0)), (F(0), F(1)), (F(0), F(-1))}
    for p, q in itertools.product(range(-8, 9), range(1, 9)):
        t = F(p, q)
        phases.add(((1-t*t)/(1+t*t), 2*t/(1+t*t)))
    for real, imag in phases:
        phase = [pilot.wire(real), pilot.wire(imag)]
        problem = dict(pilot.default_problem(), relative_sign=sign, global_phase=phase)
        result = pilot.interference(problem)
        assert result["input_state"]["common_denominator"] == "sqrt(2)"
        assert amplitudes(result["input_state"]["numerators"]) == [(real, imag), (sign*real, sign*imag)]
        expected = [(real, imag), (F(0), F(0))] if sign == 1 else [(F(0), F(0)), (real, imag)]
        assert amplitudes(result["post_h_amplitudes"]) == expected
        assert probability(result["input_probabilities"]) == [F(1, 2)] * 2
        assert probability(result["post_h_probabilities"]) == ([F(1), F(0)] if sign == 1 else [F(0), F(1)])
        assert result["model_sha256"] == pilot.digest(pilot.MODEL)
    # Independent integer matrix check: M^T M=2I and M^2=2I.
    m = ((1, 1), (1, -1))
    assert [[sum(m[k][i] * m[k][j] for k in range(2)) for j in range(2)] for i in range(2)] == [[2, 0], [0, 2]]


@pytest.mark.parametrize("phase", [[[0, 1], [0, 1]], [[2, 1], [0, 1]], [[1, 1], [1, 1]], [[3, 5], [3, 5]]])
def test_nonunit_phase_refused(phase):
    with pytest.raises(pilot.InvalidInput):
        pilot.interference(dict(pilot.default_problem(), global_phase=phase))


@pytest.mark.parametrize("weights", [
    [[0, 1], [0, 1]], [[-1, 1], [2, 1]], [[2, 1], [-1, 1]],
    [[-1, 1], [-1, 1]], [[0, 1], [-1, 1]],
])
def test_invalid_weight_preconditions(weights):
    with pytest.raises(pilot.InvalidInput):
        pilot.weight_lift({"kind": "weights", "weights": weights})


def test_weights_exact_normalization_and_scaling():
    values = (F(0), F(1, 7), F(1, 2), F(1), F(2), F(1000000000))
    for a, b in itertools.product(values, repeat=2):
        if a+b == 0:
            continue
        problem = {"kind": "weights", "weights": [pilot.wire(a), pilot.wire(b)]}
        result = pilot.calculate(problem)
        expected = [a/(a+b), b/(a+b)]
        assert probability(result["basis_probabilities"]) == expected
        assert F(*result["total_weight"]) == a+b
        assert [F(*row["nonnegative_sqrt_of"]) for row in result["square_root_lift"]] == expected
        assert result["phase_reconstruction"] == "NOT_ATTEMPTED"
        assert result["post_h_prediction"] == "NOT_EVALUATED_BY_WEIGHT_LIFT"
        assert not result["born_uniqueness_derived"]
        assert pilot.check_prediction(result, {"basis_probabilities": result["basis_probabilities"]})["submission_accepted"]
    left = pilot.weight_lift({"kind": "weights", "weights": [[1, 2], [3, 2]]})
    right = pilot.weight_lift({"kind": "weights", "weights": [[2, 1], [6, 1]]})
    assert left["basis_probabilities"] == right["basis_probabilities"]


def test_large_normalized_denominator_can_be_predicted_exactly():
    report = pilot.weight_lift({"kind": "weights", "weights": [[999999937, 999999929], [999999893, 999999883]]})
    assert report["basis_probabilities"][0][1] > 10**9
    assert pilot.check_prediction(report, {"basis_probabilities": report["basis_probabilities"]})["submission_accepted"]


def test_single_supported_sector_does_not_claim_mathematical_underdetermination():
    for weights in ([[1, 1], [0, 1]], [[0, 1], [1, 1]]):
        report = pilot.weight_lift({"kind": "weights", "weights": weights})
        assert report["post_h_prediction"] == "NOT_EVALUATED_BY_WEIGHT_LIFT"
        assert report["phase_reconstruction"] == "NOT_ATTEMPTED"
        assert "post_h_prediction_from_weights" not in report
        assert "relative_phases_determined" not in report
        assert probability(report["basis_probabilities"]) in ([F(1), F(0)], [F(0), F(1)])


@pytest.mark.parametrize("bad", [None, 1, "1/2", [], [1], [1, 2, 3], [True, 1], [1, True],
                                 [0.5, 1], [1, 1.0], ["1", 2], [1, 0], [1, -1], [2, 4],
                                 [0, 2], [10**9 + 1, 1], [1, 10**9 + 1]])
def test_rational_intake(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.rational(bad)


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(relative_sign=True), lambda p: p.update(relative_sign=1.0),
    lambda p: p.update(relative_sign=0), lambda p: p.update(relative_sign="1"),
    lambda p: p.update(global_phase=[]), lambda p: p.update(global_phase=[1, 2]),
    lambda p: p.update(global_phase=[[True, 1], [0, 1]]), lambda p: p.update(kind="weights"),
    lambda p: p.update(extra=True), lambda p: p.pop("global_phase"),
])
def test_invalid_interference_fields(mutate):
    value = pilot.default_problem()
    mutate(value)
    with pytest.raises(pilot.InvalidInput):
        pilot.interference(value)


@pytest.mark.parametrize("bad", [None, [], {}, {"kind": "other"}, {"kind": "weights", "weights": []},
                                 {"kind": "weights", "weights": [[1, 1]]},
                                 {"kind": "weights", "weights": [[1, 1]] * 3},
                                 {"kind": "weights", "weights": [[True, 1], [1, 1]]}])
def test_bad_problem(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.calculate(bad)


def test_prediction_not_weights_only_and_strict_fields():
    plus = pilot.interference(pilot.default_problem())
    minus = pilot.interference(dict(pilot.default_problem(), relative_sign=-1))
    guessed = {"post_h_probabilities": [[1, 2], [1, 2]]}
    assert not pilot.check_prediction(plus, guessed)["submission_accepted"]
    assert not pilot.check_prediction(minus, guessed)["submission_accepted"]
    correct_plus = {"post_h_probabilities": [[1, 1], [0, 1]]}
    assert pilot.check_prediction(plus, correct_plus)["submission_accepted"]
    assert not pilot.check_prediction(minus, correct_plus)["submission_accepted"]
    for invalid in [None, {}, {"post_h_probabilities": [1]},
                    {"post_h_probabilities": [[True, 1], [0, 1]]},
                    {"post_h_probabilities": [[1, 1], [0, 1]], "verified": True},
                    {"post_h_probabilities": [[2 * 10**18 + 1, 1], [0, 1]]}]:
        with pytest.raises(pilot.InvalidInput):
            pilot.check_prediction(plus, invalid)


def test_main_routes_custody_and_no_overwrite(tmp_path, capsys):
    out = tmp_path / "runs"
    args = ["--output-dir", str(out)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    receipt = json.loads(before["receipt.json"])
    assert receipt["result_sha256"] == pilot.digest(json.loads(before["result.json"]))
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["network_calls"] == 0 and receipt["cost_usd"] == "0"
    assert receipt["result_sha256"] in before["summary.md"].decode()
    problem, proposal = tmp_path / "input.json", tmp_path / "proposal.json"
    raw = json.dumps(dict(pilot.default_problem(), relative_sign=-1), indent=3).encode() + b"\r\n"
    candidate = b'{ "post_h_probabilities": [[0,1],[1,1]] }\r\n'
    problem.write_bytes(raw)
    proposal.write_bytes(candidate)
    assert pilot.main(args + ["--input", str(problem)]) == 0
    capsys.readouterr()
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(proposal)]) == 0
    folder = Path(json.loads(capsys.readouterr().out)["output"])
    cert = json.loads((folder / "receipt.json").read_text())
    assert cert["status"] == "ACCEPTED"
    assert (folder / "input.json").read_bytes() == raw and (folder / "proposal.json").read_bytes() == candidate
    assert cert["input_sha256"] == hashlib.sha256(raw).hexdigest()
    assert cert["proposal_sha256"] == hashlib.sha256(candidate).hexdigest()
    assert pilot.main(args + ["--proposal", str(proposal)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    blocked = tmp_path / "file"
    blocked.write_text("keep")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_text() == "keep"
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}


@pytest.mark.parametrize("raw", [
    b'{"x":0,"x":1}', b'{"x":{"y":0,"y":1}}', b'NaN', b'Infinity', b'-Infinity',
    b'\xff', b'{', b' ' * 65537, b'[' * 7000 + b'0' + b']' * 7000,
], ids=["duplicate", "nested_duplicate", "nan", "infinity", "negative_infinity", "invalid_utf8", "truncated", "oversize", "deep"])
def test_strict_json_refusals(tmp_path, capsys, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    root = tmp_path / "runs"
    assert pilot.main(["--input", str(path), "--output-dir", str(root)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not root.exists()
    path.unlink()
    assert pilot.main(["--input", str(path), "--output-dir", str(root)]) == 2


def test_real_cli(tmp_path):
    run = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                         capture_output=True, text=True, check=False, timeout=20)
    assert run.returncode == 0, run.stderr
    folder = Path(json.loads(run.stdout)["output"])
    assert json.loads((folder / "result.json").read_text())["cases"]["quiz20.2"]["different_probabilities"]


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("erase_relative_sign", "numerators = (phase, scale(phase, sign))", "numerators = (phase, scale(phase, abs(sign)))", "test_four_exercise_obligations"),
        ("missing_hadamard_factor", "scale(add(numerators[0], numerators[1]), F(1, 2))", "scale(add(numerators[0], numerators[1]), F(1))", "test_four_exercise_obligations"),
        ("missing_complex_conjugation", "return x[0] * x[0] + x[1] * x[1]", "return x[0] * x[0] - x[1] * x[1]", "test_rational_global_phases_and_hadamard_matrix"),
        ("absolute_global_amplitudes", '"post_h_amplitudes": [gwire(v) for v in post]', '"post_h_amplitudes": [gwire((abs(v[0]), abs(v[1]))) for v in post]', "test_four_exercise_obligations"),
        ("negative_weights_allowed", 'require(all(v >= 0 for v in weights),', 'require(True,', "test_invalid_weight_preconditions"),
        ("uniform_zero_fallback", 'require(total > 0, "Positive total weight required; no uniform fallback")', 'if total == 0:\n        weights, total = [F(1), F(1)], F(2)', "test_invalid_weight_preconditions"),
        ("nonunit_phase_allowed", 'require(norm_squared(phase) == 1,', 'require(True,', "test_nonunit_phase_refused"),
    ]
    evidence = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "nonunique anchor")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_INTERFERENCE_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_INTERFERENCE_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
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
    assert len(evidence) == 7
    if output := os.environ.get("PFP_INTERFERENCE_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
