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

PILOT_FILE = Path(os.environ.get("PFP_LP_UNDER_TEST", Path(__file__).resolve().parents[1] / "run.py"))
spec = importlib.util.spec_from_file_location("pfp_lp_under_test", PILOT_FILE)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)


def test_eight_exercises():
    cases = pilot.exercise_report()["cases"]
    assert set(cases) == {f"quiz{quiz}.{i}" for quiz in ("03", "19") for i in range(1, 5)}
    one = cases["quiz19.1"]
    assert one["optimality_certified"] and one["submission_accepted"]
    assert one["checked_row_ids"] == ["ub1", "ub2", "ub3"]
    assert one["objective"] == one["dual_bound"] == [2, 1]
    assert one["uniqueness"] == "NOT_ESTABLISHED"
    assert cases["quiz19.2"]["uniqueness"] == "NONUNIQUE"
    bad = cases["quiz19.3"]
    assert bad["original_problem"]["violated_constraints"] == ["domain:x>=0", "ub3"]
    assert bad["original_problem"]["gap_zero"] and not bad["original_problem"]["submission_accepted"]
    assert bad["domain_only_counterexample"]["violated_constraints"] == ["domain:x>=0"]
    assert not bad["domain_only_counterexample"]["optimality_certified"]
    assert cases["quiz19.4"]["float_input_refused"]
    assert not cases["quiz19.4"]["interrupted_search"]["optimality_certified"]
    initial = cases["quiz03.1"]
    assert not initial["violated_constraints"] and not initial["negative_dual_rows"]
    assert initial["dual_dominates_objective"] and not initial["optimality_certified"]
    assert initial["objective"] == [9, 1] and initial["dual_bound"] == [10, 1] and initial["gap"] == [1, 1]
    trace = cases["quiz03.2"]
    assert trace["submission_accepted"] and all(trace["checks"].values())
    assert trace["gaps"] == [[1, 1], [0, 1]] and not trace["search_performed"]
    loose = cases["quiz03.3"]
    assert loose["dual_bound"] == [12, 1] and loose["objective"] == [10, 1] and loose["gap"] == [2, 1]
    assert not loose["submission_accepted"]
    assert cases["quiz03.4"]["extra_authority_field_refused"] and cases["quiz03.4"]["authority_effect"] == "None"


@pytest.mark.parametrize("x,y", list(itertools.product(range(-2, 5), repeat=2)))
def test_feasibility_independent_grid(x, y):
    proposal = pilot.default_proposal()
    proposal["primal"] = [[x, 1], [y, 1]]
    result = pilot.check_certificate(pilot.default_problem(), proposal)
    expected_bad = []
    for condition, name in [(x < 0, "domain:x>=0"), (y < 0, "domain:y>=0"),
                            (x + y > 2, "ub1"), (x > 2, "ub2"), (y > 2, "ub3")]:
        if condition:
            expected_bad.append(name)
    assert result["violated_constraints"] == expected_bad
    assert result["optimality_certified"] is (x >= 0 and y >= 0 and x + y <= 2 and x <= 2 and y <= 2 and x + y == 2)


def test_rational_optimal_segment_and_nonuniqueness():
    problem = pilot.default_problem()
    for t in (F(0), F(1, 7), F(1, 2), F(1), F(3, 2), F(2)):
        proposal = pilot.default_proposal()
        proposal["primal"] = [pilot.wire(t), pilot.wire(2 - t)]
        proposal["alternative"] = [[0, 1], [2, 1]] if t != 0 else [[2, 1], [0, 1]]
        result = pilot.check_certificate(problem, proposal)
        assert result["optimality_certified"] and result["uniqueness"] == "NONUNIQUE"
    # This finite test does not enumerate all rationals in the interval.


@pytest.mark.parametrize("other", [
    [[1, 2], [3, 2]], [[0, 1], [0, 1]], [[-1, 1], [3, 1]], [[3, 1], [-1, 1]],
], ids=["same_point", "suboptimal", "infeasible_x", "infeasible_y"])
def test_invalid_nonuniqueness_witness(other):
    proposal = dict(pilot.default_proposal(), alternative=other)
    result = pilot.check_certificate(pilot.default_problem(), proposal)
    assert result["optimality_certified"]
    assert not result["submission_accepted"]
    assert result["uniqueness"] == "NOT_ESTABLISHED"


