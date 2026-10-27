"""Commit-Reveal Protocol and Adversary Reality Gate for C060: Checker Synthesis Scored by Mutation Kill Rate."""

import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.exact_checker import (
    verify_candidate,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.generate_mutations import (
    get_mutants,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.judge_packet.independent_checker import (
    independent_check,
)
from projects.mssn_sn_symgam.challenges.f_program_synthesis.c060_self_verifying_checker_synthesis.reference_solver.checker import (
    check as ref_check,
)


def hash_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def run_gate():
    challenge_dir = Path(__file__).resolve().parent
    ref_solver_dir = challenge_dir / "reference_solver"
    judge_dir = challenge_dir / "judge_packet"
    cases_dir = judge_dir / "cases"

    t0 = time.time()
    run_id = f"c060_eval_{int(t0)}"
    runs_dir = REPO_ROOT / "_ic/darpa/adversary" / "runs" / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print("ADVERSARY TERMINAL REALITY GATE: C060 CHECKER SYNTHESIS SCORED BY MUTATION KILL RATE")
    print(f"Run ID: {run_id}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t0))} UTC")
    print("================================================================================")

    # 1. Commit Phase
    solver_files = sorted(ref_solver_dir.glob("*.py"))
    hasher = hashlib.sha256()
    file_hashes = {}
    for sf in solver_files:
        h = hash_file(sf)
        file_hashes[sf.name] = h
        hasher.update(h.encode("utf-8"))
    solver_commitment = hasher.hexdigest()
    print(f"[COMMIT] Solver SHA-256 Digest: {solver_commitment}")
    for name, h in file_hashes.items():
        print(f"  - {name}: {h}")

    # 2. Reveal Phase: Evaluate hidden evaluation cases against reference solver
    case_files = sorted(cases_dir.glob("*.json"))
    print(f"\n[REVEAL] Evaluating {len(case_files)} hidden evaluation cases...")
    passed_cases = 0
    total_cases = len(case_files)
    cases_data = []

    for cf in case_files:
        with open(cf, "r", encoding="utf-8") as f:
            case = json.load(f)
        cases_data.append(case)
        sol = ref_check(case["case"], case["cert"])
        ok_exact, msg_exact = verify_candidate(case, sol)
        ok_indep, msg_indep = independent_check(case, sol)

        if ok_exact and ok_indep:
            passed_cases += 1
        else:
            print(
                f"  [FAIL] {case.get('case_id')}: exact=({ok_exact}, '{msg_exact}'), indep=({ok_indep}, '{msg_indep}')"
            )

    pass_rate = (passed_cases / total_cases) * 100 if total_cases > 0 else 0
    print(f"[REVEAL SUMMARY] Hidden Cases Passed: {passed_cases}/{total_cases} ({pass_rate:.1f}%)")

    # 3. Mutation Stress Testing: Evaluate 48 hostile checker mutants
    mutants = get_mutants()
    total_mutations = len(mutants)
    print(
        f"\n[MUTATION SUITE] Stress-testing suite on {total_mutations} hostile checker mutants..."
    )
    killed_mutations = 0

    for mid, mutant_fn in mutants.items():
        is_killed = False
        for case in cases_data:
            try:
                res = mutant_fn(case["case"], case["cert"])
            except Exception:
                is_killed = True
                break

            ok1, _ = verify_candidate(case, res)
            ok2, _ = independent_check(case, res)
            if (not ok1) or (not ok2):
                is_killed = True
                break

        if is_killed:
            killed_mutations += 1
        else:
            print(f"  [SURVIVED] {mid}: passed all cases without being killed!")

    kill_rate = (killed_mutations / total_mutations) * 100 if total_mutations > 0 else 0
    print(
        f"[MUTATION SUMMARY] Hostile Checker Mutants Killed: {killed_mutations}/{total_mutations} ({kill_rate:.1f}%)"
    )

    # 4. Terminal Gate Verdict
    verdict = (
        "PASS_TO_MASTER"
        if (passed_cases == total_cases and killed_mutations == total_mutations)
        else "REFUSE"
    )
    print("================================================================================")
    print(f"TERMINAL GATE VERDICT: {verdict}")
    print("================================================================================")

    # 5. Persist Adversary Intelligence Bundle (4 files)
    receipt = {
        "run_id": run_id,
        "challenge_id": "c060_self_verifying_checker_synthesis",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t0)),
        "solver_sha256": solver_commitment,
        "solver_files": file_hashes,
        "hidden_cases": {"total": total_cases, "passed": passed_cases, "pass_rate": pass_rate},
        "hostile_mutations": {
            "total": total_mutations,
            "killed": killed_mutations,
            "kill_rate": kill_rate,
        },
        "gate_verdict": verdict,
        "duration_seconds": round(time.time() - t0, 3),
    }

    with open(runs_dir / "receipt.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    with open(runs_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "verdict": verdict,
                "cases_passed": f"{passed_cases}/{total_cases}",
                "mutations_killed": f"{killed_mutations}/{total_mutations}",
            },
            f,
            indent=2,
        )

    with open(runs_dir / "dda_actions.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"action": "COMMIT", "solver_digest": solver_commitment}) + "\n")
        f.write(
            json.dumps(
                {"action": "EVALUATE_HIDDEN_CASES", "passed": passed_cases, "total": total_cases}
            )
            + "\n"
        )
        f.write(
            json.dumps(
                {"action": "STRESS_MUTATIONS", "killed": killed_mutations, "total": total_mutations}
            )
            + "\n"
        )
        f.write(json.dumps({"action": "TERMINAL_GATE", "verdict": verdict}) + "\n")

    with open(runs_dir / "novella.md", "w", encoding="utf-8") as f:
        f.write(f"# Adversary Terminal Reality Gate: Run {run_id}\n\n")
        f.write("- **Challenge:** C060 Checker Synthesis Scored by Mutation Kill Rate\n")
        f.write(f"- **Solver Commitment:** `{solver_commitment}`\n")
        f.write(f"- **Hidden Cases:** {passed_cases}/{total_cases} ({pass_rate:.1f}%)\n")
        f.write(
            f"- **Hostile Mutations Killed:** {killed_mutations}/{total_mutations} ({kill_rate:.1f}%)\n"
        )
        f.write(f"- **Verdict:** `{verdict}`\n")

    print(f"\nPersisted 4-file Adversary intelligence bundle to {runs_dir}")
    return verdict == "PASS_TO_MASTER"


if __name__ == "__main__":
    success = run_gate()
    sys.exit(0 if success else 1)
