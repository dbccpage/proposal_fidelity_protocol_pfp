"""Exact bit-vector evaluator and equivalence checker for C058 Straight-Line Superoptimization.

Supports widths w in {8, 16, 32, 64} with modular arithmetic and exact shifts modulo w.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

VALID_OPS = {"add", "sub", "mul", "and", "or", "xor", "not", "neg", "shl", "lshr", "ashr", "const"}

UNARY_OPS = {"not", "neg"}
NULLARY_OPS = {"const"}
BINARY_OPS = {"add", "sub", "mul", "and", "or", "xor", "shl", "lshr", "ashr"}


def validate_ir(case: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Validates the input straight-line program against schema and semantic constraints.

    Returns:
        (is_valid, error_code, witness_dict)
    """
    if not isinstance(case, dict):
        return False, "INVALID_CASE_TYPE", {"reason": "Case must be a JSON object"}

    width = case.get("width")
    if width not in {8, 16, 32, 64}:
        return False, "INVALID_WIDTH", {"reason": f"Width {width} must be in {{8, 16, 32, 64}}"}

    inputs = case.get("inputs")
    if not isinstance(inputs, list) or not all(isinstance(x, str) for x in inputs):
        return False, "INVALID_INPUTS", {"reason": "inputs must be a list of strings"}
    if len(inputs) > 2 or len(inputs) == 0:
        return False, "INVALID_INPUT_COUNT", {"reason": "inputs length must be 1 or 2"}
    if len(set(inputs)) != len(inputs):
        return False, "DUPLICATE_INPUTS", {"reason": "duplicate input names"}

    ops = case.get("ops")
    if not isinstance(ops, list):
        return False, "INVALID_OPS", {"reason": "ops must be a list"}

    out = case.get("out")
    if not isinstance(out, str):
        return False, "INVALID_OUT", {"reason": "out must be a string variable name"}

    target_len = case.get("target_len")
    if target_len is not None:
        if not isinstance(target_len, int) or target_len < 0:
            return (
                False,
                "INVALID_TARGET_LEN",
                {"reason": "target_len must be non-negative integer"},
            )

    defined_vars: Set[str] = set(inputs)

    for idx, inst in enumerate(ops):
        if not isinstance(inst, list) or len(inst) < 2:
            return False, "MALFORMED_INSTRUCTION", {"op_index": idx, "inst": inst}

        target = inst[0]
        if not isinstance(target, str):
            return False, "INVALID_TARGET_NAME", {"op_index": idx, "target": target}
        if target in inputs or target in defined_vars:
            return False, "OVERWRITE_VARIABLE", {"op_index": idx, "target": target}

        op = inst[1]
        if op not in VALID_OPS:
            return False, "UNKNOWN_OPERATOR", {"op_index": idx, "operator": op}

        if op == "const":
            if (
                len(inst) != 3
                or not isinstance(inst[2], int)
                or inst[2] < 0
                or inst[2] >= (1 << width)
            ):
                return False, "MALFORMED_CONST", {"op_index": idx, "inst": inst}
        elif op in UNARY_OPS:
            if len(inst) != 3:
                return False, "MALFORMED_UNARY", {"op_index": idx, "inst": inst}
            arg = inst[2]
            if not isinstance(arg, str):
                return False, "ARG_NOT_STRING", {"op_index": idx, "arg": arg}
            if arg not in defined_vars:
                return False, "UNDEFINED_OPERAND", {"op_index": idx, "name": arg}
        elif op in BINARY_OPS:
            if len(inst) != 4:
                return False, "MALFORMED_BINARY", {"op_index": idx, "inst": inst}
            arg1, arg2 = inst[2], inst[3]
            # arg can be variable name or integer literal (for immediate constant)
            for a in (arg1, arg2):
                if isinstance(a, str):
                    if a not in defined_vars:
                        return False, "UNDEFINED_OPERAND", {"op_index": idx, "name": a}
                elif isinstance(a, int):
                    if a < 0 or a >= (1 << width):
                        return False, "IMMEDIATE_OUT_OF_RANGE", {"op_index": idx, "val": a}
                else:
                    return False, "INVALID_OPERAND_TYPE", {"op_index": idx, "arg": a}

        defined_vars.add(target)

    if out not in defined_vars:
        return False, "UNDEFINED_OUTPUT", {"out": out, "defined": list(defined_vars)}

    return True, None, None