def test_coefficient_slack_is_allowed():
    problem = pilot.Problem((F(1), F(0)), (pilot.Row("r", (F(1), F(1)), F(1)),))
    result = pilot.check_certificate(problem, {"primal": [[1, 1], [0, 1]], "dual": {"r": [1, 1]}})
    assert result["dual_coefficients"] == [[1, 1], [1, 1]]
    assert result["optimality_certified"]


def test_dual_checks_not_just_objective_equality():
    problem = pilot.Problem((F(1), F(1)), (pilot.Row("r", (F(1), F(0)), F(1)),))
    result = pilot.check_certificate(problem, {"primal": [[1, 1], [0, 1]], "dual": {"r": [1, 1]}})
    assert result["gap_zero"] and not result["dual_dominates_objective"]
    assert not result["optimality_certified"]
    problem = pilot.Problem((F(-1), F(0)), (pilot.Row("r", (F(1), F(0)), F(0)),))
    result = pilot.check_certificate(problem, {"primal": [[0, 1], [0, 1]], "dual": {"r": [-1, 1]}})
    assert result["gap_zero"] and result["dual_dominates_objective"]
    assert result["negative_dual_rows"] == ["r"] and not result["optimality_certified"]
    assert pilot.candidate_only(pilot.default_problem(), [[-1, 1], [3, 1]])["violated_constraints"] == ["domain:x>=0", "ub3"]


@pytest.mark.parametrize("bad", [
    None, 1, "1/2", {}, [], [1], [1, 2, 3], [True, 1], [1, True],
    [0.5, 1], [1, 1.0], ["1", 2], [1, 0], [1, -2], [2, 4], [0, 2],
    [10**9 + 1, 1], [1, 10**9 + 1],
], ids=["null", "integer", "text", "object", "empty", "short", "long", "bool_n", "bool_d",
        "float_n", "float_d", "str_n", "zero_d", "negative_d", "unreduced", "zero_unreduced", "large_n", "large_d"])
def test_exact_rational_intake(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.rational(bad)


@pytest.mark.parametrize("bad", [None, {}, [], [1], [1, 2, 3], [[1, 1], [1, 0]]])
def test_vector_intake(bad):
    with pytest.raises(pilot.InvalidInput):
        pilot.vector(bad)


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(extra=True),
    lambda p: p.pop("objective"),
    lambda p: p.update(nonnegative=["x"]),
    lambda p: p.update(rows={}),
    lambda p: p.update(rows=[]),
    lambda p: p.update(rows=[None]),
    lambda p: p["rows"][0].update(extra=True),
    lambda p: p["rows"][0].update(id="domain:x"),
    lambda p: p["rows"][0].update(id=7),
    lambda p: p["rows"][1].update(id="ub1"),
    lambda p: p["rows"][0].update(upper=[0.1, 1]),
    lambda p: p.update(rows=p["rows"] * 11),
])
def test_problem_mutations(mutate):
    payload = pilot.default_problem().payload()
    mutate(payload)
    with pytest.raises(pilot.InvalidInput):
        pilot.parse_problem(payload)


def test_direct_dataclass_contract_and_roundtrip():
    original = pilot.default_problem()
    assert pilot.parse_problem(original.payload()) == original
    goodrow = pilot.Row("r", (F(1), F(1)), F(1))
    bad_arguments = [
        ([F(1), F(1)], (goodrow,)), ((F(1),), (goodrow,)), ((1, 1), (goodrow,)),
        ((F(1), F(1)), [goodrow]), ((F(1), F(1)), (None,)),
        ((F(1), F(1)), (pilot.Row("r", [F(1), F(1)], F(1)),)),
        ((F(1), F(1)), (pilot.Row("r", (F(1),), F(1)),)),
        ((F(1), F(1)), (pilot.Row("r", (1, 1), F(1)),)),
        ((F(1), F(1)), (pilot.Row("r", (F(1), F(1)), 1),)),
    ]
    for args in bad_arguments:
        with pytest.raises(pilot.InvalidInput):
            pilot.Problem(*args)
    with pytest.raises(pilot.InvalidInput):
        pilot.parse_problem(None)


