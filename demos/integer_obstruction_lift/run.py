"""Quiz 17: exact integer obstruction and explicitly separate rational lifts.

Scalar multiplication and three-edge rank-one-kernel certificates only.
No homology search, carrier authorization, model call or applied repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from uuid import uuid4

PILOT_ID = "pilot_0000029"
MAX_INPUT_BYTES = 65536
COMPONENT_LIMIT = 10**9


class InvalidInput(ValueError):
    """Input lies outside this pilot's bounded exact-integer interface."""


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def integer(value):
    require(type(value) is int and abs(value) <= COMPONENT_LIMIT, "Expected bounded integer, not bool/float")
    return value


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), "Fields differ from the declared contract")


def vector(value, length=3):
    require(type(value) is list and len(value) == length, "Vector has the wrong dimension")
    return [integer(x) for x in value]


def matrix(value, columns):
    require(type(value) is list and len(value) == 3, "Matrix requires three rows")
    return [vector(row, columns) for row in value]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def quotient_label(divisor):
    return "Z" if divisor == 0 else ("0" if divisor == 1 else f"Z/{divisor}Z")


def scalar_problem(value):
    fields(value, ("kind", "multiplier", "target"))
    require(value["kind"] == "scalar", "Expected scalar problem")
    m, z = integer(value["multiplier"]), integer(value["target"])
    require(m != 0, "This scalar experiment requires a nonzero multiplier")
    return m, z


def default_problem():
    return {"kind": "scalar", "multiplier": 2, "target": 1}


def scalar_report(problem):
    m, z = scalar_problem(problem)
    d = abs(m)
    q, r = divmod(z, d)
    sign = 1 if m > 0 else -1
    neighbours = (sign * q, sign * (q + 1))
    minimum = min(r, d - r)
    minimizers = sorted(c for c in neighbours if abs(z - m * c) == minimum)
    half = Fraction(z, m)
    return {
        "problem": problem, "chain_law": True, "target_closed": True,
        "integer_boundary": r == 0, "integer_witness": z // m if r == 0 else None,
        "integer_H1": quotient_label(d), "integer_H0": "Z",
        "divisibility": {"modulus": d, "multiplier_remainder": m % d, "target_remainder": r},
        "rational_witness": [half.numerator, half.denominator],
        "rational_H1": "0", "rational_H0": "Q", "rational_complex_acyclic": False,
        "minimum": {"min_abs": minimum, "minimizers": minimizers,
                    "signed_residuals": [z - m * c for c in minimizers],
                    "division": {"q": q, "r": r, "d": d},
                    "completeness_basis": "z=q*d+r, 0<=r<d; nearest multiples are q*d and (q+1)*d"},
    }


def scalar_check(problem, proposal):
    m, z = scalar_problem(problem)
    if type(proposal) is dict and "carrier" in proposal:
        fields(proposal, ("carrier", "witness"))
        require(proposal["carrier"] in ("Z", "Q"), "Declare carrier Z or Q")
        parts = vector(proposal["witness"], 2)
        n, d = parts
        require(d > 0 and math.gcd(n, d) == 1, "Rational needs positive denominator and reduced components")
        admitted = proposal["carrier"] == "Q" or d == 1
        equality = m * n == z * d
        return {"submission_accepted": admitted and equality,
                "carrier": proposal["carrier"], "witness": parts,
                "coefficient_admitted": admitted, "rational_equality": equality,
                "original_integer_problem_solved": admitted and d == 1 and equality,
                "carrier_change_authorized": False}
    fields(proposal, ("min_abs", "minimizers"))
    bound = integer(proposal["min_abs"])
    require(bound >= 0, "Minimum absolute residual cannot be negative")
    require(type(proposal["minimizers"]) is list and 1 <= len(proposal["minimizers"]) <= 2, "List one or two proposed minimizers")
    candidates = [integer(c) for c in proposal["minimizers"]]
    expected = scalar_report(problem)["minimum"]
    distinct = len(set(candidates)) == len(candidates)
    complete = distinct and sorted(candidates) == expected["minimizers"]
    return {"submission_accepted": bound == expected["min_abs"] and complete,
            "minimum_matches": bound == expected["min_abs"],
            "complete_minimizers": complete, "distinct": distinct,
            "expected": expected, "proposal": proposal}


def triangle_problem(filled):
    require(type(filled) is bool, "Face admission must be explicit boolean")
    return {"kind": "triangle", "d1": [[-1, -1, 0], [1, 0, -1], [0, 1, 1]],
            "d2": [[1], [-1], [1]] if filled else [[], [], []], "target": [1, -1, 1]}


