"""Replay this deposit's plain-Python notebook cells without a Jupyter kernel.

This checks the source calculations and assertions. It does not exercise
interactive kernel transport, display behavior, or stored-output byte equality.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    if sys.flags.optimize or not __debug__:
        raise RuntimeError("Notebook replay requires Python assertions to be active")
    root = Path(__file__).resolve().parents[1]
    source = root / "jupyter_notebooks" / "signed_exchange_and_frontier.ipynb"
    notebook = json.loads(source.read_text(encoding="utf-8"))
    scope = {"__name__": "__main__"}
    count = 0
    os.chdir(root)
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        code = "".join(cell["source"])
        exec(compile(code, f"{source.name}:cell-{index}", "exec"), scope)
        count += 1
    print(f"PASS: {count} notebook source cells; Python assertions active")
    print("No interactive Jupyter kernel or stored-output byte equality was checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
