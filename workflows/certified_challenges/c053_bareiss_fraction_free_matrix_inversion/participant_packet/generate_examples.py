"""Generate 14 public worked examples for C053: Bareiss Fraction-Free Matrix Inversion."""

import json
import sys
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "sqlite_pilot_store.py").is_file()
)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from c053_bareiss_fraction_free_matrix_inversion.reference_solver import (
    solve,
)

EXAMPLES = [
    # 1. 1x1 invertible
    {"case_id": "bf_ex_01_1x1_invertible", "matrix": [["5"]]},
    # 2. 2x2 invertible
    {"case_id": "bf_ex_02_2x2_invertible", "matrix": [["1", "2"], ["3", "4"]]},
    # 3. 2x2 singular
    {"case_id": "bf_ex_03_2x2_singular", "matrix": [["1", "2"], ["2", "4"]]},
    # 4. 3x3 invertible
    {
        "case_id": "bf_ex_04_3x3_invertible",
        "matrix": [["1", "0", "2"], ["2", "-1", "3"], ["4", "1", "8"]],
    },
    # 5. 3x3 singular rank 2
    {
        "case_id": "bf_ex_05_3x3_singular_rank2",
        "matrix": [["1", "2", "3"], ["4", "5", "6"], ["5", "7", "9"]],
    },
    # 6. 3x3 singular rank 1
    {
        "case_id": "bf_ex_06_3x3_singular_rank1",
        "matrix": [["1", "2", "3"], ["2", "4", "6"], ["3", "6", "9"]],
    },
    # 7. 4x4 diagonal
    {
        "case_id": "bf_ex_07_4x4_diagonal",
        "matrix": [
            ["2", "0", "0", "0"],
            ["0", "3", "0", "0"],
            ["0", "0", "-1", "0"],
            ["0", "0", "0", "5"],
        ],
    },
    # 8. 2x2 rational entries
    {"case_id": "bf_ex_08_2x2_rational", "matrix": [["1/2", "1/3"], ["1/4", "1/5"]]},
    # 9. 3x3 upper triangular
    {
        "case_id": "bf_ex_09_3x3_triangular",
        "matrix": [["2", "3", "5"], ["0", "4", "7"], ["0", "0", "-2"]],
    },
    # 10. Large integers
    {
        "case_id": "bf_ex_10_large_integers",
        "matrix": [["1000000", "2000000"], ["3000000", "5000000"]],
    },
    # 11. OOS: Non-square 2x3
    {"case_id": "bf_ex_11_non_square", "matrix": [["1", "2", "3"], ["4", "5", "6"]]},
    # 12. OOS: Empty matrix
    {"case_id": "bf_ex_12_empty_matrix", "matrix": []},
    # 13. OOS: Row length mismatch
    {"case_id": "bf_ex_13_row_mismatch", "matrix": [["1", "2"], ["3"]]},
    # 14. OOS: Non-numeric entry
    {"case_id": "bf_ex_14_non_numeric", "matrix": [["1", "invalid"], ["3", "4"]]},
]


def generate():
    out_dir = Path(__file__).resolve().parent / "examples"
    out_dir.mkdir(parents=True, exist_ok=True)
    for ex in EXAMPLES:
        sol = solve(ex)
        bundle = {"input": ex, "expected_output": sol}
        with open(out_dir / f"{ex['case_id']}.json", "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
    print(f"Generated {len(EXAMPLES)} public worked examples in {out_dir}")


if __name__ == "__main__":
    generate()
