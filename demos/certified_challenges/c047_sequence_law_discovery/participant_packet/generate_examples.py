import json
import math
import os
import random

from c047_sequence_law_discovery.reference_solver import (
    solve,
)

out_dir = "projects/mssn_sn_symgam/challenges/e_formal_math/c047_sequence_law_discovery/participant_packet/examples"
os.makedirs(out_dir, exist_ok=True)

examples = []

# 1. Fibonacci
fib = [0, 1]
for _ in range(40):
    fib.append(fib[-1] + fib[-2])
examples.append(
    {"case_id": "ex_01_fibonacci", "terms": [str(x) for x in fib[:35]], "r_max": 2, "d_max": 0}
)

# 2. Catalan
cat = [math.comb(2 * n, n) // (n + 1) for n in range(35)]
examples.append(
    {"case_id": "ex_02_catalan", "terms": [str(x) for x in cat], "r_max": 2, "d_max": 1}
)

# 3. Repeated root: (n+1) * 2^n
rep = [(n + 1) * (2**n) for n in range(35)]
examples.append(
    {"case_id": "ex_03_repeated_root", "terms": [str(x) for x in rep], "r_max": 2, "d_max": 0}
)

# 4. Period 3: 1, 0, -1, 1, 0, -1, ...
p3 = [1, 0, -1] * 12
examples.append(
    {"case_id": "ex_04_period_three", "terms": [str(x) for x in p3[:35]], "r_max": 3, "d_max": 0}
)

# 5. Preperiod: 3 arbitrary terms, then Fibonacci
prep = [7, 13, 99] + fib[:32]
examples.append(
    {"case_id": "ex_05_preperiod", "terms": [str(x) for x in prep], "r_max": 2, "d_max": 0}
)

# 6. Central binomial: comb(2n, n)
cb = [math.comb(2 * n, n) for n in range(35)]
examples.append(
    {"case_id": "ex_06_central_binomial", "terms": [str(x) for x in cb], "r_max": 2, "d_max": 1}
)

# 7. Pseudorandom decoy
rng = random.Random(42)
prand = [rng.randint(-1000, 1000) for _ in range(35)]
examples.append(
    {
        "case_id": "ex_07_pseudo_random_decoy",
        "terms": [str(x) for x in prand],
        "r_max": 2,
        "d_max": 1,
    }
)

# 8. Order 9 decoy under r_max=8
o9 = [1, 1, 1, 1, 1, 1, 1, 1, 1]
for _ in range(40):
    o9.append(sum(o9[-9:]))
examples.append(
    {"case_id": "ex_08_order_9_decoy", "terms": [str(x) for x in o9[:40]], "r_max": 8, "d_max": 0}
)

# 9. Non integer term
non_int = [str(x) for x in fib[:35]]
non_int[11] = "not_a_number"
examples.append({"case_id": "ex_09_non_integer_term", "terms": non_int, "r_max": 2, "d_max": 0})

# 10. Jacobsthal: J(n+2) = J(n+1) + 2 J(n)
jac = [0, 1]
for _ in range(35):
    jac.append(jac[-1] + 2 * jac[-2])
examples.append(
    {"case_id": "ex_10_jacobsthal", "terms": [str(x) for x in jac[:35]], "r_max": 2, "d_max": 0}
)

# 11. Pell: P(n+2) = 2 P(n+1) + P(n)
pell = [0, 1]
for _ in range(35):
    pell.append(2 * pell[-1] + pell[-2])
examples.append(
    {"case_id": "ex_11_pell", "terms": [str(x) for x in pell[:35]], "r_max": 2, "d_max": 0}
)

# 12. Lucas numbers: 2, 1, 3, 4, 7, 11, ...
lucas = [2, 1]
for _ in range(35):
    lucas.append(lucas[-1] + lucas[-2])
examples.append(
    {"case_id": "ex_12_lucas", "terms": [str(x) for x in lucas[:35]], "r_max": 2, "d_max": 0}
)

for ex in examples:
    res = solve(ex)
    print(
        f"{ex['case_id']}: status={res.get('status')} kind={res.get('kind')} witness={res.get('witness')}"
    )
    path = os.path.join(out_dir, f"{ex['case_id']}.json")
    with open(path, "w") as f:
        json.dump({"input": ex, "expected": res}, f, indent=2)

print("Generated 12 public worked examples successfully.")
