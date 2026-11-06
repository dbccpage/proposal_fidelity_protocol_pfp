"""
Generate 14 public worked examples for Challenge C054 Participant Packet.
"""

from pathlib import Path
import sys
import json
import os

for _parent in Path(__file__).resolve().parents:
    if (_parent / "sqlite_pilot_store.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from c054_exact_linear_systems.judge_packet.exact_checker import (
    check_exact,
)
from c054_exact_linear_systems.judge_packet.independent_checker import (
    independent_check,
)
from c054_exact_linear_systems.reference_solver.linear_solver import (
    solve_linear_system,
)

EXAMPLES = [
    {"case_id": "ls_ex_01", "A": [["1", "2", "3"], ["2", "4", "6"]], "b": ["1", "2"]},
    {"case_id": "ls_ex_02", "A": [["1", "2", "3"], ["2", "4", "6"]], "b": ["1", "3"]},
    {
        "case_id": "ls_ex_03",
        "A": [["2", "1", "-1"], ["-3", "-1", "2"], ["-2", "1", "2"]],
        "b": ["8", "-11", "-3"],
    },
    {"case_id": "ls_ex_04", "A": [["0", "0"], ["0", "0"]], "b": ["0", "0"]},
    {
        "case_id": "ls_ex_05",
        "A": [["1", "2", "1"], ["2", "4", "2"], ["3", "6", "3"]],
        "b": ["0", "0", "0"],
    },
    {"case_id": "ls_ex_06", "A": [["1", "1"], ["2", "2"], ["3", "4"]], "b": ["2", "5", "7"]},
    {"case_id": "ls_ex_07", "A": [["1", "1"], ["2", "2"], ["1", "2"]], "b": ["3", "6", "5"]},
    {"case_id": "ls_ex_08", "A": [["1/2", "1/3"], ["1/4", "1/5"]], "b": ["5/6", "9/20"]},
    {
        "case_id": "ls_ex_09",
        "A": [["1000000000", "2000000000"], ["3000000000", "7000000000"]],
        "b": ["5000000000", "17000000000"],
    },
    {"case_id": "ls_ex_10", "A": [], "b": []},
    {"case_id": "ls_ex_11", "A": [[], []], "b": ["0", "0"]},
    {"case_id": "ls_ex_12", "A": [["1", "2"], ["3"]], "b": ["1", "2"]},
    {"case_id": "ls_ex_13", "A": [["1", "2"], ["3", "4"]], "b": ["1"]},
    {"case_id": "ls_ex_14", "A": [["1", "abc"], ["2", "3"]], "b": ["1", "2"]},
]


def main():
    target_dir = os.path.join(os.path.dirname(__file__), "participant_packet", "examples")
    os.makedirs(target_dir, exist_ok=True)

    for case in EXAMPLES:
        cid = case["case_id"]
        result = solve_linear_system(case)

        ok1, msg1 = check_exact(case, result)
        ok2, msg2 = independent_check(case, result)
        if not ok1 or not ok2:
            raise RuntimeError(f"Check failed on example {cid}: exact={msg1}, indep={msg2}")

        path = os.path.join(target_dir, f"{cid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"input": case, "expected_output": result}, f, indent=2)
        print(f"Generated {cid}: status={result['status']}, kind={result.get('kind', 'N/A')}")
    print(f"All {len(EXAMPLES)} examples generated and verified by both checkers!")


if __name__ == "__main__":
    main()
