#!/usr/bin/env python3
"""Education Strands Reality Gate (CI/CD and Pre-Commit).

AuthorityEffect: None.

Runs the six declared grammar/domain strand batteries and requires validation
of the MSS-N 50-demo suite seeds, prompts, and expected fixtures. Current source-bound corpus validation is required; partial or unavailable
coverage fails closed even when all six strands pass. A seed inventory does not
replace this requirement.
Designed to run strictly on the local workstation CI engine, never relying on GitHub Actions.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from omega_engine_education.education_app.use_cases.strands.verify_strands import (
    VerifyStrandsUseCase,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class EducationStrandsGateReceipt:
    """Typed machine receipt for education strands gate evaluation."""

    gate_name: str = "education_strands_reality_v1"
    status: str = "PASS"  # "PASS" or "FAIL"
    authority_effect: str = "None"
    total_strands: int = 6
    passed_strands: int = 0
    mssn_demos_validated: int = 0
    mssn_demo_validation: Dict[str, Any] = field(default_factory=dict)
    woland_reality_verdict: str = "UNKNOWN"
    execution_time_sec: float = 0.0
    strand_summaries: Tuple[Dict[str, Any], ...] = ()
    errors: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    nonclaims: Tuple[str, ...] = field(
        default_factory=lambda: (
            "AuthorityEffect: None",
            "Gate execution verifies syntactic, grammar, codec, and AST invariants",
            "No general theorem, learner outcome, mathematical fixture replay or live model "
            "execution follows from these corpus/grammar checks",
        )
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


"""Proposed small corpus-result boundary in the existing education gate."""


def _required_demo_id(value):
    return type(value) is str and len(value) == 7 and value.startswith("DEMO_") and value[5:].isascii() and value[5:].isdigit() and 1 <= int(value[5:]) <= 50


def _required_demo_record_ids(records):
    if type(records) is not list:
        raise ValueError("REQUIRED_DEMO_RECORDS_REQUIRED")
    ids = []
    for record in records:
        if type(record) is not dict or record.get("corpus_bundle_valid") is not True:
            raise ValueError("REQUIRED_DEMO_RECORD_SHAPE")
        identity = record.get("demo_id")
        if not _required_demo_id(identity) or identity in ids:
            raise ValueError("REQUIRED_DEMO_RECORD_IDENTITY")
        ids.append(identity)
    return ids


def _required_demo_missing_ids(result, ids):
    missing = result.get("missing_ids")
    if type(missing) is not list or any(not _required_demo_id(identity) for identity in missing):
        raise ValueError("REQUIRED_DEMO_MISSING_IDENTITIES")
    if len(missing) != len(set(missing)) or set(ids) & set(missing):
        raise ValueError("REQUIRED_DEMO_DUPLICATE_COVERAGE")
    return missing


def _required_demo_result_count(result):
    if type(result) is not dict or result.get("schema") != "pfp.mssn-corpus-validation.v1":
        raise ValueError("REQUIRED_DEMO_VALIDATION_RESULT_REQUIRED")
    count = result.get("validated_count")
    if type(count) is not int or type(result.get("required_count")) is not int or result["required_count"] != 50:
        raise ValueError("REQUIRED_DEMO_COVERAGE_TYPE")
    ids = _required_demo_record_ids(result.get("record_results"))
    missing = _required_demo_missing_ids(result, ids)
    if count != len(ids) or len(ids) + len(missing) != 50:
        raise ValueError("REQUIRED_DEMO_COVERAGE_MISMATCH")
    return count


def _required_demo_complete(result, count):
    return count == 50 and not result["errors"] and not result["missing_ids"]


def _required_demo_policy(result, count):
    if result.get("authority_effect") != "None" or type(result.get("errors")) is not list:
        raise ValueError("REQUIRED_DEMO_RESULT_POLICY")
    if result.get("availability") == "UNAVAILABLE":
        if count != 0:
            raise ValueError("UNAVAILABLE_DEMOS_CANNOT_COUNT")
        return "UNAVAILABLE"
    if result.get("availability") != "AVAILABLE" or result.get("status") not in {"PASS", "FAIL"}:
        raise ValueError("REQUIRED_DEMO_RESULT_STATUS")
    complete = _required_demo_complete(result, count)
    if (result["status"] == "PASS") != complete:
        raise ValueError("REQUIRED_DEMO_RESULT_CONTRADICTION")
    return "COMPLETE" if complete else "INCOMPLETE"


def _required_demo_validation(executor):
    """No declaration-only fifty; preserve actual partial records and fail closed."""
    try:
        result = executor.validate_required_mssn_demo_bundles()
        count = _required_demo_result_count(result)
        state = _required_demo_policy(result, count)
        if state == "UNAVAILABLE":
            return 0, result, ("MSSN_REQUIRED_DEMO_OWNER_UNAVAILABLE: current bundle inputs or compilation contract unavailable; zero demos validated",)
        if state == "INCOMPLETE":
            return count, result, (f"MSSN_REQUIRED_DEMO_CORPUS_INCOMPLETE: validated {count}/50; {len(result['missing_ids'])} missing",)
        return count, result, ()
    except (AttributeError, ImportError, KeyError, OSError, TypeError, ValueError, RuntimeError) as error:
        return 0, {}, (f"MSSN_REQUIRED_DEMO_OWNER_UNAVAILABLE: {type(error).__name__}; zero demos validated",)


def evaluate_education_strands_gate() -> EducationStrandsGateReceipt:
    """Evaluate all education strands and MSS-N demo suite integrity."""
    t0 = time.perf_counter()
    errors: List[str] = []
    warnings: List[str] = []
    strand_summaries: List[Dict[str, Any]] = []

    executor = None
    # 1. Run all 6 strands through VerifyStrandsUseCase
    try:
        from omega_engine_education.education_app.infrastructure.strands.strand_verifier_adapter import (
            StrandVerifierAdapter,
        )

        executor = StrandVerifierAdapter(repo_root=REPO_ROOT)
        uc = VerifyStrandsUseCase(executor=executor)
        audit = uc.verify_all_strands()

        passed_count = audit.passed_strands_count
        total_strands = audit.strands_count
        reality_verdict = audit.woland_reality_verdict

        for r in audit.results:
            strand_summaries.append({
                "strand_id": r.strand_id,
                "strand_name": r.strand_name,
                "all_passed": r.all_passed,
                "checks_count": r.checks_count,
                "execution_time_sec": r.execution_time_sec,
                "details": list(r.details),
                "errors": list(r.errors),
            })
            if not r.all_passed:
                errors.extend(f"Strand {r.strand_id} failed: {e}" for e in r.errors)

        if not audit.all_passed:
            errors.append(f"Only {passed_count}/{total_strands} strands passed")
    except Exception as exc:
        passed_count = 0
        total_strands = 6
        reality_verdict = "REFUSE"
        errors.append(f"Strand verification failed with exception: {exc}")

    # 2. Count only current source-bound corpus records from the existing adapter.
    demos_validated, demo_validation, demo_errors = _required_demo_validation(executor)
    errors.extend(demo_errors)

    elapsed = round(time.perf_counter() - t0, 4)
    gate_status = "PASS" if not errors and passed_count == total_strands == 6 else "FAIL"

    return EducationStrandsGateReceipt(
        status=gate_status,
        total_strands=total_strands,
        passed_strands=passed_count,
        mssn_demos_validated=demos_validated,
        mssn_demo_validation=demo_validation,
        woland_reality_verdict=reality_verdict,
        execution_time_sec=elapsed,
        strand_summaries=tuple(strand_summaries),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m omega_engine_operations.use_cases.cicd.education_strands_gate",
        description="Verify education strands reality and MSS-N demo suite integrity.",
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON receipt")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    args = parser.parse_args(argv)

    receipt = evaluate_education_strands_gate()

    if args.json:
        print(json.dumps(receipt.to_dict(), indent=2))
    elif not args.quiet:
        print("\n" + "=" * 70)
        print("EDUCATION STRANDS REALITY GATE RECEIPT")
        print("=" * 70)
        print(f"Gate Status        : {receipt.status}")
        print(f"Strands Verified   : {receipt.passed_strands} / {receipt.total_strands}")
        print(f"MSS-N Demos        : {receipt.mssn_demos_validated} validated")
        print(f"Reality Verdict    : {receipt.woland_reality_verdict}")
        print(f"Execution Time     : {receipt.execution_time_sec}s")
        print(f"AuthorityEffect    : {receipt.authority_effect}")
        for s in receipt.strand_summaries:
            icon = "PASS" if s["all_passed"] else "FAIL"
            print(f"  [{icon}] {s['strand_name']} ({s['strand_id']}): {s['checks_count']} checks, {s['execution_time_sec']}s")
        if receipt.errors:
            print("\nErrors:")
            for err in receipt.errors:
                print(f"  - [FAIL] {err}")
        print("=" * 70 + "\n")


    return 0 if receipt.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
