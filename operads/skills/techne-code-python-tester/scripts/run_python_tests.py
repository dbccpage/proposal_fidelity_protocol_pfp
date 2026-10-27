#!/usr/bin/env python3
"""Run Python tests with mechanical AST pre-filtering and structured receipt generation.

Produces a machine-readable PythonTestReceipt (schema: core.python_test_receipt.v1).
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
QUALITY_GATE_SCRIPT = SCRIPT_DIR / "test_quality_gate.py"


def get_pytest_version() -> str:
    try:
        import pytest

        return getattr(pytest, "__version__", "unknown")
    except ImportError:
        return "not_installed"


def run_collection(target_paths: List[str]) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q"] + target_paths
    proc = subprocess.run(cmd, capture_output=True, text=True)
    status = "PASS" if proc.returncode == 0 else "FAIL"
    if proc.returncode != 0 and (
        "ModuleNotFoundError" in proc.stderr or "ImportError" in proc.stderr
    ):
        status = "BLOCKED"
    return {
        "status": status,
        "command": " ".join(cmd),
        "exit": proc.returncode,
        "output": (proc.stdout + proc.stderr).strip()[-500:],
    }


def run_quality_gate(target_paths: List[str]) -> Dict[str, Any]:
    cmd = [sys.executable, str(QUALITY_GATE_SCRIPT)] + target_paths + ["--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        gate_data = json.loads(proc.stdout)
        findings = gate_data.get("findings", [])
        files_scanned = gate_data.get("files_scanned", 0)
    except (ValueError, AttributeError):
        # No parseable JSON on stdout (gate crashed, or emitted a non-object).
        # Report that as a finding rather than as zero findings.
        findings = [{"path": "unknown", "line": 0, "code": "GATE_ERROR", "detail": proc.stderr}]
        files_scanned = 0

    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "files_scanned": files_scanned,
        "findings": findings,
    }


def run_focused_tests(target_paths: List[str], extra_args: List[str]) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "pytest", "-v"] + target_paths + extra_args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    summary_line = "No tests executed"
    for line in proc.stdout.splitlines()[::-1]:
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line.strip()
            break
    return {
        "command": " ".join(cmd),
        "exit": proc.returncode,
        "summary": summary_line,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def generate_receipt(target_paths: List[str], extra_args: List[str]) -> Dict[str, Any]:
    pytest_ver = get_pytest_version()
    collection_res = run_collection(target_paths)
    gate_res = run_quality_gate(target_paths)
    focused_res = run_focused_tests(target_paths, extra_args)

    receipt = {
        "schema": "core.python_test_receipt.v1",
        "interpreter": sys.executable,
        "pytest_version": pytest_ver,
        "collection": {
            "status": collection_res["status"],
            "command": collection_res["command"],
            "exit": collection_res["exit"],
        },
        "quality_gate": {
            "status": gate_res["status"],
            "files_scanned": gate_res["files_scanned"],
            "findings": gate_res["findings"],
        },
        "focused_run": {
            "command": focused_res["command"],
            "exit": focused_res["exit"],
            "summary": focused_res["summary"],
        },
        "coverage": {
            "status": "UNAVAILABLE",
            "tool": "pytest-cov (not configured for one-shot receipt)",
        },
        "mutation_check": {
            "status": "NOT_PERFORMED",
            "detail": "Dynamic mutation testing is managed by the Builder step 5",
        },
        "authority_effect": "None",
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Test paths to run")
    parser.add_argument("--json", action="store_true", help="Print JSON receipt to stdout")
    parser.add_argument("--out", type=Path, help="Save receipt JSON to file")
    args, unknown = parser.parse_known_args()

    receipt = generate_receipt(args.paths, unknown)

    if args.out:
        args.out.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(f"Receipt written to {args.out}")

    if args.json or not args.out:
        print(json.dumps(receipt, indent=2))

    # Exit code: non-zero if quality gate or tests failed
    if receipt["quality_gate"]["status"] != "PASS" or receipt["focused_run"]["exit"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
