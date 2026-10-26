import json
import os

from omega_engine_pfp.tests.demo_004.e_formal_math.c048_ternary_quadratic_forms.reference_solver import (
    solve,
)

out_dir = "omega_engine_projects/mssn_sn_symgam/challenges/e_formal_math/c048_ternary_quadratic_forms/participant_packet/examples"
os.makedirs(out_dir, exist_ok=True)

examples = [
    # 1. Simple rational point: x^2 + y^2 - 2z^2 = 0 -> (1, 1, 1)
    {"case_id": "ex_01_rational_point_simple", "a": "1", "b": "1", "c": "-2"},
    # 2. Local obstruction at 2 and 3: x^2 + y^2 - 3z^2 = 0
    {"case_id": "ex_02_local_obstruction_3", "a": "1", "b": "1", "c": "-3"},
    # 3. Obstruction at inf: x^2 + y^2 + z^2 = 0
    {"case_id": "ex_03_obstruction_inf", "a": "1", "b": "1", "c": "1"},
    # 4. Obstruction at 2: x^2 + y^2 - 7z^2 = 0
    {"case_id": "ex_04_obstruction_2", "a": "1", "b": "1", "c": "-7"},
    # 5. Zero coefficient: x^2 + y^2 = 0 -> (0, 0, 1)
    {"case_id": "ex_05_zero_coeff", "a": "1", "b": "1", "c": "0"},
    # 6. Pythagorean: x^2 + y^2 - z^2 = 0
    {"case_id": "ex_06_pythagorean", "a": "1", "b": "1", "c": "-1"},
    # 7. Scaled point: 2x^2 + 2y^2 - 4z^2 = 0
    {"case_id": "ex_07_scaled_point", "a": "2", "b": "2", "c": "-4"},
    # 8. Large solvable: 3x^2 + 5y^2 - 8z^2 = 0
    {"case_id": "ex_08_large_solvable", "a": "3", "b": "5", "c": "-8"},
    # 9. Obstruction at 7: x^2 + 2y^2 - 7z^2 = 0
    {"case_id": "ex_09_obstruction_7", "a": "1", "b": "2", "c": "-7"},
    # 10. Malformed input
    {"case_id": "ex_10_malformed_input", "a": "not_an_int", "b": "1", "c": "-1"},
    # 11. All negative obstruction at inf: -x^2 - 2y^2 - 3z^2 = 0
    {"case_id": "ex_11_all_negative_inf", "a": "-1", "b": "-2", "c": "-3"},
    # 12. Opposite pair: 5x^2 - 5y^2 + 13z^2 = 0
    {"case_id": "ex_12_opposite_pair", "a": "5", "b": "-5", "c": "13"},
]

for ex in examples:
    res = solve(ex)
    print(
        f"{ex['case_id']}: status={res.get('status')} kind={res.get('kind')} place={res.get('place')}"
    )
    path = os.path.join(out_dir, f"{ex['case_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"input": ex, "expected": res}, f, indent=2)

print("Generated 12 public worked examples successfully.")
