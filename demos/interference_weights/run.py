"""Quiz 20: exact interference in an externally declared two-state model.

Born probabilities and a fixed Hadamard operator are assumptions, not derived
from weights, Primitive Difference or a model proposal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000031"
MAX_INPUT_BYTES = 65536
MODEL = {
    "state_dimension": 2, "basis": ["0", "1"], "measurement": "Born in declared computational basis",
    "operator": {"numerator_matrix": [[1, 1], [1, -1]], "denominator": "sqrt(2)"},
    "source": "externally declared Hilbert model", "born_uniqueness_derived": False,
    "genesis_lift_derived": False, "quantum_computing_conclusion": "NOT_ESTABLISHED",
}


class InvalidInput(ValueError):
    """Input violates the exact two-state experiment's declared interface."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Fields differ from declared contract")


def rational(value, component_limit=10**9):
    require(type(value) is list and len(value) == 2, "Use [numerator,denominator]")
    n, d = value
    require(type(n) is int and type(d) is int, "Integer components only, not bool/float")
    require(abs(n) <= component_limit and 0 < d <= component_limit, "Rational exceeds bounds or denominator is nonpositive")
    require(math.gcd(n, d) == 1, "Rational must be reduced")
    return F(n, d)


def wire(value):
    return [value.numerator, value.denominator]


def gaussian(value):
    require(type(value) is list and len(value) == 2, "Gaussian rational is [real,imaginary]")
    return tuple(rational(v) for v in value)


def gwire(value):
    return [wire(v) for v in value]


def add(x, y):
    return x[0] + y[0], x[1] + y[1]


def scale(x, factor):
    return factor * x[0], factor * x[1]


def norm_squared(x):
    return x[0] * x[0] + x[1] * x[1]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def default_problem():
    return {"kind": "interference", "relative_sign": 1, "global_phase": [[1, 1], [0, 1]]}


def interference(problem):
    fields(problem, ("kind", "relative_sign", "global_phase"))
    require(problem["kind"] == "interference", "Expected interference problem")
    sign = problem["relative_sign"]
    require(type(sign) is int and sign in (-1, 1), "Relative sign is exactly -1 or 1")
    phase = gaussian(problem["global_phase"])
    require(norm_squared(phase) == 1, "Global phase must have exact unit modulus")
    numerators = (phase, scale(phase, sign))
    # H(v/sqrt(2)) = Mv/2, where M=[[1,1],[1,-1]].
    post = (scale(add(numerators[0], numerators[1]), F(1, 2)),
            scale(add(numerators[0], scale(numerators[1], -1)), F(1, 2)))
    return {
        "kind": "interference", "problem": problem, "model": MODEL, "model_sha256": digest(MODEL),
        "input_state": {"numerators": [gwire(v) for v in numerators], "common_denominator": "sqrt(2)"},
        "input_probabilities": [wire(norm_squared(v) / 2) for v in numerators],
        "post_h_amplitudes": [gwire(v) for v in post],
        "post_h_probabilities": [wire(norm_squared(v)) for v in post],
        "carrier_change_authorized": False,
    }


def weight_lift(problem):
    fields(problem, ("kind", "weights"))
    require(problem["kind"] == "weights", "Expected two-sector weights")
    raw = problem["weights"]
    require(type(raw) is list and len(raw) == 2, "Declare two sector weights")
    weights = [rational(v) for v in raw]
    require(all(v >= 0 for v in weights), "Every sector weight must be nonnegative")
    total = sum(weights)
    require(total > 0, "Positive total weight required; no uniform fallback")
    probabilities = [v / total for v in weights]
    return {
        "kind": "weights", "problem": problem, "total_weight": wire(total),
        "square_root_lift": [{"nonnegative_sqrt_of": wire(v)} for v in probabilities],
        "basis_probabilities": [wire(v) for v in probabilities],
        "identity_basis": "|sqrt(w/W)|^2=w/W under the declared nonnegative lift and Born rule",
        "phase_reconstruction": "NOT_ATTEMPTED", "post_h_prediction": "NOT_EVALUATED_BY_WEIGHT_LIFT",
        "born_uniqueness_derived": False, "carrier_change_authorized": False,
    }


