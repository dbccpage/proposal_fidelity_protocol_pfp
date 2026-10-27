"""Exercise file-backed workflow entry points with isolated valid input."""

import json
from pathlib import Path

import pytest

from operads.domain.planar_substitution import (
    SubstitutionError,
)
from operads.domain.workflow_graph import validate_workflow
from operads.infrastructure.workflow_loader import (
    load_garden,
)


def test_loaded_skill_composes_into_workflow(tmp_path: Path) -> None:
    skill = tmp_path / "identity"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\noperad_source_colours: [Code]\n"
        "operad_target_colour: Code\noperad_arity: 1\n---\nIdentity.\n",
        encoding="utf-8",
    )
    operations = load_garden(tmp_path)
    workflow = tmp_path / "workflow.json"
    workflow.write_text(json.dumps({
        "workflow_id": "fixture", "name": "Fixture",
        "source_colours": ["Code"], "target_colour": "Code",
        "pipeline": [{"slot": 0, "operation": "identity"}],
        "authority_effect": "None",
    }), encoding="utf-8")
    report = validate_workflow(
        json.loads(workflow.read_text(encoding="utf-8")),
        {op.name: op for op in operations},
    )
    assert report.is_valid
    assert report.signature_matches


def test_invalid_skill_is_a_typed_refusal(tmp_path: Path) -> None:
    skill = tmp_path / "bad"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\noperad_source_colours: [Code]\n"
        "operad_target_colour: Code\noperad_arity: 2\n---\nBad arity.\n",
        encoding="utf-8",
    )
    with pytest.raises(SubstitutionError, match="ARITY_DISAGREES"):
        load_garden(tmp_path)
