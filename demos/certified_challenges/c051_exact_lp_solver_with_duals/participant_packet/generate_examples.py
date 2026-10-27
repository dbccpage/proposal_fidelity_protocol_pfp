from pathlib import Path
import json
import os
import sys

for _parent in Path(__file__).resolve().parents:
    if (_parent / "sqlite_pilot_store.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from c051_exact_lp_solver_with_duals.reference_solver import (
    solve,
)

EXAMPLES = [
    {
        "case_id": "lp_ex_01_degenerate_optimum",
        "A": [["1", "1"], ["1", "3"], ["1", "0"]],
        "b": ["4", "6", "3"],
        "c": ["3", "2"],
    },
    {
        "case_id": "lp_ex_02_degenerate_optimum_2",
        "A": [["2", "1"], ["1", "2"], ["3", "3"]],
        "b": ["4", "4", "6"],
        "c": ["1", "1"],
    },
    {
        "case_id": "lp_ex_03_degenerate_optimum_3",
        "A": [["1", "1", "1"], ["2", "1", "0"], ["0", "1", "2"], ["1", "2", "3"]],
        "b": ["5", "6", "6", "11"],
        "c": ["2", "3", "1"],
    },
    {
        "case_id": "lp_ex_04_beale_dantzig_cycle",
        "A": [["1/4", "-8", "-1", "9"], ["1/2", "-12", "-1/2", "3"], ["0", "0", "1", "0"]],
        "b": ["0", "0", "1"],
        "c": ["3/4", "-20", "1/2", "-6"],
    },
    {"case_id": "lp_ex_05_infeasible_simple", "A": [["1", "1"]], "b": ["-1"], "c": ["1", "1"]},
    {
        "case_id": "lp_ex_06_infeasible_two_phase",
        "A": [["1", "0"], ["-1", "0"], ["0", "1"]],
        "b": ["2", "-3", "5"],
        "c": ["1", "1"],
    },
    {"case_id": "lp_ex_07_unbounded_simple", "A": [["-1", "1"]], "b": ["1"], "c": ["1", "0"]},
    {
        "case_id": "lp_ex_08_unbounded_ray",
        "A": [["1", "-1", "0"], ["0", "1", "-1"]],
        "b": ["2", "3"],
        "c": ["1", "1", "2"],
    },
    {
        "case_id": "lp_ex_09_zero_rows_cols",
        "A": [["0", "1"], ["0", "0"]],
        "b": ["5", "0"],
        "c": ["0", "2"],
    },
    {"case_id": "lp_ex_10_one_by_one_optimal", "A": [["2"]], "b": ["4"], "c": ["3"]},
    {"case_id": "lp_ex_11_one_by_one_infeasible", "A": [["1"]], "b": ["-5"], "c": ["1"]},
    {
        "case_id": "lp_ex_12_large_integers",
        "A": [["18446744073709551616", "1"], ["1", "18446744073709551616"]],
        "b": ["36893488147419103234", "36893488147419103234"],
        "c": ["1", "1"],
    },
    {
        "case_id": "lp_ex_13_malformed_row_mismatch",
        "A": [["1", "2"], ["3"]],
        "b": ["4", "5"],
        "c": ["1", "1"],
    },
    {"case_id": "lp_ex_14_malformed_missing_c", "A": [["1", "1"]], "b": ["2"]},
]


def main():
    ex_dir = os.path.join(os.path.dirname(__file__), "examples")
    os.makedirs(ex_dir, exist_ok=True)
    for ex in EXAMPLES:
        cid = ex["case_id"]
        res = solve(ex)
        with open(os.path.join(ex_dir, f"{cid}.json"), "w", encoding="utf-8") as f:
            json.dump({"input": ex, "expected_output": res}, f, indent=2)
    print("14 public examples generated.")


if __name__ == "__main__":
    main()
