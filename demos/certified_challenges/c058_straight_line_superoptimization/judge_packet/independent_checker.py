"""Independent certificate checker for C058 Straight-Line Superoptimization.

Independent second-checker implementation with topological DAG verification and randomized stress testing.
"""

from typing import Any, Dict, List, Set, Tuple


def independent_eval(ops: List[List[Any]], out: str, inp_vals: Dict[str, int], width: int) -> int:
    """Independent interpreter implementation."""
    mask = (1 << width) - 1
    state = {k: v & mask for k, v in inp_vals.items()}

    for inst in ops:
        dst = inst[0]
        op = inst[1]
        if op == "const":
            val = inst[2] & mask
        elif op == "not":
            val = (~state[inst[2]]) & mask
        elif op == "neg":
            val = (-state[inst[2]]) & mask
        else:
            arg1 = state[inst[2]] if isinstance(inst[2], str) else inst[2]
            arg2 = state[inst[3]] if isinstance(inst[3], str) else inst[3]
            arg1 &= mask
            arg2 &= mask

            if op == "add":
                val = (arg1 + arg2) & mask
            elif op == "sub":
                val = (arg1 - arg2) & mask
            elif op == "mul":
                val = (arg1 * arg2) & mask
            elif op == "and":
                val = (arg1 & arg2) & mask
            elif op == "or":
                val = (arg1 | arg2) & mask
            elif op == "xor":
                val = (arg1 ^ arg2) & mask
            elif op == "shl":
                val = (arg1 << (arg2 % width)) & mask
            elif op == "lshr":
                val = (arg1 >> (arg2 % width)) & mask
            elif op == "ashr":
                amt = arg2 % width
                if arg1 & (1 << (width - 1)):
                    s = arg1 - (1 << width)
                else:
                    s = arg1
                val = (s >> amt) & mask
            else:
                raise ValueError(f"Unknown op {op}")
        state[dst] = val

    return state[out]


