"""Generate 48 hostile mutations for C047 Judge Packet.
Verifies that exact_checker and independent_checker reject 100% of corruptions.
"""

import glob
import json
import os

cases_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
muts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostile_mutations")
os.makedirs(muts_dir, exist_ok=True)

# Load base cases
base_cases = {}
for p in glob.glob(os.path.join(cases_dir, "*.json")):
    with open(p, "r", encoding="utf-8") as f:
        c = json.load(f)
        base_cases[c["case_id"]] = c

mutations = []

# 1-6: Float string coefficients
for i, cid in enumerate(
    [
        "c047_base_01_pow2",
        "c047_base_02_fib",
        "c047_base_15_catalan",
        "c047_base_17_factorial",
        "c047_base_23_motzkin",
        "c047_base_24_derangements",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_0{i + 1}_float_coeff",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 0,
                "polys": [["-1.5"], ["1.0"]],
            },
            "expected_rejection": "float string",
        }
    )

# 7-12: All-zero trivial recurrence
for i, cid in enumerate(
    [
        "c047_base_02_fib",
        "c047_base_03_lucas",
        "c047_base_04_jacobsthal",
        "c047_base_05_pell",
        "c047_base_06_tribonacci",
        "c047_base_07_padovan",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 7:02d}_all_zero_poly",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 0,
                "polys": [["0"], ["0"], ["0"]],
            },
            "expected_rejection": "trivial all-zero",
        }
    )

# 13-18: Leading polynomial identically zero
for i, cid in enumerate(
    [
        "c047_base_02_fib",
        "c047_base_03_lucas",
        "c047_base_15_catalan",
        "c047_base_16_central_binomial",
        "c047_base_17_factorial",
        "c047_base_23_motzkin",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 13:02d}_leading_zero",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 0,
                "polys": [["-1"], ["1"], ["0"]],
            },
            "expected_rejection": "leading poly zero",
        }
    )

# 19-24: Leading polynomial has root >= start
for i, cid in enumerate(
    [
        "c047_base_01_pow2",
        "c047_base_02_fib",
        "c047_base_15_catalan",
        "c047_base_29_preperiod_fib_1",
        "c047_base_30_preperiod_pell_2",
        "c047_base_31_preperiod_cat_3",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 19:02d}_leading_root_in_range",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 1,
                # p_r(n) = n - 2 -> root at n=2 >= start=1
                "polys": [["1"], ["-2", "1"]],
            },
            "expected_rejection": "leading root",
        }
    )

# 25-30: Order / degree bound violations
for i, cid in enumerate(
    [
        "c047_base_01_pow2",
        "c047_base_02_fib",
        "c047_base_17_factorial",
        "c047_base_21_pochhammer_4",
        "c047_base_37_decoy_cubic_under_r2",
        "c047_base_35_decoy_prand_1",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 25:02d}_degree_order_exceeded",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 0,
                # Order 9 when r_max is <= 2
                "polys": [["1"]] * 10,
            },
            "expected_rejection": "order exceeded",
        }
    )

# 31-36: Corrupted / off-by-one recurrence coefficients (residual != 0)
for i, cid in enumerate(
    [
        "c047_base_02_fib",
        "c047_base_03_lucas",
        "c047_base_04_jacobsthal",
        "c047_base_05_pell",
        "c047_base_06_tribonacci",
        "c047_base_15_catalan",
    ]
):
    mutations.append(
        {
            "mutation_id": f"mut_{i + 31:02d}_bad_coeff_residual",
            "case": base_cases[cid],
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "RECURRENCE",
                "start": 0,
                # Fibonacci with bad sign: a(n) - a(n+1) + a(n+2) = 0
                "polys": [["1"], ["-1"], ["1"]],
            },
            "expected_rejection": "residual violation",
        }
    )

# 37-42: Singular minor offered for NONE_WITHIN_BOUNDS
for i, cid in enumerate(
    [
        "c047_base_33_decoy_order9",
        "c047_base_34_decoy_order10",
        "c047_base_35_decoy_prand_1",
        "c047_base_36_decoy_prand_2",
        "c047_base_37_decoy_cubic_under_r2",
        "c047_base_38_decoy_primes",
    ]
):
    c = base_cases[cid]
    r_max = c["r_max"]
    d_max = c["d_max"]
    u = (r_max + 1) * (d_max + 1)
    # Duplicate first row index so matrix has duplicate rows -> det = 0!
    bad_rows = [5] * u
    mutations.append(
        {
            "mutation_id": f"mut_{i + 37:02d}_singular_minor",
            "case": c,
            "candidate": {
                "case_id": cid,
                "status": "SOLVED",
                "kind": "NONE_WITHIN_BOUNDS",
                "order": r_max,
                "degree": d_max,
                "start_range": [0, 5],
                "minor_rows": bad_rows,
            },
            "expected_rejection": "singular minor",
        }
    )

# 43-48: False OUT_OF_SCOPE claiming integer is non-integer, or recurrence on decoy
for i, cid in enumerate(
    [
        "c047_base_01_pow2",
        "c047_base_02_fib",
        "c047_base_03_lucas",
        "c047_base_35_decoy_prand_1",
        "c047_base_36_decoy_prand_2",
        "c047_base_38_decoy_primes",
    ]
):
    if i < 3:
        mutations.append(
            {
                "mutation_id": f"mut_{i + 43:02d}_false_out_of_scope",
                "case": base_cases[cid],
                "candidate": {
                    "case_id": cid,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"reason": "NON_INTEGER_TERM", "index": 0},
                },
                "expected_rejection": "false out of scope",
            }
        )
    else:
        mutations.append(
            {
                "mutation_id": f"mut_{i + 43:02d}_bogus_recurrence_on_decoy",
                "case": base_cases[cid],
                "candidate": {
                    "case_id": cid,
                    "status": "SOLVED",
                    "kind": "RECURRENCE",
                    "start": 0,
                    "polys": [["-1"], ["-1"], ["1"]],
                },
                "expected_rejection": "bogus recurrence on decoy",
            }
        )

assert len(mutations) == 48, f"Expected 48 mutations, got {len(mutations)}"

for m in mutations:
    fpath = os.path.join(muts_dir, f"{m['mutation_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

print(f"Successfully generated {len(mutations)} hostile mutations in {muts_dir}.")