@pytest.mark.parametrize("mutate", [
    lambda p: p.pop("dual"),
    lambda p: p.update(verified=True),
    lambda p: p.update(dual=[]),
    lambda p: p["dual"].pop("ub3"),
    lambda p: p["dual"].update(ghost=[0, 1]),
    lambda p: p["dual"].update(ub1=[True, 1]),
    lambda p: p.update(primal=[[0.5, 1], [1.5, 1]]),
    lambda p: p.update(alternative=[[0, 1], [2, 0]]),
])
def test_certificate_intake(mutate):
    proposal = pilot.default_proposal()
    mutate(proposal)
    with pytest.raises(pilot.InvalidInput):
        pilot.check_certificate(pilot.default_problem(), proposal)
    with pytest.raises(pilot.InvalidInput):
        pilot.check_certificate(pilot.default_problem(), None)


def test_problem_binding_and_all_rows():
    proposal = pilot.default_proposal()
    first = pilot.check_certificate(pilot.default_problem(), proposal)
    payload = pilot.default_problem().payload()
    payload["rows"][2]["upper"] = [1, 1]
    other = pilot.parse_problem(payload)
    second = pilot.check_certificate(other, proposal)
    assert first["problem_sha256"] != second["problem_sha256"]
    assert second["violated_constraints"] == ["ub3"] and not second["submission_accepted"]


def test_trace_independent_3125_start_states():
    problem = pilot.quiz03_problem()
    for x, y in itertools.product(range(-1, 4), repeat=2):
        for a, b, c in itertools.product(range(-1, 4), repeat=3):
            trace = pilot.quiz03_trace()
            trace["steps"][0] = {"primal": [[x, 1], [y, 1]],
                                 "dual": {"ub1": [a, 1], "ub2": [b, 1], "ub3": [c, 1]}}
            result = pilot.check_trace(problem, trace)
            feasible = x >= 0 and y >= 0 and x+y <= 4 and x <= 2 and y <= 3
            dual_feasible = min(a, b, c) >= 0 and a+b >= 3 and a+c >= 2
            gap = 4*a + 2*b + 3*c - 3*x - 2*y
            assert result["submission_accepted"] is (feasible and dual_feasible and gap > 0)
            assert result["steps"][0]["gap"] == [gap, 1]
            assert result["checks"]["all_primal_feasible"] is feasible
            assert result["checks"]["all_dual_feasible"] is dual_feasible


def test_trace_boundary_controls():
    problem = pilot.quiz03_problem()
    wrong_problem = pilot.quiz03_trace()
    wrong_problem["problem_sha256"] = "0" * 64
    result = pilot.check_trace(problem, wrong_problem)
    assert not result["checks"]["problem_matches"] and not result["submission_accepted"]
    for kind in ("negative_primal", "negative_dual", "wrong_objective", "repeat", "open_final_gap"):
        trace = pilot.quiz03_trace()
        if kind == "negative_primal":
            trace["steps"][0]["primal"] = [[-1, 1], [3, 1]]
        elif kind == "negative_dual":
            trace["steps"][0] = {"primal": [[2, 1], [1, 1]],
                                 "dual": {"ub1": [3, 1], "ub2": [0, 1], "ub3": [-1, 1]}}
        elif kind == "wrong_objective":
            trace["steps"][0] = {"primal": [[2, 1], [1, 1]],
                                 "dual": {"ub1": [0, 1], "ub2": [0, 1], "ub3": [3, 1]}}
        elif kind == "repeat":
            trace["steps"].insert(1, trace["steps"][0])
        else:
            trace["steps"][0]["primal"] = [[2, 1], [1, 1]]
            trace["steps"][1]["primal"] = [[2, 1], [3, 2]]
        result = pilot.check_trace(problem, trace)
        assert not result["submission_accepted"], kind
    switched = problem.payload()
    switched["rows"][2]["upper"] = [4, 1]
    result = pilot.check_trace(pilot.parse_problem(switched), pilot.quiz03_trace())
    assert not result["checks"]["problem_matches"] and not result["submission_accepted"]
    assert result["steps"][-1]["optimality_certified"]