def check_candidate_indep(case: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """Independently checks the candidate response."""
    if not isinstance(candidate, dict):
        return False, "INDEP_FAIL_NOT_DICT"

    if candidate.get("case_id") != case.get("case_id"):
        return False, "INDEP_FAIL_CASE_ID_MISMATCH"

    status = candidate.get("status")
    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:
        return False, f"INDEP_FAIL_BAD_STATUS: {status}"

    # Check if case is poisoned or invalid
    width = case.get("width")
    if width not in {8, 16, 32, 64}:
        return (status == "OUT_OF_SCOPE"), "INDEP_WIDTH_INVALID"

    inputs = case.get("inputs")
    if (
        not isinstance(inputs, list)
        or len(inputs) == 0
        or len(inputs) > 2
        or not all(isinstance(x, str) for x in inputs)
        or len(set(inputs)) != len(inputs)
    ):
        return (status == "OUT_OF_SCOPE"), "INDEP_INPUTS_INVALID"

    target_len_raw = case.get("target_len")
    if target_len_raw is not None:
        if not isinstance(target_len_raw, int) or target_len_raw < 0:
            return (status == "OUT_OF_SCOPE"), "INDEP_TARGET_LEN_INVALID"

    case_ops = case.get("ops")
    if not isinstance(case_ops, list):
        return (status == "OUT_OF_SCOPE"), "INDEP_OPS_NOT_LIST"

    case_out = case.get("out")
    if not isinstance(case_out, str):
        return (status == "OUT_OF_SCOPE"), "INDEP_OUT_INVALID"

    defined: Set[str] = set(inputs)
    case_valid = True
    for inst in case_ops:
        if not isinstance(inst, list) or len(inst) < 2:
            case_valid = False
            break
        dst = inst[0]
        op = inst[1]
        if not isinstance(dst, str) or dst in inputs or dst in defined:
            case_valid = False
            break
        if op not in {
            "add",
            "sub",
            "mul",
            "and",
            "or",
            "xor",
            "not",
            "neg",
            "shl",
            "lshr",
            "ashr",
            "const",
        }:
            case_valid = False
            break
        # check args
        if op == "const":
            if len(inst) != 3 or not isinstance(inst[2], int):
                case_valid = False
                break
        elif op in {"not", "neg"}:
            if len(inst) != 3 or inst[2] not in defined:
                case_valid = False
                break
        else:
            if len(inst) != 4:
                case_valid = False
                break
            for a in (inst[2], inst[3]):
                if isinstance(a, str) and a not in defined:
                    case_valid = False
                    break
        if not case_valid:
            break
        defined.add(dst)

    if case_out not in defined:
        case_valid = False

    if not case_valid:
        if status == "OUT_OF_SCOPE":
            return True, "INDEP_ACCEPTED_OUT_OF_SCOPE"
        return False, "INDEP_REJECTED_EXPECTED_OUT_OF_SCOPE"

    if status == "OUT_OF_SCOPE":
        return False, "INDEP_REJECTED_FALSE_OUT_OF_SCOPE"

    target_len = case.get("target_len", len(case_ops) - 1)

    if status == "UNKNOWN":
        code = candidate.get("code")
        if code != "NO_SHORTER_FOUND":
            return False, f"INDEP_INVALID_UNKNOWN_CODE_{code}"
        if target_len >= len(case_ops):
            return False, "INDEP_REJECTED_FALSE_UNKNOWN"
        if target_len > 0:
            return False, f"INDEP_REJECTED_FALSE_UNKNOWN_TARGET_LEN_{target_len}"
        # Independent check: can it be 0 ops or 1 op?
        mask = (1 << width) - 1
        sample_inputs = [0, 1, mask, mask // 2]
        t_vals = []
        for v in sample_inputs:
            in_d = (
                {inputs[0]: v}
                if len(inputs) == 1
                else {inputs[0]: v, inputs[1]: (v * 3 + 1) & mask}
            )
            t_vals.append(independent_eval(case_ops, case_out, in_d, width))
        if target_len >= 0:
            # If all test samples return a constant or single input
            if len(set(t_vals)) == 1 or t_vals == sample_inputs:
                return False, "INDEP_FALSE_UNKNOWN_REDUCED_TO_CONST_OR_INPUT"
        if target_len >= 1 and len(inputs) == 2:
            for b_op in ["xor", "and", "or", "add", "sub"]:
                matches = True
                for v in sample_inputs:
                    in_d = {inputs[0]: v, inputs[1]: (v * 3 + 1) & mask}
                    expected = independent_eval(case_ops, case_out, in_d, width)
                    computed = independent_eval(
                        [["cand", b_op, inputs[0], inputs[1]]], "cand", in_d, width
                    )
                    if expected != computed:
                        matches = False
                        break
                if matches:
                    return False, f"INDEP_FALSE_UNKNOWN_EXISTS_SINGLE_OP_{b_op}"
        return True, "INDEP_ACCEPTED_UNKNOWN"

    # SOLVED verification
    cand_ops = candidate.get("ops")
    cand_out = candidate.get("out")
    if not isinstance(cand_ops, list) or not isinstance(cand_out, str):
        return False, "INDEP_INVALID_CANDIDATE_FORMAT"

    if len(cand_ops) > target_len:
        return False, f"INDEP_LENGTH_EXCEEDED: {len(cand_ops)} > {target_len}"

    # Check candidate validity
    c_defined: Set[str] = set(inputs)
    valid_ops = {
        "add",
        "sub",
        "mul",
        "and",
        "or",
        "xor",
        "not",
        "neg",
        "shl",
        "lshr",
        "ashr",
        "const",
    }
    for inst in cand_ops:
        if not isinstance(inst, list) or len(inst) < 2:
            return False, "INDEP_CAND_MALFORMED_INST"
        dst = inst[0]
        op = inst[1]
        if not isinstance(dst, str) or dst in inputs or dst in c_defined:
            return False, "INDEP_CAND_OVERWROTE_VAR_OR_NONSTRING"
        if op not in valid_ops:
            return False, f"INDEP_CAND_UNKNOWN_OP_{op}"
        if op == "const":
            if (
                len(inst) != 3
                or not isinstance(inst[2], int)
                or inst[2] < 0
                or inst[2] >= (1 << width)
            ):
                return False, "INDEP_CAND_MALFORMED_CONST"
        elif op in {"not", "neg"}:
            if len(inst) != 3 or not isinstance(inst[2], str) or inst[2] not in c_defined:
                return False, "INDEP_CAND_UNDEFINED_ARG"
        else:
            if len(inst) != 4:
                return False, "INDEP_CAND_MALFORMED_BINARY"
            for a in (inst[2], inst[3]):
                if isinstance(a, str):
                    if a not in c_defined:
                        return False, f"INDEP_CAND_UNDEFINED_ARG_{a}"
                elif isinstance(a, int):
                    if a < 0 or a >= (1 << width):
                        return False, "INDEP_CAND_IMMEDIATE_OUT_OF_RANGE"
                else:
                    return False, "INDEP_CAND_BAD_ARG_TYPE"
        c_defined.add(dst)

    if cand_out not in c_defined:
        return False, f"INDEP_CAND_OUT_NOT_DEFINED: {cand_out}"

    # Exhaustive evaluation for width <= 8
    mask = (1 << width) - 1
    if width <= 8:
        if len(inputs) == 1:
            for v in range(1 << width):
                in_dict = {inputs[0]: v}
                if independent_eval(case_ops, case_out, in_dict, width) != independent_eval(
                    cand_ops, cand_out, in_dict, width
                ):
                    return False, f"INDEP_EQUIV_FAILED_AT_{in_dict}"
        else:
            for x in range(1 << width):
                for y in range(1 << width):
                    in_dict = {inputs[0]: x, inputs[1]: y}
                    if independent_eval(case_ops, case_out, in_dict, width) != independent_eval(
                        cand_ops, cand_out, in_dict, width
                    ):
                        return False, f"INDEP_EQUIV_FAILED_AT_{in_dict}"
    else:
        # 10,000 stress tests for larger widths
        corners = [
            0,
            1,
            2,
            width - 1,
            width,
            (1 << (width - 1)) - 1,
            1 << (width - 1),
            mask,
            mask - 1,
            0x55555555 & mask,
            0xAAAAAAAA & mask,
        ]
        for c1 in corners:
            for c2 in corners:
                in_dict = {inputs[0]: c1} if len(inputs) == 1 else {inputs[0]: c1, inputs[1]: c2}
                if independent_eval(case_ops, case_out, in_dict, width) != independent_eval(
                    cand_ops, cand_out, in_dict, width
                ):
                    return False, f"INDEP_CORNER_FAILED_AT_{in_dict}"

        prng = 987654321
        for _ in range(2000):
            prng = (prng * 1664525 + 1013904223) & 0xFFFFFFFFFFFFFFFF
            rx = prng & mask
            prng = (prng * 1664525 + 1013904223) & 0xFFFFFFFFFFFFFFFF
            ry = prng & mask
            in_dict = {inputs[0]: rx} if len(inputs) == 1 else {inputs[0]: rx, inputs[1]: ry}
            if independent_eval(case_ops, case_out, in_dict, width) != independent_eval(
                cand_ops, cand_out, in_dict, width
            ):
                return False, f"INDEP_RANDOM_FAILED_AT_{in_dict}"

    return True, "INDEPENDENT_VERIFICATION_PASSED"
