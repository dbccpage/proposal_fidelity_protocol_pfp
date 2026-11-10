"""Quizzes 19 and 03: exact LP certificates and supplied gap-reduction traces.

For rational x>=0 and Ax<=b, check lambda>=0, A^T lambda>=c and
c*x=b*lambda. An alternative distinct optimal point establishes nonuniqueness.
No network calls, model-performance claim, or authority to apply a solution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000027"
MAX_INPUT_BYTES = 65536
VARIABLES = ("x", "y")


class InvalidInput(ValueError):
    """Input is outside the declared finite rational contract."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def rational(value):
    require(type(value) is list and len(value) == 2, "Use a [numerator,denominator] rational")
    n, d = value
    require(type(n) is int and type(d) is int, "Rational components must be integers, not bool/float")
    require(abs(n) <= 10**9 and 0 < d <= 10**9, "Rational components exceed bounds or denominator is not positive")
    require(math.gcd(n, d) == 1, "Rational must be reduced")
    return Fraction(n, d)


def wire(value):
    return [value.numerator, value.denominator]


def vector(value):
    require(type(value) is list and len(value) == 2, "Need exactly x and y coordinates")
    return tuple(rational(v) for v in value)


def dot(left, right):
    return sum((a * b for a, b in zip(left, right, strict=True)), Fraction(0))


@dataclass(frozen=True)
class Row:
    row_id: str
    coefficients: tuple[Fraction, Fraction]
    upper: Fraction


@dataclass(frozen=True)
class Problem:
    objective: tuple[Fraction, Fraction]
    rows: tuple[Row, ...]

    def __post_init__(self):
        require(type(self.objective) is tuple and len(self.objective) == 2, "Objective has two coefficients")
        require(all(type(v) is Fraction for v in self.objective), "Exact objective coefficients required")
        require(type(self.rows) is tuple and 1 <= len(self.rows) <= 32, "Need 1 to 32 rows")
        require(all(type(row) is Row for row in self.rows), "Rows must be typed")
        for row in self.rows:
            require(type(row.row_id) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,31}", row.row_id) is not None, "Invalid row identity")
            require(type(row.coefficients) is tuple and len(row.coefficients) == 2, "Rows have two coefficients")
            require(all(type(v) is Fraction for v in row.coefficients) and type(row.upper) is Fraction, "Exact row coefficients required")
        require(len({row.row_id for row in self.rows}) == len(self.rows), "Duplicate row identity")

    def payload(self):
        return {
            "objective": [wire(v) for v in self.objective],
            "nonnegative": list(VARIABLES),
            "rows": [{"id": row.row_id, "coefficients": [wire(v) for v in row.coefficients], "upper": wire(row.upper)} for row in self.rows],
        }


def parse_problem(value):
    require(type(value) is dict and set(value) == {"objective", "nonnegative", "rows"}, "Problem fields differ")
    require(value["nonnegative"] == list(VARIABLES), "Both x and y must be declared nonnegative")
    require(type(value["rows"]) is list, "rows must be an array")
    rows = []
    for row in value["rows"]:
        require(type(row) is dict and set(row) == {"id", "coefficients", "upper"}, "Row fields differ")
        rows.append(Row(row["id"], vector(row["coefficients"]), rational(row["upper"])))
    return Problem(vector(value["objective"]), tuple(rows))


def default_problem():
    f = Fraction
    return Problem((f(1), f(1)), (
        Row("ub1", (f(1), f(1)), f(2)),
        Row("ub2", (f(1), f(0)), f(2)),
        Row("ub3", (f(0), f(1)), f(2)),
    ))


def default_proposal():
    return {"primal": [[1, 2], [3, 2]], "dual": {"ub1": [1, 1], "ub2": [0, 1], "ub3": [0, 1]}}


def violations(problem, point):
    return (
        [f"domain:{v}>=0" for v, value in zip(VARIABLES, point, strict=True) if value < 0]
        + [row.row_id for row in problem.rows if dot(row.coefficients, point) > row.upper]
    )


def candidate_only(problem, value):
    point = vector(value)
    return {"status": "CANDIDATE_ONLY", "violated_constraints": violations(problem, point),
            "objective": wire(dot(problem.objective, point)), "optimality_certified": False}


