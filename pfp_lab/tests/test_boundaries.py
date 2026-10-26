"""Static boundary checks over the PFP Lab sources.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:boundaries:v1

* RULE_PY_003: no ``assert`` statement outside tests.
* RULE_PY_002 / G2: no ``isinstance(x, int)`` (bool would pass it), and in
  ``pfp_lab/core`` no float literal and no ``float(...)`` call.
* Dependency direction: imports stay within the standard library, Pydantic,
  the web stack (``pfp_lab/web`` only) and ``pfp_lab`` itself.
* Naming: no upstream engine or project names in any new tree.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parent
SOURCES = sorted(path for path in PACKAGE.rglob("*.py") if "tests" not in path.parts)
CORE = [path for path in SOURCES if "core" in path.relative_to(PACKAGE).parts]
WEB_ONLY = {"fastapi", "starlette", "uvicorn"}
ALLOWED = {"pfp_lab", "pydantic"}
# Assembled from pieces so this file does not itself contain the names it bans.
FORBIDDEN = re.compile("|".join(["om" + "ega", "anom" + "alon"]), re.IGNORECASE)
NEW_TREES = ("pfp_lab", "governance", "csharp", "contracts", "docs/plans")


def tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def test_sources_were_found() -> None:
    assert len(SOURCES) >= 10
    assert len(CORE) >= 6


@pytest.mark.parametrize("path", SOURCES, ids=rel)
def test_no_assert_statements(path: Path) -> None:
    found = [node.lineno for node in ast.walk(tree(path)) if isinstance(node, ast.Assert)]
    assert found == [], f"{rel(path)} uses assert at lines {found}"


@pytest.mark.parametrize("path", SOURCES, ids=rel)
def test_no_isinstance_int(path: Path) -> None:
    found = []
    for node in ast.walk(tree(path)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "isinstance":
            names = ast.dump(node.args[1]) if len(node.args) == 2 else ""
            if "id='int'" in names:
                found.append(node.lineno)
    assert found == [], f"{rel(path)} uses isinstance(..., int) at lines {found}"


@pytest.mark.parametrize("path", CORE, ids=rel)
def test_core_has_no_floats(path: Path) -> None:
    found = []
    for node in ast.walk(tree(path)):
        if isinstance(node, ast.Constant) and type(node.value) is float:
            found.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
            found.append(node.lineno)
    assert found == [], f"{rel(path)} has float literals or calls at lines {found}"


def imported_roots(module: ast.Module) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("path", SOURCES, ids=rel)
def test_imports_stay_in_bounds(path: Path) -> None:
    allowed = set(ALLOWED) | set(sys.stdlib_module_names)
    if "web" in path.relative_to(PACKAGE).parts:
        allowed |= WEB_ONLY
    outside = imported_roots(tree(path)) - allowed
    assert outside == set(), f"{rel(path)} imports {sorted(outside)}"


def test_core_imports_no_front_end() -> None:
    for path in CORE:
        text = path.read_text(encoding="utf-8")
        for front in ("pfp_lab.cli", "pfp_lab.web", "pfp_lab.packs"):
            assert front not in text, f"{rel(path)} imports {front}"


def test_new_trees_carry_no_upstream_names() -> None:
    hits = []
    for root in NEW_TREES:
        base = REPO / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            skip = {"bin", "obj", "__pycache__", "node_modules", ".vs"}
            if path.is_file() and not skip.intersection(path.parts):
                text = path.read_text(encoding="utf-8", errors="replace")
                if FORBIDDEN.search(text) or FORBIDDEN.search(path.name):
                    hits.append(rel(path))
    assert hits == []


CSHARP_SOURCES = sorted(
    path for path in (REPO / "csharp").rglob("*.cs") if not {"bin", "obj", "PfpLab.Tests"}.intersection(path.parts)
)
# A postfix "!" after an identifier, call or index, that is not part of "!=".
NULL_FORGIVING = re.compile(r"(?<=[\w)\]])!(?!=)")
STRING_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"')


@pytest.mark.parametrize("path", CSHARP_SOURCES, ids=rel)
def test_csharp_has_no_null_forgiving_operator(path: Path) -> None:
    """RULE_CS_002: ``x!`` silences the compiler without checking anything at run time."""
    hits = [
        number
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if not line.lstrip().startswith("//") and NULL_FORGIVING.search(STRING_LITERAL.sub('""', line))
    ]
    assert hits == [], f"{rel(path)} uses the null-forgiving operator at lines {hits}"


def test_csharp_sources_were_found() -> None:
    assert len(CSHARP_SOURCES) >= 7
