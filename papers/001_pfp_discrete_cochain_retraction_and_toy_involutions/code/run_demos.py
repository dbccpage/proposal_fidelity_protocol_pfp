"""Master Demo Runner for PFP Paper 001.

Runs the paper demonstrations in sequence:
  Demo 1: Manuscript graph-repair witnesses (demo1_holonomy.py)
  Demo 2: Certificate-gate fixtures for signed toy pairings (demo2_bqnf_fsign.py)
  Demo 3: Adversarial debate trace replay (offline) or a live OpenRouter run
  Rust tests: native cargo tests, only when --rust is given

Any failed expectation, refused configuration or unavailable requested tool
ends the run with a nonzero exit status.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
PAPER_DIR = CODE_DIR.parent
RUST_DIR = CODE_DIR / "rust"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))


def run_demo_1() -> bool:
    print("\n" + "#" * 70)
    print("# RUNNING DEMO 1: MANUSCRIPT GRAPH-REPAIR WITNESSES")
    print("#" * 70)
    from demo1_holonomy import run_demo1
    return run_demo1()


def run_demo_2() -> bool:
    print("\n" + "#" * 70)
    print("# RUNNING DEMO 2: CERTIFICATE-GATE FIXTURES")
    print("#" * 70)
    from demo2_bqnf_fsign import run_demo2
    return run_demo2()


def run_demo_3(live: bool, lattice: str, u_val: float | None, output_dir: Path | None, env_file: Path | None) -> bool:
    print("\n" + "#" * 70)
    if live:
        print("# RUNNING DEMO 3: LIVE ADVERSARIAL DEBATE (OPENROUTER)")
    else:
        print("# RUNNING DEMO 3: OFFLINE DEBATE REPLAY (HISTORICAL TRACE)")
    print("#" * 70)
    if live:
        from live_adversarial_demo import LATTICES, U_SWEEP, LiveConfigurationError, run_live_debate
        lattices = [lattice] if lattice != "both" else list(LATTICES.keys())
        u_vals = [u_val] if u_val is not None else U_SWEEP
        try:
            run_live_debate(output_dir=output_dir, lattice_keys=lattices, u_values=u_vals, env_file=env_file)
        except LiveConfigurationError as error:
            print(f"REFUSED: {error.code}: {error}")
            return False
        except RuntimeError as error:
            print(f"FAILED: {error}")
            return False
        return True
    from run_adversarial_debate_benchmark import run_benchmark
    run_benchmark()
    return True


def run_rust_tests() -> bool:
    print("\n" + "#" * 70)
    print("# RUNNING SELF-CONTAINED RUST SOLVER TESTS")
    print("#" * 70)
    if shutil.which("cargo") is None:
        print("FAILED: --rust was requested but 'cargo' is not on PATH.")
        return False
    result = subprocess.run(["cargo", "test", "-j", "1"], cwd=str(RUST_DIR), check=False)
    if result.returncode != 0:
        print(f"FAILED: Rust crate tests exited with code {result.returncode}.")
        return False
    print("Rust crate tests passed.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--demo", choices=["1", "2", "3", "all"], default="all", help="Which demo to run (default: all)")
    parser.add_argument("--all", action="store_true", help="Run all demonstrations")
    parser.add_argument("--live", action="store_true", help="Run Demo 3 live against OpenRouter (requires OPENROUTER_API_KEY)")
    parser.add_argument("--output-dir", type=Path, help="New directory for the live trace and receipt (required with --live)")
    parser.add_argument("--env-file", type=Path, help="File containing OPENROUTER_API_KEY=... (environment is read first)")
    parser.add_argument("--lattice", choices=["c5_pentagon", "kagome_cluster", "both"], default="both")
    parser.add_argument("--u", type=float, help="Specific U/t value for the live demo")
    parser.add_argument("--rust", action="store_true", help="Run cargo tests for the self-contained Rust solver")
    args = parser.parse_args()
    if args.all:
        args.demo = "all"

    print("=" * 70)
    print("PFP PAPER 001: REPRODUCIBLE DEMO SUITE")
    print("=" * 70)

    outcomes: dict[str, bool] = {}
    if args.rust:
        outcomes["rust"] = run_rust_tests()
    if args.demo in ("1", "all"):
        outcomes["demo1"] = run_demo_1()
    if args.demo in ("2", "all"):
        outcomes["demo2"] = run_demo_2()
    if args.demo in ("3", "all"):
        outcomes["demo3"] = run_demo_3(args.live, args.lattice, args.u, args.output_dir, args.env_file)

    print("\n" + "=" * 70)
    failed = [name for name, ok in outcomes.items() if not ok]
    if failed:
        print(f"DEMO SUITE FAILED: {', '.join(failed)}")
        print("=" * 70)
        return 1
    print(f"ALL REQUESTED DEMOS PASSED: {', '.join(outcomes)}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
