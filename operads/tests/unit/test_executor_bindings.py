"""Executor bindings: only the compiler sets BOUND, and only for code that exists and starts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from operads.domain.capability_catalog_v1 import CapabilityCatalogRefusal, ExecutorBindingV1
from operads.infrastructure import capability_catalog_compiler as compiler

REPO = Path(__file__).resolve().parents[3]
DIGEST = "0" * 64
CATALOG = REPO / "operads/skill_operad/json" / compiler.CATALOG_FILENAME
SCRIPTS = yaml.safe_load((REPO / compiler.SCRIPT_EXECUTORS_PATH).read_text(encoding="utf-8"))["skills"]


def test_unbound_is_the_default() -> None:
    assert ExecutorBindingV1().to_wire() == {
        "host_executor_id": None,
        "implementation_digest": None,
        "state": "UNBOUND",
    }


def test_bound_needs_an_executor_and_a_digest() -> None:
    with pytest.raises(CapabilityCatalogRefusal):
        ExecutorBindingV1(state="BOUND")
    with pytest.raises(CapabilityCatalogRefusal):
        ExecutorBindingV1(state="BOUND", host_executor_id="script:x.py", implementation_digest="sha")
    assert ExecutorBindingV1(state="BOUND", host_executor_id="x", implementation_digest=DIGEST)


def test_unbound_cannot_name_an_executor() -> None:
    with pytest.raises(CapabilityCatalogRefusal):
        ExecutorBindingV1(host_executor_id="script:x.py")


def test_other_states_are_refused() -> None:
    with pytest.raises(CapabilityCatalogRefusal):
        ExecutorBindingV1(state="HEALTHY", host_executor_id="x", implementation_digest=DIGEST)


def test_every_op_inventory_skill_with_host_executors_is_bound() -> None:
    bindings = compiler.executor_bindings(REPO)
    assert sorted(bindings) == [
        "adversarial-receipt-audit",
        "glossa-claim-hygiene-linter",
        "governance-test-isolation",
        "meta-no-comments",
        "techne-silent-failure-hunter",
    ]
    assert all(b.host_executor_id == f"op_inventory:{s}" for s, b in bindings.items())


def test_the_committed_catalogue_records_each_binding() -> None:
    skills = {row["skill_id"]: row for row in json.loads(CATALOG.read_text(encoding="utf-8"))["skills"]}
    expected = {**compiler.executor_bindings(REPO), **compiler.script_bindings(REPO)}
    bound = {skill_id for skill_id, row in skills.items() if row["executor"]["state"] == "BOUND"}
    assert bound == set(expected)
    for skill_id, binding in expected.items():
        assert skills[skill_id]["executor"] == binding.to_wire()


def test_a_script_outside_its_package_is_refused(tmp_path: Path) -> None:
    target = tmp_path / compiler.SCRIPT_EXECUTORS_PATH
    target.parent.mkdir(parents=True)
    target.write_text(
        "schema_version: core.oewas.script_executors.v1\n"
        "skills:\n- skill_id: a\n  script: operads/skills/b/scripts/run.py\n",
        encoding="utf-8",
    )
    with pytest.raises(compiler.CatalogCompileRefusal):
        compiler.script_bindings(tmp_path)


def test_a_script_without_a_main_guard_is_refused(tmp_path: Path) -> None:
    target = tmp_path / compiler.SCRIPT_EXECUTORS_PATH
    target.parent.mkdir(parents=True)
    target.write_text(
        "schema_version: core.oewas.script_executors.v1\n"
        "skills:\n- skill_id: a\n  script: operads/skills/a/scripts/run.py\n",
        encoding="utf-8",
    )
    script = tmp_path / "operads/skills/a/scripts/run.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('library only')\n", encoding="utf-8")
    with pytest.raises(compiler.CatalogCompileRefusal):
        compiler.script_bindings(tmp_path)


@pytest.mark.parametrize("row", SCRIPTS, ids=[row["skill_id"] for row in SCRIPTS])
def test_each_bound_script_starts(row: dict) -> None:
    launcher = (
        "import runpy, sys; sys.path[:0] = ['ops', '.']; sys.argv = ['skill', '--help']; "
        f"runpy.run_path({row['script']!r}, run_name='__main__')"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", launcher],
        cwd=REPO,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")[-400:]
