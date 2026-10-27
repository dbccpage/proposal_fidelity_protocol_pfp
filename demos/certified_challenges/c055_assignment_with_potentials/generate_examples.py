"""
Generate 14 public worked examples for Challenge C055 Participant Packet.
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

from c055_assignment_with_potentials.judge_packet.exact_checker import (
    check_exact,
)
from c055_assignment_with_potentials.judge_packet.independent_checker import (
    independent_check,
)
from c055_assignment_with_potentials.reference_solver.hungarian import (
    solve_assignment,
)

EXAMPLES = [
    {
        "case_id": "as_ex_01",
        "sense": "min",
        "cost": [["4", "1", "3"], ["2", "0", "5"], ["3", "2", "2"]],
    },
    {"case_id": "as_ex_02", "sense": "min", "cost": [["1", "2"], ["3", "4"]]},
    {"case_id": "as_ex_03", "sense": "min", "cost": [["7"]]},
    {
        "case_id": "as_ex_04",
        "sense": "min",
        "cost": [["1", None, None], ["2", None, None], ["1", "1", "1"]],
    },
    {
        "case_id": "as_ex_05",
        "sense": "max",
        "cost": [["4", "1", "3"], ["2", "0", "5"], ["3", "2", "2"]],
    },
    {
        "case_id": "as_ex_06",
        "sense": "min",
        "cost": [["-5", "2", "1"], ["4", "-3", "6"], ["1", "3", "-2"]],
    },
    {
        "case_id": "as_ex_07",
        "sense": "min",
        "cost": [["1", "1", "1"], ["1", "1", "1"], ["1", "1", "1"]],
    },
    {
        "case_id": "as_ex_08",
        "sense": "min",
        "cost": [
            ["1", None, "4", "3"],
            [None, "2", "1", None],
            ["3", "2", None, "1"],
            ["4", None, "2", "5"],
        ],
    },
    {
        "case_id": "as_ex_09",
        "sense": "min",
        "cost": [["5", None, None], [None, "8", None], [None, None, "3"]],
    },
    {
        "case_id": "as_ex_10",
        "sense": "min",
        "cost": [["1000000000", "2000000000"], ["3000000000", "7000000000"]],
    },
    {
        "case_id": "as_ex_11",
        "sense": "min",
        "cost": [
            ["1", "2", None, None],
            ["3", "4", None, None],
            ["5", "6", None, None],
            ["1", "2", "3", "4"],
        ],
    },
    {"case_id": "as_ex_12", "cost": [["1", "2", "3"], ["4", "5", "6"]]},
    {"case_id": "as_ex_13", "cost": [["1", "2"], ["3"]]},
    {"case_id": "as_ex_14", "cost": [["1", "abc"], ["2", "3"]]},
]


def main():
    target_dir = os.path.join(os.path.dirname(__file__), "participant_packet", "examples")
    os.makedirs(target_dir, exist_ok=True)

    for case in EXAMPLES:
        cid = case["case_id"]
        result = solve_assignment(case)

        ok1, msg1 = check_exact(case, result)
        ok2, msg2 = independent_check(case, result)
        if not ok1 or not ok2:
            raise RuntimeError(f"Check failed on example {cid}: exact={msg1}, indep={msg2}")

        path = os.path.join(target_dir, f"{cid}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"input": case, "expected_output": result}, f, indent=2)
        print(f"Generated {cid}: status={result['status']}, kind={result.get('kind', 'N/A')}")
    print(f"All {len(EXAMPLES)} C055 examples generated and verified by both checkers!")


if __name__ == "__main__":
    main()