def check_certificate(problem, proposal):
    require(type(proposal) is dict and {"primal", "dual"} <= set(proposal) <= {"primal", "dual", "alternative"}, "Certificate fields differ")
    point = vector(proposal["primal"])
    dual = proposal["dual"]
    require(type(dual) is dict and set(dual) == {row.row_id for row in problem.rows}, "Dual row identities must match all problem rows")
    multipliers = {name: rational(value) for name, value in dual.items()}
    primal_bad = violations(problem, point)
    dual_bad = [name for name, value in multipliers.items() if value < 0]
    coefficients = tuple(sum((multipliers[row.row_id] * row.coefficients[j] for row in problem.rows), Fraction(0)) for j in range(2))
    bound = sum((multipliers[row.row_id] * row.upper for row in problem.rows), Fraction(0))
    objective = dot(problem.objective, point)
    dominates = all(a >= c for a, c in zip(coefficients, problem.objective, strict=True))
    optimal = not primal_bad and not dual_bad and dominates and objective == bound
    alternative = None
    if "alternative" in proposal:
        other = vector(proposal["alternative"])
        alternative = {
            "point": [wire(v) for v in other],
            "violated_constraints": violations(problem, other),
            "distinct": other != point,
            "objective_matches": dot(problem.objective, other) == objective,
        }
        alternative["valid_nonuniqueness_witness"] = (
            optimal and not alternative["violated_constraints"] and alternative["distinct"]
            and alternative["objective_matches"]
        )
    return {
        "problem_sha256": digest(problem.payload()),
        "primal": [wire(v) for v in point],
        "checked_row_ids": [row.row_id for row in problem.rows],
        "checked_variable_domains": list(VARIABLES),
        "violated_constraints": primal_bad,
        "negative_dual_rows": dual_bad,
        "dual_coefficients": [wire(v) for v in coefficients],
        "dual_dominates_objective": dominates,
        "objective": wire(objective), "dual_bound": wire(bound),
        "gap": wire(bound - objective), "gap_zero": objective == bound,
        "optimality_certified": optimal,
        "alternative": alternative,
        "uniqueness": "NONUNIQUE" if alternative and alternative["valid_nonuniqueness_witness"] else "NOT_ESTABLISHED",
        "submission_accepted": optimal and (alternative is None or alternative["valid_nonuniqueness_witness"]),
    }


def check_trace(problem, proposal):
    require(type(proposal) is dict and set(proposal) == {"problem_sha256", "steps"}, "Trace fields differ")
    pinned = proposal["problem_sha256"]
    require(type(pinned) is str and re.fullmatch(r"[0-9a-f]{64}", pinned) is not None, "Trace needs a problem digest")
    steps = proposal["steps"]
    require(type(steps) is list and 2 <= len(steps) <= 32, "Trace needs 2 to 32 supplied states")
    checked = []
    for step in steps:
        require(type(step) is dict and set(step) == {"primal", "dual"}, "Each state needs only primal and dual")
        checked.append(check_certificate(problem, step))
    gaps = [Fraction(*row["gap"]) for row in checked]
    checks = {
        "problem_matches": pinned == digest(problem.payload()),
        "all_primal_feasible": all(not row["violated_constraints"] for row in checked),
        "all_dual_feasible": all(not row["negative_dual_rows"] and row["dual_dominates_objective"] for row in checked),
        "strictly_decreasing_gaps": all(after < before for before, after in zip(gaps, gaps[1:], strict=False)),
        "final_optimality_certified": checked[-1]["optimality_certified"],
    }
    return {"problem_sha256": digest(problem.payload()), "steps": checked,
            "gaps": [wire(gap) for gap in gaps], "checks": checks,
            "submission_accepted": all(checks.values()), "search_performed": False,
            "authority_effect": "None"}


def quiz03_problem():
    f = Fraction
    return Problem((f(3), f(2)), (
        Row("ub1", (f(1), f(1)), f(4)),
        Row("ub2", (f(1), f(0)), f(2)),
        Row("ub3", (f(0), f(1)), f(3)),
    ))


def quiz03_trace():
    return {"problem_sha256": digest(quiz03_problem().payload()), "steps": [
        {"primal": [[2, 1], [3, 2]], "dual": {"ub1": [2, 1], "ub2": [1, 1], "ub3": [0, 1]}},
        {"primal": [[2, 1], [2, 1]], "dual": {"ub1": [2, 1], "ub2": [1, 1], "ub3": [0, 1]}},
    ]}


