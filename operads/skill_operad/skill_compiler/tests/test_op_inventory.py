"""Op inventory: the live file passes, and each check turns red on a one-line mutation.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from omega_engine_operads.skill_operad.domain.planar import ColorMismatch
from omega_engine_operads.skill_operad.skill_compiler import op_inventory

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


@pytest.fixture(scope="module")
def raw() -> dict:
    return yaml.safe_load((REPO_ROOT / op_inventory.INVENTORY_PATH).read_text(encoding="utf-8"))


def _skill(data: dict, skill_id: str) -> dict:
    return next(s for s in data["skills"] if s["skill_id"] == skill_id)


def _op(data: dict, op_id: str) -> dict:
    return next(o for s in data["skills"] for o in (*s["ops"], *s["anti_ops"]) if o["op_id"] == op_id)


def _codes(data: dict) -> set[str]:
    inventory = op_inventory.OpInventory.model_validate(data)
    return {f.code for f in op_inventory.check_inventory(REPO_ROOT, inventory)}


def test_live_inventory_passes(raw: dict) -> None:
    assert _codes(raw) == set()
    assert op_inventory.main(["--repo-root", str(REPO_ROOT)]) == 0


def test_every_live_skill_composes_to_its_coarse_target(raw: dict) -> None:
    inventory = op_inventory.OpInventory.model_validate(raw)
    targets = {s.skill_id: op_inventory.skill_term(s).color for s in inventory.skills}
    assert targets["techne-silent-failure-hunter"] == "Audit"
    assert targets["meta-no-comments"] == "Code"


def _mistyped_wire(data: dict) -> None:
    _op(data, "sfh.report")["inputs"] = ["Audit.hype_hits"]


def _undeclared_subcolour(data: dict) -> None:
    _op(data, "gti.layout_check")["output"] = "Audit.layout_findngs"


def _swapped_leaves(data: dict) -> None:
    merge = _skill(data, "glossa-claim-hygiene-linter")["wiring"]["args"][0]["args"][0]
    merge["args"].reverse()


def _unwired_op(data: dict) -> None:
    _skill(data, "meta-no-comments")["ops"].append(
        {"op_id": "mnc.extra", "summary": "Not wired.", "inputs": ["Code"], "output": "Code"}
    )


def _anti_op_wrong_port(data: dict) -> None:
    _op(data, "ara.refuse_unrecomputed_hash")["inspects"] = "State"


def _missing_symbol(data: dict) -> None:
    _op(data, "sfh.scan")["binding"] = (
        "omega_engine_operations/use_cases/verification/silent_failure_hunter.py::no_such_fn"
    )


def _duplicate_id(data: dict) -> None:
    _op(data, "mnc.purge")["op_id"] = "sfh.scan"
    _skill(data, "meta-no-comments")["wiring"]["args"][0]["op"] = "sfh.scan"


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (_mistyped_wire, "OI4_WIRING"),
        (_undeclared_subcolour, "OI2_PORT"),
        (_swapped_leaves, "OI5_REFINES"),
        (_unwired_op, "OI6_UNUSED_OP"),
        (_anti_op_wrong_port, "OI7_ANTI_OP"),
        (_missing_symbol, "OI8_BINDING"),
        (_duplicate_id, "OI3_DUPLICATE_OP"),
    ],
)
def test_each_check_fails_on_its_mutation(raw: dict, mutate, code: str) -> None:
    data = copy.deepcopy(raw)
    mutate(data)
    assert code in _codes(data)


def test_swapped_leaves_type_check_but_do_not_refine(raw: dict) -> None:
    """Both scanners yield Audit.hype_hits, so typing alone cannot see the swap."""
    data = copy.deepcopy(raw)
    _swapped_leaves(data)
    assert _codes(data) == {"OI5_REFINES"}


def test_skill_term_refuses_a_mistyped_wire(raw: dict) -> None:
    data = copy.deepcopy(raw)
    _mistyped_wire(data)
    skill = op_inventory.OpInventory.model_validate(data).skills[1]
    with pytest.raises(ColorMismatch):
        op_inventory.skill_term(skill)


def test_schema_error_fails_closed(tmp_path: Path, raw: dict, capsys) -> None:
    data = copy.deepcopy(raw)
    _op(data, "sfh.scan")["colour"] = "Code"
    target = tmp_path / op_inventory.INVENTORY_PATH
    target.parent.mkdir(parents=True)
    target.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert op_inventory.main(["--repo-root", str(tmp_path)]) == 1
    assert "OI1_SCHEMA" in capsys.readouterr().out
