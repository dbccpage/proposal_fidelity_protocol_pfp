# AuthorityEffect: None.
"""
Sandboxed Participant Runner for C026 (Frustration-Free Projector Hamiltonians).

Invokes solve(case: dict) -> dict on benchmark/example cases in an isolated
environment and writes responses to answers.jsonl in RFC 8785 canonical JSON format.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List


def canonical_json_str(obj: Any) -> str:
    """Serializes obj to canonical JSON string."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_solver_func(
    solver_spec: str | Path | None = None,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
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
        spec = importlib.util.spec_from_file_location("c026_custom_solver", solver_path)
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

        mod = importlib.import_module(mod_part)
        if not hasattr(mod, func_name):
            raise AttributeError(f"Module {mod_name} does not export {func_name!r}")
        return getattr(mod, func_name)


def run_benchmark(
    cases_dir: Path | str,
    output_path: Path | str,
    solver_func: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> int:
    """Runs solver over all JSON case files in cases_dir and writes answers.jsonl."""
    cases_path = Path(cases_dir)
    out_path = Path(output_path)

    if not cases_path.is_dir():
        raise NotADirectoryError(f"Cases directory not found: {cases_path}")

    case_files = sorted(cases_path.glob("*.json"))
    if not case_files:
        print(f"Warning: No case files found in {cases_path}")
        return 0

    results: List[Dict[str, Any]] = []
    print(f"Executing {len(case_files)} cases through solver...")

    for cf in case_files:
        with open(cf, "r", encoding="utf-8") as f:
            case_data = json.load(f)

        cid = case_data.get("case_id") or case_data.get("id") or cf.stem
        try:
            ans = solver_func(case_data)
        except Exception as ex:
            ans = {
                "id": cid,
                "status": "ERROR",
                "message": f"Unhandled solver exception: {type(ex).__name__}: {ex}",
            }
        results.append(ans)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for res in results:
            f.write(canonical_json_str(res) + "\n")

    print(f"Wrote {len(results)} outputs to {out_path}")
    return len(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Runner for C026 participant solver")
    parser.add_argument(
        "--cases",
        type=str,
        default=str(Path(__file__).resolve().parent / "examples"),
        help="Path to directory containing input JSON cases",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent / "answers.jsonl"),
        help="Path to output answers.jsonl",
    )
    parser.add_argument(
        "--solver",
        type=str,
        default=None,
        help="Path to custom solver Python file or module",
    )
    args = parser.parse_args()

    solver = load_solver_func(args.solver)
    run_benchmark(args.cases, args.output, solver)


if __name__ == "__main__":
    main()
