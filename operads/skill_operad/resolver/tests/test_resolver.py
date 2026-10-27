"""OEWAS resolver: compose finds the smallest typed tree, run executes it or refuses first.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from operads.skill_operad.resolver import resolver
from operads.skill_operad.resolver.executors import (
    HOST_DETECTORS,
    HOST_EXECUTORS,
)
from operads.skill_operad.skill_compiler.op_inventory import (
    INVENTORY_PATH,
    OpInventory,
)

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
SFH = "techne-silent-failure-hunter"


@pytest.fixture(scope="module")
def raw() -> dict:
    return yaml.safe_load((REPO_ROOT / INVENTORY_PATH).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def inventory(raw: dict) -> OpInventory:
    return OpInventory.model_validate(raw)


def _wiring(inventory: OpInventory, skill_id: str):
    return next(s for s in inventory.skills if s.skill_id == skill_id).wiring


def _source(tmp_path: Path, name: str, text: str) -> list[str]:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return [str(path)]


CLEAN = "def f():\n    return 1\n"
BARE_EXCEPT = "def f():\n    try:\n        g()\n    except:\n        raise\n"


def test_compose_picks_the_fewest_ops(inventory: OpInventory) -> None:
    result = resolver.compose(inventory, ["Paper", "Code"], "Audit")
    assert isinstance(result, resolver.Composition)
    assert result.ops == ("sfh.report", "sfh.scan")
    assert result.leaves == ("Code",)
    assert result.unused_inputs == ("Paper",)
    assert result.anti_ops == (
        "sfh.refuse_bare_except", "sfh.refuse_pass_handler", "sfh.refuse_rust_unwrap"
    )
    assert result.alternatives == 2


def test_compose_reaches_a_multi_input_goal(inventory: OpInventory) -> None:
    result = resolver.compose(inventory, ["State", "Audit"], "Receipt")
    assert isinstance(result, resolver.Composition)
    assert result.ops == ("ara.receipt", "ara.refute", "ara.bind_source_hashes")
    assert result.leaves == ("State", "Audit")


def test_compose_bound_only_uses_installed_host_path(inventory: OpInventory) -> None:
    result = resolver.compose(inventory, ["State", "Audit"], "Receipt", bound_only=True)
    assert isinstance(result, resolver.Composition)
    assert result.ops == ("ara.receipt", "ara.refute", "ara.bind_source_hashes")


def test_compose_respects_the_op_budget(inventory: OpInventory) -> None:
    result = resolver.compose(inventory, ["State", "Audit"], "Receipt", max_ops=2)
    assert isinstance(result, resolver.Refusal)
    assert result.code == "NO_ADMISSIBLE_PATH"


def test_compose_uses_each_input_once(inventory: OpInventory) -> None:
    """``glossa.merge_hits`` needs two hit lists; one Paper cannot feed both scanners."""
    result = resolver.compose(inventory, ["Paper"], "Audit.hype_hits", max_ops=3)
    assert isinstance(result, resolver.Composition)
    assert result.ops == ("glossa.scan_hype_prose",)
    assert "glossa.merge_hits" not in result.ops


def test_compose_refuses_an_unknown_port(inventory: OpInventory) -> None:
    result = resolver.compose(inventory, ["Paper"], "Audit.vibes")
    assert isinstance(result, resolver.Refusal)
    assert result.code == "UNKNOWN_PORT"


def test_run_completes_on_clean_code(inventory: OpInventory, tmp_path: Path) -> None:
    values = {"Code": _source(tmp_path, "ok.py", CLEAN)}
    first = resolver.run(inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, HOST_DETECTORS)
    again = resolver.run(inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, HOST_DETECTORS)
    assert first.completed
    assert first.output["status"] == "PASS"
    assert [s.op_id for s in first.steps] == ["sfh.scan", "sfh.report"]
    assert first.steps == again.steps
    assert len(first.anti_ops_cleared) == 3
    assert first.to_json()["authority_effect"] == "None"


def test_run_refuses_when_an_anti_op_fires(inventory: OpInventory, tmp_path: Path) -> None:
    values = {"Code": _source(tmp_path, "bad.py", BARE_EXCEPT)}
    receipt = resolver.run(
        inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, HOST_DETECTORS
    )
    assert receipt.refusal == resolver.Refusal(
        "SFH-PY-001", "sfh.refuse_bare_except fired on slot 0 of sfh.scan"
    )
    assert receipt.steps == ()
    assert receipt.to_json()["output"] is None


def test_run_fails_closed_on_a_missing_target(inventory: OpInventory, tmp_path: Path) -> None:
    values = {"Code": [str(tmp_path / "absent.py")]}
    receipt = resolver.run(
        inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, HOST_DETECTORS
    )
    assert receipt.completed
    assert receipt.output["status"] == "FAIL"
    assert "SFH-INPUT-001" in receipt.output["findings_by_rule"]


def _spy() -> tuple[dict, list[str]]:
    calls: list[str] = []

    def record(op_id: str):
        def call(*args: object) -> object:
            calls.append(op_id)
            return HOST_EXECUTORS[op_id](*args)

        return call

    return {op_id: record(op_id) for op_id in HOST_EXECUTORS}, calls


def test_run_refuses_a_mistyped_wiring_before_executing(raw: dict, tmp_path: Path) -> None:
    """Red mutation: retype sfh.report's input and the same wiring must refuse, calling nothing."""
    data = copy.deepcopy(raw)
    report = next(o for s in data["skills"] for o in s["ops"] if o["op_id"] == "sfh.report")
    report["inputs"] = ["Audit.hype_hits"]
    mutated = OpInventory.model_validate(data)
    executors, calls = _spy()
    values = {"Code": _source(tmp_path, "ok.py", CLEAN)}
    receipt = resolver.run(mutated, _wiring(mutated, SFH), values, executors, HOST_DETECTORS)
    assert receipt.refusal is not None
    assert receipt.refusal.code == "TYPE_MISMATCH"
    assert calls == []


