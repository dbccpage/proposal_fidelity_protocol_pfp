"""Generate the 14 public examples for C057."""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[5]))

from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.exact_checker import (
    check,
)
from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.reference_solver import (
    solve,
)

EXAMPLES = [
    {"case_id": "sn_ex_01", "n": 4, "k": 6, "prefix": [], "forbidden": []},
    {"case_id": "sn_ex_02", "n": 4, "k": 6, "prefix": [[0, 2]], "forbidden": [[1, 3]]},
    {"case_id": "sn_ex_03", "n": 5, "k": 10, "prefix": [[0, 3]], "forbidden": []},
    {"case_id": "sn_ex_04", "n": 6, "k": 13, "prefix": [[0, 5]], "forbidden": []},
    {"case_id": "sn_ex_05", "n": 7, "k": 17, "prefix": [[1, 6]], "forbidden": []},
    {"case_id": "sn_ex_06", "n": 8, "k": 20, "prefix": [[0, 7]], "forbidden": []},
    {"case_id": "sn_ex_07", "n": 9, "k": 26, "prefix": [[2, 8]], "forbidden": []},
    {"case_id": "sn_ex_08", "n": 10, "k": 30, "prefix": [[0, 9]], "forbidden": []},
    {"case_id": "sn_ex_09", "n": 4, "k": 3, "prefix": [], "forbidden": []},
    {"case_id": "sn_ex_10", "n": 5, "k": 6, "prefix": [], "forbidden": []},
    {"case_id": "sn_ex_11", "n": 6, "k": 10, "prefix": [], "forbidden": []},
    {"case_id": "sn_ex_12", "n": 4, "k": 6, "prefix": [[2, 0]], "forbidden": []},
    {"case_id": "sn_ex_13", "n": 4, "k": 6, "prefix": [[0, 2]], "forbidden": [[0, 2]]},
    {"case_id": "sn_ex_14", "n": 14, "k": 50, "prefix": [], "forbidden": []},
]

out_dir = Path(__file__).resolve().parent / "participant_packet" / "examples"
out_dir.mkdir(parents=True, exist_ok=True)

for ex in EXAMPLES:
    sol = solve(ex)
    ok1, msg1 = check(ex, sol)
    ok2, msg2 = independent_check(ex, sol)
    assert ok1, f"Exact check failed on {ex['case_id']}: {msg1}"
    assert ok2, f"Independent check failed on {ex['case_id']}: {msg2}"

    file_path = out_dir / f"{ex['case_id']}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"input": ex, "expected_output": sol}, f, indent=2)
    print(f"Generated {file_path.name}: status={sol['status']} (exact: {msg1}, indep: {msg2})")

print("All 14 public examples generated and dual-verified successfully!")
