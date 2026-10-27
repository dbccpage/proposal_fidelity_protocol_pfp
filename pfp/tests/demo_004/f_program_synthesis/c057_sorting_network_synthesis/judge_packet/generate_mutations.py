"""
Generate and verify 48 Hostile Mutations for C057 Judge Packet.

Verifies that BOTH exact_checker and independent_checker REJECT (kill) 100% of mutations.
"""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[6]))

from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.exact_checker import (
    check,
)
from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.reference_solver import (
    solve,
)

cases_dir = Path(__file__).resolve().parent / "cases"
mutations_dir = Path(__file__).resolve().parent / "hostile_mutations"
mutations_dir.mkdir(parents=True, exist_ok=True)


def load_case(case_id: str) -> dict:
    with open(cases_dir / f"{case_id}.json", "r", encoding="utf-8") as f:
        return json.load(f)


MUTATIONS = []

# Base valid solutions to mutate
c_b01 = load_case("c057_b01_unconstrained_n4")
sol_b01 = solve(c_b01)

c_b02 = load_case("c057_b02_unconstrained_n5")
sol_b02 = solve(c_b02)

c_b05 = load_case("c057_b05_unconstrained_n8")
sol_b05 = solve(c_b05)

c_b06 = load_case("c057_b06_unconstrained_n9_optimal")
sol_b06 = solve(c_b06)

c_b07 = load_case("c057_b07_unconstrained_n10_optimal")
sol_b07 = solve(c_b07)

c_b09 = load_case("c057_b09_n4_prefix_03")
sol_b09 = solve(c_b09)

c_b10 = load_case("c057_b10_n4_prefix_01_23")
sol_b10 = solve(c_b10)

# 1. mut_01: removed comparator from n=4 (fails 0-1 principle)
MUTATIONS.append(
    (
        "mut_01_removed_comparator",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": sol_b01["network"][:-1],
        },
        "Dropped last comparator, violating 0-1 principle",
    )
)

# 2. mut_02: swapped two non-commuting comparators in n=4
net_swap = list(sol_b01["network"])
net_swap[3], net_swap[4] = net_swap[4], net_swap[3]
MUTATIONS.append(
    (
        "mut_02_swapped_comparators",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "status": "SOLVED", "network": net_swap},
        "Swapped non-commuting comparators, violating 0-1 principle",
    )
)

# 3. mut_03: exceeded comparator bound k
MUTATIONS.append(
    (
        "mut_03_exceeded_k_bound",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": sol_b01["network"] + [[0, 1]],
        },
        "Length 6 exceeds bound k=5",
    )
)

# 4. mut_04: violated prefix order
MUTATIONS.append(
    (
        "mut_04_violated_prefix_order",
        c_b10,
        {
            "case_id": "c057_b10_n4_prefix_01_23",
            "status": "SOLVED",
            "network": [[2, 3], [0, 1]] + sol_b10["network"][2:],
        },
        "Prefix comparators inverted",
    )
)

# 5. mut_05: missing mandatory prefix comparator
MUTATIONS.append(
    (
        "mut_05_missing_prefix_comparator",
        c_b09,
        {
            "case_id": "c057_b09_n4_prefix_03",
            "status": "SOLVED",
            "network": [[0, 1]] + sol_b09["network"][1:],
        },
        "Network does not start with prefix [[0, 3]]",
    )
)

# 6. mut_06: included forbidden comparator
MUTATIONS.append(
    (
        "mut_06_included_forbidden_comparator",
        c_b09,
        {
            "case_id": "c057_b09_n4_prefix_03",
            "status": "SOLVED",
            "network": sol_b09["network"][:-1] + [[0, 2]],
        },
        "Contains forbidden comparator [0, 2]",
    )
)

# 7. mut_07: self-loop comparator [1, 1]
MUTATIONS.append(
    (
        "mut_07_self_loop_comparator",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[1, 1]] + sol_b01["network"][1:],
        },
        "Contains self-loop [1, 1]",
    )
)

# 8. mut_08: reversed comparator [3, 1]
MUTATIONS.append(
    (
        "mut_08_reversed_comparator",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[3, 1]] + sol_b01["network"][1:],
        },
        "Contains unordered comparator [3, 1]",
    )
)

# 9. mut_09: negative wire index [-1, 2]
MUTATIONS.append(
    (
        "mut_09_negative_wire_index",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[-1, 2]] + sol_b01["network"][1:],
        },
        "Contains negative channel index",
    )
)

# 10. mut_10: wire index >= n
MUTATIONS.append(
    (
        "mut_10_wire_index_ge_n",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[0, 4]] + sol_b01["network"][1:],
        },
        "Contains out-of-bounds channel 4 on n=4",
    )
)