def quiz03_cases():
    problem, trace = quiz03_problem(), quiz03_trace()
    loose = dict(trace["steps"][-1], dual={"ub1": [0, 1], "ub2": [3, 1], "ub3": [2, 1]})
    promotion_refused = False
    try:
        check_certificate(problem, dict(trace["steps"][-1], production_authorized=True))
    except InvalidInput:
        promotion_refused = True
    return {
        "quiz03.1": check_certificate(problem, trace["steps"][0]),
        "quiz03.2": check_trace(problem, trace),
        "quiz03.3": check_certificate(problem, loose),
        "quiz03.4": {"extra_authority_field_refused": promotion_refused, "authority_effect": "None"},
    }


def exercise_report():
    problem = default_problem()
    proposal = default_proposal()
    with_other = dict(proposal, alternative=[[0, 1], [2, 1]])
    false_point = dict(proposal, primal=[[-1, 1], [3, 1]])
    domain_example = Problem((Fraction(1), Fraction(1)), (Row("sum", (Fraction(1), Fraction(1)), Fraction(0)),))
    float_proposal = dict(proposal, primal=[[0.5, 1], [1.5, 1]])
    float_refused = False
    try:
        check_certificate(problem, float_proposal)
    except InvalidInput:
        float_refused = True
    return {
        "pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
        "problem": problem.payload(), "quiz03_problem": quiz03_problem().payload(),
        "cases": {
            "quiz19.1": check_certificate(problem, proposal),
            "quiz19.2": check_certificate(problem, with_other),
            "quiz19.3": {
                "original_problem": check_certificate(problem, false_point),
                "domain_only_problem": domain_example.payload(),
                "domain_only_counterexample": check_certificate(domain_example, {"primal": [[-1, 1], [1, 1]], "dual": {"sum": [1, 1]}}),
            },
            "quiz19.4": {"float_input_refused": float_refused, "interrupted_search": candidate_only(problem, proposal["primal"])},
            **quiz03_cases(),
        },
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidInput(f"Non-finite JSON number: {value}")


def read_document(path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    require(len(raw) <= MAX_INPUT_BYTES, "JSON document exceeds byte limit")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant), raw


def write_run(output_root, report, status, input_bytes, proposal_bytes=None):
    folder = output_root / uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "input.json").write_bytes(input_bytes)
    if proposal_bytes is not None:
        (folder / "proposal.json").write_bytes(proposal_bytes)
    receipt = {
        "pilot_id": PILOT_ID, "status": status, "network_calls": 0, "cost_usd": "0",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "result_sha256": digest(report),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "proposal_sha256": hashlib.sha256(proposal_bytes).hexdigest() if proposal_bytes is not None else None,
    }
    for name, payload in (("result.json", report), ("receipt.json", receipt)):
        with (folder / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (folder / "summary.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {PILOT_ID}\n\nStatus: {status}.\n\nExact two-variable certificate checks; no search, model call or applied solution.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Custom problem JSON (requires --proposal or --trace)")
    submission = parser.add_mutually_exclusive_group()
    submission.add_argument("--proposal", type=Path, help="Certificate JSON; defaults to the Quiz 19 problem")
    submission.add_argument("--trace", type=Path, help="Supplied gap-reduction trace, not an optimizer")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        require(not args.input or args.proposal or args.trace, "Custom problem requires a proposal or trace")
        if args.input:
            payload, input_bytes = read_document(args.input)
            problem = parse_problem(payload)
        else:
            problem = default_problem()
            input_bytes = canonical(problem.payload()).encode("ascii")
        proposal_bytes = None
        if args.proposal or args.trace:
            proposal, proposal_bytes = read_document(args.proposal or args.trace)
            checked = check_trace(problem, proposal) if args.trace else check_certificate(problem, proposal)
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None", "problem": problem.payload(),
                      "trace" if args.trace else "certificate": checked}
            status = "ACCEPTED" if checked["submission_accepted"] else "REJECTED"
        else:
            report = exercise_report()
            status = "COMPUTED"
        folder = write_run(args.output_dir, report, status, input_bytes, proposal_bytes)
    except (InvalidInput, OSError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder)}, ensure_ascii=True))
    return 1 if status == "REJECTED" else 0


if __name__ == "__main__":
    sys.exit(main())
