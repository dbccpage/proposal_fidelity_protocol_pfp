"""Straight-line superoptimizer using observational equivalence and algebraic rewrites."""

from typing import Any, Dict, List, Optional, Set, Tuple

from .evaluator import (
    UNARY_OPS,
    eval_op,
    execute_program,
    verify_equivalence,
)


def get_signature_inputs(inputs: List[str], width: int) -> List[Dict[str, int]]:
    """Small signature input suite (up to 32 vectors) for fast pruning."""
    mask = (1 << width) - 1
    vals = [
        0,
        1,
        2,
        width - 1,
        (1 << (width - 1)) - 1,
        1 << (width - 1),
        mask,
        mask - 1,
        0x55 & mask,
        0xAA & mask,
    ]
    # deterministic random additions
    prng = 12345
    for _ in range(12):
        prng = (prng * 1103515245 + 12345) & 0x7FFFFFFF
        vals.append(prng & mask)
    vals = sorted(list(set(vals)))

    res: List[Dict[str, int]] = []
    if len(inputs) == 1:
        for v in vals[:32]:
            res.append({inputs[0]: v})
    else:
        for i in range(min(len(vals), 32)):
            x = vals[i]
            y = vals[(i * 7 + 3) % len(vals)]
            res.append({inputs[0]: x, inputs[1]: y})
    return res


def dead_code_elimination(ops: List[List[Any]], out_var: str) -> List[List[Any]]:
    """Removes instructions that do not contribute to out_var."""
    needed: Set[str] = {out_var}
    surviving_indices: List[int] = []

    for idx in range(len(ops) - 1, -1, -1):
        inst = ops[idx]
        target = inst[0]
        if target in needed:
            surviving_indices.append(idx)
            needed.remove(target)
            op = inst[1]
            if op == "const":
                pass
            elif op in UNARY_OPS:
                needed.add(inst[2])
            else:
                if isinstance(inst[2], str):
                    needed.add(inst[2])
                if isinstance(inst[3], str):
                    needed.add(inst[3])

    surviving_indices.reverse()
    return [ops[i] for i in surviving_indices]