# 11. mut_11: wire float type
MUTATIONS.append(
    (
        "mut_11_wire_float_type",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[0.0, 1]] + sol_b01["network"][1:],
        },
        "Contains float channel index",
    )
)

# 12. mut_12: wire boolean type
MUTATIONS.append(
    (
        "mut_12_wire_bool_type",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[False, 1]] + sol_b01["network"][1:],
        },
        "Contains boolean channel index",
    )
)

# 13. mut_13: wire string type
MUTATIONS.append(
    (
        "mut_13_wire_string_type",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [["0", 1]] + sol_b01["network"][1:],
        },
        "Contains string channel index",
    )
)

# 14. mut_14: comparator is 3-tuple
MUTATIONS.append(
    (
        "mut_14_comparator_is_3_tuple",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[0, 1, 2]] + sol_b01["network"][1:],
        },
        "Malformed comparator of length 3",
    )
)

# 15. mut_15: comparator is single integer
MUTATIONS.append(
    (
        "mut_15_comparator_is_single_int",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[0]] + sol_b01["network"][1:],
        },
        "Malformed comparator of length 1",
    )
)

# 16. mut_16: network is string instead of list
MUTATIONS.append(
    (
        "mut_16_network_not_list",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "status": "SOLVED", "network": "[[0,1],[2,3]]"},
        "Network is string rather than list",
    )
)

# 17. mut_17: missing network field
MUTATIONS.append(
    (
        "mut_17_missing_network_field",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "status": "SOLVED"},
        "SOLVED status with missing network key",
    )
)

# 18. mut_18: empty network on n=4
MUTATIONS.append(
    (
        "mut_18_empty_network_on_n4",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "status": "SOLVED", "network": []},
        "Empty network fails 0-1 principle",
    )
)

# 19. mut_19: false OUT_OF_SCOPE on valid base case
MUTATIONS.append(
    (
        "mut_19_false_oos_on_valid_base",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "SPOOFED_ERROR"},
        },
        "False OUT_OF_SCOPE on valid case",
    )
)

# 20. mut_20: false OUT_OF_SCOPE on valid prefix case
MUTATIONS.append(
    (
        "mut_20_false_oos_on_valid_prefix",
        c_b09,
        {
            "case_id": "c057_b09_n4_prefix_03",
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "SPOOFED_ERROR"},
        },
        "False OUT_OF_SCOPE on valid prefix case",
    )
)

# 21. mut_21: spoofed SOLVED on infeasible n=4 k=4
c_b25 = load_case("c057_b25_infeas_n4_k4")
MUTATIONS.append(
    (
        "mut_21_spoofed_solved_on_infeasible_n4_k4",
        c_b25,
        {
            "case_id": "c057_b25_infeas_n4_k4",
            "status": "SOLVED",
            "network": [[0, 1], [2, 3], [0, 2], [1, 3]],
        },
        "Claims SOLVED on infeasible bound k=4",
    )
)

# 22. mut_22: spoofed SOLVED on infeasible n=9 k=24
c_b30 = load_case("c057_b30_infeas_n9_k24")
MUTATIONS.append(
    (
        "mut_22_spoofed_solved_on_infeasible_n9_k24",
        c_b30,
        {
            "case_id": "c057_b30_infeas_n9_k24",
            "status": "SOLVED",
            "network": sol_b06["network"][:24],
        },
        "Claims SOLVED on infeasible bound k=24 for n=9",
    )
)

# 23. mut_23: spoofed SOLVED on infeasible n=10 k=28
c_b31 = load_case("c057_b31_infeas_n10_k28")
MUTATIONS.append(
    (
        "mut_23_spoofed_solved_on_infeasible_n10_k28",
        c_b31,
        {
            "case_id": "c057_b31_infeas_n10_k28",
            "status": "SOLVED",
            "network": sol_b07["network"][:28],
        },
        "Claims SOLVED on infeasible bound k=28 for n=10",
    )
)

# 24. mut_24: spoofed SOLVED on poison reversed prefix
c_p03 = load_case("c057_p03_prefix_reversed_order")
MUTATIONS.append(
    (
        "mut_24_spoofed_solved_on_poison_reversed_prefix",
        c_p03,
        {
            "case_id": "c057_p03_prefix_reversed_order",
            "status": "SOLVED",
            "network": [[0, 1], [2, 3], [0, 2], [1, 3], [1, 2]],
        },
        "Claims SOLVED on case with invalid prefix comparator [3, 1]",
    )
)

