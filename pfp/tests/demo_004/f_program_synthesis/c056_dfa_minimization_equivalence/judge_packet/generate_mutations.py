"""Generate and verify 48 hostile mutations for Challenge C056."""

import copy
import json
import sys
from pathlib import Path

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.judge_packet.exact_checker import (
    check_exact,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.judge_packet.independent_checker import (
    independent_check,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver import (
    solve,
)


def generate_and_test_mutations():
    mut_dir = Path(__file__).resolve().parent / "hostile_mutations"
    mut_dir.mkdir(parents=True, exist_ok=True)

    c_min = {
        "case_id": "c056_b07_suffix_abb",
        "task": "MINIMIZE",
        "alphabet": ["a", "b"],
        "regex": "(a|b)*abb",
    }
    sol_min = solve(c_min)

    c_diff = {
        "case_id": "c056_b25_diff_order",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "a*b*",
        "r2": "(a|b)*",
    }
    sol_diff = solve(c_diff)

    c_eq = {
        "case_id": "c056_b18_equiv_universal",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "(a|b)*",
        "r2": "(a*b*)*",
    }
    sol_eq = solve(c_eq)

    c_poison = {
        "case_id": "c056_p03_unclosed_paren",
        "task": "MINIMIZE",
        "alphabet": ["a", "b"],
        "regex": "(a|b*abb",
    }

    mutations = []

    # 1. Redirected delta transition
    m01 = copy.deepcopy(sol_min)
    m01["delta"][0][0] = (m01["delta"][0][0] + 1) % m01["states"]
    mutations.append(("mut_01_redirected_delta", c_min, m01))

    # 2. Non-minimal DFA: extra dummy state added
    m02 = copy.deepcopy(sol_min)
    m02["states"] += 1
    m02["delta"].append([0, 0])
    m02["access"].append("a")
    mutations.append(("mut_02_extra_unreachable_state", c_min, m02))

    # 3. Dropped accept state
    m03 = copy.deepcopy(sol_min)
    m03["accept"] = []
    mutations.append(("mut_03_dropped_accept_state", c_min, m03))

    # 4. Added invalid accept state
    m04 = copy.deepcopy(sol_min)
    m04["accept"].append(0)
    mutations.append(("mut_04_added_non_accept_state", c_min, m04))

    # 5. Access word reaches wrong state
    m05 = copy.deepcopy(sol_min)
    m05["access"][1] = "b"  # reaches 0 instead of 1
    mutations.append(("mut_05_access_word_wrong_state", c_min, m05))

    # 6. Empty access word on state > 0
    m06 = copy.deepcopy(sol_min)
    m06["access"][2] = ""
    mutations.append(("mut_06_empty_access_word_state_2", c_min, m06))

    # 7. Access word contains symbol not in alphabet
    m07 = copy.deepcopy(sol_min)
    m07["access"][1] = "x"
    mutations.append(("mut_07_access_word_foreign_symbol", c_min, m07))

    # 8. Separator fails to distinguish (set to wrong word)
    m08 = copy.deepcopy(sol_min)
    m08["separators"]["0,1"] = "a"  # both 0 and 1 go to 1 on 'a' (neither is accept)
    mutations.append(("mut_08_separator_fails_to_distinguish", c_min, m08))

    # 9. Separator set to foreign symbol
    m09 = copy.deepcopy(sol_min)
    m09["separators"]["0,1"] = "z"
    mutations.append(("mut_09_separator_foreign_symbol", c_min, m09))

    # 10. Missing separator key
    m10 = copy.deepcopy(sol_min)
    del m10["separators"]["0,1"]
    mutations.append(("mut_10_missing_separator_key", c_min, m10))

    # 11. Access list too short
    m11 = copy.deepcopy(sol_min)
    m11["access"].pop()
    mutations.append(("mut_11_access_list_too_short", c_min, m11))

    # 12. Access list too long
    m12 = copy.deepcopy(sol_min)
    m12["access"].append("abba")
    mutations.append(("mut_12_access_list_too_long", c_min, m12))

    # 13. Delta row too short
    m13 = copy.deepcopy(sol_min)
    m13["delta"][0] = [1]
    mutations.append(("mut_13_delta_row_too_short", c_min, m13))

    # 14. Delta row too long
    m14 = copy.deepcopy(sol_min)
    m14["delta"][0] = [1, 0, 2]
    mutations.append(("mut_14_delta_row_too_long", c_min, m14))

    # 15. Delta target out of bounds
    m15 = copy.deepcopy(sol_min)
    m15["delta"][0][0] = 999
    mutations.append(("mut_15_delta_target_out_of_bounds", c_min, m15))

    # 16. Delta target negative
    m16 = copy.deepcopy(sol_min)
    m16["delta"][0][0] = -1
    mutations.append(("mut_16_delta_target_negative", c_min, m16))

    # 17. States count zero
    m17 = copy.deepcopy(sol_min)
    m17["states"] = 0
    mutations.append(("mut_17_states_count_zero", c_min, m17))

    # 18. States count negative
    m18 = copy.deepcopy(sol_min)
    m18["states"] = -4
    mutations.append(("mut_18_states_count_negative", c_min, m18))

    # 19. Float in delta table
    m19 = copy.deepcopy(sol_min)
    m19["delta"][0][0] = 1.0
    mutations.append(("mut_19_float_in_delta", c_min, m19))

    # 20. Float in accept list
    m20 = copy.deepcopy(sol_min)
    m20["accept"] = [3.0]
    mutations.append(("mut_20_float_in_accept", c_min, m20))

    # 21. Float in states field
    m21 = copy.deepcopy(sol_min)
    m21["states"] = 4.0
    mutations.append(("mut_21_float_in_states", c_min, m21))

    # 22. Boolean in accept list
    m22 = copy.deepcopy(sol_min)
    m22["accept"] = [True]
    mutations.append(("mut_22_boolean_in_accept", c_min, m22))

    # 23. Boolean in delta table
    m23 = copy.deepcopy(sol_min)
    m23["delta"][0][0] = False
    mutations.append(("mut_23_boolean_in_delta", c_min, m23))

    # 24. String in delta table
    m24 = copy.deepcopy(sol_min)
    m24["delta"][0][0] = "1"
    mutations.append(("mut_24_string_in_delta", c_min, m24))

    # 25. String in accept list
    m25 = copy.deepcopy(sol_min)
    m25["accept"] = ["3"]
    mutations.append(("mut_25_string_in_accept", c_min, m25))

    # 26. Duplicate in accept list
    m26 = copy.deepcopy(sol_min)
    m26["accept"] = [3, 3]
    mutations.append(("mut_26_duplicate_in_accept", c_min, m26))

    # 27. Claimed DIFFERENT on EQUAL regexes
    m27 = {"case_id": c_eq["case_id"], "status": "SOLVED", "kind": "DIFFERENT", "word": "a"}
    mutations.append(("mut_27_claimed_different_on_equal", c_eq, m27))

    # 28. Claimed EQUAL on DIFFERENT regexes
    m28 = {"case_id": c_diff["case_id"], "status": "SOLVED", "kind": "EQUAL", "bijection": {"0": 0}}
    mutations.append(("mut_28_claimed_equal_on_different", c_diff, m28))

    # 29. Word in EQUIV DIFFERENT accepted in neither language
    # For a*b* vs (a|b)*, (a|b)* accepts everything! But let's test a vs b where 'c' is in neither
    c_ab = {
        "case_id": "c056_b27_diff_single_letter",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "a",
        "r2": "b",
    }
    m29 = {
        "case_id": c_ab["case_id"],
        "status": "SOLVED",
        "kind": "DIFFERENT",
        "word": "aa",
    }  # accepted by neither 'a' nor 'b'
    mutations.append(("mut_29_word_in_neither_language", c_ab, m29))

    # 30. Word in EQUIV DIFFERENT accepted in both languages
    # Word 'ab' accepted by r2, but word '%': in neither.
    # What about r1: a(a|b)* and r2: (a|b)*a? Word 'aa' accepted by both!
    c_both = {
        "case_id": "c056_b32_diff_start_vs_end",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "a(a|b)*",
        "r2": "(a|b)*a",
    }
    m30 = {"case_id": c_both["case_id"], "status": "SOLVED", "kind": "DIFFERENT", "word": "aa"}
    mutations.append(("mut_30_word_in_both_languages", c_both, m30))

    # 31. Word in EQUIV DIFFERENT has symbol not in alphabet
    m31 = copy.deepcopy(sol_diff)
    m31["word"] = "x"
    mutations.append(("mut_31_word_contains_foreign_symbol", c_diff, m31))

    # 32. Word in EQUIV DIFFERENT is not a string
    m32 = copy.deepcopy(sol_diff)
    m32["word"] = 123
    mutations.append(("mut_32_word_not_string", c_diff, m32))

    # 33. Missing word in EQUIV DIFFERENT
    m33 = copy.deepcopy(sol_diff)
    del m33["word"]
    mutations.append(("mut_33_missing_word_field", c_diff, m33))

    # 34. Missing bijection in EQUIV EQUAL
    m34 = copy.deepcopy(sol_eq)
    del m34["bijection"]
    mutations.append(("mut_34_missing_bijection_field", c_eq, m34))

    # 35. Bijection size mismatch
    m35 = copy.deepcopy(sol_eq)
    m35["bijection"] = {}
    mutations.append(("mut_35_bijection_size_mismatch", c_eq, m35))

    # 36. Bijection start state not 0
    m36 = copy.deepcopy(sol_eq)
    m36["bijection"] = {"0": 1, "1": 0}
    mutations.append(("mut_36_bijection_start_not_zero", c_eq, m36))

    # 37. Bijection not injective
    c_comm = {
        "case_id": "c056_b17_equiv_union_comm",
        "task": "EQUIV",
        "alphabet": ["a", "b"],
        "r1": "a|b",
        "r2": "b|a",
    }
    sol_comm = solve(c_comm)
    m37 = copy.deepcopy(sol_comm)
    m37["bijection"]["1"] = m37["bijection"]["0"]  # non-injective
    mutations.append(("mut_37_bijection_not_injective", c_comm, m37))

    # 38. Bijection violates accept homomorphism
    m38 = copy.deepcopy(sol_comm)
    # swap values in bijection such that accept state maps to non-accept
    keys = list(m38["bijection"].keys())
    if len(keys) >= 2:
        m38["bijection"][keys[0]], m38["bijection"][keys[1]] = (
            m38["bijection"][keys[1]],
            m38["bijection"][keys[0]],
        )
    mutations.append(("mut_38_bijection_violates_accept", c_comm, m38))

    # 39. Bijection violates transition homomorphism
    m39 = copy.deepcopy(sol_comm)
    # invert mappings
    m39["bijection"] = {
        str(k): (v + 1) % len(m39["bijection"]) for k, v in m39["bijection"].items()
    }
    m39["bijection"]["0"] = 0
    mutations.append(("mut_39_bijection_violates_transitions", c_comm, m39))

    # 40. False OUT_OF_SCOPE on valid case
    m40 = {
        "case_id": c_min["case_id"],
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "FAKE_ERROR"},
    }
    mutations.append(("mut_40_false_oos_on_valid_case", c_min, m40))

    # 41. Spoofed SOLVED on unclosed paren case
    m41 = {
        "case_id": c_poison["case_id"],
        "status": "SOLVED",
        "states": 1,
        "accept": [0],
        "delta": [[0, 0]],
        "access": [""],
        "separators": {},
    }
    mutations.append(("mut_41_spoofed_solved_on_poison", c_poison, m41))

    # 42. Spoofed SOLVED on empty alphabet case
    c_p_alpha = {
        "case_id": "c056_p07_empty_alphabet",
        "task": "MINIMIZE",
        "alphabet": [],
        "regex": "a*",
    }
    m42 = {
        "case_id": c_p_alpha["case_id"],
        "status": "SOLVED",
        "states": 1,
        "accept": [0],
        "delta": [[]],
        "access": [""],
        "separators": {},
    }
    mutations.append(("mut_42_spoofed_solved_on_empty_alpha", c_p_alpha, m42))

    # 43. Spoofed SOLVED on symbol not in alphabet
    c_p_sym = {
        "case_id": "c056_p05_symbol_not_in_alpha",
        "task": "MINIMIZE",
        "alphabet": ["a", "b"],
        "regex": "a*b*c",
    }
    m43 = {
        "case_id": c_p_sym["case_id"],
        "status": "SOLVED",
        "states": 1,
        "accept": [0],
        "delta": [[0, 0]],
        "access": [""],
        "separators": {},
    }
    mutations.append(("mut_43_spoofed_solved_on_bad_symbol", c_p_sym, m43))

    # 44. Spoofed SOLVED on missing regex key
    c_p_miss = {"case_id": "c056_p09_missing_regex_key", "task": "MINIMIZE", "alphabet": ["a", "b"]}
    m44 = {
        "case_id": c_p_miss["case_id"],
        "status": "SOLVED",
        "states": 1,
        "accept": [0],
        "delta": [[0, 0]],
        "access": [""],
        "separators": {},
    }
    mutations.append(("mut_44_spoofed_solved_on_missing_key", c_p_miss, m44))

    # 45. Unknown kind in EQUIV
    m45 = copy.deepcopy(sol_diff)
    m45["kind"] = "MAYBE_EQUAL"
    mutations.append(("mut_45_unknown_equiv_kind", c_diff, m45))

    # 46. Case ID mismatch
    m46 = copy.deepcopy(sol_min)
    m46["case_id"] = "WRONG_ID"
    mutations.append(("mut_46_case_id_mismatch", c_min, m46))

    # 47. Missing status field
    m47 = copy.deepcopy(sol_min)
    del m47["status"]
    mutations.append(("mut_47_missing_status_field", c_min, m47))

    # 48. Missing delta field
    m48 = copy.deepcopy(sol_min)
    del m48["delta"]
    mutations.append(("mut_48_missing_delta_field", c_min, m48))

    assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

    # Test all mutations against BOTH checkers
    print(f"Testing {len(mutations)} hostile mutations against both checkers...")
    killed_count = 0
    for mid, case_obj, mut_sol in mutations:
        payload = {"mutation_id": mid, "case": case_obj, "mutated_result": mut_sol}
        with open(mut_dir / f"{mid}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        ok_exact, msg_exact = check_exact(case_obj, mut_sol)
        ok_indep, msg_indep = independent_check(case_obj, mut_sol)

        if (not ok_exact) and (not ok_indep):
            killed_count += 1
        else:
            print(
                f"SURVIVED: {mid}: exact=({ok_exact}, '{msg_exact}'), indep=({ok_indep}, '{msg_indep}')"
            )

    print(
        f"Hostile Mutations Killed: {killed_count}/{len(mutations)} ({(killed_count / len(mutations)) * 100:.1f}%)"
    )
    if killed_count == len(mutations):
        print("ALL 48 HOSTILE MUTATIONS SUCCESSFULLY KILLED BY BOTH CHECKERS!")
    return killed_count == len(mutations)


if __name__ == "__main__":
    success = generate_and_test_mutations()
    sys.exit(0 if success else 1)
