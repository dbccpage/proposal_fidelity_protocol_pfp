"""Run the PFP Paper 003 package demonstrations offline.

1. Package demonstration 1: host phases, fuel, and atomic rollback.
2. Package demonstration 2: the two-signal decision table.
3. Package demonstration 3: the four candidate phrase detectors.
4. The candidate-response audit, offline (no network request).

Run from the package root: ``py -3.12 code/run_demos.py``. The exit status is
nonzero if any demonstration check fails.
"""

from __future__ import annotations

import json
import sys
import traceback

from demo1_host_transactions import run_demo as run_demo_1
from demo2_two_signal_gate import run_demo as run_demo_2
from demo3_canaries_audit import run_demo as run_demo_3
from live_proposer_demo import run_demo as run_demo_live


def main() -> int:
    print("\n" + "#" * 70)
    print("PFP PAPER 003 PACKAGE DEMONSTRATIONS (offline)")
    print("#" * 70 + "\n")

    results = {}
    try:
        results["demo1"] = run_demo_1()
        print("\n")
        results["demo2"] = run_demo_2()
        print("\n")
        results["demo3"] = run_demo_3()
        print("\n")
        results["candidate_response_audit"] = run_demo_live(live=False)
    except Exception as err:
        print(f"\n[ERROR] Demonstration failed: {err}", file=sys.stderr)
        traceback.print_exc()
        return 1

    if any(result.get("status") != "PASSED" for result in results.values()):
        print("\n[ERROR] A demonstration did not report PASSED.", file=sys.stderr)
        return 1
    print("\n" + "#" * 70)
    print("ALL PACKAGE DEMONSTRATIONS PASSED.")
    print("#" * 70)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
