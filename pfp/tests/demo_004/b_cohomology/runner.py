"""Run challenge cases through the shared port and independent checker.

This harness reports certificate checks only. It does not execute a the city bout,
claim a retinue verdict, or estimate tokens and label them as billed usage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .judge.certificate_checker import check_cohomology_certificate
from omega_engine_pfp.domain.cohomology.solver import detect_challenge

from .solve import solve
from .swarm.budget_controller import BudgetController


def run_cases(
    cases: Sequence[Mapping[str, Any]],
    output_accounting: Path | None = None,
    budget_ctrl: BudgetController | None = None,
) -> dict[str, Any]:
    """Check every returned result; unknown or unavailable execution is not a pass."""
    results = []
    for index, case in enumerate(cases):
        case_id = case.get("case_id", case.get("id", f"case_{index}"))
        try:
            result = solve(case)
            checked = check_cohomology_certificate(case, result)
        except (RuntimeError, ValueError, TypeError) as exc:
            result = {"status": "UNKNOWN", "refusal": "EXECUTION_UNAVAILABLE", "detail": str(exc)}
            checked = {"passed": False, "error": str(exc)}
        passed = checked["passed"] is True and result.get("status") in ("SOLVED", "OUT_OF_SCOPE")
        results.append(
            {
                "case_id": case_id,
                "challenge": detect_challenge(case),
                "status": result.get("status"),
                "passed": passed,
                "error": checked.get("error"),
                "res": result,
            }
        )
    passed_count = sum(row["passed"] for row in results)
    summary = {
        "total_cases": len(results),
        "passed_cases": passed_count,
        "pass_rate": passed_count / len(results) if results else 0.0,
        "complete": bool(results) and passed_count == len(results),
        "billed_cost_usd": None,
        "within_target_budget": None,
        "cost_measurement": "UNAVAILABLE",
        "authority_effect": "None",
        "results": results,
    }
    if output_accounting is not None:
        output_accounting.parent.mkdir(parents=True, exist_ok=True)
        output_accounting.write_text(
            json.dumps(
                {
                    "schema_version": "omega.accounting.v1",
                    "measurement_status": "UNAVAILABLE",
                    "total_billed_cost_usd": None,
                    "records": [],
                    "detail": "The cohomology port returns no measured billing data.",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check cohomology challenge certificates.")
    parser.add_argument(
        "--suite", choices=["public", "hidden", "controls", "poisoned", "all"], default="public"
    )
    parser.add_argument("--challenge", default="all")
    args = parser.parse_args(argv)
    base_dir = Path(__file__).parent
    suites = [args.suite] if args.suite != "all" else ["public", "hidden", "controls", "poisoned"]
    succeeded = True
    for suite in suites:
        if suite == "public":
            cases = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((base_dir / "examples").glob("*.json"))
            ]
        else:
            filename = {
                "hidden": "hidden_base_cases.json",
                "controls": "gauge_controls.json",
                "poisoned": "poisoned_cases.json",
            }[suite]
            path = base_dir / "judge" / filename
            cases = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
        if args.challenge != "all":
            cases = [case for case in cases if detect_challenge(case) == args.challenge.lower()]
        summary = run_cases(cases)
        succeeded = succeeded and summary["complete"]
        print(f"[{suite.upper()}] Checked: {summary['passed_cases']}/{summary['total_cases']}")
    print("Billing measurement: UNAVAILABLE")
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
