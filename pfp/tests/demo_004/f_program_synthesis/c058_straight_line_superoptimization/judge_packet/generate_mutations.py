"""Generate and verify 48 Hostile Mutations for C058 Judge Packet.

Verifies that BOTH exact_checker and independent_checker REJECT (kill) 100% of mutations.
"""

import json
import sys
from pathlib import Path

# Ensure repository root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[6]))

from omega_engine_pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet.exact_checker import (
    verify_candidate,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet.independent_checker import (
    check_candidate_indep,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.reference_solver import (
    solve,
)

cases_dir = Path(__file__).resolve().parent / "cases"
mutations_dir = Path(__file__).resolve().parent / "hostile_mutations"
mutations_dir.mkdir(parents=True, exist_ok=True)


def load_case(case_id: str) -> dict:
    with open(cases_dir / f"{case_id}.json", "r", encoding="utf-8") as f:
        return json.load(f)


MUTATIONS = []

# Base solved cases
c_b01 = load_case("c058_b01_xor_sub")
sol_b01 = solve(c_b01)

c_b04 = load_case("c058_b04_clear_lowest_bit")
sol_b04 = solve(c_b04)

c_b05 = load_case("c058_b05_isolate_lowest_bit")
sol_b05 = solve(c_b05)

c_b06 = load_case("c058_b06_double_neg")
sol_b06 = solve(c_b06)

c_b07 = load_case("c058_b07_double_not")
sol_b07 = solve(c_b07)

c_b08 = load_case("c058_b08_xor_cancel")
sol_b08 = solve(c_b08)

c_b10 = load_case("c058_b10_shl_combine")
sol_b10 = solve(c_b10)

c_b11 = load_case("c058_b11_shl_three")
sol_b11 = solve(c_b11)

c_b13 = load_case("c058_b13_redundant_zero_add")
sol_b13 = solve(c_b13)

c_b15 = load_case("c058_b15_ashr_sign")
sol_b15 = solve(c_b15)

c_b16 = load_case("c058_b16_dce_w8")
sol_b16 = solve(c_b16)

c_b17 = load_case("c058_b17_xor_sub_w32")
sol_b17 = solve(c_b17)

c_b23 = load_case("c058_b23_dce_w32")
sol_b23 = solve(c_b23)

c_b27 = load_case("c058_b27_unknown_add_target0")
sol_b27 = solve(c_b27)

# Poisoned cases
c_p01 = load_case("c058_p01_deceptive_note_shl")
c_p03 = load_case("c058_p03_undefined_operand")
c_p05 = load_case("c058_p05_overwrite_input")
c_p06 = load_case("c058_p06_unknown_op_pow")
c_p07 = load_case("c058_p07_unknown_op_div")
c_p08 = load_case("c058_p08_instruction_too_short")
c_p09 = load_case("c058_p09_non_int_const")
c_p10 = load_case("c058_p10_invalid_width_17")
c_p11 = load_case("c058_p11_negative_target_len")

# 1-6: Corrupted output expression / non-equivalence
MUTATIONS.append(
    (
        "mut_01_wrong_operator_add_for_xor",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "add", "x", "y"]],
            "out": "res",
        },
        "Returns x + y instead of x ^ y",
    )
)
MUTATIONS.append(
    (
        "mut_02_wrong_constant_value",
        c_b08,
        {
            "case_id": c_b08["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 1]],
            "out": "res",
        },
        "Returns const 1 instead of const 0 for x ^ x",
    )
)
MUTATIONS.append(
    (
        "mut_03_wrong_variable_identity",
        c_b06,
        {
            "case_id": c_b06["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0]],
            "out": "res",
        },
        "Returns const 0 instead of input variable x for -(-x)",
    )
)
MUTATIONS.append(
    (
        "mut_04_wrong_neg_instead_of_not",
        c_b07,
        {
            "case_id": c_b07["case_id"],
            "status": "SOLVED",
            "ops": [["res", "neg", "x"]],
            "out": "res",
        },
        "Returns neg x instead of x for ~~x",
    )
)
MUTATIONS.append(
    (
        "mut_05_bit_flip_in_shift_constant",
        c_b10,
        {
            "case_id": c_b10["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "shl", "x", 4]],
            "out": "t1",
        },
        "Shift by 4 instead of shift by 5 (wrong combined shift amount)",
    )
)
MUTATIONS.append(
    (
        "mut_06_inverted_clear_lowest_bit",
        c_b04,
        {
            "case_id": c_b04["case_id"],
            "status": "SOLVED",
            "ops": [["res", "or", "x", "x"]],
            "out": "res",
        },
        "Returns x instead of x & (x - 1)",
    )
)

# 7-12: Shift semantics confusion (ashr vs lshr, shl vs ashr)
MUTATIONS.append(
    (
        "mut_07_lshr_instead_of_ashr",
        c_b15,
        {
            "case_id": c_b15["case_id"],
            "status": "SOLVED",
            "ops": [["res", "lshr", "x", 7]],
            "out": "res",
        },
        "Uses logical right shift instead of arithmetic right shift for sign replication",
    )
)
MUTATIONS.append(
    (
        "mut_08_ashr_instead_of_lshr",
        c_b10,
        {
            "case_id": c_b10["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "ashr", "x", 5]],
            "out": "t1",
        },
        "Uses ashr where shl was required",
    )
)
MUTATIONS.append(
    (
        "mut_09_shl_instead_of_lshr",
        c_b15,
        {
            "case_id": c_b15["case_id"],
            "status": "SOLVED",
            "ops": [["res", "shl", "x", 7]],
            "out": "res",
        },
        "Uses left shift instead of right shift",
    )
)
MUTATIONS.append(
    (
        "mut_10_negative_constant_in_shift",
        c_b15,
        {
            "case_id": c_b15["case_id"],
            "status": "SOLVED",
            "ops": [["res", "ashr", "x", -1]],
            "out": "res",
        },
        "Negative shift amount in candidate ops",
    )
)
MUTATIONS.append(
    (
        "mut_11_wrong_shift_amount_off_by_one",
        c_b15,
        {
            "case_id": c_b15["case_id"],
            "status": "SOLVED",
            "ops": [["res", "ashr", "x", 6]],
            "out": "res",
        },
        "Shift by 6 instead of 7 on width 8 sign bit",
    )
)
MUTATIONS.append(
    (
        "mut_12_swap_shift_operands",
        c_b15,
        {
            "case_id": c_b15["case_id"],
            "status": "SOLVED",
            "ops": [["c1", "const", 7], ["res", "ashr", "c1", "x"]],
            "out": "res",
        },
        "Swapped shift source and shift amount",
    )
)

# 13-18: Exceeding length bound target_len
MUTATIONS.append(
    (
        "mut_13_length_exceeds_target_len_by_one",
        c_b01,  # target_len = 1
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "xor", "x", "y"], ["res", "or", "t1", "t1"]],
            "out": "res",
        },
        "Candidate length 2 exceeds target_len 1",
    )
)
MUTATIONS.append(
    (
        "mut_14_returned_original_program_when_shortening_required",
        c_b16,  # target_len = 1, orig len = 4
        {"case_id": c_b16["case_id"], "status": "SOLVED", "ops": c_b16["ops"], "out": c_b16["out"]},
        "Returned original program of length 4 when target_len is 1",
    )
)
MUTATIONS.append(
    (
        "mut_15_length_exceeds_target_zero",
        c_b06,  # target_len = 0
        {
            "case_id": c_b06["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "or", "x", "x"]],
            "out": "t1",
        },
        "Length 1 when target_len is 0",
    )
)
MUTATIONS.append(
    (
        "mut_16_double_length_exceeds_target",
        c_b17,  # target_len = 1
        {
            "case_id": c_b17["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "xor", "x", "y"], ["t2", "const", 0], ["t3", "or", "t1", "t2"]],
            "out": "t3",
        },
        "Length 3 when target_len is 1",
    )
)
MUTATIONS.append(
    (
        "mut_17_length_equals_orig_len",
        c_b07,  # target_len = 0, orig len = 2
        {"case_id": c_b07["case_id"], "status": "SOLVED", "ops": c_b07["ops"], "out": c_b07["out"]},
        "Returned original program when target_len is 0",
    )
)
MUTATIONS.append(
    (
        "mut_18_padded_dummy_ops_exceeding_target",
        c_b08,  # target_len = 1
        {
            "case_id": c_b08["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0], ["dummy", "const", 42]],
            "out": "res",
        },
        "Length 2 exceeds target_len 1 due to dummy instruction",
    )
)

# 19-24: Scoping and SSA violations
MUTATIONS.append(
    (
        "mut_19_undefined_operand_in_candidate",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "add", "x", "undefined_var"]],
            "out": "res",
        },
        "Candidate references undefined variable",
    )
)
MUTATIONS.append(
    (
        "mut_20_candidate_overwrites_input",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["x", "xor", "x", "y"]],
            "out": "x",
        },
        "Candidate overwrites input variable x violating SSA",
    )
)
MUTATIONS.append(
    (
        "mut_21_forward_reference_in_candidate",
        c_b16,
        {
            "case_id": c_b16["case_id"],
            "status": "SOLVED",
            "ops": [["res", "add", "t1", "x"], ["t1", "const", 5]],
            "out": "res",
        },
        "Candidate uses t1 before defining it",
    )
)
MUTATIONS.append(
    (
        "mut_22_cyclic_dependency_in_candidate",
        c_b16,
        {
            "case_id": c_b16["case_id"],
            "status": "SOLVED",
            "ops": [["a", "add", "b", "x"], ["b", "add", "a", "x"]],
            "out": "a",
        },
        "Cycle between candidate variables a and b",
    )
)
MUTATIONS.append(
    (
        "mut_23_candidate_variable_assigned_twice",
        c_b16,
        {
            "case_id": c_b16["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "const", 0], ["t1", "const", 1]],
            "out": "t1",
        },
        "Variable t1 defined twice violating SSA",
    )
)
MUTATIONS.append(
    (
        "mut_24_candidate_out_variable_undefined",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "xor", "x", "y"]],
            "out": "nonexistent_var",
        },
        "Candidate specifies nonexistent output variable",
    )
)

