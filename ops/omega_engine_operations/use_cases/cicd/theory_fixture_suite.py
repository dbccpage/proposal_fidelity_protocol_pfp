#!/usr/bin/env python3
"""Run the theory fixture suite across the cross-language boundary.

Part of release gate G2, G3 and Local CI gate theory_fixture_suite_v1.
Runs:
1. gate11-self (PR 1, Symbol Game K0 survivor and chain law)
2. CODA Lean-table cases through coda_evaluate (PR 4)
3. LGGR I phone test through lggr_classify (PR 7)

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from omega_engine_operating_system.adapters.rust_host.ffi import (
    RustSymbolGameHost,
)

if __package__ in (None, ""):
    from host_tools import ensure_symbol_game_host
else:
    from .host_tools import ensure_symbol_game_host


def run_gate11_self() -> tuple[bool, str]:
    """Execute gate11-self via the Symbol Game CLI."""
    cmd = [
        sys.executable,
        "-m",
        "omega_engine_pfp.entrypoints.cli.symbol_game",
        "gate11-self",
    ]
    proc = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        return False, f"gate11-self exited {proc.returncode}:\n{proc.stderr}"
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return False, f"gate11-self output is not valid JSON: {exc}\n{proc.stdout}"

    if not data.get("overall_passed"):
        return False, f"gate11-self failed: {data}"
    return True, "gate11-self PASS"


def _coda_runtime_ok(res: object) -> bool:
    return bool(res.is_ok and res.value["success"])


def _coda_case_1(result: dict) -> bool:
    # 1. Authorized ExactRepair
    return result.get("diagnostic") == "ExactRepair" and result.get("routing") == "CheckPassed"


def _coda_case_2(result: dict) -> bool:
    # 2. Firewalled Unlicensed ExactRepair (GTLA-T9)
    refused = result.get("authority", {}).get("Refused")
    return result.get("diagnostic") == "ExactRepair" and refused == "Refusal"


def _coda_case_3(result: dict) -> bool:
    # 3. ClosedResidual Anomalon
    return result.get("diagnostic") == "ClosedResidual" and result.get("routing") == "Repair"


def _coda_case_4(result: dict) -> bool:
    # 4. Sieve Empty Refusal
    refused = result.get("authority", {}).get("Refused")
    return result.get("routing") == "NoRule" and refused == "Refusal"


def _coda_case_5(result: dict) -> bool:
    # 5. Refinement Failure
    return result.get("routing") == "Repair"


def _coda_case_6(result: dict) -> bool:
    # 6. Gluing Failure
    return result.get("routing") == "Repair"


def _coda_case(host: RustSymbolGameHost, number: int, payload: dict, matches) -> tuple[bool, str] | None:
    res = host.invoke_runtime("coda_evaluate", payload)
    if not _coda_runtime_ok(res):
        return False, f"coda_evaluate case {number} failed: {res}"
    result = res.value["result"]
    if not matches(result):
        return False, f"coda_evaluate case {number} unexpected result: {result}"
    return None


def run_coda_lean_table_cases(host: RustSymbolGameHost) -> tuple[bool, str]:
    """Execute the 6 CODA Lean-table cases through native coda_evaluate."""
    base_payload = {
        "input_id": "coda_fixture_test",
        "sieve_non_empty": True,
        "refinement_consistent": True,
        "gluing_succeeded": True,
        "phi1_distance": 0,
        "gamma2_distance": 0,
        "license_granted": True,
    }
    cases = (
        (1, dict(base_payload), _coda_case_1),
        (2, dict(base_payload, license_granted=False), _coda_case_2),
        (3, dict(base_payload, phi1_distance=3, license_granted=False), _coda_case_3),
        (4, dict(base_payload, sieve_non_empty=False), _coda_case_4),
        (5, dict(base_payload, refinement_consistent=False), _coda_case_5),
        (6, dict(base_payload, gluing_succeeded=False), _coda_case_6),
    )
    for number, payload, matches in cases:
        failure = _coda_case(host, number, payload, matches)
        if failure is not None:
            return failure
    return True, "coda_evaluate 6 Lean-table cases PASS"


def run_lggr_classify_cases(host: RustSymbolGameHost) -> tuple[bool, str]:
    """Execute the LGGR I phone test cases through native lggr_classify."""
    # 1. Negative gluing defect (Local Green, Global Red): e1=true, e2=true, eg=false -> delta_eval = -1
    res1 = host.invoke_runtime("lggr_classify", {"e1": True, "e2": True, "eg": False})
    if not res1.is_ok or not res1.value["success"]:
        return False, f"lggr_classify case 1 failed: {res1}"
    val1 = res1.value["result"]
    if val1.get("delta_eval") != -1 or val1.get("defect_class") != "NegativeGluingDefect":
        return False, f"lggr_classify case 1 mismatch: {val1}"

    # 2. Positive gluing defect: e1=false, e2=true, eg=true -> delta_eval = 1
    res2 = host.invoke_runtime("lggr_classify", {"e1": False, "e2": True, "eg": True})
    if not res2.is_ok or not res2.value["success"]:
        return False, f"lggr_classify case 2 failed: {res2}"
    val2 = res2.value["result"]
    if val2.get("delta_eval") != 1 or val2.get("defect_class") != "PositiveGluingDefect":
        return False, f"lggr_classify case 2 mismatch: {val2}"

    # 3. Zero defect (Concordant): e1=true, e2=true, eg=true -> delta_eval = 0
    res3 = host.invoke_runtime("lggr_classify", {"e1": True, "e2": True, "eg": True})
    if not res3.is_ok or not res3.value["success"]:
        return False, f"lggr_classify case 3 failed: {res3}"
    val3 = res3.value["result"]
    if val3.get("delta_eval") != 0 or val3.get("defect_class") != "ZeroDefect":
        return False, f"lggr_classify case 3 mismatch: {val3}"

    return True, "lggr_classify LGGR I phone test PASS"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    _ = parser.parse_args(argv)

    binary = ensure_symbol_game_host(REPO_ROOT)
    if binary is None:
        print("theory_fixture_suite: FAIL (could not build omega_symbol_game)")
        return 1
    os.environ["OMEGA_SYMBOL_GAME_HOST"] = str(binary)

    host = RustSymbolGameHost(binary=binary)

    ok1, msg1 = run_gate11_self()
    print(f"[{'PASS' if ok1 else 'FAIL'}] {msg1}")
    if not ok1:
        return 1

    ok2, msg2 = run_coda_lean_table_cases(host)
    print(f"[{'PASS' if ok2 else 'FAIL'}] {msg2}")
    if not ok2:
        return 1

    ok3, msg3 = run_lggr_classify_cases(host)
    print(f"[{'PASS' if ok3 else 'FAIL'}] {msg3}")
    if not ok3:
        return 1

    print("theory_fixture_suite: PASS (all theory fixtures verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