def test_trace_32_states_and_slack_dual():
    trace = pilot.quiz03_trace()
    dual = trace["steps"][0]["dual"]
    trace["steps"] = [{"primal": [[2, 1], pilot.wire(F(33+i, 32))], "dual": dual} for i in range(32)]
    result = pilot.check_trace(pilot.quiz03_problem(), trace)
    assert result["submission_accepted"] and len(result["steps"]) == 32
    assert result["gaps"] == [pilot.wire(F(31-i, 16)) for i in range(32)]
    problem = pilot.Problem((F(1), F(0)), (pilot.Row("r", (F(1), F(1)), F(1)),))
    trace = {"problem_sha256": pilot.digest(problem.payload()), "steps": [
        {"primal": [[0, 1], [0, 1]], "dual": {"r": [1, 1]}},
        {"primal": [[1, 1], [0, 1]], "dual": {"r": [1, 1]}},
    ]}
    assert pilot.check_trace(problem, trace)["submission_accepted"]


def test_saved_quiz03_fixtures():
    folder = Path(__file__).resolve().parents[1]
    problem = pilot.parse_problem(json.loads((folder / "quiz03_problem.json").read_text()))
    trace = json.loads((folder / "quiz03_trace.json").read_text())
    certificate = json.loads((folder / "quiz03_certificate.json").read_text())
    assert problem == pilot.quiz03_problem() and trace == pilot.quiz03_trace()
    assert pilot.check_trace(problem, trace)["submission_accepted"]
    assert pilot.check_certificate(problem, certificate)["submission_accepted"]


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(extra=True), lambda p: p.pop("problem_sha256"),
    lambda p: p.update(problem_sha256=None), lambda p: p.update(problem_sha256="a"*63),
    lambda p: p.update(problem_sha256="A"*64), lambda p: p.update(steps=None),
    lambda p: p.update(steps=[]), lambda p: p.update(steps=p["steps"][:1]),
    lambda p: p.update(steps=p["steps"]*17), lambda p: p["steps"].__setitem__(0, None),
    lambda p: p["steps"][0].update(alternative=[[0, 1], [0, 1]]),
    lambda p: p["steps"][0].update(problem_sha256="0"*64),
    lambda p: p["steps"][0].update(gap=[0, 1]),
    lambda p: p["steps"][0].update(production_authorized=True),
    lambda p: p["steps"][0].update(primal=[[True, 1], [1, 1]]),
])
def test_trace_intake(mutate):
    trace = pilot.quiz03_trace()
    mutate(trace)
    with pytest.raises(pilot.InvalidInput):
        pilot.check_trace(pilot.quiz03_problem(), trace)
    with pytest.raises(pilot.InvalidInput):
        pilot.check_trace(pilot.quiz03_problem(), None)


def test_quiz03_changed_bound_reuses_dual_without_claiming_minimal_repair():
    payload = pilot.quiz03_problem().payload()
    payload["rows"][1]["upper"] = [1, 1]
    problem = pilot.parse_problem(payload)
    old = pilot.quiz03_trace()["steps"][-1]
    stale = pilot.check_certificate(problem, old)
    assert stale["violated_constraints"] == ["ub2"] and not stale["submission_accepted"]
    assert not stale["negative_dual_rows"] and stale["dual_dominates_objective"]
    assert stale["dual_bound"] == [9, 1]
    repaired = pilot.check_certificate(problem, dict(old, primal=[[1, 1], [3, 1]]))
    assert repaired["submission_accepted"] and repaired["objective"] == [9, 1]


def test_trace_real_cli_and_raw_custody(tmp_path):
    problem, trace = tmp_path / "problem.json", tmp_path / "trace.json"
    raw_problem = json.dumps(pilot.quiz03_problem().payload(), indent=3).encode() + b"\r\n"
    raw_trace = json.dumps(pilot.quiz03_trace(), indent=4).encode() + b"\r\n"
    problem.write_bytes(raw_problem)
    trace.write_bytes(raw_trace)
    args = [sys.executable, str(PILOT_FILE), "--input", str(problem), "--trace", str(trace),
            "--output-dir", str(tmp_path / "runs")]
    first = subprocess.run(args, capture_output=True, text=True, check=False, timeout=20)
    assert first.returncode == 0, first.stderr
    folder = Path(json.loads(first.stdout)["output"])
    report = json.loads((folder / "result.json").read_text())
    receipt = json.loads((folder / "receipt.json").read_text())
    assert report["trace"]["submission_accepted"] and report["trace"]["gaps"] == [[1, 1], [0, 1]]
    assert (folder / "input.json").read_bytes() == raw_problem
    assert (folder / "proposal.json").read_bytes() == raw_trace
    assert receipt["input_sha256"] == hashlib.sha256(raw_problem).hexdigest()
    assert receipt["proposal_sha256"] == hashlib.sha256(raw_trace).hexdigest()
    assert receipt["result_sha256"] == pilot.digest(report)
    wrong = dict(pilot.quiz03_trace(), problem_sha256="0"*64)
    trace.write_text(json.dumps(wrong))
    rejected = subprocess.run(args, capture_output=True, text=True, check=False, timeout=20)
    assert rejected.returncode == 1 and json.loads(rejected.stdout)["status"] == "REJECTED"
    trace.write_text('{"steps":[],"steps":[]}')
    refused = subprocess.run(args, capture_output=True, text=True, check=False, timeout=20)
    assert refused.returncode == 2 and json.loads(refused.stdout)["status"] == "REFUSED"
    exclusive = subprocess.run(args + ["--proposal", str(trace)], capture_output=True, text=True, check=False, timeout=20)
    assert exclusive.returncode == 2 and "not allowed with argument" in exclusive.stderr