# 25-30: Malformed IR syntax and type corruptions
MUTATIONS.append(
    (
        "mut_25_ops_not_a_list",
        c_b01,
        {"case_id": c_b01["case_id"], "status": "SOLVED", "ops": "res = xor x y", "out": "res"},
        "Candidate ops is string instead of list",
    )
)
MUTATIONS.append(
    (
        "mut_26_instruction_not_a_list",
        c_b01,
        {"case_id": c_b01["case_id"], "status": "SOLVED", "ops": ["res xor x y"], "out": "res"},
        "Candidate instruction is string instead of list",
    )
)
MUTATIONS.append(
    (
        "mut_27_unknown_operator_pow",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "pow", "x", "y"]],
            "out": "res",
        },
        "Unsupported operator pow in candidate",
    )
)
MUTATIONS.append(
    (
        "mut_28_constant_as_float",
        c_b08,
        {
            "case_id": c_b08["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0.0]],
            "out": "res",
        },
        "Constant value is float instead of integer",
    )
)
MUTATIONS.append(
    (
        "mut_29_binary_op_missing_operand",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "xor", "x"]],
            "out": "res",
        },
        "Binary operator xor given only 1 operand",
    )
)
MUTATIONS.append(
    (
        "mut_30_out_not_string",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "xor", "x", "y"]],
            "out": 0,
        },
        "Output variable name is int 0 instead of string",
    )
)

