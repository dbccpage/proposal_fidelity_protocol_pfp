import glob
import json
import sys
import time

sys.path.insert(0, ".")
from c047_sequence_law_discovery.judge_packet.exact_checker import (
    check_solution,
)
from c047_sequence_law_discovery.judge_packet.independent_checker import (
    independent_check,
)
from c047_sequence_law_discovery.reference_solver import (
    solve,
)

case_files = sorted(
    glob.glob(
        "projects/mssn_sn_symgam/challenges/e_formal_math/c047_sequence_law_discovery/judge_packet/cases/*.json"
    )
)
print(f"Total cases: {len(case_files)}", flush=True)

passed = 0
for i, fpath in enumerate(case_files):
    t0 = time.time()
    with open(fpath, "r", encoding="utf-8") as f:
        case = json.load(f)
    cid = case["case_id"]
    print(f"[{i + 1}/{len(case_files)}] Running {cid}...", end="", flush=True)
    res = solve(case)
    ok1, msg1 = check_solution(case, res)
    ok2, msg2 = independent_check(case, res)
    dt = time.time() - t0
    status = "OK" if (ok1 and ok2) else "FAIL"
    st = res.get("status")
    kd = res.get("kind")
    print(f" {status} ({dt:.2f}s) status={st} kind={kd}", flush=True)
    if not (ok1 and ok2):
        print(f"  ok1={ok1} ({msg1}), ok2={ok2} ({msg2})", flush=True)
    else:
        passed += 1

print(f"\nFinal result: {passed}/{len(case_files)} passed.", flush=True)
