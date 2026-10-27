"""Skill listing gate: description caps, the listing budget, and catalog drift.

AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from operads.infrastructure.capability_catalog_compiler import (
    compile_capability_catalog,
)
from operads.skill_operad.skill_compiler import skill_listing
from operads.skill_operad.skill_compiler.skill_listing import (
    DESCRIPTION_CAP_BYTES,
    ListedSkill,
    listing_problems,
)

REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())


def _skill(name: str = "a", description: str = "Use when testing.", invocable: bool = True):
    return ListedSkill(name=name, description=description, model_invocable=invocable)


def test_the_live_tree_passes() -> None:
    assert skill_listing.main(["--repo-root", str(REPO_ROOT)]) == 0


def test_every_live_ext_stub_is_hidden_from_the_model() -> None:
    stubs = [s for s in skill_listing.listed_skills(REPO_ROOT) if s.name.startswith("ext-")]
    assert len(stubs) == 19
    assert not any(s.model_invocable for s in stubs)


def test_budget_keeps_little_headroom_over_the_tree() -> None:
    """The ratchet stays near the tree's size, so it cannot drift into a no-op."""
    listed = [s for s in skill_listing.listed_skills(REPO_ROOT) if s.model_invocable]
    total = sum(s.listing_bytes for s in listed)
    assert total <= skill_listing.LISTING_BUDGET_BYTES <= total * 1.10


def test_a_description_over_the_cap_is_refused() -> None:
    long = "x" * (DESCRIPTION_CAP_BYTES + 1)
    assert listing_problems([_skill(description=long)], budget=10**6) == [
        f"a: description is {DESCRIPTION_CAP_BYTES + 1} B, cap {DESCRIPTION_CAP_BYTES} B"
    ]


def test_the_cap_counts_bytes_not_characters() -> None:
    text = "é" * (DESCRIPTION_CAP_BYTES // 2 + 1)
    assert listing_problems([_skill(description=text)], budget=10**6)


def test_empty_and_multiline_descriptions_are_refused() -> None:
    problems = listing_problems(
        [_skill("a", " "), _skill("b", "one\ntwo")], budget=10**6
    )
    assert problems == ["a: empty description", "b: description spans more than one line"]


def test_the_summed_listing_must_fit_the_budget() -> None:
    skills = [_skill("ab", "cd"), _skill("ef", "gh")]
    assert listing_problems(skills, budget=8) == []
    assert listing_problems(skills, budget=7) == ["listing is 8 B over 2 skills, budget 7 B"]


def test_a_skill_hidden_from_the_model_is_exempt() -> None:
    hidden = _skill(description="x" * 1000, invocable=False)
    assert listing_problems([hidden, _skill("ab", "cd")], budget=4) == []


def test_frontmatter_flag_hides_a_skill(tmp_path: Path) -> None:
    skill = tmp_path / ".agents" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        '---\nname: s\ndescription: "d"\ndisable-model-invocation: true\n---\nbody\n',
        encoding="utf-8",
    )
    assert skill_listing.listed_skills(tmp_path) == [ListedSkill("s", "d", False)]


def test_a_stale_catalog_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Red mutation: one changed byte in a tracked catalog copy and the gate must refuse."""
    catalog = compile_capability_catalog(REPO_ROOT)
    monkeypatch.setattr(skill_listing, "compile_capability_catalog", lambda root: catalog)
    rel = ".agents/skill_operads"
    shutil.copytree(REPO_ROOT / rel, tmp_path / rel)
    assert skill_listing.catalog_problems(tmp_path) == []
    target = tmp_path / rel / "capability_catalog.v1.json"
    target.write_bytes(target.read_bytes().replace(b'"description"', b'"description" ', 1))
    problems = skill_listing.catalog_problems(tmp_path)
    assert problems and "HOST_PROJECTION_DRIFT" in problems[0]