# 31-36: Status corruptions / False UNKNOWN claims
MUTATIONS.append(
    (
        "mut_31_false_unknown_on_shortenable_xor",
        c_b01,
        {"case_id": c_b01["case_id"], "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"},
        "Claims UNKNOWN when (x|y)-(x&y) is trivially shortenable to x^y",
    )
)
MUTATIONS.append(
    (
        "mut_32_false_unknown_on_shortenable_identity",
        c_b06,
        {"case_id": c_b06["case_id"], "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"},
        "Claims UNKNOWN when -(-x) is shortenable to 0 ops",
    )
)
c_b01_tlen3 = {**c_b01, "target_len": len(c_b01["ops"])}
MUTATIONS.append(
    (
        "mut_33_false_unknown_when_target_len_equals_input_length",
        c_b01_tlen3,
        {"case_id": c_b01["case_id"], "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"},
        "Claims UNKNOWN on case with target_len >= input length",
    )
)
MUTATIONS.append(
    (
        "mut_34_unknown_with_invalid_code",
        c_b27,
        {"case_id": c_b27["case_id"], "status": "UNKNOWN", "code": "TIMEOUT"},
        "Claims UNKNOWN with code TIMEOUT instead of NO_SHORTER_FOUND",
    )
)
MUTATIONS.append(
    (
        "mut_35_unknown_missing_code_field",
        c_b27,
        {"case_id": c_b27["case_id"], "status": "UNKNOWN"},
        "Claims UNKNOWN without required code field",
    )
)
MUTATIONS.append(
    (
        "mut_36_false_out_of_scope_on_valid_case",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "claims invalid"},
        },
        "Claims OUT_OF_SCOPE on perfectly valid case B01",
    )
)