def optimize_program(case: Dict[str, Any]) -> Tuple[str, Optional[List[List[Any]]], Optional[str]]:
    """Main superoptimization entrypoint.

    Returns:
        status ("SOLVED" | "UNKNOWN"), ops, out
    """
    width = case["width"]
    inputs = case["inputs"]
    ops = case["ops"]
    out = case["out"]
    target_len = case.get("target_len", len(ops) - 1)

    # 1. Dead code elimination
    dce_ops = dead_code_elimination(ops, out)
    if len(dce_ops) <= target_len:
        # Check equivalence
        ok, _, _ = verify_equivalence(ops, out, dce_ops, out, inputs, width)
        if ok:
            return "SOLVED", dce_ops, out

    sig_inputs = get_signature_inputs(inputs, width)
    target_sig = tuple(execute_program(ops, out, inp, width) for inp in sig_inputs)

    # 2. Check length 0 (direct input or constant)
    if target_len >= 0:
        for inp_name in inputs:
            inp_sig = tuple(inp[inp_name] for inp in sig_inputs)
            if inp_sig == target_sig:
                ok, _, _ = verify_equivalence(ops, out, [], inp_name, inputs, width)
                if ok:
                    return "SOLVED", [], inp_name

        # Check constant 0
        if all(v == target_sig[0] for v in target_sig):
            c_val = target_sig[0]
            cand_ops = [["r0", "const", c_val]]
            if len(cand_ops) <= target_len:
                ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                if ok:
                    return "SOLVED", cand_ops, "r0"

    # 3. Known bit-trick library patterns
    # Check if target_sig matches any canonical 1-instruction or 2-instruction bit trick
    list(inputs)

    # Enumerate length 1
    if target_len >= 1:
        # Unary ops on inputs
        for inp_name in inputs:
            for op_name in ("not", "neg"):
                cand_ops = [["r0", op_name, inp_name]]
                sig = tuple(eval_op(op_name, [inp[inp_name]], width) for inp in sig_inputs)
                if sig == target_sig:
                    ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                    if ok:
                        return "SOLVED", cand_ops, "r0"

        # Binary ops on pairs of inputs
        all_pairs = []
        if len(inputs) == 1:
            all_pairs = [(inputs[0], inputs[0])]
        else:
            all_pairs = [
                (inputs[0], inputs[1]),
                (inputs[1], inputs[0]),
                (inputs[0], inputs[0]),
                (inputs[1], inputs[1]),
            ]

        bin_ops = ("xor", "and", "or", "add", "sub", "mul", "shl", "lshr", "ashr")
        for op_name in bin_ops:
            for a1, a2 in all_pairs:
                sig = tuple(eval_op(op_name, [inp[a1], inp[a2]], width) for inp in sig_inputs)
                if sig == target_sig:
                    cand_ops = [["r0", op_name, a1, a2]]
                    ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                    if ok:
                        return "SOLVED", cand_ops, "r0"

        # Binary ops with constants
        consts = [0, 1, 2, 3, 4, 7, 8, width - 1, (1 << width) - 1]
        for inp_name in inputs:
            for c_val in consts:
                for op_name in bin_ops:
                    # inp op const
                    sig1 = tuple(
                        eval_op(op_name, [inp[inp_name], c_val], width) for inp in sig_inputs
                    )
                    if sig1 == target_sig:
                        cand_ops = [["r0", op_name, inp_name, c_val]]
                        ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                        if ok:
                            return "SOLVED", cand_ops, "r0"
                    # const op inp
                    if op_name in ("sub", "shl", "lshr", "ashr"):
                        sig2 = tuple(
                            eval_op(op_name, [c_val, inp[inp_name]], width) for inp in sig_inputs
                        )
                        if sig2 == target_sig:
                            cand_ops = [
                                ["c_temp", "const", c_val],
                                ["r0", op_name, "c_temp", inp_name],
                            ]
                            if len(cand_ops) <= target_len:
                                ok, _, _ = verify_equivalence(
                                    ops, out, cand_ops, "r0", inputs, width
                                )
                                if ok:
                                    return "SOLVED", cand_ops, "r0"

    # Enumerate length 2
    if target_len >= 2:
        # Precompute all depth-1 values
        depth1_map: Dict[Tuple[int, ...], List[Any]] = {}
        # Unary on inputs
        for inp_name in inputs:
            for op_name in ("not", "neg"):
                sig = tuple(eval_op(op_name, [inp[inp_name]], width) for inp in sig_inputs)
                if sig not in depth1_map:
                    depth1_map[sig] = [["t1", op_name, inp_name], "t1"]
        # Binary on inputs
        for op_name in ("xor", "and", "or", "add", "sub", "shl", "lshr", "ashr"):
            for a1, a2 in all_pairs:
                sig = tuple(eval_op(op_name, [inp[a1], inp[a2]], width) for inp in sig_inputs)
                if sig not in depth1_map:
                    depth1_map[sig] = [["t1", op_name, a1, a2], "t1"]
            # With small constants
            for inp_name in inputs:
                for c_val in (1, 2, 3, 4, width - 1):
                    sig = tuple(
                        eval_op(op_name, [inp[inp_name], c_val], width) for inp in sig_inputs
                    )
                    if sig not in depth1_map:
                        depth1_map[sig] = [["t1", op_name, inp_name, c_val], "t1"]

        # Now try combining depth-1 results with inputs or constants
        depth1_items = list(depth1_map.items())
        for d1_sig, (d1_inst, d1_var) in depth1_items:
            # Unary on depth-1
            for op_name in ("not", "neg"):
                sig = tuple(eval_op(op_name, [val], width) for val in d1_sig)
                if sig == target_sig:
                    cand_ops = [d1_inst, ["r0", op_name, d1_var]]
                    ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                    if ok:
                        return "SOLVED", cand_ops, "r0"

            # Binary with input
            for inp_name in inputs:
                inp_vals = [inp[inp_name] for inp in sig_inputs]
                for op_name in ("xor", "and", "or", "add", "sub", "mul", "shl", "lshr", "ashr"):
                    # d1 op inp
                    sig1 = tuple(
                        eval_op(op_name, [d1_sig[i], inp_vals[i]], width)
                        for i in range(len(sig_inputs))
                    )
                    if sig1 == target_sig:
                        cand_ops = [d1_inst, ["r0", op_name, d1_var, inp_name]]
                        ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                        if ok:
                            return "SOLVED", cand_ops, "r0"
                    # inp op d1
                    if op_name in ("sub", "shl", "lshr", "ashr"):
                        sig2 = tuple(
                            eval_op(op_name, [inp_vals[i], d1_sig[i]], width)
                            for i in range(len(sig_inputs))
                        )
                        if sig2 == target_sig:
                            cand_ops = [d1_inst, ["r0", op_name, inp_name, d1_var]]
                            ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                            if ok:
                                return "SOLVED", cand_ops, "r0"

            # Binary with constant
            for c_val in (1, 2, 3, 4, width - 1):
                for op_name in ("xor", "and", "or", "add", "sub", "shl", "lshr", "ashr"):
                    sig1 = tuple(
                        eval_op(op_name, [d1_sig[i], c_val], width) for i in range(len(sig_inputs))
                    )
                    if sig1 == target_sig:
                        cand_ops = [d1_inst, ["r0", op_name, d1_var, c_val]]
                        ok, _, _ = verify_equivalence(ops, out, cand_ops, "r0", inputs, width)
                        if ok:
                            return "SOLVED", cand_ops, "r0"

    # Enumerate length 3 for common 3-op patterns (e.g. shift-add-mask or sign-isolate)
    if target_len >= 3 and len(depth1_map) > 0:
        # Search among combinations of depth1 and binary ops
        for d1_sig, (d1_inst, d1_var) in depth1_items[:30]:
            for inp_name in inputs:
                inp_vals = [inp[inp_name] for inp in sig_inputs]
                for op1 in ("and", "add", "sub", "xor", "shl"):
                    sig_mid = tuple(
                        eval_op(op1, [d1_sig[i], inp_vals[i]], width)
                        for i in range(len(sig_inputs))
                    )
                    # try 3rd op with constant or input
                    for c_val in (1, 2, 3, 4, 7, 8, width - 1):
                        for op2 in ("and", "add", "sub", "xor", "shl", "lshr"):
                            sig_fin = tuple(
                                eval_op(op2, [sig_mid[i], c_val], width)
                                for i in range(len(sig_inputs))
                            )
                            if sig_fin == target_sig:
                                cand_ops = [
                                    d1_inst,
                                    ["t2", op1, d1_var, inp_name],
                                    ["r0", op2, "t2", c_val],
                                ]
                                ok, _, _ = verify_equivalence(
                                    ops, out, cand_ops, "r0", inputs, width
                                )
                                if ok:
                                    return "SOLVED", cand_ops, "r0"

    return "UNKNOWN", None, None
