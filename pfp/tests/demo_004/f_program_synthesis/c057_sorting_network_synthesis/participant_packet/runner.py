#!/usr/bin/env python3
"""
Test runner for C057: Sorting Network Synthesis participant packet.
"""

import json
import sys
from pathlib import Path


def verify_01(n: int, network: list) -> tuple:
    """Run bit-parallel 0-1 verification."""
    num_cases = 1 << n
    mask = (1 << num_cases) - 1
    w = [0] * n
    for c in range(n):
        val = 0
        for m in range(num_cases):
            if (m >> c) & 1:
                val |= 1 << m
        w[c] = val

    for i, j in network:
        wi, wj = w[i], w[j]
        w[i] = wi & wj
        w[j] = wi | wj

    for c in range(n - 1):
        unsorted = (w[c] & ~w[c + 1]) & mask
        if unsorted:
            failing_m = (unsorted & -unsorted).bit_length() - 1
            return False, failing_m

    return True, None


def main():
    examples_dir = Path(__file__).parent / "examples"
    example_files = sorted(examples_dir.glob("*.json"))

    if not example_files:
        print("No example files found.")
        sys.exit(1)

    print(f"Running C057 verification on {len(example_files)} examples...")
    passed = 0
    for ex_path in example_files:
        with open(ex_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inp = data["input"]
        exp = data["expected_output"]

        status = exp.get("status")
        if status == "SOLVED":
            net = exp.get("network", [])
            valid, failing = verify_01(inp["n"], net)
            if not valid:
                print(f"[-] {ex_path.name}: 0-1 principle failed on input {failing}")
                continue
            if len(net) > inp["k"]:
                print(f"[-] {ex_path.name}: Network length {len(net)} > bound {inp['k']}")
                continue
        print(f"[+] {ex_path.name}: PASSED (status: {status})")
        passed += 1

    print(f"\nResult: {passed}/{len(example_files)} examples verified successfully.")
    sys.exit(0 if passed == len(example_files) else 1)


if __name__ == "__main__":
    main()
