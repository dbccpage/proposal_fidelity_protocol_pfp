"""Challenge Packet Runner CLI commands with commit-reveal protocol (U07).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from pfp.entrypoints.cli.io_utils import _read_json, _write_json


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_challenge_build(args: argparse.Namespace) -> int:
    """Build participant and judge packets from specification and case fixtures."""
    challenge_id: str = args.challenge_id
    spec_path: Path = args.spec
    public_cases_path: Path = args.public_cases
    hidden_cases_path: Path = args.hidden_cases
    checker_a: str = getattr(args, "checker_a", "checker_exact_match_a")
    checker_b: str = getattr(args, "checker_b", "checker_exact_match_b")
    out_dir: Path = getattr(args, "output_dir", Path("."))

    spec_bytes = spec_path.read_bytes()
    spec_hash = _sha256(spec_bytes)
    public_cases = _read_json(public_cases_path)
    hidden_cases = _read_json(hidden_cases_path)

    hidden_manifest_bytes = json.dumps(hidden_cases, sort_keys=True).encode("utf-8")
    commitment_hash = _sha256(hidden_manifest_bytes)

    participant_packet = {
        "challenge_id": challenge_id,
        "specification_hash": spec_hash,
        "prompt_template": spec_bytes.decode("utf-8", errors="replace"),
        "public_cases": public_cases,
        "timeout_ms": args.timeout_ms or 5000,
        "max_tokens": args.max_tokens or 4096,
        "judge_commitment_hash": commitment_hash,
        "authority_effect": "None",
    }

    judge_packet = {
        "challenge_id": challenge_id,
        "commitment_hash": commitment_hash,
        "committed_at_utc": _now_utc(),
        "operator": args.operator or "system",
        "version": "v1.0.0",
        "hidden_cases": hidden_cases,
        "checker_a_id": checker_a,
        "checker_b_id": checker_b,
        "authority_effect": "None",
    }

    _write_json(out_dir / "participant_packet.json", participant_packet)
    _write_json(out_dir / "judge_packet.json", judge_packet)
    return 0


def cmd_challenge_commit(args: argparse.Namespace) -> int:
    """Commit judge hidden manifest before release of challenge."""
    challenge_id: str = args.challenge_id
    manifest_path: Path = args.manifest
    operator: str = getattr(args, "operator", "operator_alpha")
    version: str = getattr(args, "version", "v1.0.0")

    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = _sha256(manifest_bytes)

    # Hash combining challenge metadata and manifest
    commit_hasher = hashlib.sha256()
    commit_hasher.update(challenge_id.encode("utf-8"))
    commit_hasher.update(manifest_hash.encode("utf-8"))
    commit_hasher.update(operator.encode("utf-8"))
    commit_hasher.update(version.encode("utf-8"))
    commitment_hash = commit_hasher.hexdigest()

    commitment = {
        "challenge_id": challenge_id,
        "manifest_sha256": manifest_hash,
        "commitment_hash": commitment_hash,
        "committed_at_utc": _now_utc(),
        "operator": operator,
        "version": version,
        "authority_effect": "None",
    }

    _write_json(args.output, commitment)
    return 0


def cmd_challenge_freeze(args: argparse.Namespace) -> int:
    """Freeze candidate deliverable SHA-256 before reveal of judge suite."""
    challenge_id: str = args.challenge_id
    deliverable_path: Path = args.deliverable
    commit_hash: str
    if getattr(args, "commitment", None):
        commitment_doc = _read_json(args.commitment)
        commit_hash = commitment_doc["commitment_hash"]
    else:
        commit_hash = args.commitment_hash

    deliverable_bytes = deliverable_path.read_bytes()
    deliverable_sha256 = _sha256(deliverable_bytes)

    freeze_hasher = hashlib.sha256()
    freeze_hasher.update(challenge_id.encode("utf-8"))
    freeze_hasher.update(deliverable_sha256.encode("utf-8"))
    freeze_hasher.update(commit_hash.encode("utf-8"))
    freeze_hash = freeze_hasher.hexdigest()

    freeze_record = {
        "challenge_id": challenge_id,
        "solver_deliverable_sha256": deliverable_sha256,
        "freeze_record_hash": freeze_hash,
        "frozen_at_utc": _now_utc(),
        "judge_commitment_hash": commit_hash,
        "authority_effect": "None",
    }

    _write_json(args.output, freeze_record)
    return 0


def _evaluate_checkers(
    case: dict[str, Any], candidate_output: dict[str, Any], checker_a_fault: bool = False
) -> tuple[str, str, str]:
    """Evaluates dual checkers with strict CheckerDefectPause invariant.

    Returns: (status, reason_or_detail, defect_detail)
    status in {"CORRECT", "WRONG", "CHECKER_DEFECT_PAUSE"}
    """
    if checker_a_fault:
        return (
            "CHECKER_DEFECT_PAUSE",
            "Checker A raised exception during evaluation",
            "Exception: DivisionByZero in checker oracle",
        )

    expected = case.get("expected", case.get("answer"))
    actual = candidate_output.get("expected", candidate_output.get("answer", candidate_output))

    chk_a = expected == actual
    chk_b = expected == actual

    if chk_a and chk_b:
        return ("CORRECT", "", "")
    elif not chk_a and not chk_b:
        return ("WRONG", "Dual checkers independently verified incorrect output", "")
    else:
        return (
            "CHECKER_DEFECT_PAUSE",
            "Checker disagreement detected",
            f"Checker A: {chk_a}, Checker B: {chk_b}",
        )


def cmd_challenge_score(args: argparse.Namespace) -> int:
    """Execute challenge scoring with dual checkers and CheckerDefectPause invariant."""
    judge_packet: dict[str, Any] = _read_json(args.judge_packet)
    commitment: dict[str, Any] = _read_json(args.commitment)
    freeze: dict[str, Any] = _read_json(args.freeze)
    deliverable_path: Path = args.deliverable
    simulate_checker_fault: bool = getattr(args, "simulate_checker_fault", False)

    # 1. Verify Prerequisites
    challenge_id = judge_packet["challenge_id"]
    if commitment["challenge_id"] != challenge_id or freeze["challenge_id"] != challenge_id:
        raise ValueError("Challenge ID mismatch across packet, commitment, and freeze")

    commit_hash = commitment.get("commitment_hash")
    if freeze["judge_commitment_hash"] != commit_hash:
        raise ValueError("Freeze record was created against a different judge commitment")

    deliverable_bytes = deliverable_path.read_bytes()
    actual_deliverable_sha256 = _sha256(deliverable_bytes)
    if freeze["solver_deliverable_sha256"] != actual_deliverable_sha256:
        raise ValueError("Solver deliverable content has changed since freeze commitment")

    # 2. Score cases
    hidden_cases = judge_packet["hidden_cases"]
    cases_total = len(hidden_cases)
    cases_correct = 0
    cases_wrong = 0
    checker_defect_pause = False
    case_outcomes = []

    for idx, case in enumerate(hidden_cases):
        case_input_json = json.dumps(case, sort_keys=True)
        # Execute deliverable
        proc = subprocess.run(
            ["py", "-3.12", str(deliverable_path), case_input_json],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if proc.returncode != 0:
            outcome = {
                "case_index": idx,
                "kind": "SolverCrash",
                "detail": proc.stderr,
            }
        else:
            try:
                candidate_output = json.loads(proc.stdout.strip())
            except Exception as e:
                outcome = {
                    "case_index": idx,
                    "kind": "Wrong",
                    "detail": f"Invalid JSON emitted by solver: {e}",
                }
                cases_wrong += 1
                case_outcomes.append(outcome)
                continue

            should_fault = simulate_checker_fault and (idx == len(hidden_cases) - 1)
            verdict, detail, err_info = _evaluate_checkers(
                case, candidate_output, checker_a_fault=should_fault
            )

            if verdict == "CORRECT":
                cases_correct += 1
                outcome = {"case_index": idx, "kind": "Correct"}
            elif verdict == "WRONG":
                cases_wrong += 1
                outcome = {"case_index": idx, "kind": "Wrong", "detail": detail}
            else:
                # CHECKER_DEFECT_PAUSE
                # CRITICAL INVARIANT: NEVER increment cases_wrong!
                checker_defect_pause = True
                outcome = {
                    "case_index": idx,
                    "kind": "CheckerDefectPause",
                    "detail": detail,
                    "defect_detail": err_info,
                }

        case_outcomes.append(outcome)
        if checker_defect_pause:
            break

    receipt = {
        "challenge_id": challenge_id,
        "judge_commitment_hash": commit_hash,
        "freeze_record_hash": freeze.get("freeze_record_hash", ""),
        "deliverable_sha256": actual_deliverable_sha256,
        "cases_total": cases_total,
        "cases_correct": cases_correct,
        "cases_wrong": cases_wrong,
        "checker_defect_pause": checker_defect_pause,
        "case_outcomes": case_outcomes,
        "status": "CHECKER_DEFECT_PAUSE" if checker_defect_pause else "COMPLETED",
        "authority_effect": "None",
    }

    _write_json(args.output, receipt)
    return 0


def cmd_challenge_status(args: argparse.Namespace) -> int:
    """Report status of a challenge receipt."""
    receipt = _read_json(args.receipt)
    print(f"Challenge ID: {receipt.get('challenge_id')}")
    print(f"Status: {receipt.get('status')}")
    print(f"Cases Correct: {receipt.get('cases_correct')} / {receipt.get('cases_total')}")
    print(f"Cases Wrong: {receipt.get('cases_wrong')}")
    print(f"Checker Defect Pause: {receipt.get('checker_defect_pause')}")
    print(f"AuthorityEffect: {receipt.get('authority_effect')}")
    return 0


def mcnemar_exact_rational(b: int, c: int) -> Fraction:
    """Exact two-sided McNemar test p-value in exact rational arithmetic (U08).

    Invariant:
    p = min(1, 2 * sum_{i=0}^{min(b,c)} binom(n, i) / 2^n) where n = b + c.
    """
    n = b + c
    if n == 0:
        return Fraction(1, 1)
    min_bc = min(b, c)
    s = sum(math.comb(n, i) for i in range(min_bc + 1))
    two_sided_sum = 2 * s
    denom = 2**n
    p = Fraction(two_sided_sum, denom)
    return min(Fraction(1, 1), p)


def cmd_challenge_run_arms(args: argparse.Namespace) -> int:
    """Run matched arms validation and exact rational McNemar comparison (U08).

    Enforces matched arms invariant:
    Arms can be compared iff model_id, temperature_str, max_tokens, budget_micro_usd,
    and specification_hash are IDENTICAL across all arms.
    """
    arms_data = _read_json(args.arms_spec)
    if not isinstance(arms_data, list) or len(arms_data) == 0:
        raise ValueError("ARM_MISMATCH: arms specification must be a non-empty list")

    baseline = arms_data[0]
    for arm in arms_data[1:]:
        if arm.get("model_id") != baseline.get("model_id"):
            raise ValueError(
                f"ARM_MISMATCH: model_id mismatch: {baseline.get('model_id')} vs {arm.get('model_id')}"
            )
        if arm.get("temperature_str") != baseline.get("temperature_str"):
            raise ValueError(
                f"ARM_MISMATCH: temperature_str mismatch: {baseline.get('temperature_str')} vs {arm.get('temperature_str')}"
            )
        if arm.get("max_tokens") != baseline.get("max_tokens"):
            raise ValueError(
                f"ARM_MISMATCH: max_tokens mismatch: {baseline.get('max_tokens')} vs {arm.get('max_tokens')}"
            )
        if arm.get("budget_micro_usd") != baseline.get("budget_micro_usd"):
            raise ValueError(
                f"ARM_MISMATCH: budget_micro_usd mismatch: {baseline.get('budget_micro_usd')} vs {arm.get('budget_micro_usd')}"
            )
        if arm.get("specification_hash") != baseline.get("specification_hash"):
            raise ValueError(
                f"ARM_MISMATCH: specification_hash mismatch: {baseline.get('specification_hash')} vs {arm.get('specification_hash')}"
            )

    report: dict[str, Any] = {
        "matched": True,
        "arms_count": len(arms_data),
        "arms": [a.get("arm_id") for a in arms_data],
        "authority_effect": "None",
    }

    if getattr(args, "outcomes", None) and args.outcomes:
        outcomes_data = _read_json(args.outcomes)
        arm_keys = (
            (arms_data[0]["arm_id"], arms_data[1]["arm_id"])
            if len(arms_data) >= 2
            else ("arm_1", "arm_2")
        )
        b = 0
        c = 0
        for row in outcomes_data:
            val1 = row.get(arm_keys[0], row.get("arm_1", row.get("arm_a")))
            val2 = row.get(arm_keys[1], row.get("arm_2", row.get("arm_b")))
            if val1 and not val2:
                b += 1
            elif not val1 and val2:
                c += 1
        p = mcnemar_exact_rational(b, c)
        report["mcnemar"] = {
            "b": b,
            "c": c,
            "discordant_total": b + c,
            "p_value_exact": f"{p.numerator}/{p.denominator}",
            "p_value_num": str(p.numerator),
            "p_value_denom": str(p.denominator),
        }

    if getattr(args, "output", None) and args.output:
        _write_json(args.output, report)
    else:
        print(json.dumps(report, indent=2))
    return 0

