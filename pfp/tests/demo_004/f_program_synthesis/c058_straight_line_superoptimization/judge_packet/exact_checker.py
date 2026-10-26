"""Exact certificate checker for C058 Straight-Line Superoptimization."""

from typing import Any, Dict, Tuple

from .evaluator import (
    execute_program,
    generate_test_inputs,
    validate_ir,
    verify_equivalence,
)


def verify_candidate(case: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """Verifies candidate response against problem case using exact semantics.

    Returns:
        (is_valid, message)
    """
    if not isinstance(candidate, dict):
        return False, "CANDIDATE_NOT_A_DICT"

    if "case_id" not in candidate:
        return False, "MISSING_CASE_ID"
    if candidate["case_id"] != case.get("case_id"):
        return (
            False,
            f"CASE_ID_MISMATCH: expected {case.get('case_id')}, got {candidate['case_id']}",
        )

    status = candidate.get("status")
    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:
        return False, f"INVALID_STATUS: {status}"

    # Check if case itself is invalid / out of scope
    case_is_valid, err_code, _ = validate_ir(case)
    if not case_is_valid:
        if status != "OUT_OF_SCOPE":
            return False, f"EXPECTED_OUT_OF_SCOPE_FOR_POISONED_CASE, got {status}"
        return True, "OUT_OF_SCOPE_CORRECTLY_IDENTIFIED"

    if status == "OUT_OF_SCOPE":
        return False, f"FALSE_OUT_OF_SCOPE_ON_VALID_CASE: case was well-formed ({err_code})"

    target_len = case.get("target_len", len(case.get("ops", [])) - 1)

    if status == "UNKNOWN":
        # Candidate claims no shorter program exists
        code = candidate.get("code")
        if code != "NO_SHORTER_FOUND":
            return False, f"INVALID_UNKNOWN_CODE: {code}"
        # If target_len was already >= input length, claiming UNKNOWN is invalid
        if target_len >= len(case.get("ops", [])):
            return (
                False,
                "FALSE_UNKNOWN: target_len >= input length can always be satisfied by input program",
            )
        if target_len > 0:
            return False, f"FALSE_UNKNOWN: shorter program exists for target_len {target_len}"

        # target_len == 0: check if case program reduces to a 0-op output (input variable or constant)
        ops = case["ops"]
        out_var = case["out"]
        inputs = case["inputs"]
        width = case["width"]
        test_inputs = generate_test_inputs(inputs, width)
        for inp_name in inputs:
            if all(execute_program(ops, out_var, ti, width) == ti[inp_name] for ti in test_inputs):
                return False, f"FALSE_UNKNOWN: program reduces to 0-op input {inp_name}"
        first_val = execute_program(ops, out_var, test_inputs[0], width)
        if all(execute_program(ops, out_var, ti, width) == first_val for ti in test_inputs):
            return False, f"FALSE_UNKNOWN: program reduces to 0-op constant {first_val}"
        return True, "WARRANTED_REFUSAL: UNKNOWN_ACCEPTED: NO_SHORTER_FOUND"

    # status == "SOLVED"
    cand_ops = candidate.get("ops")
    cand_out = candidate.get("out")

    if not isinstance(cand_ops, list):
        return False, "OPS_MUST_BE_LIST"
    if not isinstance(cand_out, str):
        return False, "OUT_MUST_BE_STRING"

    if len(cand_ops) > target_len:
        return False, f"LENGTH_EXCEEDS_TARGET: got {len(cand_ops)}, target_len is {target_len}"

    # Validate candidate IR structure
    cand_case = {
        "width": case["width"],
        "inputs": case["inputs"],
        "ops": cand_ops,
        "out": cand_out,
        "target_len": target_len,
    }
    cand_valid, cand_err, cand_wit = validate_ir(cand_case)
    if not cand_valid:
        return False, f"CANDIDATE_IR_INVALID: {cand_err} ({cand_wit})"

    # Verify semantic equivalence against original program
    is_equiv, counterexample, vals = verify_equivalence(
        case["ops"], case["out"], cand_ops, cand_out, case["inputs"], case["width"]
    )

    if not is_equiv:
        return (
            False,
            f"NOT_EQUIVALENT: on input {counterexample}, original gave {vals[0]}, candidate gave {vals[1]}",
        )

    return True, "CERTIFICATE_VERIFIED_VALID"
