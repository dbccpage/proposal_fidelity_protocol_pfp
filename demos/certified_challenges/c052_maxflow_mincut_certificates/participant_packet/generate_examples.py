"""Generate public worked examples for C052: Max-Flow Min-Cut Certificates."""

import json
import sys
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "sqlite_pilot_store.py").is_file()
)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from c052_maxflow_mincut_certificates.reference_solver import (
    solve,
)

EXAMPLES = [
    # 1. Diamond network
    {
        "case_id": "mf_ex_01_diamond",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "3"], [0, 2, "2"], [1, 2, "1"], [1, 3, "2"], [2, 3, "3"]],
    },
    # 2. Unreachable sink
    {"case_id": "mf_ex_02_unreachable_sink", "n": 3, "s": 0, "t": 2, "arcs": [[0, 1, "5"]]},
    # 3. Parallel arcs
    {
        "case_id": "mf_ex_03_parallel_arcs",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "4"], [0, 1, "6"], [1, 2, "7"], [1, 2, "5"]],
    },
    # 4. Antiparallel arcs
    {
        "case_id": "mf_ex_04_antiparallel_arcs",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "10"], [1, 2, "5"], [2, 1, "3"], [2, 3, "10"], [0, 2, "2"], [1, 3, "4"]],
    },
    # 5. Self-loop
    {
        "case_id": "mf_ex_05_self_loop",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 0, "10"], [0, 1, "4"], [1, 1, "5"], [1, 2, "4"]],
    },
    # 6. Huge 64-bit capacity (10^18)
    {
        "case_id": "mf_ex_06_huge_capacity",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "1000000000000000000"], [1, 2, "1000000000000000000"]],
    },
    # 7. Multiple minimum cuts
    {
        "case_id": "mf_ex_07_multiple_min_cuts",
        "n": 4,
        "s": 0,
        "t": 3,
        "arcs": [[0, 1, "5"], [1, 2, "5"], [2, 3, "5"]],
    },
    # 8. Bottleneck path
    {
        "case_id": "mf_ex_08_bottleneck",
        "n": 5,
        "s": 0,
        "t": 4,
        "arcs": [[0, 1, "100"], [1, 2, "1"], [2, 3, "100"], [3, 4, "100"]],
    },
    # 9. Bipartite with super source/sink
    {
        "case_id": "mf_ex_09_bipartite_matching",
        "n": 6,
        "s": 0,
        "t": 5,
        "arcs": [
            [0, 1, "1"],
            [0, 2, "1"],
            [1, 3, "1"],
            [1, 4, "1"],
            [2, 3, "1"],
            [3, 5, "1"],
            [4, 5, "1"],
        ],
    },
    # 10. Star network
    {
        "case_id": "mf_ex_10_star",
        "n": 5,
        "s": 0,
        "t": 4,
        "arcs": [[0, 1, "2"], [0, 2, "3"], [0, 3, "4"], [1, 4, "1"], [2, 4, "5"], [3, 4, "2"]],
    },
    # 11. Poisoned / OOS: s == t
    {
        "case_id": "mf_ex_11_source_equals_sink",
        "n": 3,
        "s": 1,
        "t": 1,
        "arcs": [[0, 1, "5"], [1, 2, "5"]],
    },
    # 12. Poisoned / OOS: negative capacity
    {
        "case_id": "mf_ex_12_negative_capacity",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "5"], [1, 2, "-3"]],
    },
    # 13. Poisoned / OOS: node out of range
    {
        "case_id": "mf_ex_13_node_out_of_range",
        "n": 3,
        "s": 0,
        "t": 2,
        "arcs": [[0, 1, "5"], [1, 5, "5"]],
    },
    # 14. Poisoned / OOS: malformed arc tuple
    {"case_id": "mf_ex_14_malformed_arc", "n": 3, "s": 0, "t": 2, "arcs": [[0, 1]]},
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
