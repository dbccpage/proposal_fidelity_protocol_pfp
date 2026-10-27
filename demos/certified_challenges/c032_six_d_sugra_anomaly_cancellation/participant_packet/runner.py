"""Participant Packet Runner for C032 (Six-Dimensional Supergravity Anomaly Cancellation).

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
    parser = argparse.ArgumentParser(description="C032 Participant Packet Runner")
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
    else:
        print(f"ERROR: Cases path does not exist: {args.cases}", file=sys.stderr)
        return 1

    results: list[dict[str, Any]] = []
    for cf in case_files:
        try:
            case_data = json.loads(cf.read_text(encoding="utf-8"))
            res = solve_fn(case_data)
            results.append(res)
        except Exception as e:
            results.append(
                {
                    "id": cf.stem,
                    "status": "UNKNOWN",
                    "refusal_code": "MALFORMED_CASE_STRUCTURE",
                    "error": str(e),
                }
            )

    output_str = canonical_json_dump(results if len(results) > 1 else results[0])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_str + "\n", encoding="utf-8")
        print(f"Results written to {args.output}")
    else:
        print(output_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
