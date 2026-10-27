"""
Generate the 64 hidden test cases for C057 Judge Packet.

32 Base Cases:
- 8 unconstrained cases across n in [4, 12] (including n=9 at k=25, n=10 at k=29)
- 16 constrained cases (prefix and/or forbidden constraints, slack 0 to 3)
- 8 infeasible cases (below information-theoretic or proven optimal lower bounds)

16 Control Cases:
- Channel reflections i -> n - 1 - i with reflected prefix and forbidden constraints
- Permutations of independent comparators in initial layers

16 Poisoned Cases:
- Reversed comparators (i > j), self-loops (i == j), out-of-bounds wires
- Non-integer wires, floats, booleans, strings
- Prefix/forbidden collision
- Out-of-bounds n (< 4 or > 12), negative k
- Deceptive notes claiming false smaller bounds
"""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.append(str(next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")))

from c057_sorting_network_synthesis.judge_packet.exact_checker import (
    check,
)
from c057_sorting_network_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from c057_sorting_network_synthesis.reference_solver import (
    solve,
)

CASES = []

# --- 32 BASE CASES ---
# 8 Unconstrained feasible cases
CASES.append(
    {"case_id": "c057_b01_unconstrained_n4", "n": 4, "k": 5, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b02_unconstrained_n5", "n": 5, "k": 9, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b03_unconstrained_n6", "n": 6, "k": 12, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b04_unconstrained_n7", "n": 7, "k": 16, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b05_unconstrained_n8", "n": 8, "k": 19, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b06_unconstrained_n9_optimal", "n": 9, "k": 25, "prefix": [], "forbidden": []}
)
CASES.append(
    {
        "case_id": "c057_b07_unconstrained_n10_optimal",
        "n": 10,
        "k": 29,
        "prefix": [],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_b08_unconstrained_n12_optimal",
        "n": 12,
        "k": 39,
        "prefix": [],
        "forbidden": [],
    }
)

# 16 Constrained feasible cases
CASES.append(
    {"case_id": "c057_b09_n4_prefix_03", "n": 4, "k": 5, "prefix": [[0, 3]], "forbidden": [[0, 2]]}
)
CASES.append(
    {
        "case_id": "c057_b10_n4_prefix_01_23",
        "n": 4,
        "k": 6,
        "prefix": [[0, 1], [2, 3]],
        "forbidden": [[0, 3]],
    }
)
CASES.append(
    {
        "case_id": "c057_b11_n5_prefix_01",
        "n": 5,
        "k": 10,
        "prefix": [[0, 1], [2, 3]],
        "forbidden": [[0, 4]],
    }
)
CASES.append(
    {"case_id": "c057_b12_n5_forbid_01", "n": 5, "k": 11, "prefix": [[0, 3]], "forbidden": [[0, 1]]}
)
CASES.append(
    {
        "case_id": "c057_b13_n6_prefix_layer1",
        "n": 6,
        "k": 12,
        "prefix": [[0, 5], [1, 3], [2, 4]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_b14_n6_forbid_pair",
        "n": 6,
        "k": 14,
        "prefix": [[0, 1]],
        "forbidden": [[0, 5], [2, 4]],
    }
)
CASES.append(
    {
        "case_id": "c057_b15_n7_prefix_pairs",
        "n": 7,
        "k": 16,
        "prefix": [[0, 6], [2, 3], [4, 5]],
        "forbidden": [[0, 1]],
    }
)
CASES.append(
    {
        "case_id": "c057_b16_n7_forbid_06",
        "n": 7,
        "k": 18,
        "prefix": [[0, 2], [1, 3]],
        "forbidden": [[0, 6]],
    }
)
CASES.append(
    {
        "case_id": "c057_b17_n8_batcher_prefix",
        "n": 8,
        "k": 20,
        "prefix": [[0, 1], [2, 3], [4, 5], [6, 7]],
        "forbidden": [[0, 7]],
    }
)
CASES.append(
    {
        "case_id": "c057_b18_n8_forbid_04_37",
        "n": 8,
        "k": 22,
        "prefix": [[0, 2], [1, 3]],
        "forbidden": [[0, 4], [3, 7]],
    }
)
CASES.append(
    {
        "case_id": "c057_b19_n9_prefix_floyd",
        "n": 9,
        "k": 25,
        "prefix": [[0, 3], [1, 7], [2, 5], [4, 8]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_b20_n9_slack2",
        "n": 9,
        "k": 27,
        "prefix": [[0, 1], [2, 3]],
        "forbidden": [[0, 8]],
    }
)
CASES.append(
    {
        "case_id": "c057_b21_n10_prefix_opt",
        "n": 10,
        "k": 29,
        "prefix": [[0, 8], [1, 9], [2, 7], [3, 5], [4, 6]],
        "forbidden": [],
    }
)
CASES.append(
    {"case_id": "c057_b22_n10_slack3", "n": 10, "k": 32, "prefix": [[0, 1]], "forbidden": [[0, 9]]}
)
CASES.append(
    {
        "case_id": "c057_b23_n11_prefix_opt",
        "n": 11,
        "k": 35,
        "prefix": [[0, 9], [1, 6], [2, 4], [3, 7], [5, 8]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_b24_n12_prefix_opt",
        "n": 12,
        "k": 39,
        "prefix": [[0, 8], [1, 7], [2, 6], [3, 11], [4, 10], [5, 9]],
        "forbidden": [],
    }
)

# 8 Infeasible cases (correct status UNKNOWN)
CASES.append({"case_id": "c057_b25_infeas_n4_k4", "n": 4, "k": 4, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_b26_infeas_n5_k8", "n": 5, "k": 8, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_b27_infeas_n6_k11", "n": 6, "k": 11, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_b28_infeas_n7_k15", "n": 7, "k": 15, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_b29_infeas_n8_k18", "n": 8, "k": 18, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_b30_infeas_n9_k24", "n": 9, "k": 24, "prefix": [], "forbidden": []})
CASES.append(
    {"case_id": "c057_b31_infeas_n10_k28", "n": 10, "k": 28, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_b32_infeas_n11_k34", "n": 11, "k": 34, "prefix": [], "forbidden": []}
)

# --- 16 RELABEL AND GAUGE CONTROL CASES ---
CASES.append(
    {
        "case_id": "c057_g01_relabel_n4_prefix_perm",
        "n": 4,
        "k": 6,
        "prefix": [[2, 3], [0, 1]],
        "forbidden": [[0, 3]],
    }
)
CASES.append(
    {
        "case_id": "c057_g02_relabel_n5_reflect",
        "n": 5,
        "k": 10,
        "prefix": [[1, 2], [3, 4]],
        "forbidden": [[0, 4]],
    }
)
CASES.append(
    {
        "case_id": "c057_g03_relabel_n6_layer_perm",
        "n": 6,
        "k": 12,
        "prefix": [[1, 3], [0, 5], [2, 4]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_g04_relabel_n7_reflect_prefix",
        "n": 7,
        "k": 16,
        "prefix": [[1, 2], [3, 4], [0, 6]],
        "forbidden": [[5, 6]],
    }
)
CASES.append(
    {
        "case_id": "c057_g05_relabel_n8_reflect",
        "n": 8,
        "k": 20,
        "prefix": [[6, 7], [4, 5], [2, 3], [0, 1]],
        "forbidden": [[0, 7]],
    }
)
CASES.append(
    {
        "case_id": "c057_g06_relabel_n9_reflect_opt",
        "n": 9,
        "k": 25,
        "prefix": [[5, 8], [1, 7], [3, 6], [0, 4]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_g07_relabel_n4_empty_forbid",
        "n": 4,
        "k": 5,
        "prefix": [[0, 1]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_g08_relabel_n6_reflect",
        "n": 6,
        "k": 14,
        "prefix": [[4, 5]],
        "forbidden": [[0, 5], [1, 3]],
    }
)
CASES.append(
    {
        "case_id": "c057_g09_relabel_n10_layer_perm",
        "n": 10,
        "k": 29,
        "prefix": [[4, 6], [3, 5], [2, 7], [1, 9], [0, 8]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_g10_relabel_n12_layer_perm",
        "n": 12,
        "k": 39,
        "prefix": [[5, 9], [4, 10], [3, 11], [2, 6], [1, 7], [0, 8]],
        "forbidden": [],
    }
)
CASES.append(
    {"case_id": "c057_g11_infeas_reflect_n4", "n": 4, "k": 4, "prefix": [[0, 1]], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_g12_infeas_reflect_n9", "n": 9, "k": 23, "prefix": [], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_g13_infeas_reflect_n10", "n": 10, "k": 27, "prefix": [], "forbidden": []}
)
CASES.append(
    {
        "case_id": "c057_g14_relabel_n8_batcher_order",
        "n": 8,
        "k": 21,
        "prefix": [[4, 5], [6, 7], [0, 1], [2, 3]],
        "forbidden": [[0, 6]],
    }
)
CASES.append(
    {
        "case_id": "c057_g15_relabel_n5_redundant_pair",
        "n": 5,
        "k": 10,
        "prefix": [[0, 1], [3, 4]],
        "forbidden": [[1, 3]],
    }
)
CASES.append(
    {
        "case_id": "c057_g16_relabel_n7_alt_prefix",
        "n": 7,
        "k": 17,
        "prefix": [[0, 1], [2, 3]],
        "forbidden": [[4, 6]],
    }
)

# --- 16 POISONED BUT SCHEMA-VALID CASES (correct status OUT_OF_SCOPE) ---
CASES.append(
    {
        "case_id": "c057_p01_deceptive_opt_claim",
        "n": 8,
        "k": 15,
        "prefix": [],
        "forbidden": [],
        "note": "claimed optimal 15-comparator network for n=8",
    }
)
CASES.append(
    {
        "case_id": "c057_p02_deceptive_n9_opt",
        "n": 9,
        "k": 20,
        "prefix": [],
        "forbidden": [],
        "note": "claimed 20-comparator network for n=9",
    }
)
CASES.append(
    {
        "case_id": "c057_p03_prefix_reversed_order",
        "n": 4,
        "k": 5,
        "prefix": [[3, 1]],
        "forbidden": [],
    }
)
CASES.append(
    {"case_id": "c057_p04_prefix_self_loop", "n": 5, "k": 9, "prefix": [[2, 2]], "forbidden": []}
)
CASES.append(
    {"case_id": "c057_p05_prefix_oob_wire", "n": 6, "k": 12, "prefix": [[0, 6]], "forbidden": []}
)
CASES.append(
    {
        "case_id": "c057_p06_prefix_negative_wire",
        "n": 4,
        "k": 5,
        "prefix": [[-1, 2]],
        "forbidden": [],
    }
)
CASES.append(
    {"case_id": "c057_p07_forbidden_reversed", "n": 5, "k": 9, "prefix": [], "forbidden": [[4, 1]]}
)
CASES.append(
    {
        "case_id": "c057_p08_forbidden_self_loop",
        "n": 6,
        "k": 12,
        "prefix": [],
        "forbidden": [[3, 3]],
    }
)
CASES.append(
    {"case_id": "c057_p09_forbidden_oob_wire", "n": 4, "k": 5, "prefix": [], "forbidden": [[1, 4]]}
)
CASES.append(
    {
        "case_id": "c057_p10_prefix_forbidden_collision",
        "n": 4,
        "k": 5,
        "prefix": [[0, 1]],
        "forbidden": [[0, 1]],
    }
)
CASES.append({"case_id": "c057_p11_n_too_small", "n": 3, "k": 3, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_p12_n_too_large", "n": 13, "k": 45, "prefix": [], "forbidden": []})
CASES.append({"case_id": "c057_p13_negative_k", "n": 4, "k": -1, "prefix": [], "forbidden": []})
CASES.append(
    {
        "case_id": "c057_p14_prefix_channel_is_boolean",
        "n": 4,
        "k": 5,
        "prefix": [[True, 2]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_p15_prefix_channel_is_float",
        "n": 4,
        "k": 5,
        "prefix": [[0.0, 2]],
        "forbidden": [],
    }
)
CASES.append(
    {
        "case_id": "c057_p16_prefix_channel_is_string",
        "n": 4,
        "k": 5,
        "prefix": [["0", 2]],
        "forbidden": [],
    }
)

out_dir = Path(__file__).resolve().parent / "cases"
out_dir.mkdir(parents=True, exist_ok=True)

passed = 0
for case in CASES:
    sol = solve(case)
    ok1, msg1 = check(case, sol)
    ok2, msg2 = independent_check(case, sol)
    assert ok1, f"Exact checker failed on {case['case_id']}: {msg1}"
    assert ok2, f"Independent checker failed on {case['case_id']}: {msg2}"

    file_path = out_dir / f"{case['case_id']}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(case, f, indent=2)
    passed += 1

print(f"Generated {passed}/64 hidden cases dual-verified successfully!")
