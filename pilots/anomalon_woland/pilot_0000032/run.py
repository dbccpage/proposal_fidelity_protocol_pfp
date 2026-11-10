"""Quiz 07: three-sector normalization, checked lifts and an explicit Born assumption.

Exact finite-dimensional examples; no derivation of Born uniqueness, general
quantum theory, Genesis stages, or permission to apply a proposal.
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

PILOT_ID = "pilot_0000032"
MAX_INPUT_BYTES = 65536
BORN_ASSUMPTION = "Born rule in declared basis a,b,c"


class InvalidInput(ValueError):
    """Input is outside the declared three-sector exact interface."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Fields differ from the declared contract")


def integer(value, bound=10**9):
    require(type(value) is int and abs(value) <= bound, "Bounded integer required, not bool/float")
    return value


def rational(value, bound=10**9):
    require(type(value) is list and len(value) == 2, "Use [numerator,denominator]")
    n, d = (integer(v, bound) for v in value)
    require(d > 0 and math.gcd(n, d) == 1, "Rational needs positive denominator and reduced components")
    return F(n, d)


def rational_vector(value, bound=10**9):
    require(type(value) is list and len(value) == 3, "Exactly three sectors required")
    return [rational(v, bound) for v in value]


def wire(value):
    return [value.numerator, value.denominator]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def default_problem():
    return {"kind": "weights", "weights": [2, 1, 0]}


def normalize(problem):
    fields(problem, ("kind", "weights"))
    require(problem["kind"] == "weights", "Expected weight problem")
    raw = problem["weights"]
    require(type(raw) is list and len(raw) == 3, "Exactly three weights required")
    weights = [integer(w) for w in raw]
    require(all(w >= 0 for w in weights), "Every weight must be nonnegative")
    total = sum(weights)
    require(total > 0, "Total weight must be positive")
    probabilities = [F(w, total) for w in weights]
    return {"kind": "weights", "problem": problem, "total": total,
            "probabilities": [wire(p) for p in probabilities],
            "square_root_lift": [{"nonnegative_sqrt_of": wire(p)} for p in probabilities],
            "basis": ["a", "b", "c"], "identity_is_by_construction": True}


def check_lift(problem, proposal):
    result = normalize(problem)
    fields(proposal, ("total", "probabilities", "lift_radicands"))
    total = integer(proposal["total"], 3 * 10**9)
    probabilities = rational_vector(proposal["probabilities"], 3 * 10**18)
    radicands = rational_vector(proposal["lift_radicands"], 3 * 10**18)
    expected = [F(*value) for value in result["probabilities"]]
    checks = {"total_matches": total == result["total"],
              "probabilities_match_weights": probabilities == expected,
              "lift_radicands_match_weights": radicands == expected}
    return {"submission_accepted": all(checks.values()), "checks": checks,
            "problem_sha256": digest(problem), "expected": result, "proposal": proposal,
            "lift_identity": "|sqrt(p)|^2=p for the declared nonnegative root"}


def representation_comparison(problem):
    result = normalize(problem)
    probabilities = [F(*v) for v in result["probabilities"]]
    different_coordinates = [i for i, p in enumerate(probabilities) if p*p != p]
    return {
        "simplex": {"encoding": result["probabilities"], "readout": "identity",
                    "result": result["probabilities"]},
        "square_root": {"encoding": result["square_root_lift"], "readout": "squared_magnitude",
                        "result": [entry["nonnegative_sqrt_of"] for entry in result["square_root_lift"]]},
        "coordinates_where_sqrt_p_differs_from_p": different_coordinates,
        "same_probability_readout": True,
        "born_uniqueness": "NOT_ESTABLISHED",
        "scope": "Two declared representation/readout pairs, not a counterexample to quantum uniqueness theorems",
    }


def amplitude_readout(problem):
    fields(problem, ("kind", "amplitudes", "assumption"))
    require(problem["kind"] == "amplitudes", "Expected amplitude problem")
    amplitudes = rational_vector(problem["amplitudes"])
    squares = [a*a for a in amplitudes]
    require(sum(squares) == 1, "Amplitudes must have squared norm one")
    assumption = problem["assumption"]
    require(assumption is None or assumption == BORN_ASSUMPTION, "Unknown external assumption")
    interpreted = assumption == BORN_ASSUMPTION
    return {"kind": "amplitudes", "problem": problem, "squared_components": [wire(v) for v in squares],
            "squared_norm": wire(sum(squares)), "assumption": assumption,
            "probability_interpretation": "EXTERNALLY_ASSUMED" if interpreted else "NOT_SUPPLIED",
            "probabilities": [wire(v) for v in squares] if interpreted else None,
            "born_rule_derived": False, "authority_effect": "None"}


def calculate(problem):
    require(type(problem) is dict and problem.get("kind") in ("weights", "amplitudes"), "Unknown problem kind")
    return normalize(problem) if problem["kind"] == "weights" else amplitude_readout(problem)


def check_proposal(problem, proposal):
    result = calculate(problem)
    if result["kind"] == "weights":
        return check_lift(problem, proposal)
    fields(proposal, ("probabilities",))
    probabilities = rational_vector(proposal["probabilities"], 3 * 10**18)
    interpreted = result["probabilities"] is not None
    accepted = interpreted and probabilities == [F(*v) for v in result["probabilities"]]
    return {"submission_accepted": accepted, "interpretation_supplied": interpreted,
            "expected": result, "proposal": proposal}


def exercise_report():
    problem = default_problem()
    proposal = {"total": 3, "probabilities": [[2, 3], [1, 3], [0, 1]],
                "lift_radicands": [[2, 3], [1, 3], [0, 1]]}
    amplitudes = {"kind": "amplitudes", "amplitudes": [[3, 5], [4, 5], [0, 1]], "assumption": BORN_ASSUMPTION}
    return {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
            "cases": {"quiz07.1": normalize(problem), "quiz07.2": check_lift(problem, proposal),
                      "quiz07.3": representation_comparison(problem),
                      "quiz07.4": {"with_assumption": amplitude_readout(amplitudes),
                                   "without_assumption": amplitude_readout(dict(amplitudes, assumption=None))}}}


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
        stream.write(f"# {PILOT_ID}\n\nStatus: {status}.\n\nExact three-sector normalization and checked lift; Born probability interpretation is an explicit assumption, not a derived law.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Three weights or explicitly declared amplitudes")
    parser.add_argument("--proposal", type=Path, help="Lift certificate or proposed probabilities")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        problem, input_bytes = read_document(args.input) if args.input else (default_problem(), canonical(default_problem()).encode("ascii"))
        proposal_bytes = None
        if args.input or args.proposal:
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
                      "calculation": calculate(problem)}
            status = "COMPUTED"
            if args.proposal:
                proposal, proposal_bytes = read_document(args.proposal)
                report["certificate"] = check_proposal(problem, proposal)
                status = "ACCEPTED" if report["certificate"]["submission_accepted"] else "REJECTED"
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