# 25. mut_25: spoofed SOLVED on poison self loop
c_p04 = load_case("c057_p04_prefix_self_loop")
MUTATIONS.append(
    (
        "mut_25_spoofed_solved_on_poison_self_loop",
        c_p04,
        {"case_id": "c057_p04_prefix_self_loop", "status": "SOLVED", "network": sol_b02["network"]},
        "Claims SOLVED on case with prefix self-loop [2, 2]",
    )
)

# 26. mut_26: spoofed SOLVED on poison oob wire
c_p05 = load_case("c057_p05_prefix_oob_wire")
MUTATIONS.append(
    (
        "mut_26_spoofed_solved_on_poison_oob_wire",
        c_p05,
        {"case_id": "c057_p05_prefix_oob_wire", "status": "SOLVED", "network": []},
        "Claims SOLVED on case with prefix channel 6 on n=6",
    )
)

# 27. mut_27: spoofed SOLVED on poison collision
c_p10 = load_case("c057_p10_prefix_forbidden_collision")
MUTATIONS.append(
    (
        "mut_27_spoofed_solved_on_poison_collision",
        c_p10,
        {
            "case_id": "c057_p10_prefix_forbidden_collision",
            "status": "SOLVED",
            "network": sol_b01["network"],
        },
        "Claims SOLVED on case where prefix comparator is forbidden",
    )
)

# 28. mut_28: spoofed SOLVED on poison n=3
c_p11 = load_case("c057_p11_n_too_small")
MUTATIONS.append(
    (
        "mut_28_spoofed_solved_on_poison_n3",
        c_p11,
        {
            "case_id": "c057_p11_n_too_small",
            "status": "SOLVED",
            "network": [[0, 1], [1, 2], [0, 1]],
        },
        "Claims SOLVED on out-of-scope n=3",
    )
)

# 29. mut_29: spoofed SOLVED on poison n=13
c_p12 = load_case("c057_p12_n_too_large")
MUTATIONS.append(
    (
        "mut_29_spoofed_solved_on_poison_n13",
        c_p12,
        {"case_id": "c057_p12_n_too_large", "status": "SOLVED", "network": []},
        "Claims SOLVED on out-of-scope n=13",
    )
)

# 30. mut_30: spoofed SOLVED on poison negative k
c_p13 = load_case("c057_p13_negative_k")
MUTATIONS.append(
    (
        "mut_30_spoofed_solved_on_poison_negative_k",
        c_p13,
        {"case_id": "c057_p13_negative_k", "status": "SOLVED", "network": []},
        "Claims SOLVED on out-of-scope negative bound k=-1",
    )
)

# 31. mut_31: spoofed SOLVED on poison boolean wire
c_p14 = load_case("c057_p14_prefix_channel_is_boolean")
MUTATIONS.append(
    (
        "mut_31_spoofed_solved_on_poison_boolean_wire",
        c_p14,
        {
            "case_id": "c057_p14_prefix_channel_is_boolean",
            "status": "SOLVED",
            "network": sol_b01["network"],
        },
        "Claims SOLVED on case with boolean channel index",
    )
)

# 32. mut_32: single bit flip failure on n=5 (omitting last comparator)
MUTATIONS.append(
    (
        "mut_32_single_bit_flip_fails_01",
        c_b02,
        {
            "case_id": "c057_b02_unconstrained_n5",
            "status": "SOLVED",
            "network": sol_b02["network"][:-1],
        },
        "Omitting last comparator [2, 3] on n=5",
    )
)

# 33. mut_33: trivial single comparator network on n=4
MUTATIONS.append(
    (
        "mut_33_all_zeros_passes_but_random_fails",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "status": "SOLVED", "network": [[0, 1]]},
        "Trivial network [[0, 1]] fails 0-1 principle on n=4",
    )
)

# 34. mut_34: unknown status string
MUTATIONS.append(
    (
        "mut_34_unknown_status_string",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SUCCESS",
            "network": sol_b01["network"],
        },
        "Invalid status string 'SUCCESS'",
    )
)

# 35. mut_35: missing status field
MUTATIONS.append(
    (
        "mut_35_missing_status_field",
        c_b01,
        {"case_id": "c057_b01_unconstrained_n4", "network": sol_b01["network"]},
        "Missing 'status' key in solution",
    )
)

# 36. mut_36: case_id mismatch
MUTATIONS.append(
    (
        "mut_36_case_id_mismatch",
        c_b01,
        {"case_id": "c057_wrong_id", "status": "SOLVED", "network": sol_b01["network"]},
        "Case ID mismatch",
    )
)