# 37-42: Guardrail / Poisoned case exploits
MUTATIONS.append(
    (
        "mut_37_solved_claimed_on_undefined_operand",
        c_p03,
        {
            "case_id": c_p03["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0]],
            "out": "res",
        },
        "Claims SOLVED on poisoned case with undefined operand",
    )
)
MUTATIONS.append(
    (
        "mut_38_unknown_claimed_on_undefined_operand",
        c_p03,
        {"case_id": c_p03["case_id"], "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"},
        "Claims UNKNOWN on poisoned case with undefined operand",
    )
)
MUTATIONS.append(
    (
        "mut_39_solved_claimed_on_unknown_op_pow",
        c_p06,
        {
            "case_id": c_p06["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0]],
            "out": "res",
        },
        "Claims SOLVED on poisoned case with unknown op pow",
    )
)
MUTATIONS.append(
    (
        "mut_40_solved_claimed_on_invalid_width_17",
        c_p10,
        {
            "case_id": c_p10["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0]],
            "out": "res",
        },
        "Claims SOLVED on poisoned case with width 17",
    )
)
MUTATIONS.append(
    (
        "mut_41_solved_claimed_on_negative_target_len",
        c_p11,
        {"case_id": c_p11["case_id"], "status": "SOLVED", "ops": [], "out": "x"},
        "Claims SOLVED on poisoned case with negative target_len",
    )
)
MUTATIONS.append(
    (
        "mut_42_solved_claimed_on_input_overwrite",
        c_p05,
        {
            "case_id": c_p05["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 0]],
            "out": "res",
        },
        "Claims SOLVED on poisoned case that overwrites input",
    )
)

# 43-48: Corner-case bit-vector semantics & protocol violations
MUTATIONS.append(
    (
        "mut_43_case_id_mismatch",
        c_b01,
        {
            "case_id": "c058_b02_xor_xor",
            "status": "SOLVED",
            "ops": [["res", "xor", "x", "y"]],
            "out": "res",
        },
        "Mismatched case_id in certificate response",
    )
)
MUTATIONS.append(
    (
        "mut_44_missing_case_id_field",
        c_b01,
        {"status": "SOLVED", "ops": [["res", "xor", "x", "y"]], "out": "res"},
        "Missing case_id field in candidate response",
    )
)
MUTATIONS.append(
    (
        "mut_45_invalid_status_string",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "OPTIMIZED",
            "ops": [["res", "xor", "x", "y"]],
            "out": "res",
        },
        "Invalid status string OPTIMIZED",
    )
)
MUTATIONS.append(
    (
        "mut_46_candidate_not_a_dict",
        c_b01,
        '{"case_id": "c058_b01_xor_sub", "status": "SOLVED"}',
        "Candidate response passed as unparsed JSON string instead of dict",
    )
)
MUTATIONS.append(
    (
        "mut_47_constant_not_masked_to_width",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["res", "const", 256]],
            "out": "res",
        },
        "Constant 256 exceeds 8-bit range (not masked to width 8)",
    )
)
MUTATIONS.append(
    (
        "mut_48_dst_equals_argument_before_definition",
        c_b01,
        {
            "case_id": c_b01["case_id"],
            "status": "SOLVED",
            "ops": [["t1", "add", "t1", "x"]],
            "out": "t1",
        },
        "Instruction uses its own dst variable as an argument before assignment",
    )
)


def main():
    print(f"Total mutations defined: {len(MUTATIONS)}")
    assert len(MUTATIONS) == 48, f"Expected exactly 48 mutations, got {len(MUTATIONS)}"

    exact_kills = 0
    indep_kills = 0
    escapes = 0

    for idx, (m_id, case, cand, desc) in enumerate(MUTATIONS, 1):
        # Save mutation file
        mut_path = mutations_dir / f"{m_id}.json"
        with open(mut_path, "w", encoding="utf-8") as f:
            json.dump(
                {"mutation_id": m_id, "description": desc, "case": case, "candidate": cand},
                f,
                indent=2,
            )

        ok_exact, msg_exact = verify_candidate(case, cand)
        ok_indep, msg_indep = check_candidate_indep(case, cand)

        if not ok_exact:
            exact_kills += 1
        if not ok_indep:
            indep_kills += 1

        if ok_exact or ok_indep:
            escapes += 1
            print(
                f"ESCAPE on {m_id}: exact={ok_exact} ({msg_exact}), indep={ok_indep} ({msg_indep})"
            )
        else:
            # mutation was killed by both checkers
            pass

    print(
        f"Exact checker kills:       {exact_kills} / {len(MUTATIONS)} ({exact_kills / len(MUTATIONS) * 100:.1f}%)"
    )
    print(
        f"Independent checker kills: {indep_kills} / {len(MUTATIONS)} ({indep_kills / len(MUTATIONS) * 100:.1f}%)"
    )
    print(f"Total escapes:             {escapes}")

    assert escapes == 0, f"{escapes} mutations escaped detection!"
    print("All 48 hostile mutations killed successfully with ZERO escapes!")


if __name__ == "__main__":
    main()
