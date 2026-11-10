"""Sandboxed Participant Runner for C012 (Cellular Sheaf Cohomology H^0 and H^1).

Invokes solve(case: dict) -> dict on benchmark/example cases in an isolated
environment and writes responses to answers.jsonl in RFC 8785 canonical JSON format.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable


def canonical_json_str(obj: Any) -> str:
    """Serializes obj to canonical RFC 8785 JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_solver_func(
    solver_spec: str | Path | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Loads solve function from file path, module spec, or default reference solver."""
    if solver_spec is None:
        candidate = Path(__file__).resolve().parent.parent / "reference_solver" / "solver.py"
        if candidate.is_file():
            solver_spec = candidate
        else:
            solver_spec = "reference_solver.solver"

    if isinstance(solver_spec, Path) or (
        isinstance(solver_spec, str)
        and (solver_spec.endswith(".py") or os.sep in solver_spec or "/" in solver_spec)
    ):
        solver_path = Path(solver_spec).resolve()
        if not solver_path.is_file():
            raise FileNotFoundError(f"Solver file not found: {solver_path}")
        parent_dir = str(solver_path.parent)
        grandparent_dir = str(solver_path.parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        if grandparent_dir not in sys.path:
            sys.path.insert(0, grandparent_dir)
        spec = importlib.util.spec_from_file_location("c012_custom_solver", solver_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load solver spec from {solver_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "solve"):
            raise AttributeError(
                f"Module {solver_path} does not export 'solve(case: dict) -> dict'"
            )
        return getattr(mod, "solve")
    else:
        mod_name = str(solver_spec)
        if ":" in mod_name:
            mod_part, func_name = mod_name.split(":", 1)
        else:
            mod_part, func_name = mod_name, "solve"

        root_dir = str(Path(__file__).resolve().parent.parent)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        mod = importlib.import_module(mod_part)
        return getattr(mod, func_name)


def load_cases(cases_path: Path) -> list[dict[str, Any]]:
    """Loads cases from a directory of JSON files, a single JSON, or a JSONL file."""
    if not cases_path.exists():
        raise FileNotFoundError(f"Cases path does not exist: {cases_path}")

    cases: list[dict[str, Any]] = []

    if cases_path.is_dir():
        for json_file in sorted(cases_path.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "input" in data:
                    cases.append(data["input"])
                elif isinstance(data, dict):
                    cases.append(data)
    elif cases_path.suffix == ".jsonl":
        with open(cases_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                data = json.loads(line_str)
                if isinstance(data, dict) and "input" in data:
                    cases.append(data["input"])
                elif isinstance(data, dict):
                    cases.append(data)
    else:
        with open(cases_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "input" in item:
                        cases.append(item["input"])
                    elif isinstance(item, dict):
                        cases.append(item)
            elif isinstance(data, dict) and "input" in data:
                cases.append(data["input"])
            elif isinstance(data, dict):
                cases.append(data)

    return cases


def run_cases(
    solve_fn: Callable[[dict[str, Any]], dict[str, Any]],
    cases: list[dict[str, Any]],
    output_path: Path,
) -> int:
    """Executes solve on all cases and writes results to answers.jsonl."""
    answers: list[dict[str, Any]] = []

    for case in cases:
        case_id = str(case.get("id") or case.get("case_id") or "unnamed_case")
        try:
            res = solve_fn(case)
        except Exception as exc:
            res = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal": "RUNNER_SOLVER_CRASH",
                "refusal_code": "RUNNER_SOLVER_CRASH",
                "error": str(exc),
            }
        answers.append(res)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for ans in answers:
            f.write(canonical_json_str(ans) + "\n")

    return len(answers)


def main() -> int:
    default_examples = Path(__file__).resolve().parent / "examples"
    default_output = Path(__file__).resolve().parent / "answers.jsonl"

    parser = argparse.ArgumentParser(description="C012 Participant Runner")
    parser.add_argument(
        "--cases",
        type=Path,
        default=default_examples,
        help="Path to cases directory, JSON file, or JSONL file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Path to output answers.jsonl file",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default=None,
        help="Path to solver .py file or importable module string",
    )

    args = parser.parse_args()

    solve_fn = load_solver_func(args.solver)
    cases = load_cases(args.cases)
    count = run_cases(solve_fn, cases, args.output)
    print(f"Executed {count} cases -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
