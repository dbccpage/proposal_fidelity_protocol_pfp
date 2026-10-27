from pathlib import Path
import copy
import json
import os
import sys
from fractions import Fraction

for _parent in Path(__file__).resolve().parents:
    if (_parent / "sqlite_pilot_store.py").is_file():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from c051_exact_lp_solver_with_duals.reference_solver import (
    solve,
)


def main():
    cases_dir = os.path.join(os.path.dirname(__file__), "cases")
    mut_dir = os.path.join(os.path.dirname(__file__), "hostile_mutations")
    os.makedirs(mut_dir, exist_ok=True)

    c_opt1 = json.load(open(os.path.join(cases_dir, "case_01_base_opt_degen_2d_vertex.json")))
    c_opt2 = json.load(open(os.path.join(cases_dir, "case_14_base_opt_standard_2x2.json")))
    c_opt3 = json.load(open(os.path.join(cases_dir, "case_16_base_opt_large_3x3.json")))
    c_inf1 = json.load(open(os.path.join(cases_dir, "case_25_base_infeas_single_neg.json")))
    c_inf2 = json.load(open(os.path.join(cases_dir, "case_26_base_infeas_two_bounds.json")))
    c_inf3 = json.load(
        open(os.path.join(cases_dir, "case_27_base_infeas_parallel_hyperplanes.json"))
    )
    c_unb1 = json.load(open(os.path.join(cases_dir, "case_33_base_unbounded_1x1.json")))
    c_unb2 = json.load(open(os.path.join(cases_dir, "case_35_base_unbounded_diagonal_ray.json")))
    c_unb3 = json.load(open(os.path.join(cases_dir, "case_36_base_unbounded_cone_3d.json")))

    s_opt1, s_opt2, s_opt3 = solve(c_opt1), solve(c_opt2), solve(c_opt3)
    s_inf1, s_inf2, s_inf3 = solve(c_inf1), solve(c_inf2), solve(c_inf3)
    s_unb1, s_unb2, s_unb3 = solve(c_unb1), solve(c_unb2), solve(c_unb3)

    mutations = []

    # 1. Dual sign flipped (mut 01-06)
    for idx, (c, s) in enumerate([(c_opt1, s_opt1), (c_opt2, s_opt2), (c_opt3, s_opt3)]):
        m1 = copy.deepcopy(s)
        for i, val in enumerate(m1["y"]):
            if val != "0":
                m1["y"][i] = f"-{val}"
                break
        mutations.append(
            {
                "mut_id": f"mut_{idx * 2 + 1:02d}_dual_sign_flipped",
                "case": c,
                "corrupted_result": m1,
                "type": "dual_sign",
            }
        )
        m2 = copy.deepcopy(s)
        m2["y"][-1] = "-1"
        mutations.append(
            {
                "mut_id": f"mut_{idx * 2 + 2:02d}_dual_negative_entry",
                "case": c,
                "corrupted_result": m2,
                "type": "dual_sign",
            }
        )

    # 2. Primal x perturbed (mut 07-12)
    for idx, (c, s) in enumerate([(c_opt1, s_opt1), (c_opt2, s_opt2), (c_opt3, s_opt3)]):
        m1 = copy.deepcopy(s)
        f0 = Fraction(m1["x"][0]) + Fraction(1, 1000000000)
        m1["x"][0] = f"{f0.numerator}/{f0.denominator}"
        mutations.append(
            {
                "mut_id": f"mut_{7 + idx * 2:02d}_primal_plus_eps",
                "case": c,
                "corrupted_result": m1,
                "type": "primal_eps",
            }
        )
        m2 = copy.deepcopy(s)
        f0 = Fraction(m2["x"][0]) - Fraction(1, 1000000000)
        m2["x"][0] = f"{f0.numerator}/{f0.denominator}"
        mutations.append(
            {
                "mut_id": f"mut_{8 + idx * 2:02d}_primal_minus_eps",
                "case": c,
                "corrupted_result": m2,
                "type": "primal_eps",
            }
        )

    # 3. Value differs from c.x (mut 13-18)
    for idx, (c, s) in enumerate([(c_opt1, s_opt1), (c_opt2, s_opt2), (c_opt3, s_opt3)]):
        m1 = copy.deepcopy(s)
        v = Fraction(m1["value"]) + 1
        m1["value"] = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
        mutations.append(
            {
                "mut_id": f"mut_{13 + idx * 2:02d}_val_off_by_one",
                "case": c,
                "corrupted_result": m1,
                "type": "val_diff",
            }
        )
        m2 = copy.deepcopy(s)
        m2["value"] = "999999"
        mutations.append(
            {
                "mut_id": f"mut_{14 + idx * 2:02d}_val_spoofed",
                "case": c,
                "corrupted_result": m2,
                "type": "val_diff",
            }
        )

    # 4. Farkas y negative (mut 19-24)
    for idx, (c, s) in enumerate([(c_inf1, s_inf1), (c_inf2, s_inf2), (c_inf3, s_inf3)]):
        m1 = copy.deepcopy(s)
        m1["farkas_y"][0] = "-1"
        mutations.append(
            {
                "mut_id": f"mut_{19 + idx * 2:02d}_farkas_neg",
                "case": c,
                "corrupted_result": m1,
                "type": "farkas_neg",
            }
        )
        m2 = copy.deepcopy(s)
        m2["farkas_y"] = ["-1"] * len(m2["farkas_y"])
        mutations.append(
            {
                "mut_id": f"mut_{20 + idx * 2:02d}_farkas_all_neg",
                "case": c,
                "corrupted_result": m2,
                "type": "farkas_neg",
            }
        )

    # 5. Farkas invalid (mut 25-30)
    for idx, (c, s) in enumerate([(c_inf1, s_inf1), (c_inf2, s_inf2), (c_inf3, s_inf3)]):
        m1 = copy.deepcopy(s)
        m1["farkas_y"] = ["0"] * len(m1["farkas_y"])
        mutations.append(
            {
                "mut_id": f"mut_{25 + idx * 2:02d}_farkas_zero",
                "case": c,
                "corrupted_result": m1,
                "type": "farkas_zero",
            }
        )
        m2 = copy.deepcopy(s)
        m2["farkas_y"].append("1")  # length mismatch
        mutations.append(
            {
                "mut_id": f"mut_{26 + idx * 2:02d}_farkas_len_mismatch",
                "case": c,
                "corrupted_result": m2,
                "type": "farkas_len",
            }
        )

    # 6. Unbounded ray Ad > 0 or c.d <= 0 (mut 31-36)
    for idx, (c, s) in enumerate([(c_unb1, s_unb1), (c_unb2, s_unb2), (c_unb3, s_unb3)]):
        m1 = copy.deepcopy(s)
        m1["ray"] = ["0"] * len(m1["ray"])
        mutations.append(
            {
                "mut_id": f"mut_{31 + idx * 2:02d}_ray_zero",
                "case": c,
                "corrupted_result": m1,
                "type": "ray_zero",
            }
        )
        m2 = copy.deepcopy(s)
        m2["ray"] = ["-1"] * len(m2["ray"])
        mutations.append(
            {
                "mut_id": f"mut_{32 + idx * 2:02d}_ray_neg",
                "case": c,
                "corrupted_result": m2,
                "type": "ray_neg",
            }
        )

    # 7. Format violations (mut 37-42)
    m37 = copy.deepcopy(s_opt1)
    m37["value"] = "0.5"
    mutations.append(
        {"mut_id": "mut_37_float_dec", "case": c_opt1, "corrupted_result": m37, "type": "format"}
    )
    m38 = copy.deepcopy(s_opt1)
    m38["x"][0] = True
    mutations.append(
        {"mut_id": "mut_38_bool_x", "case": c_opt1, "corrupted_result": m38, "type": "format"}
    )
    m39 = copy.deepcopy(s_opt1)
    m39["x"][0] = "1/1"
    mutations.append(
        {
            "mut_id": "mut_39_unreduced_1_1",
            "case": c_opt1,
            "corrupted_result": m39,
            "type": "format",
        }
    )
    m40 = copy.deepcopy(s_opt1)
    m40["y"][0] = "2/4"
    mutations.append(
        {
            "mut_id": "mut_40_unreduced_2_4",
            "case": c_opt1,
            "corrupted_result": m40,
            "type": "format",
        }
    )
    m41 = copy.deepcopy(s_inf1)
    m41["farkas_y"][0] = "0.0"
    mutations.append(
        {"mut_id": "mut_41_float_farkas", "case": c_inf1, "corrupted_result": m41, "type": "format"}
    )
    m42 = copy.deepcopy(s_unb1)
    m42["ray"][0] = True
    mutations.append(
        {"mut_id": "mut_42_bool_ray", "case": c_unb1, "corrupted_result": m42, "type": "format"}
    )

    # 8. Status / Kind spoofing (mut 43-48)
    m43 = {
        "case_id": c_opt1["case_id"],
        "status": "SOLVED",
        "kind": "INFEASIBLE",
        "farkas_y": ["1"] * len(c_opt1["b"]),
    }
    mutations.append(
        {"mut_id": "mut_43_spoof_inf", "case": c_opt1, "corrupted_result": m43, "type": "spoof"}
    )
    m44 = {
        "case_id": c_inf1["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "x": ["1"] * len(c_inf1["c"]),
        "y": ["1"] * len(c_inf1["b"]),
        "value": "1",
    }
    mutations.append(
        {"mut_id": "mut_44_spoof_opt", "case": c_inf1, "corrupted_result": m44, "type": "spoof"}
    )
    m45 = {
        "case_id": c_unb1["case_id"],
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "x": ["0"] * len(c_unb1["c"]),
        "y": ["0"] * len(c_unb1["b"]),
        "value": "0",
    }
    mutations.append(
        {"mut_id": "mut_45_spoof_unb", "case": c_unb1, "corrupted_result": m45, "type": "spoof"}
    )
    m46 = {"case_id": c_opt1["case_id"], "status": "OUT_OF_SCOPE", "witness": {"reason": "fake"}}
    mutations.append(
        {"mut_id": "mut_46_spurious_oos", "case": c_opt1, "corrupted_result": m46, "type": "spoof"}
    )
    m47 = copy.deepcopy(s_opt1)
    del m47["y"]
    mutations.append(
        {"mut_id": "mut_47_missing_y", "case": c_opt1, "corrupted_result": m47, "type": "spoof"}
    )
    m48 = copy.deepcopy(s_unb1)
    del m48["ray"]
    mutations.append(
        {"mut_id": "mut_48_missing_ray", "case": c_unb1, "corrupted_result": m48, "type": "spoof"}
    )

    for m in mutations:
        with open(os.path.join(mut_dir, f"{m['mut_id']}.json"), "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)
    print(f"Generated {len(mutations)} hostile mutations.")


if __name__ == "__main__":
    main()
