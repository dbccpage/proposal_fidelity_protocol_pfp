"""A BOUND skill that states its residual effect has evidence for it.

``neutral`` scripts read their inputs and write at most the report file a flag names.
``contractive`` meta-no-comments removes comments from a fixture and keeps its AST.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from operads.skill_operad.resolver import executors

REPO = Path(__file__).resolve().parents[3]
CATALOG = json.loads((REPO / "operads/skill_operad/json/capability_catalog.v1.json").read_text(encoding="utf-8"))
BOUND = [row for row in CATALOG["skills"] if row["executor"]["state"] == "BOUND"]
WRITES = {"write_text", "write_bytes", "unlink", "rmtree", "remove", "rename", "move", "run", "Popen"}
REPORT_TARGETS = {"out", "out_file", "output_path"}


def _neutral_scripts() -> list[tuple[str, str]]:
    return [
        (row["skill_id"], row["executor"]["host_executor_id"].removeprefix("script:"))
        for row in BOUND
        if row["residual_effect"] == "neutral" and row["executor"]["host_executor_id"].startswith("script:")
    ]


def _write_calls(tree: ast.AST) -> list[ast.Call]:
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
        opens_for_write = name == "open" and any(
            isinstance(arg, ast.Constant) and isinstance(arg.value, str) and set(arg.value) & set("wax")
            for arg in (*node.args[1:], *(k.value for k in node.keywords if k.arg == "mode"))
        )
        if name in WRITES or opens_for_write:
            calls.append(node)
    return calls


def test_states_are_from_the_canon() -> None:
    assert {row["residual_effect"] for row in BOUND} <= {"unknown", "contractive", "neutral", "dilative"}


@pytest.mark.parametrize(("skill_id", "script"), _neutral_scripts())
def test_a_neutral_script_writes_only_its_report(skill_id: str, script: str) -> None:
    tree = ast.parse((REPO / script).read_text(encoding="utf-8"))
    for call in _write_calls(tree):
        target = call.func.value if isinstance(call.func, ast.Attribute) else None
        assert isinstance(target, ast.Name) and target.id in REPORT_TARGETS, (
            f"{skill_id}: {ast.unparse(call)[:80]} is not a report write"
        )


def test_meta_no_comments_contracts_the_comment_residual() -> None:
    source = "x = 1  # set x\n# a note\n\ndef f():\n    return x  # read\n"
    result = executors._mnc_purge({"pkg/mod.py": source})
    cleaned = result["sources"]["pkg/mod.py"]
    assert source.count("#") == 3
    assert cleaned.count("#") == 0
    assert ast.dump(ast.parse(cleaned)) == ast.dump(ast.parse(source))
