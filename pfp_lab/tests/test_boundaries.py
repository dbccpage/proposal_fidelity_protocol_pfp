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
import json
import re
import sys
from pathlib import Path
from typing import Any

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
ARCHIVE_INPUT_PREFIXES = ("atlas/archive/", "papers/")
SKIP_PARTS = frozenset({"bin", "obj", "__pycache__", "node_modules", ".vs"})


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


def _load_json_object(text: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _is_archive_reference(value: object, prefixes: tuple[str, ...]) -> bool:
    if not isinstance(value, str) or not value.startswith(prefixes):
        return False
    return "\\" not in value and not {"", ".", ".."}.intersection(value.split("/"))


def _scannable_text(relative_path: str, text: str) -> str:
    """Mask resolving archive path references in provenance and baseline JSON records.

    Per ``dag/build_atlas.py`` and ``atlas/archive_path_map.json``, upstream names stay
    inside ``atlas/archive/`` (frozen bytes), while resolving file paths keep their real
    spelling; ``governance/evidence/`` is a frozen root whose pre-move ``papers/`` input
    paths resolve to ``atlas/archive/``.
    """
    if relative_path == "governance/baseline.json":
        body = _load_json_object(text)
        if body is None or not isinstance(body.get("entries"), dict):
            return text
        entries = [
            ("" if _is_archive_reference(key, ("atlas/archive/",)) else key, value)
            for key, value in body["entries"].items()
        ]
        return json.dumps({**body, "entries": entries})
    if relative_path.startswith("governance/evidence/") and relative_path.endswith(".run.json"):
        body = _load_json_object(text)
        if body is None or not isinstance(body.get("inputs"), list):
            return text
        inputs = [
            {**item, "path": ""}
            if isinstance(item, dict) and _is_archive_reference(item.get("path"), ARCHIVE_INPUT_PREFIXES)
            else item
            for item in body["inputs"]
        ]
        return json.dumps({**body, "inputs": inputs})
    return text


def _iter_new_tree_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for root in NEW_TREES:
        base = repo / root
        if not base.exists():
            continue
        files.extend(
            path
            for path in sorted(base.rglob("*"))
            if path.is_file() and not SKIP_PARTS.intersection(path.relative_to(repo).parts)
        )
    return files


def upstream_name_hits(repo: Path) -> list[str]:
    hits: list[str] = []
    for path in _iter_new_tree_files(repo):
        relative = path.relative_to(repo).as_posix()
        text = _scannable_text(relative, path.read_text(encoding="utf-8", errors="replace"))
        if FORBIDDEN.search(text) or FORBIDDEN.search(relative):
            hits.append(relative)
    return hits


def test_new_trees_carry_no_upstream_names() -> None:
    assert upstream_name_hits(REPO) == []


def test_upstream_name_check_catches_active_violations(tmp_path: Path) -> None:
    banned_engine = "om" + "ega"
    banned_project = "anom" + "alon"
    (tmp_path / "pfp_lab").mkdir()
    (tmp_path / "pfp_lab" / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "pfp_lab" / "bad_source.py").write_text(f"{banned_engine}_value = 1\n", encoding="utf-8")
    (tmp_path / "contracts").mkdir()
    (tmp_path / "contracts" / f"{banned_project}.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "contracts" / banned_engine).mkdir()
    (tmp_path / "contracts" / banned_engine / "clean.json").write_text("{}\n", encoding="utf-8")
    evidence = tmp_path / "governance" / "evidence"
    evidence.mkdir(parents=True)
    archive_only_baseline = {
        "rule": "clean",
        "entries": {f"atlas/archive/non_pfp/016_the_{banned_project}_boundary/x.py": {"sha256": "00", "reason": "ok"}},
    }
    (tmp_path / "governance" / "baseline.json").write_text(json.dumps(archive_only_baseline), encoding="utf-8")
    archive_only_run = {
        "name": "pytest-all",
        "inputs": [
            {"path": f"atlas/archive/non_pfp/016_the_{banned_project}_boundary/x.py", "sha256": "00"},
            {"path": f"papers/029_the_{banned_project}_boundary/x.py", "sha256": "00"},
        ],
    }
    (evidence / "clean.run.json").write_text(json.dumps(archive_only_run), encoding="utf-8")
    active_leak_run = {"name": "leak", "inputs": [{"path": f"pfp_lab/{banned_engine}.py", "sha256": "00"}]}
    (evidence / "leak.run.json").write_text(json.dumps(active_leak_run), encoding="utf-8")
    escaped_input = {"inputs": [{"path": f"papers/../pfp_lab/{banned_engine}.py", "sha256": "00"}]}
    (evidence / "escape.run.json").write_text(json.dumps(escaped_input), encoding="utf-8")
    assert upstream_name_hits(tmp_path) == [
        "pfp_lab/bad_source.py",
        "governance/evidence/escape.run.json",
        "governance/evidence/leak.run.json",
        f"contracts/{banned_project}.json",
        f"contracts/{banned_engine}/clean.json",
    ]
    active_baseline_leak = {
        "rule": "clean",
        "entries": {f"atlas/archive/../../pfp/{banned_engine}.py": {"sha256": "00", "reason": "ok"}},
    }
    (tmp_path / "governance" / "baseline.json").write_text(json.dumps(active_baseline_leak), encoding="utf-8")
    assert "governance/baseline.json" in upstream_name_hits(tmp_path)


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
