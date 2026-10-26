"""Gate 5 structure metrics and the ceiling they allow (SCORING.md section 3.5).

AuthorityEffect: None.
Contract: urn:pfp-governance:metrics:v1

For each file: the worst function's cyclomatic complexity (lizard), cognitive
complexity (complexipy, Python only) and control-flow nesting depth (Python:
this module's AST walk; C#: brace depth, see ``csharp_nesting``). Each metric maps to the band of the
metric ceilings table, and the file's Gate 5 ceiling is the lowest band. A
metric a tool cannot measure is reported as ``null`` and caps nothing here;
the score that cites this report must say how that metric was assessed.

``python -m governance.tools.metrics OUT.json PATH ...`` writes the report.
"""

from __future__ import annotations

import ast
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TextIO

import complexipy
import lizard

from governance.tools.checker import GRADES
from governance.tools.mutation import mask

# (A/A+ upper bound, B, C, D); above D is E. From the SCORING.md metric ceilings table.
BANDS: dict[str, tuple[int, int, int, int]] = {
    "ccn": (10, 15, 20, 50),
    "cognitive": (15, 20, 25, 40),
    "nesting": (3, 4, 5, 8),
}
_NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def band(metric: str, value: int | None) -> str:
    """The highest grade a metric value permits; ``A+`` when unmeasured."""
    if value is None:
        return "A+"
    for limit, grade in zip(BANDS[metric], ("A+", "B", "C", "D"), strict=True):
        if value <= limit:
            return grade
    return "E"


def nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Deepest control-flow nesting below ``node``; an ``elif`` stays at its ``if``'s depth.

    A nested function, lambda or class starts its own count, as lizard and
    complexipy measure functions separately.
    """
    deepest = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _SCOPES):
            continue
        is_elif = isinstance(node, ast.If) and isinstance(child, ast.If) and node.orelse == [child]
        step = 1 if isinstance(child, _NESTING_NODES) and not is_elif else 0
        deepest = max(deepest, nesting_depth(child, depth + step))
    return deepest


def python_nesting(path: Path) -> int:
    module = ast.parse(path.read_text(encoding="utf-8"))
    scopes = [node for node in ast.walk(module) if isinstance(node, _SCOPES)]
    return max((nesting_depth(scope) for scope in scopes), default=nesting_depth(module))


def csharp_nesting(path: Path) -> int:
    """Deepest brace nesting below a method body, for a file-scoped-namespace C# file.

    lizard reports no nesting for C#, and reporting 0 would be a false zero. This
    counts ``{`` depth with literals and comments masked, less two levels (type
    and member). Lambdas, initialisers and accessors count as nesting too, so the
    figure can only overstate the control-flow depth, never understate it.
    """
    depth = deepest = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        for char in mask(line):
            depth += {"{": 1, "}": -1}.get(char, 0)
            deepest = max(deepest, depth)
    return max(0, deepest - 2)


def file_metrics(path: Path) -> dict[str, int | str | None]:
    analysis = lizard.analyze_file(str(path))
    functions = analysis.function_list
    ccn = max((item.cyclomatic_complexity for item in functions), default=0)
    if path.suffix == ".py":
        cognitive: int | None = max(
            (item.complexity for item in complexipy.file_complexity(str(path)).functions), default=0
        )
        nesting: int | None = python_nesting(path)
    else:
        cognitive = None
        nesting = csharp_nesting(path)
    ceiling = min((band("ccn", ccn), band("cognitive", cognitive), band("nesting", nesting)), key=GRADES.index)
    return {
        "ccn_max": ccn,
        "cognitive_max": cognitive,
        "nesting_max": nesting,
        "functions": len(functions),
        "gate5_ceiling": ceiling,
    }


def report(paths: Iterable[Path], root: Path) -> dict[str, dict[str, int | str | None]]:
    return {path.resolve().relative_to(root).as_posix(): file_metrics(path) for path in paths}


def main(argv: Sequence[str] | None = None, out: TextIO | None = None) -> int:
    stream = out if out is not None else sys.stdout
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        stream.write("usage: metrics OUT.json PATH ...\n")
        return 2
    root = Path.cwd().resolve()
    result = report((Path(item) for item in args[1:]), root)
    Path(args[0]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    worst = min((entry["gate5_ceiling"] for entry in result.values()), key=lambda grade: GRADES.index(str(grade)))
    stream.write(f"{len(result)} files; lowest Gate 5 ceiling {worst}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