def calculate(problem):
    require(type(problem) is dict and problem.get("kind") in ("interference", "weights"), "Unknown problem kind")
    return interference(problem) if problem["kind"] == "interference" else weight_lift(problem)


def check_prediction(report, proposal):
    key = "post_h_probabilities" if report["kind"] == "interference" else "basis_probabilities"
    fields(proposal, (key,))
    values = proposal[key]
    require(type(values) is list and len(values) == 2, "Prediction requires two exact probabilities")
    proposed = [rational(v, 2 * 10**18) for v in values]
    expected = [F(*v) for v in report[key]]
    return {"submission_accepted": proposed == expected, "field": key,
            "proposed": values, "expected": report[key], "scope": report["kind"]}


def exercise_report():
    plus = interference(default_problem())
    minus = interference(dict(default_problem(), relative_sign=-1))
    global_minus = interference(dict(default_problem(), global_phase=[[-1, 1], [0, 1]]))
    refused = {}
    for name, weights in (("zero_total", [[0, 1], [0, 1]]), ("negative_weight", [[-1, 1], [2, 1]])):
        try:
            weight_lift({"kind": "weights", "weights": weights})
        except InvalidInput as error:
            refused[name] = {"weights": weights, "status": "REFUSED", "reason": str(error)}
    return {
        "pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None", "model": MODEL,
        "cases": {
            "quiz20.1": {"plus": plus, "minus": minus,
                        "equal_initial_probabilities": plus["input_probabilities"] == minus["input_probabilities"],
                        "different_amplitudes": plus["input_state"] != minus["input_state"]},
            "quiz20.2": {"plus": plus["post_h_amplitudes"], "minus": minus["post_h_amplitudes"],
                        "different_probabilities": plus["post_h_probabilities"] != minus["post_h_probabilities"],
                        "weights_determine_post_h": False},
            "quiz20.3": {"global_minus": global_minus,
                        "probabilities_unchanged": plus["post_h_probabilities"] == global_minus["post_h_probabilities"],
                        "amplitudes_changed": plus["post_h_amplitudes"] != global_minus["post_h_amplitudes"]},
            "quiz20.4": {"lift": weight_lift({"kind": "weights", "weights": [[2, 1], [3, 1]]}),
                        "refusals": refused},
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
        "result_sha256": digest(report), "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "proposal_sha256": hashlib.sha256(proposal_bytes).hexdigest() if proposal_bytes is not None else None,
    }
    for name, payload in (("result.json", report), ("receipt.json", receipt)):
        with (folder / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (folder / "summary.md").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(f"# {PILOT_ID}\n\nStatus: {status}.\n\nExact two-state calculation under an imported Born/Hadamard model; no quantum-computing conclusion or applied change.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Declared interference or weight-lift problem")
    parser.add_argument("--proposal", type=Path, help="Exact proposed probabilities to check")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        problem, input_bytes = read_document(args.input) if args.input else (default_problem(), canonical(default_problem()).encode("ascii"))
        proposal_bytes = None
        if args.input or args.proposal:
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None", "calculation": calculate(problem)}
            status = "COMPUTED"
            if args.proposal:
                proposal, proposal_bytes = read_document(args.proposal)
                report["prediction"] = check_prediction(report["calculation"], proposal)
                status = "ACCEPTED" if report["prediction"]["submission_accepted"] else "REJECTED"
        else:
            report, status = exercise_report(), "COMPUTED"
        folder = write_run(args.output_dir, report, status, input_bytes, proposal_bytes)
    except (InvalidInput, OSError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}, ensure_ascii=True))
        return 2
    print(json.dumps({"status": status, "output": str(folder)}, ensure_ascii=True))
    return 1 if status == "REJECTED" else 0


if __name__ == "__main__":
    sys.exit(main())
