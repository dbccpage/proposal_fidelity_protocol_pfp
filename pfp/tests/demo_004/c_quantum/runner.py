"""C021 local certificate diagnostics.

Runs the frozen solver against challenge test cases, verifies algebraic & dense certificates,
and logs synthetic cost estimates into accounting.json. This is a native solver diagnostic, with numerical secondary evidence and
synthetic cost estimates. It is not a the city swarm execution or paid model trial.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if __package__ in (None, ""):
    __package__ = "pfp.tests.demo_004.c_quantum"

from pfp.domain.quantum.certificate_checker import check_certificate
from pfp.infrastructure.adapters.stabilizer_rust_adapter import (
    StabilizerRustAdapter,
)
from pfp.infrastructure.quantum.dense_checker import verify_dense_spectrum

from .solve import solve
from .swarm.budget_controller import (
    BudgetController,
)

_STABILIZER = StabilizerRustAdapter()

CHALLENGE_DIR = Path(__file__).parent
EXAMPLES_DIR = CHALLENGE_DIR / "examples"
JUDGE_DIR = CHALLENGE_DIR / "judge"


def run_cases(
    cases: Sequence[Mapping[str, Any]],
    output_accounting: Path | None = None,
    output_answers: Path | None = None,
    budget_ctrl: BudgetController | None = None,
) -> dict[str, Any]:
    """Executes solver on a batch of test cases, recording verification and cost."""
    budget = budget_ctrl or BudgetController()
    results = []
    passed_count = 0
    answers_to_write = []

    for i, case in enumerate(cases):
        case_id = case.get("id", f"case_{i}")
        terms = case.get("terms") or case.get("paulis") or []
        if not isinstance(terms, list):
            terms = []
        n = case.get("n") if "n" in case else case.get("num_qubits", 0)

        # Micro-budget charge
        budget.charge(
            op_id=f"solve_{case_id}",
            solver_name="native_rust_c021",
            inp_tokens=len(terms) * 20 + 30,
            outp_tokens=len(terms) * 15 + 40,
            rate_per_1k_input=Decimal("0.0001"),
            rate_per_1k_output=Decimal("0.0002"),
        )

        res = solve(case)
        answers_to_write.append(res)

        # Verification 1: Primary Algebraic Certificate Checker
        chk1 = check_certificate(case, res, port=_STABILIZER)
        is_passed = chk1.get("verdict") == "PASS" and res.get("status") in (
            "SOLVED",
            "OUT_OF_SCOPE",
        )
        failure_reason = chk1.get("error")
        if res.get("status") == "UNKNOWN":
            failure_reason = res.get("refusal_code", "UNKNOWN")

        # Verification 2: Independent Dense Spectrum Checker (for SOLVED cases with n <= 6)
        dense_passed = True
        if is_passed and res.get("status") == "SOLVED" and isinstance(n, int) and n <= 6:
            chk2 = verify_dense_spectrum(case, res)
            dense_passed = chk2.get("dense_check") in ("PASS", "PASSED")
            if not dense_passed:
                is_passed = False
                failure_reason = f"Dense spectrum mismatch: {chk2}"

        if is_passed:
            passed_count += 1

        results.append(
            {
                "case_id": case_id,
                "status": res.get("status"),
                "passed": is_passed,
                "error": failure_reason,
            }
        )

    if output_answers is not None:
        output_answers.parent.mkdir(parents=True, exist_ok=True)
        with open(output_answers, "w", encoding="utf-8") as f:
            for ans in answers_to_write:
                f.write(json.dumps(ans, sort_keys=True) + "\n")

    if output_accounting is not None:
        output_accounting.parent.mkdir(parents=True, exist_ok=True)
        with open(output_accounting, "w", encoding="utf-8") as f:
            json.dump(budget.ledger.to_dict(), f, indent=2, sort_keys=True)

    return {
        "total_cases": len(cases),
        "passed_cases": passed_count,
        "failed_cases": len(cases) - passed_count,
        "all_passed": bool(cases) and passed_count == len(cases),
        "refused_cases": sum(r.get("status") == "UNKNOWN" for r in results),
        "billed_cost_usd": str(budget.current_cost),
        "cost_basis": "SYNTHETIC_ESTIMATE",
        "billing_verified": False,
        "is_within_target": budget.is_within_target,
        "details": results,
    }


def load_public_cases() -> list[dict]:
    manifest_file = EXAMPLES_DIR / "manifest.json"
    if not manifest_file.exists():
        return []
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    cases = []
    for item in manifest:
        case_file = EXAMPLES_DIR / item["file"]
        with open(case_file, "r", encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def load_judge_file(name: str) -> list[dict]:
    p = JUDGE_DIR / name
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="C021 Challenge Runner")
    parser.add_argument(
        "--suite",
        choices=["public", "hidden", "controls", "poisoned", "all"],
        default="all",
        help="Test suite to execute (default: all)",
    )
    args = parser.parse_args()

    budget = BudgetController()
    accounting_file = CHALLENGE_DIR / "accounting.json"
    # Reference answers include the hidden, control and poisoned suites, so they
    # are written on the judge side, never next to the participant examples.
    answers_file = JUDGE_DIR / "reference_answers.jsonl"

    selected_cases: list[dict] = []
    if args.suite in ("public", "all"):
        pub = load_public_cases()
        print(f"Loaded {len(pub)} public examples.")
        selected_cases.extend(pub)

    if args.suite in ("hidden", "all"):
        hid = load_judge_file("hidden_base_cases.json")
        print(f"Loaded {len(hid)} hidden base cases.")
        selected_cases.extend(hid)

    if args.suite in ("controls", "all"):
        ctrl = load_judge_file("relabel_controls.json")
        print(f"Loaded {len(ctrl)} relabel controls.")
        selected_cases.extend(ctrl)

    if args.suite in ("poisoned", "all"):
        psn = load_judge_file("poisoned_cases.json")
        print(f"Loaded {len(psn)} poisoned cases.")
        selected_cases.extend(psn)

    print(f"\nChecking {len(selected_cases)} C021 cases locally...\n")
    report = run_cases(
        selected_cases,
        output_accounting=accounting_file,
        output_answers=answers_file,
        budget_ctrl=budget,
    )

    print("=" * 70)
    print(f"C021 SUITE EXECUTION SUMMARY: {args.suite.upper()}")
    print("=" * 70)
    print(f"Total Cases Checked:  {report['total_cases']}")
    print(f"Passed Cases:         {report['passed_cases']}")
    print(f"Failed Cases:         {report['failed_cases']}")
    print(f"All Passed:           {report['all_passed']}")
    print(f"Estimated Cost USD (not billed): ${report['billed_cost_usd']}")
    print(f"Target (< $0.05):     {report['is_within_target']}")
    print(f"Hard Ceiling (<= $0.25): {budget.current_cost <= Decimal('0.25')}")
    print("=" * 70)

    if not report["all_passed"]:
        print("\nFailures:")
        for d in report["details"]:
            if not d["passed"]:
                print(f"  [FAIL] {d['case_id']}: status={d['status']}, error={d['error']}")
        sys.exit(1)
    else:
        print("\nAll cases passed with 100% verified certificates.")


if __name__ == "__main__":
    main()
