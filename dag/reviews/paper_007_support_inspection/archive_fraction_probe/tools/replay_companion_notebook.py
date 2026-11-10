#!/usr/bin/env python3
"""Replay the fraction-only notebook without replacing its deposited bytes.

The default backend executes ordinary Python cells in a fresh CPython process.
Its execution counts are sequential code-cell counters, not Jupyter kernel
history. The optional Jupyter backend requires nbformat/nbclient and an
explicitly selected registered kernel. Both compare normalized output data.
Neither observes a learner or establishes full repository integration.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def python_cells(path: Path) -> dict[str, object]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    if notebook["nbformat"] != 4:
        raise ValueError("requires a version-4 notebook")
    namespace: dict[str, object] = {"__name__": "__main__"}
    rows = []
    for index, cell in enumerate(notebook["cells"], 1):
        if cell["cell_type"] != "code":
            continue
        stdout, stderr = io.StringIO(), io.StringIO()
        source = "".join(cell["source"])
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(source, f"{path.name}:cell-{index}", "exec"), namespace)
        outputs = []
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            if stream.getvalue():
                outputs.append({
                    "output_type": "stream", "name": name,
                    "text": stream.getvalue(),
                })
        rows.append({
            "cell_index": index, "execution_count": len(rows) + 1, "outputs": outputs,
        })
    return {"python": sys.version.split()[0], "rows": rows}


def normalized(outputs: list[dict]) -> list[dict]:
    result = copy.deepcopy(outputs)
    for output in result:
        if output.get("output_type") == "stream" and isinstance(output.get("text"), list):
            output["text"] = "".join(output["text"])
    return result


def replay(path: Path, backend: str, kernel: str | None) -> dict[str, object]:
    before = path.read_bytes()
    expected = json.loads(before)
    with tempfile.TemporaryDirectory(prefix="paper007-notebook-") as directory:
        if backend == "python":
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker", str(path)],
                cwd=directory, capture_output=True, text=True, timeout=180, check=False,
            )
            if completed.returncode:
                raise ValueError(completed.stdout + completed.stderr)
            data = json.loads(completed.stdout)
        else:
            if not kernel:
                raise ValueError("the Jupyter backend requires --kernel")
            import nbformat
            from nbclient import NotebookClient

            notebook = nbformat.reads(before.decode("utf-8"), as_version=4)
            nbformat.validate(notebook)
            executed = NotebookClient(
                copy.deepcopy(notebook), kernel_name=kernel, timeout=180,
                resources={"metadata": {"path": directory}},
            ).execute()
            data = {
                "python": executed.metadata.language_info.version,
                "rows": [
                    {"cell_index": index, "execution_count": cell.execution_count,
                     "outputs": normalized(cell.outputs)}
                    for index, cell in enumerate(executed.cells, 1)
                    if cell.cell_type == "code"
                ],
            }
    if path.read_bytes() != before:
        raise ValueError("deposited notebook changed during replay")
    if tuple(int(v) for v in data["python"].split(".")[:2]) < (3, 12):
        raise ValueError("replay Python is below the declared 3.12 minimum")
    expected_indices = [
        index for index, cell in enumerate(expected["cells"], 1) if cell["cell_type"] == "code"
    ]
    if not expected_indices or expected_indices != [row["cell_index"] for row in data["rows"]]:
        raise ValueError("missing or inconsistent code-cell sequence")
    for row in data["rows"]:
        stored = expected["cells"][row["cell_index"] - 1]
        if (
            stored["execution_count"] != row["execution_count"]
            or normalized(stored["outputs"]) != normalized(row["outputs"])
        ):
            raise ValueError(f"stored count or outputs differ at cell {row['cell_index']}")
    return {
        "status": "PASS", "notebook": path.name,
        "notebook_sha256": hashlib.sha256(before).hexdigest(),
        "backend": backend, "kernel": kernel if backend == "jupyter" else None,
        "python": data["python"], "code_cells": len(data["rows"]),
        "comparison": "sequential code-cell counts and normalized output data",
        "deposited_notebook_unchanged": True,
        "scope": (
            "fresh CPython execution of ordinary Python cells; no Jupyter rendering or learner data"
            if backend == "python" else "fresh Jupyter kernel replay; no learner data"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("python", "jupyter"), default="python")
    parser.add_argument("--kernel", help="Explicit registered Python 3.12+ Jupyter kernel")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--notebook", type=Path,
        default=Path(__file__).resolve().parents[1]
        / "jupyter_notebooks" / "007_moving_a_discrepancy.ipynb",
    )
    args = parser.parse_args()
    try:
        result = (
            python_cells(args.worker.resolve()) if args.worker
            else replay(args.notebook.resolve(), args.backend, args.kernel)
        )
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