# 37. mut_37: solution is list
MUTATIONS.append(
    (
        "mut_37_solution_not_dict",
        c_b01,
        ["SOLVED", sol_b01["network"]],
        "Solution is list instead of dictionary",
    )
)

# 38. mut_38: solution is null
MUTATIONS.append(("mut_38_solution_null", c_b01, None, "Solution is None"))

# 39. mut_39: comparator is dict instead of list
MUTATIONS.append(
    (
        "mut_39_comparator_is_dict",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [{"i": 0, "j": 1}] + sol_b01["network"][1:],
        },
        "Comparator is dictionary instead of pair",
    )
)

# 40. mut_40: network contains None channel
MUTATIONS.append(
    (
        "mut_40_network_contains_null",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[None, 1]] + sol_b01["network"][1:],
        },
        "Channel index is None",
    )
)

# 41. mut_41: network contains NaN channel
MUTATIONS.append(
    (
        "mut_41_network_contains_nan",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[float("nan"), 1]] + sol_b01["network"][1:],
        },
        "Channel index is float NaN",
    )
)

# 42. mut_42: network contains Inf channel
MUTATIONS.append(
    (
        "mut_42_network_contains_inf",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "SOLVED",
            "network": [[0, float("inf")]] + sol_b01["network"][1:],
        },
        "Channel index is float infinity",
    )
)

# 43. mut_43: drop last comparator from n=8
MUTATIONS.append(
    (
        "mut_43_n8_drop_last_comparator",
        c_b05,
        {
            "case_id": "c057_b05_unconstrained_n8",
            "status": "SOLVED",
            "network": sol_b05["network"][:-1],
        },
        "Dropped last comparator on n=8 network",
    )
)

# 44. mut_44: drop last comparator from n=9
MUTATIONS.append(
    (
        "mut_44_n9_drop_last_comparator",
        c_b06,
        {
            "case_id": "c057_b06_unconstrained_n9_optimal",
            "status": "SOLVED",
            "network": sol_b06["network"][:-1],
        },
        "Dropped last comparator on n=9 network",
    )
)

# 45. mut_45: drop last comparator from n=10
MUTATIONS.append(
    (
        "mut_45_n10_drop_last_comparator",
        c_b07,
        {
            "case_id": "c057_b07_unconstrained_n10_optimal",
            "status": "SOLVED",
            "network": sol_b07["network"][:-1],
        },
        "Dropped last comparator on n=10 network",
    )
)

# 46. mut_46: append forbidden comparator at end of valid network
MUTATIONS.append(
    (
        "mut_46_forbidden_used_at_end",
        c_b09,
        {
            "case_id": "c057_b09_n4_prefix_03",
            "status": "SOLVED",
            "network": sol_b09["network"][:4] + [[0, 2]],
        },
        "Appended forbidden comparator [0, 2] at end",
    )
)

# 47. mut_47: prefix truncated
MUTATIONS.append(
    (
        "mut_47_prefix_truncated",
        c_b10,
        {
            "case_id": "c057_b10_n4_prefix_01_23",
            "status": "SOLVED",
            "network": [[0, 1]] + sol_b10["network"][2:],
        },
        "Second comparator of prefix [[2, 3]] omitted",
    )
)

# 48. mut_48: false UNKNOWN on easily feasible unconstrained n=4
MUTATIONS.append(
    (
        "mut_48_false_unknown_on_unconstrained_n4",
        c_b01,
        {
            "case_id": "c057_b01_unconstrained_n4",
            "status": "UNKNOWN",
            "code": "NO_NETWORK_FOUND_WITHIN_BOUND",
        },
        "False UNKNOWN on feasible base case",
    )
)

assert len(MUTATIONS) == 48, f"Expected 48 mutations, got {len(MUTATIONS)}"

killed_exact = 0
killed_indep = 0

for mut_id, case, corrupted_sol, desc in MUTATIONS:
    ok1, msg1 = check(case, corrupted_sol)
    ok2, msg2 = independent_check(case, corrupted_sol)

    assert not ok1, f"Exact checker SURVIVED mutation {mut_id}! msg={msg1}"
    assert not ok2, f"Independent checker SURVIVED mutation {mut_id}! msg={msg2}"

    killed_exact += 1
    killed_indep += 1

    file_path = mutations_dir / f"{mut_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "mutation_id": mut_id,
                "description": desc,
                "case": case,
                "corrupted_solution": corrupted_sol,
                "exact_checker_rejection": msg1,
                "independent_checker_rejection": msg2,
            },
            f,
            indent=2,
        )

print(
    f"Verified 48/48 hostile mutations killed by BOTH checkers: exact={killed_exact}/48, indep={killed_indep}/48!"
)
