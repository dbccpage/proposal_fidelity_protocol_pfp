"""CLI Driver for Challenge C040 (M-Theory Toroidal Reduction & Cremmer-Julia Scalar Count).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def canonical_json(data: Any) -> str:
    """Formats data into RFC 8785 canonical JSON string."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_solver_func(solver_path: Path):
    if not solver_path.is_file():
        raise FileNotFoundError(f"Solver file not found: {solver_path}")
    solver_dir = str(solver_path.resolve().parent)
    if solver_dir not in sys.path:
        sys.path.insert(0, solver_dir)
    spec = importlib.util.spec_from_file_location("c040_solver_module", solver_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec from {solver_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "solve"):
        raise AttributeError("Solver module must expose a 'solve(case: dict) -> dict' function")
    return module.solve


def main() -> int:
    parser = argparse.ArgumentParser(description="Challenge C040 Participant Runner")
    parser.add_argument(
        "--cases", required=True, help="Path to single case JSON or directory of cases"
    )
    parser.add_argument("--solver", required=True, help="Path to Python solver script")
    parser.add_argument("--output", help="Optional output path for JSON results")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    solver_path = Path(args.solver)
    if not cases_path.exists():
        print(f"Error: Cases path not found: {cases_path}", file=sys.stderr)
        return 1

    try:
        solve_fn = load_solver_func(solver_path)
    except Exception as exc:
        print(f"Error loading solver: {exc}", file=sys.stderr)
        return 1

    case_files: list[Path] = []
    if cases_path.is_file():
        case_files = [cases_path]
    elif cases_path.is_dir():
        case_files = sorted(cases_path.glob("*.json"), key=lambda p: p.name.encode("utf-8"))

    results = []
    for cf in case_files:
        try:
            case_data = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve_fn(case_data)
            results.append(ans)
        except Exception as exc:
            print(f"Error executing solver on {cf.name}: {exc}", file=sys.stderr)
            return 1

    output_str = canonical_json(results if len(case_files) > 1 else results[0]) if results else "[]"
    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(output_str + "\n", encoding="utf-8")
    else:
        print(output_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
