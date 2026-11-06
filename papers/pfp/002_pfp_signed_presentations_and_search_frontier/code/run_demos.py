#!/usr/bin/env python3
"""Unified Demo Runner for PFP Paper 002.

Runs self-contained demos demonstrating:
  Demo 1: Exact Z2 sign-gauge classification and odd-cycle obstruction (Rust & Python)
  Demo 2: Bounded frontier search and SHA-256 receipt replay chain
  Demo 3: 64-state exact Fock space path-weight gap on triangular Hubbard plaquette
  Live:   Optional OpenRouter proposer audited by the exact local checker
          (needs your own key; see .env.example)

Usage (from the package root):
  py -3.12 code/run_demos.py --all
  py -3.12 code/run_demos.py --demo 1
  py -3.12 code/run_demos.py --demo 2
  py -3.12 code/run_demos.py --demo 3
  py -3.12 code/run_demos.py --live --env-file .env
  py -3.12 code/run_demos.py --rust
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_code_dir = Path(__file__).resolve().parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

import demo1_signed_gauge  # noqa: E402
import demo2_frontier_search  # noqa: E402
import demo3_fock_obstruction  # noqa: E402
import live_proposer_demo  # noqa: E402
from native_sign_graph import find_binary  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="PFP Paper 002 Unified Demo Runner")
    parser.add_argument("--all", action="store_true", help="Run demos 1, 2, and 3")
    parser.add_argument("--demo", type=int, choices=[1, 2, 3], help="Run a specific demo (1, 2, or 3)")
    parser.add_argument("--live", action="store_true", help="Run live OpenRouter LLM proposer demo")
    parser.add_argument("--rust", action="store_true", help="Check native Rust solver binary status")
    parser.add_argument("--model", default="meta-llama/llama-3.1-8b-instruct", help="OpenRouter model for live demo")
    parser.add_argument("--env-file", type=Path, help="File containing OPENROUTER_API_KEY=... (environment is read first)")

    args = parser.parse_args()

    if args.rust:
        bin_path = find_binary()
        print("=" * 72)
        print("NATIVE RUST SOLVER STATUS")
        print("=" * 72)
        if bin_path:
            print(f"[+] Found native executable: {bin_path}")
        else:
            print("[-] Native binary not found. Build with:")
            print("    cargo build -j 1 --manifest-path code/rust/Cargo.toml --bin solve_sign_graph")
        return

    if args.live:
        if not live_proposer_demo.run_live_demo(model=args.model, env_file=args.env_file):
            print("\n[!] Live demo failed or proposal rejected!")
            sys.exit(1)
        return

    if args.demo == 1:
        if not demo1_signed_gauge.run_demo():
            print("\n[!] Demo 1 failed!")
            sys.exit(1)
        return

    if args.demo == 2:
        if not demo2_frontier_search.run_demo():
            print("\n[!] Demo 2 failed!")
            sys.exit(1)
        return

    if args.demo == 3:
        if not demo3_fock_obstruction.run_demo():
            print("\n[!] Demo 3 failed!")
            sys.exit(1)
        return

    # Default or --all: run demos 1, 2, 3
    print("Running all Paper 002 core verification demos...\n")
    if not demo1_signed_gauge.run_demo():
        print("\n[!] Demo 1 failed!")
        sys.exit(1)
    print("\n")
    if not demo2_frontier_search.run_demo():
        print("\n[!] Demo 2 failed!")
        sys.exit(1)
    print("\n")
    if not demo3_fock_obstruction.run_demo():
        print("\n[!] Demo 3 failed!")
        sys.exit(1)
    print("\n" + "=" * 72)
    print("ALL CORE DEMOS COMPLETED SUCCESSFULLY")
    print("=" * 72)


if __name__ == "__main__":
    main()