def test_mistyped_op_drops_out_of_compose(raw: dict) -> None:
    data = copy.deepcopy(raw)
    report = next(o for s in data["skills"] for o in s["ops"] if o["op_id"] == "sfh.report")
    report["inputs"] = ["Audit.hype_hits"]
    result = resolver.compose(OpInventory.model_validate(data), ["Code"], "Audit")
    assert isinstance(result, resolver.Composition)
    assert "sfh.scan" not in result.ops


def test_run_refuses_an_op_without_an_executor(inventory: OpInventory) -> None:
    executors, calls = _spy()
    executors.pop("glossa.report")
    receipt = resolver.run(
        inventory,
        _wiring(inventory, "glossa-claim-hygiene-linter"),
        {"Paper": "text", "Code": []},
        executors,
        HOST_DETECTORS,
    )
    assert receipt.refusal is not None
    assert receipt.refusal.code == "NOT_EXECUTABLE"
    assert "glossa.report" in receipt.refusal.message
    assert calls == []


def test_run_refuses_an_anti_op_without_a_detector(inventory: OpInventory, tmp_path: Path) -> None:
    detectors = {k: v for k, v in HOST_DETECTORS.items() if k != "sfh.refuse_rust_unwrap"}
    values = {"Code": _source(tmp_path, "ok.py", CLEAN)}
    receipt = resolver.run(inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, detectors)
    assert receipt.refusal is not None
    assert receipt.refusal.code == "NOT_EXECUTABLE"
    assert "sfh.refuse_rust_unwrap" in receipt.refusal.message


def test_run_refuses_a_missing_input(inventory: OpInventory) -> None:
    receipt = resolver.run(inventory, _wiring(inventory, SFH), {}, HOST_EXECUTORS, HOST_DETECTORS)
    assert receipt.refusal == resolver.Refusal("MISSING_INPUT", "no value for input port Code")


def test_run_refuses_output_that_is_not_json(inventory: OpInventory, tmp_path: Path) -> None:
    executors = {**HOST_EXECUTORS, "sfh.scan": lambda paths: {object()}}
    values = {"Code": _source(tmp_path, "ok.py", CLEAN)}
    receipt = resolver.run(inventory, _wiring(inventory, SFH), values, executors, HOST_DETECTORS)
    assert receipt.refusal is not None
    assert receipt.refusal.code == "OUTPUT_NOT_JSON"


def test_run_fails_closed_on_a_directory_and_an_unsupported_target(
    inventory: OpInventory, tmp_path: Path
) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "bad.py").write_text(BARE_EXCEPT, encoding="utf-8")
    receipt = resolver.run(
        inventory, _wiring(inventory, SFH), {"Code": [str(package)]}, HOST_EXECUTORS, HOST_DETECTORS
    )
    assert receipt.refusal is not None and receipt.refusal.code == "SFH-PY-001"
    note = tmp_path / "notes.md"
    note.write_text("not source\n", encoding="utf-8")
    values = {"Code": [str(note), str(tmp_path / "missing")]}
    receipt = resolver.run(inventory, _wiring(inventory, SFH), values, HOST_EXECUTORS, HOST_DETECTORS)
    assert receipt.completed
    assert receipt.output["status"] == "FAIL"
    assert receipt.output["findings_by_rule"] == {"SFH-INPUT-000": 2}


def test_run_fails_closed_when_the_code_slot_is_not_a_list(
    inventory: OpInventory, tmp_path: Path
) -> None:
    path = _source(tmp_path, "ok.py", CLEAN)[0]
    for slot in (path, 42, {"path": path}):
        receipt = resolver.run(
            inventory, _wiring(inventory, SFH), {"Code": slot}, HOST_EXECUTORS, HOST_DETECTORS
        )
        assert receipt.completed, slot
        assert receipt.output["status"] == "FAIL"
        assert receipt.output["findings_by_rule"] == {"SFH-INPUT-000": 1}


def test_run_refuses_output_that_is_not_strict_json(inventory: OpInventory, tmp_path: Path) -> None:
    executors = {**HOST_EXECUTORS, "sfh.scan": lambda paths: [{"score": float("nan")}]}
    values = {"Code": _source(tmp_path, "ok.py", CLEAN)}
    receipt = resolver.run(inventory, _wiring(inventory, SFH), values, executors, HOST_DETECTORS)
    assert receipt.refusal is not None
    assert receipt.refusal.code == "OUTPUT_NOT_JSON"


def test_cli_compose_and_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = ["--repo-root", str(REPO_ROOT)]
    assert resolver.main([*root, "compose", "--inputs", "Code", "--goal", "Audit"]) == 0
    assert json.loads(capsys.readouterr().out)["ops"] == ["sfh.report", "sfh.scan"]
    bad = json.dumps(_source(tmp_path, "bad.py", BARE_EXCEPT))
    assert resolver.main([*root, "run", "--skill", SFH, "--input", f"Code={bad}"]) == 1
    assert json.loads(capsys.readouterr().out)["refusal"]["code"] == "SFH-PY-001"
    assert resolver.main([*root, "run", "--skill", "no-such-skill"]) == 1
    assert json.loads(capsys.readouterr().out)["code"] == "UNKNOWN_SKILL"
