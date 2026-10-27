"""Static AST check that the paper-run domain modules do no disk I/O.

Ported from an internal test suite and pointed at the ``paperrun`` package here.
The pure modules may not call ``open()`` or any ``read_bytes``/``read_text``/
``write_bytes``/``write_text`` method. The three modules that touch the disk
(carrier, tree hash, stage tape) are fenced to the calls they make today, so new
I/O cannot creep in unnoticed. AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parent / "paperrun"
IO_METHODS = frozenset({"read_bytes", "read_text", "write_bytes", "write_text"})

PURE_MODULES = (
    "claim_ir.py",
    "claim_node.py",
    "enums.py",
    "errors.py",
    "obligation_node.py",
    "paper_plan.py",
    "paper_run_graph.py",
    "result.py",
    "run_plan.py",
    "services.py",
    "stage_spec.py",
    "transition_event.py",
)

#: Modules allowed to touch the disk, and the only I/O methods each may call.
RECORDED_IO = {
    "carrier.py": {"read_text"},
    "tree_hash.py": {"read_bytes"},
    "stage_driver.py": {"read_text"},
}


def disk_io_calls(py_file: Path) -> list[tuple[int, str]]:
    """``(line, call)`` for every ``open()`` or file read/write method call."""
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            found.append((node.lineno, "open"))
        elif isinstance(node.func, ast.Attribute) and node.func.attr in IO_METHODS:
            found.append((node.lineno, node.func.attr))
    return found


@pytest.mark.parametrize("module", PURE_MODULES)
def test_pure_module_has_no_disk_io(module: str) -> None:
    target = PACKAGE / module
    assert target.is_file(), f"module missing: {target}"
    assert disk_io_calls(target) == []


def test_every_module_is_classified() -> None:
    """A new module must be declared pure or given a recorded I/O allowance."""
    present = {p.name for p in PACKAGE.glob("*.py")} - {"__init__.py"}
    assert present == set(PURE_MODULES) | set(RECORDED_IO)


def test_io_modules_do_not_expand_beyond_recorded_calls() -> None:
    for module, allowed in RECORDED_IO.items():
        for line, call in disk_io_calls(PACKAGE / module):
            assert call in allowed, f"unrecorded disk I/O {call!r} at {module}:{line}"


def test_the_scanner_catches_planted_io(tmp_path: Path) -> None:
    """Negative control: without this the empty results above could mean a blind scanner."""
    planted = tmp_path / "planted.py"
    planted.write_text(
        "from pathlib import Path\n"
        "def f(p):\n"
        "    open(p).close()\n"
        "    return Path(p).read_text()\n",
        encoding="utf-8",
    )
    assert sorted(disk_io_calls(planted)) == [(3, "open"), (4, "read_text")]