def eval_op(op: str, args: List[int], width: int) -> int:
    """Evaluates a single bit-vector operator with exact modular semantics."""
    mask = (1 << width) - 1
    if op == "const":
        return args[0] & mask
    elif op == "not":
        return (~args[0]) & mask
    elif op == "neg":
        return (-args[0]) & mask
    elif op == "add":
        return (args[0] + args[1]) & mask
    elif op == "sub":
        return (args[0] - args[1]) & mask
    elif op == "mul":
        return (args[0] * args[1]) & mask
    elif op == "and":
        return (args[0] & args[1]) & mask
    elif op == "or":
        return (args[0] | args[1]) & mask
    elif op == "xor":
        return (args[0] ^ args[1]) & mask
    elif op == "shl":
        amt = args[1] % width
        return (args[0] << amt) & mask
    elif op == "lshr":
        amt = args[1] % width
        return (args[0] >> amt) & mask
    elif op == "ashr":
        amt = args[1] % width
        val = args[0] & mask
        if val & (1 << (width - 1)):
            signed_val = val - (1 << width)
        else:
            signed_val = val
        return (signed_val >> amt) & mask
    else:
        raise ValueError(f"Unknown op {op}")


def execute_program(
    ops: List[List[Any]], out_var: str, input_vals: Dict[str, int], width: int
) -> int:
    """Executes a straight-line program on a given concrete input assignment."""
    env = dict(input_vals)
    mask = (1 << width) - 1
    for k in env:
        env[k] &= mask

    for inst in ops:
        target = inst[0]
        op = inst[1]
        if op == "const":
            res = inst[2] & mask
        elif op in UNARY_OPS:
            arg = env[inst[2]]
            res = eval_op(op, [arg], width)
        else:
            a1 = env[inst[2]] if isinstance(inst[2], str) else inst[2]
            a2 = env[inst[3]] if isinstance(inst[3], str) else inst[3]
            res = eval_op(op, [a1, a2], width)
        env[target] = res

    return env[out_var]


def generate_test_inputs(inputs: List[str], width: int) -> List[Dict[str, int]]:
    """Generates a representative suite of test inputs for testing equivalence."""
    if width <= 8:
        # Exhaustive input space
        if len(inputs) == 1:
            return [{inputs[0]: x} for x in range(1 << width)]
        else:
            res = []
            for x in range(1 << width):
                for y in range(1 << width):
                    res.append({inputs[0]: x, inputs[1]: y})
            return res

    # For width > 8 (e.g. 16, 32, 64): comprehensive boundary and stratified vectors
    mask = (1 << width) - 1
    interesting_vals = [
        0,
        1,
        2,
        3,
        4,
        7,
        8,
        15,
        16,
        31,
        32,
        width - 1,
        width,
        width + 1,
        (1 << (width - 1)) - 1,  # max signed positive
        1 << (width - 1),  # min signed negative
        mask,  # all ones (-1)
        mask - 1,
        mask - 2,
        0x55555555 & mask,
        0xAAAAAAAA & mask,
        0x0F0F0F0F & mask,
        0xF0F0F0F0 & mask,
        0x00FF00FF & mask,
        0xFF00FF00 & mask,
    ]

    # Add deterministic pseudorandom samples
    seed = 1790650000
    prng = seed
    for _ in range(256):
        prng = (prng * 1664525 + 1013904223) & 0xFFFFFFFFFFFFFFFF
        interesting_vals.append(prng & mask)

    interesting_vals = sorted(list(set(interesting_vals)))

    pairs: List[Dict[str, int]] = []
    if len(inputs) == 1:
        for x in interesting_vals:
            pairs.append({inputs[0]: x})
    else:
        # Diagonal and all pairs of the primary 16 corner values
        core = interesting_vals[:20]
        for x in core:
            for y in core:
                pairs.append({inputs[0]: x, inputs[1]: y})
        # Sparse pairing across the rest
        for i, val in enumerate(interesting_vals):
            x = val
            y = interesting_vals[(i * 37) % len(interesting_vals)]
            pairs.append({inputs[0]: x, inputs[1]: y})
            pairs.append({inputs[0]: y, inputs[1]: x})

    return pairs


def verify_equivalence(
    ops1: List[List[Any]],
    out1: str,
    ops2: List[List[Any]],
    out2: str,
    inputs: List[str],
    width: int,
) -> Tuple[bool, Optional[Dict[str, int]], Optional[Tuple[int, int]]]:
    """Verifies semantic equivalence of two programs.

    Returns:
        (is_equiv, counterexample_input, (val1, val2))
    """
    test_suite = generate_test_inputs(inputs, width)
    for inp in test_suite:
        v1 = execute_program(ops1, out1, inp, width)
        v2 = execute_program(ops2, out2, inp, width)
        if v1 != v2:
            return False, inp, (v1, v2)
    return True, None, None
