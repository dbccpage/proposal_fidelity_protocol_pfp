"""Roles compile into catalogue agents whose licences the catalogue seal checks."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogRefusal,
    compute_agent_license_digest,
    seal_capability_catalog,
)
from operads.infrastructure import capability_catalog_compiler as compiler

REPO = Path(__file__).resolve().parents[3]
JSON_DIR = REPO / "operads/skill_operad/json"
ROLES = yaml.safe_load((REPO / compiler.ROLES_PATH).read_text(encoding="utf-8"))["agents"]
CATALOG = json.loads((JSON_DIR / compiler.CATALOG_FILENAME).read_text(encoding="utf-8"))


def test_every_role_is_a_catalogued_agent() -> None:
    assert sorted(agent["agent_id"] for agent in CATALOG["agents"]) == sorted(ROLES)


def test_a_licence_is_exactly_the_skills_its_colours_type() -> None:
    skills = {row["skill_id"]: row for row in CATALOG["skills"]}
    for agent in CATALOG["agents"]:
        allowed = set(ROLES[agent["agent_id"]]["licence"])
        expected = sorted(
            skill_id
            for skill_id, row in skills.items()
            if {*row["source_colours"], row["target_colour"]} <= allowed
        )
        assert agent["licensed_skill_ids"] == expected
        assert agent["licensed_colour_ids"] == sorted(allowed)


def test_slices_list_each_agents_licence() -> None:
    slices = json.loads((JSON_DIR / compiler.SLICES_FILENAME).read_text(encoding="utf-8"))["agents"]
    assert set(slices) == set(ROLES)
    assert slices["rust-dev"]["sub_operad"] == ["Audit", "Code"]


def test_the_seal_refuses_a_licence_wider_than_its_colours() -> None:
    catalog = compiler.compile_capability_catalog(REPO)
    agent = next(item for item in catalog.agents if item.agent_id == "rust-dev")
    paper_skill = next(
        skill.skill_id for skill in catalog.skills if skill.target_colour == "Paper"
    )
    widened_skills = tuple(sorted({*agent.licensed_skill_ids, paper_skill}))
    widened = replace(
        agent,
        licensed_skill_ids=widened_skills,
        license_digest=compute_agent_license_digest(
            agent_id=agent.agent_id,
            licensed_skill_ids=widened_skills,
            licensed_colour_ids=agent.licensed_colour_ids,
            tools=agent.tools,
            standalone=agent.standalone,
        ),
    )
    agents = tuple(widened if item is agent else item for item in catalog.agents)
    with pytest.raises(CapabilityCatalogRefusal):
        seal_capability_catalog(skills=catalog.skills, agents=agents)


def test_a_role_with_an_extra_field_is_refused(tmp_path: Path) -> None:
    roles = tmp_path / compiler.ROLES_PATH
    roles.parent.mkdir(parents=True)
    roles.write_text(
        "schema: core.registry.roles.v1\nauthority_effect: None\n"
        "agents:\n  rust-dev:\n    licence: [Audit, Code]\n    tools: [Bash]\n",
        encoding="utf-8",
    )
    catalog = compiler.compile_capability_catalog(REPO)
    with pytest.raises(compiler.CatalogCompileRefusal):
        compiler._agents_from_roles(tmp_path, catalog.skills)
