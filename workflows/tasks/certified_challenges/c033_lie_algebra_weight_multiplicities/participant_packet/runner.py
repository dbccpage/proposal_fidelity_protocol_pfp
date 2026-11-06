"""Participant Packet Runner for C033 (Lie Algebra Weight Multiplicities).

CLI tool to execute candidate solver against case files, emitting RFC 8785 canonical JSON.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

# Ensure repository root is on sys.path
REPO_ROOT = next(p for p in Path(__file__).resolve().parents if p.name == "certified_challenges")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def canonical_json_dump(obj: Any) -> str:
    """Serializes obj to RFC 8785 canonical JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_solver(solver_path: Path) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Dynamically imports solve function from specified solver path."""
    if not solver_path.is_file():
        raise FileNotFoundError(f"Solver file not found: {solver_path}")

    spec = importlib.util.spec_from_file_location("candidate_solver", solver_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec from {solver_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate_solver"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "solve"):
        raise AttributeError(f"Module {solver_path} does not expose 'solve' function")

    return getattr(module, "solve")


def main() -> int:
    parser = argparse.ArgumentParser(description="C033 Participant Packet Runner")
    parser.add_argument(
        "--cases", type=Path, required=True, help="Path to input case JSON or directory"
    )
    parser.add_argument("--solver", type=Path, required=True, help="Path to solver.py")
    parser.add_argument("--output", type=Path, required=False, help="Path to output results file")
    args = parser.parse_args()

    solve_fn = load_solver(args.solver)

    case_files: list[Path] = []
    if args.cases.is_file():
        case_files = [args.cases]
    elif args.cases.is_dir():
        case_files = sorted(args.cases.glob("*.json"))

    if not case_files:
        print(f"No case files found at: {args.cases}", file=sys.stderr)
        return 1

    results = []
    for cf in case_files:
        data = json.loads(cf.read_text(encoding="utf-8"))
        case_payload = data.get("input", data)
        res = solve_fn(case_payload)
        results.append(res)
        print(f"[{res.get('status', 'ERROR')}] {cf.name} -> dim={res.get('dimension', 'N/A')}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json_dump(results) + "\n", encoding="utf-8")
        print(f"Results written to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