def test_main_routes_and_raw_custody(tmp_path, capsys):
    out = tmp_path / "runs"
    args = ["--output-dir", str(out)]
    assert pilot.main(args) == 0
    first = Path(json.loads(capsys.readouterr().out)["output"])
    report = json.loads((first / "result.json").read_text())
    receipt = json.loads((first / "receipt.json").read_text())
    assert receipt["result_sha256"] == pilot.digest(report)
    assert receipt["code_sha256"] == hashlib.sha256(PILOT_FILE.read_bytes()).hexdigest()
    assert receipt["cost_usd"] == "0" and receipt["network_calls"] == 0
    assert receipt["result_sha256"] in (first / "summary.md").read_text()
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    problem = tmp_path / "problem.json"
    raw_problem = json.dumps(pilot.default_problem().payload(), indent=3).encode() + b"\r\n"
    problem.write_bytes(raw_problem)
    candidate = tmp_path / "candidate.json"
    raw_proposal = json.dumps(pilot.default_proposal(), indent=4).encode() + b"\r\n"
    candidate.write_bytes(raw_proposal)
    assert pilot.main(args + ["--input", str(problem)]) == 2
    capsys.readouterr()
    assert pilot.main(args + ["--proposal", str(candidate)]) == 0
    capsys.readouterr()
    assert pilot.main(args + ["--input", str(problem), "--proposal", str(candidate)]) == 0
    current = Path(json.loads(capsys.readouterr().out)["output"])
    receipt = json.loads((current / "receipt.json").read_text())
    assert receipt["status"] == "ACCEPTED"
    assert (current / "input.json").read_bytes() == raw_problem
    assert (current / "proposal.json").read_bytes() == raw_proposal
    assert receipt["input_sha256"] == hashlib.sha256(raw_problem).hexdigest()
    assert receipt["proposal_sha256"] == hashlib.sha256(raw_proposal).hexdigest()
    bad = dict(pilot.default_proposal(), primal=[[-1, 1], [3, 1]])
    candidate.write_text(json.dumps(bad))
    assert pilot.main(args + ["--proposal", str(candidate)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "REJECTED"
    candidate.write_text("{")
    assert pilot.main(args + ["--proposal", str(candidate)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    candidate.unlink()
    assert pilot.main(args + ["--proposal", str(candidate)]) == 2
    capsys.readouterr()
    blocked = tmp_path / "file_not_dir"
    blocked.write_text("keep")
    assert pilot.main(["--output-dir", str(blocked)]) == 2
    capsys.readouterr()
    assert blocked.read_text() == "keep"
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}


@pytest.mark.parametrize("raw", [
    b'{"x":0,"x":1}', b'{"nested":{"x":0,"x":1}}', b'NaN', b'Infinity', b'-Infinity', b'\xff', b' '*65537,
], ids=["duplicate", "nested_duplicate", "nan", "infinity", "negative_infinity", "invalid_utf8", "oversize"])
def test_strict_json(tmp_path, raw):
    path = tmp_path / "bad.json"
    path.write_bytes(raw)
    with pytest.raises((pilot.InvalidInput, ValueError)):
        pilot.read_document(path)


def test_real_cli(tmp_path):
    run = subprocess.run([sys.executable, str(PILOT_FILE), "--output-dir", str(tmp_path / "cli")],
                         capture_output=True, text=True, check=False, timeout=20)
    assert run.returncode == 0, run.stderr
    folder = Path(json.loads(run.stdout)["output"])
    assert json.loads((folder / "result.json").read_text())["cases"]["quiz19.3"]["original_problem"]["optimality_certified"] is False


def test_deep_json_returns_controlled_refusal(tmp_path, capsys):
    proposal = tmp_path / "deep.json"
    proposal.write_text("[" * 7000 + "0" + "]" * 7000)
    assert pilot.main(["--proposal", str(proposal), "--output-dir", str(tmp_path / "runs")]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "REFUSED"
    assert not (tmp_path / "runs").exists()


def test_implementation_mutations_are_killed(tmp_path):
    original = PILOT_FILE.read_bytes()
    source = original.decode("utf-8")
    mutations = [
        ("omit_domains", "zip(VARIABLES, point, strict=True) if value < 0", "zip(VARIABLES, point, strict=True) if False", "test_feasibility_independent_grid"),
        ("omit_last_row", "for row in problem.rows if dot(row.coefficients, point)", "for row in problem.rows[:-1] if dot(row.coefficients, point)", "test_problem_binding_and_all_rows"),
        ("equality_only", "optimal = not primal_bad and not dual_bad and dominates and objective == bound", "optimal = objective == bound", "test_dual_checks_not_just_objective_equality"),
        ("reject_slack_certificate", "dominates = all(a >= c", "dominates = all(a == c", "test_coefficient_slack_is_allowed"),
        ("allow_bool", "type(n) is int and type(d) is int", "isinstance(n, int) and isinstance(d, int)", "test_exact_rational_intake"),
        ("trace_rebind", '"problem_matches": pinned == digest(problem.payload())', '"problem_matches": True', "test_trace_boundary_controls"),
        ("trace_omit_primal", '"all_primal_feasible": all(not row["violated_constraints"] for row in checked)', '"all_primal_feasible": True', "test_trace_boundary_controls"),
        ("trace_omit_dual", '"all_dual_feasible": all(not row["negative_dual_rows"] and row["dual_dominates_objective"] for row in checked)', '"all_dual_feasible": True', "test_trace_boundary_controls"),
        ("trace_allow_stall", 'all(after < before for before, after in zip(gaps, gaps[1:], strict=False))', 'all(after <= before for before, after in zip(gaps, gaps[1:], strict=False))', "test_trace_boundary_controls"),
        ("trace_open_terminal", '"final_optimality_certified": checked[-1]["optimality_certified"]', '"final_optimality_certified": True', "test_trace_boundary_controls"),
    ]
    observations = []
    for name, anchor, replacement, test_name in mutations:
        assert source.count(anchor) == 1, (name, "nonunique anchor")
        mutant = tmp_path / (name + ".py")
        mutant.write_text(source.replace(anchor, replacement), encoding="utf-8")
        env = dict(os.environ, PFP_LP_UNDER_TEST=str(mutant), NO_COLOR="1")
        for variable in ("PFP_LP_MUTATION_OUTPUT", "FORCE_COLOR", "PY_COLORS"):
            env.pop(variable, None)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", str(Path(__file__).resolve()) + "::" + test_name,
             "-q", "--color=no", "-o", "addopts=", "--import-mode=importlib", "--basetemp", str(tmp_path / name)],
            env=env, capture_output=True, text=True, check=False, timeout=40)
        assert completed.returncode == 1, (name, completed.stdout, completed.stderr)
        failures = [line for line in completed.stdout.splitlines() if line.startswith("FAILED ")]
        assert failures and all(test_name in line for line in failures)
        observations.append({
            "name": name, "target": str(PILOT_FILE), "anchor": anchor, "replacement": replacement,
            "applied": mutant.read_text(encoding="utf-8") == source.replace(anchor, replacement),
            "mutant_sha256": hashlib.sha256(mutant.read_bytes()).hexdigest(),
            "failed_nodes": failures, "exit_code": completed.returncode,
            "original_unchanged": PILOT_FILE.read_bytes() == original,
            "original_sha256": hashlib.sha256(original).hexdigest(),
        })
    assert len(observations) == 10
    if output := os.environ.get("PFP_LP_MUTATION_OUTPUT"):
        Path(output).write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(PILOT_FILE), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(PILOT_FILE), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "COMPUTED"
