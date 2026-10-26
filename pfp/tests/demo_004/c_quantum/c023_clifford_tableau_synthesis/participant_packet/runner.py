"""Sandboxed Participant Runner for C023 (Clifford Tableau Synthesis).

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
    """Serializes obj to canonical JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_solver_func(
    solver_spec: str | Path | None = None,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Loads solve function from file path, module spec, or default reference solver."""
    if solver_spec is None:
        candidate = Path(__file__).resolve().parent.parent / "reference_solver" / "synthesis.py"
        if candidate.is_file():
            solver_spec = candidate
        else:
            solver_spec = "reference_solver.synthesis"

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
        spec = importlib.util.spec_from_file_location("c023_custom_solver", solver_path)
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
            elif isinstance(data, dict):
                if "input" in data:
                    cases.append(data["input"])
                else:
                    cases.append(data)

    return cases


def run_benchmark(
    solver_spec: str | Path | None = None,
    cases_dir: Path | None = None,
    output_path: Path | None = None,
) -> int:
    """Executes the solver against the cases and writes answers.jsonl."""
    pkg_dir = Path(__file__).resolve().parent
    if cases_dir is None:
        cases_dir = pkg_dir / "examples"
    if output_path is None:
        output_path = pkg_dir / "answers.jsonl"

    solver_fn = load_solver_func(solver_spec)
    cases = load_cases(cases_dir)

    print(f"[C023 Runner] Loaded {len(cases)} cases from {cases_dir}")
    print(f"[C023 Runner] Writing answers to {output_path}")

    solved_count = 0
    refused_count = 0

    with open(output_path, "w", encoding="utf-8", newline="\n") as out_f:
        for idx, case in enumerate(cases):
            case_id = case.get("id") or case.get("case_id", f"case_{idx:03d}")
            try:
                res = solver_fn(case)
            except Exception as e:
                res = {
                    "id": case_id,
                    "status": "UNKNOWN",
                    "refusal_code": "SOLVER_EXCEPTION",
                    "exception": str(e),
                }

            if res.get("status") == "SOLVED":
                solved_count += 1
            else:
                refused_count += 1

            out_f.write(canonical_json_str(res) + "\n")

    print(f"[C023 Runner] Complete: {solved_count} SOLVED, {refused_count} OUT_OF_SCOPE / REFUSED.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run C023 participant solver.")
    parser.add_argument(
        "--solver",
        type=str,
        default=None,
        help="Path or module for synthesis.py (default: reference_solver/synthesis.py)",
    )
    parser.add_argument(
        "--cases",
        type=str,
        default=None,
        help="Path to directory or file containing test cases (default: participant_packet/examples)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output answers.jsonl (default: participant_packet/answers.jsonl)",
    )
    args = parser.parse_args()

    cases_p = Path(args.cases) if args.cases else None
    out_p = Path(args.output) if args.output else None
    run_benchmark(args.solver, cases_p, out_p)


if __name__ == "__main__":
    main()
