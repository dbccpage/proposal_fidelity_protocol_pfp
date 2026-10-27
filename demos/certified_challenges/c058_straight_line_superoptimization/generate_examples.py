"""Generates and dual-verifies 14 public examples for C058 Straight-Line Superoptimization."""

import json
from pathlib import Path

from c058_straight_line_superoptimization.judge_packet.exact_checker import (
    verify_candidate,
)
from c058_straight_line_superoptimization.judge_packet.independent_checker import (
    check_candidate_indep,
)
from c058_straight_line_superoptimization.reference_solver import (
    solve,
)

EXAMPLES = [
    # 1. XOR identity: (x | y) - (x & y) == x ^ y
    {
        "case_id": "so_ex_01",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "or", "x", "y"], ["t2", "and", "x", "y"], ["t3", "sub", "t1", "t2"]],
        "out": "t3",
        "target_len": 1,
    },
    # 2. Clear lowest set bit: x & (x - 1) bloated
    {
        "case_id": "so_ex_02",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "const", 1], ["t2", "sub", "x", "t1"], ["t3", "and", "x", "t2"]],
        "out": "t3",
        "target_len": 2,
    },
    # 3. Double negation: -(-x) == x (target_len 0)
    {
        "case_id": "so_ex_03",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "neg", "x"], ["t2", "neg", "t1"]],
        "out": "t2",
        "target_len": 0,
    },
    # 4. Multiply by 4: (x << 1) + (x << 1) -> x << 2 or x * 4
    {
        "case_id": "so_ex_04",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "shl", "x", 1], ["t2", "shl", "x", 1], ["t3", "add", "t1", "t2"]],
        "out": "t3",
        "target_len": 1,
    },
    # 5. Arithmetic shift sign test: (x ashr 7)
    {
        "case_id": "so_ex_05",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "ashr", "x", 3], ["t2", "ashr", "t1", 4]],
        "out": "t2",
        "target_len": 1,
    },
    # 6. Shift by width modulo w: (x shl 8) == (x shl 0) == x
    {
        "case_id": "so_ex_06",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "shl", "x", 8]],
        "out": "t1",
        "target_len": 0,
    },
    # 7. Width 32 XOR identity: (x | y) ^ (x & y) -> x ^ y
    {
        "case_id": "so_ex_07",
        "width": 32,
        "inputs": ["x", "y"],
        "ops": [["t1", "or", "x", "y"], ["t2", "and", "x", "y"], ["t3", "xor", "t1", "t2"]],
        "out": "t3",
        "target_len": 1,
    },
    # 8. Dead code elimination: 4 dead instructions
    {
        "case_id": "so_ex_08",
        "width": 32,
        "inputs": ["x", "y"],
        "ops": [
            ["d1", "mul", "x", "y"],
            ["d2", "add", "d1", "x"],
            ["d3", "xor", "d2", "y"],
            ["r1", "add", "x", "y"],
        ],
        "out": "r1",
        "target_len": 1,
    },
    # 9. Infeasible target_len 0 for irreducible binary addition: UNKNOWN
    {
        "case_id": "so_ex_09",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "x", "y"]],
        "out": "t1",
        "target_len": 0,
    },
    # 10. Infeasible target_len 0 for irreducible XOR: UNKNOWN
    {
        "case_id": "so_ex_10",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "xor", "x", "y"]],
        "out": "t1",
        "target_len": 0,
    },
    # 11. Bloated addition with redundant self-cancellation: (x + y) + z - z -> x + y
    {
        "case_id": "so_ex_11",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "x", "y"], ["t2", "add", "t1", "x"], ["t3", "sub", "t2", "x"]],
        "out": "t3",
        "target_len": 1,
    },
    # 12. Poisoned / Out of scope: undefined operand variable
    {
        "case_id": "so_ex_12",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "x", "non_existent_var"]],
        "out": "t1",
        "target_len": 1,
    },
    # 13. Poisoned / Out of scope: unsupported operator "mod"
    {
        "case_id": "so_ex_13",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "mod", "x", "y"]],
        "out": "t1",
        "target_len": 1,
    },
    # 14. Poisoned / Out of scope: invalid width 17
    {
        "case_id": "so_ex_14",
        "width": 17,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "x", "y"]],
        "out": "t1",
        "target_len": 1,
    },
]


def main():
    ex_dir = Path(__file__).parent / "participant_packet" / "examples"
    ex_dir.mkdir(parents=True, exist_ok=True)

    for case in EXAMPLES:
        cid = case["case_id"]
        out_path = ex_dir / f"{cid}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2)

        sol = solve(case)
        ok1, msg1 = verify_candidate(case, sol)
        ok2, msg2 = check_candidate_indep(case, sol)
        assert ok1, f"Exact checker failed on {cid}: {msg1}"
        assert ok2, f"Independent checker failed on {cid}: {msg2}"
        print(f"Generated {cid}.json: status={sol['status']} (exact: {msg1}, indep: {msg2})")

    print(f"All {len(EXAMPLES)} public examples generated and dual-verified successfully!")


if __name__ == "__main__":
    main()
