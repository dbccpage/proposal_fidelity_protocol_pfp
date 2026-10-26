"""Participant runner for C049: Universal Constructions in Finite Categories.
Executes participant solver against the 12 public examples.
"""

import glob
import json
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = str(next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from omega_engine_pfp.tests.demo_004.e_formal_math.c049_finite_category_universal_constructions.reference_solver import (
    solve,
)


def main():
    examples_dir = os.path.join(SCRIPT_DIR, "examples")
    files = sorted(glob.glob(os.path.join(examples_dir, "*.json")))
    if not files:
        print(f"Error: no example files found in {examples_dir}")
        sys.exit(1)

    print(f"Running C049 Participant Runner across {len(files)} public examples...")
    passed = 0
    t0 = time.time()

    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data["input"]
        expected = data["expected"]
        case_id = inp.get("case_id")

        actual = solve(inp)

        status_ok = actual.get("status") == expected.get("status")
        kind_ok = actual.get("kind") == expected.get("kind")

        ok = status_ok and kind_ok
        if actual.get("status") == "SOLVED" and actual.get("kind") == "EXISTS":
            if actual.get("apex") != expected.get("apex"):
                ok = False
        elif actual.get("status") == "OUT_OF_SCOPE":
            if actual.get("witness", {}).get("reason") != expected.get("witness", {}).get("reason"):
                ok = False

        if ok:
            passed += 1
            print(
                f"  [PASS] {case_id} (status: {actual.get('status')}, kind: {actual.get('kind')})"
            )
        else:
            print(f"  [FAIL] {case_id}")
            print(f"         Expected: {expected}")
            print(f"         Actual:   {actual}")

    dt = time.time() - t0
    print(f"\nResult: {passed}/{len(files)} passed in {dt:.3f}s")
    if passed == len(files):
        print("ALL PUBLIC EXAMPLES PASSED.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