def triangle_proof():
    return {"generator": [1, -1, 1], "coordinate": [1, 0, 0],
            "factor": [[0, 0, 0], [-1, 0, 0], [0, -1, 0]]}


def triangle_check(problem, proof):
    fields(problem, ("kind", "d1", "d2", "target"))
    require(problem["kind"] == "triangle", "Expected three-edge complex")
    d1 = matrix(problem["d1"], 3)
    raw_d2 = problem["d2"]
    require(type(raw_d2) is list and len(raw_d2) == 3 and type(raw_d2[0]) is list
            and len(raw_d2[0]) in (0, 1), "C2 has rank zero or one")
    columns = len(raw_d2[0])
    d2 = matrix(raw_d2, columns)
    z = vector(problem["target"])
    fields(proof, ("generator", "coordinate", "factor"))
    g, p, a = vector(proof["generator"]), vector(proof["coordinate"]), matrix(proof["factor"], 3)
    checks = {
        "chain_law": all(dot(row, [d2[i][j] for i in range(3)]) == 0 for row in d1 for j in range(columns)),
        "target_closed": all(dot(row, z) == 0 for row in d1),
        "generator_closed": all(dot(row, g) == 0 for row in d1),
        "coordinate_splits_generator": dot(p, g) == 1,
        "kernel_identity": all(
            int(i == j) - g[i] * p[j] == dot(a[i], [d1[k][j] for k in range(3)])
            for i in range(3) for j in range(3)),
    }
    accepted = all(checks.values())
    result = {"submission_accepted": accepted, "checks": checks, "C2_rank": columns,
              "integer_H1": None, "target_is_boundary": None, "boundary_witness": None}
    if accepted:
        generator_multiple = dot(p, [row[0] for row in d2]) if columns else 0
        coordinate = dot(p, z)
        divisor = abs(generator_multiple)
        boundary = coordinate == 0 if divisor == 0 else coordinate % divisor == 0
        result.update(integer_H1=quotient_label(divisor), target_coordinate=coordinate,
                      boundary_generator_multiple=generator_multiple, target_is_boundary=boundary)
        if boundary:
            result["boundary_witness"] = ([coordinate // generator_multiple if generator_multiple else 0]
                                          if columns else [])
    return result


def exercise_report():
    problem = default_problem()
    scalar = scalar_report(problem)
    proofs = triangle_proof()
    hollow, filled = triangle_problem(False), triangle_problem(True)
    return {
        "pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
        "cases": {
            "quiz17.1": scalar,
            "quiz17.2": {"Z": scalar_check(problem, {"carrier": "Z", "witness": [1, 2]}),
                        "Q": scalar_check(problem, {"carrier": "Q", "witness": [1, 2]})},
            "quiz17.3": {"certificate": scalar_check(problem, {"min_abs": 1, "minimizers": [0, 1]}),
                        "mean_signed_residual": [0, 1], "mean_witness": [1, 2],
                        "mean_solves_integer_problem": False, "repair_applied": False},
            "quiz17.4": {"hollow_problem": hollow, "filled_problem": filled, "kernel_certificate": proofs,
                        "hollow": triangle_check(hollow, proofs), "filled": triangle_check(filled, proofs),
                        "face_admission_inferred_from_edges": False},
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
        stream.write(f"# {PILOT_ID}\n\nStatus: {status}.\n\nExact scalar and matrix-certificate checks; no authorized carrier change or applied repair.\n\nResult SHA-256: {receipt['result_sha256']}.\n")
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Declared scalar or three-edge problem (requires --proposal)")
    parser.add_argument("--proposal", type=Path, help="Witness, minimum or kernel certificate JSON")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent / "pilot_output" / PILOT_ID)
    args = parser.parse_args(argv)
    try:
        require(not args.input or args.proposal, "Custom problem requires a proposal")
        problem, input_bytes = read_document(args.input) if args.input else (default_problem(), canonical(default_problem()).encode("ascii"))
        proposal_bytes = None
        if args.proposal:
            proposal, proposal_bytes = read_document(args.proposal)
            require(type(problem) is dict and problem.get("kind") in ("scalar", "triangle"), "Unknown problem kind")
            checked = scalar_check(problem, proposal) if problem["kind"] == "scalar" else triangle_check(problem, proposal)
            report = {"pilot_id": PILOT_ID, "kind": "NO_LLM", "authority_effect": "None",
                      "problem": problem, "certificate": checked}
            status = "ACCEPTED" if checked["submission_accepted"] else "REJECTED"
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

