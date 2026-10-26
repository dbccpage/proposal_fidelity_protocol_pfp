#!/usr/bin/env python3
"""Replay the deposited lesson in a fresh process and compare stored outputs.

The notebook is never rewritten. A matching replay is execution evidence for
these cells, not an independent proof of their headline or learner assessment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "jupyter_notebooks" / "009_triangle_cycle_sum.ipynb"


def compare_code_outputs(expected: dict, actual: dict) -> list[str]:
    old = [(i, c) for i, c in enumerate(expected["cells"]) if c["cell_type"] == "code"]
    new = [(i, c) for i, c in enumerate(actual["cells"]) if c["cell_type"] == "code"]
    errors = []
    if len(old) != len(new):
        return ["code-cell count changed"]
    for (i, before), (j, after) in zip(old, new):
        if i != j or before["source"] != after["source"]:
            errors.append(f"cell {i}: source or position changed")
        if before.get("execution_count") != after.get("execution_count"):
            errors.append(f"cell {i}: execution count differs")
        if before.get("outputs", []) != after.get("outputs", []):
            errors.append(f"cell {i}: outputs differ")
        if any(out.get("output_type") == "error" for out in after.get("outputs", [])):
            errors.append(f"cell {i}: execution error")
    return errors


def replay(path: Path, transport: str = "tcp", engine: str = "cpython") -> dict:
    source = path.read_bytes()
    expected = nbformat.reads(source.decode("utf-8"), as_version=4)
    nbformat.validate(expected)
    actual = nbformat.reads(source.decode("utf-8"), as_version=4)
    for cell in actual.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    if engine == "cpython":
        worker = """
import ast, contextlib, io, json, sys, traceback
notebook = json.load(sys.stdin)
namespace = {"__name__": "__main__"}
count = 0
for cell in notebook["cells"]:
    if cell["cell_type"] != "code":
        continue
    count += 1
    stdout, stderr = io.StringIO(), io.StringIO()
    cell["execution_count"], cell["outputs"] = count, []
    try:
        ast.parse(cell["source"])
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(cell["source"], "paper009-cell-" + str(count), "exec"), namespace)
    except Exception as error:
        cell["outputs"].append({
            "output_type": "error", "ename": type(error).__name__, "evalue": str(error),
            "traceback": traceback.format_exc().splitlines(),
        })
    for name, stream in (("stdout", stdout), ("stderr", stderr)):
        if stream.getvalue():
            cell["outputs"].append({
                "output_type": "stream", "name": name, "text": stream.getvalue(),
            })
    if any(o["output_type"] == "error" for o in cell["outputs"]):
        break
print(json.dumps(notebook))
"""
        environment = dict(os.environ)
        environment.pop("PYTHONOPTIMIZE", None)
        result = subprocess.run(
            [sys.executable, "-B", "-c", worker], input=json.dumps(actual),
            text=True, capture_output=True, cwd=ROOT, env=environment, timeout=60,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        actual = nbformat.from_dict(json.loads(result.stdout))
    else:
        actual = execute_jupyter(actual, transport)
    errors = compare_code_outputs(expected, actual)
    if path.read_bytes() != source:
        errors.append("notebook changed during replay")
    return {
        "status": "PASS" if not errors else "FAIL",
        "notebook": path.name,
        "notebook_sha256": hashlib.sha256(source).hexdigest(),
        "python_version": sys.version.split()[0],
        "interpreter": sys.executable,
        "engine": engine,
        "transport": transport if engine == "jupyter" else None,
        "versions": {name: version(name) for name in ("nbclient", "nbformat", "ipykernel")},
        "code_cells": sum(c.cell_type == "code" for c in actual.cells),
        "comparison": "all code-cell sources, positions, outputs, and execution counts",
        "errors": errors,
        "scope": (
            "fresh CPython process; ordinary Python cells only; no IPython rendering"
            if engine == "cpython" else "fresh Jupyter kernel execution"
        ) + "; stored-output comparison; no learner outcome",
    }


def execute_jupyter(actual, transport):
    with tempfile.TemporaryDirectory(prefix="paper009-kernel-") as directory:
        kernel_dir = Path(directory) / "paper009"
        kernel_dir.mkdir()
        specification = {
            "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
            "display_name": "Paper 009 replay interpreter",
            "language": "python",
        }
        (kernel_dir / "kernel.json").write_text(json.dumps(specification), encoding="utf-8")
        manager = KernelSpecManager(kernel_dirs=[directory])
        kernel = KernelManager(
            kernel_name="paper009", kernel_spec_manager=manager, transport=transport,
            ip="127.0.0.1" if transport == "tcp" else str(Path(directory) / "ipc"),
        )
        NotebookClient(
            actual, km=kernel, timeout=60, allow_errors=False,
            resources={"metadata": {"path": str(ROOT)}}, record_timing=False,
        ).execute()
    return actual


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--transport", choices=("tcp", "ipc"), default="tcp")
    parser.add_argument("--engine", choices=("cpython", "jupyter"), default="cpython")
    args = parser.parse_args()
    try:
        report = replay(args.notebook.resolve(), args.transport, args.engine)
    except Exception as error:
        report = {"status": "FAIL", "error": f"{type(error).__name__}: {error}"}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
