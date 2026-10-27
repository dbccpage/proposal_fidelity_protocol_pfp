"""Tests for the stage type catalog (stages/stage_types.yaml) against stage and controller files.

The typed models for stages already exist: ``stage_types.yaml`` is the source, ``stage_models.yaml``
is generated from it, and ``domain/stages/stage.py`` is the generated Pydantic module. This test
does not redefine them. It checks that the stage files and the controller satisfy the per-stage
rules stated in ``stage_types.yaml`` and in ``stages/README.md``, with negative controls.

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pfp_types_test_support import load_yaml, pfp_root  # noqa: E402

TYPES = load_yaml("stages/stage_types.yaml")["types"]
_stages_dir = pfp_root() / "infrastructure" / "yaml" / "stages"
STAGE_FILES = sorted(_stages_dir.glob("stage_[0-9]*_*.yaml"), key=lambda p: int(p.name.split("_")[1]))


def _rules() -> dict[int, dict]:
    """Per-stage constants from the allOf table in StageFile."""
    out: dict[int, dict] = {}
    for clause in TYPES["StageFile"]["json_schema_extra"]["allOf"]:
        stage = clause["if"]["properties"]["stage"]["const"]
        then = clause["then"]
        props = then["properties"]
        out[stage] = {
            "name": props["name"]["const"],
            "executor": props["executor"]["const"],
            "requires": props["requires"]["const"],
            "seat": props.get("seat", {}).get("const"),
            "required": then.get("required", []),
            "forbidden": [r for item in then["not"]["anyOf"] for r in item["required"]],
        }
    return out


def _check_stage(doc: dict, rules: dict[int, dict]) -> list[str]:
    problems: list[str] = []
    fields = TYPES["StageFile"]["fields"]
    optional = {k for k, v in fields.items() if v.get("optional")}
    unknown = set(doc) - set(fields)
    if unknown:
        problems.append(f"unknown fields {sorted(unknown)}")
    missing = set(fields) - optional - set(doc)
    if missing:
        problems.append(f"missing fields {sorted(missing)}")
    stage = doc.get("stage")
    if stage not in rules:
        return problems + ["stage outside 1..11"]
    rule = rules[stage]
    for key in ("name", "executor", "requires", "seat"):
        if doc.get(key) != rule[key]:
            problems.append(f"{key} differs from rule for stage {stage}")
    for key in rule["required"]:
        if key not in doc:
            problems.append(f"{key} required for stage {stage}")
    for key in rule["forbidden"]:
        if key in doc:
            problems.append(f"{key} forbidden for stage {stage}")
    if doc.get("authority_effect") != "None":
        problems.append("authority_effect must be None")
    if doc.get("derived_under_policy") != "SPK-001":
        problems.append("derived_under_policy must be SPK-001")
    return problems


def test_enums_match_readme_pipeline() -> None:
    assert TYPES["StageName"]["values"] == [
        "admit", "ideation", "audit", "l2_extraction", "evaluation", "adversarial",
        "challenge_replay", "selection", "receipt", "hand_off", "evidence_plan",
    ]  # fmt: skip
    assert TYPES["Executor"]["values"] == ["model", "host"]
    assert TYPES["AuthorityEffect"]["values"] == ["None"]


def test_rule_table_is_a_dependency_graph_with_the_declared_host_stages() -> None:
    from pfp.domain.stages.stages import HOST_STAGES, SEAT_BY_STAGE, requires_problem

    rules = _rules()
    assert sorted(rules) == list(range(1, 12))
    for n, rule in rules.items():
        assert requires_problem(n, rule["requires"]) is None, n
    # Selection, hand-off and the evidence plan are sinks: no later stage requires them.
    required = {r for rule in rules.values() for r in rule["requires"]}
    assert set(range(1, 12)) - required == {8, 10, 11}
    assert {n for n, r in rules.items() if r["executor"] == "host"} == set(HOST_STAGES) == {1, 5, 7, 8, 9, 10}
    assert {n: r["seat"] for n, r in rules.items() if r["seat"]} == SEAT_BY_STAGE
    assert [r["name"] for _, r in sorted(rules.items())] == TYPES["StageName"]["values"]


def test_all_eleven_stage_files_conform() -> None:
    assert [int(p.name.split("_")[1]) for p in STAGE_FILES] == list(range(1, 12))
    rules = _rules()
    for path in STAGE_FILES:
        doc = load_yaml(f"stages/{path.name}")
        assert _check_stage(doc, rules) == [], path.name


def test_controller_matches_stage_files_and_type() -> None:
    controller = load_yaml("stages/controller.yaml")
    fields = TYPES["StageController"]["fields"]
    assert set(controller) == set(fields)
    assert controller["policy_id"] == "SPK-001"
    assert controller["authority_effect"] == "None"
    assert controller["public_stage_count"] == 11 == len(controller["stages"])
    assert len(controller["source_golden_sha256"]) == 64
    by_stage = {s["stage"]: s for s in controller["stages"]}
    for path in STAGE_FILES:
        doc = load_yaml(f"stages/{path.name}")
        ref = by_stage[doc["stage"]]
        assert set(TYPES["ControllerStageRef"]["fields"]) - {"seat"} <= set(ref) <= set(TYPES["ControllerStageRef"]["fields"])
        assert ref.get("seat") == doc.get("seat")
        assert {k: doc[k] for k in ref} == ref


def test_stage_five_is_host_executed_with_input_contract() -> None:
    doc = load_yaml("stages/stage_5_evaluation.yaml")
    assert doc["executor"] == "host"
    assert "response_schema" not in doc
    contract = doc["input_contract"]
    assert set(contract) == set(TYPES["InputContract"]["fields"])
    assert contract["candidate_source_stage"] == 4
    assert contract["independent_checker_required"] is True


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(executor="host"),
        lambda d: d.update(requires=[]),
        lambda d: d.update(name="audit"),
        lambda d: d.update(authority_effect="Granted"),
        lambda d: d.update(derived_under_policy="SPK-002"),
        lambda d: d.update(input_contract={}),
        lambda d: d.pop("response_schema"),
        lambda d: d.update(extra_field=1),
        lambda d: d.update(stage=12),
        lambda d: d.update(seat="seat_adversary"),
    ],
)
def test_stage_negative_controls(mutate) -> None:
    doc = copy.deepcopy(load_yaml("stages/stage_2_ideation.yaml"))
    mutate(doc)
    assert _check_stage(doc, _rules()) != []


def test_host_stage_with_response_schema_rejected() -> None:
    doc = copy.deepcopy(load_yaml("stages/stage_5_evaluation.yaml"))
    doc["response_schema"] = {"type": "object"}
    assert _check_stage(doc, _rules()) != []
    doc = copy.deepcopy(load_yaml("stages/stage_5_evaluation.yaml"))
    del doc["input_contract"]
    assert _check_stage(doc, _rules()) != []


def test_receipt_obligation_rules_name_refusal_map_keys() -> None:
    import json

    from pfp.domain.stages.stages import OBLIGATION_CODES

    doc = load_yaml("stages/stage_9_receipt.yaml")
    mapping = json.loads((pfp_root() / "packet_schemas" / "kill_condition_refusal_map_v1.json").read_text(
        encoding="utf-8"))["mapping"]
    assert set(doc["obligation_rules"]) == set(OBLIGATION_CODES)
    assert all(value in mapping for value in doc["obligation_rules"].values())
    broken = copy.deepcopy(doc)
    broken.pop("obligation_rules")
    assert _check_stage(broken, _rules()) != []
    from pydantic import ValidationError

    from pfp.domain.stages.stages import StageFile

    other = load_yaml("stages/stage_8_selection.yaml")
    StageFile.model_validate(other)
    with pytest.raises(ValidationError):
        StageFile.model_validate({**other, "obligation_rules": doc["obligation_rules"]})


def test_seats_are_core_panel_seats() -> None:
    import json

    from pfp.domain.stages.stages import SEAT_BY_STAGE

    layout = pfp_root().parent / "engine" / "crates_rs" / "core_adversary" / "src" / "council_layout_v1.json"
    core = json.loads(layout.read_text(encoding="utf-8"))["core_required"]
    # The layout lists every seat; the default (core) panel is these five of them.
    seats = set(SEAT_BY_STAGE.values())
    assert seats == {"seat_gauge_breaker", "seat_defect_hunter", "seat_adversary", "seat_primal_dual", "seat_manuscript_truth"}
    assert seats <= {row[0] for row in core}
